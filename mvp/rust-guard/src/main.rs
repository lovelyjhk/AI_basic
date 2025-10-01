use anyhow::Result;
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
struct Alert {
    source_ip: String,
    severity: String,
    reason: String,
    patient_ids: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    let redis_url = std::env::var("REDIS_URL").unwrap_or("redis://localhost:6379".into());
    let client = redis::Client::open(redis_url)?;
    let mut con = client.get_async_connection().await?;

    let stream = "risk.alerts";
    let mut last_id = String::from("$");
    loop {
        let resp: Vec<(String, Vec<(String, std::collections::HashMap<String,String>)>)> = redis::cmd("XREAD")
            .arg("BLOCK").arg(1000)
            .arg("STREAMS").arg(stream).arg(&last_id)
            .query_async(&mut con).await?;
        if resp.is_empty() { continue; }
        for (_s, msgs) in resp {
            for (id, fields) in msgs {
                last_id = id;
                let alert: Alert = serde_json::from_value(serde_json::to_value(&fields)?)?;
                if alert.severity == "block" {
                    let _: () = con.hset("block_write", &alert.source_ip, "1").await?;
                    println!("Applied write block for {} (reason: {})", alert.source_ip, alert.reason);
                }
            }
        }
    }
}
