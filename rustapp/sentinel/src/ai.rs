use anyhow::Result;
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Features {
    pub file_write_rate_per_sec: f32,
    pub unique_ext_ratio: f32,
    pub entropy_delta: f32,
    pub process_count_delta: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiResponse {
    pub risk_score: f32,
    pub action: String, // "allow" | "throttle" | "isolate"
}

pub async fn query_ai(client: &Client, url: &str, features: &Features) -> Result<AiResponse> {
    let resp = client.post(url).json(features).send().await?;
    let parsed: AiResponse = resp.json().await?;
    Ok(parsed)
}

