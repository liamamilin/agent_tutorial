"""
第5章：结构化输出 —— 解析和执行 Tool Calls
=============================================
展示了如何从模型响应中解析 tool_calls、执行对应的函数、
以及处理并行工具调用（模型一次性请求多个工具）。

核心要点：
1. tool_calls 是一个列表，可能包含多个并行调用
2. 每个 tool_call 有 id、function.name、function.arguments
3. arguments 是 JSON 字符串，需要用 json.loads() 解析
4. 执行结果以 tool role 消息返回，tool_call_id 必须匹配
5. 模型可能在一轮对话中多次请求工具调用（循环）
"""

import os
import json
import time
from typing import Any, Callable
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================================
# 第1部分：模拟的工具函数
# ============================================================================

def get_weather(city: str, unit: str = "celsius") -> str:
    """获取天气信息（模拟）"""
    weather_data = {
        "北京": {"celsius": "25°C，晴", "fahrenheit": "77°F，晴"},
        "上海": {"celsius": "28°C，多云", "fahrenheit": "82°F，多云"},
        "东京": {"celsius": "22°C，小雨", "fahrenheit": "72°F，小雨"},
    }
    city_data = weather_data.get(city, {})
    return city_data.get(unit, f"{city}：数据不可用")


def search_web(query: str) -> str:
    """搜索互联网（模拟）"""
    # 模拟搜索延迟
    time.sleep(0.3)
    return f"关于'{query}'的搜索结果：[模拟结果1] [模拟结果2] [模拟结果3]"


def calculate(expression: str) -> str:
    """计算数学表达式（模拟）"""
    try:
        # 注意：这里简化处理，实际中应该用更安全的方式
        # 这里仅返回模拟结果
        return f"{expression} = 42.0 (模拟计算结果)"
    except Exception:
        return "计算错误"


# ============================================================================
# 第2部分：工具注册表 —— 集中管理工具定义和执行
# ============================================================================

class ToolRegistry:
    """
    工具注册表：将工具的定义（Schema）和执行函数（Handler）集中管理。

    这是 Agent 开发中的常见模式：
    - tools_schema: 提供给 OpenAI API 的工具定义列表
    - 通过工具名来查找对应的执行函数
    - 方便添加新工具和统一管理
    """

    def __init__(self):
        # 存储: tool_name -> {"schema": ..., "handler": ...}
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, parameters: dict, handler: Callable):
        """
        注册一个工具。

        参数:
            name: 工具名称（唯一标识）
            description: 工具描述（帮助模型理解何时使用）
            parameters: JSON Schema 参数定义
            handler: 实际执行的函数，接收关键字参数
        """
        self._tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
            "handler": handler,
        }

    def get_schemas(self) -> list[dict]:
        """返回所有工具的 schema 列表，可直接传给 OpenAI API"""
        return [t["schema"] for t in self._tools.values()]

    def execute(self, name: str, arguments: dict) -> str:
        """根据工具名和参数执行对应的工具函数"""
        if name not in self._tools:
            return f"错误：未知工具 '{name}'。可用工具: {list(self._tools.keys())}"

        handler = self._tools[name]["handler"]
        try:
            result = handler(**arguments)
            return str(result)
        except Exception as e:
            return f"工具执行错误 ({name}): {e}"

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名"""
        return list(self._tools.keys())


# 初始化注册表并注册工具
registry = ToolRegistry()

registry.register(
    name="get_weather",
    description="查询指定城市的实时天气信息。",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"},
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "温度单位，默认 celsius",
            },
        },
        "required": ["city"],
    },
    handler=get_weather,
)

registry.register(
    name="search_web",
    description="在互联网上搜索信息，返回相关结果摘要。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
        },
        "required": ["query"],
    },
    handler=search_web,
)

registry.register(
    name="calculate",
    description="计算数学表达式的结果。",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 '2+3*4'"},
        },
        "required": ["expression"],
    },
    handler=calculate,
)


# ============================================================================
# 第3部分：Tool Call 解析器
# ============================================================================

def parse_and_execute_tool_calls(message, registry: ToolRegistry) -> list[dict]:
    """
    解析模型返回的 tool_calls 并逐个执行。

    参数:
        message: OpenAI ChatCompletionMessage 对象
        registry: ToolRegistry 实例

    返回:
        列表，每个元素为 {"tool_call_id": ..., "role": "tool", "content": ...}
        可以直接追加到 messages 列表中
    """
    results = []

    if not message.tool_calls:
        return results

    for tc in message.tool_calls:
        # Step 1: 提取基本信息
        tool_call_id = tc.id
        function_name = tc.function.name
        arguments_str = tc.function.arguments

        print(f"\n  🔧 解析 Tool Call:")
        print(f"     id: {tool_call_id}")
        print(f"     function: {function_name}")
        print(f"     arguments (raw): {arguments_str}")

        # Step 2: 将 arguments JSON 字符串解析为 Python dict
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            print(f"     ⚠️ arguments JSON 解析失败: {e}")
            results.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": f"参数解析错误: {e}。原始参数: {arguments_str}",
            })
            continue

        print(f"     arguments (parsed): {json.dumps(arguments, ensure_ascii=False)}")

        # Step 3: 执行工具
        print(f"     ⚡ 执行 {function_name}...")
        result = registry.execute(function_name, arguments)
        print(f"     ✅ 结果: {result[:100]}...")

        # Step 4: 构造 tool 响应消息
        results.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        })

    return results


# ============================================================================
# 第4部分：场景演示
# ============================================================================

def demo_single_tool_call():
    """
    演示一：单个工具调用 —— 最基本的情况。

    模型只请求调用一个工具。
    """
    print("\n" + "=" * 60)
    print("【演示一】单个工具调用")
    print("=" * 60)

    messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

    print(f"用户: {messages[0]['content']}")

    # 第一次请求
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=registry.get_schemas(),
        temperature=0.3,
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        # 将助手消息（含 tool_calls）加入对话
        messages.append(msg)

        # 解析并执行
        tool_results = parse_and_execute_tool_calls(msg, registry)

        # 将工具结果加入对话
        messages.extend(tool_results)

        # 第二次请求：获取最终回复
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        print(f"\n  模型最终回复: {final_response.choices[0].message.content}")


def demo_parallel_tool_calls():
    """
    演示二：并行工具调用 —— 模型一次性请求多个工具。

    这是 Function Calling 的强大功能：模型可以在一次响应中
    请求多个相互独立的工具调用，显著减少延迟。

    例如用户问"北京和上海的天气分别怎么样"，
    模型会一次请求两个 get_weather 调用。
    """
    print("\n" + "=" * 60)
    print("【演示二】并行工具调用")
    print("=" * 60)

    messages = [
        {"role": "user", "content": "帮我同时查一下北京、上海、东京的天气"}
    ]

    print(f"用户: {messages[0]['content']}")

    # 第一次请求
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=registry.get_schemas(),
        temperature=0.3,
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        print(f"\n模型一次请求了 {len(msg.tool_calls)} 个工具调用:")

        # 将助手消息加入对话
        messages.append(msg)

        # 解析并执行所有工具调用
        tool_results = parse_and_execute_tool_calls(msg, registry)

        # 将所有工具结果加入对话
        messages.extend(tool_results)

        # 第二次请求：模型汇总所有结果
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        print(f"\n  模型最终汇总:")
        print(f"  {final_response.choices[0].message.content}")
    else:
        print("  模型没有使用工具")


def demo_multi_tool_types():
    """
    演示三：一次调用不同类型的工具。

    用户可能同时需要不同工具，模型能够智能判断。
    """
    print("\n" + "=" * 60)
    print("【演示三】混合工具调用")
    print("=" * 60)

    messages = [
        {"role": "user", "content": "北京天气如何？另外帮我算一下 123 * 456 等于多少？"}
    ]

    print(f"用户: {messages[0]['content']}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=registry.get_schemas(),
        temperature=0.3,
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        print(f"\n模型请求了 {len(msg.tool_calls)} 个不同类型的工具:")

        messages.append(msg)
        tool_results = parse_and_execute_tool_calls(msg, registry)
        messages.extend(tool_results)

        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        print(f"\n  模型最终回复: {final_response.choices[0].message.content}")


def demo_multi_turn_tool_loop():
    """
    演示四：多轮工具调用循环。

    有些情况下，模型需要先调用一个工具，然后根据结果决定是否
    调用下一个工具。这需要多轮 Tool Call 循环。

    流程:
    1. 用户输入
    2. 模型请求 tool call A
    3. 执行 A，返回结果
    4. 模型看到 A 的结果后，请求 tool call B
    5. 执行 B，返回结果
    6. 模型给出最终回答

    这与"并行调用"不同 —— 并行调用中多个工具互不依赖，
    而多轮循环中后一个工具依赖前一个工具的结果。
    """
    print("\n" + "=" * 60)
    print("【演示四】多轮工具调用循环")
    print("=" * 60)

    messages = [
        {
            "role": "user",
            "content": (
                "先查一下北京的天气，如果天气好（晴天）就帮我搜索'北京旅游攻略'，"
                "如果天气不好就搜索'北京室内景点'"
            )
        }
    ]

    print(f"用户: {messages[0]['content']}")

    MAX_TURNS = 5  # 防止无限循环的安全上限

    for turn in range(MAX_TURNS):
        print(f"\n--- 第 {turn + 1} 轮 ---")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=registry.get_schemas(),
            temperature=0.3,
        )

        msg = response.choices[0].message

        # 如果模型不再请求工具，说明它可以给出最终回复了
        if not msg.tool_calls:
            print(f"  模型最终回复: {msg.content}")
            break

        # 有工具调用，继续循环
        print(f"  模型请求了 {len(msg.tool_calls)} 个工具调用")

        messages.append(msg)
        tool_results = parse_and_execute_tool_calls(msg, registry)
        messages.extend(tool_results)

    else:
        print(f"  ⚠️ 达到最大轮次 {MAX_TURNS}，强制停止。")


def demo_complete_message_history():
    """
    演示五：查看完整的多轮对话消息历史。

    这对于调试和理解 Agent 的"思考过程"非常重要。
    """
    print("\n" + "=" * 60)
    print("【演示五】查看完整消息历史")
    print("=" * 60)

    messages = [{"role": "user", "content": "上海天气如何？"}]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=registry.get_schemas(),
        temperature=0.3,
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        tool_results = parse_and_execute_tool_calls(msg, registry)
        messages.extend(tool_results)

        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        messages.append(final_response.choices[0].message)

    # 打印完整历史
    print("完整对话历史:")
    for i, m in enumerate(messages):
        role = m.get("role", "?")
        if hasattr(m, "role"):
            role = m.role

        content = ""
        if hasattr(m, "content"):
            content = m.content or ""
        elif isinstance(m, dict):
            content = m.get("content", "")

        tool_calls_info = ""
        if hasattr(m, "tool_calls") and m.tool_calls:
            tc_names = [tc.function.name for tc in m.tool_calls]
            tool_calls_info = f" [tool_calls: {tc_names}]"

        tool_call_id_info = ""
        if isinstance(m, dict) and "tool_call_id" in m:
            tool_call_id_info = f" [tool_call_id: {m['tool_call_id']}]"

        content_preview = (content[:80] + "...") if len(str(content)) > 80 else content
        print(f"  [{i}] role={role}{tool_calls_info}{tool_call_id_info}")
        if content_preview:
            print(f"      content: {content_preview}")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— 解析和执行 Tool Calls")
    print(f"使用模型: {MODEL}")
    print(f"已注册工具: {registry.list_tools()}")

    demo_single_tool_call()
    demo_parallel_tool_calls()
    demo_multi_tool_types()
    demo_multi_turn_tool_loop()
    demo_complete_message_history()

    print("\n" + "=" * 60)
    print("总结：使用 ToolRegistry 模式可以优雅地管理工具定义和执行。")
    print("parse_and_execute_tool_calls 函数是连接模型和实际工具的桥梁。")
    print("支持单次调用、并行调用和多轮循环，覆盖了大部分 Agent 场景。")
