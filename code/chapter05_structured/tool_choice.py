"""
第5章：结构化输出 —— tool_choice 参数详解
============================================
演示 OpenAI tool_choice 参数的各种用法。

tool_choice 控制模型是否以及如何使用工具：
- "auto"（默认）: 模型自己决定是否调用工具
- "none": 禁止模型调用任何工具，即使提供了工具定义
- "required": 强制模型必须调用至少一个工具
- {"type": "function", "function": {"name": "xxx"}}: 强制调用指定的工具

理解 tool_choice 可以帮助你精确控制 Agent 的行为。
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ---------------------------------------------------------------------------
# 工具定义 —— 定义两个工具用于演示
# ---------------------------------------------------------------------------

GET_WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的实时天气信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称",
                }
            },
            "required": ["city"],
        },
    },
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "在互联网上搜索信息。当用户询问实时信息或需要查找资料时使用。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "num_results": {
                    "type": "integer",
                    "description": "返回结果数量",
                },
            },
            "required": ["query"],
        },
    },
}

ALL_TOOLS = [GET_WEATHER_TOOL, SEARCH_TOOL]


def simulate_tool_execution(tool_name: str, args: dict) -> str:
    """模拟工具执行（实际项目中应调用真实的 API）"""
    if tool_name == "get_weather":
        return f"{args.get('city', '未知城市')}的天气：晴，22°C，湿度 50%"
    elif tool_name == "search_web":
        return f"关于'{args.get('query', '')}'的搜索结果：（这里是模拟的搜索结果...）"
    return f"未知工具: {tool_name}"


# ============================================================================
# 演示1: tool_choice="auto" —— 默认行为
# ============================================================================

def demo_auto():
    """
    tool_choice="auto" (默认): 模型自主判断是否需要调用工具。

    当用户问题涉及到工具能处理的内容时，模型会调用工具；
    当问题与工具无关时，模型直接以文字回复。

    适用场景: 绝大多数对话场景，让模型智能判断。
    """
    print("\n" + "=" * 60)
    print("【演示1】tool_choice = 'auto' (默认)")
    print("=" * 60)

    test_cases = [
        "今天北京天气怎么样？",          # 应该调用 get_weather
        "什么是机器学习？请简要解释。",   # 应该不调用工具，直接回复
        "帮我搜索一下最新的 AI 新闻",    # 应该调用 search_web
    ]

    for user_input in test_cases:
        print(f"\n用户: {user_input}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": user_input}],
            tools=ALL_TOOLS,
            tool_choice="auto",  # 默认值，显式写出来以示强调
            temperature=0.3,
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                print(f"  -> 调用工具: {tc.function.name}({args})")
        else:
            print(f"  -> 直接回复: {msg.content[:80]}...")


# ============================================================================
# 演示2: tool_choice="none" —— 禁止使用工具
# ============================================================================

def demo_none():
    """
    tool_choice="none": 完全禁止模型调用工具。

    即使你提供了工具定义，模型也会忽略它们，只用文字回复。

    适用场景:
    - 你想先让用户澄清问题，暂时不让模型调用工具
    - 系统提示词中说"先回答用户的问题"，等用户确认后再调用工具
    - A/B 测试：对比有无工具时模型的回答质量
    """
    print("\n" + "=" * 60)
    print("【演示2】tool_choice = 'none' (禁止使用工具)")
    print("=" * 60)

    test_cases = [
        "今天北京天气怎么样？",          # 本来应该调用工具，但被禁止
        "帮我搜索最新的 AI 新闻",        # 同样被禁止
    ]

    for user_input in test_cases:
        print(f"\n用户: {user_input}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": user_input}],
            tools=ALL_TOOLS,
            tool_choice="none",  # 禁止调用工具
            temperature=0.3,
        )

        msg = response.choices[0].message

        print(f"  tool_calls: {msg.tool_calls}")
        print(f"  content: {msg.content[:120]}...")
        # 注意：模型可能会说类似"抱歉我无法获取实时天气"这样的回复


# ============================================================================
# 演示3: tool_choice="required" —— 强制使用工具
# ============================================================================

def demo_required():
    """
    tool_choice="required": 强制模型必须调用至少一个工具。

    即使问一个闲聊问题，模型也会想办法调用某个工具。

    适用场景:
    - 你确定用户的意图就是要执行某个操作
    - Agent 管道中，你已经分析了用户意图，知道需要工具，想跳过判断阶段
    - 防止模型"偷懒"不用工具

    注意: 如果模型实在无法确定调用哪个工具，可能会"强行"选一个不太合适的。
    """
    print("\n" + "=" * 60)
    print("【演示3】tool_choice = 'required' (强制使用工具)")
    print("=" * 60)

    test_cases = [
        "今天北京天气怎么样？",           # 自然的天气查询
        "你好，今天过得怎么样？",         # 闲聊 —— 但模型被强制调用工具！
        "Python 和 JavaScript 哪个更好？", # 主观问题 —— 模型也被强制调用工具
    ]

    for user_input in test_cases:
        print(f"\n用户: {user_input}")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": user_input}],
                tools=ALL_TOOLS,
                tool_choice="required",
                temperature=0.3,
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    print(f"  -> 强制调用了工具: {tc.function.name}({args})")
            else:
                print(f"  -> 意外：没有调用工具！")

        except Exception as e:
            print(f"  -> 错误: {e}")


# ============================================================================
# 演示4: 指定特定函数 —— 锁定工具
# ============================================================================

def demo_specific_function():
    """
    指定 tool_choice 为特定函数名，强制模型只使用该函数。

    格式: {"type": "function", "function": {"name": "函数名"}}

    适用场景:
    - 多步工作流中，某一步的意图已经明确，直接锁定工具
    - 你希望提取特定类型的结构化信息（如总是调用 extract_info）
    - 安全考虑：只允许调用某个安全的工具

    注意: 即使锁定了特定函数，你仍然可以（也应该）在 tools 参数中
    传入所有工具的列表（包括不被锁定的），或者只传被锁定的那个。
    """
    print("\n" + "=" * 60)
    print("【演示4】tool_choice 指定特定函数")
    print("=" * 60)

    # 即使用户问的是搜索问题，我们也强制模型调用 get_weather
    test_cases = [
        "帮我查一下北京的天气",     # 与所选的函数匹配
        "帮我搜索人工智能的最新进展", # 用户想搜索，但我们强制要求天气函数
    ]

    for user_input in test_cases:
        print(f"\n用户: {user_input}")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": user_input}],
                tools=ALL_TOOLS,
                # 强制指定只能调用 get_weather
                tool_choice={
                    "type": "function",
                    "function": {"name": "get_weather"},
                },
                temperature=0.3,
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    print(f"  -> 强制调用: {tc.function.name}({args})")
                    # 注意：第二个测试中模型可能会"强行"在搜索 query 里
                    # 塞入一个能当作 city 的值，这说明了强制指定函数
                    # 的局限性 —— 只应在意图明确的场景下使用。
            else:
                print(f"  -> 没有调用工具")

        except Exception as e:
            print(f"  -> 错误: {e}")


# ============================================================================
# 演示5: 实际应用场景对比
# ============================================================================

def demo_practical_scenario():
    """
    展示一个实际场景中 tool_choice 各模式的使用时机。

    场景: 用户说"我想知道明天适不适合去公园"
    分析: 这需要先查天气，然后做判断。但第一步是查天气。

    不同 tool_choice 的行为:
    - auto: 模型判断需要查天气 → 调用 get_weather
    - none: 模型直接给建议（可能不准确，因为没有真实天气数据）
    - required: 模型必须调用工具 → 调用 get_weather
    - 指定函数: 精确调用 get_weather
    """
    print("\n" + "=" * 60)
    print("【演示5】实际场景 —— 不同 tool_choice 的对比")
    print("=" * 60)

    user_input = "明天适合去公园吗？我在北京。"

    modes = {
        "auto": "auto",
        "none": "none",
        "required": "required",
        "特定函数(get_weather)": {"type": "function", "function": {"name": "get_weather"}},
    }

    for mode_name, mode_value in modes.items():
        print(f"\n--- tool_choice = {mode_name} ---")
        print(f"用户: {user_input}")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": user_input}],
                tools=ALL_TOOLS,
                tool_choice=mode_value,
                temperature=0.3,
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  调用: {tc.function.name}({tc.function.arguments})")

            if msg.content:
                print(f"  回复: {msg.content[:100]}...")

        except Exception as e:
            print(f"  错误: {e}")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— tool_choice 参数详解")
    print(f"使用模型: {MODEL}")

    demo_auto()
    demo_none()
    demo_required()
    demo_specific_function()
    demo_practical_scenario()

    print("\n" + "=" * 60)
    print("总结：tool_choice 参数让你精确控制模型何时使用工具。")
    print("  - 'auto': 适合大多数场景，让模型自主判断")
    print("  - 'none': 适合纯对话、信息收集、澄清问题")
    print("  - 'required': 适合已知需要工具的场景，强制使用")
    print("  - 指定函数: 适合多步工作流中锁定具体步骤")
