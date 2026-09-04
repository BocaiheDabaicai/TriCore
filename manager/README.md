# manager（服务管理守护服务）

统一管理各 Agent 服务的启动、停止、运行状态与日志。端口 8002。

它是整个项目**唯一需要手动启动的进程**——启动后自动拉起 `services.json` 里 `auto_start` 的服务，并持续监控：进程死了自动重启（连续失败 5 次转 error，需人工处理）；手动 stop 的不会被拉起。

## 使用

```powershell
cd manager
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn main:app --port 8002
```

## 接口

| 接口 | 说明 |
|---|---|
| `GET /api/v1/services` | 所有服务状态 |
| `POST /api/v1/services/{name}/start` | 启动 |
| `POST /api/v1/services/{name}/stop` | 停止 |
| `POST /api/v1/services/{name}/restart` | 重启 |
| `POST /api/v1/services/start-all` | 全部启动（auto_start 项） |
| `POST /api/v1/services/stop-all` | 全部停止 |
| `GET /api/v1/services/{name}/logs?lines=100` | 日志（尾部 N 行） |

## 新增服务

往 `services.json` 的 services 数组加一项即可，**无需改代码**：

```json
{ "name": "doc-review-agent", "port": 8003, "cwd": "doc-review-agent", "command": "{python} -m uvicorn main:app --port 8003", "auto_start": true }
```

- `{python}` 会被解析为该服务自己目录下的 venv 解释器（Windows/Linux 自动适配）
- 前端服务（Vite/nginx）同样是进程，照此加配置即可管理
- 日志落在 `manager/logs/{name}.log`
