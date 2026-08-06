use actix_web::{web, HttpResponse};
use log::{error, info};
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::dto::ApiResponse;
use crate::modules::data_snapshot::models::*;

/// Core snapshot creation — also used by the background task.
pub async fn create_snapshot(
    pool: &PgPool,
    notes: Option<String>,
) -> Result<DataSnapshot, AppError> {
    let snapshot_time = chrono::Utc::now();

    // Insert placeholder row
    let row = sqlx::query_as::<_, DataSnapshot>(
        "INSERT INTO data_snapshots (snapshot_time, status, notes)
         VALUES ($1, 'in_progress', $2)
         RETURNING id, snapshot_time, table_count, status, notes, created_at",
    )
    .bind(snapshot_time)
    .bind(&notes)
    .fetch_one(pool)
    .await?;

    let snapshot_id = row.id;

    // Capture all tables
    let mut tables_data = serde_json::Map::new();
    let mut table_count = 0i32;

    for table_name in TABLE_INSERT_ORDER {
        let query = format!(
            "SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) FROM (SELECT * FROM {}) t",
            table_name
        );
        let result: (serde_json::Value,) = sqlx::query_as(&query).fetch_one(pool).await?;
        tables_data.insert(table_name.to_string(), result.0);
        table_count += 1;
    }

    let snapshot_data = serde_json::json!({ "tables": tables_data });

    // Update with data and mark completed
    let updated = sqlx::query_as::<_, DataSnapshot>(
        "UPDATE data_snapshots
         SET snapshot_data = $1, table_count = $2, status = 'completed'
         WHERE id = $3
         RETURNING id, snapshot_time, table_count, status, notes, created_at",
    )
    .bind(&snapshot_data)
    .bind(table_count)
    .bind(snapshot_id)
    .fetch_one(pool)
    .await?;

    // Enforce 12-snapshot limit
    enforce_limit(pool, MAX_SNAPSHOTS).await;

    info!("Snapshot {} created with {} tables", snapshot_id, table_count);
    Ok(updated)
}

pub async fn list_snapshots(pool: web::Data<PgPool>) -> Result<HttpResponse, AppError> {
    let snapshots = sqlx::query_as::<_, DataSnapshot>(
        "SELECT id, snapshot_time, table_count, status, notes, created_at
         FROM data_snapshots ORDER BY created_at DESC",
    )
    .fetch_all(pool.get_ref())
    .await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(snapshots)))
}

pub async fn create_snapshot_handler(
    pool: web::Data<PgPool>,
    body: Option<web::Json<CreateSnapshotRequest>>,
) -> Result<HttpResponse, AppError> {
    let notes = body.and_then(|b| b.notes.clone());
    let snapshot = create_snapshot(pool.get_ref(), notes).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(snapshot)))
}

pub async fn restore_snapshot(
    pool: web::Data<PgPool>,
    path: web::Path<Uuid>,
    body: web::Json<RestoreConfirm>,
) -> Result<HttpResponse, AppError> {
    if !body.confirm {
        return Err(AppError::BadRequest("请确认恢复操作（confirm: true）".into()));
    }

    let snapshot_id = path.into_inner();

    // Load snapshot with data
    let snapshot = sqlx::query_as::<_, DataSnapshotFull>(
        "SELECT * FROM data_snapshots WHERE id = $1",
    )
    .bind(snapshot_id)
    .fetch_optional(pool.get_ref())
    .await?
    .ok_or_else(|| AppError::NotFound("快照不存在".into()))?;

    let tables = snapshot
        .snapshot_data
        .get("tables")
        .and_then(|v| v.as_object())
        .ok_or_else(|| AppError::Internal("快照数据格式异常".into()))?;

    // Begin transaction
    let mut tx = pool.begin().await?;

    // DELETE in reverse order (children before parents)
    let delete_order: Vec<&str> = TABLE_INSERT_ORDER.iter().rev().copied().collect();
    for table_name in &delete_order {
        let query = format!("DELETE FROM {}", table_name);
        sqlx::query(&query).execute(&mut *tx).await?;
    }

    // INSERT in order (parents before children)
    for table_name in TABLE_INSERT_ORDER {
        if let Some(rows) = tables.get(*table_name) {
            if rows.as_array().map_or(true, |a| a.is_empty()) {
                continue;
            }
            let query = format!(
                "INSERT INTO {} SELECT * FROM jsonb_populate_recordset(null::{}, $1::jsonb)",
                table_name, table_name
            );
            sqlx::query(&query).bind(rows).execute(&mut *tx).await?;
        }
    }

    tx.commit().await?;

    info!("Restored database from snapshot {}", snapshot_id);
    Ok(HttpResponse::Ok().json(ApiResponse::<()>::message("数据恢复成功")))
}

pub async fn delete_snapshot(
    pool: web::Data<PgPool>,
    path: web::Path<Uuid>,
) -> Result<HttpResponse, AppError> {
    let snapshot_id = path.into_inner();

    let result = sqlx::query("DELETE FROM data_snapshots WHERE id = $1")
        .bind(snapshot_id)
        .execute(pool.get_ref())
        .await?;

    if result.rows_affected() == 0 {
        return Err(AppError::NotFound("快照不存在".into()));
    }

    Ok(HttpResponse::Ok().json(ApiResponse::<()>::message("快照已删除")))
}

async fn enforce_limit(pool: &PgPool, max: i64) {
    let result = sqlx::query(
        "DELETE FROM data_snapshots
         WHERE id NOT IN (
             SELECT id FROM data_snapshots
             ORDER BY created_at DESC LIMIT $1
         )",
    )
    .bind(max)
    .execute(pool)
    .await;

    match result {
        Ok(r) => {
            if r.rows_affected() > 0 {
                info!("Cleaned up {} old snapshot(s)", r.rows_affected());
            }
        }
        Err(e) => error!("Failed to clean up old snapshots: {}", e),
    }
}
