"""
API 错误分类与处理

学习目标：
1. 理解常见 API 错误类型
2. 学会区分需要重试 vs 需要修改请求的错误
3. 为不同错误类型设计不同的处理策略
"""

import os
from openai import (
    OpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
)
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


def classify_error(error: Exception) -> str:
    """将错误分类为可恢复 / 不可恢复"""
    if isinstance(error, RateLimitError):
        return "rate_limit"       # 可重试
    elif isinstance(error, APITimeoutError):
        return "timeout"          # 可重试
    elif isinstance(error, APIConnectionError):
        return "connection"       # 可重试（网络波动）
    elif isinstance(error, AuthenticationError):
        return "auth"             # 不可重试（检查 API Key）
    elif isinstance(error, BadRequestError):
        return "bad_request"      # 不可重试（检查请求参数）
    elif isinstance(error, APIError):
        # 服务器内部错误 (5xx) 可重试，其他不可
        if hasattr(error, "status_code") and error.status_code and error.status_code >= 500:
            return "server_error"  # 可重试
        return "api_error"
    return "unknown"


def demonstrate_errors():
    """展示不同类型的错误（不会真的触发，只展示处理逻辑）"""
    test_cases = [
        ("正确的请求", lambda: client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )),
    ]

    for name, fn in test_cases:
        print(f"\n--- {name} ---")
        try:
            result = fn()
            print(f"✅ 成功: {result.choices[0].message.content}")
        except Exception as e:
            error_type = classify_error(e)
            print(f"❌ 错误类型: {error_type}")
            print(f"   原始错误: {e}")


if __name__ == "__main__":
    print("常见 API 错误类型速查表:")
    print("=" * 50)
    print("可重试（临时性错误）:")
    print("  RateLimitError   - 请求频率过高，等待后重试")
    print("  APITimeoutError  - 请求超时")
    print("  APIConnectionError - 网络连接问题")
    print("  5xx Server Error  - 服务器内部错误")
    print()
    print("不可重试（需要修改请求）:")
    print("  AuthenticationError - API Key 无效")
    print("  BadRequestError     - 请求参数错误（如 token 超限）")
    print("  4xx Client Error    - 其他客户端错误")

    demonstrate_errors()
