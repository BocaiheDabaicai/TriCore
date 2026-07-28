use actix_web::{HttpResponse, web};
use sqlx::PgPool;

use crate::error::AppError;
use crate::models::ai::*;
use crate::models::dto::ApiResponse;

// ═══════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════

pub async fn get_config(
    pool: web::Data<PgPool>,
) -> Result<HttpResponse, AppError> {
    let cfg = sqlx::query_as::<_, AiConfig>("SELECT * FROM ai_configs WHERE id = 1")
        .fetch_optional(pool.get_ref()).await?
        .unwrap_or(AiConfig {
            id: 1,
            api_key: String::new(),
            model: "claude-sonnet-4-6".into(),
            base_url: "https://api.anthropic.com".into(),
            system_prompt: None,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
        });
    Ok(HttpResponse::Ok().json(ApiResponse::success(cfg)))
}

pub async fn update_config(
    pool: web::Data<PgPool>,
    body: web::Json<UpdateAiConfigRequest>,
) -> Result<HttpResponse, AppError> {
    let ex = sqlx::query_as::<_, AiConfig>("SELECT * FROM ai_configs WHERE id = 1")
        .fetch_optional(pool.get_ref()).await?;

    let api_key = body.api_key.clone().unwrap_or_else(|| ex.as_ref().map(|c| c.api_key.clone()).unwrap_or_default());
    let model = body.model.clone().unwrap_or_else(|| ex.as_ref().map(|c| c.model.clone()).unwrap_or_else(|| "claude-sonnet-4-6".into()));
    let base_url = body.base_url.clone().unwrap_or_else(|| ex.as_ref().map(|c| c.base_url.clone()).unwrap_or_else(|| "https://api.anthropic.com".into()));
    let sys_prompt = body.system_prompt.clone().or_else(|| ex.as_ref().and_then(|c| c.system_prompt.clone()));

    let cfg = sqlx::query_as::<_, AiConfig>(
        "INSERT INTO ai_configs (id, api_key, model, base_url, system_prompt)
         VALUES (1, $1, $2, $3, $4)
         ON CONFLICT (id) DO UPDATE SET api_key=EXCLUDED.api_key, model=EXCLUDED.model,
         base_url=EXCLUDED.base_url, system_prompt=EXCLUDED.system_prompt, updated_at=NOW()
         RETURNING *"
    ).bind(&api_key).bind(&model).bind(&base_url).bind(&sys_prompt)
    .fetch_one(pool.get_ref()).await?;

    Ok(HttpResponse::Ok().json(ApiResponse::success(cfg)))
}

// ═══════════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════════

const SYSTEM_PROMPT: &str = r#"你是 TriCore 企业系统的 AI 助手。你可以帮助用户查询和分析系统中的数据。

可用工具：
1. query_orders(status, keyword) - 查询销售订单
2. query_products() - 查询商品列表
3. query_inventory() - 查询库存状况
4. query_workflows() - 查询审批流程
5. query_employees() - 查询员工信息
6. get_dashboard() - 获取系统概览统计

当用户询问具体数据时，请先调用相应工具获取最新数据，然后基于数据回答。
回答请使用中文，简洁清晰。"#;

fn build_tools() -> serde_json::Value {
    serde_json::json!([
        {
            "name": "query_orders",
            "description": "查询销售订单列表，可按状态(status: pending/confirmed/processing/shipped/delivered/cancelled)和关键字筛选",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "订单状态"},
                    "keyword": {"type": "string", "description": "搜索关键字"}
                }
            }
        },
        {
            "name": "query_products",
            "description": "查询商品列表和库存",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "query_inventory",
            "description": "查询库存状况概览，包含各商品总库存和仓库分布",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "query_workflows",
            "description": "查询审批流程列表",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "query_employees",
            "description": "查询员工信息",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "query_regulations",
            "description": "查询规章制度文件列表",
            "input_schema": {"type": "object", "properties": {}}
        },
        {
            "name": "get_dashboard",
            "description": "获取系统概览统计：订单总数、商品数、库存预警、待审批流程等",
            "input_schema": {"type": "object", "properties": {}}
        }
    ])
}

async fn execute_tool(name: &str, pool: &PgPool) -> String {
    match name {
        "query_orders" => {
            match sqlx::query_as::<_, crate::models::sales::Order>(
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT 20"
            ).fetch_all(pool).await {
                Ok(orders) => {
                    let items: Vec<String> = orders.iter().map(|o|
                        format!("订单号:{} 金额:¥{} 状态:{} 时间:{}",
                            o.order_no, o.final_amount, o.status,
                            o.created_at.format("%Y-%m-%d %H:%M"))
                    ).collect();
                    format!("最近 20 笔订单：\n{}", items.join("\n"))
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "query_products" => {
            match sqlx::query_as::<_, crate::models::sales::Product>(
                "SELECT * FROM products WHERE is_active = true ORDER BY quantity ASC"
            ).fetch_all(pool).await {
                Ok(prods) => {
                    let items: Vec<String> = prods.iter().map(|p|
                        format!("{}({}) 库存:{} 价格:¥{} 分类:{}",
                            p.name, p.sku, p.quantity, p.original_price,
                            p.category.as_deref().unwrap_or("无"))
                    ).collect();
                    format!("商品列表（按库存从少到多）：\n{}", items.join("\n"))
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "query_inventory" => {
            match sqlx::query_as::<_, crate::models::sales::Product>(
                "SELECT * FROM products WHERE is_active = true ORDER BY quantity ASC"
            ).fetch_all(pool).await {
                Ok(prods) => {
                    let low: Vec<_> = prods.iter().filter(|p| p.quantity < 50).collect();
                    let mut report = format!("总商品数: {} 种\n库存预警(<50): {} 种\n\n", prods.len(), low.len());
                    if !low.is_empty() {
                        report.push_str("⚠ 低库存商品：\n");
                        for p in low {
                            report.push_str(&format!("  - {} 仅剩 {} 件\n", p.name, p.quantity));
                        }
                    }
                    report.push_str("\n全部库存：\n");
                    for p in &prods {
                        let warn = if p.quantity < 50 { " ⚠" } else { "" };
                        report.push_str(&format!("  {}: {} 件{}\n", p.name, p.quantity, warn));
                    }
                    report
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "query_workflows" => {
            match sqlx::query_as::<_, crate::models::oa::WorkflowForm>(
                "SELECT * FROM workflow_forms ORDER BY updated_at DESC LIMIT 20"
            ).fetch_all(pool).await {
                Ok(wfs) => {
                    let items: Vec<String> = wfs.iter().map(|w| {
                        let sc = match w.status.as_str() {
                            "pending" => "待提交", "in_progress" => "审批中",
                            "approved" => "已通过", "rejected" => "已退回", _ => &w.status
                        };
                        format!("{} [{}] 进度:{}/{} 时间:{}",
                            w.title, sc,
                            w.current_step, w.total_steps,
                            w.created_at.format("%m-%d %H:%M"))
                    }).collect();
                    format!("最近 20 条审批流程：\n{}", items.join("\n"))
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "query_employees" => {
            match sqlx::query_as::<_, crate::models::oa::Employee>(
                "SELECT * FROM employees WHERE status='active' ORDER BY department, name"
            ).fetch_all(pool).await {
                Ok(emps) => {
                    let items: Vec<String> = emps.iter().map(|e|
                        format!("{}({}) {} - {} {}",
                            e.name, e.employee_no, e.department, e.position, e.email)
                    ).collect();
                    format!("在职员工 {} 人：\n{}", emps.len(), items.join("\n"))
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "query_regulations" => {
            match sqlx::query_as::<_, crate::models::regulation::RegulationFile>(
                "SELECT * FROM regulation_files ORDER BY created_at DESC LIMIT 20"
            ).fetch_all(pool).await {
                Ok(files) => {
                    let items: Vec<String> = files.iter().map(|f|
                        format!("{} ({} KB) 上传:{}",
                            f.title, f.file_size / 1024,
                            f.created_at.format("%m-%d %H:%M"))
                    ).collect();
                    format!("最近 20 个文件：\n{}", items.join("\n"))
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "get_dashboard" => {
            let orders: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM orders").fetch_one(pool).await.unwrap_or((0,));
            let prods: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE is_active=true").fetch_one(pool).await.unwrap_or((0,));
            let low: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM products WHERE quantity<50 AND is_active=true").fetch_one(pool).await.unwrap_or((0,));
            let wf: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM workflow_forms WHERE status='in_progress'").fetch_one(pool).await.unwrap_or((0,));
            let emps: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM employees WHERE status='active'").fetch_one(pool).await.unwrap_or((0,));
            let files: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM regulation_files").fetch_one(pool).await.unwrap_or((0,));
            format!("TriCore 系统概览：\n- 销售订单: {} 笔\n- 商品种类: {} 种 (库存预警: {} 种)\n- 待审批流程: {} 个\n- 在职员工: {} 人\n- 规章制度文件: {} 份",
                orders.0, prods.0, low.0, wf.0, emps.0, files.0)
        }
        _ => "未知工具".to_string()
    }
}

fn is_openai_format(base_url: &str) -> bool {
    let url = base_url.to_lowercase();
    url.contains("deepseek") || url.contains("openai") || url.contains("openrouter")
        || url.contains("groq") || url.contains("zhipu") || url.contains("qwen")
        || url.contains("mistral")
}

fn anthropic_tools_to_openai(tools: &serde_json::Value) -> Vec<serde_json::Value> {
    tools.as_array().map(|arr| {
        arr.iter().map(|t| {
            serde_json::json!({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                }
            })
        }).collect()
    }).unwrap_or_default()
}

pub async fn chat(
    pool: web::Data<PgPool>,
    body: web::Json<ChatRequest>,
) -> Result<HttpResponse, AppError> {
    let cfg = sqlx::query_as::<_, AiConfig>("SELECT * FROM ai_configs WHERE id = 1")
        .fetch_optional(pool.get_ref()).await?
        .unwrap_or(AiConfig {
            id: 1, api_key: String::new(), model: "claude-sonnet-4-6".into(),
            base_url: "https://api.anthropic.com".into(), system_prompt: None,
            created_at: chrono::Utc::now(), updated_at: chrono::Utc::now(),
        });

    if cfg.api_key.is_empty() {
        return Err(AppError::BadRequest("请先在「AI配置」中设置 API Key".into()));
    }

    let client = reqwest::Client::new();
    let system_text = cfg.system_prompt.as_deref().unwrap_or(SYSTEM_PROMPT);
    let use_openai = is_openai_format(&cfg.base_url);
    let tools = build_tools();

    // Build messages for API
    let mut api_messages: Vec<serde_json::Value> = if use_openai {
        let mut msgs: Vec<serde_json::Value> = vec![
            serde_json::json!({ "role": "system", "content": system_text })
        ];
        msgs.extend(body.messages.iter().map(|m| {
            serde_json::json!({ "role": m.role, "content": m.content })
        }));
        msgs
    } else {
        body.messages.iter().map(|m| {
            serde_json::json!({ "role": m.role, "content": m.content })
        }).collect()
    };

    // Function calling loop (max 5 tool calls)
    let max_rounds = 5;
    for _round in 0..max_rounds {
        let (resp_text, tool_calls) = if use_openai {
            call_openai(&client, &cfg, &api_messages, &tools).await?
        } else {
            call_anthropic(&client, &cfg, system_text, &api_messages, &tools).await?
        };

        if tool_calls.is_empty() {
            if resp_text.is_empty() {
                return Err(AppError::Internal("AI 返回了空响应".into()));
            }
            return Ok(HttpResponse::Ok().json(ApiResponse::success(ChatResponse {
                message: ChatMessage { role: "assistant".into(), content: resp_text },
            })));
        }

        // Execute tools
        let mut tool_results: Vec<serde_json::Value> = vec![];
        let mut assistant_tool_calls: Vec<serde_json::Value> = vec![];

        for tc in &tool_calls {
            let tool_name = tc["name"].as_str().unwrap_or("").to_string();
            let tool_id = tc["id"].as_str().unwrap_or("").to_string();
            let result = execute_tool(&tool_name, pool.get_ref()).await;

            if use_openai {
                tool_results.push(serde_json::json!({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result,
                }));
                assistant_tool_calls.push(serde_json::json!({
                    "id": tool_id,
                    "type": "function",
                    "function": { "name": tool_name, "arguments": "{}" }
                }));
            } else {
                tool_results.push(serde_json::json!({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                }));
                assistant_tool_calls.push(tc.clone());
            }
        }

        // Add assistant message with tool calls
        if use_openai {
            api_messages.push(serde_json::json!({
                "role": "assistant",
                "content": null,
                "tool_calls": assistant_tool_calls,
            }));
            // Add tool result messages
            for tr in tool_results {
                api_messages.push(tr);
            }
        } else {
            api_messages.push(serde_json::json!({
                "role": "assistant",
                "content": assistant_tool_calls,
            }));
            api_messages.push(serde_json::json!({
                "role": "user",
                "content": tool_results,
            }));
        }
    }

    Err(AppError::Internal("AI 对话达到最大轮次限制".into()))
}

async fn call_anthropic(
    client: &reqwest::Client,
    cfg: &AiConfig,
    system_text: &str,
    messages: &[serde_json::Value],
    tools: &serde_json::Value,
) -> Result<(String, Vec<serde_json::Value>), AppError> {
    let url = format!("{}/v1/messages", cfg.base_url.trim_end_matches('/'));
    let resp = client.post(&url)
        .header("x-api-key", &cfg.api_key)
        .header("anthropic-version", "2023-06-01")
        .json(&serde_json::json!({
            "model": cfg.model,
            "max_tokens": 2048,
            "system": system_text,
            "messages": messages,
            "tools": tools,
        }))
        .send().await
        .map_err(|e| AppError::BadRequest(format!("API 请求失败: {e}")))?;

    let resp_json: serde_json::Value = resp.json().await
        .map_err(|e| AppError::BadRequest(format!("响应解析失败: {e}")))?;

    let content: Vec<serde_json::Value> = resp_json["content"]
        .as_array().cloned().unwrap_or_default();

    let mut texts = vec![];
    let mut tool_calls = vec![];
    for item in &content {
        if item["type"] == "text" {
            if let Some(t) = item["text"].as_str() { texts.push(t.to_string()); }
        }
        if item["type"] == "tool_use" {
            tool_calls.push(item.clone());
        }
    }
    Ok((texts.join("\n"), tool_calls))
}

async fn call_openai(
    client: &reqwest::Client,
    cfg: &AiConfig,
    messages: &[serde_json::Value],
    tools: &serde_json::Value,
) -> Result<(String, Vec<serde_json::Value>), AppError> {
    let openai_tools = anthropic_tools_to_openai(tools);
    let url = format!("{}/v1/chat/completions", cfg.base_url.trim_end_matches('/'));
    let resp = client.post(&url)
        .header("Authorization", format!("Bearer {}", cfg.api_key))
        .json(&serde_json::json!({
            "model": cfg.model,
            "max_tokens": 2048,
            "messages": messages,
            "tools": openai_tools,
            "tool_choice": "auto",
        }))
        .send().await
        .map_err(|e| AppError::BadRequest(format!("API 请求失败: {e}")))?;

    let resp_json: serde_json::Value = resp.json().await
        .map_err(|e| AppError::BadRequest(format!("响应解析失败: {e}")))?;

    let choice = &resp_json["choices"][0];
    let msg = &choice["message"];

    let text = msg["content"].as_str().unwrap_or("").to_string();
    let raw_calls = msg["tool_calls"].as_array().cloned().unwrap_or_default();

    let tool_calls: Vec<serde_json::Value> = raw_calls.iter().map(|tc| {
        let func = &tc["function"];
        serde_json::json!({
            "id": tc["id"],
            "name": func["name"],
        })
    }).collect();

    Ok((text, tool_calls))
}
