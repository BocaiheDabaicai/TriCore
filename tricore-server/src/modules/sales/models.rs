use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

// ═══════════════════════════════════════════════════════════
// Entity structs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub username: String,
    #[serde(skip_serializing)]
    pub password_hash: String,
    pub role: String,
    pub full_name: String,
    pub phone: Option<String>,
    pub fingerprint_data: Option<String>,
    pub face_data: Option<String>,
    pub email: Option<String>,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Product {
    pub id: Uuid,
    pub sku: String,
    pub name: String,
    pub description: Option<String>,
    pub original_price: rust_decimal::Decimal,
    pub surprise_discount_percent: rust_decimal::Decimal,
    pub subsidized_price: Option<rust_decimal::Decimal>,
    pub quantity: i32,
    pub unit: String,
    pub is_active: bool,
    pub category: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Order {
    pub id: Uuid,
    pub order_no: String,
    pub customer_id: Uuid,
    pub salesperson_id: Option<Uuid>,
    pub merchant_id: Option<Uuid>,
    pub total_amount: rust_decimal::Decimal,
    pub discount_amount: rust_decimal::Decimal,
    pub final_amount: rust_decimal::Decimal,
    pub status: String,
    pub vehicle_info: Option<String>,
    pub driver_info: Option<String>,
    pub notes: Option<String>,
    pub discounts: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct OrderItem {
    pub id: Uuid,
    pub order_id: Uuid,
    pub product_id: Uuid,
    pub quantity: i32,
    pub unit_price: rust_decimal::Decimal,
    pub subtotal: rust_decimal::Decimal,
    pub warehouse_allocations: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct BundleSale {
    pub id: Uuid,
    pub bundle_name: String,
    pub salesperson_id: Uuid,
    pub merchant_id: Uuid,
    pub customer_id: Option<Uuid>,
    pub total_original_price: rust_decimal::Decimal,
    pub bundle_price: rust_decimal::Decimal,
    pub status: String,
    pub notes: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct BundleItem {
    pub id: Uuid,
    pub bundle_id: Uuid,
    pub product_id: Uuid,
    pub quantity: i32,
    pub unit_price: rust_decimal::Decimal,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct ReturnOrder {
    pub id: Uuid,
    pub return_no: String,
    pub order_id: Uuid,
    pub salesperson_id: Uuid,
    pub reason: String,
    pub total_refund_amount: rust_decimal::Decimal,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct ReturnItem {
    pub id: Uuid,
    pub return_id: Uuid,
    pub product_id: Uuid,
    pub quantity: i32,
    pub refund_amount: rust_decimal::Decimal,
    pub reason_detail: Option<String>,
    pub created_at: DateTime<Utc>,
}

// ═══════════════════════════════════════════════════════════
// Join / display structs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize)]
pub struct OrderWithItems {
    #[serde(flatten)]
    pub order: Order,
    pub items: Vec<OrderItem>,
}

#[derive(Debug, Serialize)]
pub struct BundleWithItems {
    #[serde(flatten)]
    pub bundle: BundleSale,
    pub items: Vec<BundleItem>,
}

#[derive(Debug, Serialize)]
pub struct ReturnWithItems {
    #[serde(flatten)]
    pub return_order: ReturnOrder,
    pub items: Vec<ReturnItem>,
}

// ═══════════════════════════════════════════════════════════
// Request DTOs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
}

#[derive(Debug, Serialize)]
pub struct LoginResponse {
    pub token: String,
    pub user: UserPublic,
}

#[derive(Debug, Serialize)]
pub struct UserPublic {
    pub id: Uuid,
    pub username: String,
    pub role: String,
    pub full_name: String,
    pub phone: Option<String>,
    pub email: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub password: String,
    pub role: String,
    pub full_name: String,
    pub phone: Option<String>,
    pub fingerprint_data: Option<String>,
    pub face_data: Option<String>,
    pub email: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateUserRequest {
    pub full_name: Option<String>,
    pub phone: Option<String>,
    pub fingerprint_data: Option<String>,
    pub face_data: Option<String>,
    pub email: Option<String>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct CreateProductRequest {
    pub sku: String,
    pub name: String,
    pub description: Option<String>,
    pub original_price: f64,
    pub surprise_discount_percent: Option<f64>,
    pub subsidized_price: Option<f64>,
    pub unit: Option<String>,
    pub category: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateProductRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub original_price: Option<f64>,
    pub surprise_discount_percent: Option<f64>,
    pub subsidized_price: Option<f64>,
    pub unit: Option<String>,
    pub category: Option<String>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DiscountItem {
    pub mode: String,
    pub value: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub note: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateOrderRequest {
    pub customer_id: Uuid,
    pub salesperson_id: Option<Uuid>,
    pub merchant_id: Option<Uuid>,
    pub discount_amount: Option<f64>,
    pub vehicle_info: Option<String>,
    pub driver_info: Option<String>,
    pub notes: Option<String>,
    #[serde(default)]
    pub discounts: Option<Vec<DiscountItem>>,
    pub items: Vec<CreateOrderItem>,
}

#[derive(Debug, Deserialize)]
pub struct CreateOrderItem {
    pub product_id: Uuid,
    pub quantity: i32,
    pub unit_price: f64,
    #[serde(default)]
    pub allocations: Vec<CreateOrderAllocation>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateOrderAllocation {
    pub warehouse_id: Uuid,
    pub quantity: i32,
}

#[derive(Debug, Deserialize)]
pub struct UpdateOrderStatusRequest {
    pub status: String,
}

#[derive(Debug, Deserialize)]
pub struct CreateBundleRequest {
    pub bundle_name: String,
    pub salesperson_id: Uuid,
    pub merchant_id: Uuid,
    pub customer_id: Option<Uuid>,
    pub bundle_price: f64,
    pub notes: Option<String>,
    pub items: Vec<CreateBundleItem>,
}

#[derive(Debug, Deserialize)]
pub struct CreateBundleItem {
    pub product_id: Uuid,
    pub quantity: i32,
    pub unit_price: f64,
}

#[derive(Debug, Deserialize)]
pub struct CreateReturnRequest {
    pub order_id: Uuid,
    pub salesperson_id: Uuid,
    pub reason: String,
    pub items: Vec<CreateReturnItem>,
}

#[derive(Debug, Deserialize)]
pub struct CreateReturnItem {
    pub product_id: Uuid,
    pub quantity: i32,
    pub refund_amount: f64,
    pub reason_detail: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateReturnStatusRequest {
    pub status: String,
}

#[derive(Debug, Serialize)]
pub struct SalesDashboard {
    pub total_orders: i64,
    pub total_revenue: Option<rust_decimal::Decimal>,
    pub total_users: i64,
    pub total_products: i64,
    pub orders_by_status: Vec<StatusCount>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct StatusCount {
    pub status: String,
    pub count: i64,
}

#[derive(Debug, Deserialize)]
pub struct UserListQuery {
    pub role: Option<String>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct ProductListQuery {
    pub category: Option<String>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct OrderListQuery {
    pub status: Option<String>,
    pub customer_id: Option<Uuid>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

// ═══════════════════════════════════════════════════════════
// Product Category
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct ProductCategory {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateCategoryRequest {
    pub name: String,
    pub description: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateCategoryRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub is_active: Option<bool>,
}
