use std::any::TypeId;
use std::collections::HashMap;
use std::sync::Arc;
use std::thread;

use crossbeam_channel::{bounded, Receiver, Select, Sender};
use crate::event::{Event, HandleEvent, PubEvent, SubEvent};


pub trait SetEventSenderProxy {
    fn set_event_sender_proxy(&mut self, proxy: EventSenderProxy);
}

pub trait Publish {
    fn publish_event(&mut self);
}

pub trait AddSender {
    fn add_senders(&mut self, event_type_id: TypeId, sender: Sender<Arc<dyn Event + Sync + Send>>);
}

pub struct EventSenderProxy {
    sender: HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
}

impl EventSenderProxy {
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


struct Publisher<T: Publish + PubEvent + SetEventSenderProxy + Send + 'static> {
    sender_registry: HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
    app: T,
}

impl<T> AddSender for Publisher<T> where T: Publish + PubEvent + SetEventSenderProxy + Send + 'static {
    fn add_senders(&mut self, event_type_id: TypeId, sender: Sender<Arc<dyn Event + Sync + Send>>) {
        if self.sender_registry.contains_key(&event_type_id) {
            let vec = self.sender_registry.get_mut(&event_type_id).unwrap();
            vec.push(sender);
        } else {
            self.sender_registry.insert(event_type_id, vec![sender]);
        }
    }
}

impl<T> Publisher<T> where T: Publish + PubEvent + SetEventSenderProxy + Send + 'static {
    fn new(app: T) -> Self {
        Publisher {
            sender_registry: HashMap::new(),
            app,
        }
    }

    fn run(&mut self) {
        let proxy = EventSenderProxy { sender: self.sender_registry.clone() };
        self.app.set_event_sender_proxy(proxy);
        self.app.publish_event();
    }

    fn get_pub_event_ids(&self) -> Vec<TypeId> {
        self.app.get_pub_event_ids()
    }
}

struct Subscriber<T: SubEvent + PubEvent + HandleEvent + SetEventSenderProxy + Send + 'static> {
    readers: Vec<Receiver<Arc<dyn Event + Sync + Send>>>,
    senders: HashMap<TypeId, Sender<Arc<dyn Event + Sync + Send>>>,
    sender_registry: HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
    app: T,
}

impl<T> AddSender for Subscriber<T> where T: SubEvent + PubEvent + HandleEvent + SetEventSenderProxy + Send + 'static {
    fn add_senders(&mut self, event_type_id: TypeId, sender: Sender<Arc<dyn Event + Sync + Send>>) {
        if self.sender_registry.contains_key(&event_type_id) {
            let vec = self.sender_registry.get_mut(&event_type_id).unwrap();
            vec.push(sender);
        } else {
            self.sender_registry.insert(event_type_id, vec![sender]);
        }
    }
}

impl<T> Subscriber<T> where T: SubEvent + PubEvent + HandleEvent + SetEventSenderProxy + Send + 'static {
    fn new(app: T) -> Self {
        let mut readers = Vec::new();
        let mut senders = HashMap::new();
        let sub_event_ids = app.get_sub_event_ids();
        for elem in sub_event_ids.iter() {
            let (sender, reader): (Sender<Arc<dyn Event + Sync + Send>>, Receiver<Arc<dyn Event + Sync + Send>>) = bounded(100);
            readers.push(reader);
            senders.insert(*elem, sender);
        }
        Subscriber { readers, senders, sender_registry: HashMap::new(), app }
    }

    fn run(&mut self) {
        let proxy = EventSenderProxy { sender: self.sender_registry.clone() };
        self.app.set_event_sender_proxy(proxy);
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
        self.app.get_sub_event_ids()
    }

    fn get_pub_event_ids(&self) -> Vec<TypeId> {
        self.app.get_pub_event_ids()
    }
}


pub struct AppEngine<T1, T2>
    where
        T1: SubEvent + PubEvent + HandleEvent + SetEventSenderProxy + Send + 'static,
        T2: Publish + PubEvent + SetEventSenderProxy + Send + 'static
{
    subscribers: Vec<Subscriber<T1>>,
    publishers: Vec<Publisher<T2>>,
}

impl<T1, T2> AppEngine<T1, T2>
    where
        T1: SubEvent + PubEvent + HandleEvent + SetEventSenderProxy + Send + 'static,
        T2: Publish + PubEvent + SetEventSenderProxy + Send + 'static
{
    pub fn new() -> Self {
        AppEngine {
            subscribers: Vec::new(),
            publishers: Vec::new(),
        }
    }

    pub fn add_sub_app(&mut self, sub_app: T1) {
        let subscriber = Subscriber::new(sub_app);
        self.subscribers.push(subscriber);
    }

    pub fn add_pub_app(&mut self, pub_app: T2) {
        let publisher = Publisher::new(pub_app);
        self.publishers.push(publisher);
    }

    fn build_channel(&mut self) {
        let mut sender_registry = HashMap::new();
        for elem in self.subscribers.iter_mut() {
            for (type_id, sender) in elem.senders.iter() {
                if sender_registry.contains_key(type_id) {
                    let vec: &mut Vec<Sender<Arc<dyn Event + Sync + Send>>> = sender_registry.get_mut(type_id).unwrap();
                    vec.push(sender.clone());
                } else {
                    sender_registry.insert(*type_id, vec![sender.clone()]);
                }
            }
        }
        for elem in self.publishers.iter_mut() {
            let pub_event_ids = elem.get_pub_event_ids();
            Self::set_sender(&sender_registry, elem, pub_event_ids);
        }
        for elem in self.subscribers.iter_mut() {
            let sub_event_ids = elem.get_sub_event_ids();
            Self::set_sender(&sender_registry, elem, sub_event_ids);
        }
    }

    fn set_sender(sender_registry: &HashMap<TypeId, Vec<Sender<Arc<dyn Event + Sync + Send>>>>,
                  publisher: &mut dyn AddSender, pub_event_ids: Vec<TypeId>) {
        for each in pub_event_ids.iter() {
            if sender_registry.contains_key(each) {
                let vec = sender_registry.get(each).unwrap();
                for sender in vec.iter() {
                    publisher.add_senders(*each, sender.clone());
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
