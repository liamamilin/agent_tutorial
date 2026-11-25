"""
封装可复用的 LLM 调用函数

学习目标：
1. 将 API 调用封装为可复用函数
2. 支持自定义参数（temperature、max_tokens 等）
3. 为后续 Agent 构建打基础
"""

import os
from typing import Sequence
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """
        发送消息并返回文本回复。

        参数：
        - messages: [{"role": "user", "content": "..."}, ...]
        - temperature: 0~2，越高越随机
        - max_tokens: 限制输出长度（None 表示不限制）
        """
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def chat_with_usage(self, messages: list[dict], **kwargs) -> tuple[str, dict]:
        """返回回复文本和 token 消耗信息"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        text = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }
        return text, usage


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    llm = LLMClient()

    # 基础调用
    reply = llm.chat([
        {"role": "system", "content": "你是一个简洁的助手，回答不超过一句话。"},
        {"role": "user", "content": "什么是机器学习？"},
    ])
    print(f"回复: {reply}")

    # 带用量统计的调用
    reply2, usage = llm.chat_with_usage([
        {"role": "user", "content": "1+1等于几？"},
    ])
    print(f"\n回复: {reply2}")
    print(f"Token 消耗: {usage}")
