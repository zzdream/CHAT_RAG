import { defineComponent, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useChatStream } from '@/hooks/use-chat-stream'
import { STORAGE_KEY } from '@/utils/chat-session'

vi.mock('@/api/chat', () => ({
  streamChat: vi.fn()
}))

import { streamChat } from '@/api/chat'

const mockedStreamChat = vi.mocked(streamChat)

function mountChatHook() {
  const state: { chat: ReturnType<typeof useChatStream> | null } = { chat: null }

  const Wrapper = defineComponent({
    setup() {
      state.chat = useChatStream()
      return () => null
    }
  })

  mount(Wrapper)
  return state as { chat: ReturnType<typeof useChatStream> }
}

async function* fakeStream(events: Array<{ content?: string; usage?: object; done?: boolean; error?: string }>) {
  for (const event of events) {
    yield event
  }
}

describe('useChatStream', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('首条用户消息会更新会话标题', async () => {
    mockedStreamChat.mockReturnValue(fakeStream([{ content: '你好' }, { done: true }]) as never)

    const { chat } = mountChatHook()
    chat.input.value = '用 Python 写快速排序算法示例'
    await chat.sendMessage()
    await flushPromises()

    expect(chat.messages.value).toHaveLength(2)
    expect(chat.messages.value[0].content).toContain('Python')
    expect(chat.sessions.value[0].title).toBe('用 Python 写快速排序算法示例')
  })

  it('流式结束后写入 assistant 内容与 usage', async () => {
    mockedStreamChat.mockReturnValue(
      fakeStream([
        { content: '你好' },
        {
          usage: {
            prompt_tokens: 5,
            completion_tokens: 3,
            total_tokens: 8
          }
        },
        { done: true }
      ]) as never
    )

    const { chat } = mountChatHook()
    chat.input.value = '你好'
    await chat.sendMessage()
    await flushPromises()

    const assistant = chat.messages.value[1]
    expect(assistant.role).toBe('assistant')
    expect(assistant.content).toBe('你好')
    expect(assistant.usage).toEqual({
      prompt_tokens: 5,
      completion_tokens: 3,
      total_tokens: 8
    })
    expect(chat.getMessageUsage(assistant)?.total_tokens).toBe(8)
  })

  it('会话数据会持久化到 localStorage', async () => {
    mockedStreamChat.mockReturnValue(fakeStream([{ content: 'OK' }, { done: true }]) as never)

    const { chat } = mountChatHook()
    chat.input.value = '持久化测试'
    await chat.sendMessage()
    await flushPromises()
    await nextTick()

    const raw = localStorage.getItem(STORAGE_KEY)
    expect(raw).toBeTruthy()
    expect(raw).toContain('持久化测试')
    expect(raw).toContain('OK')
  })
})
