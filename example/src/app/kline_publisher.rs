use std::sync::Arc;
use std::thread;
use std::time::Duration;

use crate::app::event::Kline;
use event_flow::core::prelude::*;

pub struct KlinePublisher {
    sender_proxy: Option<EventSenderProxy>,
}

impl KlinePublisher {
    pub fn new() -> KlinePublisher {
        KlinePublisher {
            sender_proxy: None
        }
    }
}

impl SetEventSenderProxy for KlinePublisher {
    fn set_event_sender_proxy(&mut self, proxy: EventSenderProxy) {
        self.sender_proxy = Some(proxy);
    }
}

impl Publish for KlinePublisher {
    fn publish_event(&mut self) {
        loop {
            let kline = Arc::new(Kline::new(1.1, 1.2, 1.0, 1.3));
            self.sender_proxy.as_mut().unwrap().send_event(kline);
            let duration = Duration::from_secs(1);
            thread::sleep(duration);
        }
    }
}

pub_event!(KlinePublisher, [Kline]);