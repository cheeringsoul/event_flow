use std::any::{Any, TypeId};
use std::sync::Arc;

pub trait AssociatedSubEvent {
    fn get_associated_sub_event_ids(&self) -> Vec<TypeId>;
}

pub trait AssociatedPubEvent {
    fn get_associated_pub_event_ids(&self) -> Vec<TypeId> {
        vec![]
    }
}

pub trait HandleEvent {
    fn handle_event(&mut self, event: Arc<dyn Event + Sync + Send>);
}

pub trait Event {
    fn get_event_type(&self) -> TypeId where Self: 'static {
        TypeId::of::<Self>()
    }
    fn as_any(&self) -> &dyn Any;
}