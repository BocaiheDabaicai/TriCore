use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub employee_no: String,
    pub password: String,
}

#[derive(Debug, Serialize)]
pub struct LoginResponse {
    pub token: String,
    pub user: EmployeePublic,
}

#[derive(Debug, Serialize)]
pub struct EmployeePublic {
    pub id: Uuid,
    pub employee_no: String,
    pub name: String,
    pub department: String,
    pub position: String,
    pub email: String,
    pub phone: Option<String>,
    pub role: String,
}
