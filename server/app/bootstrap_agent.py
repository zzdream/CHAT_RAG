"""
Phase 3 LangChain Agent 引导 —— 注册路由，不修改 Phase 1 / Phase 2 业务模块。
"""

from fastapi import FastAPI

from app.api.routes import chat_agent


def setup_agent(app: FastAPI) -> None:
    """挂载 LangChain Agent 路由。"""
    app.include_router(chat_agent.router)
