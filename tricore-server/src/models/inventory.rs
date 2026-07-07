use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

// ═══════════════════════════════════════════════════════════
// Entity structs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Warehouse {
    pub id: Uuid,
    pub name: String,
    pub location: Option<String>,
    pub manager_id: Option<Uuid>,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct StockInRecord {
    pub id: Uuid,
    pub stock_in_no: String,
    pub order_id: Option<Uuid>,
    pub warehouse_id: Uuid,
    pub operator_id: Uuid,
    pub notes: Option<String>,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct StockInItem {
    pub id: Uuid,
    pub stock_in_id: Uuid,
    pub product_id: Uuid,
    pub expected_quantity: i32,
    pub actual_quantity: i32,
    pub unit_price: Option<rust_decimal::Decimal>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct StockOutRecord {
    pub id: Uuid,
    pub stock_out_no: String,
    pub order_id: Option<Uuid>,
    pub warehouse_id: Uuid,
    pub operator_id: Uuid,
    pub vehicle_info: Option<String>,
    pub driver_info: Option<String>,
    pub notes: Option<String>,
    pub status: String,
    pub shipped_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct StockOutItem {
    pub id: Uuid,
    pub stock_out_id: Uuid,
    pub product_id: Uuid,
    pub quantity: i32,
    pub unit_price: Option<rust_decimal::Decimal>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Issue {
    pub id: Uuid,
    pub related_type: String,
    pub related_id: Uuid,
    pub description: String,
    pub severity: String,
    pub status: String,
    pub reported_by: Uuid,
    pub assigned_to: Option<Uuid>,
    pub resolution: Option<String>,
    pub resolved_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

// ═══════════════════════════════════════════════════════════
// Join / display structs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize)]
pub struct StockInWithItems {
    #[serde(flatten)]
    pub record: StockInRecord,
    pub items: Vec<StockInItem>,
}

#[derive(Debug, Serialize)]
pub struct StockOutWithItems {
    #[serde(flatten)]
    pub record: StockOutRecord,
    pub items: Vec<StockOutItem>,
}

// ═══════════════════════════════════════════════════════════
// Request DTOs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Deserialize)]
pub struct CreateWarehouseRequest {
    pub name: String,
    pub location: Option<String>,
    pub manager_id: Option<Uuid>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateWarehouseRequest {
    pub name: Option<String>,
    pub location: Option<String>,
    pub manager_id: Option<Uuid>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct CreateStockInRequest {
    pub order_id: Option<Uuid>,
    pub warehouse_id: Uuid,
    pub operator_id: Uuid,
    pub notes: Option<String>,
    pub items: Vec<CreateStockInItem>,
}

#[derive(Debug, Deserialize)]
pub struct CreateStockInItem {
    pub product_id: Uuid,
    pub expected_quantity: i32,
    pub actual_quantity: i32,
    pub unit_price: Option<f64>,
}

#[derive(Debug, Deserialize)]
pub struct VerifyStockInRequest {
    pub items: Vec<VerifyStockInItem>,
}

#[derive(Debug, Deserialize)]
pub struct VerifyStockInItem {
    pub item_id: Uuid,
    pub actual_quantity: i32,
}

#[derive(Debug, Deserialize)]
pub struct CreateStockOutRequest {
    pub order_id: Option<Uuid>,
    pub warehouse_id: Uuid,
    pub operator_id: Uuid,
    pub vehicle_info: Option<String>,
    pub driver_info: Option<String>,
    pub notes: Option<String>,
    pub items: Vec<CreateStockOutItem>,
}

#[derive(Debug, Deserialize)]
pub struct CreateStockOutItem {
    pub product_id: Uuid,
    pub quantity: i32,
    pub unit_price: Option<f64>,
}

#[derive(Debug, Deserialize)]
pub struct ShipStockOutRequest {
    pub vehicle_info: Option<String>,
    pub driver_info: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateIssueRequest {
    pub related_type: String,
    pub related_id: Uuid,
    pub description: String,
    pub reported_by: Uuid,
    pub severity: Option<String>,
    pub assigned_to: Option<Uuid>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateIssueRequest {
    pub description: Option<String>,
    pub severity: Option<String>,
    pub status: Option<String>,
    pub assigned_to: Option<Uuid>,
}

#[derive(Debug, Deserialize)]
pub struct ResolveIssueRequest {
    pub resolution: String,
}

#[derive(Debug, Serialize)]
pub struct InventoryDashboard {
    pub total_products: i64,
    pub low_stock_count: i64,
    pub total_stock_in: i64,
    pub total_stock_out: i64,
    pub open_issues: i64,
}

#[derive(Debug, Deserialize)]
pub struct StockInListQuery {
    pub status: Option<String>,
    pub warehouse_id: Option<Uuid>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct StockOutListQuery {
    pub status: Option<String>,
    pub warehouse_id: Option<Uuid>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct IssueListQuery {
    pub status: Option<String>,
    pub severity: Option<String>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}
