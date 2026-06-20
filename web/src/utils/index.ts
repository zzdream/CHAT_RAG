/**
 * 示例工具函数：格式化日期为 YYYY-MM-DD
 * @example formatDate(new Date()) // '2026-06-15'
 */
export function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}
