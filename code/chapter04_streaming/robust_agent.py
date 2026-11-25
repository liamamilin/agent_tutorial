"""
项目：健壮的对话 Agent

整合第 3 章和第 4 章的全部能力：
- 多轮对话 + 历史管理
- 流式输出
- 重试 + 超时
- 日志
- 降级策略
"""

import os
import sys
import time
import random
import logging
from openai import (
    OpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIError,
)
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 日志
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RobustAgent")

# ============================================================
# 可重试错误
# ============================================================
RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError)


def is_retryable(error: Exception) -> bool:
    if isinstance(error, RETRYABLE):
        return True
    if isinstance(error, APIError):
        status = getattr(error, "status_code", None)
        return status is not None and status >= 500
    return False


def backoff(attempt: int) -> float:
    return min(1.0 * (2 ** attempt) + random.uniform(0, 0.5), 30.0)


# ============================================================
# RobustAgent
# ============================================================
class RobustAgent:
    """健壮的对话 Agent"""

    def __init__(
        self,
        name: str = "小助手",
        system_prompt: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        self.name = name
        self.model = model or os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")
        self.max_retries = max_retries
        self.timeout = timeout

        self.system_prompt = system_prompt or (
            f"你是{name}，一个友善、有帮助的AI助手。回答简洁明了。"
        )
        self.history: list[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )

        self.total_tokens = 0
        self.total_cost = 0.0

    def run(self, user_input: str, stream: bool = True) -> str:
        """运行 Agent，自动处理重试和错误"""
        self.history.append({"role": "user", "content": user_input})

        try:
            reply = self._call_llm(stream=stream)
        except Exception as e:
            logger.error(f"LLM 调用最终失败: {e}")
            reply = "抱歉，我暂时无法处理你的请求。请稍后再试。"

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def _call_llm(self, stream: bool = True) -> str:
        """带重试的 LLM 调用"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if stream:
                    return self._streaming_call()
                else:
                    return self._non_streaming_call()
            except Exception as e:
                last_error = e
                if not is_retryable(e):
                    raise
                if attempt < self.max_retries:
                    delay = backoff(attempt)
                    logger.warning(f"重试 {attempt + 1}/{self.max_retries}, 等待 {delay:.1f}s")
                    time.sleep(delay)

        raise last_error

    def _non_streaming_call(self) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.7,
            timeout=self.timeout,
        )
        reply = resp.choices[0].message.content
        self._update_stats(resp.usage)
        return reply

    def _streaming_call(self) -> str:
        print(f"{self.name}: ", end="", flush=True)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.7,
            stream=True,
            timeout=self.timeout,
            stream_options={"include_usage": True},
        )

        full_reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_reply += delta.content
                print(delta.content, end="", flush=True)
            # 流式模式的 usage 在最后一个 chunk
            if hasattr(chunk, "usage") and chunk.usage:
                self._update_stats(chunk.usage)

        print()
        return full_reply

    def _update_stats(self, usage):
        if usage is None:
            return
        self.total_tokens += usage.total_tokens
        # GPT-4o-mini 定价
        cost = (usage.prompt_tokens * 0.15 + usage.completion_tokens * 0.60) / 1_000_000
        self.total_cost += cost
        logger.info(
            f"tokens: in={usage.prompt_tokens} out={usage.completion_tokens} "
            f"total={usage.total_tokens} | cost≈${cost:.6f}"
        )

    def stats(self) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "history_length": len(self.history),
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }

    def reset(self):
        self.history = [{"role": "system", "content": self.system_prompt}]


# ============================================================
# 交互式运行
# ============================================================
if __name__ == "__main__":
    agent = RobustAgent(name="小助手")

    print(f"\n{'='*50}")
    print(f"  {agent.name} 已上线！(健壮版)")
    print(f"  集成: 多轮对话 + 流式输出 + 自动重试")
    print(f"  输入 'quit' 退出, '/stats' 查看统计")
    print(f"{'='*50}\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "退出"):
            print(f"{agent.name}: 再见！")
            break
        if user_input == "/stats":
            stats = agent.stats()
            print(f"\n统计: {stats}\n")
            continue
        if user_input == "/reset":
            agent.reset()
            print("[历史已重置]\n")
            continue

        agent.run(user_input)
        print()
