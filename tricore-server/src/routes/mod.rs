mod inventory;
mod oa;
mod sales;

use actix_web::web;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .configure(sales::configure)
            .configure(oa::configure)
            .configure(inventory::configure),
    );
}
