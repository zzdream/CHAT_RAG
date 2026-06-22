"""LangChain 工具注册表测试"""

from langchain_core.tools import BaseTool

from app.services.agent.tool_registry import (
    calculator,
    create_rag_search_tool,
    get_agent_tools,
    text_formatter,
)
from app.services.tools.registry import execute_tool


def test_get_agent_tools_without_rag() -> None:
    tools = get_agent_tools()
    assert len(tools) == 2
    assert all(isinstance(tool, BaseTool) for tool in tools)
    names = {tool.name for tool in tools}
    assert names == {"calculator", "text_formatter"}


def test_get_agent_tools_with_rag() -> None:
    tools = get_agent_tools("kb-123", top_k=3)
    assert len(tools) == 3
    names = {tool.name for tool in tools}
    assert names == {"calculator", "text_formatter", "rag_search"}


def test_create_rag_search_tool_name() -> None:
    tool = create_rag_search_tool("kb-1", 5)
    assert tool.name == "rag_search"


def test_langchain_calculator_tool() -> None:
    assert calculator.invoke({"expression": "2 + 3"}) == "5"


def test_langchain_text_formatter_tool() -> None:
    assert text_formatter.invoke({"text": "hello", "format_type": "uppercase"}) == "HELLO"


def test_langchain_tools_match_native_registry() -> None:
    assert calculator.invoke({"expression": "10 * 5"}) == execute_tool(
        "calculator", '{"expression": "10 * 5"}'
    )
    assert text_formatter.invoke({"text": " hi ", "format_type": "trim"}) == execute_tool(
        "text_formatter", '{"text": " hi ", "format_type": "trim"}'
    )
