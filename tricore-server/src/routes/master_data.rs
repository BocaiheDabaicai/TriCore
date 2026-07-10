use actix_web::web;
use crate::handlers::master_data as md;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/master-data")
            .route("/customers", web::get().to(md::list_customers))
            .route("/customers/{id}", web::get().to(md::get_customer))
            .route("/customers", web::post().to(md::create_customer))
            .route("/customers/{id}", web::put().to(md::update_customer))
            .route("/customers/{id}", web::delete().to(md::delete_customer))
            .route("/departments", web::get().to(md::list_departments))
            .route("/departments/{id}", web::get().to(md::get_department))
            .route("/departments", web::post().to(md::create_department))
            .route("/departments/{id}", web::put().to(md::update_department))
            .route("/departments/{id}", web::delete().to(md::delete_department))
            .route("/positions", web::get().to(md::list_positions))
            .route("/positions/{id}", web::get().to(md::get_position))
            .route("/positions", web::post().to(md::create_position))
            .route("/positions/{id}", web::put().to(md::update_position))
            .route("/positions/{id}", web::delete().to(md::delete_position))
            .route("/vehicles", web::get().to(md::list_vehicles))
            .route("/vehicles/{id}", web::get().to(md::get_vehicle))
            .route("/vehicles", web::post().to(md::create_vehicle))
            .route("/vehicles/{id}", web::put().to(md::update_vehicle))
            .route("/vehicles/{id}", web::delete().to(md::delete_vehicle)),
    );
}
