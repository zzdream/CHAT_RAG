"""
LangChain 工具注册 —— 用 @tool 包装 Step 1 的纯 Python 工具函数。
"""

from langchain_core.tools import BaseTool, StructuredTool, tool

from app.services.tools.calculator import calculate
from app.services.tools.rag_search import resolve_rag_top_k, search_knowledge_base
from app.services.tools.text_formatter import format_text


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。支持加减乘除、整除、取模、幂运算与括号。示例：'123 * 456'、'(1 + 2) * 3'。"""
    return calculate(expression)


@tool
def text_formatter(text: str, format_type: str) -> str:
    """格式化文本。format_type 可选：uppercase、lowercase、title、trim、reverse、json_pretty。"""
    return format_text(text, format_type)


def create_rag_search_tool(knowledge_base_id: str, top_k: int) -> StructuredTool:
    """为指定知识库创建绑定了 kb_id 的 rag_search 工具。"""

    def _rag_search(query: str) -> str:
        return search_knowledge_base(knowledge_base_id, query, top_k)

    return StructuredTool.from_function(
        func=_rag_search,
        name="rag_search",
        description=(
            "在当前知识库中检索与问题相关的文档片段。"
            "输入应为简洁的检索关键词或问句；返回检索到的资料摘要。"
        ),
    )


def get_agent_tools(
    knowledge_base_id: str | None = None,
    top_k: int | None = None,
) -> list[BaseTool]:
    """返回 LangChain Agent 绑定的工具列表；传入 knowledge_base_id 时追加 rag_search。"""
    tools: list[BaseTool] = [calculator, text_formatter]
    if knowledge_base_id:
        effective_top_k = resolve_rag_top_k(top_k)
        tools.append(create_rag_search_tool(knowledge_base_id, effective_top_k))
    return tools
