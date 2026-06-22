#!/usr/bin/env python3
"""
Step 0：验证 DeepSeek Function Calling 是否可用。

用法（在 server 目录下）：
  python scripts/verify_function_calling.py

需要 server/.env 中配置有效的 DEEPSEEK_API_KEY。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SERVER_ROOT = Path(__file__).resolve().parent.parent
if str(_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVER_ROOT))

from dotenv import load_dotenv

load_dotenv(_SERVER_ROOT / ".env")

from app.config import get_settings
from app.services.llm import get_openai_client
from app.services.tools.registry import TOOL_DEFINITIONS, execute_tool


def main() -> int:
    settings = get_settings()
    if not settings.deepseek_api_key:
        print("❌ DEEPSEEK_API_KEY 未配置，请在 server/.env 中设置")
        return 1

    print(f"模型: {settings.deepseek_model}")
    print(f"Base URL: {settings.deepseek_base_url}")
    print("发送测试请求：计算 123 * 456 ...")

    client = get_openai_client(settings)
    messages = [
        {
            "role": "user",
            "content": "请用 calculator 工具计算 123 乘以 456 等于多少，只调用工具即可。",
        }
    ]

    try:
        response = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0,
        )
    except Exception as exc:  # noqa: BLE001 — 验证脚本需要捕获所有 API 错误
        print(f"❌ API 调用失败: {exc}")
        return 1

    message = response.choices[0].message
    if not message.tool_calls:
        print("⚠️  模型未返回 tool_calls，Function Calling 可能未生效")
        print(f"   模型回复: {message.content}")
        return 1

    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = tool_call.function.arguments
    print(f"✅ 模型返回 tool_call: {tool_name}({tool_args})")

    try:
        result = execute_tool(tool_name, tool_args)
    except ValueError as exc:
        print(f"❌ 工具执行失败: {exc}")
        return 1

    print(f"✅ 工具执行结果: {result}")

    messages.append(
        {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_args,
                    },
                }
            ],
        }
    )
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        }
    )

    final = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
        temperature=0,
    )
    final_content = final.choices[0].message.content or ""
    print(f"✅ 最终回答: {final_content.strip()}")

    expected = "56088"
    if expected in result or expected in final_content:
        print("\n🎉 Step 0 验证通过：DeepSeek Function Calling 可用")
        return 0

    print(f"\n⚠️  结果中未找到期望值 {expected}，请人工确认")
    print(json.dumps({"tool_result": result, "final": final_content}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
