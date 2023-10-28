mod app;

use std::collections::HashMap;
use app::kline_publisher::KlinePublisher;
use app::market_maker_app::MarketMakerApp;
use event_flow::app::AppEngine;
use crate::app::price_consumer::PriceConsumerApp;
use crate::app::price_feed_app::c;
use crate::app::settings::get_settings;

fn main() {
    let mut engine = AppEngine::new();
    engine.add_sub_app(Box::new(MarketMakerApp::new()));
    engine.add_pub_app(Box::new(KlinePublisher::new()));
    engine.add_sub_app(Box::new(PriceConsumerApp::new()));
    engine.run();
    // c();
}
