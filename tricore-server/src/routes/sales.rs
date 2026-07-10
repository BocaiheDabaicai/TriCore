use actix_web::web;
use crate::handlers::sales;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/sales")
            // Auth
            .route("/auth/login", web::post().to(sales::login))
            // Users
            .route("/users", web::get().to(sales::list_users))
            .route("/users/{id}", web::get().to(sales::get_user))
            .route("/users", web::post().to(sales::create_user))
            .route("/users/{id}", web::put().to(sales::update_user))
            // Products
            .route("/products", web::get().to(sales::list_products))
            .route("/products/{id}", web::get().to(sales::get_product))
            .route("/products", web::post().to(sales::create_product))
            .route("/products/{id}", web::put().to(sales::update_product))
            // Orders
            .route("/orders", web::get().to(sales::list_orders))
            .route("/orders/{id}", web::get().to(sales::get_order))
            .route("/orders", web::post().to(sales::create_order))
            .route("/orders/{id}", web::put().to(sales::update_order))
            .route("/orders/{id}/status", web::patch().to(sales::update_order_status))
            // Bundle Sales
            .route("/bundles", web::get().to(sales::list_bundles))
            .route("/bundles/{id}", web::get().to(sales::get_bundle))
            .route("/bundles", web::post().to(sales::create_bundle))
            // Returns
            .route("/returns", web::get().to(sales::list_returns))
            .route("/returns/{id}", web::get().to(sales::get_return))
            .route("/returns", web::post().to(sales::create_return))
            .route("/returns/{id}/status", web::patch().to(sales::update_return_status))
            // Dashboard
            .route("/dashboard", web::get().to(sales::dashboard)),
    );
}
