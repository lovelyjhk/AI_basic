use actix_web::{post, web, App, HttpServer, Responder};
use chacha20poly1305::{aead::{Aead, KeyInit}, XChaCha20Poly1305};
use rand_core::OsRng;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct DataPayload {
    records: Vec<serde_json::Value>,
}

#[derive(Serialize)]
struct EncryptedResponse {
    ciphertext: String,
}

#[post("/encrypt")]
async fn encrypt(data: web::Json<DataPayload>) -> impl Responder {
    let key = XChaCha20Poly1305::generate_key(&mut OsRng);
    let cipher = XChaCha20Poly1305::new(&key);
    let nonce = XChaCha20Poly1305::generate_nonce(&mut OsRng);
    let serialized = serde_json::to_vec(&data.records).unwrap();
    let ciphertext = cipher.encrypt(&nonce, serialized.as_ref()).unwrap();
    let encoded = base64::encode(ciphertext);
    web::Json(EncryptedResponse { ciphertext: encoded })
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("🚀 Rust 암호화 서버 실행: http://127.0.0.1:8080/encrypt");
    HttpServer::new(|| App::new().service(encrypt))
        .bind(("127.0.0.1", 8080))?
        .run()
        .await
}
