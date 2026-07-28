mod ai;
mod auth;
mod inventory;
mod master_data;
mod oa;
mod regulation;
mod sales;

use actix_web::web;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .configure(ai::configure)
            .configure(auth::configure)
            .configure(sales::configure)
            .configure(oa::configure)
            .configure(inventory::configure)
            .configure(master_data::configure)
            .configure(regulation::configure),
    );
}
