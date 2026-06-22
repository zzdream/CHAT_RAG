# OmniChat — 前端

Vue 3 + TypeScript + Vite 前端，通过 Vite 代理联调 FastAPI 后端，覆盖 **流式对话**、**知识库 RAG**、**工具 Agent** 与 **3D 场景 Agent**。

## 功能

### 通用

- 多会话、流式 SSE、Markdown / 代码高亮
- 角色设定、模型选择、温度滑块（按会话保存）
- Token 用量展示、导出 Markdown / JSON
- 深色 / 浅色主题与消息动效
- 顶部导航切换各功能页

### 按 Phase

| 页面 | 路由 | 说明 |
|------|------|------|
| 自由对话 | `/chat` | Phase 1 基础聊天 |
| 知识库 | `/knowledge` | Phase 2 上传与管理文档 |
| 知识库问答 | `/rag-chat` | Phase 2 RAG 流式问答 + 引用 |
| 工具 Agent | `/agent-chat` | Phase 3 工具调用步骤展示 |
| 3D 场景 Agent | `/scene-agent` | Phase 4 GLB 渲染 + Agent 控场景 |

### 3D 场景 Agent（Phase 4）

- 侧栏上传 `.glb` / `.gltf`，Three.js 渲染（Meshopt + KTX2 + Draco）
- 点击模型选中（蓝色 BoxHelper），顶栏「解释选中模型」手动提问
- 文字 / Web Speech API 语音输入
- 接收 SSE `scene_action`，执行平移、旋转、聚焦、高亮
- 可选绑定知识库

## 启动

```bash
pnpm install
pnpm dev
```

浏览器访问：<http://localhost:5173/chat>

各页面入口见顶部导航，或直接访问 `/rag-chat`、`/agent-chat`、`/scene-agent`。

## 环境变量

`.env` / `.env.development`：

```env
VITE_APP_TITLE=OmniChat
VITE_BASE_API=http://localhost:8000
```

## 测试

```bash
pnpm test:run        # 跑一遍 Vitest（CI / 提交前）
pnpm test            # 监听模式，改代码自动重跑
pnpm test:coverage   # 带覆盖率报告
pnpm typecheck       # vue-tsc 类型检查
pnpm build           # 类型检查 + 生产构建
```

测试文件集中在 `tests/`，目录结构与 `src/` 对应。

业务代码在 `src/`，通过 `@/` 别名引用。

## 联调说明

前端请求统一走 `/api/*` 前缀，Vite 代理到 `http://localhost:8000`：

| 前端 | 后端 |
|------|------|
| `/api/chat/stream` | `/chat/stream` |
| `/api/chat/rag/stream` | `/chat/rag/stream` |
| `/api/chat/agent/stream` | `/chat/agent/stream` |
| `/api/chat/scene/stream` | `/chat/scene/stream` |
| `/api/knowledge/*` | `/knowledge/*` |

需先启动后端（见 `../server/README.md`）。

## 主要文件

```
src/
├── router/index.ts              # 路由：chat / knowledge / rag-chat / agent-chat / scene-agent
├── api/
│   ├── chat.ts                  # Phase 1 SSE
│   ├── chat-rag.ts              # Phase 2 RAG SSE
│   ├── agent-chat.ts            # Phase 3 Agent SSE
│   ├── scene-agent.ts           # Phase 4 Scene SSE
│   └── knowledge.ts             # 知识库 CRUD
├── hooks/
│   ├── use-chat-stream.ts       # 自由对话
│   ├── use-rag-chat.ts          # 知识库问答
│   ├── use-agent-chat.ts        # 工具 Agent
│   ├── use-scene-agent.ts       # Scene Agent 会话 + SSE
│   ├── use-scene-three.ts       # Three.js 场景、GLB、拾取、scene_action 执行
│   ├── use-speech-recognition.ts# Web Speech 语音输入
│   └── use-knowledge.ts         # 知识库管理
├── views/
│   ├── chat/index.vue
│   ├── knowledge/index.vue
│   ├── rag-chat/index.vue
│   ├── agent-chat/index.vue
│   └── scene-agent/index.vue
├── types/                       # chat / rag / agent / scene 类型
└── constants/                   # 各模块常量

public/
├── basis/                       # KTX2 纹理解码器（GLB 贴图）
└── draco/gltf/                  # Draco 网格解码器
```

## 3D 模型说明

- 支持标准 GLB/GLTF；若模型使用 KTX2 贴图或 Draco 压缩，解码器已放在 `public/basis`、`public/draco`
- 单文件大小上限见 `src/constants/scene.ts`（默认 50MB）
- 推荐本地测试模型：任意 `.glb`；复杂模型可参考 simrender 导出的 FarmVehicle / bus 等
