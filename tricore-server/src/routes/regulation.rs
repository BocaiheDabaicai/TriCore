use actix_web::web;
use crate::handlers::regulation;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/regulations")
            .app_data(web::PayloadConfig::new(50 * 1024 * 1024))
            // Categories
            .route("/categories", web::get().to(regulation::list_categories))
            .route("/categories", web::post().to(regulation::create_category))
            .route("/categories/{id}", web::delete().to(regulation::delete_category))
            // Files
            .route("/files", web::get().to(regulation::list_files))
            .route("/files/{id}/download", web::get().to(regulation::download_file))
            .route("/files/{id}", web::get().to(regulation::get_file))
            .route("/files", web::post().to(regulation::upload_file))
            .route("/files/{id}", web::put().to(regulation::update_file))
            .route("/files/{id}", web::delete().to(regulation::delete_file)),
    );
}
