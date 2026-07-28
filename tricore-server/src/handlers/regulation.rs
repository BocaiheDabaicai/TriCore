use actix_web::{HttpResponse, web};
use actix_multipart::Multipart;
use futures_util::TryStreamExt;
use sqlx::PgPool;
use std::path::Path;
use uuid::Uuid;

use crate::error::AppError;
use crate::models::dto::{ApiResponse, PaginatedResponse};
use crate::models::regulation::*;

// ═══════════════════════════════════════════════════════════
// CATEGORIES
// ═══════════════════════════════════════════════════════════

pub async fn list_categories(
    pool: web::Data<PgPool>,
    query: web::Query<CategoryListQuery>,
) -> Result<HttpResponse, AppError> {
    let cats = if let Some(ref name) = query.name {
        sqlx::query_as::<_, RegulationCategory>(
            "SELECT * FROM regulation_categories WHERE name ILIKE $1 ORDER BY name"
        ).bind(format!("%{}%", name)).fetch_all(pool.get_ref()).await?
    } else {
        sqlx::query_as::<_, RegulationCategory>(
            "SELECT * FROM regulation_categories ORDER BY name"
        ).fetch_all(pool.get_ref()).await?
    };
    Ok(HttpResponse::Ok().json(ApiResponse::success(cats)))
}

pub async fn create_category(
    pool: web::Data<PgPool>,
    body: web::Json<CreateCategoryRequest>,
) -> Result<HttpResponse, AppError> {
    if body.name.trim().is_empty() {
        return Err(AppError::BadRequest("分类名称不能为空".into()));
    }
    let cat = sqlx::query_as::<_, RegulationCategory>(
        "INSERT INTO regulation_categories (name) VALUES ($1) RETURNING *"
    ).bind(&body.name).fetch_one(pool.get_ref()).await
        .map_err(|e: sqlx::Error| {
            if e.to_string().contains("unique") {
                AppError::BadRequest("该分类名称已存在".into())
            } else {
                AppError::from(e)
            }
        })?;
    Ok(HttpResponse::Created().json(ApiResponse::success(cat)))
}

pub async fn delete_category(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let rows = sqlx::query("DELETE FROM regulation_categories WHERE id = $1")
        .bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("分类不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

// ═══════════════════════════════════════════════════════════
// FILES
// ═══════════════════════════════════════════════════════════

pub async fn list_files(
    pool: web::Data<PgPool>,
    query: web::Query<FileListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut conditions: Vec<String> = vec![];
    let mut idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref title) = query.title {
        if !title.is_empty() {
            idx += 1;
            conditions.push(format!("rf.title ILIKE ${idx}"));
            params.push(format!("%{}%", title));
        }
    }
    if let Some(cid) = query.category_id {
        idx += 1;
        conditions.push(format!("rf.category_id = ${idx}::uuid"));
        params.push(cid.to_string());
    }

    let where_sql = if conditions.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", conditions.join(" AND "))
    };

    let count_sql = format!("SELECT COUNT(*) FROM regulation_files rf {where_sql}");
    let list_sql = format!(
        "SELECT rf.id, rf.title, rf.category_id, rc.name AS category_name, \
         rf.notes, rf.file_name, rf.file_size, rf.content_type, \
         rf.created_at, rf.updated_at \
         FROM regulation_files rf \
         LEFT JOIN regulation_categories rc ON rc.id = rf.category_id \
         {where_sql} ORDER BY rf.created_at DESC LIMIT ${0} OFFSET ${1}",
        idx + 1, idx + 2
    );

    let total: (i64,) = {
        let mut q = sqlx::query_as(&count_sql);
        for p in &params { q = q.bind(p); }
        q.fetch_one(pool.get_ref()).await?
    };

    let files: Vec<RegulationFileListItem> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params { q = q.bind(p); }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(files, total.0, page, per_page))))
}

pub async fn get_file(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let file = sqlx::query_as::<_, RegulationFile>(
        "SELECT * FROM regulation_files WHERE id = $1"
    ).bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("文件不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(file)))
}

pub async fn upload_file(
    pool: web::Data<PgPool>,
    upload_dir: web::Data<String>,
    mut payload: Multipart,
) -> Result<HttpResponse, AppError> {
    let mut title = String::new();
    let mut category_id: Option<Uuid> = None;
    let mut notes = String::new();
    let mut file_data: Option<(String, Vec<u8>, String)> = None;

    while let Ok(Some(mut field)) = payload.try_next().await {
        let disposition = field.content_disposition().cloned();
        let field_name = disposition.as_ref().and_then(|d| d.get_name()).unwrap_or("").to_string();

        let mut bytes = Vec::new();
        while let Ok(Some(chunk)) = field.try_next().await {
            bytes.extend_from_slice(&chunk);
        }

        match field_name.as_str() {
            "title" => title = String::from_utf8_lossy(&bytes).trim().to_string(),
            "category_id" => {
                let s = String::from_utf8_lossy(&bytes).trim().to_string();
                if !s.is_empty() {
                    category_id = Uuid::parse_str(&s).ok();
                }
            }
            "notes" => notes = String::from_utf8_lossy(&bytes).trim().to_string(),
            "file" => {
                let filename = disposition.as_ref()
                    .and_then(|d| d.get_filename())
                    .unwrap_or("unnamed").to_string();
                let content_type = field.content_type()
                    .map(|m| m.to_string())
                    .unwrap_or_else(|| "application/octet-stream".to_string());
                file_data = Some((filename, bytes, content_type));
            }
            _ => {}
        }
    }

    if title.is_empty() {
        return Err(AppError::BadRequest("文件标题不能为空".into()));
    }
    let (original_name, file_bytes, content_type) = file_data
        .ok_or_else(|| AppError::BadRequest("请选择要上传的文件".into()))?;
    if file_bytes.is_empty() {
        return Err(AppError::BadRequest("文件内容为空".into()));
    }

    let stored_name = format!("{}-{}", Uuid::new_v4(), &original_name);
    let dir = Path::new(upload_dir.as_str());
    tokio::fs::create_dir_all(dir).await?;
    tokio::fs::write(dir.join(&stored_name), &file_bytes).await?;

    let record = sqlx::query_as::<_, RegulationFile>(
        "INSERT INTO regulation_files (title, category_id, notes, file_name, file_path, file_size, content_type)
         VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *"
    ).bind(&title).bind(category_id).bind(&notes)
     .bind(&original_name).bind(&stored_name)
     .bind(file_bytes.len() as i64).bind(&content_type)
    .fetch_one(pool.get_ref()).await?;

    Ok(HttpResponse::Created().json(ApiResponse::success(record)))
}

pub async fn update_file(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateFileRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, RegulationFile>(
        "SELECT * FROM regulation_files WHERE id = $1"
    ).bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("文件不存在".into()))?;

    let title = body.title.as_deref().unwrap_or(&existing.title);
    let cat_id = body.category_id.or(existing.category_id);
    let notes = body.notes.as_deref().or(existing.notes.as_deref());

    let file = sqlx::query_as::<_, RegulationFile>(
        "UPDATE regulation_files SET title=$1, category_id=$2, notes=$3 WHERE id=$4 RETURNING *"
    ).bind(title).bind(cat_id).bind(notes).bind(*path)
    .fetch_one(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(file)))
}

pub async fn delete_file(
    pool: web::Data<PgPool>,
    upload_dir: web::Data<String>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let file = sqlx::query_as::<_, RegulationFile>(
        "SELECT * FROM regulation_files WHERE id = $1"
    ).bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("文件不存在".into()))?;

    let disk_path = Path::new(upload_dir.as_str()).join(&file.file_path);
    let _ = tokio::fs::remove_file(&disk_path).await;

    sqlx::query("DELETE FROM regulation_files WHERE id = $1")
        .bind(*path).execute(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}

pub async fn download_file(
    pool: web::Data<PgPool>,
    upload_dir: web::Data<String>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let file = sqlx::query_as::<_, RegulationFile>(
        "SELECT * FROM regulation_files WHERE id = $1"
    ).bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("文件不存在".into()))?;

    let disk_path = Path::new(upload_dir.as_str()).join(&file.file_path);
    let bytes = tokio::fs::read(&disk_path).await
        .map_err(|_| AppError::NotFound("文件在磁盘上未找到".into()))?;

    Ok(HttpResponse::Ok()
        .insert_header(("Content-Type", file.content_type.as_str()))
        .insert_header(("Content-Disposition", format!("inline; filename=\"{}\"", file.file_name)))
        .insert_header(("Content-Length", bytes.len().to_string()))
        .body(bytes))
}
