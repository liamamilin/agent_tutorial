"""
第5章：结构化输出 —— Function Calling vs 正则解析
=====================================================
对比两种从 LLM 输出中提取结构化信息的方法：
1. 原生 Function Calling —— 干净、可靠、标准化
2. 手动正则解析 —— 脆弱、依赖格式、难以维护

通过实际代码展示两种方法在处理同一批任务时的表现差异。
"""

import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================================
# 任务定义：从用户输入中提取实体信息
# ============================================================================

SAMPLE_INPUTS = [
    "我叫张三，今年28岁，住在北京，我的邮箱是 zhangsan@example.com",
    "李四，上海，35岁，电话13812345678",
    "王五是杭州的一名工程师，电子邮件 wangwu@test.org",
    "赵六，30，来自深圳，没有联系方式",
]


# ============================================================================
# 方法一：正则表达式解析（传统方法）
# ============================================================================

def extract_with_regex(text: str) -> dict:
    """
    使用正则表达式从文本中提取姓名、年龄、城市、联系方式。

    问题：
    - 需要为每种格式编写规则，维护成本高
    - 对文本格式变化极其敏感
    - 无法理解语义（如"28岁"和"二十八岁"完全不同）
    - 无法处理复杂的嵌套或变体
    - 每个新实体类型都需要新增正则
    """
    result = {
        "name": None,
        "age": None,
        "city": None,
        "email": None,
        "phone": None,
    }

    # 提取邮箱 —— 有明确模式，相对容易
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        result["email"] = email_match.group()

    # 提取手机号 —— 中国手机号11位，1开头
    phone_match = re.search(r'1[3-9]\d{9}', text)
    if phone_match:
        result["phone"] = phone_match.group()

    # 提取年龄 —— 问题：中文中"28岁"、"28"、"二十八"、"年龄28"等格式繁多
    age_match = re.search(r'(\d+)\s*岁', text)
    if age_match:
        result["age"] = int(age_match.group(1))
    else:
        # 备用：尝试 "年龄: 28"
        age_match = re.search(r'年龄[：:]\s*(\d+)', text)
        if age_match:
            result["age"] = int(age_match.group(1))

    # 提取城市 —— 需要维护一个城市名称列表
    known_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉"]
    for city in known_cities:
        if city in text:
            result["city"] = city
            break
    # 如果不在列表中呢？正则无法处理，除非穷举所有城市

    # 提取姓名 —— 最难的正则任务！
    # 中文人名没有明显模式，高度依赖语境
    # 这里只做最简单的尝试：找"我叫XXX"模式
    name_match = re.search(r'我叫(\S{1,3})', text)
    if name_match:
        result["name"] = name_match.group(1)
    else:
        # 尝试匹配 "XXX，28岁" 模式（姓名在前，后跟逗号和数字）
        name_match = re.search(r'^(\S{1,3})[，,]\s*\d+', text)
        if name_match:
            result["name"] = name_match.group(1)
        else:
            # 尝试最后一个模式：文本开头的人名
            name_match = re.search(r'^(\S{1,3})\s*[，,]', text)
            if name_match:
                result["name"] = name_match.group(1)

    return result


# ============================================================================
# 方法二：原生 Function Calling（现代方法）
# ============================================================================

EXTRACT_ENTITY_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_entity",
        "description": (
            "从用户输入中提取个人信息实体。当用户提供了个人背景信息时使用。"
            "即使某些字段在文本中不存在，也要尽力推断或返回 null。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "提取到的姓名",
                },
                "age": {
                    "type": "integer",
                    "description": "年龄（从文字中提取，如'28岁'提取为28）",
                },
                "city": {
                    "type": "string",
                    "description": "城市名称",
                },
                "email": {
                    "type": "string",
                    "description": "邮箱地址",
                },
                "phone": {
                    "type": "string",
                    "description": "电话号码",
                },
            },
            "required": ["name"],  # 只要求 name 必填
        },
    },
}


def extract_with_function_calling(text: str) -> dict:
    """
    使用 OpenAI 原生 Function Calling 从文本中提取实体。

    优势：
    - 模型理解语义，不依赖模式匹配
    - 自动处理各种表达变体
    - 不需要维护正则规则
    - 新增字段只需修改 schema，无需重写解析逻辑
    - 模型可以"理解"文本中隐含的实体
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个信息提取助手。从用户输入中提取个人信息。",
            },
            {"role": "user", "content": text},
        ],
        tools=[EXTRACT_ENTITY_TOOL],
        tool_choice={
            "type": "function",
            "function": {"name": "extract_entity"},
        },
        temperature=0.1,  # 低温度以获得更一致的输出
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        args = json.loads(msg.tool_calls[0].function.arguments)
        return args

    return {}


# ============================================================================
# 对比测试
# ============================================================================

def compare_on_samples():
    """
    在相同的样本上运行两种方法，并排比较结果。

    对比维度：
    1. 准确性：能否正确提取实体
    2. 健壮性：对不同文本格式的适应能力
    3. 完整性：能否提取到所有要求的字段
    4. 代码复杂度：实现和维护的难易程度
    """
    print("\n" + "=" * 60)
    print("【对比测试】正则 vs Function Calling")
    print("=" * 60)

    for i, text in enumerate(SAMPLE_INPUTS, 1):
        print(f"\n{'─' * 60}")
        print(f"样本 {i}: {text}")

        # 正则方法
        regex_result = extract_with_regex(text)
        print(f"\n  📝 正则方法:")
        for key, value in regex_result.items():
            status = "✅" if value is not None else "❌"
            print(f"     {status} {key}: {value}")

        # Function Calling 方法
        fc_result = extract_with_function_calling(text)
        print(f"\n  🤖 Function Calling:")
        for key in regex_result.keys():
            value = fc_result.get(key)
            status = "✅" if value is not None else "❌"
            print(f"     {status} {key}: {value}")

        # 简单对比总结
        regex_filled = sum(1 for v in regex_result.values() if v is not None)
        fc_filled = sum(1 for v in fc_result.values() if v is not None)
        print(f"\n  📊 正则提取到 {regex_filled}/5 个字段")
        print(f"  📊 FC 提取到 {fc_filled}/5 个字段")


# ============================================================================
# 极限测试 —— 边界情况
# ============================================================================

EDGE_CASES = [
    # 情况1: 间接表达
    "小明马上就要三十了，他住的那个城市挨着上海，你可以给他发邮件到 xm@test.com",
    # 情况2: 纯数字，没有"岁"字
    "张三 25 北京 zhangsan@test.com 13900001111",
    # 情况3: 信息分散在长文本中
    (
        "今天天气真好，我想起我的朋友张三。他已经在杭州生活了十年，"
        "今年应该32岁了。对了，上次他给我留了个邮箱 zs@example.com，"
        "说有事可以联系他。他的电话好像是 13800009999。"
    ),
    # 情况4: 英文为主
    "My name is John, I'm 28 years old, living in Beijing, email john@example.com",
]


def compare_edge_cases():
    """
    在边界情况下比较两种方法。这些边界情况是对正则方法的"压力测试"。
    """
    print("\n" + "=" * 60)
    print("【边界测试】处理复杂和非常规文本")
    print("=" * 60)

    for i, text in enumerate(EDGE_CASES, 1):
        print(f"\n{'─' * 60}")
        print(f"边界案例 {i}: {text[:80]}...")

        regex_result = extract_with_regex(text)
        fc_result = extract_with_function_calling(text)

        print(f"\n  正则: name={regex_result['name']}, age={regex_result['age']}, "
              f"city={regex_result['city']}, email={regex_result['email']}, "
              f"phone={regex_result['phone']}")

        print(f"  FC:   name={fc_result.get('name')}, age={fc_result.get('age')}, "
              f"city={fc_result.get('city')}, email={fc_result.get('email')}, "
              f"phone={fc_result.get('phone')}")


# ============================================================================
# 方法三：混合方法 —— 最佳实践
# ============================================================================

def hybrid_approach():
    """
    混合方法：结合 Function Calling 和 Pydantic 验证。

    这是推荐的最佳实践：
    1. 用 Function Calling 提取结构化数据
    2. 用 Pydantic 验证数据完整性
    3. 添加后处理（如标准化、去重）

    这样可以同时获得 FC 的灵活性和 Pydantic 的安全性。
    """
    print("\n" + "=" * 60)
    print("【推荐方案】Function Calling + Pydantic 验证")
    print("=" * 60)

    from pydantic import BaseModel, Field, ValidationError

    class PersonEntity(BaseModel):
        """人员实体验证模型"""
        name: str = Field(min_length=1)
        age: int | None = Field(default=None, ge=0, le=150)
        city: str | None = Field(default=None)
        email: str | None = Field(default=None)
        phone: str | None = Field(default=None)

        @field_validator("email")
        @classmethod
        def validate_email(cls, v):
            if v is not None and "@" not in v:
                raise ValueError(f"无效的邮箱格式: {v}")
            return v

        @field_validator("phone")
        @classmethod
        def validate_phone(cls, v):
            if v is not None and not re.match(r'^1[3-9]\d{9}$', v):
                raise ValueError(f"无效的手机号格式: {v}")
            return v

    text = "张三，29岁，北京，zhangsan@example.com，13812345678"
    print(f"输入: {text}")

    # Step 1: Function Calling 提取
    fc_data = extract_with_function_calling(text)
    print(f"\nStep 1 - FC 提取: {json.dumps(fc_data, ensure_ascii=False)}")

    # Step 2: Pydantic 验证
    try:
        person = PersonEntity.model_validate(fc_data)
        print(f"\nStep 2 - Pydantic 验证通过:")
        print(f"  姓名: {person.name}")
        print(f"  年龄: {person.age}")
        print(f"  城市: {person.city}")
        print(f"  邮箱: {person.email}")
        print(f"  电话: {person.phone}")
    except ValidationError as e:
        print(f"\nStep 2 - Pydantic 验证失败:")
        print(f"  {e}")

    # Step 3: 如果验证失败，可以使用正则做后备或反馈给 LLM 重试
    print(f"\n💡 混合方案总结:")
    print(f"  - FC 负责'理解'和提取")
    print(f"  - Pydantic 负责'验证'和类型安全")
    print(f"  - 正则负责'后处理'（如格式标准化）")
    print(f"  - 各司其职，互为补充")


# ============================================================================
# 成本与权衡分析
# ============================================================================

def tradeoff_analysis():
    """
    系统分析三种方法的权衡。

    这不是代码，而是帮助你做技术选型的知识总结。
    """
    print("\n" + "=" * 60)
    print("【权衡分析】三种方法对比总结")
    print("=" * 60)

    comparison = """
┌──────────────────┬─────────────────┬─────────────────┬──────────────────┐
│ 维度             │ 正则表达式      │ Function Calling│ FC + Pydantic    │
├──────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ 准确性           │ ★★☆☆☆          │ ★★★★★           │ ★★★★★           │
│ 健壮性           │ ★☆☆☆☆          │ ★★★★☆           │ ★★★★★           │
│ 实现复杂度       │ ★★★☆☆          │ ★★☆☆☆           │ ★★☆☆☆           │
│ 维护成本         │ ★★★★★ (高)     │ ★★☆☆☆ (低)     │ ★☆☆☆☆ (很低)    │
│ API 调用成本     │ 无              │ 有（tokens）    │ 有（tokens）     │
│ 离线可用         │ 是              │ 否              │ 否              │
│ 延迟             │ 毫秒级          │ 秒级            │ 秒级            │
│ 处理语义模糊     │ 否              │ 是              │ 是              │
│ 处理新字段       │ 需新增正则      │ 修改 schema     │ 修改 Pydantic   │
│ 适用场景         │ 固定格式文本    │ 自然语言理解    │ 生产级应用      │
└──────────────────┴─────────────────┴─────────────────┴──────────────────┘
"""
    print(comparison)

    print("选择指南:")
    print("  1. 如果输入格式极其固定且不需要语义理解 -> 用正则")
    print("  2. 如果需要理解自然语言（推荐） -> 用 Function Calling")
    print("  3. 如果对数据质量有严格要求（强烈推荐） -> Function Calling + Pydantic")
    print("  4. 如果对延迟敏感且离线运行 -> 正则 + 传统 NLP")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— Function Calling vs 正则解析")
    print(f"使用模型: {MODEL}")

    compare_on_samples()
    compare_edge_cases()
    hybrid_approach()
    tradeoff_analysis()

    print("\n" + "=" * 60)
    print("总结：原生 Function Calling 是处理自然语言结构化提取的最佳选择。")
    print("正则适合格式极其固定的场景，但一旦格式有变动就容易出错。")
    print("推荐在生产环境中使用 Function Calling + Pydantic 的组合方案。")
