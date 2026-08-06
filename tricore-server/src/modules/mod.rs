pub mod ai;
pub mod auth;
pub mod data_snapshot;
pub mod inventory;
pub mod master_data;
pub mod mcp;
pub mod oa;
pub mod regulation;
pub mod sales;

use actix_web::web;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .configure(ai::routes::configure)
            .configure(auth::routes::configure)
            .configure(sales::routes::configure)
            .configure(oa::routes::configure)
            .configure(inventory::routes::configure)
            .configure(master_data::routes::configure)
            .configure(regulation::routes::configure)
            .configure(data_snapshot::routes::configure)
            .configure(mcp::routes::configure),
    );
}
