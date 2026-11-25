"""
深入理解 API 响应对象

学习目标：
1. 查看响应的完整结构
2. 提取 choices、usage、finish_reason
3. 理解 token 消耗统计
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

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "用一句话解释什么是API。"},
    ],
    temperature=0.3,
)

# ============================================================
# 1. 原始响应对象
# ============================================================
print("=== 原始响应对象 ===")
print(f"raw:{response}")
print(f"id: {response.id}")
print(f"model: {response.model}")
print(f"created: {response.created}")
print()

# ============================================================
# 2. choices 列表
# ============================================================
print("=== choices ===")
choice = response.choices[0]
print(f"finish_reason: {choice.finish_reason}")
print(f"message.role: {choice.message.role}")
print(f"message.content: {choice.message.content}")
print()

# ============================================================
# 3. usage —— 你的"账单"
# ============================================================
print("=== usage（Token 消耗） ===")
usage = response.usage
if usage:
    print(f"prompt_tokens（输入）:     {usage.prompt_tokens}")
    print(f"completion_tokens（输出）:  {usage.completion_tokens}")
    print(f"total_tokens（总计）:       {usage.total_tokens}")

    # GPT-4o-mini 定价（仅供参考，以官方为准）
    # 输入: $0.15 / 1M tokens
    # 输出: $0.60 / 1M tokens
    input_cost = usage.prompt_tokens * 0.15 / 1_000_000
    output_cost = usage.completion_tokens * 0.60 / 1_000_000
    print(f"\n估算费用（GPT-4o-mini）:")
    print(f"  输入费用: ${input_cost:.6f}")
    print(f"  输出费用: ${output_cost:.6f}")
    print(f"  总费用:   ${input_cost + output_cost:.6f}")
