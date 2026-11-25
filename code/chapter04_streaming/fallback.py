"""
优雅降级策略

学习目标：
1. 实现多级 fallback
2. 主模型不可用时切换到备选模型
3. LLM 不可用时返回本地缓存/静态回复
"""

import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)


# ============================================================
# Fallback 级别定义
# ============================================================

# 常见问题的本地缓存回复（零成本、零延迟）
LOCAL_CACHE = {
    "你好": "你好！有什么可以帮你的？",
    "再见": "再见！祝你愉快！",
    "谢谢": "不客气！",
    "你叫什么": "我叫小助手，是你的 AI 伙伴。",
}


class RobustLLMClient:
    """带降级策略的 LLM 客户端"""

    def __init__(self):
        # 主模型
        self.primary_model = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")
        # 备选模型（更便宜、更稳定，用于降级）
        self.fallback_model = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")  # 同一模型的不同超参也可
        self.client = client

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> tuple[str, str]:  # (回复, 使用的策略)
        """
        按优先级尝试：
        1. 本地缓存
        2. 主模型
        3. 备选模型
        4. 静态降级回复
        """

        user_msg = messages[-1]["content"].strip()

        # ---- Level 1: 本地缓存 ----
        for key, reply in LOCAL_CACHE.items():
            if key in user_msg:
                return reply, "cache"

        # ---- Level 2: 主模型 ----
        try:
            resp = self.client.chat.completions.create(
                model=self.primary_model,
                messages=messages,
                temperature=temperature,
                timeout=15.0,
            )
            return resp.choices[0].message.content, "primary"
        except Exception as e:
            print(f"[Fallback] 主模型失败 ({type(e).__name__}), 尝试备选...")

        # ---- Level 3: 备选模型 ----
        try:
            resp = self.client.chat.completions.create(
                model=self.fallback_model,
                messages=messages,
                temperature=temperature,
                timeout=15.0,
            )
            return resp.choices[0].message.content, "fallback_model"
        except Exception as e:
            print(f"[Fallback] 备选模型也失败 ({type(e).__name__})")

        # ---- Level 4: 静态降级 ----
        return "抱歉，服务暂时不可用。请稍后再试。", "static"


if __name__ == "__main__":
    llm = RobustLLMClient()

    # 测试缓存命中
    reply, strategy = llm.chat([{"role": "user", "content": "你好！"}])
    print(f"[{strategy}] {reply}")

    # 测试正常调用
    reply, strategy = llm.chat([{"role": "user", "content": "解释一下什么是机器学习。"}])
    print(f"[{strategy}] {reply[:80]}...")
