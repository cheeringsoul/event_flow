use std::any::TypeId;
use std::sync::Arc;
use chrono::Utc;

use crate::app::event::Kline;
use event_flow::core::prelude::*;

pub struct MarketMakerApp {
    sender_proxy: EventSenderProxy,
}

impl MarketMakerApp {
    pub fn new() -> MarketMakerApp {
        MarketMakerApp {
            sender_proxy: EventSenderProxy::new()
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

impl HasEventSenderProxy for MarketMakerApp {
    fn get_event_sender_proxy(&mut self) -> &mut EventSenderProxy {
        &mut self.sender_proxy
    }
}

impl AssociatedPubEvent for MarketMakerApp {}

sub_event!(MarketMakerApp, [Kline]);
