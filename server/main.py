"""
应用入口 —— 相当于前端的 main.ts

职责：
1. 创建 FastAPI 应用实例（类似 createApp()）
2. 注册中间件（类似 Vue Router 守卫 / Express middleware）
3. 挂载路由模块（类似 router.use() / app.use(routes)）
4. 直接运行时可启动 uvicorn 服务器

启动方式：
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  或：source venv/bin/activate  &&  python main.py
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routes import chat, health
from app.bootstrap_rag import setup_rag
from app.bootstrap_tools import setup_tools
from app.bootstrap_agent import setup_agent
from app.bootstrap_scene import setup_scene
from app.config import get_settings
from app.core.limiter import limiter

# 读取 .env 配置（类似前端的 import.meta.env / process.env）
settings = get_settings()

# 创建应用实例，类似 const app = express()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="OmniChat 后端服务 — 全栈 AI 应用 API",
)

# 限流：按 IP 统计，超出返回 429
app.state.limiter = limiter

# exception_handler「注册异常处理器」的方法 把 rate_limit_handler 注册到 FastAPI 里：以后只要任何地方抛出 RateLimitExceeded，框架就自动调这个函数
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"请求过于频繁，请稍后再试（{exc.detail}）"},
    )

# CORS 中间件：允许浏览器跨域访问（前端 5173 → 后端 8000 时需要）
# 类似 nginx 或 devServer 里配的 Access-Control-Allow-Origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,          # 白名单域名列表
    allow_origin_regex=settings.cors_origin_regex,  # 或用正则匹配（开发环境更方便）
    allow_credentials=True,                       # 允许携带 cookie
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],                          # 允许所有请求头
    expose_headers=["*"],
)

# 挂载路由模块 —— 每个 router 文件管理一组接口
# 类似：app.use('/chat', chatRouter)
app.include_router(health.router)
app.include_router(chat.router)
setup_rag(app)
setup_tools(app)
setup_agent(app)
setup_scene(app)


@app.get("/") # 这是 装饰器（decorator） 语法：把下面的函数「注册」成某个 HTTP 接口。等价于 app.get("/", read_root)
def read_root() -> dict[str, str]:  # 返回值类型为dict[str, str]
    """
    GET / —— 根路径，返回服务状态和可用接口列表
    类似前端首页的一个 status JSON
    """
    return {
        "message": "OmniChat API is running",
        "docs": "/docs",                    # FastAPI 自动生成的 Swagger 文档
        "health": "/health",
        "chat": "/chat",
        "chat_stream": "/chat/stream",      # 前端实际使用的流式聊天接口
        "knowledge": "/knowledge/bases",
        "chat_rag_stream": "/chat/rag/stream",
        "chat_tools_stream": "/chat/tools/stream",
        "chat_agent_stream": "/chat/agent/stream",
        "chat_scene_stream": "/chat/scene/stream",
    }


# Python 惯例：直接运行此文件时执行（类似 if (require.main === module)）
# Python 里很常见的一种写法，用来区分：这个文件是被直接运行，还是被别的文件 import 进来。
# main.py 是被当作模块导入的，它的 __name__ 是 "main"，main.py 被直接运行时 __name__ 是 "__main__"
if __name__ == "__main__":
    import uvicorn  # 导入 uvicorn 模块

    uvicorn.run(
        "main:app",              # 模块路径:应用变量名，main.py 里的 app 变量
        host=settings.host,      # 监听地址
        port=settings.port,      # 监听端口
        reload=settings.debug,   # 热重载，改代码自动重启（类似 vite HMR）
    )
