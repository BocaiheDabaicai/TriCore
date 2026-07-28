use actix_web::web;
use crate::handlers::inventory;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/inventory")
            // Warehouse Inventory
            .route("/warehouse-inventory/{product_id}", web::get().to(inventory::get_warehouse_inventory))
            .route("/adjust", web::post().to(inventory::adjust_inventory))
            // Warehouses
            .route("/warehouses", web::get().to(inventory::list_warehouses))
            .route("/warehouses/{id}", web::get().to(inventory::get_warehouse))
            .route("/warehouses", web::post().to(inventory::create_warehouse))
            .route("/warehouses/{id}", web::put().to(inventory::update_warehouse))
            .route("/warehouses/{id}", web::delete().to(inventory::delete_warehouse))
            // Stock In
            .route("/stock-in", web::get().to(inventory::list_stock_in))
            .route("/stock-in/{id}", web::get().to(inventory::get_stock_in))
            .route("/stock-in", web::post().to(inventory::create_stock_in))
            .route("/stock-in/{id}/verify", web::put().to(inventory::verify_stock_in))
            .route("/stock-in/{id}/complete", web::put().to(inventory::complete_stock_in))
            // Stock Out
            .route("/stock-out", web::get().to(inventory::list_stock_out))
            .route("/stock-out/{id}", web::get().to(inventory::get_stock_out))
            .route("/stock-out", web::post().to(inventory::create_stock_out))
            .route("/stock-out/{id}/ship", web::put().to(inventory::ship_stock_out))
            .route("/stock-out/{id}/deliver", web::put().to(inventory::deliver_stock_out))
            // Issues
            .route("/issues", web::get().to(inventory::list_issues))
            .route("/issues/{id}", web::get().to(inventory::get_issue))
            .route("/issues", web::post().to(inventory::create_issue))
            .route("/issues/{id}", web::put().to(inventory::update_issue))
            .route("/issues/{id}/resolve", web::put().to(inventory::resolve_issue))
            // Products (inventory view)
            .route("/products", web::get().to(inventory::list_products))
            // Dashboard
            .route("/dashboard", web::get().to(inventory::dashboard)),
    );
}
