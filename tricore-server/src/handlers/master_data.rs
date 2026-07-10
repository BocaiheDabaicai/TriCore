use actix_web::{HttpResponse, web};
use sqlx::PgPool;

use crate::error::AppError;
use crate::models::dto::ApiResponse;
use crate::models::master_data::*;

type HandlerResult = Result<HttpResponse, AppError>;

// ═══════════════════════════════════════════════════════════
// CUSTOMERS
// ═══════════════════════════════════════════════════════════

pub async fn list_customers(pool: web::Data<PgPool>) -> HandlerResult {
    let rows = sqlx::query_as::<_, Customer>(
        "SELECT * FROM customers WHERE is_active = true ORDER BY name"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(rows)))
}
pub async fn get_customer(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let row = sqlx::query_as::<_, Customer>("SELECT * FROM customers WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("客户不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(row)))
}
pub async fn create_customer(pool: web::Data<PgPool>, body: web::Json<CreateCustomerRequest>) -> HandlerResult {
    let c = sqlx::query_as::<_, Customer>(
        "INSERT INTO customers (name, contact_person, phone, email, address, notes) VALUES ($1,$2,$3,$4,$5,$6) RETURNING *"
    ).bind(&body.name).bind(&body.contact_person).bind(&body.phone).bind(&body.email).bind(&body.address).bind(&body.notes)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(c)))
}
pub async fn update_customer(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>, body: web::Json<UpdateCustomerRequest>) -> HandlerResult {
    let ex = sqlx::query_as::<_, Customer>("SELECT * FROM customers WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("客户不存在".into()))?;
    let c = sqlx::query_as::<_, Customer>(
        "UPDATE customers SET name=$1,contact_person=$2,phone=$3,email=$4,address=$5,notes=$6,is_active=$7 WHERE id=$8 RETURNING *"
    ).bind(body.name.as_deref().unwrap_or(&ex.name))
     .bind(body.contact_person.as_deref().or(ex.contact_person.as_deref()))
     .bind(body.phone.as_deref().or(ex.phone.as_deref()))
     .bind(body.email.as_deref().or(ex.email.as_deref()))
     .bind(body.address.as_deref().or(ex.address.as_deref()))
     .bind(body.notes.as_deref().or(ex.notes.as_deref()))
     .bind(body.is_active.unwrap_or(ex.is_active)).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(c)))
}
pub async fn delete_customer(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let rows = sqlx::query("DELETE FROM customers WHERE id = $1").bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("客户不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

// ═══════════════════════════════════════════════════════════
// DEPARTMENTS
// ═══════════════════════════════════════════════════════════

pub async fn list_departments(pool: web::Data<PgPool>) -> HandlerResult {
    let rows = sqlx::query_as::<_, Department>(
        "SELECT * FROM departments WHERE is_active = true ORDER BY name"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(rows)))
}
pub async fn get_department(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let row = sqlx::query_as::<_, Department>("SELECT * FROM departments WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("部门不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(row)))
}
pub async fn create_department(pool: web::Data<PgPool>, body: web::Json<CreateDepartmentRequest>) -> HandlerResult {
    let d = sqlx::query_as::<_, Department>(
        "INSERT INTO departments (name, description) VALUES ($1,$2) RETURNING *"
    ).bind(&body.name).bind(&body.description).fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(d)))
}
pub async fn update_department(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>, body: web::Json<UpdateDepartmentRequest>) -> HandlerResult {
    let ex = sqlx::query_as::<_, Department>("SELECT * FROM departments WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("部门不存在".into()))?;
    let d = sqlx::query_as::<_, Department>(
        "UPDATE departments SET name=$1,description=$2,is_active=$3 WHERE id=$4 RETURNING *"
    ).bind(body.name.as_deref().unwrap_or(&ex.name)).bind(body.description.as_deref().or(ex.description.as_deref()))
     .bind(body.is_active.unwrap_or(ex.is_active)).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(d)))
}
pub async fn delete_department(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let rows = sqlx::query("DELETE FROM departments WHERE id = $1").bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("部门不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

// ═══════════════════════════════════════════════════════════
// POSITIONS
// ═══════════════════════════════════════════════════════════

pub async fn list_positions(pool: web::Data<PgPool>) -> HandlerResult {
    let rows = sqlx::query_as::<_, Position>(
        "SELECT * FROM positions WHERE is_active = true ORDER BY name"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(rows)))
}
pub async fn get_position(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let row = sqlx::query_as::<_, Position>("SELECT * FROM positions WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("职位不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(row)))
}
pub async fn create_position(pool: web::Data<PgPool>, body: web::Json<CreatePositionRequest>) -> HandlerResult {
    let p = sqlx::query_as::<_, Position>(
        "INSERT INTO positions (name, department_id, description) VALUES ($1,$2,$3) RETURNING *"
    ).bind(&body.name).bind(body.department_id).bind(&body.description).fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(p)))
}
pub async fn update_position(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>, body: web::Json<UpdatePositionRequest>) -> HandlerResult {
    let ex = sqlx::query_as::<_, Position>("SELECT * FROM positions WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("职位不存在".into()))?;
    let p = sqlx::query_as::<_, Position>(
        "UPDATE positions SET name=$1,department_id=$2,description=$3,is_active=$4 WHERE id=$5 RETURNING *"
    ).bind(body.name.as_deref().unwrap_or(&ex.name)).bind(body.department_id.or(ex.department_id))
     .bind(body.description.as_deref().or(ex.description.as_deref())).bind(body.is_active.unwrap_or(ex.is_active)).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(p)))
}
pub async fn delete_position(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let rows = sqlx::query("DELETE FROM positions WHERE id = $1").bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("职位不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

// ═══════════════════════════════════════════════════════════
// VEHICLES
// ═══════════════════════════════════════════════════════════

pub async fn list_vehicles(pool: web::Data<PgPool>) -> HandlerResult {
    let rows = sqlx::query_as::<_, Vehicle>(
        "SELECT * FROM vehicles WHERE is_active = true ORDER BY plate_number"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(rows)))
}
pub async fn get_vehicle(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let row = sqlx::query_as::<_, Vehicle>("SELECT * FROM vehicles WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("车辆不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(row)))
}
pub async fn create_vehicle(pool: web::Data<PgPool>, body: web::Json<CreateVehicleRequest>) -> HandlerResult {
    let v = sqlx::query_as::<_, Vehicle>(
        "INSERT INTO vehicles (plate_number, model, capacity, driver_name, driver_phone, notes) VALUES ($1,$2,$3,$4,$5,$6) RETURNING *"
    ).bind(&body.plate_number).bind(&body.model).bind(&body.capacity).bind(&body.driver_name).bind(&body.driver_phone).bind(&body.notes)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(v)))
}
pub async fn update_vehicle(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>, body: web::Json<UpdateVehicleRequest>) -> HandlerResult {
    let ex = sqlx::query_as::<_, Vehicle>("SELECT * FROM vehicles WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("车辆不存在".into()))?;
    let v = sqlx::query_as::<_, Vehicle>(
        "UPDATE vehicles SET plate_number=$1,model=$2,capacity=$3,driver_name=$4,driver_phone=$5,status=$6,notes=$7,is_active=$8 WHERE id=$9 RETURNING *"
    ).bind(body.plate_number.as_deref().unwrap_or(&ex.plate_number))
     .bind(body.model.as_deref().or(ex.model.as_deref())).bind(body.capacity.as_deref().or(ex.capacity.as_deref()))
     .bind(body.driver_name.as_deref().or(ex.driver_name.as_deref())).bind(body.driver_phone.as_deref().or(ex.driver_phone.as_deref()))
     .bind(body.status.as_deref().unwrap_or(&ex.status)).bind(body.notes.as_deref().or(ex.notes.as_deref()))
     .bind(body.is_active.unwrap_or(ex.is_active)).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(v)))
}
pub async fn delete_vehicle(pool: web::Data<PgPool>, path: web::Path<uuid::Uuid>) -> HandlerResult {
    let rows = sqlx::query("DELETE FROM vehicles WHERE id = $1").bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("车辆不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}
