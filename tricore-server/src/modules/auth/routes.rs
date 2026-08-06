use actix_web::web;
use super::handlers as auth;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/auth")
            .route("/login", web::post().to(auth::login))
            .route("/me", web::get().to(auth::me)),
    );
}
