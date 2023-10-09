use std::sync::Arc;
use chrono::Utc;
use event_flow::app::{EventSenderProxy, HasEventSenderProxy};
use event_flow::event::{Event, HandleEvent};

use crate::app::event::{Kline, Price};
use event_flow::macros::SubApp;

#[derive(SubApp)]
#[sub_event(Kline)]
#[pub_event(Price)]
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

impl HasEventSenderProxy for MarketMakerApp {
    fn get_event_sender_proxy(&mut self) -> &mut EventSenderProxy {
        &mut self.sender_proxy
    }
}

impl HandleEvent for MarketMakerApp {
    #[inline]
    fn handle_event(&mut self, event: Arc<dyn Event + Sync + Send>) {
        let n = Utc::now();
        if let Some(kline) = event.as_any().downcast_ref::<Kline>() {
            let s = kline.timestamp;
            println!("MarketMakerApp: {}", n.signed_duration_since(s).num_nanoseconds().unwrap());
            self.sender_proxy.send_event(Arc::new(Price::new(kline.symbol.clone(), kline.close)));
        }
    }
}
