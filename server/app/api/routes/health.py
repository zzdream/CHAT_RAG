"""
健康检查路由 —— 部署运维用，类似前端的 ping 接口

用途：
  - 检查服务是否存活：curl http://localhost:8000/health
  - K8s / Docker 健康探针
  - 前端一般不需要调用
"""

from fastapi import APIRouter
# 子路由模块
router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """
    GET /health → { "status": "ok" }

    @router.get("/health") 是装饰器语法，等价于：
      router.get('/health', health_check)  // 注册路由

    -> dict[str, str] 是返回类型标注，表示返回 {"字符串键": "字符串值"} 的字典
    """
    return {"status": "ok"}
