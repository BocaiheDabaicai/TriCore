use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Tables to snapshot, ordered by FK dependency (parents before children).
/// This order is safe for both INSERT (snapshot → restore) and reverse for DELETE.
pub const TABLE_INSERT_ORDER: &[&str] = &[
    "categories",
    "users",
    "products",
    "customers",
    "departments",
    "vehicles",
    "employees",
    "warehouses",
    "regulation_categories",
    "workflow_templates",
    "issues",
    "positions",
    "regulation_files",
    "orders",
    "bundle_sales",
    "workflow_forms",
    "stock_in_records",
    "stock_out_records",
    "order_items",
    "bundle_items",
    "return_orders",
    "stock_in_items",
    "stock_out_items",
    "warehouse_inventory",
    "workflow_steps",
    "workflow_archives",
    "return_items",
];

pub const MAX_SNAPSHOTS: i64 = 12;

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct DataSnapshot {
    pub id: Uuid,
    pub snapshot_time: DateTime<Utc>,
    pub table_count: i32,
    pub status: String,
    pub notes: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct DataSnapshotFull {
    pub id: Uuid,
    pub snapshot_time: DateTime<Utc>,
    pub table_count: i32,
    pub status: String,
    pub notes: Option<String>,
    pub snapshot_data: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateSnapshotRequest {
    pub notes: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct RestoreConfirm {
    pub confirm: bool,
}
