pub mod event;
pub mod app;
pub mod prelude;

#[macro_export]
macro_rules! sub_event {
    ($struct_name:ident, [$($event_type:ty),*]) => {
        impl AssociatedSubEvent for $struct_name {
            fn get_associated_sub_event_ids(&self) -> Vec<std::any::TypeId> {
                let result: Vec<std::any::TypeId> = vec![$(std::any::TypeId::of::<$event_type>()),*];
                result
            }
        }
    }
}

#[macro_export]
macro_rules! pub_event {
    ($struct_name:ident, [$($event_type:ty),*]) => {
        impl AssociatedPubEvent for $struct_name {
            fn get_associated_pub_event_ids(&self) -> Vec<std::any::TypeId> {
                let result: Vec<std::any::TypeId> = vec![$(std::any::TypeId::of::<$event_type>()),*];
                result
            }
        }
    }
}
