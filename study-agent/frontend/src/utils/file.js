// 附件（论文 PDF / 截图）的类型判断
export const ALLOWED_EXT = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp']

export function isAllowedAttachment(name) {
  const lower = (name || '').toLowerCase()
  return ALLOWED_EXT.some((ext) => lower.endsWith(ext))
}

const IMAGE_RE = /\.(png|jpe?g|gif|webp)$/i

export function isImageFile(name) {
  return IMAGE_RE.test(name || '')
}
