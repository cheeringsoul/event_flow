use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::TcpStream;
use openssl::ssl::{SslConnector, SslMethod};
use crate::app::settings::get_settings;

pub fn c(){
    let connector = SslConnector::builder(SslMethod::tls()).unwrap().build();
    let stream = TcpStream::connect("example.com:443").unwrap();
    let ssl_stream = connector.connect("example.com", stream).unwrap();
    let mut stream = std::io::BufReader::new(ssl_stream);
}