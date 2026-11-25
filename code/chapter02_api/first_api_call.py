"""
第一个 API 调用 —— 从零开始调用大语言模型

学习目标：
1. 加载 API 密钥
2. 初始化 OpenAI 客户端
3. 发送第一个请求
4. 理解请求和响应的基本结构
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# ============================================================
# 1. 初始化客户端
# ============================================================
# api_key: 你的 API 密钥（从 .env 中读取）
# base_url: API 端点地址（默认 OpenAI，可改为其他兼容服务）
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)

MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")

# ============================================================
# 2. 发送第一个请求
# ============================================================
# messages 是一个列表，每个元素是一个 dict，包含 role 和 content
# role 可以是 "system"（系统指令）、"user"（用户）、"assistant"（助手）
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "你是一个友善的AI助手。"},
        {"role": "user", "content": "你好！请用一句话介绍你自己。"},
    ],
    temperature=0.7,
)

# ============================================================
# 3. 提取并打印回复
# ============================================================
reply = response.choices[0].message.content
print("=" * 50)
print(f"模型回复: {reply}")
print("=" * 50)
