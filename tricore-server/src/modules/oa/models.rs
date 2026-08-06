use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

// ═══════════════════════════════════════════════════════════
// Entity structs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Employee {
    pub id: Uuid,
    pub employee_no: String,
    pub name: String,
    pub department: String,
    pub position: String,
    pub email: String,
    pub phone: Option<String>,
    #[serde(skip_serializing)]
    pub password_hash: String,
    pub status: String,
    pub role: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct WorkflowForm {
    pub id: Uuid,
    pub creator_id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub form_data: serde_json::Value,
    pub status: String,
    pub current_step: i32,
    pub total_steps: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct WorkflowStep {
    pub id: Uuid,
    pub workflow_id: Uuid,
    pub step_number: i32,
    pub reviewer_id: Uuid,
    pub status: String,
    pub comment: Option<String>,
    pub attachment_url: Option<String>,
    pub acted_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct WorkflowArchive {
    pub id: Uuid,
    pub workflow_id: Uuid,
    pub archived_data: serde_json::Value,
    pub final_decision: String,
    pub archived_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct WorkflowTemplate {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub steps: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

// ═══════════════════════════════════════════════════════════
// Join / display structs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Serialize)]
pub struct WorkflowWithSteps {
    #[serde(flatten)]
    pub workflow: WorkflowForm,
    pub steps: Vec<WorkflowStep>,
}

// ═══════════════════════════════════════════════════════════
// Request DTOs
// ═══════════════════════════════════════════════════════════

#[derive(Debug, Deserialize)]
pub struct CreateEmployeeRequest {
    pub employee_no: String,
    pub name: String,
    pub department: String,
    pub position: String,
    pub email: String,
    pub phone: Option<String>,
    pub password: String,
    pub role: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateEmployeeRequest {
    pub name: Option<String>,
    pub department: Option<String>,
    pub position: Option<String>,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub password: Option<String>,
    pub status: Option<String>,
    pub role: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CreateWorkflowRequest {
    pub title: String,
    pub description: Option<String>,
    pub form_data: Option<serde_json::Value>,
    pub steps: Vec<StepDefinition>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StepDefinition {
    pub step_number: i32,
    pub reviewer_id: Uuid,
}

#[derive(Debug, Deserialize)]
pub struct UpdateWorkflowRequest {
    pub title: Option<String>,
    pub description: Option<String>,
    pub form_data: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct ReviewStepRequest {
    pub action: String,
    pub comment: Option<String>,
    pub attachment_url: Option<String>,
    #[serde(default)]
    pub reject_mode: Option<String>,  // "full" or "node" when action is "reject"
}

#[derive(Debug, Serialize)]
pub struct OADashboard {
    pub total_employees: i64,
    pub total_workflows: i64,
    pub pending_workflows: i64,
    pub workflows_by_status: Vec<crate::modules::sales::models::StatusCount>,
}

#[derive(Debug, Deserialize)]
pub struct EmployeeListQuery {
    pub department: Option<String>,
    pub status: Option<String>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct WorkflowListQuery {
    pub status: Option<String>,
    pub creator_id: Option<Uuid>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize)]
pub struct CreateTemplateRequest {
    pub name: String,
    pub description: Option<String>,
    pub steps: Vec<StepDefinition>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateTemplateRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub steps: Option<Vec<StepDefinition>>,
}
