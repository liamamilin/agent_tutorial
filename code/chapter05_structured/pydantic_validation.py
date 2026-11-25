"""
第5章：结构化输出 —— Pydantic 验证
=====================================
演示如何使用 Pydantic 验证 LLM 输出的 JSON 数据。
Pydantic 提供了类型安全的解析和自动验证，是 LLM 输出处理的最佳拍档。

学习目标：
1. 定义 Pydantic 模型来描述期望的数据结构
2. 将 LLM 的 JSON 输出解析为 Pydantic 对象
3. 处理验证错误并给出有意义的反馈
4. 利用 Pydantic 的验证能力进行自动纠错
"""

import os
import json
from typing import Optional, Literal
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

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
# 第1部分：定义 Pydantic 模型
# ============================================================================

class WeatherReport(BaseModel):
    """
    天气预报模型 —— 一个简单的结构化数据定义。

    每个字段都有类型标注和描述，Pydantic 会自动验证类型。
    """
    city: str = Field(description="城市名称")
    temperature: float = Field(description="温度（摄氏度）")
    humidity: int = Field(description="湿度（百分比，0-100）", ge=0, le=100)
    condition: Literal["sunny", "cloudy", "rainy", "snowy", "stormy"] = Field(
        description="天气状况"
    )
    wind_speed: Optional[float] = Field(
        default=None, description="风速（km/h），可选"
    )

    @field_validator("temperature")
    @classmethod
    def temp_must_be_reasonable(cls, v: float) -> float:
        """自定义验证：温度应该在合理范围内（-50 ~ 55°C）"""
        if v < -50 or v > 55:
            raise ValueError(f"温度 {v}°C 不合理，应该在 -50 到 55 之间")
        return v


class TravelPlan(BaseModel):
    """
    旅行计划模型 —— 展示嵌套对象和数组。

    包含目的地列表，每个目的地有城市、停留天数、和可选的备注。
    """
    class Destination(BaseModel):
        """嵌套模型：单个目的地"""
        city: str = Field(description="城市名")
        days: int = Field(description="停留天数", ge=1)
        activities: list[str] = Field(description="计划活动列表")
        notes: Optional[str] = Field(default=None, description="备注")

    traveler: str = Field(description="旅行者姓名")
    total_budget: float = Field(description="总预算（元）", ge=0)
    destinations: list[Destination] = Field(description="目的地列表", min_length=1)
    start_date: Optional[str] = Field(default=None, description="出发日期 YYYY-MM-DD")

    @model_validator(mode="after")
    def budget_must_be_sufficient(self):
        """模型级别的验证：预算至少覆盖每天500元"""
        total_days = sum(d.days for d in self.destinations)
        min_budget = total_days * 500
        if self.total_budget < min_budget:
            raise ValueError(
                f"总预算 {self.total_budget} 不足以覆盖 {total_days} 天的旅行 "
                f"（至少需要 {min_budget}，按每天500元计算）"
            )
        return self


class CodeSnippet(BaseModel):
    """
    代码片段模型 —— 展示如何处理可能有语法错误的 JSON 内容。
    """
    language: str = Field(description="编程语言")
    code: str = Field(description="代码内容")
    explanation: str = Field(description="代码解释")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        description="难度等级"
    )


# ============================================================================
# 第2部分：辅助函数 —— 从 LLM 获取 JSON 并验证
# ============================================================================

def get_json_from_llm(prompt: str, system_prompt: str = "") -> str:
    """通用函数：向 LLM 发送请求并获取原始文本内容。"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


def clean_json_text(text: str) -> str:
    """
    清理 LLM 返回的文本中可能夹杂的 markdown 代码块标记。
    LLM 经常把 JSON 包在 ```json ... ``` 里，需要去掉。
    """
    text = text.strip()
    if text.startswith("```"):
        # 去掉开头的 ```json 或 ```
        lines = text.split("\n")
        # 去掉首尾的 ``` 行
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


def parse_with_validation(raw_text: str, model_class: type[BaseModel]):
    """
    核心函数：将 LLM 输出解析为 Pydantic 模型。

    流程：
    1. 清理 markdown 包裹
    2. 尝试 JSON 解析
    3. 尝试 Pydantic 模型验证
    4. 如果失败，返回错误信息

    返回: (成功标志, 解析后的对象或None, 错误信息)
    """
    print(f"  原始输出（截断）: {raw_text[:200]}...")

    # Step 1: 清理
    cleaned = clean_json_text(raw_text)

    # Step 2: JSON 解析
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return False, None, f"JSON 解析失败: {e}"

    # Step 3: Pydantic 验证
    try:
        obj = model_class.model_validate(data)
        return True, obj, None
    except ValidationError as e:
        return False, None, f"Pydantic 验证失败:\n{e}"


# ============================================================================
# 第3部分：各场景演示
# ============================================================================

def demo_weather_report():
    """
    演示一：天气预报解析
    使用 Pydantic 验证 LLM 输出的天气数据。
    这是最基础的使用场景。
    """
    print("\n" + "=" * 60)
    print("【演示一】天气预报 —— 基础 Pydantic 验证")
    print("=" * 60)

    prompt = (
        "今天北京的天气是晴天，温度 24.5 度，湿度 45%，风速 12 km/h。"
        "请以 JSON 返回天气信息，字段: city, temperature, humidity, condition, wind_speed。"
        "condition 必须是以下之一: sunny, cloudy, rainy, snowy, stormy。"
        "只返回 JSON。"
    )

    raw = get_json_from_llm(prompt)
    success, obj, error = parse_with_validation(raw, WeatherReport)

    if success:
        print(f"  ✅ 验证通过!")
        print(f"     城市: {obj.city}")
        print(f"     温度: {obj.temperature}°C")
        print(f"     湿度: {obj.humidity}%")
        print(f"     天气: {obj.condition}")
        print(f"     风速: {obj.wind_speed} km/h")
    else:
        print(f"  ❌ {error}")


def demo_travel_plan():
    """
    演示二：旅行计划解析
    展示嵌套模型、数组字段、自定义验证器的完整用法。
    """
    print("\n" + "=" * 60)
    print("【演示二】旅行计划 —— 嵌套模型 + 自定义验证")
    print("=" * 60)

    prompt = (
        "小明计划去三个城市旅行：北京3天（爬长城、逛故宫），上海2天（外滩、迪士尼），"
        "杭州2天（西湖、灵隐寺）。总预算6000元，5月20日出发。"
        "请以JSON返回旅行计划，包含: traveler, total_budget, destinations（数组，"
        "每个元素含 city, days, activities 数组, notes 可选字段）, start_date。"
        "只返回 JSON。"
    )

    raw = get_json_from_llm(prompt)
    success, obj, error = parse_with_validation(raw, TravelPlan)

    if success:
        print(f"  ✅ 验证通过!")
        print(f"     旅行者: {obj.traveler}")
        print(f"     出发日: {obj.start_date}")
        print(f"     预算: {obj.total_budget} 元")
        print(f"     目的地数量: {len(obj.destinations)}")
        for i, dest in enumerate(obj.destinations, 1):
            print(f"       [{i}] {dest.city} - {dest.days}天 - {', '.join(dest.activities)}")
    else:
        print(f"  ❌ {error}")


def demo_validation_failure():
    """
    演示三：故意触发验证失败
    让 LLM 输出一个不符合 Pydantic 模型的数据，
    展示 Pydantic 如何捕获并报告错误。
    """
    print("\n" + "=" * 60)
    print("【演示三】验证失败处理 —— 捕获并报告错误")
    print("=" * 60)

    # 故意要求一个 condition 不在枚举范围内的数据
    prompt = (
        "描述今天深圳的天气：多云转阵雨，温度 60 度，湿度 80%。"
        "用 JSON 返回，字段: city, temperature, humidity, condition。"
        "注意：condition 必须是 sunny, cloudy, rainy, snowy, stormy 之一。"
        "只返回 JSON。"
    )

    raw = get_json_from_llm(prompt)
    success, obj, error = parse_with_validation(raw, WeatherReport)

    if success:
        print(f"  ✅ 验证通过（模型正确使用了枚举值）")
        print(f"     条件: {obj.condition}")
    else:
        print(f"  ❌ 验证失败！")
        print(f"     {error}")
        print(f"  💡 在实际应用中，你可以将错误信息反馈给 LLM 进行修正。")


def demo_code_snippet():
    """
    演示四：代码片段解析
    展示更丰富的 Pydantic 约束 —— Literal 类型做枚举验证。
    """
    print("\n" + "=" * 60)
    print("【演示四】代码片段 —— Literal 枚举约束")
    print("=" * 60)

    prompt = (
        "用 Python 写一个冒泡排序函数，加上中文注释，并说明其原理。"
        "以 JSON 返回，字段: language, code, explanation, difficulty。"
        "difficulty 必须是 beginner, intermediate, advanced 之一。"
        "只返回 JSON。"
    )

    raw = get_json_from_llm(prompt)
    success, obj, error = parse_with_validation(raw, CodeSnippet)

    if success:
        print(f"  ✅ 验证通过!")
        print(f"     语言: {obj.language}")
        print(f"     难度: {obj.difficulty}")
        print(f"     解释: {obj.explanation[:100]}...")
        print(f"     代码:")
        for line in obj.code.split("\n")[:5]:
            print(f"       {line}")
        if len(obj.code.split("\n")) > 5:
            print(f"       ...（共 {len(obj.code.splitlines())} 行）")
    else:
        print(f"  ❌ {error}")


def demo_retry_on_validation_error():
    """
    演示五：验证失败后的重试机制
    当 Pydantic 验证失败时，将错误信息反馈给 LLM，让它自我修正。

    这是实际应用中的关键模式：
    1. 获取 LLM 输出
    2. 尝试 Pydantic 验证
    3. 如果失败，将验证错误发送回 LLM
    4. LLM 根据错误信息修正输出
    """
    print("\n" + "=" * 60)
    print("【演示五】验证失败 → 自动重试修正")
    print("=" * 60)

    # 构造一个有意不合理的 prompt，导致预算不足
    prompt = (
        "小红想去巴黎旅行5天，预算只有1000元。"
        "请以 JSON 返回旅行计划，字段: traveler, total_budget, destinations。"
        "destinations 数组中每个元素含 city, days, activities。"
        "只返回 JSON。"
    )

    max_retries = 3
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(1, max_retries + 1):
        print(f"\n  --- 第 {attempt} 次尝试 ---")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
        )
        raw = response.choices[0].message.content

        success, obj, error = parse_with_validation(raw, TravelPlan)

        if success:
            print(f"  ✅ 第 {attempt} 次尝试成功!")
            print(f"     旅行者: {obj.traveler}, 预算: {obj.total_budget} 元")
            break
        else:
            print(f"  ❌ 第 {attempt} 次验证失败")
            # 将错误信息追加到对话中，让 LLM 自我修正
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": (
                    f"你返回的 JSON 不符合要求。验证错误如下：\n"
                    f"{error}\n"
                    f"请根据以上错误修正你的 JSON 输出。只返回修正后的 JSON。"
                )
            })
    else:
        print(f"  ⚠️  {max_retries} 次尝试后仍未通过验证，请人工检查。")


# ============================================================================
# 第4部分：Pydantic v2 的高级特性
# ============================================================================

class ExtractedEntity(BaseModel):
    """
    实体抽取模型 —— 展示 Pydantic 的高级验证特性。

    包括：
    - Field 的 ge/le/min_length 约束
    - 自定义 field_validator
    - 模型文档字符串自动成为 JSON Schema description
    """
    name: str = Field(description="实体名称", min_length=1)

    entity_type: Literal["person", "organization", "location", "date", "event"] = Field(
        description="实体类型"
    )

    confidence: float = Field(
        description="置信度（0.0-1.0）",
        ge=0.0,
        le=1.0,
    )

    context: Optional[str] = Field(
        default=None,
        description="实体在原文中的上下文",
        max_length=200,
    )

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """名称不能只有空白字符"""
        if not v.strip():
            raise ValueError("实体名称不能为空")
        return v.strip()


def demo_entity_extraction():
    """
    演示六：实体抽取 —— 展示 Field 约束和 field_validator
    """
    print("\n" + "=" * 60)
    print("【演示六】实体抽取 —— Field 约束 + 自定义验证器")
    print("=" * 60)

    text = "2024年3月，OpenAI 在旧金山发布了 GPT-4，Sam Altman 出席了发布会。"

    prompt = (
        f"从以下文本中抽取实体，以 JSON 数组返回。每个实体包含 name, entity_type "
        f"(person/organization/location/date/event), confidence (0.0-1.0), context。\n\n"
        f"文本: {text}\n\n"
        f"只返回 JSON 数组。"
    )

    raw = get_json_from_llm(prompt)
    cleaned = clean_json_text(raw)

    try:
        data_list = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        return

    if not isinstance(data_list, list):
        print("  ❌ 期望一个 JSON 数组")
        return

    success_count = 0
    for i, item in enumerate(data_list):
        try:
            entity = ExtractedEntity.model_validate(item)
            print(f"  ✅ [{entity.entity_type}] {entity.name} (置信度: {entity.confidence})")
            success_count += 1
        except ValidationError as e:
            print(f"  ❌ 实体 {i+1} 验证失败: {e.errors()}")

    print(f"\n  成功: {success_count}/{len(data_list)}")


# ============================================================================
# 第5部分：生成 JSON Schema
# ============================================================================

def demo_schema_generation():
    """
    演示七：从 Pydantic 模型自动生成 JSON Schema

    Pydantic 的一大优势是可以自动生成 JSON Schema，
    这个 Schema 可以直接放入 Function Calling 的 parameters 字段。
    """
    print("\n" + "=" * 60)
    print("【演示七】自动生成 JSON Schema")
    print("=" * 60)

    print("\nWeatherReport 的 JSON Schema:")
    # Pydantic v2 使用 model_json_schema()
    schema = WeatherReport.model_json_schema()
    print(json.dumps(schema, ensure_ascii=False, indent=2))

    print("\n💡 这个 Schema 可以直接用于 OpenAI Function Calling 的 parameters 字段。")
    print("   这样就不用手动编写复杂的 JSON Schema 了！")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— Pydantic 验证实战")
    print(f"使用模型: {MODEL}")

    demo_weather_report()
    demo_travel_plan()
    demo_validation_failure()
    demo_code_snippet()
    demo_retry_on_validation_error()
    demo_entity_extraction()
    demo_schema_generation()

    print("\n" + "=" * 60)
    print("总结：Pydantic 为 LLM 输出提供了类型安全的验证层。")
    print("结合验证失败重试机制，可以构建可靠的 LLM 输出管道。")
    print("下一节将介绍更强大的方案 —— OpenAI 原生 Function Calling。")
