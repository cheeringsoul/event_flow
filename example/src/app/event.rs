use chrono::{DateTime, Utc};

use event_flow::mark_event::MarkAsEvent;
use event_flow::core::prelude::*;

#[derive(Debug, MarkAsEvent)]
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