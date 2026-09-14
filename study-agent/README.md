# study-agent（研读库）

> 个人研读助手：精读 + 泛读论文/课程，结构化笔记与阅读管理，服务于毕业论文写作练习与知识沉淀。
>
> 与 kb-agent 的区别：kb-agent 是"文档 → 分块 → 问答"的企业知识库；研读库是"结构化阅读管理"（精读模板、分类标签、统计），数据模型本质不同，因此独立成项目。**保持独立：不接入调度器、不作为集群问答 Agent**——仅由 manager 守护（统一起停/探活/日志）、在管理端统一查看。

## 现状（2026-09-14）

- **后端已建成**（8003）：readings（研读记录 增/改/查 + 附件下载端点）+ sources（寻文站点）两组接口；SQLite 启动自动建表；寻文站点首次启动（表为空）自动灌入种子（paper.md 记录 0003 的清单）
- **前端已接真实接口**（5175）：请求层 `src/api/request.js`（axios 实例，走 Vite 代理 `/api` → 8003）；`readings.js` / `sources.js` 由静态数据切为 HTTP 调用（返回结构不变，页面零改动）
- 四个页面：
  - 研读页（精读 = 左论文右笔记）：左区点击/拖拽上传 PDF/图片，**上传后直接内嵌显示翻阅**——PDF 调浏览器内置阅读器（翻页/缩放）、图片直接显示；新选文件保存前先本地预览，保存后自动上传；右侧 Markdown 编辑器（CodeMirror 6）+ 选填行（作者/出版时间/期刊/分类标签）+ 底部实时时钟；**自动保存**——停笔 1.2 秒自动存（首次=创建并切到 `/edit/:id`，之后=更新），离开页面兜底补存，底部显示保存状态；「保存」按钮 = 立即保存并去详情
  - 回顾页：列表头检索行（搜索框 + 高级筛选开关）——开关开启后左侧出现筛选面板（类型/标签两组标签按钮），关闭时重置面板内筛选；列表卡片第二行显示小领域徽章与只读星级（没评分 / 没领域的不显示）
  - 寻文页：文献站点按类型汇总，点击跳转去找论文
  - 详情页：Markdown 渲染；**评分**（5 星 + 半星 = 10 分制，悬停预览、点星即存、再点同一颗取消）与**小领域**（最多 3 个，可自创或从候选复用，徽章 × 可删）直接在本页设置——只改这两个字段时不走「修改」流程；底部一行 [论文文件名（精读，点击打开）] … [删除（确认弹窗）] [修改]
- **修改流程**：详情页「修改」→ `/edit/:id` 研读页编辑模式（带入全部内容），按钮变「更新」（PUT）
- **附件与删除**：`POST /api/readings/{id}/attachment`（multipart 存 `uploads/{id}_{文件名}`，换新附件先删旧文件）；`GET .../attachment` 浏览器内直接打开（PDF/图片内联）；`DELETE /api/readings/{id}` 连带删除附件文件
- **全局轻提示**（pinia store + ToastHost）：创建/更新/上传/删除成功与各类失败都有顶部提示，2.6 秒自动消失
- **已接入 manager**：`manager/services.json` 增加 study-agent（8003）/ study-frontend（5175）两条
- **下一步**：精读模板字段与领域泛读追问集、LLM 辅助；uploads/ 目录进 .gitignore（数据策略落实时）

## 启动

```powershell
# 后端（8003）
cd study-agent
python -m venv .venv                                          # 首次
.venv\Scripts\python.exe -m pip install -r requirements.txt  # 首次
.venv\Scripts\python.exe -m uvicorn main:app --port 8003

# 前端（5175）
cd study-agent\frontend
npm install        # 首次
npm run dev        # http://localhost:5175
```

或由 manager 一键拉起（8003 + 5175 已在服务清单里）。

## 结构

```
study-agent/
├── main.py                  # 后端入口（8003）
├── core/database.py         # SQLite 配置 + get_db
├── models/                  # reading.py（研读记录）/ source.py（寻文站点）
├── api/                     # readings.py / sources.py（接口 + 种子）
├── frontend/                # 前端（Vite 8 + Vue3 + daisyUI + pinia + vue-router）
│   ├── src/api/             # request.js（axios 实例）+ readings.js / sources.js（接口封装）
│   ├── src/utils/           # 通用纯函数：reading.js（精读/泛读显示元数据）/ file.js（附件类型判断）/ format.js（时钟格式化）
│   ├── src/stores/          # toast.js（全局轻提示，pinia Options 写法）
│   ├── src/components/      # Sidebar（hover 图标轨道）/ MarkdownEditor（CodeMirror 6）/ ToastHost / StarRating（星级，详情页交互 + 列表只读）
│   └── src/views/           # StudyView / ReviewView / ReviewDetailView / SourcesView
└── README.md
```

## 记录字段约定（接口契约）

| 字段 | 说明 |
|---|---|
| title | 文献标题 |
| mode | 精读 `close` / 泛读 `skim` |
| tag | 分类标签（选填，可自创或复用已有） |
| rating | 评分 0-10（详情页点星设置，0 = 未打分；半星 = 1 分） |
| domains | 小领域列表（0-3 个，如 数字化 / 智能体；JSON 存字符串数组） |
| author / published / journal | 作者 / 出版时间（YYYY-MM）/ 期刊（皆选填） |
| note | 笔记正文（Markdown） |
| attachment | 论文文件名（精读，上传后写入；原文件在 uploads/） |
| created_at / updated_at | 时间戳 |

## 产品设想（讨论记录）

- 精读：上传 PDF/截图，左右对照一点一点写结构化笔记（为什么写/背景/现状/提出内容/验证/作用/局限/参考文献）
- 泛读：轻记录 + 自由总结（解决什么问题/方法不足/验证没有/局限），Web3 等领域另有专属追问集
- 月度配额统计（导师要求每月 20 篇）、领域/期刊分布——paper.md 记录 0001~0003
