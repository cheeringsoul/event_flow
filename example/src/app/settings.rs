use config::Config;
use lazy_static::lazy_static;
use std::sync::RwLock;

lazy_static! {
    static ref SETTINGS: RwLock<Config> = {
    let settings = Config::builder()
        .add_source(config::File::with_name("example/Settings"))
        .build()
        .unwrap();
         RwLock::new(settings)
    };
}

pub fn get_settings() -> Config {
    SETTINGS.read().expect("Failed to read settings").clone()
}