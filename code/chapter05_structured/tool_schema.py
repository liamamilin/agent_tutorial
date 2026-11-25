"""
第5章：结构化输出 —— 工具 Schema 深入
=======================================
深入讲解 OpenAI Function Calling 中工具定义的 JSON Schema。

工具 Schema 是 Function Calling 的核心 —— 它告诉模型：
- 有哪些函数可用
- 每个函数的作用
- 每个参数的类型和含义

写好 tool schema 是高质量 Function Calling 的前提。

本文件涵盖：
1. 基本参数类型：string, number, integer, boolean
2. enum 枚举参数
3. required vs optional 参数
4. 嵌套对象参数
5. 数组参数
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================================
# 第1部分：工具 Schema 的基本结构
# ============================================================================

def explain_tool_structure():
    """
    解释一个 tool schema 的基本组成部分。

    每个工具定义包含：
    - type: 固定为 "function"
    - function.name: 函数名（模型会引用这个名字）
    - function.description: 函数功能描述（帮助模型判断何时使用）
    - function.parameters: JSON Schema 描述的参数定义
    """
    print("\n" + "=" * 60)
    print("【基础知识】工具 Schema 的基本结构")
    print("=" * 60)

    example_tool = {
        "type": "function",
        "function": {
            # name: 函数的唯一标识符。
            # 模型在 tool_calls 中返回这个 name，代码用它来定位要执行的函数。
            "name": "send_email",

            # description: 详细说明这个函数是干什么的。
            # 模型依赖这个 description 来决定是否调用此函数。
            # 好的 description 要说明：
            #   1) 函数的功能
            #   2) 什么场景下应该使用
            #   3) 返回值是什么
            "description": (
                "发送一封电子邮件。当用户要求发送邮件、回复邮件或转发邮件时使用。"
                "不要在用户只是讨论邮件内容但没有明确要求发送时调用。"
            ),

            # parameters: 使用 JSON Schema 描述参数。
            # OpenAI 要求 type 为 "object"，参数在 properties 中定义。
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "收件人邮箱地址，例如 user@example.com",
                    },
                    "subject": {
                        "type": "string",
                        "description": "邮件主题",
                    },
                    "body": {
                        "type": "string",
                        "description": "邮件正文内容",
                    },
                    "cc": {
                        "type": "string",
                        "description": "抄送邮箱地址，可选",
                    },
                },
                # required: 列出必填参数。
                # 模型会确保这些参数一定被提供。
                "required": ["to", "subject", "body"],
            },
        },
    }

    print(json.dumps(example_tool, ensure_ascii=False, indent=2))
    return example_tool


# ============================================================================
# 第2部分：各种参数类型示例
# ============================================================================

# --- Tool 1: 展示 string / number / integer / boolean 类型 ---
CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "执行数学计算。支持加法、减法、乘法、除法。",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",           # string 类型
                    "description": "运算类型",
                    "enum": ["add", "subtract", "multiply", "divide"],  # 枚举约束
                },
                "a": {
                    "type": "number",           # number 类型（浮点数）
                    "description": "第一个操作数",
                },
                "b": {
                    "type": "number",
                    "description": "第二个操作数",
                },
                "round_result": {
                    "type": "boolean",          # boolean 类型
                    "description": "是否对结果四舍五入取整",
                },
            },
            "required": ["operation", "a", "b"],
        },
    },
}

# --- Tool 2: 展示嵌套对象 ---
BOOKING_TOOL = {
    "type": "function",
    "function": {
        "name": "book_hotel",
        "description": "预订酒店房间。",
        "parameters": {
            "type": "object",
            "properties": {
                "hotel_name": {
                    "type": "string",
                    "description": "酒店名称",
                },
                "check_in": {
                    "type": "string",
                    "description": "入住日期，格式 YYYY-MM-DD",
                },
                "check_out": {
                    "type": "string",
                    "description": "退房日期，格式 YYYY-MM-DD",
                },
                "rooms": {
                    "type": "integer",          # integer 类型（整数）
                    "description": "房间数量",
                },
                "guests": {
                    "type": "array",            # array 类型 —— 数组
                    "description": "住客信息列表",
                    "items": {
                        "type": "object",       # 数组中每个元素是对象（嵌套对象）
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "住客姓名",
                            },
                            "age": {
                                "type": "integer",
                                "description": "年龄",
                            },
                            "special_requests": {
                                "type": "string",
                                "description": "特殊需求（如高楼层、无烟房），可选",
                            },
                        },
                        "required": ["name", "age"],
                    },
                },
                "contact": {
                    "type": "object",           # 嵌套对象
                    "description": "联系人信息",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "联系电话",
                        },
                        "email": {
                            "type": "string",
                            "description": "电子邮箱",
                        },
                    },
                    "required": ["phone"],
                },
            },
            "required": ["hotel_name", "check_in", "check_out", "rooms"],
        },
    },
}

# --- Tool 3: 展示 enum + 可选参数 ---
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "在知识库中搜索文档。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "doc_type": {
                    "type": "string",
                    "description": "文档类型过滤",
                    "enum": ["report", "manual", "article", "email", "all"],
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回结果数（默认10）",
                    "default": 10,
                },
                "sort_by": {
                    "type": "string",
                    "description": "排序方式（可选）",
                    "enum": ["relevance", "date", "title"],
                },
                "date_from": {
                    "type": "string",
                    "description": "起始日期 YYYY-MM-DD（可选）",
                },
                "date_to": {
                    "type": "string",
                    "description": "结束日期 YYYY-MM-DD（可选）",
                },
            },
            "required": ["query"],  # 只有 query 是必填的，其余可选
        },
    },
}

# --- Tool 4: 展示复杂嵌套数组 + anyOf ---
ANALYTICS_TOOL = {
    "type": "function",
    "function": {
        "name": "run_analytics",
        "description": "对指定数据集运行分析。支持多种分析类型。",
        "parameters": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "数据集名称",
                },
                "metrics": {
                    "type": "array",
                    "description": "要计算的指标列表",
                    "items": {
                        "type": "string",
                        "enum": ["mean", "median", "std", "min", "max", "count", "sum"],
                    },
                },
                "filters": {
                    "type": "array",
                    "description": "过滤条件列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "description": "字段名",
                            },
                            "operator": {
                                "type": "string",
                                "enum": ["eq", "neq", "gt", "gte", "lt", "lte", "in", "contains"],
                            },
                            "value": {
                                "description": "比较值。可以是字符串或数字。",
                                # 使用 anyOf 支持多种类型
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "number"},
                                ],
                            },
                        },
                        "required": ["field", "operator", "value"],
                    },
                },
                "group_by": {
                    "type": "string",
                    "description": "分组字段（可选）",
                },
            },
            "required": ["dataset_name", "metrics"],
        },
    },
}


# ============================================================================
# 第3部分：对比测试 —— schema 质量对结果的影响
# ============================================================================

def test_tool_schema(tool_def: dict, user_input: str, label: str):
    """
    给模型一个工具定义，观察模型如何填充参数。
    通过对比不同质量的 schema，可以直观感受到写好 schema 的重要性。
    """
    print(f"\n--- {label} ---")
    print(f"工具: {tool_def['function']['name']}")
    print(f"用户输入: {user_input}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": user_input}],
        tools=[tool_def],
        temperature=0.3,
    )

    message = response.choices[0].message

    if message.tool_calls:
        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"  模型填充的参数:")
            print(f"    {json.dumps(args, ensure_ascii=False, indent=4)}")
    else:
        print(f"  模型没有调用工具，回复: {message.content}")


def demo_parameter_types():
    """
    逐个测试不同参数类型的 schema，观察模型如何理解和填充参数。
    """
    print("\n" + "=" * 60)
    print("【演示】各种参数类型的实际表现")
    print("=" * 60)

    # 测试计算器 —— 基本类型
    test_tool_schema(
        CALCULATOR_TOOL,
        "帮我算一下 15.7 乘以 3.2 等于多少，结果要四舍五入",
        "计算器工具（基本类型 + enum + boolean）"
    )

    # 测试酒店预订 —— 嵌套对象 + 数组
    test_tool_schema(
        BOOKING_TOOL,
        "我要在希尔顿酒店订两个房间，5月20日入住，5月23日退房。"
        "住客是张三和李四，张三35岁要无烟房，李四28岁。"
        "联系电话 13812345678。",
        "酒店预订（嵌套对象 + 复杂数组）"
    )

    # 测试搜索 —— enum + 可选参数
    test_tool_schema(
        SEARCH_TOOL,
        "帮我找最近一个月关于机器学习的报告，按日期排序，找5篇就行",
        "文档搜索（enum + 默认值 + 可选参数）"
    )

    # 测试分析工具 —— 复杂过滤
    test_tool_schema(
        ANALYTICS_TOOL,
        "分析销售数据，计算平均值和中位数，只看2024年的记录，"
        "按地区分组，过滤出金额大于10000的订单",
        "数据分析（anyOf + 嵌套过滤数组）"
    )


# ============================================================================
# 第4部分：Schema 编写最佳实践
# ============================================================================

def demo_schema_best_practices():
    """
    对比好的 schema 和坏的 schema，展示最佳实践。

    好的 schema 特点：
    1. description 清晰说明函数用途和使用场景
    2. 每个参数都有准确的 description
    3. 使用 enum 限制可选值
    4. required 准确标注必选/可选参数
    5. 参数名有明确含义

    坏的 schema 特点：
    1. description 模糊或缺失
    2. 参数没有说明
    3. 没有使用 enum 限制
    4. 没有标记 required
    5. 参数名含义不清（如 p1, p2）
    """
    print("\n" + "=" * 60)
    print("【最佳实践】好 Schema vs 坏 Schema")
    print("=" * 60)

    # 好的 schema
    good_schema = {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": (
                "创建一个提醒事项。当用户说'提醒我'、'设个闹钟'、"
                "'到时间通知我'等时使用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "提醒标题，简洁概括提醒内容",
                    },
                    "datetime": {
                        "type": "string",
                        "description": "提醒时间，ISO 8601 格式，如 2024-06-01T14:30:00",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "优先级",
                    },
                    "repeat": {
                        "type": "string",
                        "enum": ["none", "daily", "weekly", "monthly"],
                        "description": "重复模式（默认 none）",
                    },
                },
                "required": ["title", "datetime"],
            },
        },
    }

    # 坏的 schema
    bad_schema = {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "提醒",  # 太简短，模型难以判断何时使用
            "parameters": {
                "type": "object",
                "properties": {
                    "t": {"type": "string"},   # 含义不清
                    "d": {"type": "string"},   # 没有 description
                    "p": {"type": "string"},   # 没有 enum 限制
                },
                # 没有 required 字段
            },
        },
    }

    user_input = "明天下午3点提醒我开会"

    print("\n使用【好的 Schema】:")
    test_tool_schema(good_schema, user_input, "好 Schema")

    print("\n使用【坏的 Schema】:")
    test_tool_schema(bad_schema, user_input, "坏 Schema")

    print("\n对比总结:")
    print("  - 好的 schema：参数填充精确，值在约束范围内")
    print("  - 坏的 schema：参数可能缺失、值不可预测、难以在代码中使用")


# ============================================================================
# 第5部分：从 Pydantic 模型自动生成 Tool Schema
# ============================================================================

def demo_pydantic_to_tool():
    """
    如果你已经用 Pydantic 定义了数据模型，可以自动转换成 tool schema。

    这避免了手动维护两份定义（Pydantic 模型 + tool schema）的问题。
    """
    print("\n" + "=" * 60)
    print("【技巧】从 Pydantic 模型生成 Tool Schema")
    print("=" * 60)

    # 这里演示手动转换的方法（Pydantic model_json_schema 的结果
    # 可以直接用于 parameters 字段）

    from pydantic import BaseModel, Field

    class WeatherQuery(BaseModel):
        """查询天气的参数模型"""
        city: str = Field(description="城市名称")
        date: Optional[str] = Field(
            default=None,
            description="日期，格式 YYYY-MM-DD。不提供则查询今天。",
        )
        include_forecast: bool = Field(
            default=False,
            description="是否包含未来一周的预报",
        )

    # 从 Pydantic 模型生成 JSON Schema
    json_schema = WeatherQuery.model_json_schema()
    print("Pydantic model_json_schema() 输出:")
    print(json.dumps(json_schema, ensure_ascii=False, indent=2))

    # 组装为 tool schema
    tool_from_pydantic = {
        "type": "function",
        "function": {
            "name": "query_weather",
            "description": WeatherQuery.__doc__ or "查询天气",
            # 直接使用 Pydantic 生成的 schema 作为 parameters
            "parameters": json_schema,
        },
    }

    print("\n自动生成的 Tool Schema:")
    print(json.dumps(tool_from_pydantic, ensure_ascii=False, indent=2))


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— 工具 Schema 深入")
    print(f"使用模型: {MODEL}")

    explain_tool_structure()
    demo_parameter_types()
    demo_schema_best_practices()
    demo_pydantic_to_tool()

    print("\n" + "=" * 60)
    print("总结：Tool Schema 是 Function Calling 的基础设施。")
    print("高质量的 schema = 准确的 description + 精确的类型定义 +")
    print("合理的 enum 约束 + 正确的 required 标记。")
    print("利用 Pydantic 可以自动生成 schema，减少手动维护成本。")
