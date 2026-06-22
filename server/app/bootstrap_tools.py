"""
Phase 3 工具调用引导 —— 注册路由，不修改 Phase 1 / Phase 2 业务模块。
"""

from fastapi import FastAPI

from app.api.routes import chat_tools


def setup_tools(app: FastAPI) -> None:
    """挂载 Function Calling 练习路由。"""
    app.include_router(chat_tools.router)
