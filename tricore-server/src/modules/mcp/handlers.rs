use actix_web::{web, HttpResponse};
use log::info;
use sqlx::PgPool;
use uuid::Uuid;

use crate::error::AppError;
use crate::dto::ApiResponse;
use crate::modules::mcp::client;
use crate::modules::mcp::models::*;

pub async fn list_servers(pool: web::Data<PgPool>) -> Result<HttpResponse, AppError> {
    let servers = sqlx::query_as::<_, McpServer>(
        "SELECT * FROM mcp_servers ORDER BY created_at DESC"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(servers)))
}

pub async fn create_server(
    pool: web::Data<PgPool>,
    body: web::Json<CreateMcpServerRequest>,
) -> Result<HttpResponse, AppError> {
    let server = sqlx::query_as::<_, McpServer>(
        "INSERT INTO mcp_servers (name, transport, command, args, url, is_enabled)
         VALUES ($1, $2, $3, $4, $5, $6) RETURNING *"
    )
    .bind(&body.name)
    .bind(&body.transport)
    .bind(&body.command)
    .bind(&body.args)
    .bind(&body.url)
    .bind(body.is_enabled)
    .fetch_one(pool.get_ref()).await?;

    info!("MCP server created: {}", server.name);
    refresh_all_servers(pool.get_ref()).await;
    Ok(HttpResponse::Ok().json(ApiResponse::success(server)))
}

pub async fn update_server(
    pool: web::Data<PgPool>,
    path: web::Path<Uuid>,
    body: web::Json<UpdateMcpServerRequest>,
) -> Result<HttpResponse, AppError> {
    let id = path.into_inner();
    let existing = sqlx::query_as::<_, McpServer>("SELECT * FROM mcp_servers WHERE id = $1")
        .bind(id).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("MCP 服务不存在".into()))?;

    let server = sqlx::query_as::<_, McpServer>(
        "UPDATE mcp_servers SET name=$1, transport=$2, command=$3, args=$4, url=$5, is_enabled=$6, updated_at=NOW()
         WHERE id=$7 RETURNING *"
    )
    .bind(body.name.as_deref().unwrap_or(&existing.name))
    .bind(body.transport.as_deref().unwrap_or(&existing.transport))
    .bind(body.command.as_ref().or(existing.command.as_ref()))
    .bind(body.args.as_ref().or(existing.args.as_ref()))
    .bind(body.url.as_ref().or(existing.url.as_ref()))
    .bind(body.is_enabled.unwrap_or(existing.is_enabled))
    .bind(id)
    .fetch_one(pool.get_ref()).await?;

    refresh_all_servers(pool.get_ref()).await;
    Ok(HttpResponse::Ok().json(ApiResponse::success(server)))
}

pub async fn delete_server(
    pool: web::Data<PgPool>,
    path: web::Path<Uuid>,
) -> Result<HttpResponse, AppError> {
    let id = path.into_inner();
    let result = sqlx::query("DELETE FROM mcp_servers WHERE id = $1")
        .bind(id).execute(pool.get_ref()).await?;
    if result.rows_affected() == 0 {
        return Err(AppError::NotFound("MCP 服务不存在".into()));
    }
    refresh_all_servers(pool.get_ref()).await;
    Ok(HttpResponse::Ok().json(ApiResponse::<()>::message("已删除")))
}

pub async fn list_tools(_pool: web::Data<PgPool>) -> Result<HttpResponse, AppError> {
    let tools = client::list_tools().await;
    Ok(HttpResponse::Ok().json(ApiResponse::success(tools)))
}

pub async fn refresh_servers(pool: web::Data<PgPool>) -> Result<HttpResponse, AppError> {
    refresh_all_servers(pool.get_ref()).await;
    let tools = client::list_tools().await;
    Ok(HttpResponse::Ok().json(ApiResponse::success(tools)))
}

pub(crate) async fn refresh_all_servers(pool: &PgPool) {
    let servers = sqlx::query_as::<_, McpServer>(
        "SELECT * FROM mcp_servers WHERE is_enabled = true"
    ).fetch_all(pool).await.unwrap_or_default();
    client::refresh_tools(&servers).await;
}
