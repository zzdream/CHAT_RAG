export const AGENT_STORAGE_KEY = 'omnichat-agent-sessions'
export const AGENT_DEFAULT_TITLE = '新对话'
export const AGENT_DEFAULT_TOP_K = 5
export const AGENT_PAGE_NAME = '工具 Agent'
export const AGENT_KB_NONE = ''

export const AGENT_TOOL_LABELS: Record<string, string> = {
  calculator: '计算器',
  text_formatter: '文本格式化',
  rag_search: '知识库检索'
}

export const AGENT_CAPABILITIES = [
  {
    icon: '📚',
    title: '查文档',
    desc: '绑定知识库后，自动检索资料再回答',
    requiresKb: true
  },
  {
    icon: '🔢',
    title: '算数字',
    desc: '调用计算器精确运算，不靠模型猜测',
    requiresKb: false
  },
  {
    icon: '✏️',
    title: '改文本',
    desc: '大小写转换、去空格、JSON 美化等',
    requiresKb: false
  }
] as const

export const AGENT_EXAMPLES_WITH_KB = [
  '这份资料主要讲了什么？',
  '把资料里的关键数字加起来',
  '检索内容并把标题转成大写'
]

export const AGENT_EXAMPLES_WITHOUT_KB = [
  '123 乘以 456 等于多少？',
  '把 hello world 转成大写',
  '计算 (100 + 50) * 2'
]

export const AGENT_RAG_DIFF_HINT =
  '知识库问答会固定先检索再回答；工具 Agent 由 AI 自主决定何时查文档、何时计算或格式化。'
