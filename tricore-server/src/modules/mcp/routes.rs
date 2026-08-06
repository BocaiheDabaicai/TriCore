use actix_web::web;
use crate::modules::mcp::handlers;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/mcp")
            .route("/servers", web::get().to(handlers::list_servers))
            .route("/servers", web::post().to(handlers::create_server))
            .route("/servers/{id}", web::put().to(handlers::update_server))
            .route("/servers/{id}", web::delete().to(handlers::delete_server))
            .route("/tools", web::get().to(handlers::list_tools))
            .route("/refresh", web::post().to(handlers::refresh_servers)),
    );
}
