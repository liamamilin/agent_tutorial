"""
第5章：结构化输出 —— JSON 输出示例
=====================================
演示如何通过 prompt 工程引导 LLM 稳定输出 JSON 格式。
包含成功案例、失败案例，以及有无明确 JSON 指令的对比。

核心要点：
- LLM 会根据 prompt 的引导决定输出格式
- 明确要求 JSON 格式能显著提高成功率
- 但仅仅靠自然语言指令并不完全可靠
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# 统一客户端配置 —— 可通过环境变量切换不同的 LLM 后端
# ---------------------------------------------------------------------------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================================
# 场景一：不明确要求 JSON —— 模型自由发挥
# ============================================================================
def demo_no_json_instruction():
    """
    不给模型任何 JSON 格式要求，看看它返回什么。

    多数现代模型在这种场景下也会返回看似 JSON 的文本，
    但格式不固定、可能包含 markdown 包裹、额外注释等。
    """
    print("\n" + "=" * 60)
    print("【场景一】无 JSON 指令 —— 模型自由发挥")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "列出三种编程语言及其主要用途。"
            }
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    print(f"模型返回内容:\n{content}")

    # 尝试直接解析为 JSON —— 大概率会失败
    try:
        parsed = json.loads(content)
        print(f"\n✅ 意外地成功解析为 JSON: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"\n❌ 无法解析为 JSON（意料之中）: {e}")

    return content


# ============================================================================
# 场景二：明确要求输出 JSON —— 基本指令
# ============================================================================
def demo_simple_json_instruction():
    """
    在 prompt 中明确要求模型返回 JSON 格式。
    这比场景一可靠得多，但仍可能出现格式偏差。
    """
    print("\n" + "=" * 60)
    print("【场景二】明确要求 JSON 输出")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "列出三种编程语言及其主要用途。"
                    "请以 JSON 数组格式返回，每个元素包含 'name' 和 'purpose' 字段。"
                    "只返回 JSON，不要其他文字。"
                )
            }
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    print(f"模型返回内容:\n{content}")

    try:
        parsed = json.loads(content)
        print(f"\n✅ 成功解析为 JSON:")
        for item in parsed:
            print(f"   - {item.get('name', '?')}: {item.get('purpose', '?')}")
    except json.JSONDecodeError as e:
        print(f"\n❌ 解析失败: {e}")
        # 尝试去掉可能的 markdown 代码块包裹
        if content.startswith("```"):
            print("检测到 markdown 代码块，尝试清理...")
            cleaned = content.strip("`").strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            try:
                parsed = json.loads(cleaned)
                print(f"✅ 清理后成功解析")
            except json.JSONDecodeError:
                print(f"❌ 清理后仍然失败")

    return content


# ============================================================================
# 场景三：带 JSON Schema 约束的指令
# ============================================================================
def demo_json_with_schema():
    """
    在 prompt 中提供一个 JSON Schema 示例，引导模型严格遵循结构。

    这比仅仅说"返回 JSON"更可靠，因为模型看到了具体的字段定义。
    但这仍然只是"软约束"——模型可能会也可能不会遵循。
    """
    print("\n" + "=" * 60)
    print("【场景三】提供 JSON Schema 约束")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个数据分析助手。你必须始终以 JSON 格式回复。"
                    "你的回复必须符合以下结构:\n"
                    '{\n'
                    '  "summary": "一句话总结",\n'
                    '  "details": [\n'
                    '    {"language": "语言名", "strength": "优势", "ecosystem": "生态评分/10"}\n'
                    '  ],\n'
                    '  "recommendation": "推荐结论"\n'
                    '}'
                )
            },
            {
                "role": "user",
                "content": "比较 Python、JavaScript 和 Rust 三种语言。"
            }
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    print(f"模型返回内容:\n{content}")

    try:
        # 清理可能的 markdown 包裹
        cleaned = content
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            cleaned = "\n".join(lines)

        parsed = json.loads(cleaned)
        print(f"\n✅ 成功解析为 JSON:")
        print(f"   总结: {parsed.get('summary', 'N/A')}")
        print(f"   详情:")
        for d in parsed.get("details", []):
            print(f"     - {d.get('language', '?')}: {d.get('strength', '?')} (生态: {d.get('ecosystem', '?')})")
        print(f"   推荐: {parsed.get('recommendation', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"\n❌ 解析失败: {e}")

    return content


# ============================================================================
# 场景四：故意给一个"刁钻"的 prompt —— 展示失败案例
# ============================================================================
def demo_failure_case():
    """
    展示 JSON 输出的典型失败场景：
    - 要求模型输出嵌套 JSON
    - 内容中包含特殊字符（引号、换行）
    - 模型可能输出格式错误

    这类失败正是为什么我们需要 Function Calling 和 Pydantic 验证的原因。
    """
    print("\n" + "=" * 60)
    print("【场景四】失败案例 —— 嵌套 JSON + 特殊内容")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "用 JSON 描述一本小说的信息，包括: 书名（含引号，比如 \"To Kill a Mockingbird\"）、"
                    "作者、出版年份、以及一段包含换行的简介。JSON 格式: "
                    '{"title": "...", "author": "...", "year": ..., "description": "..."}'
                    "只返回 JSON。"
                )
            }
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    print(f"模型返回内容:\n{content}")

    # 尝试解析
    try:
        cleaned = content
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            cleaned = "\n".join(lines)
        parsed = json.loads(cleaned)
        print(f"\n✅ 成功解析")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 解析失败: {e}")
        print("这正是我们需要的——仅靠自然语言指令并不完全可靠，需要更强的约束手段。")

    return content


# ============================================================================
# 场景五：多次调用统计成功率
# ============================================================================
def demo_reliability_test(n_calls: int = 3):
    """
    多次调用同一 prompt，统计 JSON 解析的成功率。

    这展示了基于自然语言 prompt 的 JSON 输出的可靠性问题：
    即使在相同的 prompt 下，不同调用也可能产生不同的输出格式。
    """
    print("\n" + "=" * 60)
    print(f"【场景五】可靠性测试 —— 连续 {n_calls} 次调用")
    print("=" * 60)

    success_count = 0
    prompt = (
        "返回一个 JSON 对象，包含字段 name（你的名字）、mood（当前心情）、"
        "以及一个 hobbies 数组（你的三个爱好）。只返回 JSON，不要 markdown 包裹。"
    )

    for i in range(n_calls):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # 提高 temperature 增加多样性
        )
        content = response.choices[0].message.content
        try:
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").strip()
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:].strip()
            parsed = json.loads(cleaned)
            print(f"  调用 {i+1}: ✅ 成功 - {parsed.get('name', '?')}")
            success_count += 1
        except json.JSONDecodeError as e:
            print(f"  调用 {i+1}: ❌ 失败 - {str(e)[:60]}")

    print(f"\n成功率: {success_count}/{n_calls} ({100*success_count/n_calls:.0f}%)")
    print("提示：如果成功率不是 100%，就说明需要更强的约束手段（如 Function Calling）。")


# ============================================================================
# 主入口
# ============================================================================
if __name__ == "__main__":
    print("第5章：结构化输出 —— JSON 输出技巧与陷阱")
    print(f"使用模型: {MODEL}")

    # 逐一运行各个演示
    demo_no_json_instruction()
    demo_simple_json_instruction()
    demo_json_with_schema()
    demo_failure_case()
    demo_reliability_test(n_calls=3)

    print("\n" + "=" * 60)
    print("总结：自然语言 prompt 引导 JSON 输出是可行的，但不够可靠。")
    print("下一节将介绍如何使用 Pydantic 进行输出验证，")
    print("以及 OpenAI 原生 Function Calling 提供的强约束输出机制。")
