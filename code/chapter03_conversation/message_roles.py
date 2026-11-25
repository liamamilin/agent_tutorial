"""
Message 角色的深入理解

学习目标：
1. 理解 system / user / assistant 三种角色的含义
2. 观察不同角色对模型行为的影响
3. 理解为什么 system prompt 放在 messages 最前面
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


def call(messages: list[dict], temp: float = 0.7) -> str:
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=temp,
    )
    return resp.choices[0].message.content


# ============================================================
# 实验 1: 没有 system prompt
# ============================================================
print("=" * 50)
print("实验 1: 只有 user message（没有 system prompt）")
print("=" * 50)
r1 = call([
    {"role": "user", "content": "你是谁？请用一句话回答。"},
])
print(f"> {r1}\n")

# ============================================================
# 实验 2: 有 system prompt —— 设定身份
# ============================================================
print("=" * 50)
print('实验 2: system prompt 设定身份为"海盗"')
print("=" * 50)
r2 = call([
    {"role": "system", "content": "你是一个粗犷的加勒比海盗船长。用海盗的语气说话。"},
    {"role": "user", "content": "你是谁？"},
])
print(f"> {r2}\n")

# ============================================================
# 实验 3: system prompt 设定行为规则
# ============================================================
print("=" * 50)
print("实验 3: system prompt 设定输出规则")
print("=" * 50)
r3 = call([
    {
        "role": "system",
        "content": (
            "你是一个简洁的助手。回答规则：\n"
            "1. 每句话不超过 15 个字\n"
            "2. 使用编号列表\n"
            "3. 结尾加一个 emoji"
        ),
    },
    {"role": "user", "content": "推荐三个学习编程的方法。"},
])
print(f"> {r3}\n")

# ============================================================
# 实验 4: assistant 角色在历史中的作用
# ============================================================
print("=" * 50)
print("实验 4: 使用 assistant 历史维持上下文")
print("=" * 50)
r4 = call([
    {"role": "system", "content": "你是一个助教，帮助学生学习。"},
    {"role": "user", "content": "我叫小明。"},
    {"role": "assistant", "content": "好的，小明！我记住了。"},
    {"role": "user", "content": "我叫什么名字？"},
])
print(f"> {r4}")
