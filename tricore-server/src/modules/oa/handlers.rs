use actix_web::{HttpResponse, web};
use sqlx::PgPool;

use crate::error::AppError;
use crate::dto::{ApiResponse, PaginatedResponse};
use crate::modules::oa::models::*;
use crate::modules::sales::models::StatusCount;

// ═══════════════════════════════════════════════════════════
// EMPLOYEES
// ═══════════════════════════════════════════════════════════

pub async fn list_employees(
    pool: web::Data<PgPool>,
    query: web::Query<EmployeeListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut conditions = vec!["1=1".to_string()];
    let mut idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref dept) = query.department {
        idx += 1; conditions.push(format!("department = ${idx}")); params.push(dept.clone());
    }
    if let Some(ref s) = query.status {
        idx += 1; conditions.push(format!("status = ${idx}")); params.push(s.clone());
    }

    let where_sql = conditions.join(" AND ");
    let count_sql = format!("SELECT COUNT(*) FROM employees WHERE {where_sql}");

    let total: (i64,) = {
        let mut q = sqlx::query_as(&count_sql);
        for p in &params { q = q.bind(p); }
        q.fetch_one(pool.get_ref()).await?
    };

    let list_sql = format!(
        "SELECT * FROM employees WHERE {where_sql} ORDER BY created_at DESC LIMIT ${0} OFFSET ${1}",
        idx + 1, idx + 2
    );
    let employees: Vec<Employee> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params { q = q.bind(p); }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(employees, total.0, page, per_page))))
}

pub async fn get_employee(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let emp = sqlx::query_as::<_, Employee>("SELECT * FROM employees WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("员工不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(emp)))
}

pub async fn create_employee(
    pool: web::Data<PgPool>,
    body: web::Json<CreateEmployeeRequest>,
) -> Result<HttpResponse, AppError> {
    let hash = bcrypt::hash(&body.password, 10)?;
    let role = body.role.as_deref().unwrap_or("user");
    let emp = sqlx::query_as::<_, Employee>(
        "INSERT INTO employees (employee_no, name, department, position, email, phone, password_hash, role)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING *"
    ).bind(&body.employee_no).bind(&body.name).bind(&body.department)
     .bind(&body.position).bind(&body.email).bind(&body.phone).bind(&hash).bind(role)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(emp)))
}

pub async fn update_employee(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateEmployeeRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, Employee>("SELECT * FROM employees WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("员工不存在".into()))?;

    let name = body.name.as_deref().unwrap_or(&existing.name);
    let dept = body.department.as_deref().unwrap_or(&existing.department);
    let pos = body.position.as_deref().unwrap_or(&existing.position);
    let email = body.email.as_deref().unwrap_or(&existing.email);
    let phone = body.phone.as_deref().or(existing.phone.as_deref());
    let status = body.status.as_deref().unwrap_or(&existing.status);
    let role = body.role.as_deref().unwrap_or(&existing.role);

    let pwd_hash: String = match &body.password {
        Some(pwd) if !pwd.is_empty() => bcrypt::hash(pwd, 10)?,
        _ => existing.password_hash.clone(),
    };

    let emp = sqlx::query_as::<_, Employee>(
        "UPDATE employees SET name=$1, department=$2, position=$3, email=$4, phone=$5, status=$6, role=$7, password_hash=$8
         WHERE id=$9 RETURNING *"
    ).bind(name).bind(dept).bind(pos).bind(email).bind(phone).bind(status).bind(role).bind(pwd_hash).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(emp)))
}

pub async fn delete_employee(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let emp = sqlx::query_as::<_, Employee>("SELECT * FROM employees WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("员工不存在".into()))?;

    sqlx::query("DELETE FROM employees WHERE id = $1")
        .bind(emp.id).execute(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("员工已删除")))
}

// ═══════════════════════════════════════════════════════════
// WORKFLOWS
// ═══════════════════════════════════════════════════════════

pub async fn list_workflows(
    pool: web::Data<PgPool>,
    query: web::Query<WorkflowListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;

    let mut conditions = vec!["1=1".to_string()];
    let mut idx = 0u32;
    let mut params: Vec<String> = vec![];

    if let Some(ref s) = query.status {
        idx += 1; conditions.push(format!("status = ${idx}")); params.push(s.clone());
    }
    if let Some(cid) = query.creator_id {
        idx += 1; conditions.push(format!("creator_id = ${idx}")); params.push(cid.to_string());
    }

    let where_sql = conditions.join(" AND ");
    let count_sql = format!("SELECT COUNT(*) FROM workflow_forms WHERE {where_sql}");
    let total: (i64,) = {
        let mut q = sqlx::query_as(&count_sql);
        for p in &params { q = q.bind(p); }
        q.fetch_one(pool.get_ref()).await?
    };

    let list_sql = format!(
        "SELECT * FROM workflow_forms WHERE {where_sql} ORDER BY created_at DESC LIMIT ${0} OFFSET ${1}",
        idx + 1, idx + 2
    );
    let workflows: Vec<WorkflowForm> = {
        let mut q = sqlx::query_as(&list_sql);
        for p in &params { q = q.bind(p); }
        q.bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(workflows, total.0, page, per_page))))
}

pub async fn get_workflow(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let wf = sqlx::query_as::<_, WorkflowForm>("SELECT * FROM workflow_forms WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("流程不存在".into()))?;
    let steps = sqlx::query_as::<_, WorkflowStep>(
        "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_number"
    ).bind(*path).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(WorkflowWithSteps { workflow: wf, steps })))
}

pub async fn create_workflow(
    pool: web::Data<PgPool>,
    body: web::Json<CreateWorkflowRequest>,
) -> Result<HttpResponse, AppError> {
    if body.steps.is_empty() {
        return Err(AppError::BadRequest("审核步骤不能为空".into()));
    }
    let total = body.steps.len() as i32;
    let form_data = body.form_data.clone().unwrap_or(serde_json::json!({}));

    let mut tx = pool.begin().await?;

    // Get creator (first reviewer = employee)
    let first_reviewer = body.steps[0].reviewer_id;
    let creator = sqlx::query_as::<_, Employee>("SELECT * FROM employees WHERE id = $1")
        .bind(first_reviewer).fetch_optional(&mut *tx).await?
        .map(|_| first_reviewer)
        .unwrap_or(first_reviewer);

    let wf = sqlx::query_as::<_, WorkflowForm>(
        "INSERT INTO workflow_forms (creator_id, title, description, form_data, total_steps)
         VALUES ($1,$2,$3,$4,$5) RETURNING *"
    ).bind(creator).bind(&body.title).bind(&body.description).bind(&form_data).bind(total)
    .fetch_one(&mut *tx).await?;

    for step_def in &body.steps {
        sqlx::query(
            "INSERT INTO workflow_steps (workflow_id, step_number, reviewer_id) VALUES ($1,$2,$3)"
        ).bind(wf.id).bind(step_def.step_number).bind(step_def.reviewer_id)
        .execute(&mut *tx).await?;
    }

    tx.commit().await?;

    let steps = sqlx::query_as::<_, WorkflowStep>(
        "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_number"
    ).bind(wf.id).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Created().json(ApiResponse::success(WorkflowWithSteps { workflow: wf, steps })))
}

pub async fn update_workflow(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateWorkflowRequest>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, WorkflowForm>("SELECT * FROM workflow_forms WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("流程不存在".into()))?;

    if existing.status != "rejected" && existing.status != "pending" {
        return Err(AppError::BadRequest("当前状态不可修改".into()));
    }

    let title = body.title.as_deref().unwrap_or(&existing.title);
    let desc = body.description.as_deref().or(existing.description.as_deref());
    let fd = body.form_data.clone().unwrap_or(existing.form_data);

    let wf = sqlx::query_as::<_, WorkflowForm>(
        "UPDATE workflow_forms SET title=$1, description=$2, form_data=$3 WHERE id=$4 RETURNING *"
    ).bind(title).bind(desc).bind(&fd).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(wf)))
}

pub async fn submit_workflow(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, WorkflowForm>("SELECT * FROM workflow_forms WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("流程不存在".into()))?;

    if existing.status != "pending" && existing.status != "rejected" {
        return Err(AppError::BadRequest("当前状态不可提交".into()));
    }

    // Check if any steps are already approved (node rejection scenario)
    let approved_count: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM workflow_steps WHERE workflow_id = $1 AND status = 'approved'"
    ).bind(*path).fetch_one(pool.get_ref()).await?;

    let start_step = if approved_count.0 > 0 {
        // Node rejection: find the first rejected step, reset from there
        let first_rejected: (i32,) = sqlx::query_as(
            "SELECT COALESCE(MIN(step_number), 1) FROM workflow_steps WHERE workflow_id = $1 AND status = 'rejected'"
        ).bind(*path).fetch_one(pool.get_ref()).await?;
        first_rejected.0
    } else {
        1
    };

    let wf = sqlx::query_as::<_, WorkflowForm>(
        "UPDATE workflow_forms SET status='in_progress', current_step=$1 WHERE id=$2 RETURNING *"
    ).bind(start_step).bind(*path).fetch_one(pool.get_ref()).await?;

    // Reset steps from the target step onwards (for full rejection: all steps; for node: only rejected & beyond)
    sqlx::query(
        "UPDATE workflow_steps SET status='pending', comment=NULL, acted_at=NULL WHERE workflow_id=$1 AND step_number >= $2"
    ).bind(*path).bind(start_step).execute(pool.get_ref()).await?;

    let steps = sqlx::query_as::<_, WorkflowStep>(
        "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_number"
    ).bind(*path).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(WorkflowWithSteps { workflow: wf, steps })))
}

pub async fn delete_workflow(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let existing = sqlx::query_as::<_, WorkflowForm>("SELECT * FROM workflow_forms WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("流程不存在".into()))?;

    if existing.status != "pending" && existing.status != "rejected" {
        return Err(AppError::BadRequest("只能删除待提交或已退回的流程".into()));
    }

    let mut tx = pool.begin().await?;
    sqlx::query("DELETE FROM workflow_steps WHERE workflow_id = $1")
        .bind(*path).execute(&mut *tx).await?;
    sqlx::query("DELETE FROM workflow_forms WHERE id = $1")
        .bind(*path).execute(&mut *tx).await?;
    tx.commit().await?;

    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("流程已删除")))
}

pub async fn get_steps(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let steps = sqlx::query_as::<_, WorkflowStep>(
        "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_number"
    ).bind(*path).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(steps)))
}

pub async fn review_step(
    pool: web::Data<PgPool>,
    path: web::Path<(uuid::Uuid, uuid::Uuid)>,
    body: web::Json<ReviewStepRequest>,
) -> Result<HttpResponse, AppError> {
    let (workflow_id, step_id) = *path;

    let step = sqlx::query_as::<_, WorkflowStep>(
        "SELECT * FROM workflow_steps WHERE id = $1 AND workflow_id = $2"
    ).bind(step_id).bind(workflow_id).fetch_optional(pool.get_ref()).await?
    .ok_or_else(|| AppError::NotFound("审核步骤不存在".into()))?;

    if step.status != "pending" {
        return Err(AppError::BadRequest("该步骤已被审核".into()));
    }

    // Sequential check: all previous steps must be approved
    let prev_unapproved: (i64,) = sqlx::query_as(
        "SELECT COUNT(*) FROM workflow_steps WHERE workflow_id = $1 AND step_number < $2 AND status != 'approved'"
    ).bind(workflow_id).bind(step.step_number).fetch_one(pool.get_ref()).await?;
    if prev_unapproved.0 > 0 {
        return Err(AppError::BadRequest("请先完成前面的审核步骤".into()));
    }

    let mut tx = pool.begin().await?;

    match body.action.as_str() {
        "approve" => {
            sqlx::query(
                "UPDATE workflow_steps SET status='approved', comment=$1, attachment_url=$2, acted_at=NOW()
                 WHERE id=$3"
            ).bind(&body.comment).bind(&body.attachment_url).bind(step_id)
            .execute(&mut *tx).await?;

            let wf = sqlx::query_as::<_, WorkflowForm>("SELECT * FROM workflow_forms WHERE id = $1")
                .bind(workflow_id).fetch_one(&mut *tx).await?;

            if step.step_number >= wf.total_steps {
                // Last step approved → archive
                sqlx::query("UPDATE workflow_forms SET status='approved' WHERE id=$1")
                    .bind(workflow_id).execute(&mut *tx).await?;

                let all_steps = sqlx::query_as::<_, WorkflowStep>(
                    "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_number"
                ).bind(workflow_id).fetch_all(&mut *tx).await?;

                let archive_data = serde_json::json!({
                    "title": wf.title,
                    "description": wf.description,
                    "form_data": wf.form_data,
                    "total_steps": wf.total_steps,
                    "steps": all_steps.iter().map(|s| serde_json::json!({
                        "step_number": s.step_number,
                        "reviewer_id": s.reviewer_id,
                        "status": s.status,
                        "comment": s.comment,
                        "acted_at": s.acted_at,
                    })).collect::<Vec<_>>(),
                });

                sqlx::query(
                    "INSERT INTO workflow_archives (workflow_id, archived_data, final_decision) VALUES ($1,$2,'approved')
                     ON CONFLICT (workflow_id) DO NOTHING"
                ).bind(workflow_id).bind(&archive_data).execute(&mut *tx).await?;
            } else {
                sqlx::query(
                    "UPDATE workflow_forms SET current_step = current_step + 1 WHERE id = $1"
                ).bind(workflow_id).execute(&mut *tx).await?;
            }
        }
        "reject" => {
            let mode = body.reject_mode.as_deref().unwrap_or("full");

            if mode == "node" {
                // Node-level rejection: only reject current step, keep prior approvals
                sqlx::query(
                    "UPDATE workflow_steps SET status='rejected', comment=$1, attachment_url=$2, acted_at=NOW()
                     WHERE id=$3"
                ).bind(&body.comment).bind(&body.attachment_url).bind(step_id)
                .execute(&mut *tx).await?;

                sqlx::query(
                    "UPDATE workflow_forms SET status='rejected', current_step=$1 WHERE id=$2"
                ).bind(step.step_number).bind(workflow_id).execute(&mut *tx).await?;
            } else {
                // Full rejection: reset ALL steps to pending, reject entire workflow
                sqlx::query(
                    "UPDATE workflow_steps SET status='pending', comment=NULL, acted_at=NULL
                     WHERE workflow_id=$1"
                ).bind(workflow_id).execute(&mut *tx).await?;

                sqlx::query(
                    "UPDATE workflow_steps SET status='rejected', comment=$1, attachment_url=$2, acted_at=NOW()
                     WHERE id=$3"
                ).bind(&body.comment).bind(&body.attachment_url).bind(step_id)
                .execute(&mut *tx).await?;

                sqlx::query(
                    "UPDATE workflow_forms SET status='rejected', current_step=1 WHERE id=$1"
                ).bind(workflow_id).execute(&mut *tx).await?;
            }
        }
        _ => return Err(AppError::BadRequest("action 必须是 approve 或 reject".into())),
    }

    tx.commit().await?;

    let updated_wf = sqlx::query_as::<_, WorkflowForm>("SELECT * FROM workflow_forms WHERE id = $1")
        .bind(workflow_id).fetch_one(pool.get_ref()).await?;
    let updated_steps = sqlx::query_as::<_, WorkflowStep>(
        "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY step_number"
    ).bind(workflow_id).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(WorkflowWithSteps { workflow: updated_wf, steps: updated_steps })))
}

// ═══════════════════════════════════════════════════════════
// ARCHIVES
// ═══════════════════════════════════════════════════════════

pub async fn list_archives(
    pool: web::Data<PgPool>,
    query: web::Query<WorkflowListQuery>,
) -> Result<HttpResponse, AppError> {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    let offset = (page - 1) * per_page;
    let total: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM workflow_archives").fetch_one(pool.get_ref()).await?;
    let archives = sqlx::query_as::<_, WorkflowArchive>(
        "SELECT * FROM workflow_archives ORDER BY archived_at DESC LIMIT $1 OFFSET $2"
    ).bind(per_page).bind(offset).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(PaginatedResponse::new(archives, total.0, page, per_page))))
}

pub async fn get_archive(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let archive = sqlx::query_as::<_, WorkflowArchive>("SELECT * FROM workflow_archives WHERE id = $1")
        .bind(*path).fetch_optional(pool.get_ref()).await?
        .ok_or_else(|| AppError::NotFound("归档记录不存在".into()))?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(archive)))
}

// ═══════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════

pub async fn dashboard(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let total_emp: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM employees WHERE status='active'").fetch_one(pool.get_ref()).await?;
    let total_wf: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM workflow_forms").fetch_one(pool.get_ref()).await?;
    let pending: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM workflow_forms WHERE status='in_progress'").fetch_one(pool.get_ref()).await?;

    let rows = sqlx::query_as::<_, StatusCount>(
        "SELECT status, COUNT(*) as count FROM workflow_forms GROUP BY status ORDER BY status"
    ).fetch_all(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(OADashboard {
        total_employees: total_emp.0,
        total_workflows: total_wf.0,
        pending_workflows: pending.0,
        workflows_by_status: rows,
    })))
}

// ═══════════════════════════════════════════════════════════
// WORKFLOW TEMPLATES
// ═══════════════════════════════════════════════════════════

pub async fn list_templates(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let templates = sqlx::query_as::<_, WorkflowTemplate>(
        "SELECT * FROM workflow_templates ORDER BY name"
    ).fetch_all(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(templates)))
}

pub async fn create_template(
    pool: web::Data<PgPool>,
    body: web::Json<CreateTemplateRequest>,
) -> Result<HttpResponse, AppError> {
    if body.name.trim().is_empty() {
        return Err(AppError::BadRequest("模板名称不能为空".into()));
    }
    if body.steps.is_empty() {
        return Err(AppError::BadRequest("至少需要一个审核步骤".into()));
    }
    let steps_json = serde_json::to_value(&body.steps).unwrap_or_default();
    let tmpl = sqlx::query_as::<_, WorkflowTemplate>(
        "INSERT INTO workflow_templates (name, description, steps) VALUES ($1,$2,$3) RETURNING *"
    ).bind(&body.name).bind(&body.description).bind(&steps_json)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Created().json(ApiResponse::success(tmpl)))
}

pub async fn update_template(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
    body: web::Json<UpdateTemplateRequest>,
) -> Result<HttpResponse, AppError> {
    let ex = sqlx::query_as::<_, WorkflowTemplate>(
        "SELECT * FROM workflow_templates WHERE id = $1"
    ).bind(*path).fetch_optional(pool.get_ref()).await?
    .ok_or_else(|| AppError::NotFound("模板不存在".into()))?;

    let name = body.name.as_deref().unwrap_or(&ex.name);
    let desc = body.description.as_deref().or(ex.description.as_deref());
    let steps_json = body.steps.as_ref()
        .map(|s| serde_json::to_value(s).unwrap_or(ex.steps.clone()))
        .unwrap_or_else(|| ex.steps.clone());

    let tmpl = sqlx::query_as::<_, WorkflowTemplate>(
        "UPDATE workflow_templates SET name=$1, description=$2, steps=$3 WHERE id=$4 RETURNING *"
    ).bind(name).bind(desc).bind(&steps_json).bind(*path)
    .fetch_one(pool.get_ref()).await?;
    Ok(HttpResponse::Ok().json(ApiResponse::success(tmpl)))
}

pub async fn delete_template(
    pool: web::Data<PgPool>,
    path: web::Path<uuid::Uuid>,
) -> Result<HttpResponse, AppError> {
    let rows = sqlx::query("DELETE FROM workflow_templates WHERE id = $1")
        .bind(*path).execute(pool.get_ref()).await?.rows_affected();
    if rows == 0 { return Err(AppError::NotFound("模板不存在".into())); }
    Ok(HttpResponse::Ok().json(ApiResponse::<String>::message("已删除")))
}
