use actix_web::{HttpResponse, web};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::dto::{ApiResponse, PaginatedResponse};
use crate::models::inventory::*;
use crate::models::sales::Product;

// ═══════════════════════════════════════════════════════════
// WAREHOUSES
// ═══════════════════════════════════════════════════════════

pub async fn list_warehouses(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let warehouses = sqlx::query_as::<_, Warehouse>(
        "SELECT * FROM warehouses WHERE is_active = true ORDER BY name"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(warehouses)))
}

pub async fn get_warehouse(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let wh = sqlx::query_as::<_, Warehouse>("SELECT * FROM warehouses WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("仓库不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(wh)))
}

pub async fn create_warehouse(
    pool: web::Data<PgPool>,
    body: web::Json<CreateWarehouseRequest>,
) -> Result<HttpResponse, AppError> {
    let wh = sqlx::query_as::<_, Warehouse>(
        "INSERT INTO warehouses (name, location, manager_id) VALUES ($1,$2,$3) RETURNING *"
    ).bind(&body.name).bind(&body.location).bind(body.manager_id)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(wh)))
}

pub async fn update_warehouse(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateWarehouseRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, Warehouse>("SELECT * FROM warehouses WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("仓库不存在".into()))?;

    let name = body.name.as_deref().unwrap_or(&existing.name);
    let loc = body.location.as_deref().or(existing.location.as_deref());
    let mgr = body.manager_id.or(existing.manager_id);
    let active = body.is_active.unwrap_or(existing.is_active);

    let wh = sqlx::query_as::<_, Warehouse>(
        "UPDATE warehouses SET name=$1, location=$2, manager_id=$3, is_active=$4 WHERE id=$5 RETURNING *"
    ).bind(name).bind(loc).bind(mgr).bind(active).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(wh)))
}

pub async fn delete_warehouse(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let rows = sqlx::query("DELETE FROM warehouses WHERE id = $1")
        .bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("仓库不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

// ═══════════════════════════════════════════════════════════
// WAREHOUSE INVENTORY
// ═══════════════════════════════════════════════════════════

pub async fn get_warehouse_inventory(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let rows = sqlx::query_as::<_, WarehouseInventory>(
        "SELECT * FROM warehouse_inventory WHERE product_id = $1 ORDER BY quantity DESC"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    let mut result: Vec<WarehouseInventoryWithName> = vec![];
    for inv in rows {
        let wn: (String,) = sqlx::query_as("SELECT name FROM warehouses WHERE id = $1")
            .bind(inv.warehouse_id).fetch_one(pool.get_ref()).await
            .unwrap_or(("未知仓库".into(),));
        result.push(WarehouseInventoryWithName { inv, warehouse_name: wn.0 });
    }
    Ok(HttpResponse::Ok().json(ApiResponse::success(result)))
}

pub async fn adjust_inventory(
    pool: web::Data<PgPool>,
    body: web::Json<AdjustInventoryRequest>,
) -> Result<HttpResponse, AppError> {
    if body.adjustments.is_empty() {
        return Err(AppError::BadRequest("至少需要一个仓库调整项".into()));
    }

    let product = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
        .bind(body.product_id).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("商品不存在".into()))?;

    let mut stock_in_ids: Vec<Uuid> = vec![];
    let mut stock_out_ids: Vec<Uuid> = vec![];

    for adj in &body.adjustments {
        let current = sqlx::query_as::<_, WarehouseInventory>(
            "SELECT * FROM warehouse_inventory WHERE product_id = $1 AND warehouse_id = $2"
        ).bind(body.product_id).bind(adj.warehouse_id)
        .fetch_optional(pool.get_ref()).await?;

        let current_qty = current.as_ref().map(|c| c.quantity).unwrap_or(0);
        let delta = adj.quantity - current_qty;

        if delta == 0 {
            // Upsert warehouse_inventory to ensure row exists
            sqlx::query(
                "INSERT INTO warehouse_inventory (product_id, warehouse_id, quantity)
                 VALUES ($1,$2,$3)
                 ON CONFLICT (product_id, warehouse_id) DO UPDATE SET quantity = EXCLUDED.quantity, updated_at = NOW()"
            ).bind(body.product_id).bind(adj.warehouse_id).bind(adj.quantity)
            .execute(pool.get_ref()).await?;
            continue;
        }

        let notes = body.notes.clone().unwrap_or_else(|| {
            format!("库存调整: {} {} ({} → {})",
                product.name,
                if delta > 0 { "入库" } else { "出库" },
                current_qty, adj.quantity)
        });

        if delta > 0 {
            // Stock-in flow
            let stock_in_no = format!("SIN-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);
            let mut tx = pool.begin().await?;

            let record = sqlx::query_as::<_, StockInRecord>(
                "INSERT INTO stock_in_records (stock_in_no, warehouse_id, operator_id, notes)
                 VALUES ($1,$2,$3,$4) RETURNING *"
            ).bind(&stock_in_no).bind(adj.warehouse_id).bind(body.operator_id).bind(&notes)
            .fetch_one(&mut *tx).await?;

            sqlx::query(
                "INSERT INTO stock_in_items (stock_in_id, product_id, expected_quantity, actual_quantity)
                 VALUES ($1,$2,$3,$4)"
            ).bind(record.id).bind(body.product_id).bind(delta).bind(delta)
            .execute(&mut *tx).await?;

            // Verify + complete directly
            let items = sqlx::query_as::<_, StockInItem>(
                "SELECT * FROM stock_in_items WHERE stock_in_id = $1"
            ).bind(record.id).fetch_all(&mut *tx).await?;

            for item in &items {
                sqlx::query("UPDATE stock_in_items SET actual_quantity = $1 WHERE id = $2")
                    .bind(delta).bind(item.id).execute(&mut *tx).await?;
            }
            sqlx::query("UPDATE stock_in_records SET status='verified' WHERE id=$1")
                .bind(record.id).execute(&mut *tx).await?;
            sqlx::query("UPDATE products SET quantity = quantity + $1 WHERE id = $2")
                .bind(delta).bind(body.product_id).execute(&mut *tx).await?;
            sqlx::query("UPDATE stock_in_records SET status='completed' WHERE id=$1")
                .bind(record.id).execute(&mut *tx).await?;

            // Update warehouse_inventory
            sqlx::query(
                "INSERT INTO warehouse_inventory (product_id, warehouse_id, quantity)
                 VALUES ($1,$2,$3)
                 ON CONFLICT (product_id, warehouse_id) DO UPDATE SET quantity = warehouse_inventory.quantity + EXCLUDED.quantity, updated_at = NOW()"
            ).bind(body.product_id).bind(adj.warehouse_id).bind(delta)
            .execute(&mut *tx).await?;

            tx.commit().await?;
            stock_in_ids.push(record.id);
        } else {
            // Stock-out flow
            let out_qty = -delta;
            if current_qty < out_qty {
                return Err(AppError::BadRequest(
                    format!("仓库库存不足，当前 {} 件，尝试出库 {} 件", current_qty, out_qty)
                ));
            }
            let mut tx = pool.begin().await?;

            // Check product stock
            let prod = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
                .bind(body.product_id).fetch_optional(&mut *tx).await?
                .ok_or_else(|| AppError::NotFound("商品不存在".into()))?;
            if prod.quantity < out_qty {
                return Err(AppError::BadRequest(
                    format!("商品总库存不足 (可用: {}, 需要: {})", prod.quantity, out_qty)
                ));
            }

            let stock_out_no = format!("SOUT-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);
            let record = sqlx::query_as::<_, StockOutRecord>(
                "INSERT INTO stock_out_records (stock_out_no, warehouse_id, operator_id, notes)
                 VALUES ($1,$2,$3,$4) RETURNING *"
            ).bind(&stock_out_no).bind(adj.warehouse_id).bind(body.operator_id).bind(&notes)
            .fetch_one(&mut *tx).await?;

            sqlx::query(
                "INSERT INTO stock_out_items (stock_out_id, product_id, quantity)
                 VALUES ($1,$2,$3)"
            ).bind(record.id).bind(body.product_id).bind(out_qty)
            .execute(&mut *tx).await?;

            sqlx::query("UPDATE products SET quantity = quantity - $1 WHERE id = $2")
                .bind(out_qty).bind(body.product_id).execute(&mut *tx).await?;

            sqlx::query(
                "UPDATE warehouse_inventory SET quantity = quantity - $1, updated_at = NOW()
                 WHERE product_id = $2 AND warehouse_id = $3"
            ).bind(out_qty).bind(body.product_id).bind(adj.warehouse_id)
            .execute(&mut *tx).await?;

            tx.commit().await?;
            stock_out_ids.push(record.id);
        }
    }

    let mut parts: Vec<String> = vec![];
    if !stock_in_ids.is_empty() { parts.push(format!("入库 {} 条", stock_in_ids.len())); }
    if !stock_out_ids.is_empty() { parts.push(format!("出库 {} 条", stock_out_ids.len())); }

    Ok(HttpResponse::Ok().json(ApiResponse::success(AdjustInventoryResponse {
        stock_in_ids,
        stock_out_ids,
        message: format!("调整完成: {}", parts.join(", ")),
    })))
}

// ═══════════════════════════════════════════════════════════
// STOCK IN
// ═══════════════════════════════════════════════════════════

pub async fn list_stock_in(
    pool: web::Data<PgPool>,
    query: web::Query<StockInListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut conditions = vec!["1=1".to_string()];
    let mut idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref s) = query.status {
        idx += 1; conditions.push(format!("status = ${idx}")); params.push(s.clone());
    }
    if let Some(wid) = query.warehouse_id {
        idx += 1; conditions.push(format!("warehouse_id = ${idx}")); params.push(wid.to_string());
    }

    let where_sql = conditions.join(" AND ");
    let total: (i64,) = {
        let count_sql = format!("SELECT COUNT(*) FROM stock_in_records WHERE {where_sql}");
        let mut q = sqlx::query_as(&count_sql);
        for p in &params { q = q.bind(p); }
        q.fetch_one(pool.get_ref()).await?
    };

    let list_sql = format!(
        "SELECT * FROM stock_in_records WHERE {where_sql} ORDER BY created_at DESC LIMIT ${0} OFFSET ${1}",
        idx + 1, idx + 2
    );
    let records: Vec<StockInRecord> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params { q = q.bind(p); }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(records, total.0, page, per_page))))
}

pub async fn get_stock_in(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let record = sqlx::query_as::<_, StockInRecord>("SELECT * FROM stock_in_records WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("入库记录不存在".into()))?;
    let items = sqlx::query_as::<_, StockInItem>(
        "SELECT * FROM stock_in_items WHERE stock_in_id = $1"
    ).bind(*path).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(StockInWithItems { record, items })))
}

pub async fn create_stock_in(
    pool: web::Data<PgPool>,
    body: web::Json<CreateStockInRequest>,
) -> Result<HttpResponse, AppError> {
    if body.items.is_empty() {
        return Err(AppError::BadRequest("入库至少需要一个商品".into()));
    }
    let stock_in_no = format!("SIN-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);

    let mut tx = pool.begin().await?;

    let record = sqlx::query_as::<_, StockInRecord>(
        "INSERT INTO stock_in_records (stock_in_no, order_id, warehouse_id, operator_id, notes)
         VALUES ($1,$2,$3,$4,$5) RETURNING *"
    ).bind(&stock_in_no).bind(body.order_id).bind(body.warehouse_id)
     .bind(body.operator_id).bind(&body.notes)
    .fetch_one(&mut *tx).await?;

    for item in &body.items {
        let up = item.unit_price.map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default());
        sqlx::query(
            "INSERT INTO stock_in_items (stock_in_id, product_id, expected_quantity, actual_quantity, unit_price)
             VALUES ($1,$2,$3,$4,$5)"
        ).bind(record.id).bind(item.product_id).bind(item.expected_quantity).bind(item.actual_quantity).bind(up)
        .execute(&mut *tx).await?;
    }

    tx.commit().await?;

    let items = sqlx::query_as::<_, StockInItem>(
        "SELECT * FROM stock_in_items WHERE stock_in_id = $1"
    ).bind(record.id).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Created().json(ApiResponse::success(StockInWithItems { record, items })))
}

pub async fn verify_stock_in(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<VerifyStockInRequest>,
) -> Result<HttpResponse, AppError> {
    let record = sqlx::query_as::<_, StockInRecord>("SELECT * FROM stock_in_records WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("入库记录不存在".into()))?;

    if record.status != "pending" {
        return Err(AppError::BadRequest("只有待处理的入库单才能盘点".into()));
    }

    let mut tx = pool.begin().await?;
    for vi in &body.items {
        sqlx::query(
            "UPDATE stock_in_items SET actual_quantity = $1 WHERE id = $2 AND stock_in_id = $3"
        ).bind(vi.actual_quantity).bind(vi.item_id).bind(*path).execute(&mut *tx).await?;
    }
    sqlx::query("UPDATE stock_in_records SET status='verified' WHERE id=$1")
        .bind(*path).execute(&mut *tx).await?;
    tx.commit().await?;

    let updated = sqlx::query_as::<_, StockInRecord>("SELECT * FROM stock_in_records WHERE id = $1")
        .bind(*path).fetch_one(pool.get_ref()).await?;
    let items = sqlx::query_as::<_, StockInItem>(
        "SELECT * FROM stock_in_items WHERE stock_in_id = $1"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(StockInWithItems { record: updated, items })))
}

pub async fn complete_stock_in(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let record = sqlx::query_as::<_, StockInRecord>("SELECT * FROM stock_in_records WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("入库记录不存在".into()))?;

    if record.status != "verified" {
        return Err(AppError::BadRequest("只有已盘点的入库单才能确认入库".into()));
    }

    let mut tx = pool.begin().await?;
    let items = sqlx::query_as::<_, StockInItem>(
        "SELECT * FROM stock_in_items WHERE stock_in_id = $1"
    ).bind(*path).fetch_all(&mut *tx).await?;

    for item in &items {
        sqlx::query("UPDATE products SET quantity = quantity + $1 WHERE id = $2")
            .bind(item.actual_quantity).bind(item.product_id).execute(&mut *tx).await?;
        sqlx::query(
            "INSERT INTO warehouse_inventory (product_id, warehouse_id, quantity)
             VALUES ($1,$2,$3)
             ON CONFLICT (product_id, warehouse_id) DO UPDATE SET quantity = warehouse_inventory.quantity + EXCLUDED.quantity, updated_at = NOW()"
        ).bind(item.product_id).bind(record.warehouse_id).bind(item.actual_quantity)
        .execute(&mut *tx).await?;
    }

    sqlx::query("UPDATE stock_in_records SET status='completed' WHERE id=$1")
        .bind(*path).execute(&mut *tx).await?;
    tx.commit().await?;

    let updated = sqlx::query_as::<_, StockInRecord>("SELECT * FROM stock_in_records WHERE id = $1")
        .bind(*path).fetch_one(pool.get_ref()).await?;
    let items = sqlx::query_as::<_, StockInItem>(
        "SELECT * FROM stock_in_items WHERE stock_in_id = $1"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(StockInWithItems { record: updated, items })))
}

// ═══════════════════════════════════════════════════════════
// STOCK OUT
// ═══════════════════════════════════════════════════════════

pub async fn list_stock_out(
    pool: web::Data<PgPool>,
    query: web::Query<StockOutListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut conditions = vec!["1=1".to_string()];
    let mut idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref s) = query.status {
        idx += 1; conditions.push(format!("status = ${idx}")); params.push(s.clone());
    }
    if let Some(wid) = query.warehouse_id {
        idx += 1; conditions.push(format!("warehouse_id = ${idx}")); params.push(wid.to_string());
    }

    let where_sql = conditions.join(" AND ");
    let total: (i64,) = {
        let count_sql = format!("SELECT COUNT(*) FROM stock_out_records WHERE {where_sql}");
        let mut q = sqlx::query_as(&count_sql);
        for p in &params { q = q.bind(p); }
        q.fetch_one(pool.get_ref()).await?
    };

    let list_sql = format!(
        "SELECT * FROM stock_out_records WHERE {where_sql} ORDER BY created_at DESC LIMIT ${0} OFFSET ${1}",
        idx + 1, idx + 2
    );
    let records: Vec<StockOutRecord> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params { q = q.bind(p); }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(records, total.0, page, per_page))))
}

pub async fn get_stock_out(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let record = sqlx::query_as::<_, StockOutRecord>("SELECT * FROM stock_out_records WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("出库记录不存在".into()))?;
    let items = sqlx::query_as::<_, StockOutItem>(
        "SELECT * FROM stock_out_items WHERE stock_out_id = $1"
    ).bind(*path).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(StockOutWithItems { record, items })))
}

pub async fn create_stock_out(
    pool: web::Data<PgPool>,
    body: web::Json<CreateStockOutRequest>,
) -> Result<HttpResponse, AppError> {
    if body.items.is_empty() {
        return Err(AppError::BadRequest("出库至少需要一个商品".into()));
    }
    let stock_out_no = format!("SOUT-{}-{:06}", chrono::Utc::now().format("%Y%m%d"), rand::random::<u16>() % 10000);

    let mut tx = pool.begin().await?;

    // Check stock availability
    for item in &body.items {
        let product = sqlx::query_as::<_, Product>("SELECT * FROM products WHERE id = $1")
            .bind(item.product_id).fetch_optional(&mut *tx).await?
            .ok_or_else(|| AppError::NotFound(format!("商品 {} 不存在", item.product_id)))?;
        if product.quantity < item.quantity {
            return Err(AppError::BadRequest(format!("商品 {} 库存不足 (可用: {}, 需要: {})", product.name, product.quantity, item.quantity)));
        }
    }

    let record = sqlx::query_as::<_, StockOutRecord>(
        "INSERT INTO stock_out_records (stock_out_no, order_id, warehouse_id, operator_id, vehicle_info, driver_info, notes)
         VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *"
    ).bind(&stock_out_no).bind(body.order_id).bind(body.warehouse_id)
     .bind(body.operator_id).bind(&body.vehicle_info).bind(&body.driver_info).bind(&body.notes)
    .fetch_one(&mut *tx).await?;

    for item in &body.items {
        let up = item.unit_price.map(|v| rust_decimal::Decimal::try_from(v).unwrap_or_default());
        sqlx::query(
            "INSERT INTO stock_out_items (stock_out_id, product_id, quantity, unit_price) VALUES ($1,$2,$3,$4)"
        ).bind(record.id).bind(item.product_id).bind(item.quantity).bind(up).execute(&mut *tx).await?;

        sqlx::query("UPDATE products SET quantity = quantity - $1 WHERE id = $2")
            .bind(item.quantity).bind(item.product_id).execute(&mut *tx).await?;

        sqlx::query(
            "UPDATE warehouse_inventory SET quantity = quantity - $1, updated_at = NOW()
             WHERE product_id = $2 AND warehouse_id = $3 AND quantity >= $1"
        ).bind(item.quantity).bind(item.product_id).bind(record.warehouse_id)
        .execute(&mut *tx).await?;
    }

    tx.commit().await?;

    let items = sqlx::query_as::<_, StockOutItem>(
        "SELECT * FROM stock_out_items WHERE stock_out_id = $1"
    ).bind(record.id).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Created().json(ApiResponse::success(StockOutWithItems { record, items })))
}

pub async fn ship_stock_out(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<ShipStockOutRequest>,
) -> Result<HttpResponse, AppError> {
    let record = sqlx::query_as::<_, StockOutRecord>("SELECT * FROM stock_out_records WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("出库记录不存在".into()))?;

    if record.status != "pending" {
        return Err(AppError::BadRequest("只有待处理的出库单才能发货".into()));
    }

    let vi = body.vehicle_info.as_deref().or(record.vehicle_info.as_deref());
    let di = body.driver_info.as_deref().or(record.driver_info.as_deref());

    let updated = sqlx::query_as::<_, StockOutRecord>(
        "UPDATE stock_out_records SET status='shipped', vehicle_info=$1, driver_info=$2, shipped_at=NOW()
         WHERE id=$3 RETURNING *"
    ).bind(vi).bind(di).bind(*path).fetch_one(pool.get_ref()).await?;

    let items = sqlx::query_as::<_, StockOutItem>(
        "SELECT * FROM stock_out_items WHERE stock_out_id = $1"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(StockOutWithItems { record: updated, items })))
}

pub async fn deliver_stock_out(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let record = sqlx::query_as::<_, StockOutRecord>("SELECT * FROM stock_out_records WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("出库记录不存在".into()))?;

    if record.status != "shipped" {
        return Err(AppError::BadRequest("只有已发货的出库单才能确认送达".into()));
    }

    let updated = sqlx::query_as::<_, StockOutRecord>(
        "UPDATE stock_out_records SET status='delivered' WHERE id=$1 RETURNING *"
    ).bind(*path).fetch_one(pool.get_ref()).await?;

    let items = sqlx::query_as::<_, StockOutItem>(
        "SELECT * FROM stock_out_items WHERE stock_out_id = $1"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(StockOutWithItems { record: updated, items })))
}

// ═══════════════════════════════════════════════════════════
// ISSUES
// ═══════════════════════════════════════════════════════════

pub async fn list_issues(
    pool: web::Data<PgPool>,
    query: web::Query<IssueListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut conditions = vec!["1=1".to_string()];
    let mut idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref s) = query.status {
        idx += 1; conditions.push(format!("status = ${idx}")); params.push(s.clone());
    }
    if let Some(ref sev) = query.severity {
        idx += 1; conditions.push(format!("severity = ${idx}")); params.push(sev.clone());
    }

    let where_sql = conditions.join(" AND ");
    let total: (i64,) = {
        let count_sql = format!("SELECT COUNT(*) FROM issues WHERE {where_sql}");
        let mut q = sqlx::query_as(&count_sql);
        for p in &params { q = q.bind(p); }
        q.fetch_one(pool.get_ref()).await?
    };

    let list_sql = format!(
        "SELECT * FROM issues WHERE {where_sql} ORDER BY created_at DESC LIMIT ${0} OFFSET ${1}",
        idx + 1, idx + 2
    );
    let issues: Vec<Issue> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params { q = q.bind(p); }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(issues, total.0, page, per_page))))
}

pub async fn get_issue(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let issue = sqlx::query_as::<_, Issue>("SELECT * FROM issues WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("问题不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(issue)))
}

pub async fn create_issue(
    pool: web::Data<PgPool>,
    body: web::Json<CreateIssueRequest>,
) -> Result<HttpResponse, AppError> {
    let severity = body.severity.clone().unwrap_or_else(|| "medium".into());
    let issue = sqlx::query_as::<_, Issue>(
        "INSERT INTO issues (related_type, related_id, description, severity, reported_by, assigned_to)
         VALUES ($1,$2,$3,$4,$5,$6) RETURNING *"
    ).bind(&body.related_type).bind(body.related_id).bind(&body.description)
     .bind(&severity).bind(body.reported_by).bind(body.assigned_to)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(issue)))
}

pub async fn update_issue(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateIssueRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, Issue>("SELECT * FROM issues WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("问题不存在".into()))?;

    let desc = body.description.as_deref().unwrap_or(&existing.description);
    let sev = body.severity.as_deref().unwrap_or(&existing.severity);
    let status = body.status.as_deref().unwrap_or(&existing.status);
    let assigned = body.assigned_to.or(existing.assigned_to);

    let issue = sqlx::query_as::<_, Issue>(
        "UPDATE issues SET description=$1, severity=$2, status=$3, assigned_to=$4 WHERE id=$5 RETURNING *"
    ).bind(desc).bind(sev).bind(status).bind(assigned).bind(*path).fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(issue)))
}

pub async fn resolve_issue(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<ResolveIssueRequest>,
) -> Result<HttpResponse, AppError> {
    let issue = sqlx::query_as::<_, Issue>("SELECT * FROM issues WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("问题不存在".into()))?;

    if issue.status == "resolved" || issue.status == "closed" {
        return Err(AppError::BadRequest("问题已解决或已关闭".into()));
    }

    let updated = sqlx::query_as::<_, Issue>(
        "UPDATE issues SET status='resolved', resolution=$1, resolved_at=NOW() WHERE id=$2 RETURNING *"
    ).bind(&body.resolution).bind(*path).fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(updated)))
}

// ═══════════════════════════════════════════════════════════
// PRODUCTS (inventory view)
// ═══════════════════════════════════════════════════════════

pub async fn list_products(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let products = sqlx::query_as::<_, Product>(
        "SELECT * FROM products WHERE is_active = true ORDER BY quantity ASC"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(products)))
}

// ═══════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════

pub async fn dashboard(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let total_prod: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE is_active = true").fetch_one(pool.get_ref()).await?;
    let low_stock: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE quantity < 50 AND is_active = true").fetch_one(pool.get_ref()).await?;
    let total_si: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM stock_in_records").fetch_one(pool.get_ref()).await?;
    let total_so: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM stock_out_records").fetch_one(pool.get_ref()).await?;
    let open_issues: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM issues WHERE status IN ('open', 'in_progress')").fetch_one(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(InventoryDashboard {
        total_products: total_prod.0,
        low_stock_count: low_stock.0,
        total_stock_in: total_si.0,
        total_stock_out: total_so.0,
        open_issues: open_issues.0,
    })))
}
