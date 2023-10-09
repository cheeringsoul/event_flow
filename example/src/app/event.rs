use chrono::{DateTime, Utc};
use event_flow::macros::EventType;

#[derive(EventType)]
pub struct Kline{
    pub symbol: String,
    pub open: f32,
    pub close: f32,
    pub low: f32,
    pub high: f32,
    pub timestamp: DateTime<Utc>,
}

impl Kline {
    pub fn new(symbol: String, open: f32, close: f32, low: f32, high: f32) -> Self {
        Kline {
            symbol,
            open,
            close,
            low,
            high,
            timestamp: Utc::now(),
        }
    }
}

#[derive(EventType)]
pub struct Price {
    pub symbol: String,
    pub price: f32,
}

impl Price {
    pub fn new(symbol: String, price: f32) -> Self {
        Price {
            symbol,
            price,
        }
    }
}