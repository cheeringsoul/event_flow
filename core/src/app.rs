use std::any::TypeId;
use std::collections::HashMap;
use std::sync::Arc;
use std::thread;

use crossbeam_channel::{bounded, Receiver, Select, Sender};
use crate::event::{Event, HandleEvent, AssociatedPubEvent, AssociatedSubEvent};


pub trait HasEventSenderProxy {
    fn get_event_sender_proxy(&mut self) -> &mut EventSenderProxy;
}

pub trait Publish {
    fn publish_event(&mut self);
}

type SenderRegistry = HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>;

pub struct EventSenderProxy {
    sender: HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
}

impl EventSenderProxy {
    pub fn new() -> Self {
        EventSenderProxy { sender: HashMap::new() }
    }

    #[inline]
    pub fn send_event(&self, event: Arc<dyn Event + Sync + Send>) {
        let id = event.get_event_type();
        if self.sender.contains_key(&id) {
            let vec = self.sender.get(&id).unwrap();
            for elem in vec.iter() {
                elem.send(Arc::clone(&event)).expect("Failed to send message");
            }
        }
    }
}

pub trait SubApp: AssociatedSubEvent + AssociatedPubEvent + HandleEvent + HasEventSenderProxy + Send {}

pub trait PubApp: Publish + AssociatedPubEvent + HasEventSenderProxy + Send {}

struct PublisherRunner {
    sender_registry: SenderRegistry,
    app: Box<dyn PubApp>,
}


impl PublisherRunner {
    fn new(app: Box<dyn PubApp>) -> Self {
        PublisherRunner {
            sender_registry: HashMap::new(),
            app,
        }
    }

    fn run(&mut self) {
        let proxy = self.app.get_event_sender_proxy();
        proxy.sender = self.sender_registry.clone();
        self.app.publish_event();
    }

    fn get_pub_event_ids(&self) -> Vec<TypeId> {
        self.app.get_associated_pub_event_ids()
    }
}

struct SubscriberRunner {
    readers: Vec<Receiver<Arc<dyn Event + Sync + Send>>>,
    senders: HashMap<TypeId, Sender<Arc<dyn Event + Sync + Send>>>,
    sender_registry: HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
    app: Box<dyn SubApp>,
}

impl SubscriberRunner {
    fn new(app: Box<dyn SubApp>) -> Self {
        let mut readers = Vec::new();
        let mut senders = HashMap::new();
        let sub_event_ids = app.get_associated_sub_event_ids();
        for elem in sub_event_ids.iter() {
            let (sender, reader): (Sender<Arc<dyn Event + Sync + Send>>, Receiver<Arc<dyn Event + Sync + Send>>) = bounded(100);
            readers.push(reader);
            senders.insert(*elem, sender);
        }
        SubscriberRunner { readers, senders, sender_registry: HashMap::new(), app }
    }

    fn run(&mut self) {
        let proxy = self.app.get_event_sender_proxy();
        proxy.sender = self.sender_registry.clone();
        let mut sel = Select::new();
        for r in self.readers.iter() {
            sel.recv(r);
        }
        loop {
            let index = sel.ready();
            let reader = self.readers.get(index).unwrap();
            let event = reader.try_recv();
            if let Err(e) = event {
                if e.is_empty() {
                    continue;
                }
            }
            self.app.handle_event(event.unwrap());
        }
    }

    fn get_sub_event_ids(&self) -> Vec<TypeId> {
        self.app.get_associated_sub_event_ids()
    }

    fn get_pub_event_ids(&self) -> Vec<TypeId> {
        self.app.get_associated_pub_event_ids()
    }
}


pub struct AppEngine {
    subscribers: Vec<SubscriberRunner>,
    publishers: Vec<PublisherRunner>,
}

impl AppEngine {
    pub fn new() -> Self {
        AppEngine {
            subscribers: Vec::new(),
            publishers: Vec::new(),
        }
    }

    pub fn add_sub_app(&mut self, sub_app: Box<dyn SubApp>) {
        let subscriber = SubscriberRunner::new(sub_app);
        self.subscribers.push(subscriber);
    }

    pub fn add_pub_app(&mut self, pub_app: Box<dyn PubApp>) {
        let publisher = PublisherRunner::new(pub_app);
        self.publishers.push(publisher);
    }

    fn build_channel(&mut self) {
        let mut sub_registry = HashMap::new();
        for elem in self.subscribers.iter_mut() {
            for (type_id, sender) in elem.senders.iter() {
                if sub_registry.contains_key(type_id) {
                    let vec: &mut Vec<Sender<Arc<dyn Event + Sync + Send>>> = sub_registry.get_mut(type_id).unwrap();
                    vec.push(sender.clone());
                } else {
                    sub_registry.insert(*type_id, vec![sender.clone()]);
                }
            }
        }
        for elem in self.publishers.iter_mut() {
            let pub_event_ids = elem.get_pub_event_ids();
            Self::set_sender(&sub_registry, &mut (elem.sender_registry), pub_event_ids);
        }
        for elem in self.subscribers.iter_mut() {
            let sub_event_ids = elem.get_sub_event_ids();
            Self::set_sender(&sub_registry, &mut (elem.sender_registry), sub_event_ids);
        }
    }

    fn set_sender(sub_registry: &HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
                  sender_registry: &mut SenderRegistry, pub_event_ids: Vec<TypeId>) {
        for each in pub_event_ids.iter() {
            if sub_registry.contains_key(each) {
                let vec = sub_registry.get(each).unwrap();
                for sender in vec.iter() {
                    if sender_registry.contains_key(each) {
                        let vec = sender_registry.get_mut(each).unwrap();
                        vec.push(sender.clone());
                    } else {
                        sender_registry.insert(*each, vec![sender.clone()]);
                    }
                }
            }
        }
    }

    pub fn run(mut self) {
        self.build_channel();
        let mut tasks = Vec::new();
        for mut subscriber in self.subscribers {
            let task = thread::spawn(move || {
                subscriber.run();
            });
            tasks.push(task);
        }
        for mut publisher in self.publishers {
            let task = thread::spawn(move || {
                publisher.run();
            });
            tasks.push(task);
        }
        for task in tasks {
            task.join().unwrap();
        }
    }
}
