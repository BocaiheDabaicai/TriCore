use actix_web::{web, HttpResponse};
use sqlx::PgPool;

use crate::auth::{self, validate_token};
use crate::error::AppError;
use crate::dto::ApiResponse;
use crate::modules::auth::models::*;
use crate::modules::oa::models::Employee;

pub async fn login(
    pool: web::Data<PgPool>,
    secret: web::Data<String>,
    body: web::Json<LoginRequest>,
) -> Result<HttpResponse, AppError> {
    let emp = sqlx::query_as::<_, Employee>(
        "SELECT * FROM employees WHERE employee_no = $1 AND status = 'active'"
    )
    .bind(&body.employee_no)
    .fetch_optional(pool.get_ref())
    .await?
    .ok_or_else(|| AppError::Unauthorized("工号或密码错误".into()))?;

    let valid = bcrypt::verify(&body.password, &emp.password_hash)?;
    if !valid {
        return Err(AppError::Unauthorized("工号或密码错误".into()));
    }

    let token = auth::create_token(
        emp.id,
        &emp.employee_no,
        &emp.name,
        &emp.department,
        &emp.position,
        &emp.email,
        emp.phone.as_deref(),
        &emp.role,
        secret.get_ref(),
    )?;

    let resp = LoginResponse {
        token,
        user: EmployeePublic {
            id: emp.id,
            employee_no: emp.employee_no,
            name: emp.name,
            department: emp.department,
            position: emp.position,
            email: emp.email,
            phone: emp.phone,
            role: emp.role,
        },
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(resp)))
}

pub async fn me(
    req: actix_web::HttpRequest,
) -> Result<HttpResponse, AppError> {
    let secret = req
        .app_data::<web::Data<String>>()
        .map(|s| s.get_ref().clone())
        .unwrap_or_default();

    let token = req
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .ok_or_else(|| AppError::Unauthorized("未登录".into()))?;

    let claims = validate_token(token, &secret)?;

    let user = EmployeePublic {
        id: claims.sub.parse().unwrap_or_default(),
        employee_no: claims.emp_no,
        name: claims.name,
        department: claims.department,
        position: claims.position,
        email: claims.email,
        phone: claims.phone,
        role: claims.role,
    };

    Ok(HttpResponse::Ok().json(ApiResponse::success(user)))
}
