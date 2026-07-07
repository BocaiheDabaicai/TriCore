use actix_web::{HttpResponse, ResponseError};
use std::fmt;

#[derive(Debug)]
pub enum AppError {
    NotFound(String),
    BadRequest(String),
    Internal(String),
    DatabaseError(String),
    Unauthorized(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound(msg) => write!(f, "Not found: {msg}"),
            Self::BadRequest(msg) => write!(f, "Bad request: {msg}"),
            Self::Internal(msg) => write!(f, "Internal error: {msg}"),
            Self::DatabaseError(msg) => write!(f, "Database error: {msg}"),
            Self::Unauthorized(msg) => write!(f, "Unauthorized: {msg}"),
        }
    }
}

impl ResponseError for AppError {
    fn error_response(&self) -> HttpResponse {
        let (status, message) = match self {
            Self::NotFound(msg) => (actix_web::http::StatusCode::NOT_FOUND, msg.clone()),
            Self::BadRequest(msg) => (actix_web::http::StatusCode::BAD_REQUEST, msg.clone()),
            Self::Internal(msg) => (actix_web::http::StatusCode::INTERNAL_SERVER_ERROR, msg.clone()),
            Self::DatabaseError(msg) => (actix_web::http::StatusCode::INTERNAL_SERVER_ERROR, msg.clone()),
            Self::Unauthorized(msg) => (actix_web::http::StatusCode::UNAUTHORIZED, msg.clone()),
        };
        HttpResponse::build(status).json(serde_json::json!({
            "success": false,
            "message": message,
        }))
    }
}

impl From<sqlx::Error> for AppError {
    fn from(err: sqlx::Error) -> Self {
        match err {
            sqlx::Error::RowNotFound => Self::NotFound("Record not found".into()),
            _ => Self::DatabaseError(err.to_string()),
        }
    }
}

impl From<bcrypt::BcryptError> for AppError {
    fn from(err: bcrypt::BcryptError) -> Self {
        Self::Internal(format!("Password hashing error: {err}"))
    }
}
