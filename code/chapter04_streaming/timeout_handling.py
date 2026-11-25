"""
超时处理

学习目标：
1. 使用 timeout 参数控制请求超时
2. 处理超时后的降级策略
3. 理解 timeout 和 max_retries 的关系
"""

import os
from openai import OpenAI, APITimeoutError
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    # 全局超时设置
    timeout=30.0,  # 30 秒超时
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


def call_with_timeout(
    messages: list[dict],
    timeout: float = 10.0,
    temperature: float = 0.7,
) -> str:
    """
    带超时控制的 LLM 调用

    OpenAI SDK 的 timeout 参数：
    - 单个 float: 总超时时间
    - Timeout 对象: 分别设置连接超时和读取超时
    """
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            timeout=timeout,
        )
        return resp.choices[0].message.content

    except APITimeoutError:
        print(f"⚠️ 请求超时（>{timeout}s），返回降级回复")
        # 降级策略：返回预设回复
        return "抱歉，服务响应较慢，请稍后再试。"


# ============================================================
# 超时配置的最佳实践
# ============================================================
if __name__ == "__main__":
    print("超时配置建议:")
    print("-" * 40)
    print("短对话（<100 tokens）: timeout=10s")
    print("中等对话（100-500 tokens）: timeout=30s")
    print("长对话/复杂推理: timeout=60s-120s")
    print("流式输出: 需要更长的读取超时，短连接超时")
    print()
    print("生产环境建议:")
    print("  - 始终设置 timeout")
    print("  - 连接超时: 5-10s")
    print("  - 读取超时: 30-60s")
    print("  - 配合重试机制使用")

    # 正常调用
    reply = call_with_timeout(
        [{"role": "user", "content": "1+1=?"}],
        timeout=10.0,
    )
    print(f"\n回复: {reply}")
