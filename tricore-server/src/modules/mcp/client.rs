use log::{info, error};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;

use crate::modules::mcp::models::{McpServer, McpTool};

/// Global MCP client state: holds connected servers and their tools
static MCP_STATE: std::sync::LazyLock<Arc<Mutex<McpState>>> = std::sync::LazyLock::new(|| {
    Arc::new(Mutex::new(McpState::new()))
});

struct McpState {
    tools: Vec<McpTool>,
    // For SSE transport, stores HTTP client and URL
    sse_clients: HashMap<Uuid, SseConnection>,
}

struct SseConnection {
    url: String,
    session_id: Option<String>,
}

impl McpState {
    fn new() -> Self {
        Self { tools: vec![], sse_clients: HashMap::new() }
    }
}

/// Connect to all enabled MCP servers and collect their tools
pub async fn refresh_tools(servers: &[McpServer]) {
    let mut state = MCP_STATE.lock().await;
    state.tools.clear();
    state.sse_clients.clear();

    for server in servers {
        if !server.is_enabled {
            continue;
        }
        match server.transport.as_str() {
            "sse" => {
                if let Some(ref url) = server.url {
                    match discover_sse_tools(server.id, server.name.clone(), url).await {
                        Ok(tools) => {
                            let count = tools.len();
                            state.sse_clients.insert(server.id, SseConnection { url: url.clone(), session_id: None });
                            state.tools.extend(tools);
                            info!("MCP SSE server '{}' connected: {} tools", server.name, count);
                        }
                        Err(e) => error!("MCP SSE server '{}' failed: {}", server.name, e),
                    }
                }
            }
            "stdio" => {
                match discover_stdio_tools(&server).await {
                    Ok(tools) => {
                        let count = tools.len();
                        state.tools.extend(tools);
                        info!("MCP stdio server '{}' connected: {} tools", server.name, count);
                    }
                    Err(e) => error!("MCP stdio server '{}' failed: {}", server.name, e),
                }
            }
            _ => error!("Unknown MCP transport: {}", server.transport),
        }
    }
    info!("MCP refresh complete: {} total tools from {} servers", state.tools.len(), servers.iter().filter(|s| s.is_enabled).count());
}

/// Get all currently available MCP tools
pub async fn list_tools() -> Vec<McpTool> {
    MCP_STATE.lock().await.tools.clone()
}

/// Call an MCP tool by name
pub async fn call_tool(tool_name: &str, args: &Value) -> String {
    let state = MCP_STATE.lock().await;

    // Find which server owns this tool
    let tool = state.tools.iter().find(|t| t.name == tool_name);
    if tool.is_none() {
        return format!("未找到 MCP 工具: {}", tool_name);
    }
    let tool = tool.unwrap();
    let server_id = tool.server_id;

    // Check if it's an SSE connection
    if let Some(conn) = state.sse_clients.get(&server_id) {
        return call_sse_tool(conn, tool_name, args).await;
    }

    // For stdio, we'd need to spawn a process. For now, use SSE fallback or return error
    format!("MCP 工具 '{}' 调用失败: stdio 模式暂不支持在线调用，请使用 SSE 模式", tool_name)
}

async fn discover_sse_tools(server_id: Uuid, server_name: String, url: &str) -> Result<Vec<McpTool>, String> {
    let client = reqwest::Client::new();
    let base = url.trim_end_matches('/');

    // MCP SSE handshake: GET the SSE endpoint, receive session endpoint
    let resp = client.get(base)
        .header("Accept", "text/event-stream")
        .send().await
        .map_err(|e| format!("连接失败: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("HTTP {}", resp.status().as_u16()));
    }

    let body = resp.text().await.map_err(|e| format!("读取响应失败: {}", e))?;

    // Parse SSE to find the session endpoint
    let session_url = parse_sse_endpoint(&body, base)?;

    // Send tools/list request to the session endpoint
    let list_req = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    });

    let resp = client.post(&session_url)
        .header("Content-Type", "application/json")
        .json(&list_req)
        .send().await
        .map_err(|e| format!("tools/list 请求失败: {}", e))?;

    let json: Value = resp.json().await.map_err(|e| format!("解析响应失败: {}", e))?;

    let tools_arr = json["result"]["tools"]
        .as_array()
        .ok_or("响应中缺少 tools 数组")?;

    let tools: Vec<McpTool> = tools_arr.iter().map(|t| McpTool {
        server_name: server_name.clone(),
        server_id,
        name: t["name"].as_str().unwrap_or("unknown").to_string(),
        description: t["description"].as_str().map(|s| s.to_string()),
        input_schema: t.get("inputSchema").cloned().unwrap_or(serde_json::json!({})),
    }).collect();

    Ok(tools)
}

fn parse_sse_endpoint(body: &str, base: &str) -> Result<String, String> {
    for line in body.lines() {
        if let Some(data) = line.strip_prefix("data: ") {
            if let Ok(json) = serde_json::from_str::<Value>(data) {
                if let Some(endpoint) = json["endpoint"].as_str() {
                    if endpoint.starts_with("http") {
                        return Ok(endpoint.to_string());
                    }
                    return Ok(format!("{}{}", base, endpoint));
                }
            }
        }
    }
    // Fallback: assume the base URL is also the message endpoint
    Ok(base.to_string())
}

async fn call_sse_tool(conn: &SseConnection, tool_name: &str, args: &Value) -> String {
    let client = reqwest::Client::new();
    let url = &conn.url;

    let call_req = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args,
        }
    });

    match client.post(url)
        .header("Content-Type", "application/json")
        .json(&call_req)
        .send()
        .await
    {
        Ok(resp) => {
            match resp.json::<Value>().await {
                Ok(json) => {
                    if let Some(err) = json["error"].as_object() {
                        format!("MCP 错误: {}", err.get("message").and_then(|m| m.as_str()).unwrap_or("未知"))
                    } else {
                        json["result"]["content"]
                            .as_array()
                            .and_then(|arr| {
                                arr.iter()
                                    .filter_map(|c| c["text"].as_str())
                                    .collect::<Vec<_>>()
                                    .first()
                                    .map(|s| s.to_string())
                            })
                            .unwrap_or_else(|| json["result"].to_string())
                    }
                }
                Err(e) => format!("MCP 响应解析失败: {}", e),
            }
        }
        Err(e) => format!("MCP 请求失败: {}", e),
    }
}

async fn discover_stdio_tools(server: &McpServer) -> Result<Vec<McpTool>, String> {
    let cmd = server.command.as_ref().ok_or("stdio 模式需要指定 command")?;
    let args: Vec<String> = server.args.as_ref()
        .and_then(|a| serde_json::from_str(a).ok())
        .unwrap_or_default();

    let mut child = tokio::process::Command::new(cmd)
        .args(&args)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| format!("启动进程失败: {}", e))?;

    let mut stdin = child.stdin.take().ok_or("无法获取 stdin")?;
    let stdout = child.stdout.take().ok_or("无法获取 stdout")?;

    use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

    // Send initialize request
    let init_req = serde_json::json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": { "name": "tricore-server", "version": "0.1.0" }
        }
    });
    let mut init_str = serde_json::to_string(&init_req).unwrap();
    init_str.push('\n');
    stdin.write_all(init_str.as_bytes()).await.map_err(|e| format!("写入失败: {}", e))?;

    // Read response lines
    let reader = BufReader::new(stdout);
    let mut lines = reader.lines();
    let mut initialized = false;

    while let Ok(Some(line)) = lines.next_line().await {
        if line.trim().is_empty() { continue; }
        if let Ok(json) = serde_json::from_str::<Value>(&line) {
            if json["id"] == 1 && json["result"].is_object() {
                // Got initialize response, now send tools/list
                let list_req = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                });
                let mut list_str = serde_json::to_string(&list_req).unwrap();
                list_str.push('\n');
                stdin.write_all(list_str.as_bytes()).await.map_err(|e| format!("写入失败: {}", e))?;
            } else if json["id"] == 2 {
                let tools_arr = json["result"]["tools"].as_array()
                    .ok_or("tools/list 响应缺少 tools 数组")?;

                let server_id = server.id;
                let server_name = server.name.clone();
                let tools: Vec<McpTool> = tools_arr.iter().map(|t| McpTool {
                    server_name: server_name.clone(),
                    server_id,
                    name: t["name"].as_str().unwrap_or("unknown").to_string(),
                    description: t["description"].as_str().map(|s| s.to_string()),
                    input_schema: t.get("inputSchema").cloned().unwrap_or(serde_json::json!({})),
                }).collect();

                initialized = true;
                // Send initialized notification
                let notify = serde_json::json!({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                });
                let mut notify_str = serde_json::to_string(&notify).unwrap();
                notify_str.push('\n');
                let _ = stdin.write_all(notify_str.as_bytes()).await;

                // Kill the child process since we only needed discovery
                let _ = child.start_kill();
                return Ok(tools);
            }
        }
        if initialized { break; }
    }

    let _ = child.start_kill();
    Err("MCP stdio 握手失败：未收到 tools/list 响应".into())
}
