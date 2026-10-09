// 精读 / 泛读的显示元数据：文案 + 徽章颜色（回顾列表、详情页共用一套映射）
export const MODE_META = {
  close: { text: '精读', badge: 'badge-primary' },
  skim: { text: '泛读', badge: 'badge-secondary' },
}

// 文献语言：圆形标识的文案 + 配色（回顾列表、研读页/详情页切换共用）
export const LANG_META = {
  zh: { text: 'Cn', circle: 'border-primary/30 bg-primary/5 text-primary' },
  en: { text: 'En', circle: 'border-accent/30 bg-accent/5 text-accent' },
}
