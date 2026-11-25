"""
指数退避重试机制

学习目标：
1. 实现带指数退避的重试逻辑
2. 理解为什么不能用固定间隔重试
3. 区分可重试和不可重试的错误
"""

import os
import time
import random
from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIError,
)
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


# ============================================================
# 可重试的错误类型
# ============================================================
RETRYABLE_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError)


def is_retryable(error: Exception) -> bool:
    """判断是否应该重试"""
    if isinstance(error, RETRYABLE_ERRORS):
        return True
    if isinstance(error, APIError):
        # 5xx 服务器错误可重试
        status = getattr(error, "status_code", None)
        return status is not None and status >= 500
    return False


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    计算指数退避的等待时间，加入随机抖动（jitter）

    公式: min(base_delay * 2^attempt + random_jitter, max_delay)

    示例:
      attempt 0: ~1s
      attempt 1: ~2s
      attempt 2: ~4s
      attempt 3: ~8s
      ...
    """
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, delay * 0.5)  # 最多 50% 的随机抖动
    return min(delay + jitter, max_delay)


def call_with_retry(
    messages: list[dict],
    max_retries: int = 3,
    base_delay: float = 1.0,
    temperature: float = 0.7,
) -> str:
    """
    带指数退避重试的 LLM 调用

    参数:
    - max_retries: 最大重试次数
    - base_delay: 基础等待时间（秒）
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
            )
            return resp.choices[0].message.content

        except Exception as e:
            last_error = e

            if not is_retryable(e):
                print(f"❌ 不可重试的错误: {type(e).__name__}")
                raise

            if attempt < max_retries:
                delay = exponential_backoff(attempt, base_delay)
                print(f"⚠️ {type(e).__name__} — 第 {attempt + 1} 次重试，等待 {delay:.1f}s...")
                time.sleep(delay)
            else:
                print(f"❌ 已达最大重试次数 ({max_retries})")

    raise last_error


# ============================================================
# 测试（正常调用，不一定会触发重试）
# ============================================================
if __name__ == "__main__":
    reply = call_with_retry([
        {"role": "user", "content": "1+1等于几？"},
    ])
    print(f"回复: {reply}")
