// 架构图（总体视图）的绘图工具 —— 坐标 / 连线 / 卡片样式，纯函数
import { CARD_W, CARD_H } from '../data/architecture'

// 矩形定位（分区 / 守护框通用）
export function rectStyle(r) {
  return { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px` }
}

// 连线路径：默认"右中点 → 左中点"的直角折线（H-V-H）；points 可自定义拐点
export function edgePath(e, nodes) {
  if (e.points) return `M ${e.points.map((p) => p.join(' ')).join(' L ')}`
  const a = nodes.find((n) => n.key === e.from)
  const b = nodes.find((n) => n.key === e.to)
  const x1 = a.x + CARD_W
  const y1 = a.y + CARD_H / 2
  const x2 = b.x
  const y2 = b.y + CARD_H / 2
  if (Math.abs(y1 - y2) < 1) return `M ${x1} ${y1} H ${x2}`
  const mx = (x1 + x2) / 2
  return `M ${x1} ${y1} H ${mx} V ${y2} H ${x2}`
}

// 节点卡片的外框样式（规划 = 虚线、不受 manager 管 = 主色浅底、正常 = 默认）
export function cardClass(n) {
  if (n.planned) return 'border-dashed border-base-content/25 bg-base-100/40 text-base-content/50 hover:border-base-content/50'
  if (n.unmanaged) return 'border-primary/40 bg-primary/5 hover:border-primary/70'
  return 'border-base-300 bg-base-100 hover:border-primary/60'
}
