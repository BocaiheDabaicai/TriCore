use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, FromRow, Clone)]
pub struct McpServer {
    pub id: Uuid,
    pub name: String,
    pub transport: String,
    pub command: Option<String>,
    pub args: Option<String>,
    pub url: Option<String>,
    pub is_enabled: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateMcpServerRequest {
    pub name: String,
    #[serde(default = "default_transport")]
    pub transport: String,
    pub command: Option<String>,
    pub args: Option<String>,
    pub url: Option<String>,
    #[serde(default = "default_true")]
    pub is_enabled: bool,
}

fn default_transport() -> String { "stdio".into() }
fn default_true() -> bool { true }

#[derive(Debug, Deserialize)]
pub struct UpdateMcpServerRequest {
    pub name: Option<String>,
    pub transport: Option<String>,
    pub command: Option<String>,
    pub args: Option<String>,
    pub url: Option<String>,
    pub is_enabled: Option<bool>,
}

#[derive(Debug, Serialize, Clone)]
pub struct McpTool {
    pub server_name: String,
    pub server_id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub input_schema: serde_json::Value,
}
