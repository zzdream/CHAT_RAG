export const CHAT_MODELS = [
  { label: 'DeepSeek V4 Flash', value: 'deepseek-v4-flash' },
  { label: 'DeepSeek V4 Pro', value: 'deepseek-v4-pro' }
] as const

export const DEFAULT_CHAT_MODEL = 'deepseek-v4-flash'
export const DEFAULT_TEMPERATURE = 0.7
export const MIN_TEMPERATURE = 0
export const MAX_TEMPERATURE = 2
export const TEMPERATURE_STEP = 0.1
