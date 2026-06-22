# LLM — 后端服务

基于 **Python + FastAPI** 的 AI 聊天机器人后端，对接 **DeepSeek** 模型 API。

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
# pip install fastapi uvicorn openai python-multipart python-dotenv
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

`.env.example` 示例（模板，用占位符即可）：

```env
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

> **为什么不要把真实 Key 写在 `.env.example`？**  
> 这个文件通常会提交到 Git。一旦 push 到 GitHub/Gitee，密钥就泄露了，别人可以用你的额度。

> `.env` 已在 `.gitignore` 中，只存在你本机，可以放心填真实 Key。

## 五、依赖说明

| 包 | 用途 |
|---|---|
| fastapi | Web 框架 |
| uvicorn | ASGI 服务器 |
| openai | 调用 DeepSeek（OpenAI 兼容接口） |
| python-dotenv | 读取 `.env` 配置 |
| python-multipart | FastAPI 表单 / 文件上传支持 |

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
- 聊天接口：<http://127.0.0.1:8000/chat>（POST）
- 流式聊天：<http://127.0.0.1:8000/chat/stream>（POST，SSE）
- API 文档：<http://127.0.0.1:8000/docs>

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

每个事件一行 `data:`，JSON  payload：

```
data: {"content": "Fast"}

data: {"content": "API"}

data: {"done": true}
```

出错时：

```
data: {"error": "DeepSeek API 调用失败: ..."}
```

### 前端消费

已实现于 `web/src/api/chat.ts` 与 `web/src/hooks/use-chat-stream.ts`。

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

浏览器打开 <http://localhost:5173/chat>，即可使用 AI 聊天页面。

## 运行测试

安装开发依赖后执行 pytest（**不会真实调用 DeepSeek**，LLM 已 mock）：

```bash
cd server
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

覆盖范围：`/health`、请求校验（敏感词/历史条数）、SSE 流式响应、`build_messages` 多轮拼接。

## 项目结构

```
server/
├── main.py                 # 应用入口，uvicorn 启动点
├── app/
│   ├── config.py           # 环境变量与配置
│   ├── schemas/
│   │   └── chat.py         # 聊天请求/响应模型
│   ├── services/
│   │   └── llm.py          # DeepSeek 调用（含 stream=True）
│   └── api/
│       └── routes/
│           ├── health.py   # 健康检查
│           └── chat.py     # POST /chat、POST /chat/stream
├── requirements.txt
├── requirements-dev.txt  # pytest 等开发依赖
├── pytest.ini
├── tests/                # API 与单元测试
├── .env.example
└── README.md
```

## 七、常见问题

### `pip install` 很慢

可使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
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
