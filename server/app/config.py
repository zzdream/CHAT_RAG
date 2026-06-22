"""
配置模块 —— 类似前端的 .env + config.ts

读取 server/.env 文件中的环境变量，供其他模块使用。
Python 里 os.getenv('KEY', '默认值') ≈ 前端的 import.meta.env.VITE_XXX
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

# 加载 .env 文件到环境变量（启动时执行一次）
load_dotenv()


class Settings:
    """
    配置类 —— 类似 TypeScript 的 interface + 默认值

    类属性后面的 `: str` 是类型标注（类似 TS），不会运行时强制校验，
    主要给 IDE 提示和阅读代码用。
    """

    # 服务基础配置
    app_name: str = "OmniChat API"
    app_version: str = "0.1.0"
    host: str = os.getenv("APP_HOST", "0.0.0.0")       # 监听地址，0.0.0.0 = 所有网卡
    port: int = int(os.getenv("APP_PORT", "8000"))       # 监听端口
    debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"  # 是否开发模式

    # DeepSeek API 配置（密钥只放 .env，不要提交 Git）
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    # CORS 白名单 —— 允许哪些前端地址跨域访问
    # 下面这种 [... for ... in ...] 写法叫「列表推导式」，类似 JS 的 .map().filter()
    # 如 const cors_origins = (process.env.CORS_ORIGINS ?? "http://localhost:5173,http://127.0.0.1:5173").split(",").map(origin => origin.trim()).filter(Boolean);
    # origin.strip()：去掉首尾空格
    # if origin.strip()：过滤空字符串（比如 "a,,b" 中间的空项）
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

    # 开发环境用正则放宽限制（localhost / 局域网 IP 都能访问）
    cors_origin_regex: str | None = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?",
    )

    # 请求限流（slowapi 格式，如 10/minute、100/hour）
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_chat: str = os.getenv("RATE_LIMIT_CHAT", "10/minute")

    # 敏感词（逗号分隔，匹配时忽略大小写） frozenset（不可变集合）最终 frozenset({"违禁", "暴力", "赌博", "色情", "毒品"})
    sensitive_words: frozenset[str] = frozenset(
        word.strip().lower()
        for word in os.getenv(
            "SENSITIVE_WORDS",
            "违禁,暴力,赌博,色情,毒品",
        ).split(",")
        if word.strip()
    )

    # 聊天入参长度上限
    chat_message_max_length: int = int(os.getenv("CHAT_MESSAGE_MAX_LENGTH", "4000"))
    chat_system_max_length: int = int(os.getenv("CHAT_SYSTEM_MAX_LENGTH", "2000"))

    # 多轮对话：history 最多保留条数（不含当前 message），超出时服务端截断最早的消息
    chat_history_max_messages: int = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "20"))

    # LLM 采样温度默认值；前端可在 0～2 之间调整
    chat_default_temperature: float = float(os.getenv("CHAT_DEFAULT_TEMPERATURE", "0.7"))

    # 允许前端选择的模型白名单（逗号分隔）
    chat_allowed_models: frozenset[str] = frozenset(
        model.strip()
        for model in os.getenv(
            "CHAT_ALLOWED_MODELS",
            "deepseek-v4-flash,deepseek-v4-pro",
        ).split(",")
        if model.strip()
    )


@lru_cache  # 缓存装饰器：只创建一次 Settings 实例（类似单例模式）
def get_settings() -> Settings:  # 返回值类型为Settings
    """获取配置单例，其他文件通过 from app.config import get_settings 调用"""
    return Settings()  # 返回Settings实例
