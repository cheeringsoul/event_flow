use std::any::{Any, TypeId};
use std::sync::Arc;

pub trait SubEvent {
    // Return the subscribed event type.
    fn get_sub_event_ids(&self) -> Vec<TypeId>;
}

pub trait PubEvent {
    // Return the published event type.
    fn get_pub_event_ids(&self) -> Vec<TypeId> {
        vec![]
    }
}

pub trait HandleEvent {
    fn handle_event(&mut self, event: Arc<dyn Event + Sync + Send>);
}

pub trait Event {
    // Used for marking a struct as event.
    fn get_event_type(&self) -> TypeId where Self: 'static {
        TypeId::of::<Self>()
    }
    fn as_any(&self) -> &dyn Any;
}