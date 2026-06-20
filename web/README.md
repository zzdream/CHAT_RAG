# Study LLM — 前端

Vue 3 + TypeScript + Vite 聊天界面，通过 Vite 代理联调 FastAPI 后端。

## 功能

- 多会话、流式 SSE、Markdown / 代码高亮
- 角色设定、模型选择、温度滑块（按会话保存）
- Token 用量展示、导出 Markdown / JSON
- 深色 / 浅色主题与消息动效

## 启动

```bash
pnpm install
pnpm dev
```

浏览器访问：<http://localhost:5173/chat>

## 环境变量

`.env` / `.env.development`：

```env
VITE_APP_TITLE=Study LLM
VITE_BASE_API=http://localhost:8000
```

## 测试

```bash
pnpm test:run        # 跑一遍 Vitest（CI / 提交前）
pnpm test            # 监听模式，改代码自动重跑
pnpm test:coverage   # 带覆盖率报告
```

测试文件集中在 `tests/`，目录结构与 `src/` 对应：

```
tests/
├── utils/chat-session.test.ts    # 标题截断、history、localStorage 解析
├── utils/export-chat.test.ts     # 导出 Markdown/JSON
└── hooks/use-chat-stream.test.ts # 聊天 hook（mock SSE）
```

业务代码仍在 `src/`，通过 `@/` 别名引用。

## 联调说明

前端请求 `/api/chat/stream`，Vite 代理到 `http://localhost:8000/chat/stream`。

需先启动后端（见 `../server/README.md`）。

## 主要文件

```
src/
├── api/chat.ts              # SSE 流式 API
├── constants/chat.ts        # 模型列表、温度默认值
├── hooks/use-chat-stream.ts # 聊天逻辑 hook
├── utils/export-chat.ts     # 导出 Markdown / JSON
├── views/chat/index.vue     # 聊天页面
└── types/chat.ts            # 类型定义
```
