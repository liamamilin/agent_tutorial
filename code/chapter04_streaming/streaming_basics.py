"""
流式输出原理

学习目标：
1. 理解 streaming 和非 streaming 的区别
2. 观察 chunk 的结构
3. 理解为什么 Agent 需要流式输出
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================
# 对比 1: 非流式调用（默认）
# ============================================================
print("=== 非流式（Non-Streaming） ===")
start = time.time()
resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "用20句话介绍人工智能。"}],
    stream=False,  # 默认值
)
elapsed = time.time() - start
print(f"等待时间: {elapsed:.2f}s")
print(f"完整回复: {resp.choices[0].message.content}")
print(f"回复字符数: {len(resp.choices[0].message.content)}")
print()

# ============================================================
# 对比 2: 流式调用
# ============================================================
print("=== 流式（Streaming） ===")
start = time.time()
stream = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "用20句话介绍人工智能。"}],
    stream=True,
)

first_chunk_time = None
full_text = ""
chunk_count = 0

print("逐 chunk 输出: ", end="", flush=True)
for chunk in stream:
    chunk_count += 1
    if first_chunk_time is None:
        first_chunk_time = time.time() - start

    # 最后一个 chunk 可能只带 usage 而没有 choices，务必先判空
    if not chunk.choices:
        continue

    delta = chunk.choices[0].delta
    if delta.content:
        full_text += delta.content
        print(delta.content, end="", flush=True)

elapsed = time.time() - start
print(f"\n\n统计:")
print(f"  首个 chunk 到达: {first_chunk_time:.2f}s")
print(f"  总耗时: {elapsed:.2f}s")
print(f"  Chunk 数量: {chunk_count}")
print(f"  回复字符数: {len(full_text)}")
