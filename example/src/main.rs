mod app;

use app::kline_publisher::KlinePublisher;
use app::market_maker_app::MarketMakerApp;
use event_flow::app::AppEngine;


fn main() {
    let mut engine = AppEngine::new();
    engine.add_sub_app(MarketMakerApp::new());
    engine.add_pub_app(KlinePublisher::new());
    engine.run();
}
