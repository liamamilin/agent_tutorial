"""
HelloAgents — LLM 调用中枢

统一 OpenAI 兼容接口，支持多提供商。
"""

import os
from openai import OpenAI


class HelloAgentsLLM:
    """统一 LLM 调用接口（OpenAI 兼容）"""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
    ):
        self.model = model or os.getenv("LLM_MODEL_ID", "qwen3:14b")
        self.temperature = temperature

        self._client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )

    def invoke(self, messages: list[dict], **kwargs) -> str:
        """非流式调用"""
        t = kwargs.pop("temperature", self.temperature)
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=t,
            **kwargs,
        )
        return (resp.choices[0].message.content or "").strip()

    def think(self, messages: list[dict], **kwargs):
        """流式调用（生成器）"""
        t = kwargs.pop("temperature", self.temperature)
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=t,
            stream=True,
            **kwargs,
        )
        for event in stream:
            # 最后一个 chunk 可能只带 usage 而没有 choices，务必先判空
            if not event.choices:
                continue

            delta = event.choices[0].delta
            if delta.content:
                yield delta.content
