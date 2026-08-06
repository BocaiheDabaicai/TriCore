use actix_web::{HttpResponse, web};
use serde::Deserialize;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::dto::{ApiResponse, PaginatedResponse};
use crate::modules::sales::models::*;

// ═══════════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════════

pub async fn login(
    pool: web::Data<PgPool>,
    body: web::Json<LoginRequest>,
) -> Result<HttpResponse, AppError> {
    let user = sqlx::query_as::<_, User>(
        "SELECT * FROM users WHERE username = $1 AND is_active = true"
    )
    .bind(&body.username)
    .fetch_optional(pool.get_ref())
    .await?
    .ok_or_else(|| AppError::Unauthorized("用户名或密码错误".into()))?;

    let valid = bcrypt::verify(&body.password, &user.password_hash)?;
    if !valid {
        return Err(AppError::Unauthorized("用户名或密码错误".into()));
    }

    let public = UserPublic {
        id: user.id,
        username: user.username,
        role: user.role,
        full_name: user.full_name,
        phone: user.phone,
        email: user.email,
    };

    // Simplified token (plain UUID for now)
    let resp = LoginResponse {
        token: user.id.to_string(),
        user: public,
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(resp)))
}

// ═══════════════════════════════════════════════════════════
// USERS
// ═══════════════════════════════════════════════════════════

pub async fn list_users(
    pool: web::Data<PgPool>,
    query: web::Query<UserListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let (users, total): (Vec<User>, i64) = if let Some(ref role) = query.role {
        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users WHERE role = $1")
            .bind(role).fetch_one(pool.get_ref()).await?;
        let users = sqlx::query_as::<_, User>(
            "SELECT * FROM users WHERE role = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3"
        ).bind(role).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;
        (users, total.0)
    } else {
        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users").fetch_one(pool.get_ref()).await?;
        let users = sqlx::query_as::<_, User>(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2"
        ).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;
        (users, total.0)
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(users, total, page, per_page))))
}

pub async fn get_user(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
        .bind(*path)
        .fetch_optional(pool.get_ref())
        .await?
        .ok_or_else(|| AppError::NotFound("用户不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(user)))
}

pub async fn create_user(
    pool: web::Data<PgPool>,
    body: web::Json<CreateUserRequest>,
) -> Result<HttpResponse, AppError> {
    let hash = bcrypt::hash(&body.password, 10)?;
    let user = sqlx::query_as::<_, User>(
        "INSERT INTO users (username, password_hash, role, full_name, phone, fingerprint_data, face_data, email)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *"
    )
    .bind(&body.username).bind(&hash).bind(&body.role).bind(&body.full_name)
    .bind(&body.phone).bind(&body.fingerprint_data).bind(&body.face_data).bind(&body.email)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(user)))
}

pub async fn update_user(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateUserRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("用户不存在".into()))?;

    let name = body.full_name.as_deref().unwrap_or(&existing.full_name);
    let phone = body.phone.as_deref().or(existing.phone.as_deref());
    let email = body.email.as_deref().or(existing.email.as_deref());
    let fp = body.fingerprint_data.as_deref().or(existing.fingerprint_data.as_deref());
    let face = body.face_data.as_deref().or(existing.face_data.as_deref());
    let active = body.is_active.unwrap_or(existing.is_active);

    let user = sqlx::query_as::<_, User>(
        "UPDATE users SET full_name=$1, phone=$2, email=$3, fingerprint_data=$4, face_data=$5, is_active=$6
         WHERE id=$7 RETURNING *"
    ).bind(name).bind(phone).bind(email).bind(fp).bind(face).bind(active).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(user)))
}

// ═══════════════════════════════════════════════════════════
// PRODUCTS
// ═══════════════════════════════════════════════════════════

pub async fn list_products(
    pool: web::Data<PgPool>,
    query: web::Query<ProductListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let (products, total): (Vec<Product>, i64) = if let Some(ref cat) = query.category {
        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE category = $1 AND is_active = true")
            .bind(cat).fetch_one(pool.get_ref()).await?;
        let products = sqlx::query_as::<_, Product>(
            "SELECT * FROM products WHERE category = $1 AND is_active = true ORDER BY created_at DESC LIMIT $2 OFFSET $3"
        ).bind(cat).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;
        (products, total.0)
    } else {
        let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE is_active = true").fetch_one(pool.get_ref()).await?;
        let products = sqlx::query_as::<_, Product>(
            "SELECT * FROM products WHERE is_active = true ORDER BY created_at DESC LIMIT $1 OFFSET $2"
        ).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;
        (products, total.0)
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(products, total, page, per_page))))
}

pub async fn get_product(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let product = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("商品不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(product)))
}

pub async fn create_product(
    pool: web::Data<PgPool>,
    body: web::Json<CreateProductRequest>,
) -> Result<HttpResponse, AppError> {
    let disc = body.surprise_discount_percent.unwrap_or(0.0);
    let disc_d = rust_decimal::Decimal::try_from(disc).unwrap_or_default();
    let orig_d = rust_decimal::Decimal::try_from(body.original_price).unwrap_or_default();
    let sub_d = body.subsidized_price.map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default());
    let unit = body.unit.clone().unwrap_or_else(|| "件".into());

    let product = sqlx::query_as::<_, Product>(
        "INSERT INTO products (sku, name, description, original_price, surprise_discount_percent, subsidized_price, unit, category)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *"
    ).bind(&body.sku).bind(&body.name).bind(&body.description)
     .bind(orig_d).bind(disc_d).bind(sub_d).bind(unit).bind(&body.category)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(product)))
}

pub async fn update_product(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateProductRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("商品不存在".into()))?;

    let name = body.name.as_deref().unwrap_or(&existing.name);
    let desc = body.description.as_deref().or(existing.description.as_deref());
    let orig = body.original_price.map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default()).unwrap_or(existing.original_price);
    let disc = body.surprise_discount_percent.map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default()).unwrap_or(existing.surprise_discount_percent);
    let sub = match body.subsidized_price {
        Some(v) => Some(rust_decimal::Decimal::try_from(v).unwrap_or_default()),
        None => existing.subsidized_price,
    };
    let unit = body.unit.as_deref().unwrap_or(&existing.unit);
    let cat = body.category.as_deref().or(existing.category.as_deref());
    let active = body.is_active.unwrap_or(existing.is_active);

    let product = sqlx::query_as::<_, Product>(
        "UPDATE products SET name=$1, description=$2, original_price=$3, surprise_discount_percent=$4,
         subsidized_price=$5, unit=$6, category=$7, is_active=$8 WHERE id=$9 RETURNING *"
    ).bind(name).bind(desc).bind(orig).bind(disc).bind(sub).bind(unit).bind(cat).bind(active).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(product)))
}

// ═══════════════════════════════════════════════════════════
// ORDERS
// ═══════════════════════════════════════════════════════════

pub async fn list_orders(
    pool: web::Data<PgPool>,
    query: web::Query<OrderListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut where_clauses: Vec<String> = vec![];
    let mut bind_idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref status) = query.status {
        bind_idx += 1;
        where_clauses.push(format!("status = ${bind_idx}"));
        params.push(status.clone());
    }
    if let Some(cid) = query.customer_id {
        bind_idx += 1;
        where_clauses.push(format!("customer_id = ${bind_idx}"));
        params.push(cid.to_string());
    }

    let where_sql = if where_clauses.is_empty() { String::new() } else { format!("WHERE {}", where_clauses.join(" AND ")) };
    let count_sql = format!("SELECT COUNT(*) FROM orders {where_sql}");
    let list_sql = format!("SELECT * FROM orders {where_sql} ORDER BY created_at DESC LIMIT ${0} OFFSET ${1}", bind_idx + 1, bind_idx + 2);

    // Build queries manually since we have dynamic where
    let total: (i64,) = {
        let mut q = sqlx::query_as(&count_sql);
        for p in &params {
            q = q.bind(p);
        }
        q.fetch_one(pool.get_ref()).await?
    };

    let orders: Vec<Order> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params {
            q = q.bind(p);
        }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(orders, total.0, page, per_page))))
}

pub async fn get_order(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let order = sqlx::query_as::<_, Order>("SELECT * FROM orders WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("订单不存在".into()))?;
    let items = sqlx::query_as::<_, OrderItem>(
        "SELECT * FROM order_items WHERE order_id = $1 ORDER BY created_at"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(OrderWithItems { order, items })))
}

pub async fn create_order(
    pool: web::Data<PgPool>,
    body: web::Json<CreateOrderRequest>,
) -> Result<HttpResponse, AppError> {
    if body.items.is_empty() {
        return Err(AppError::BadRequest("订单至少需要一个商品".into()));
    }

    let total: f64 = body.items.iter().map(|i| i.unit_price * i.quantity as f64).sum();
    let discount = body.discount_amount.unwrap_or(0.0);
    let final_amt = total - discount;
    let order_no = format!("ORD-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);

    let total_d = rust_decimal::Decimal::try_from(total).unwrap_or_default();
    let discount_d = rust_decimal::Decimal::try_from(discount).unwrap_or_default();
    let final_d = rust_decimal::Decimal::try_from(final_amt).unwrap_or_default();

    let mut tx = pool.begin().await?;

    let discounts_json = body.discounts.as_ref()
        .and_then(|d| serde_json::to_value(d).ok());
    let order = sqlx::query_as::<_, Order>(
        "INSERT INTO orders (order_no, customer_id, salesperson_id, merchant_id, total_amount, discount_amount, final_amount, vehicle_info, driver_info, notes, discounts)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) RETURNING *"
    ).bind(&order_no).bind(body.customer_id).bind(body.salesperson_id)
     .bind(body.merchant_id).bind(total_d).bind(discount_d).bind(final_d)
     .bind(&body.vehicle_info).bind(&body.driver_info).bind(&body.notes)
     .bind(&discounts_json)
    .fetch_one(&mut *tx).await?;

    for item in &body.items {
        let product = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
            .bind(item.product_id).fetch_optional(&mut *tx).await?
            .ok_or_else(|| AppError::NotFound(format!("商品 {} 不存在", item.product_id)))?;
        if product.quantity < item.quantity {
            return Err(AppError::BadRequest(format!("商品「{}」库存不足 (可用: {}, 需要: {})", product.name, product.quantity, item.quantity)));
        }

        let sub = rust_decimal::Decimal::try_from(item.unit_price * item.quantity as f64).unwrap_or_default();
        let up = rust_decimal::Decimal::try_from(item.unit_price).unwrap_or_default();
        let allocs_json = if item.allocations.is_empty() {
            None
        } else {
            Some(serde_json::to_value(&item.allocations).unwrap_or_default())
        };
        sqlx::query(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, warehouse_allocations) VALUES ($1,$2,$3,$4,$5,$6)"
        ).bind(order.id).bind(item.product_id).bind(item.quantity).bind(up).bind(sub).bind(&allocs_json)
        .execute(&mut *tx).await?;

        // Deduct inventory immediately upon order creation
        sqlx::query("UPDATE products SET quantity = quantity - $1 WHERE id = $2")
            .bind(item.quantity).bind(item.product_id).execute(&mut *tx).await?;

        // Deduct from warehouse_inventory based on allocations
        if !item.allocations.is_empty() {
            let mut allocated_total = 0i32;
            for alloc in &item.allocations {
                allocated_total += alloc.quantity;
                // Verify warehouse has enough stock
                let wi = sqlx::query_as::<_, crate::modules::inventory::models::WarehouseInventory>(
                    "SELECT * FROM warehouse_inventory WHERE product_id = $1 AND warehouse_id = $2"
                ).bind(item.product_id).bind(alloc.warehouse_id)
                .fetch_optional(&mut *tx).await?;
                let current = wi.map(|w| w.quantity).unwrap_or(0);
                if current < alloc.quantity {
                    return Err(AppError::BadRequest(
                        format!("商品「{}」在指定仓库库存不足 (可用: {}, 需要: {})", product.name, current, alloc.quantity)
                    ));
                }
                sqlx::query(
                    "UPDATE warehouse_inventory SET quantity = quantity - $1, updated_at = NOW()
                     WHERE product_id = $2 AND warehouse_id = $3"
                ).bind(alloc.quantity).bind(item.product_id).bind(alloc.warehouse_id)
                .execute(&mut *tx).await?;
            }
            if allocated_total != item.quantity {
                return Err(AppError::BadRequest(
                    format!("商品「{}」的仓库分配数量合计({})与商品总数({})不一致", product.name, allocated_total, item.quantity)
                ));
            }
        } else if item.quantity > 0 {
            // No allocations provided: auto-deduct from warehouses with stock (FIFO-like)
            let warehouses = sqlx::query_as::<_, crate::modules::inventory::models::WarehouseInventory>(
                "SELECT * FROM warehouse_inventory WHERE product_id = $1 AND quantity > 0 ORDER BY quantity DESC"
            ).bind(item.product_id).fetch_all(&mut *tx).await?;
            let mut remaining = item.quantity;
            for wi in &warehouses {
                if remaining <= 0 { break; }
                let take = remaining.min(wi.quantity);
                sqlx::query(
                    "UPDATE warehouse_inventory SET quantity = quantity - $1, updated_at = NOW()
                     WHERE id = $2"
                ).bind(take).bind(wi.id).execute(&mut *tx).await?;
                remaining -= take;
            }
        }
    }

    tx.commit().await?;

    let items = sqlx::query_as::<_, OrderItem>(
        "SELECT * FROM order_items WHERE order_id = $1"
    ).bind(order.id).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Created().json(ApiResponse::success(OrderWithItems { order, items })))
}

#[derive(Debug, Deserialize)]
pub struct UpdateOrderRequest {
    customer_id: Option<Uuid>,
    vehicle_info: Option<String>,
    driver_info: Option<String>,
    notes: Option<String>,
    discount_amount: Option<f64>,
    #[serde(default)]
    pub discounts: Option<Vec<DiscountItem>>,
    pub items: Option<Vec<CreateOrderItem>>,
}

pub async fn update_order(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateOrderRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, Order>("SELECT * FROM orders WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("订单不存在".into()))?;

    if existing.status != "pending" {
        return Err(AppError::BadRequest("只有待处理的订单才能修改".into()));
    }

    let mut tx = pool.begin().await?;

    let vehicle = body.vehicle_info.as_deref().or(existing.vehicle_info.as_deref());
    let driver = body.driver_info.as_deref().or(existing.driver_info.as_deref());
    let notes = body.notes.as_deref().or(existing.notes.as_deref());
    let customer = body.customer_id.unwrap_or(existing.customer_id);

    let discounts_json = body.discounts.as_ref()
        .and_then(|d| serde_json::to_value(d).ok());

    // Calculate amounts — either from new items or from existing + discount delta
    let (total_amount, discount_amount, final_amount) = if let Some(ref new_items) = body.items {
        if new_items.is_empty() {
            return Err(AppError::BadRequest("订单至少需要一个商品".into()));
        }

        // Restore old inventory
        let old_items = sqlx::query_as::<_, OrderItem>(
            "SELECT * FROM order_items WHERE order_id = $1"
        ).bind(*path).fetch_all(&mut *tx).await?;
        for oi in &old_items {
            sqlx::query("UPDATE products SET quantity = quantity + $1 WHERE id = $2")
                .bind(oi.quantity).bind(oi.product_id).execute(&mut *tx).await?;
            let wis = sqlx::query_as::<_, crate::modules::inventory::models::WarehouseInventory>(
                "SELECT * FROM warehouse_inventory WHERE product_id = $1 ORDER BY updated_at DESC"
            ).bind(oi.product_id).fetch_all(&mut *tx).await?;
            if !wis.is_empty() {
                sqlx::query(
                    "UPDATE warehouse_inventory SET quantity = quantity + $1, updated_at = NOW()
                     WHERE id = $2"
                ).bind(oi.quantity).bind(wis[0].id).execute(&mut *tx).await?;
            }
        }

        // Delete old order items
        sqlx::query("DELETE FROM order_items WHERE order_id = $1")
            .bind(*path).execute(&mut *tx).await?;

        // Recalculate totals from new items
        let new_total: f64 = new_items.iter().map(|i| i.unit_price * i.quantity as f64).sum();
        let total = rust_decimal::Decimal::try_from(new_total).unwrap_or_default();
        let discount = body.discount_amount
            .map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default())
            .unwrap_or(existing.discount_amount);
        let final_amt = total - discount;

        // Insert new items and deduct inventory
        for item in new_items {
            let product = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
                .bind(item.product_id).fetch_optional(&mut *tx).await?
                .ok_or_else(|| AppError::NotFound(format!("商品 {} 不存在", item.product_id)))?;
            if product.quantity < item.quantity {
                return Err(AppError::BadRequest(format!("商品「{}」库存不足 (可用: {}, 需要: {})", product.name, product.quantity, item.quantity)));
            }
            let sub = rust_decimal::Decimal::try_from(item.unit_price * item.quantity as f64).unwrap_or_default();
            let up = rust_decimal::Decimal::try_from(item.unit_price).unwrap_or_default();
            let allocs_json = if item.allocations.is_empty() {
                None
            } else {
                Some(serde_json::to_value(&item.allocations).unwrap_or_default())
            };
            sqlx::query(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal, warehouse_allocations) VALUES ($1,$2,$3,$4,$5,$6)"
            ).bind(*path).bind(item.product_id).bind(item.quantity).bind(up).bind(sub).bind(&allocs_json)
            .execute(&mut *tx).await?;

            sqlx::query("UPDATE products SET quantity = quantity - $1 WHERE id = $2")
                .bind(item.quantity).bind(item.product_id).execute(&mut *tx).await?;

            if !item.allocations.is_empty() {
                for alloc in &item.allocations {
                    sqlx::query(
                        "UPDATE warehouse_inventory SET quantity = quantity - $1, updated_at = NOW()
                         WHERE product_id = $2 AND warehouse_id = $3"
                    ).bind(alloc.quantity).bind(item.product_id).bind(alloc.warehouse_id)
                    .execute(&mut *tx).await?;
                }
            }
        }

        (total, discount, final_amt)
    } else {
        // No item change: keep existing total, apply discount delta from body
        let discount_val = body.discount_amount
            .map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default())
            .unwrap_or(existing.discount_amount);
        let final_val = existing.total_amount - discount_val;
        (existing.total_amount, discount_val, final_val)
    };

    // Single UPDATE — amounts are always correctly computed above
    let order = sqlx::query_as::<_, Order>(
        "UPDATE orders SET customer_id=$1, vehicle_info=$2, driver_info=$3, notes=$4,
         total_amount=$5, discount_amount=$6, final_amount=$7,
         discounts=COALESCE($8, orders.discounts) WHERE id=$9 RETURNING *"
    ).bind(customer).bind(vehicle).bind(driver).bind(notes)
     .bind(total_amount).bind(discount_amount).bind(final_amount)
     .bind(&discounts_json).bind(*path)
    .fetch_one(&mut *tx).await?;

    tx.commit().await?;

    let items = sqlx::query_as::<_, OrderItem>(
        "SELECT * FROM order_items WHERE order_id = $1"
    ).bind(order.id).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(OrderWithItems { order, items })))
}

pub async fn update_order_status(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateOrderStatusRequest>,
) -> Result<HttpResponse, AppError> {
    let valid = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"];
    if !valid.contains(&body.status.as_str()) {
        return Err(AppError::BadRequest("无效的订单状态".into()));
    }

    let existing = sqlx::query_as::<_, Order>("SELECT * FROM orders WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("订单不存在".into()))?;

    let mut tx = pool.begin().await?;

    let order = sqlx::query_as::<_, Order>(
        "UPDATE orders SET status = $1 WHERE id = $2 RETURNING *"
    ).bind(&body.status).bind(*path)
    .fetch_one(&mut *tx).await?;

    // Restore inventory when cancelled
    if body.status == "cancelled" {
        let items = sqlx::query_as::<_, OrderItem>(
            "SELECT * FROM order_items WHERE order_id = $1"
        ).bind(order.id).fetch_all(&mut *tx).await?;
        for item in &items {
            sqlx::query("UPDATE products SET quantity = quantity + $1 WHERE id = $2")
                .bind(item.quantity).bind(item.product_id).execute(&mut *tx).await?;
            // Restore to the most recently updated warehouse for this product
            let wi = sqlx::query_as::<_, crate::modules::inventory::models::WarehouseInventory>(
                "SELECT * FROM warehouse_inventory WHERE product_id = $1 ORDER BY updated_at DESC LIMIT 1"
            ).bind(item.product_id).fetch_optional(&mut *tx).await?;
            if let Some(w) = wi {
                sqlx::query(
                    "UPDATE warehouse_inventory SET quantity = quantity + $1, updated_at = NOW() WHERE id = $2"
                ).bind(item.quantity).bind(w.id).execute(&mut *tx).await?;
            }
        }
    }

    // When shipped: auto-create stock-out record
    if body.status == "shipped" {
        let items = sqlx::query_as::<_, OrderItem>(
            "SELECT * FROM order_items WHERE order_id = $1"
        ).bind(order.id).fetch_all(&mut *tx).await?;

        let warehouse = sqlx::query_as::<_, crate::modules::inventory::models::Warehouse>(
            "SELECT * FROM warehouses WHERE is_active = true ORDER BY name LIMIT 1"
        ).fetch_optional(&mut *tx).await?
        .ok_or_else(|| AppError::BadRequest("没有可用的仓库".into()))?;

        let operator_id = existing.salesperson_id.unwrap_or(existing.customer_id);
        let stock_out_no = format!("SOUT-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);

        let stock_out = sqlx::query_as::<_, crate::modules::inventory::models::StockOutRecord>(
            "INSERT INTO stock_out_records (stock_out_no, order_id, warehouse_id, operator_id, vehicle_info, driver_info, notes, status)
             VALUES ($1,$2,$3,$4,$5,$6,$7,'completed') RETURNING *"
        ).bind(&stock_out_no).bind(order.id).bind(warehouse.id).bind(operator_id)
         .bind(&order.vehicle_info).bind(&order.driver_info).bind("订单发货自动生成出库单")
        .fetch_one(&mut *tx).await?;

        for item in &items {
            let up_d = item.unit_price;
            sqlx::query(
                "INSERT INTO stock_out_items (stock_out_id, product_id, quantity, unit_price) VALUES ($1,$2,$3,$4)"
            ).bind(stock_out.id).bind(item.product_id).bind(item.quantity).bind(up_d)
            .execute(&mut *tx).await?;
        }
    }

    tx.commit().await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(order)))
}

// ═══════════════════════════════════════════════════════════
// BUNDLE SALES
// ═══════════════════════════════════════════════════════════

pub async fn list_bundles(
    pool: web::Data<PgPool>,
    query: web::Query<OrderListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM bundle_sales").fetch_one(pool.get_ref()).await?;
    let bundles = sqlx::query_as::<_, BundleSale>(
        "SELECT * FROM bundle_sales ORDER BY created_at DESC LIMIT $1 OFFSET $2"
    ).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(bundles, total.0, page, per_page))))
}

pub async fn get_bundle(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let bundle = sqlx::query_as::<_, BundleSale>("SELECT * FROM bundle_sales WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("捆绑销售不存在".into()))?;
    let items = sqlx::query_as::<_, BundleItem>("SELECT * FROM bundle_items WHERE bundle_id = $1")
        .bind(*path).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(BundleWithItems { bundle, items })))
}

pub async fn create_bundle(
    pool: web::Data<PgPool>,
    body: web::Json<CreateBundleRequest>,
) -> Result<HttpResponse, AppError> {
    let total_orig: f64 = body.items.iter().map(|i| i.unit_price * i.quantity as f64).sum();
    let orig_d = rust_decimal::Decimal::try_from(total_orig).unwrap_or_default();
    let price_d = rust_decimal::Decimal::try_from(body.bundle_price).unwrap_or_default();

    let mut tx = pool.begin().await?;

    let bundle = sqlx::query_as::<_, BundleSale>(
        "INSERT INTO bundle_sales (bundle_name, salesperson_id, merchant_id, customer_id, total_original_price, bundle_price, notes)
         VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *"
    ).bind(&body.bundle_name).bind(body.salesperson_id).bind(body.merchant_id)
     .bind(body.customer_id).bind(orig_d).bind(price_d).bind(&body.notes)
    .fetch_one(&mut *tx).await?;

    for item in &body.items {
        let up = rust_decimal::Decimal::try_from(item.unit_price).unwrap_or_default();
        sqlx::query(
            "INSERT INTO bundle_items (bundle_id, product_id, quantity, unit_price) VALUES ($1,$2,$3,$4)"
        ).bind(bundle.id).bind(item.product_id).bind(item.quantity).bind(up).execute(&mut *tx).await?;
    }

    tx.commit().await?;

    let items = sqlx::query_as::<_, BundleItem>("SELECT * FROM bundle_items WHERE bundle_id = $1")
        .bind(bundle.id).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(BundleWithItems { bundle, items })))
}

// ═══════════════════════════════════════════════════════════
// RETURNS
// ═══════════════════════════════════════════════════════════

pub async fn list_returns(
    pool: web::Data<PgPool>,
    query: web::Query<OrderListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;
    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM return_orders").fetch_one(pool.get_ref()).await?;
    let returns = sqlx::query_as::<_, ReturnOrder>(
        "SELECT * FROM return_orders ORDER BY created_at DESC LIMIT $1 OFFSET $2"
    ).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(returns, total.0, page, per_page))))
}

pub async fn get_return(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let ret = sqlx::query_as::<_, ReturnOrder>("SELECT * FROM return_orders WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("退单不存在".into()))?;
    let items = sqlx::query_as::<_, ReturnItem>("SELECT * FROM return_items WHERE return_id = $1")
        .bind(*path).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(ReturnWithItems { return_order: ret, items })))
}

pub async fn create_return(
    pool: web::Data<PgPool>,
    body: web::Json<CreateReturnRequest>,
) -> Result<HttpResponse, AppError> {
    let total_refund: f64 = body.items.iter().map(|i| i.refund_amount * i.quantity as f64).sum();
    let refund_d = rust_decimal::Decimal::try_from(total_refund).unwrap_or_default();
    let return_no = format!("RET-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);

    let mut tx = pool.begin().await?;

    let ret = sqlx::query_as::<_, ReturnOrder>(
        "INSERT INTO return_orders (return_no, order_id, salesperson_id, reason, total_refund_amount)
         VALUES ($1,$2,$3,$4,$5) RETURNING *"
    ).bind(&return_no).bind(body.order_id).bind(body.salesperson_id).bind(&body.reason).bind(refund_d)
    .fetch_one(&mut *tx).await?;

    for item in &body.items {
        let ra = rust_decimal::Decimal::try_from(item.refund_amount).unwrap_or_default();
        sqlx::query(
            "INSERT INTO return_items (return_id, product_id, quantity, refund_amount, reason_detail) VALUES ($1,$2,$3,$4,$5)"
        ).bind(ret.id).bind(item.product_id).bind(item.quantity).bind(ra).bind(&item.reason_detail)
        .execute(&mut *tx).await?;
    }

    tx.commit().await?;

    let items = sqlx::query_as::<_, ReturnItem>("SELECT * FROM return_items WHERE return_id = $1")
        .bind(ret.id).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(ReturnWithItems { return_order: ret, items })))
}

pub async fn update_return_status(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateReturnStatusRequest>,
) -> Result<HttpResponse, AppError> {
    let valid = ["pending", "approved", "rejected", "completed"];
    if !valid.contains(&body.status.as_str()) {
        return Err(AppError::BadRequest("无效的退单状态".into()));
    }
    let ret = sqlx::query_as::<_, ReturnOrder>(
        "UPDATE return_orders SET status = $1 WHERE id = $2 RETURNING *"
    ).bind(&body.status).bind(*path).fetch_optional(pool.get_ref()).await?
    .ok_or_else(|| AppError::NotFound("退单不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(ret)))
}

// ═══════════════════════════════════════════════════════════
// CATEGORIES
// ═══════════════════════════════════════════════════════════

pub async fn list_categories(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let cats = sqlx::query_as::<_, ProductCategory>(
        "SELECT * FROM categories WHERE is_active = true ORDER BY name"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(cats)))
}

pub async fn get_category(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let cat = sqlx::query_as::<_, ProductCategory>("SELECT * FROM categories WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("分类不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(cat)))
}

pub async fn create_category(
    pool: web::Data<PgPool>,
    body: web::Json<CreateCategoryRequest>,
) -> Result<HttpResponse, AppError> {
    let cat = sqlx::query_as::<_, ProductCategory>(
        "INSERT INTO categories (name, description) VALUES ($1,$2) RETURNING *"
    ).bind(&body.name).bind(&body.description).fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(cat)))
}

pub async fn update_category(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateCategoryRequest>,
) -> Result<HttpResponse, AppError> {
    let ex = sqlx::query_as::<_, ProductCategory>("SELECT * FROM categories WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("分类不存在".into()))?;
    let cat = sqlx::query_as::<_, ProductCategory>(
        "UPDATE categories SET name=$1,description=$2,is_active=$3 WHERE id=$4 RETURNING *"
    ).bind(body.name.as_deref().unwrap_or(&ex.name))
     .bind(body.description.as_deref().or(ex.description.as_deref()))
     .bind(body.is_active.unwrap_or(ex.is_active)).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(cat)))
}

pub async fn delete_category(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let rows = sqlx::query("DELETE FROM categories WHERE id = $1")
        .bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("分类不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

// ═══════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════

pub async fn dashboard(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let total_orders: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM orders").fetch_one(pool.get_ref()).await?;
    let total_revenue: (Option<rust_decimal::Decimal>,) = sqlx::query_as(
        "SELECT SUM(final_amount) FROM orders WHERE status = 'delivered'"
    ).fetch_one(pool.get_ref()).await?;
    let total_users: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users WHERE is_active = true").fetch_one(pool.get_ref()).await?;
    let total_products: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE is_active = true").fetch_one(pool.get_ref()).await?;

    let status_rows: Vec<StatusCount> = sqlx::query_as::<_, StatusCount>(
        "SELECT status, COUNT(*) as count FROM orders GROUP BY status ORDER BY status"
    ).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(SalesDashboard {
        total_orders: total_orders.0,
        total_revenue: total_revenue.0,
        total_users: total_users.0,
        total_products: total_products.0,
        orders_by_status: status_rows,
    })))
}
