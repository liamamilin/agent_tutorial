"""
第5章：结构化输出 —— Function Calling 基础
=============================================
演示 OpenAI 原生 Function Calling 的基本用法。

Function Calling 是 OpenAI 提供的一种机制，允许模型"决定"调用一个预定义
的函数并生成结构化的参数。它的核心流程是：
1. 你告诉模型有哪些工具（函数）可用
2. 模型根据用户输入决定是否调用工具，以及传什么参数
3. 你执行实际的函数并把结果返回给模型
4. 模型结合函数返回结果生成最终回复

这是实现"结构化输出"最可靠的方式 —— 模型输出的参数是严格符合 schema 的 JSON。
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# 客户端配置
# ---------------------------------------------------------------------------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================================
# 第1部分：定义一个简单的工具（函数）
# ============================================================================

def get_weather(city: str) -> str:
    """
    模拟获取天气的函数（实际应用中会调用真实的天气 API）

    这是模型会"请求调用"的函数。模型的 tool_calls 会告诉我们需要调用
    这个函数以及传递什么参数，我们负责真正执行它。
    """
    # 模拟天气数据
    weather_db = {
        "北京": "晴天，25°C，湿度 40%，北风 3 级",
        "上海": "多云，28°C，湿度 65%，东南风 2 级",
        "东京": "小雨，22°C，湿度 80%，西南风 4 级",
        "纽约": "阴天，18°C，湿度 55%，西风 5 级",
        "伦敦": "阵雨，15°C，湿度 75%，南风 3 级",
    }

    return weather_db.get(
        city,
        f"{city}的天气：晴转多云，23°C，湿度 50%（模拟数据）"
    )


# ---------------------------------------------------------------------------
# 工具 Schema 定义 —— 告诉模型这个函数是干什么的
# ---------------------------------------------------------------------------
# Function Calling 的核心是 tool schema，用 JSON Schema 描述函数签名。
# 模型通过这个 schema 理解函数的用途和参数要求。
GET_WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",  # 函数名 —— 模型返回的 tool_calls 中会引用这个名字
        "description": "查询指定城市的实时天气信息。当用户询问天气相关问题时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如'北京'、'上海'、'东京'等",
                }
            },
            "required": ["city"],  # city 是必填参数
        },
    },
}


# ============================================================================
# 第2部分：场景一 —— 模型决定调用工具
# ============================================================================

def demo_model_calls_tool():
    """
    场景一：用户询问天气，模型判断需要调用 get_weather 工具。

    这是 Function Calling 的标准流程：
    1. 发送用户消息 + tools 定义
    2. 检查响应中的 tool_calls
    3. 如果有 tool_calls，说明模型想要调用某个函数
    4. 解析 tool_calls，提取函数名和参数
    5. 执行函数
    6. 将结果以 tool role 消息返回给模型
    """
    print("\n" + "=" * 60)
    print("【场景一】模型决定调用工具 —— 用户询问天气")
    print("=" * 60)

    messages = [
        {"role": "user", "content": "今天北京的天气怎么样？"}
    ]

    print(f"用户: {messages[0]['content']}")

    # 第一次请求：发送用户消息和工具定义
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[GET_WEATHER_TOOL],
        temperature=0.3,
    )

    # 检查模型是否决定调用工具
    message = response.choices[0].message

    print(f"\n模型响应详情:")
    print(f"  content: {message.content}")  # 当有 tool_calls 时，content 通常为 None
    print(f"  role: {message.role}")
    print(f"  tool_calls 存在: {message.tool_calls is not None}")

    if message.tool_calls:
        print(f"\n  模型决定调用 {len(message.tool_calls)} 个工具:")

        for tc in message.tool_calls:
            print(f"\n  --- Tool Call ---")
            print(f"    id: {tc.id}")
            print(f"    function.name: {tc.function.name}")
            print(f"    function.arguments (原始 JSON 字符串): {tc.function.arguments}")

            # 解析参数 —— arguments 是 JSON 字符串，需要 parse
            args = json.loads(tc.function.arguments)
            print(f"    function.arguments (解析后): {args}")

            # 执行对应的函数
            if tc.function.name == "get_weather":
                city = args["city"]
                result = get_weather(city)
                print(f"\n  执行 get_weather('{city}')")
                print(f"  返回结果: {result}")

                # 将助手消息（含 tool_calls）和工具结果加入对话
                messages.append(message)  # 助手的 tool_calls 消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        # 第二次请求：将工具执行结果返回给模型，让模型生成最终回答
        print(f"\n  发送工具结果给模型，获取最终回复...")
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        final_message = final_response.choices[0].message
        print(f"\n  模型最终回复: {final_message.content}")
    else:
        print(f"  模型没有调用工具，直接回复: {message.content}")


# ============================================================================
# 第3部分：场景二 —— 模型不调用工具（直接回复）
# ============================================================================

def demo_model_does_not_call_tool():
    """
    场景二：用户问一个与工具无关的问题，模型直接以文字回复。

    这说明 Function Calling 是智能的：模型只在必要时才调用工具。
    并非每次对话都必须使用工具。
    """
    print("\n" + "=" * 60)
    print("【场景二】模型不调用工具 —— 用户问非工具问题")
    print("=" * 60)

    messages = [
        {"role": "user", "content": "什么是函数式编程？请用简单的话解释一下。"}
    ]

    print(f"用户: {messages[0]['content']}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[GET_WEATHER_TOOL],  # 提供了天气工具，但模型判断不需要
        temperature=0.3,
    )

    message = response.choices[0].message

    print(f"\n模型响应详情:")
    print(f"  content 存在: {message.content is not None}")
    print(f"  tool_calls 存在: {message.tool_calls is not None}")

    if message.content:
        # 模型认为不需要工具，直接回复
        print(f"\n  模型直接回复（没有调用工具）:")
        print(f"  {message.content}")
    elif message.tool_calls:
        print(f"  模型意外地决定调用工具!")
    else:
        print(f"  空响应")


# ============================================================================
# 第4部分：深入理解 tool_calls 响应结构
# ============================================================================

def demo_tool_calls_structure():
    """
    场景三：深入分析 tool_calls 的完整响应结构。

    理解响应的每一个字段对于后续的 tool call 解析至关重要。
    """
    print("\n" + "=" * 60)
    print("【场景三】深入理解 tool_calls 响应结构")
    print("=" * 60)

    messages = [
        {"role": "user", "content": "上海和东京的天气分别是怎样的？"}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[GET_WEATHER_TOOL],
        temperature=0.3,
    )

    message = response.choices[0].message

    # 打印完整的 message 对象
    print(f"message.role: {message.role}")
    print(f"message.content: {repr(message.content)}")
    print(f"message.tool_calls: {message.tool_calls}")

    if message.tool_calls:
        for i, tc in enumerate(message.tool_calls):
            print(f"\n--- Tool Call #{i+1} ---")
            print(f"  tc.id: {tc.id}")
            print(f"  tc.type: {tc.type}")  # 通常是 "function"
            print(f"  tc.function.name: {tc.function.name}")
            print(f"  tc.function.arguments: {tc.function.arguments}")

            # 演示参数解析
            args = json.loads(tc.function.arguments)
            print(f"  解析后的参数: {json.dumps(args, ensure_ascii=False)}")

    # 打印原始 HTTP 响应的关键部分
    print(f"\n--- 响应元数据 ---")
    print(f"  model: {response.model}")
    print(f"  finish_reason: {response.choices[0].finish_reason}")
    # finish_reason 为 "tool_calls" 表示模型想要调用工具
    print(f"  usage: {response.usage}")


# ============================================================================
# 第5部分：完整的 Function Calling 循环
# ============================================================================

def demo_full_loop():
    """
    场景四：展示完整的 Function Calling 循环。

    这是 Agent 开发中最核心的模式：
    用户输入 -> 模型判断 -> 调用工具 -> 获取结果 -> 模型总结 -> 最终回复
    """
    print("\n" + "=" * 60)
    print("【场景四】完整的 Function Calling 循环")
    print("=" * 60)

    user_input = "我想知道北京的天气，以及明天是否适合出游。"

    print(f"用户: {user_input}")

    # 初始消息
    messages = [{"role": "user", "content": user_input}]

    # Step 1: 发送给模型，附带工具定义
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[GET_WEATHER_TOOL],
        temperature=0.3,
    )
    message = response.choices[0].message

    # Step 2: 检查是否有 tool_calls
    if message.tool_calls:
        print(f"\n📞 模型请求调用工具...")

        # Step 3: 将助手的 tool_calls 消息加入历史
        messages.append(message)

        # Step 4: 执行每一个 tool call
        for tc in message.tool_calls:
            func_name = tc.function.name
            args = json.loads(tc.function.arguments)

            print(f"   执行: {func_name}({args})")

            # 根据函数名分发调用
            if func_name == "get_weather":
                result = get_weather(**args)
            else:
                result = f"未知函数: {func_name}"

            print(f"   结果: {result}")

            # Step 5: 将工具结果加入历史
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        # Step 6: 再次请求模型，让它基于工具结果生成回复
        print(f"\n🤖 模型基于工具结果生成回复...")
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        final_message = final_response.choices[0].message

        # Step 7: 输出最终回复
        print(f"\n模型最终回复:")
        print(f"  {final_message.content}")

        # 如果模型还想调用更多工具（多步推理），会再次返回 tool_calls
        if final_message.tool_calls:
            print(f"\n  ⚠️ 模型希望继续调用工具（多步推理）")
    else:
        print(f"\n模型直接回复: {message.content}")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— Function Calling 基础")
    print(f"使用模型: {MODEL}")

    # 逐一运行演示
    demo_model_calls_tool()
    demo_model_does_not_call_tool()
    demo_tool_calls_structure()
    demo_full_loop()

    print("\n" + "=" * 60)
    print("总结：Function Calling 是获取结构化输出的最佳方式。")
    print("模型通过 tool_calls 响应返回精确的 JSON 参数，")
    print("开发者执行实际函数后，模型再基于结果生成自然语言回复。")
    print("这是构建 LLM Agent 的核心技术。")
