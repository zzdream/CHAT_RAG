import { describe, expect, it, vi } from 'vitest'
import {
  buildSessionExportPayload,
  buildSessionMarkdownContent,
  exportSessionAsJson,
  sanitizeFilename
} from '@/utils/export-chat'
import type { ChatSession } from '@/types/chat'

const sampleSession: ChatSession = {
  id: 'session-1',
  title: 'React/Vue 对比',
  system: '你是助教',
  model: 'deepseek-v4-flash',
  temperature: 0.8,
  createdAt: 1000,
  updatedAt: 2000,
  messages: [
    {
      id: 'u1',
      role: 'user',
      content: '有什么区别？'
    },
    {
      id: 'a1',
      role: 'assistant',
      content: '两者都是组件化框架。',
      usage: {
        prompt_tokens: 10,
        completion_tokens: 20,
        total_tokens: 30
      }
    }
  ]
}

describe('sanitizeFilename', () => {
  it('替换非法字符并限制长度', () => {
    expect(sanitizeFilename('  hello:world?  ')).toBe('hello_world_')
    expect(sanitizeFilename('')).toBe('新对话')
    expect(sanitizeFilename('a'.repeat(60)).length).toBe(48)
  })
})

describe('buildSessionExportPayload', () => {
  it('导出 JSON 结构包含会话元信息与消息', () => {
    expect(buildSessionExportPayload(sampleSession)).toEqual({
      title: 'React/Vue 对比',
      system: '你是助教',
      model: 'deepseek-v4-flash',
      temperature: 0.8,
      createdAt: 1000,
      updatedAt: 2000,
      messages: [
        { role: 'user', content: '有什么区别？', usage: null },
        {
          role: 'assistant',
          content: '两者都是组件化框架。',
          usage: {
            prompt_tokens: 10,
            completion_tokens: 20,
            total_tokens: 30
          }
        }
      ]
    })
  })
})

describe('buildSessionMarkdownContent', () => {
  it('生成包含标题、系统提示与 Token 的 Markdown', () => {
    const exportedAt = new Date('2026-06-17T10:00:00')
    const markdown = buildSessionMarkdownContent(sampleSession, exportedAt)

    expect(markdown).toContain('# React/Vue 对比')
    expect(markdown).toContain('## 系统提示词')
    expect(markdown).toContain('你是助教')
    expect(markdown).toContain('### 用户')
    expect(markdown).toContain('有什么区别？')
    expect(markdown).toContain('> Token：输入 10 · 输出 20 · 合计 30')
  })
})

describe('exportSessionAsJson', () => {
  it('触发浏览器下载', () => {
    const click = vi.fn()
    const revokeObjectURL = vi.fn()
    const createObjectURL = vi.fn(() => 'blob:mock')

    vi.stubGlobal('URL', {
      createObjectURL,
      revokeObjectURL
    })

    const anchor = {
      href: '',
      download: '',
      click
    }
    vi.spyOn(document, 'createElement').mockReturnValue(anchor as unknown as HTMLElement)

    exportSessionAsJson(sampleSession)

    expect(createObjectURL).toHaveBeenCalled()
    expect(anchor.download).toBe('React_Vue 对比.json')
    expect(click).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock')

    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })
})
