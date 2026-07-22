mod auth;
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

    let jwt_secret = cfg.jwt_secret.clone();

    HttpServer::new(move || {
        let cors = Cors::permissive();

        App::new()
            .wrap(cors)
            .wrap(middleware::Logger::default())
            .wrap(middleware::from_fn(auth::auth_middleware))
            .app_data(web::Data::new(pool.clone()))
            .app_data(web::Data::new(jwt_secret.clone()))
            .configure(routes::configure)
    })
    .bind(format!("{}:{}", cfg.server_host, cfg.server_port))?
    .run()
    .await
}
