use actix_web::web;
use crate::handlers::ai;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/ai")
            .route("/config", web::get().to(ai::get_config))
            .route("/config", web::put().to(ai::update_config))
            .route("/chat", web::post().to(ai::chat)),
    );
}
