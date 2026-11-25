"""
日志系统

学习目标：
1. 记录每次 API 调用的详细信息
2. 追踪耗时和 Token 消耗
3. 为调试和成本分析提供数据
"""

import os
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 配置日志
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),           # 控制台输出
        logging.FileHandler("agent.log"),  # 文件持久化
    ],
)

logger = logging.getLogger("Agent")


class LoggedLLMClient:
    """带日志记录的 LLM 客户端"""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )
        self.call_count = 0
        self.total_cost = 0.0

    def chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        self.call_count += 1
        call_id = self.call_count

        # 日志：请求开始
        user_msg = messages[-1]["content"][:50].replace("\n", " ")
        logger.info(f"[Call #{call_id}] 请求: \"{user_msg}...\" | model={self.model} | temp={temperature}")

        start = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"[Call #{call_id}] 失败: {type(e).__name__} | 耗时={elapsed:.2f}s")
            raise

        elapsed = time.time() - start
        reply = resp.choices[0].message.content

        # Token 统计
        if resp.usage:
            prompt_tokens = resp.usage.prompt_tokens
            completion_tokens = resp.usage.completion_tokens
            total_tokens = resp.usage.total_tokens

            # 费用估算（GPT-4o-mini 价格，仅供参考）
            cost = (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000
            self.total_cost += cost

            logger.info(
                f"[Call #{call_id}] 成功 | "
                f"耗时={elapsed:.2f}s | "
                f"tokens: in={prompt_tokens} out={completion_tokens} total={total_tokens} | "
                f"费用≈${cost:.6f}"
            )
        else:
            logger.info(f"[Call #{call_id}] 成功 | 耗时={elapsed:.2f}s (无 usage 信息)")

        return reply

    def stats(self):
        """打印累计统计"""
        logger.info("=" * 40)
        logger.info(f"累计调用: {self.call_count} 次")
        logger.info(f"累计费用: ${self.total_cost:.6f}")
        logger.info("=" * 40)


if __name__ == "__main__":
    llm = LoggedLLMClient()

    print("（日志同步输出到 agent.log 文件）\n")

    reply = llm.chat([{"role": "user", "content": "什么是 API？一句话回答。"}])
    print(f"回复: {reply}\n")

    reply = llm.chat([{"role": "user", "content": "1+1 等于几？"}])
    print(f"回复: {reply}\n")

    llm.stats()
