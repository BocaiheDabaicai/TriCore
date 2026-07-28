use actix_web::web;
use crate::handlers::oa;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/oa")
            // Employees
            .route("/employees", web::get().to(oa::list_employees))
            .route("/employees/{id}", web::get().to(oa::get_employee))
            .route("/employees", web::post().to(oa::create_employee))
            .route("/employees/{id}", web::put().to(oa::update_employee))
            .route("/employees/{id}", web::delete().to(oa::delete_employee))
            // Workflows
            .route("/workflows", web::get().to(oa::list_workflows))
            .route("/workflows/{id}", web::get().to(oa::get_workflow))
            .route("/workflows", web::post().to(oa::create_workflow))
            .route("/workflows/{id}", web::put().to(oa::update_workflow))
            .route("/workflows/{id}", web::delete().to(oa::delete_workflow))
            .route("/workflows/{id}/submit", web::post().to(oa::submit_workflow))
            .route("/workflows/{id}/steps", web::get().to(oa::get_steps))
            .route("/workflows/{id}/steps/{step_id}/review", web::post().to(oa::review_step))
            // Archives
            .route("/archives", web::get().to(oa::list_archives))
            .route("/archives/{id}", web::get().to(oa::get_archive))
            // Dashboard
            .route("/dashboard", web::get().to(oa::dashboard))
            // Templates
            .route("/templates", web::get().to(oa::list_templates))
            .route("/templates", web::post().to(oa::create_template))
            .route("/templates/{id}", web::put().to(oa::update_template))
            .route("/templates/{id}", web::delete().to(oa::delete_template)),
    );
}
