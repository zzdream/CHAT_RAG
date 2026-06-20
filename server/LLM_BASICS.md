# LLM 基础概念

本文档整理大语言模型（LLM）的常见基础概念，并结合本项目的代码说明对应关系。

---

## 1. Token（词元）

**Token 不是「一个字」或「一个单词」，而是模型处理文本的最小单位。**

模型不会直接读「你好世界」，而是先把文本切成 token，再计算、再生成。

| 文本 | 大致 token 数（示意） |
|------|----------------------|
| `Hello` | 往往 1 个 |
| `你好` | 中文常 1～2 个 |
| 一段 1000 字中文 | 大约几百～上千 token |

### 和计费、限长的关系

- API 通常按 **输入 token + 输出 token** 计费
- 模型有 **最大上下文长度**（如 8K、32K、128K），超出就装不下

### 在本项目中的体现

流式聊天接口中，API 一块一块推送文本，每一块通常就是一个 token（或几个字符组成的片段）：

```python
# app/api/routes/chat.py
for token in chat_completion_stream(messages):
    yield format_sse({"content": token})
```

前端看到的就是逐字/逐词蹦出来的效果。

---

## 2. 上下文（Context）

**上下文 = 模型这次请求能「看到」的全部内容。**

包括：

- 系统提示（system）
- 历史对话（user / assistant 来回）
- 当前用户输入

可以把它想成模型的**短期记忆窗口**：窗口里有的它记得，窗口外的它不知道。

```
┌─────────────────── 上下文窗口（例如 32K tokens）───────────────────┐
│ system: 你是一位 Python 助教                                      │
│ user: 什么是装饰器？                                              │
│ assistant: 装饰器是...                                            │
│ user: 再举个例子                                                  │  ← 当前问题
└───────────────────────────────────────────────────────────────────┘
                              ↓
                         模型基于这些生成回答
```

### 注意事项

- 对话越长，占用的 token 越多
- 接近上限时，要么截断旧消息，要么报错
- 本项目目前是**单轮**（只有 system + 当前 message），没有传历史

```python
# app/services/llm.py — build_messages()
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})

messages.append({"role": "user", "content": user_message})
```

要做多轮聊天，需要把之前的 `user` / `assistant` 也 append 进 `messages`。

---

## 3. 温度（Temperature）

**Temperature 控制回答的「随机性 / 创造性」。**

取值一般是 `0 ~ 2`（常见默认 `1` 或 `0.7`）：

| 温度 | 效果 | 适合场景 |
|------|------|----------|
| **低（0～0.3）** | 更稳定、可重复、偏保守 | 代码生成、事实问答、数据提取 |
| **中（0.5～0.8）** | 平衡 | 日常聊天、写作 |
| **高（1+）** | 更随机、更有创意，也可能胡说 | 头脑风暴、创意写作 |

### 类比理解

- 温度低 → 每次回答差不多，像「标准答案」
- 温度高 → 同样问题，回答可能差很多，像「发散思维」

### 在本项目中的状态

目前 `chat.completions.create` **未传 `temperature`**，会使用 API 默认值。若要添加：

```python
# app/services/llm.py
client.chat.completions.create(
    model=target_model,
    messages=messages,
    stream=True,
    temperature=0.7,  # 可选
)
```

也可在 `.env` 中增加配置项，通过 `Settings` 读取。

---

## 4. 角色设定（Role / System Prompt）

大模型 API 里，对话通常用 **`role` 区分谁说的话**：

| role | 含义 | 作用 |
|------|------|------|
| **system** | 系统指令 | 设定 AI 的身份、风格、规则（用户一般看不到） |
| **user** | 用户 | 用户的问题或指令 |
| **assistant** | 助手 | 模型之前的回复（多轮对话时用） |

**角色设定 = 写在 `system` 里的 Prompt**，用来告诉模型「你是谁、该怎么答」。

### 在本项目中的体现

前端 POST `/chat/stream` 时可传 `system` 字段：

```json
{
  "message": "解释一下 Python 装饰器",
  "system": "你是一位耐心的编程老师，用简单例子讲解，每次回答不超过 200 字"
}
```

后端 `build_messages` 会组装为：

```python
[
    {"role": "system", "content": "你是一位耐心的编程老师..."},
    {"role": "user", "content": "解释一下 Python 装饰器"}
]
```

### 好的 system 设定通常包括

- **身份**：你是翻译官 / 代码审查员 / 客服
- **风格**：简洁 / 详细 / 用中文 / 用 bullet 列表
- **边界**：不知道就说不知道；不要编造数据
- **格式**：先结论后解释；输出 JSON 等

`system` 字段长度上限由 `.env` 的 `CHAT_SYSTEM_MAX_LENGTH` 控制（默认 2000 字符）。

---

## 5. Prompt 基础写法

**Prompt = 你给模型的指令 + 问题**，分两层：

### System Prompt（系统层，定规则）

```
你是一位 Python 助教。
规则：
1. 用中文回答
2. 先给结论，再给代码示例
3. 代码必须可运行
4. 不确定时明确说「我不确定」
```

### User Prompt（用户层，具体问题）

```
@classmethod 和 @staticmethod 有什么区别？请各举一个例子。
```

### 常用写法技巧

#### ① 说清楚任务

```
❌ 帮我看看这个
✅ 请审查下面这段 Python 代码，找出 bug 并说明原因
```

#### ② 给上下文和约束

```
下面是一段 FastAPI 路由代码。
请只返回修改后的代码，不要解释。
[粘贴代码]
```

#### ③ 指定输出格式

```
请用 JSON 返回，字段：summary（字符串）、steps（字符串数组）
```

#### ④ 分步思考（复杂问题时）

```
请先列出思路，再给出最终答案。
```

#### ⑤ Few-shot（给例子）

```
把用户输入分类为：咨询 / 投诉 / 其他

示例：
输入：怎么退款 → 咨询
输入：你们服务太差了 → 投诉

输入：发货太慢了 →
```

---

## 6. 一次完整请求的流程

```
用户在前端输入
  ↓
POST { message, system }
  ↓
Pydantic 校验（长度、敏感词等）  ← app/schemas/chat.py
  ↓
build_messages 组装上下文          ← app/services/llm.py
  ↓
DeepSeek API（消耗 input tokens）
  ↓
流式返回 output tokens
  ↓
前端逐字显示（SSE）
```

---

## 7. 概念与本项目代码对照

| 概念 | 说明 | 在本项目中的位置 |
|------|------|------------------|
| Token | 模型读写的最小单位 | `chat_completion_stream` 流式 yield 的每个片段 |
| 上下文 | 模型本次能看到的全部内容 | `build_messages` 返回的 `messages` 数组 |
| 温度 | 回答随机性 | 暂未配置，使用 API 默认 |
| 角色设定 | 用 system 定义 AI 行为 | 前端传的 `system` 字段 |
| Prompt | 指令 + 问题 | `system` + `message` 合起来 |

---

## 8. 相关文件

| 文件 | 职责 |
|------|------|
| `app/schemas/chat.py` | 请求体模型，校验 message / system |
| `app/services/llm.py` | 组装 messages、调用 DeepSeek API |
| `app/api/routes/chat.py` | HTTP 接口，SSE 流式推送 |
| `app/config.py` | 模型名、长度限制等配置 |
| `.env` | `DEEPSEEK_MODEL`、`CHAT_MESSAGE_MAX_LENGTH` 等 |

---

## 9. 一句话记忆

- **Token**：模型读写的最小单位，关系计费和长度限制
- **上下文**：模型这次能看到的全部对话内容
- **温度**：回答有多「稳」还是多「飘」
- **角色设定**：用 `system` 告诉模型「你是谁、怎么答」
- **Prompt**：把任务、规则、格式写清楚，模型才答得准
