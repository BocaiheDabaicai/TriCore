use actix_web::{
    body::BoxBody,
    dev::{ServiceRequest, ServiceResponse},
    http::Method,
    middleware::Next,
    web, HttpResponse,
};
use chrono::Utc;
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::error::AppError;

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub emp_no: String,
    pub name: String,
    pub department: String,
    pub position: String,
    pub email: String,
    pub phone: Option<String>,
    pub role: String,
    pub exp: usize,
    pub iat: usize,
}

pub fn create_token(
    id: Uuid,
    employee_no: &str,
    name: &str,
    department: &str,
    position: &str,
    email: &str,
    phone: Option<&str>,
    role: &str,
    secret: &str,
) -> Result<String, AppError> {
    let now = Utc::now();
    let claims = Claims {
        sub: id.to_string(),
        emp_no: employee_no.to_string(),
        name: name.to_string(),
        department: department.to_string(),
        position: position.to_string(),
        email: email.to_string(),
        phone: phone.map(|s| s.to_string()),
        role: role.to_string(),
        iat: now.timestamp() as usize,
        exp: (now.timestamp() + 86400) as usize,
    };
    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .map_err(|e| AppError::Internal(format!("JWT encode error: {e}")))
}

pub fn validate_token(token: &str, secret: &str) -> Result<Claims, AppError> {
    decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::default(),
    )
    .map(|data| data.claims)
    .map_err(|e| AppError::Unauthorized(format!("令牌无效: {e}")))
}

pub async fn auth_middleware(
    req: ServiceRequest,
    next: Next<impl actix_web::body::MessageBody + 'static>,
) -> Result<ServiceResponse<BoxBody>, actix_web::Error> {
    // Skip auth for login endpoint and CORS preflight requests
    if (req.path() == "/api/auth/login" && req.method() == Method::POST)
        || req.method() == Method::OPTIONS
    {
        return next.call(req).await.map(|r| r.map_into_boxed_body());
    }

    let secret = req
        .app_data::<web::Data<String>>()
        .map(|s| s.get_ref().clone())
        .unwrap_or_default();

    let valid = req
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .map(|t| validate_token(t, &secret).is_ok())
        .unwrap_or(false);

    if valid {
        next.call(req).await.map(|r| r.map_into_boxed_body())
    } else {
        let resp = HttpResponse::Unauthorized().json(serde_json::json!({
            "success": false,
            "message": "未登录或令牌已失效"
        }));
        Ok(req.into_response(resp).map_into_boxed_body())
    }
}
