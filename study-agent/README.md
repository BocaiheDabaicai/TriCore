# study-agent（研读库）

> 个人研读助手：精读 + 泛读论文/课程，结构化笔记与阅读管理，服务于毕业论文写作练习与知识沉淀。
>
> 与 kb-agent 的区别：kb-agent 是"文档 → 分块 → 问答"的企业知识库；研读库是"结构化阅读管理"（精读模板、阅读状态、统计），数据模型本质不同，因此独立成项目（未来可成集群里的一个 Agent）。

## 现状（2026-09-10）

- **前端已搭好**（5175，静态数据）：
  - 研读页：左上传占位（PDF/图片下一步接入）+ 右 Markdown 笔记编辑器（CodeMirror 6）+ 选填文献信息（作者/出版时间/期刊）+ 底部实时时钟 + 精读/泛读切换动画
  - 回顾页：列表 + 左栏筛选（关键词搜索、精读/泛读、吸顶跟随）+ 右下角悬停展开的统计卡
  - 详情页：Markdown 渲染（marked）、标记完成
- **后端骨架**（8003）：应用入口 + SQLite 配置 + readings 模型；接口（api/readings.py）留到"构建后端"阶段
- **数据**：前端目前用静态数据模拟（`frontend/src/api/readings.js`），形状与未来真实接口一致（`{message, data}` + 同字段），后端就绪后只换这一个文件
- **下一步**：文件上传（PDF/图片）、精读模板字段与领域泛读追问集、草稿自动保存、接入 manager、LLM 辅助

## 启动

```powershell
# 前端（5175）
cd study-agent\frontend
npm install        # 首次
npm run dev        # http://localhost:5175

# 后端（8003，骨架阶段可不启动）
cd study-agent
.venv\Scripts\python.exe -m uvicorn main:app --port 8003
```

## 结构

```
study-agent/
├── main.py                  # 后端入口（8003，骨架）
├── core/database.py         # SQLite 配置（study_agent.db)
├── models/reading.py        # 研读记录模型
├── frontend/                # 前端（Vite 8 + Vue3 + daisyUI + pinia + vue-router）
│   ├── src/api/readings.js  # 数据层（现为静态模拟 = 接口契约草稿）
│   ├── src/components/      # Sidebar（hover 图标轨道）/ MarkdownEditor（CodeMirror 6）
│   └── src/views/           # StudyView（研读）/ ReviewView（回顾）/ ReviewDetailView（详情）
└── README.md
```

## 记录字段约定（接口契约草稿）

| 字段 | 说明 |
|---|---|
| title | 文献标题 |
| mode | 精读 `close` / 泛读 `skim` |
| status | 草稿 `draft` / 完成 `done` |
| author / published / journal | 作者 / 出版时间（YYYY-MM）/ 期刊（皆选填） |
| note | 笔记正文（Markdown） |
| created_at / updated_at | 时间戳 |

## 产品设想（讨论记录）

- 精读：上传 PDF/截图，左右对照一点一点写结构化笔记（为什么写/背景/现状/提出内容/验证/作用/局限/参考文献）
- 泛读：轻记录 + 自由总结（解决什么问题/方法不足/验证没有/局限），Web3 等领域另有专属追问集
- 月度配额统计（导师要求每月 20 篇）、领域/期刊分布——paper.md 记录 0001~0003
