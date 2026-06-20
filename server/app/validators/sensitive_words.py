"""
敏感词校验 —— 供 Pydantic 自定义校验器调用

默认词表可通过 .env 的 SENSITIVE_WORDS 覆盖（逗号分隔）。
匹配策略：忽略大小写的子串包含（学习项目够用；生产可换 AC 自动机）。
"""


def find_sensitive_words(text: str, words: frozenset[str]) -> list[str]:
    """返回文本中命中的敏感词列表（去重、保持词表顺序）。"""
    if not text or not words:
        return []

    lowered = text.lower()
    return [word for word in words if word in lowered] 
    # 上面这个写法等价于下面的写法：
    # found = []
    #     for word in words:
    #         if word in lowered:
    #             found.append(word)
    #     return found


def format_sensitive_word_error(found: list[str]) -> str:
    """生成给前端的校验错误文案。"""
    # "、".join(...) 类似 JS：["赌博", "暴力", "色情"].join("、") =》 "赌博、暴力、色情"
    # found 是敏感词列表，如 ["赌博", "暴力", "色情", "毒品"]
    # found[:3]   # → ["赌博", "暴力", "色情"]
    # found[3:]   # → ["毒品"]  （剩下的）
    preview = "、".join(found[:3])
    if len(found) > 3:
        preview += " 等"
    return f"内容包含敏感词（{preview}），请修改后重试"
