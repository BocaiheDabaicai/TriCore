use actix_web::web;
use super::handlers as data_snapshot;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/data-snapshots")
            .route("", web::get().to(data_snapshot::list_snapshots))
            .route("", web::post().to(data_snapshot::create_snapshot_handler))
            .route("/{id}", web::delete().to(data_snapshot::delete_snapshot))
            .route("/{id}/restore", web::post().to(data_snapshot::restore_snapshot)),
    );
}
