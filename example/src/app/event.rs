use chrono::{DateTime, Utc};

use event_flow::prelude::*;


#[derive(BuildEventType)]
pub struct Kline {
    open: f32,
    close: f32,
    low: f32,
    high: f32,
    pub timestamp: DateTime<Utc>,
}

impl Kline {
    pub fn new(open: f32, close: f32, low: f32, high: f32) -> Self {
        Kline {
            open,
            close,
            low,
            high,
            timestamp: Utc::now(),
        }
    }
}

#[derive(BuildEventType)]
pub struct Price {
    pub price: f32,
}
