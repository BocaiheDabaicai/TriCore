mod auth;
mod config;
mod db;
mod dto;
mod error;
mod modules;

use actix_cors::Cors;
use actix_web::{App, HttpServer, middleware, web};
use log::info;
use std::time::Duration;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenvy::dotenv().ok();
    env_logger::init();

    let cfg = config::Config::from_env();
    let pool = db::create_pool(&cfg.database_url).await;

    db::run_migrations(&pool).await;

    // Refresh MCP tools on startup
    modules::mcp::handlers::refresh_all_servers(&pool).await;

    // Background snapshot task
    let snapshot_pool = pool.clone();
    let interval = cfg.snapshot_interval_secs;
    tokio::spawn(async move {
        info!("Auto-snapshot task started (interval: {}s, max: {})", interval, modules::data_snapshot::models::MAX_SNAPSHOTS);
        loop {
            tokio::time::sleep(Duration::from_secs(interval)).await;
            match modules::data_snapshot::handlers::create_snapshot(&snapshot_pool, Some("auto".into())).await {
                Ok(s) => info!("Auto-snapshot completed: id={}, tables={}", s.id, s.table_count),
                Err(e) => log::error!("Auto-snapshot failed: {}", e),
            }
        }
    });

    info!("TriCore Server starting on {}:{}", cfg.server_host, cfg.server_port);

    let jwt_secret = cfg.jwt_secret.clone();
    let upload_dir = cfg.upload_dir.clone();
    let server_port = cfg.server_port.to_string();

    HttpServer::new(move || {
        let cors = Cors::permissive();

        App::new()
            .wrap(cors)
            .wrap(middleware::Logger::default())
            .wrap(middleware::from_fn(auth::auth_middleware))
            .app_data(web::Data::new(pool.clone()))
            .app_data(web::Data::new(jwt_secret.clone()))
            .app_data(web::Data::new(upload_dir.clone()))
            .app_data(web::Data::new(server_port.clone()))
            .configure(modules::configure)
    })
    .bind(format!("{}:{}", cfg.server_host, cfg.server_port))?
    .run()
    .await
}
