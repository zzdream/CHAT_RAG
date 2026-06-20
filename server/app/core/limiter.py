"""
请求限流 —— 基于 slowapi，按客户端 IP 限制调用频率

类似前端的防抖/节流，但在服务端按 IP 统计：
  @limiter.limit("10/minute")  →  同一 IP 每分钟最多 10 次

health 等探活接口不加限流，避免影响监控。
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# key_func=get_remote_address：用请求来源 IP 作为限流键
limiter = Limiter(key_func=get_remote_address)
