use std::sync::Arc;
use std::thread;
use std::time::Duration;
use event_flow::app::{EventSenderProxy, HasEventSenderProxy, Publish};

use crate::app::event::Kline;
use event_flow::macros::PubApp;

#[derive(PubApp)]
#[pub_event(Kline)]
pub struct KlinePublisher {
    sender_proxy: EventSenderProxy,
}

impl KlinePublisher {
    pub fn new() -> KlinePublisher {
        KlinePublisher {
            sender_proxy: EventSenderProxy::new()
        }
    }
}

impl HasEventSenderProxy for KlinePublisher {
    fn get_event_sender_proxy(&mut self) -> &mut EventSenderProxy{
        &mut self.sender_proxy
    }
}

impl Publish for KlinePublisher {
    fn publish_event(&mut self) {
        loop {
            let kline = Arc::new(Kline::new("BTCUSDT".to_string(), 1.1, 1.2, 1.0, 1.3));
            self.sender_proxy.send_event(kline);
            let duration = Duration::from_secs(1);
            thread::sleep(duration);
        }
    }
}
