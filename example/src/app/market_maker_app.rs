use std::any::TypeId;
use std::sync::Arc;
use chrono::Utc;

use crate::app::event::Kline;
use event_flow::core::prelude::*;

pub struct MarketMakerApp {
    sender_proxy: Option<EventSenderProxy>,
}

impl MarketMakerApp {
    pub fn new() -> MarketMakerApp {
        MarketMakerApp {
            sender_proxy: None
        }
    }
}

impl HandleEvent for MarketMakerApp {
    fn handle_event(&mut self, event: Arc<dyn Event + Sync + Send>) {
        let n = Utc::now();
        if let Some(kline) = event.as_any().downcast_ref::<Kline>() {
            let s = kline.timestamp;
            println!("MarketMakerApp: {}", n.signed_duration_since(s).num_nanoseconds().unwrap());
        }
    }
}

impl SetEventSenderProxy for MarketMakerApp {
    fn set_event_sender_proxy(&mut self, proxy: EventSenderProxy) {
        self.sender_proxy = Some(proxy);
    }
}

impl PubEvent for MarketMakerApp {}

sub_event!(MarketMakerApp, [Kline]);
