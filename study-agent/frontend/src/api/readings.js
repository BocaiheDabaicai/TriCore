// 研读记录数据层 —— 现在返回静态数据，后端就绪后只改这一个文件（函数体换成 request.js 调用）
// 页面零改动的前提：静态数据的字段和将来真实接口一模一样
//   id / title / mode / status / author / published / journal / note / created_at / updated_at
// 返回结构也一致：{ message, data } —— 这一层现在就是"接口契约"的草稿

let nextId = 4   // 种子数据占用了 1~3

const store = [
  {
    id: 1,
    title: '数字化转型背景下工程项目知识转移机制研究',
    mode: 'close',
    status: 'draft',
    note: `## 为什么写
工程企业数字化转型投入大，但知识在项目间流失严重，作者想回答"数字化平台能否促进项目间知识转移"。

## 背景与现状
- 现有研究多停留在组织层面，缺少项目层面的实证
- 知识转移的测量指标不统一

## 提出内容
构建"数字化平台能力 → 知识转移意愿 → 转移绩效"模型，用 236 份问卷做结构方程。

待续：方法细节和局限还没读完…`,
    author: '王芳、刘洋',
    published: '2024-06',
    journal: '管理工程学报',
    created_at: '2026-09-08 21:10:00',
    updated_at: '2026-09-09 22:30:00',
  },
  {
    id: 2,
    title: '基于区块链的工程项目供应链信任机制研究',
    mode: 'skim',
    status: 'done',
    note: `- 解决的问题：工程供应链多主体协作中信任建立成本高、履约纠纷多
- 方法不足：智能合约只覆盖结算环节，治理机制不完善（谁有权修改合约没交代）
- 验证：只在单一试点项目验证，未在真实企业规模化验证
- 局限里明确写了"组织惯性可能抵消技术收益"——可作我论文的引用点`,
    author: '陈晨 等',
    published: '2023-11',
    journal: '工程管理学报',
    created_at: '2026-09-06 20:05:00',
    updated_at: '2026-09-06 21:40:00',
  },
  {
    id: 3,
    title: 'Human-AI Collaboration in Engineering Project Management: A Systematic Review',
    mode: 'close',
    status: 'done',
    note: `## 为什么写
AI 工具在工程管理中应用零散，缺少系统性梳理。

## 现状
综述 2015-2025 年 78 篇文献，把协作模式分成三类：AI 辅助决策、AI 自动执行、人机协同迭代。

## 可借鉴
- 文献筛选流程图直接可以套用
- 三类分法的提出方式（从现有文献中归纳，而不是自己拍脑袋分）值得学

## 局限
讨论部分承认样本以欧美项目为主，中国情境的外部效度存疑。`,
    author: 'Smith, J., & Lee, K.',
    published: '2025-02',
    journal: 'International Journal of Project Management',
    created_at: '2026-09-03 19:20:00',
    updated_at: '2026-09-04 23:10:00',
  },
]

// 模拟一点网络延迟，让 loading 状态真实可见
const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

function now() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

export async function listReadings() {
  await delay()
  const data = [...store].sort((a, b) => b.updated_at.localeCompare(a.updated_at))
  return { message: 'ok', total: data.length, data }
}

export async function getReading(id) {
  await delay(150)
  const row = store.find((r) => r.id === Number(id))
  return { message: row ? 'ok' : '记录不存在', data: row ?? null }
}

export async function createReading(payload) {
  await delay()
  const row = {
    id: nextId++,
    title: payload.title || '未命名文献',
    mode: payload.mode || 'close',
    status: 'draft',
    author: payload.author || '',
    published: payload.published || '',
    journal: payload.journal || '',
    note: payload.note || '',
    created_at: now(),
    updated_at: now(),
  }
  store.push(row)
  return { message: '已创建（静态数据）', data: row }
}

export async function updateReading(id, payload) {
  await delay()
  const row = store.find((r) => r.id === Number(id))
  if (!row) return { message: '记录不存在', data: null }
  Object.assign(row, payload, { updated_at: now() })
  return { message: '已保存（静态数据）', data: row }
}
