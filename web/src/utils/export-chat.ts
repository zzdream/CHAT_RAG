import type { ChatSession } from '@/types/chat'

export function sanitizeFilename(title: string): string {
  const trimmed = title.trim() || '新对话'
  return trimmed.replace(/[\\/:*?"<>|]/g, '_').slice(0, 48)
}

function downloadText(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function buildSessionExportPayload(session: ChatSession) {
  return {
    title: session.title,
    system: session.system ?? '',
    model: session.model ?? null,
    temperature: session.temperature ?? null,
    createdAt: session.createdAt,
    updatedAt: session.updatedAt,
    messages: session.messages.map(item => ({
      role: item.role,
      content: item.content,
      usage: item.usage ?? null
    }))
  }
}

export function buildSessionMarkdownContent(
  session: ChatSession,
  exportedAt: Date = new Date()
): string {
  const lines: string[] = [
    `# ${session.title}`,
    '',
    `- 导出时间：${exportedAt.toLocaleString('zh-CN')}`,
    `- 模型：${session.model ?? '默认'}`,
    `- 温度：${session.temperature ?? '默认'}`,
    ''
  ]

  if (session.system?.trim()) {
    lines.push('## 系统提示词', '', session.system.trim(), '')
  }

  lines.push('## 对话记录', '')

  for (const message of session.messages) {
    const roleLabel = message.role === 'user' ? '用户' : 'AI'
    lines.push(`### ${roleLabel}`, '', message.content.trim(), '')
    if (message.usage) {
      lines.push(
        `> Token：输入 ${message.usage.prompt_tokens} · 输出 ${message.usage.completion_tokens} · 合计 ${message.usage.total_tokens}`,
        ''
      )
    }
  }

  return lines.join('\n')
}

export function exportSessionAsJson(session: ChatSession) {
  const payload = buildSessionExportPayload(session)
  const filename = `${sanitizeFilename(session.title)}.json`
  downloadText(filename, JSON.stringify(payload, null, 2), 'application/json;charset=utf-8')
}

export function exportSessionAsMarkdown(session: ChatSession) {
  const filename = `${sanitizeFilename(session.title)}.md`
  downloadText(filename, buildSessionMarkdownContent(session), 'text/markdown;charset=utf-8')
}
