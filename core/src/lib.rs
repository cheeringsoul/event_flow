pub mod event;
pub mod app;
pub mod prelude;

#[macro_export]
macro_rules! sub_event {
    ($struct_name:ident, [$($event_type:ty),*]) => {
        impl SubEvent for $struct_name {
            fn get_sub_event_ids(&self) -> Vec<TypeId> {
                let result: Vec<TypeId> = vec![$(TypeId::of::<$event_type>()),*];
                result
            }
        }
    }
}

#[macro_export]
macro_rules! pub_event {
    ($struct_name:ident, [$($event_type:ty),*]) => {
        impl PubEvent for $struct_name {
            fn get_pub_event_ids(&self) -> Vec<TypeId> {
                let result: Vec<TypeId> = vec![$(TypeId::of::<$event_type>()),*];
                result
            }
        }
    }
}
