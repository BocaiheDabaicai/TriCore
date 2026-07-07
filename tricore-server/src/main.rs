mod config;
mod db;
mod error;
mod handlers;
mod models;
mod routes;

use actix_cors::Cors;
use actix_web::{App, HttpServer, middleware, web};
use log::info;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenvy::dotenv().ok();
    env_logger::init();

    let cfg = config::Config::from_env();
    let pool = db::create_pool(&cfg.database_url).await;

    db::run_migrations(&pool).await;

    info!("TriCore Server starting on {}:{}", cfg.server_host, cfg.server_port);

    HttpServer::new(move || {
        let cors = Cors::permissive();

        App::new()
            .wrap(cors)
            .wrap(middleware::Logger::default())
            .app_data(web::Data::new(pool.clone()))
            .configure(routes::configure)
    })
    .bind(format!("{}:{}", cfg.server_host, cfg.server_port))?
    .run()
    .await
}
