# rpa-agent（办公自动化执行器）

用浏览器自动化把**固定流程**做掉：按"单元"驱动网页系统（金蝶、OA）完成重复录入。端口 8004，自带操作台（5176）。

## 现状（2026-09-24）

**骨架建成、演示单元跑通**——操作台、浏览器执行器、运行留痕、截图资料库全部可用；真实业务单元尚未实现（等页面截图到位再写选择器）。

| 单元 | 状态 |
|---|---|
| `demo_form` 演示：本地表单 | ✅ 跑通（打开本地 HTML → 填三个字段 → 提交 → 断言回显） |
| `kd_add_supplier` ① 添加供应商 | 骨架（`SEL` 占位 + 输入字段 + 5 步声明，`run()` 直接报"等截图"） |

后续单元按依赖顺序叠加：② 手机号码 → ③ 激活手机号码 → ④ 分配车辆 → ⑤ 收货地址 → ⑥ 价格策略分配 →（⑦ 1~n 条循环留痕 → ⑧ 从 OA 取数 → ⑨ 回 OA 点批准）。

## 快速启动

```powershell
cd rpa-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 配置：复制 .env.example 为 .env（金蝶 / OA 网址、浏览器通道）
.venv\Scripts\python.exe -m uvicorn main:app --port 8004
```

操作台在 `frontend/`（5176）：`npm install` 后 `npm run dev`。日常由 manager 一起拉起（services.json 两条：`rpa-agent` / `rpa-frontend`）。

浏览器用**系统已装的 Edge**（`BROWSER_CHANNEL=msedge`），不需要 `playwright install` 下载百兆的 chromium。

## 结构

```
rpa-agent/
├── main.py                  # 装配 + 启动时把遗留的"执行中"运行标成被打断
├── api/
│   ├── health.py            # GET /api/health —— manager 探活用（只读内存快照，绝不碰浏览器）
│   ├── browser_api.py       # 浏览器状态 / 打开 / 关闭 / 强制结束残留进程
│   ├── unit_api.py          # 单元清单 / 投一次运行 / 人工标记已验证
│   ├── runs.py              # 运行详情（步骤 + 日志）/ 取消 / 取截图
│   ├── shots.py             # 截图资料库：上传 / 列表 / 查看 / 删除
│   └── stats.py             # 给管理端「数据」视角报数
├── core/
│   ├── config.py            # .env 读取 + 数据目录
│   ├── database.py          # SQLite 连接（check_same_thread=False：浏览器线程也要写库）
│   ├── browser.py           # ★ BrowserWorker：Playwright 专用线程 + 任务队列
│   └── registry.py          # 扫描 units/*.py 自动注册单元
├── services/
│   ├── unit_runner.py       # 单元执行：ctx.step 分步、留痕、失败留现场、协作式取消
│   └── run_service.py       # 运行记录读写、日志落盘、启动清理
├── units/                   # ← 加单元就加一个文件，别的代码都不用改
│   ├── demo_form.py
│   └── kd_add_supplier.py
├── static/demo_form.html    # 演示单元用的本地页面
├── frontend/                # 操作台（5176）
└── data/                    # 运行期数据（不进 git）：登录态、每步截图、上传的页面截图
★ 运行留痕：SQLite rpa_agent.db（runs / run_steps / unit_meta）+ logs/run_{id}.log
```

## 两个核心设计

### 1. 浏览器锁在一条专用线程里（`core/browser.py`）

- Playwright 用**同步 API**，所有调用都发生在一条专用 worker 线程；别的线程只能通过 `submit()` 投任务
- 好处一：**机械上不可能冻住事件循环**。同步 API 放 FastAPI 路由里会冻住事件循环 → manager 探活 2 秒超时 → 服务被判死重启（kb-agent 踩过这个坑），关进线程后这个 bug 写不出来
- 好处二：**互斥是队列白送的**。浏览器同一时刻只能被一个操作驱动，任务串行执行，不需要额外加锁
- 浏览器**懒加载**（第一次用才启动）：headful 冷启动 1~3 秒，放在服务启动路径会拖超 manager 的 30 秒启动窗口
- 登录要过验证码 → headful + 人工登录一次 + `data/browser_profile` 持久化登录态
- 三种自愈：浏览器被外部关掉 → 自动重启；启动失败（残留进程占着用户目录）→ 清理后重试一次；服务重启 → 遗留运行标成 `interrupted`

### 2. 单元 = 一条业务数据 × 一个操作环节

```python
# units/xxx.py —— 加一个单元只要这一个文件
UNIT = {
    "key": "kd_xxx", "cn_name": "① 某某", "order": 1, "env": "kingdee",
    "desc": "一句话说明",
    "inputs": [{"key": "name", "label": "名称", "required": True, "example": ""}],
    "steps": [{"key": "enter", "cn_name": "进入列表"}, ...],   # 顺序必须与代码一致
}

def run(ctx):
    with ctx.step("enter"):          # 进来自动标"进行中"，出来自动标"成功"
        ctx.page.goto(...)           # 出异常自动标"失败" + 截图 + dump HTML
```

- `ctx` 给的东西：`ctx.page`（Playwright 页面）、`ctx.inputs`（这次运行的输入）、`ctx.step(key)`、`ctx.log(msg)`、`ctx.snap(name)`（截图挂到当前步）
- **选择器集中在文件顶部 `SEL` 字典**：系统改版只改这一块；优先用 label 文本 / name 属性这类稳定特征，不用位置选择器
- 运行时：`POST /api/v1/units/{key}/run` 建运行记录 + 投队列 + 立刻返回 `run_id`，前端轮询 —— 这就是项目里写的"任务队列"形状（入队返回 id + 轮询），不是让请求干等
- **双判定才算跑通**：系统断言（脚本没报错、回显对）+ 人工确认（打开目标系统核对过结果，操作台上点"标记为已跑通"）

## 已知限制与待办

- 真实单元的选择器待页面截图到位后逐个补（截图传操作台「截图资料库」，放在 `data/shots/`）
- 长流程耗时可能到分钟级 → 与 kb-agent 一样，将来该上真正的任务队列（现在已经是"入队 + 轮询"的形状，改造面很小）
- 尚无 n 条加点信息的循环（单元⑦）、尚无 OA 取数（单元⑧）
- **写生产系统要先有授权**：先用最小验证量跑通、量出准确率与耗时，再去谈 IT + 业务部门的书面授权
