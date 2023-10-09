use std::sync::Arc;
use event_flow::app::{EventSenderProxy, HasEventSenderProxy};
use event_flow::event::{Event, HandleEvent};

use crate::app::event::Price;
use event_flow::macros::SubApp;

#[derive(SubApp)]
#[sub_event(Price)]
pub struct PriceConsumerApp {
    sender_proxy: EventSenderProxy,
}

impl PriceConsumerApp {
    pub fn new() -> PriceConsumerApp {
        PriceConsumerApp {
            sender_proxy: EventSenderProxy::new()
        }
    }
}

impl HasEventSenderProxy for PriceConsumerApp {
    fn get_event_sender_proxy(&mut self) -> &mut EventSenderProxy {
        &mut self.sender_proxy
    }
}

impl HandleEvent for PriceConsumerApp {
    fn handle_event(&mut self, event: Arc<dyn Event + Sync + Send>) {
        if let Some(p) = event.as_any().downcast_ref::<Price>() {
            println!("Price: {}", p.price);
        }
    }
}
