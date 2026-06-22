export const SCENE_STORAGE_KEY = 'omnichat-scene-sessions'
export const SCENE_DEFAULT_TITLE = '新对话'
export const SCENE_DEFAULT_TOP_K = 5
export const SCENE_PAGE_NAME = '3D 场景 Agent'
export const SCENE_KB_NONE = ''
export const SCENE_MAX_GLB_BYTES = 50 * 1024 * 1024

export const SCENE_TOOL_LABELS: Record<string, string> = {
  scene_list_objects: '列出场景对象',
  scene_move_object: '移动对象',
  scene_rotate_object: '旋转对象',
  scene_focus_object: '聚焦对象',
  scene_highlight_object: '高亮对象',
  scene_clear_highlight: '清除高亮',
  rag_search: '知识库检索'
}

export const SCENE_EXAMPLES_WITH_KB = [
  '这份场景文档里有哪些设备？',
  '把选中的模型向右移 1 米',
  '检索资料并解释当前选中模型'
]

export const SCENE_EXAMPLES_WITHOUT_KB = [
  '列出场景里有哪些模型',
  '把第一个模型绕 Y 轴转 45 度',
  '聚焦到选中的对象'
]

export const SCENE_CAPABILITIES = [
  {
    icon: '📦',
    title: '上传 GLB',
    desc: '本地上传模型，支持多文件与点击选中',
    requiresKb: false
  },
  {
    icon: '🖱️',
    title: '点击联动',
    desc: '点击画布选中模型，需要时再点顶栏「解释选中模型」',
    requiresKb: false
  },
  {
    icon: '📚',
    title: '场景 RAG',
    desc: '绑定知识库后检索场景说明文档',
    requiresKb: true
  },
  {
    icon: '🎮',
    title: 'Agent 控场景',
    desc: '文字或语音指令移动、旋转、聚焦模型',
    requiresKb: false
  }
] as const

export const SCENE_HINT =
  '与工具 Agent 不同：本页在 3D 画布中操作模型，AI 通过 scene_* 工具驱动浏览器执行变换。'
