"""
System Prompt 设计方法论

学习目标：
1. 掌握 System Prompt 的基本结构
2. 理解"身份 + 规则 + 约束"的三段式设计
3. 学会调试 System Prompt 效果
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


def test_prompt(system_prompt: str, user_input: str, label: str):
    """测试一个 system prompt 的效果"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,
    )
    print(f"\n{'='*50}")
    print(f"【{label}】")
    print(f"System: {system_prompt[:60]}...")
    print(f"User: {user_input}")
    print(f"Response: {resp.choices[0].message.content}")
    print(f"{'='*50}")


# ============================================================
# 三段式 System Prompt 结构
# ============================================================
# 一个好的 System Prompt 通常包含三段：
#   1. 身份（你是谁）
#   2. 规则（你怎么做）
#   3. 约束（你不能做什么 / 输出格式）

# --- 基础版：只有身份 ---
test_prompt(
    system_prompt="你是一个 Python 编程专家。",
    user_input="GIL 是什么？",
    label="基础版：只有身份",
)

# --- 进阶版：身份 + 规则 ---
test_prompt(
    system_prompt=(
        "你是一个 Python 编程专家。\n"
        "规则：\n"
        "1. 先给出简短定义，再展开详细解释\n"
        "2. 使用类比帮助理解\n"
        "3. 如果有代码示例，必须注明 Python 版本要求"
    ),
    user_input="GIL 是什么？",
    label="进阶版：身份 + 规则",
)

# --- 完整版：身份 + 规则 + 约束 ---
test_prompt(
    system_prompt=(
        "你是一个 Python 编程专家，面向初学者教学。\n\n"
        "回答规则：\n"
        "1. 先给出一句话总结\n"
        "2. 用类比解释核心概念\n"
        "3. 给出一个极简代码示例\n\n"
        "约束：\n"
        "- 不要使用过于专业的术语而不加解释\n"
        "- 代码示例不超过 5 行\n"
        "- 结尾给出一个延伸思考问题"
    ),
    user_input="GIL 是什么？",
    label="完整版：身份 + 规则 + 约束",
)
