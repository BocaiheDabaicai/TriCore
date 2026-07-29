use actix_web::{HttpRequest, HttpResponse, web};
use sqlx::{PgPool, Row, Column};

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

const SYSTEM_PROMPT: &str = r#"你是 TriCore 企业系统的 AI 助手。你可以查询数据库进行数据分析，也可以调用后端 API 执行操作任务。

## 可用工具
1. **list_tables** — 列出数据库中所有数据表
2. **describe_table(table_name)** — 查看指定表的列结构
3. **run_query(sql)** — 执行只读 SELECT 查询进行数据分析
4. **list_apis** — 列出所有可用的后端 API（含必填字段说明）
5. **call_api(method, path, body?)** — 调用后端 API 执行操作（创建/更新/删除等）

## 任务执行流程
当用户要求你执行操作时：

1. **理解意图** — 弄清楚用户想做什么，需要哪些信息
2. **收集信息** — 如果用户已提供所有必填信息，直接执行；如有缺失（含重要可选字段如配送信息），**直接回复询问**
3. **执行操作** — 调用 call_api。如果不确定 API 路径或必填字段，先调用 list_apis 查看
4. **确认结果** — 反馈执行结果。如需验证可调用 run_query

避免不必要的工具调用：能一步完成的不要分两步，不确定 API 时才查 list_apis。

## 数据库表概览
销售: categories, users, products, orders, order_items, bundle_sales, bundle_items, return_orders, return_items
OA: employees, workflow_forms, workflow_steps, workflow_archives, workflow_templates
库存: warehouses, stock_in_records, stock_in_items, stock_out_records, stock_out_items, warehouse_inventory, issues
主数据: customers, departments, positions, vehicles
规章制度: regulation_categories, regulation_files

回答请使用中文，简洁清晰。"#;

fn build_tools() -> serde_json::Value {
    serde_json::json!([
        {
            "name": "list_tables",
            "description": "列出数据库中所有可用的数据表",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "describe_table",
            "description": "查看指定表的所有列信息：列名、数据类型、是否可为空、默认值",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "要查看的表名"
                    }
                },
                "required": ["table_name"]
            }
        },
        {
            "name": "run_query",
            "description": "执行只读 SELECT 查询进行数据分析。支持聚合函数(COUNT/SUM/AVG/MAX/MIN)、JOIN、GROUP BY、ORDER BY、WHERE 筛选、子查询等完整 SQL 能力。用于统计汇总、趋势分析、数据探索等场景。查询结果以 Markdown 表格返回。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SELECT 查询语句。仅允许只读查询，自动追加 LIMIT 100 若无指定。"
                    }
                },
                "required": ["sql"]
            }
        },
        {
            "name": "list_apis",
            "description": "列出所有可用的后端 API 接口，包含 HTTP 方法、路径、描述和必填字段。在执行创建/更新/删除等操作前，先调用此工具了解有哪些接口可用。",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "call_api",
            "description": "调用后端 API 执行操作。支持创建、更新、删除等写操作，也可用于查询。执行前确保已收集所有必填字段。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP 方法：GET, POST, PUT, PATCH, DELETE",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]
                    },
                    "path": {
                        "type": "string",
                        "description": "API 路径，如 /sales/orders 或 /master-data/customers"
                    },
                    "body": {
                        "type": "object",
                        "description": "请求体（JSON 对象），POST/PUT/PATCH 时需要。仅包含 API 要求的字段。"
                    }
                },
                "required": ["method", "path"]
            }
        }
    ])
}

fn get_api_catalog() -> String {
    r#"## 后端 API 目录

### 认证 (auth)
| POST | /auth/login | 员工登录 | body: {employee_no, password} |

### 销售 (sales)
| POST | /sales/auth/login | 销售用户登录 | body: {username, password} |
| GET | /sales/users | 销售用户列表 | query: role?, page?, per_page? |
| GET | /sales/users/{id} | 获取销售用户 | |
| POST | /sales/users | 创建销售用户 | body: {username, password, role, full_name, phone?, fingerprint_data?, face_data?, email?} |
| PUT | /sales/users/{id} | 更新销售用户 | body: {full_name?, phone?, email?, is_active?} |
| GET | /sales/products | 产品列表 | query: category?, page?, per_page? |
| GET | /sales/products/{id} | 获取产品 | |
| POST | /sales/products | 创建产品 | body: {sku, name, original_price, description?, surprise_discount_percent?, subsidized_price?, unit?, category?} |
| PUT | /sales/products/{id} | 更新产品 | body: {name?, description?, original_price?, category?, is_active?} |
| GET | /sales/orders | 订单列表 | query: status?, customer_id?, page?, per_page? |
| GET | /sales/orders/{id} | 获取订单(含明细) | |
| POST | /sales/orders | 创建订单。注意：创建前应询问用户是否需要配送，如需配送则提供 vehicle_info(车牌号) 和 driver_info(司机姓名/电话) | body: {customer_id, items:[{product_id,quantity,unit_price}], salesperson_id?, discount_amount?, vehicle_info?, driver_info?, notes?} |
| PUT | /sales/orders/{id} | 更新订单(仅pending) | body: {customer_id?, items?, discount_amount?, notes?} |
| PATCH | /sales/orders/{id}/status | 改订单状态 | body: {status: pending/confirmed/processing/shipped/delivered/cancelled} |
| GET | /sales/bundles | 捆绑销售列表 | query: page?, per_page? |
| GET | /sales/bundles/{id} | 获取捆绑销售 | |
| POST | /sales/bundles | 创建捆绑销售 | body: {bundle_name, salesperson_id, merchant_id, bundle_price, items:[{product_id,quantity,unit_price}]} |
| GET | /sales/returns | 退单列表 | query: page?, per_page? |
| GET | /sales/returns/{id} | 获取退单 | |
| POST | /sales/returns | 创建退单 | body: {order_id, salesperson_id, reason, items:[{product_id,quantity,refund_amount}]} |
| PATCH | /sales/returns/{id}/status | 改退单状态 | body: {status: pending/approved/rejected/completed} |
| GET | /sales/categories | 产品分类列表 | |
| POST | /sales/categories | 创建分类 | body: {name, description?} |
| PUT | /sales/categories/{id} | 更新分类 | body: {name?, description?, is_active?} |
| DELETE | /sales/categories/{id} | 删除分类 | |
| GET | /sales/dashboard | 销售仪表板 | |

### OA (oa)
| GET | /oa/employees | 员工列表 | query: department?, status?, page?, per_page? |
| GET | /oa/employees/{id} | 获取员工 | |
| POST | /oa/employees | 创建员工 | body: {employee_no, name, department, position, email, password, phone?, role?} |
| PUT | /oa/employees/{id} | 更新员工 | body: {name?, department?, position?, email?, phone?, status?, role?} |
| DELETE | /oa/employees/{id} | 删除员工 | |
| GET | /oa/workflows | 工作流列表 | query: status?, creator_id?, page?, per_page? |
| GET | /oa/workflows/{id} | 获取工作流 | |
| POST | /oa/workflows | 创建工作流 | body: {title, steps:[{step_number,reviewer_id}], description?, form_data?} |
| PUT | /oa/workflows/{id} | 更新工作流 | body: {title?, description?, form_data?} |
| DELETE | /oa/workflows/{id} | 删除工作流 | |
| POST | /oa/workflows/{id}/submit | 提交审批 | |
| GET | /oa/workflows/{id}/steps | 查看审批步骤 | |
| POST | /oa/workflows/{wf_id}/steps/{step_id}/review | 审批步骤 | body: {action: approve/reject, comment?, reject_mode?: full/node} |
| GET | /oa/archives | 审批归档 | query: page?, per_page? |
| GET | /oa/dashboard | OA仪表板 | |
| GET | /oa/templates | 模板列表 | |
| POST | /oa/templates | 创建模板 | body: {name, steps:[{step_number,reviewer_id}], description?} |
| PUT | /oa/templates/{id} | 更新模板 | body: {name?, description?, steps?} |
| DELETE | /oa/templates/{id} | 删除模板 | |

### 库存 (inventory)
| GET | /inventory/warehouses | 仓库列表 | |
| POST | /inventory/warehouses | 创建仓库 | body: {name, location?, manager_id?} |
| PUT | /inventory/warehouses/{id} | 更新仓库 | body: {name?, location?, manager_id?, is_active?} |
| DELETE | /inventory/warehouses/{id} | 删除仓库 | |
| GET | /inventory/warehouse-inventory/{product_id} | 各仓库存 | |
| POST | /inventory/adjust | 调整库存 | body: {product_id, operator_id, adjustments:[{warehouse_id,quantity}], notes?} |
| GET | /inventory/stock-in | 入库单列表 | query: status?, warehouse_id?, page?, per_page? |
| POST | /inventory/stock-in | 创建入库单 | body: {warehouse_id, operator_id, items:[{product_id,expected_quantity,actual_quantity}], order_id?, notes?} |
| PUT | /inventory/stock-in/{id}/verify | 盘点入库 | body: {items:[{item_id,actual_quantity}]} |
| PUT | /inventory/stock-in/{id}/complete | 完成入库 | |
| GET | /inventory/stock-out | 出库单列表 | query: status?, warehouse_id?, page?, per_page? |
| POST | /inventory/stock-out | 创建出库单 | body: {warehouse_id, operator_id, items:[{product_id,quantity}], vehicle_info?, driver_info?, notes?} |
| PUT | /inventory/stock-out/{id}/ship | 发货 | body: {vehicle_info?, driver_info?} |
| PUT | /inventory/stock-out/{id}/deliver | 送达 | |
| GET | /inventory/issues | 问题列表 | query: status?, severity?, page?, per_page? |
| POST | /inventory/issues | 报告问题 | body: {related_type, related_id, description, reported_by, severity?, assigned_to?} |
| PUT | /inventory/issues/{id} | 更新问题 | body: {description?, severity?, status?, assigned_to?} |
| PUT | /inventory/issues/{id}/resolve | 解决问题 | body: {resolution} |
| GET | /inventory/dashboard | 库存仪表板 | |

### 主数据 (master-data)
| GET | /master-data/customers | 客户列表 | |
| POST | /master-data/customers | 创建客户 | body: {name, contact_person?, phone?, email?, address?, notes?} |
| PUT | /master-data/customers/{id} | 更新客户 | body: {name?, contact_person?, phone?, email?, address?, notes?, is_active?} |
| DELETE | /master-data/customers/{id} | 删除客户 | |
| GET | /master-data/departments | 部门列表 | |
| POST | /master-data/departments | 创建部门 | body: {name, description?} |
| PUT | /master-data/departments/{id} | 更新部门 | body: {name?, description?, is_active?} |
| DELETE | /master-data/departments/{id} | 删除部门 | |
| GET | /master-data/positions | 职位列表 | |
| POST | /master-data/positions | 创建职位 | body: {name, department_id?, description?} |
| PUT | /master-data/positions/{id} | 更新职位 | body: {name?, department_id?, description?, is_active?} |
| DELETE | /master-data/positions/{id} | 删除职位 | |
| GET | /master-data/vehicles | 车辆列表 | |
| POST | /master-data/vehicles | 创建车辆 | body: {plate_number, model?, capacity?, driver_name?, driver_phone?, notes?} |
| PUT | /master-data/vehicles/{id} | 更新车辆 | body: {plate_number?, model?, driver_name?, driver_phone?, status?, notes?, is_active?} |
| DELETE | /master-data/vehicles/{id} | 删除车辆 | |

### 规章制度 (regulations)
| GET | /regulations/categories | 分类列表 | |
| POST | /regulations/categories | 创建分类 | body: {name} |
| DELETE | /regulations/categories/{id} | 删除分类 | |
| GET | /regulations/files | 文件列表 | query: title?, category_id?, page?, per_page? |
| POST | /regulations/files | 上传文件 | multipart: title, category_id?, notes?, file |
| PUT | /regulations/files/{id} | 更新文件信息 | body: {title?, category_id?, notes?} |
| DELETE | /regulations/files/{id} | 删除文件 | |

注意：
- {id} 表示路径参数，用实际 UUID 替换
- body 中带 ? 的为可选字段
- 所有 POST/PUT 请求，body 中不带 ? 的是必填字段
- 调用前请先确认用户已提供所有必填字段"#.to_string()
}

fn validate_sql(sql: &str) -> Result<String, String> {
    let trimmed = sql.trim();
    let upper = trimmed.to_uppercase();

    if !upper.starts_with("SELECT") && !upper.starts_with("WITH") && !upper.starts_with("EXPLAIN") {
        return Err("仅允许 SELECT / WITH / EXPLAIN 查询".into());
    }
    if !upper.contains("SELECT") {
        return Err("查询必须包含 SELECT".into());
    }

    let stripped = trimmed.trim_end_matches(';').trim().to_string();
    if stripped.contains(';') {
        return Err("不允许执行多条语句".into());
    }

    if upper.contains("LIMIT") {
        Ok(stripped)
    } else {
        Ok(format!("{} LIMIT 100", stripped))
    }
}

fn cell_value(row: &sqlx::postgres::PgRow, col: &str) -> String {
    if let Ok(v) = row.try_get::<Option<String>, _>(col) {
        return v.unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<i64>, _>(col) {
        return v.map(|n| n.to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<i32>, _>(col) {
        return v.map(|n| n.to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<rust_decimal::Decimal>, _>(col) {
        return v.map(|d| d.to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<f64>, _>(col) {
        return v.map(|n| format!("{:.2}", n)).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<bool>, _>(col) {
        return v.map(|b| b.to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<chrono::DateTime<chrono::Utc>>, _>(col) {
        return v.map(|d| d.format("%Y-%m-%d %H:%M").to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<chrono::NaiveDateTime>, _>(col) {
        return v.map(|d| d.format("%Y-%m-%d %H:%M").to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<chrono::NaiveDate>, _>(col) {
        return v.map(|d| d.format("%Y-%m-%d").to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<uuid::Uuid>, _>(col) {
        return v.map(|u| u.to_string()).unwrap_or_else(|| "NULL".into());
    }
    if let Ok(v) = row.try_get::<Option<serde_json::Value>, _>(col) {
        return v.map(|j| j.to_string()).unwrap_or_else(|| "NULL".into());
    }
    "?".into()
}

async fn call_api_internal(
    method: &str,
    path: &str,
    body: Option<&serde_json::Value>,
    port: &str,
    token: &str,
) -> String {
    let client = reqwest::Client::new();
    let url = format!("http://127.0.0.1:{}/api{}", port, path);

    let req = match method.to_uppercase().as_str() {
        "GET" => client.get(&url),
        "DELETE" => client.delete(&url),
        "POST" => {
            let b = body.cloned().unwrap_or(serde_json::json!({}));
            client.post(&url).json(&b)
        }
        "PUT" => {
            let b = body.cloned().unwrap_or(serde_json::json!({}));
            client.put(&url).json(&b)
        }
        "PATCH" => {
            let b = body.cloned().unwrap_or(serde_json::json!({}));
            client.patch(&url).json(&b)
        }
        _ => return format!("不支持的 HTTP 方法: {method}"),
    };

    match req
        .header("Authorization", format!("Bearer {}", token))
        .header("Content-Type", "application/json")
        .send()
        .await
    {
        Ok(resp) => {
            let status = resp.status();
            match resp.text().await {
                Ok(text) => {
                    let short: String = if text.len() > 2000 {
                        format!("{}...(已截断)", &text[..2000])
                    } else {
                        text
                    };
                    format!("HTTP {} — {}", status.as_u16(), short)
                }
                Err(e) => format!("HTTP {} — 读取响应失败: {e}", status.as_u16()),
            }
        }
        Err(e) => format!("API 调用失败: {e}"),
    }
}

async fn execute_tool(name: &str, args: &serde_json::Value, pool: &PgPool, port: &str, token: &str) -> String {
    match name {
        "list_apis" => get_api_catalog(),
        "call_api" => {
            let method = args["method"].as_str().unwrap_or("GET");
            let path = args["path"].as_str().unwrap_or("");
            if path.is_empty() {
                return "请提供 API 路径".into();
            }
            // Block recursive calls and login
            if path.starts_with("/ai/chat") || path.starts_with("/auth/login") {
                return "不允许通过 AI 调用此接口".into();
            }
            let body = args.get("body");
            call_api_internal(method, path, body, port, token).await
        }
        "list_tables" => {
            match sqlx::query(
                "SELECT table_name FROM information_schema.tables \
                 WHERE table_schema='public' AND table_type='BASE TABLE' \
                 ORDER BY table_name"
            ).fetch_all(pool).await {
                Ok(rows) => {
                    let tables: Vec<String> = rows.iter()
                        .map(|r| r.get::<String, _>("table_name"))
                        .collect();
                    format!("数据库共有 {} 个表：\n\n{}", tables.len(),
                        tables.iter().enumerate()
                            .map(|(i, t)| format!("{}. {}", i + 1, t))
                            .collect::<Vec<_>>().join("\n"))
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "describe_table" => {
            let table_name = args["table_name"].as_str().unwrap_or("");
            if table_name.is_empty() {
                return "请指定表名".into();
            }
            match sqlx::query(
                "SELECT column_name, data_type, is_nullable, \
                 COALESCE(column_default::text, '') AS column_default \
                 FROM information_schema.columns \
                 WHERE table_schema='public' AND table_name=$1 \
                 ORDER BY ordinal_position"
            ).bind(table_name).fetch_all(pool).await {
                Ok(rows) => {
                    if rows.is_empty() {
                        return format!("表 '{}' 不存在或没有列", table_name);
                    }
                    let mut result = format!("表 **{}** 的结构：\n\n", table_name);
                    result.push_str("| 列名 | 类型 | 可为空 | 默认值 |\n| --- | --- | --- | --- |\n");
                    for row in &rows {
                        let col: String = row.get("column_name");
                        let dt: String = row.get("data_type");
                        let nl: String = row.get("is_nullable");
                        let def: String = row.get("column_default");
                        result.push_str(&format!("| {} | {} | {} | {} |\n",
                            col, dt, nl, if def.is_empty() { "-" } else { &def }));
                    }
                    result
                }
                Err(e) => format!("查询失败: {e}")
            }
        }
        "run_query" => {
            let sql = args["sql"].as_str().unwrap_or("");
            if sql.is_empty() {
                return "请提供 SQL 查询语句".into();
            }
            let safe_sql = match validate_sql(sql) {
                Ok(s) => s,
                Err(e) => return format!("SQL 校验失败: {e}"),
            };

            let _ = sqlx::query("SET LOCAL statement_timeout = '10000'").execute(pool).await;

            let rows = match sqlx::query(&safe_sql).fetch_all(pool).await {
                Ok(r) => r,
                Err(e) => return format!("查询执行失败: {e}"),
            };

            if rows.is_empty() {
                return "查询结果为空。".into();
            }

            let columns: Vec<String> = rows[0].columns().iter()
                .map(|c| c.name().to_string())
                .collect();

            let mut result = format!("共 {} 行：\n\n", rows.len());
            result.push_str("| ");
            result.push_str(&columns.join(" | "));
            result.push_str(" |\n|");
            result.push_str(&columns.iter().map(|_| "---").collect::<Vec<_>>().join("|"));
            result.push_str("|\n");

            for row in &rows {
                result.push_str("| ");
                let vals: Vec<String> = columns.iter()
                    .map(|col| {
                        let v = cell_value(row, col);
                        if v.len() > 100 {
                            format!("{}...", &v[..97])
                        } else {
                            v
                        }
                    })
                    .collect();
                result.push_str(&vals.join(" | "));
                result.push_str(" |\n");
            }
            result
        }
        _ => format!("未知工具: {name}")
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
    req: HttpRequest,
    pool: web::Data<PgPool>,
    port: web::Data<String>,
    body: web::Json<ChatRequest>,
) -> Result<HttpResponse, AppError> {
    let token = req
        .headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .unwrap_or("")
        .to_string();

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
    let max_rounds = 10;
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
            let args = &tc["input"];
            let result = execute_tool(&tool_name, args, pool.get_ref(), port.get_ref(), &token).await;

            if use_openai {
                tool_results.push(serde_json::json!({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result,
                }));
                assistant_tool_calls.push(serde_json::json!({
                    "id": tool_id,
                    "type": "function",
                    "function": { "name": tool_name, "arguments": serde_json::to_string(args).unwrap_or_else(|_| "{}".into()) }
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
            "max_tokens": 4096,
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
            "max_tokens": 4096,
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
        let args: serde_json::Value = serde_json::from_str(
            func["arguments"].as_str().unwrap_or("{}")
        ).unwrap_or(serde_json::json!({}));
        serde_json::json!({
            "id": tc["id"],
            "name": func["name"],
            "input": args,
        })
    }).collect();

    Ok((text, tool_calls))
}
