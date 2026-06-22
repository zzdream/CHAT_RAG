# OmniChat — 后端服务

基于 **Python + FastAPI** 的 AI 后端，对接 **DeepSeek**，并扩展 **RAG 知识库**、**工具 Agent** 与 **3D Scene Agent**。

## 环境要求

- Python 3.10+（推荐 3.11 / 3.12）
- pip

## 一、创建并激活虚拟环境

### macOS / Linux

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

激活成功后，终端提示符前会出现 `(venv)`。

### Windows（PowerShell）

```powershell
cd server
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Windows（CMD）

```cmd
cd server
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

## 二、退出虚拟环境

```bash
deactivate
```

## 三、重建环境（可选）

若虚拟环境损坏或需从零安装：

```bash
cd server
rm -rf venv          # Windows: rmdir /s /q venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 四、配置环境变量

项目使用 **两个文件**，不要搞混：

| 文件 | 作用 | 是否提交 Git |
|---|---|---|
| `.env.example` | 配置模板，给团队/自己参考格式 | ✅ 提交 |
| `.env` | **你的真实密钥**，本地运行读取这个 | ❌ 不提交（已在 .gitignore） |

### 正确写法

```bash
cp .env.example .env
# 然后只编辑 .env，填入你的真实 DEEPSEEK_API_KEY
```

`.env` 示例（真实配置写这里）：

```env
DEEPSEEK_API_KEY=sk-你的真实密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

> **为什么不要把真实 Key 写在 `.env.example`？**  
> 这个文件通常会提交到 Git。一旦 push 到 GitHub/Gitee，密钥就泄露了，别人可以用你的额度。

> `.env` 已在 `.gitignore` 中，只存在你本机，可以放心填真实 Key。

Phase 2～4 的 RAG、Agent、Scene 相关变量见 `.env.example` 底部注释块。

## 五、依赖说明

| 包 | 用途 |
|---|---|
| fastapi | Web 框架 |
| uvicorn | ASGI 服务器 |
| openai | 调用 DeepSeek（OpenAI 兼容接口） |
| langchain / langgraph | Agent 编排与工具调用 |
| chromadb | 向量存储 |
| FlagEmbedding / sentence-transformers | BGE-M3 嵌入 |
| python-dotenv | 读取 `.env` 配置 |
| python-multipart | FastAPI 表单 / 文件上传支持 |
| slowapi | 请求限流 |

## 六、启动服务

```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或：

```bash
python main.py
```

启动后访问：

- 根路径：<http://127.0.0.1:8000/>
- 健康检查：<http://127.0.0.1:8000/health>
- API 文档：<http://127.0.0.1:8000/docs>

## API 一览

| 接口 | 说明 | Phase |
|------|------|-------|
| `POST /chat/stream` | 自由对话 SSE | 1 |
| `GET/POST/DELETE /knowledge/bases` | 知识库管理 | 2 |
| `POST /knowledge/bases/{id}/documents` | 上传文档 | 2 |
| `POST /chat/rag/stream` | 知识库问答 SSE | 2 |
| `POST /chat/tools/stream` | Function Calling Agent SSE | 3 |
| `POST /chat/agent/stream` | LangChain Agent SSE | 3 |
| `POST /chat/scene/stream` | 3D 场景 Agent SSE | 4 |

### Phase 1：流式对话

`POST /chat/stream`，请求体与响应格式见下方「SSE 流式输出」。

### Phase 2：知识库 RAG

- 文档解析支持 txt、md、pdf、Word、Excel、PPT、图片（OCR）
- 分块写入 Chroma，问答时检索 Top-K 片段注入 Prompt
- `POST /chat/rag/stream` 请求体含 `knowledge_base_id`、`message`、`history` 等

### Phase 3：工具 Agent

- `POST /chat/tools/stream` — 原生 Function Calling
- `POST /chat/agent/stream` — LangChain Agent
- 内置工具：`calculator`、`text_formatter`；绑定知识库时可用 `rag_search`
- 环境变量：`TOOLS_MAX_ITERATIONS`、`AGENT_MAX_ITERATIONS`、`LLM_RETRY_*`

### Phase 4：Scene Agent

`POST /chat/scene/stream` — 在 Agent 请求基础上附加：

- `scene_objects` — 前端上报的对象快照（id、name、position、rotation、scale）
- `selected_object_id` — 当前选中对象

Agent 可用工具：

| 工具 | 作用 |
|------|------|
| `scene_list_objects` | 列出场景对象 |
| `scene_move_object` | 平移 |
| `scene_rotate_object` | 旋转 |
| `scene_focus_object` | 相机聚焦 |
| `scene_highlight_object` | 高亮 |
| `scene_clear_highlight` | 清除高亮 |
| `rag_search` | （可选）检索绑定的知识库 |

工具返回的 JSON 指令通过 SSE `scene_action` 事件推送给前端执行。

相关配置：`config_scene.py`（`SCENE_DEFAULT_SYSTEM`、`RATE_LIMIT_SCENE` 等）。

## 步骤 2：DeepSeek 聊天接口

### 请求示例

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好，用一句话介绍你自己"}'
```

### 响应示例

```json
{
  "content": "你好，我是 DeepSeek ...",
  "model": "deepseek-v4-flash"
}
```

### 可选系统提示词

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"写一首关于春天的诗","system":"你是一位中文诗人"}'
```

## 步骤 3：SSE 流式输出

### 接口

`POST /chat/stream`，请求体与 `/chat` 相同，响应为 **SSE（Server-Sent Events）**。

### curl 测试（`-N` 禁用缓冲，才能看到逐字输出）

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"用三句话介绍 FastAPI"}'
```

### SSE 数据格式

每个事件一行 `data:`，JSON payload：

```
data: {"content": "Fast"}

data: {"content": "API"}

data: {"done": true}
```

出错时：

```
data: {"error": "DeepSeek API 调用失败: ..."}
```

Scene Agent 额外事件示例：

```
data: {"scene_action": {"type": "move", "objectName": "bus", "axis": "x", "distance": 2}}
```

### 前端消费

- Phase 1：`web/src/api/chat.ts`、`web/src/hooks/use-chat-stream.ts`
- Phase 2：`web/src/api/chat-rag.ts`、`web/src/hooks/use-rag-chat.ts`
- Phase 3：`web/src/api/agent-chat.ts`、`web/src/hooks/use-agent-chat.ts`
- Phase 4：`web/src/api/scene-agent.ts`、`web/src/hooks/use-scene-agent.ts`

## 步骤 4：CORS + 前后端联调

### 后端 CORS

`main.py` 已配置 `CORSMiddleware`，默认允许：

- `http://localhost:5173`
- `http://127.0.0.1:5173`

可在 `.env` 中自定义：

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 前端代理

`web/.env` 中 `VITE_BASE_API=http://localhost:8000`，Vite 将 `/api/*` 代理到后端：

```
浏览器  /api/chat/stream  →  Vite 5173  →  FastAPI 8000/chat/stream
```

### 同时启动前后端

终端 1 — 后端：

```bash
cd server
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

终端 2 — 前端：

```bash
cd web
pnpm dev
```

浏览器打开 <http://localhost:5173/chat>，导航栏可切换各 Phase 页面。

## 运行测试

安装开发依赖后执行 pytest（**不会真实调用 DeepSeek**，LLM 已 mock）：

```bash
cd server
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

覆盖范围：健康检查、聊天校验、SSE 流式、RAG 检索、Agent 工具链、Scene 工具与 `/chat/scene/stream`。

## 项目结构

```
server/
├── main.py                      # 应用入口，挂载 Phase 1–4
├── app/
│   ├── config.py                # 基础配置
│   ├── config_rag.py            # RAG 配置
│   ├── config_agent.py          # Agent 配置
│   ├── config_scene.py          # Scene Agent 配置
│   ├── bootstrap_rag.py         # 挂载 knowledge + chat_rag
│   ├── bootstrap_tools.py       # 挂载 chat_tools
│   ├── bootstrap_agent.py       # 挂载 chat_agent
│   ├── bootstrap_scene.py       # 挂载 chat_scene
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── chat_rag.py
│   │   ├── chat_agent.py
│   │   └── chat_scene.py
│   ├── services/
│   │   ├── llm.py
│   │   ├── rag/                 # 解析、分块、嵌入、检索
│   │   ├── agent/               # langchain_agent、scene_agent
│   │   └── tools/               # calculator、rag_search、scene_actions
│   └── api/routes/
│       ├── health.py
│       ├── chat.py
│       ├── knowledge.py
│       ├── chat_rag.py
│       ├── chat_tools.py
│       ├── chat_agent.py
│       └── chat_scene.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── tests/
├── .env.example
└── README.md
```

## 七、常见问题

### `pip install` 很慢

可使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### RAG 首次启动下载模型很慢

在 `.env` 中设置 HuggingFace 镜像：

```env
HF_ENDPOINT=https://hf-mirror.com
```

### macOS 提示 `command not found: python3`

先安装 Python：<https://www.python.org/downloads/>

或使用 Homebrew：

```bash
brew install python
```

### Windows 无法执行 Activate.ps1

PowerShell 以管理员运行：

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
