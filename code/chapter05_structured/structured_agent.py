"""
第5章：结构化输出 —— 综合项目：结构化 Agent
===============================================
本章的综合项目：构建一个使用 Function Calling 的完整 Agent。

这个 Agent 具备以下能力：
1. 对话历史管理 —— 维护多轮对话上下文
2. 工具注册系统 —— 统一管理工具的定义和执行
3. 原生 Function Calling —— 利用 OpenAI 的 tool_calls 机制
4. 多工具支持 —— 天气查询、搜索、计算、翻译
5. 完整的调用循环 —— 用户输入 → 模型决策 → 工具执行 → 结果反馈 → 最终回复

架构：
  User Input
      ↓
  StructuredAgent.run()
      ↓
  [Loop: 最多 N 轮]
      ↓
  LLM (with tools) → tool_calls?
      ├── No → 返回最终回复
      └── Yes → 执行工具 → 追加结果 → 继续循环
"""

import os
import json
import sys
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
# 第1部分：工具定义 —— 实际可用的工具函数
# ============================================================================

def get_weather(city: str) -> str:
    """
    查询天气（模拟实现，实际应调用天气 API）

    城市参数可以是中文或英文名。
    """
    weather_db = {
        "北京": "晴天，25°C，湿度40%，北风3级，空气质量优",
        "上海": "多云，28°C，湿度65%，东南风2级，空气质量良",
        "广州": "雷阵雨，32°C，湿度85%，无持续风，注意带伞",
        "深圳": "晴转多云，30°C，湿度70%，微风",
        "杭州": "小雨，22°C，湿度78%，西风2级",
        "成都": "阴天，26°C，湿度60%，无持续风",
        "tokyo": "Partly cloudy, 22°C, humidity 55%, light wind",
        "new york": "Sunny, 18°C, humidity 45%, NW wind 10mph",
    }
    return weather_db.get(city, f"{city}的天气：晴间多云，23°C，湿度50%（模拟数据）")


def search_knowledge(query: str, max_results: int = 3) -> str:
    """
    搜索知识库（模拟实现，实际应调用搜索引擎或向量数据库）

    实际项目中这里可能接入 Elasticsearch、向量数据库（如 Pinecone、Milvus）等。
    """
    # 模拟知识库
    kb = {
        "python": "Python 是一种解释型、面向对象的高级编程语言，由 Guido van Rossum 于 1991 年发布。",
        "agent": (
            "LLM Agent 是以大语言模型为核心、能够自主感知环境、做出决策并执行动作的智能体。"
            "它通常包含规划（Planning）、工具使用（Tool Use）和记忆（Memory）三大核心能力。"
        ),
        "function calling": (
            "Function Calling 是 OpenAI 提供的一种机制，允许模型在对话中请求调用预定义的函数。"
            "模型通过 tool_calls 响应返回结构化的 JSON 参数，开发者执行函数后将结果返回模型。"
        ),
        "pydantic": "Pydantic 是 Python 的数据验证库，使用类型注解定义数据模型，支持自动验证和序列化。",
    }

    results = []
    query_lower = query.lower()
    for key, value in kb.items():
        if key in query_lower or any(w in query_lower for w in key.split()):
            results.append(value)

    if not results:
        results.append(f"关于'{query}'，知识库中暂无精确匹配。请尝试其他关键词。")

    # 限制结果数量
    results = results[:max_results]
    return "\n\n".join(f"[{i+1}] {r}" for i, r in enumerate(results))


def calculate(expression: str) -> str:
    """
    安全地计算数学表达式。

    注意：生产环境中应该使用更安全的计算方式（如 numexpr 或预定义函数集），
    避免直接使用 eval()。这里使用受限的 ast 解析来保证安全。
    """
    import ast
    import operator

    # 安全的白名单操作符
    allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def safe_eval(node):
        """递归安全求值 AST 节点"""
        if isinstance(node, ast.Expression):
            return safe_eval(node.body)
        elif isinstance(node, ast.BinOp):
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            op_type = type(node.op)
            if op_type in allowed_ops:
                return allowed_ops[op_type](left, right)
            raise ValueError(f"不支持的操作符: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = safe_eval(node.operand)
            op_type = type(node.op)
            if op_type in allowed_ops:
                return allowed_ops[op_type](operand)
            raise ValueError(f"不支持的一元操作符: {op_type.__name__}")
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise ValueError(f"不支持的节点类型: {type(node).__name__}")

    try:
        tree = ast.parse(expression, mode="eval")
        result = safe_eval(tree)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


def get_current_time() -> str:
    """获取当前时间（模拟）"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')} (星期{['一','二','三','四','五','六','日'][now.weekday()]})"


# ============================================================================
# 第2部分：ToolRegistry —— 统一工具管理
# ============================================================================

class ToolRegistry:
    """
    集中管理所有工具的定义和执行。

    设计原则：
    - 单一职责：只负责工具的注册和执行
    - 开闭原则：通过 register() 添加新工具，无需修改现有代码
    - 接口统一：所有工具的 schema 格式一致，方便传给 OpenAI API
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable[..., str],
    ):
        """
        注册一个新工具。

        参数:
            name: 工具名称（唯一标识）
            description: 详细功能描述（帮助模型理解何时调用）
            parameters: JSON Schema 参数定义
            handler: 实际执行函数，接收关键字参数，返回字符串结果
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
        """获取所有工具的 schema 列表，可直接作为 API 的 tools 参数"""
        return [t["schema"] for t in self._tools.values()]

    def execute(self, name: str, arguments: dict) -> str:
        """
        根据工具名和参数执行对应的处理函数。

        返回:
            执行结果的字符串表示
        """
        if name not in self._tools:
            available = list(self._tools.keys())
            return f"错误: 未知工具 '{name}'。可用工具: {available}"

        handler = self._tools[name]["handler"]
        try:
            return str(handler(**arguments))
        except TypeError as e:
            return f"参数错误 ({name}): {e}。期望参数: {handler.__code__.co_varnames}"
        except Exception as e:
            return f"执行错误 ({name}): {e}"

    def get_tool_names(self) -> list[str]:
        """返回所有已注册工具的名称列表"""
        return list(self._tools.keys())


# ============================================================================
# 第3部分：StructuredAgent —— 完整的 Agent 实现
# ============================================================================

class StructuredAgent:
    """
    基于 Function Calling 的结构化 Agent。

    核心能力：
    - 多轮对话管理
    - 自动工具调用循环
    - 结果汇总和最终回复

    使用方法:
        agent = StructuredAgent()
        agent.register_default_tools()
        response = agent.run("你的问题")
    """

    def __init__(
        self,
        system_prompt: str | None = None,
        max_tool_rounds: int = 5,
        model: str | None = None,
    ):
        """
        初始化 Agent。

        参数:
            system_prompt: 系统提示词，定义 Agent 的角色和行为
            max_tool_rounds: 最大工具调用轮次（防止无限循环）
            model: 使用的模型名称，默认使用全局 MODEL
        """
        self.registry = ToolRegistry()
        self.max_tool_rounds = max_tool_rounds
        self.model = model or MODEL

        # 对话历史 —— Agent 的状态核心
        self.messages: list[dict] = []

        # 设置系统提示词
        if system_prompt is None:
            system_prompt = (
                "你是一个智能助手，可以访问以下工具来帮助用户解决问题：\n"
                "- 查询天气 (get_weather)\n"
                "- 搜索知识库 (search_knowledge)\n"
                "- 数学计算 (calculate)\n"
                "- 获取当前时间 (get_current_time)\n\n"
                "使用规则：\n"
                "1. 当用户的问题可以通过工具解决时，果断使用工具\n"
                "2. 根据工具返回的结果，用自然语言给用户清晰完整的回答\n"
                "3. 如果一次工具调用不够，可以多次调用\n"
                "4. 回答要友好、有帮助\n"
            )
        self.messages.append({"role": "system", "content": system_prompt})

    def register_default_tools(self):
        """注册 Agent 的默认工具集"""
        self.registry.register(
            name="get_weather",
            description="查询指定城市的实时天气信息。当用户询问天气时使用。",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'、'tokyo'等",
                    }
                },
                "required": ["city"],
            },
            handler=get_weather,
        )

        self.registry.register(
            name="search_knowledge",
            description="在知识库中搜索信息。当用户询问概念、定义、技术问题时使用。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或问题",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大返回结果数（默认3）",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
            handler=search_knowledge,
        )

        self.registry.register(
            name="calculate",
            description="执行数学计算。当用户要求计算、求值、算术运算时使用。",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2+3*4' 或 '(100-20)/4'",
                    }
                },
                "required": ["expression"],
            },
            handler=calculate,
        )

        self.registry.register(
            name="get_current_time",
            description="获取当前的日期和时间。当用户询问时间、日期、星期几时使用。",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=get_current_time,
        )

    def run(self, user_input: str, verbose: bool = True) -> str:
        """
        运行 Agent：处理用户输入，执行完整的工具调用循环，返回最终回复。

        参数:
            user_input: 用户的输入消息
            verbose: 是否打印详细的调试信息

        返回:
            模型的最终回复文本
        """
        # Step 1: 将用户消息加入对话历史
        self.messages.append({"role": "user", "content": user_input})

        if verbose:
            print(f"\n{'='*60}")
            print(f"👤 用户: {user_input}")
            print(f"{'='*60}")

        # Step 2: 工具调用循环
        for round_num in range(1, self.max_tool_rounds + 1):
            if verbose:
                print(f"\n--- 第 {round_num} 轮 ---")

            # 调用 LLM
            response = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.registry.get_schemas() or None,
                temperature=0.3,
            )

            assistant_message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            if verbose:
                print(f"  finish_reason: {finish_reason}")

            # 情况 A: 模型决定调用工具
            if assistant_message.tool_calls:
                if verbose:
                    print(f"  🔧 模型请求 {len(assistant_message.tool_calls)} 个工具调用")

                # 将助手的 tool_calls 消息加入历史
                self.messages.append(assistant_message)

                # 执行每个工具调用
                for tc in assistant_message.tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    if verbose:
                        print(f"    调用: {tool_name}({json.dumps(args, ensure_ascii=False)})")

                    # 执行工具
                    result = self.registry.execute(tool_name, args)

                    if verbose:
                        result_preview = result[:120] + "..." if len(result) > 120 else result
                        print(f"    结果: {result_preview}")

                    # 将工具结果加入历史
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # 继续循环，让模型基于工具结果继续推理
                continue

            # 情况 B: 模型直接回复（不调用工具）—— 循环结束
            else:
                final_content = assistant_message.content or ""
                self.messages.append({
                    "role": "assistant",
                    "content": final_content,
                })

                if verbose:
                    print(f"\n{'='*60}")
                    print(f"🤖 Agent 回复:")
                    print(f"{'='*60}")
                    print(final_content)

                return final_content

        # 达到最大轮次上限
        fallback = "抱歉，处理过程花费了太长时间。请尝试简化您的问题。"
        if verbose:
            print(f"\n⚠️  达到最大轮次 {self.max_tool_rounds}，返回兜底回复")
        return fallback

    def get_history(self) -> list[dict]:
        """获取完整的对话历史（用于调试和持久化）"""
        return self.messages

    def clear_history(self):
        """清空对话历史，保留系统提示词"""
        system_msg = self.messages[0] if self.messages else None
        self.messages = [system_msg] if system_msg else []

    def print_history(self):
        """打印对话历史的摘要（用于调试）"""
        print("\n" + "=" * 60)
        print("📋 对话历史摘要")
        print("=" * 60)
        for i, msg in enumerate(self.messages):
            role = msg["role"]
            content = msg.get("content", "")

            if role == "tool":
                tool_id = msg.get("tool_call_id", "?")
                print(f"  [{i}] {role} (id={tool_id}): {str(content)[:60]}...")
            elif role == "assistant" and "tool_calls" in msg:
                # 这是包含 tool_calls 的特殊消息，但没有 content
                tc_names = [tc["function"]["name"] if isinstance(tc, dict) else tc.function.name
                           for tc in msg.get("tool_calls", [])]
                print(f"  [{i}] {role}: [tool_calls: {tc_names}]")
            else:
                print(f"  [{i}] {role}: {str(content)[:80]}...")


# ============================================================================
# 第4部分：演示 —— 各种交互场景
# ============================================================================

def demo_basic_query():
    """单工具调用 —— 天气查询"""
    print("\n" + "=" * 70)
    print("【演示1】基本查询 —— 单个工具调用")
    print("=" * 70)

    agent = StructuredAgent()
    agent.register_default_tools()
    agent.run("今天北京天气怎么样？")


def demo_multi_tool():
    """多工具调用 —— 在同一个对话中先后使用不同工具"""
    print("\n" + "=" * 70)
    print("【演示2】多工具调用 —— 连续使用不同工具")
    print("=" * 70)

    agent = StructuredAgent()
    agent.register_default_tools()

    # 第一问：天气
    agent.run("上海天气如何？")

    # 第二问：搜索（利用同一个对话历史）
    agent.run("什么是 Function Calling？给我解释一下。")

    # 第三问：计算
    agent.run("帮我算一下 (456 + 789) * 12 / 3 等于多少？")


def demo_complex_reasoning():
    """需要多步推理的复杂问题"""
    print("\n" + "=" * 70)
    print("【演示3】复杂推理 —— 需要多步工具调用")
    print("=" * 70)

    agent = StructuredAgent()
    agent.register_default_tools()

    agent.run("北京天气如何？如果温度超过20度，帮我搜索一下'北京户外景点'；否则搜索'北京室内景点'。")


def demo_parallel_calls():
    """并行调用 —— 模型同时请求多个工具"""
    print("\n" + "=" * 70)
    print("【演示4】并行调用 —— 一次返回多个工具请求")
    print("=" * 70)

    agent = StructuredAgent()
    agent.register_default_tools()

    agent.run("同时查一下北京、上海、广州三地的天气")


def demo_conversation_with_context():
    """利用对话上下文的连续对话"""
    print("\n" + "=" * 70)
    print("【演示5】上下文对话 —— Agent 记住之前的交流")
    print("=" * 70)

    agent = StructuredAgent()
    agent.register_default_tools()

    agent.run("我叫小明，我住在北京。")
    agent.run("我之前说我住哪来着？帮我查查那里的天气。")
    agent.run("现在几点了？")


# ============================================================================
# 第5部分：Agent 的扩展性展示
# ============================================================================

def demo_custom_tool():
    """演示如何轻松扩展 Agent —— 添加自定义工具"""
    print("\n" + "=" * 70)
    print("【演示6】自定义工具 —— 扩展 Agent 的能力")
    print("=" * 70)

    agent = StructuredAgent()
    agent.register_default_tools()

    # 添加一个自定义的"翻译"工具
    def translate(text: str, target_lang: str = "英文") -> str:
        """简单的翻译模拟（实际应调用翻译 API）"""
        translations = {
            ("你好", "英文"): "Hello",
            ("谢谢", "英文"): "Thank you",
            ("人工智能", "英文"): "Artificial Intelligence",
            ("机器学习", "英文"): "Machine Learning",
        }
        key = (text, target_lang)
        if key in translations:
            return f"'{text}' 翻译为{target_lang}: {translations[key]}"
        # 使用 LLM 进行翻译
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": f"请将以下文本翻译为{target_lang}，只返回翻译结果：{text}"
            }],
            temperature=0.3,
        )
        return f"'{text}' 翻译为{target_lang}: {response.choices[0].message.content}"

    agent.registry.register(
        name="translate",
        description="将文本翻译为指定语言。当用户要求翻译时使用。",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要翻译的文本",
                },
                "target_lang": {
                    "type": "string",
                    "description": "目标语言，如'英文'、'日文'、'法文'等",
                },
            },
            "required": ["text", "target_lang"],
        },
        handler=translate,
    )

    print(f"  已注册工具: {agent.registry.get_tool_names()}")

    agent.run("帮我把'人工智能'翻译成英文")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— 综合项目：结构化 Agent")
    print(f"使用模型: {MODEL}")
    print("=" * 70)
    print("StructuredAgent —— 具备工具使用能力的智能代理")
    print("=" * 70)

    # 运行所有演示
    demo_basic_query()
    demo_multi_tool()
    demo_complex_reasoning()
    demo_parallel_calls()
    demo_conversation_with_context()
    demo_custom_tool()

    print("\n" + "=" * 70)
    print("总结：")
    print("1. StructuredAgent 是一个完整、可运行的 LLM Agent 实现")
    print("2. 基于 Function Calling 实现可靠的结构化输出")
    print("3. ToolRegistry 模式使工具管理清晰、易于扩展")
    print("4. 多轮循环支持复杂的多步推理任务")
    print("5. 对话历史管理支持上下文感知的连续对话")
    print("6. 你可以在此基础上添加更多工具、实现持久化存储等")
    print("=" * 70)
