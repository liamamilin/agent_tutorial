"""
Token 计数与上下文窗口管理

学习目标：
1. 用 tiktoken 精确统计对话历史的 token 数
2. 理解上下文窗口限制
3. 在接近窗口限制时发出警告
"""

import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")

# GPT-4o-mini 上下文窗口: 128,000 tokens
CONTEXT_WINDOW = 128_000
WARNING_THRESHOLD = 0.8  # 达到 80% 时警告


def count_message_tokens(messages: list[dict], model: str = "gpt-4o") -> int:
    """精确计算一个 messages 列表的总 token 数"""
    encoder = tiktoken.encoding_for_model(model)
    total = 0
    for msg in messages:
        # 每条消息有固定开销（role + 分隔符）
        total += 4
        total += len(encoder.encode(msg["content"]))
    total += 2  # 回复的 priming
    return total


class TokenAwareAgent:
    """对 Token 有感知的对话 Agent"""

    def __init__(self, system_prompt: str, context_limit: int = CONTEXT_WINDOW):
        self.system_prompt = system_prompt
        self.context_limit = context_limit
        self.history: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def run(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        # 检查 token 数
        token_count = count_message_tokens(self.history)
        usage_pct = token_count / self.context_limit * 100

        print(f"[Token 用量: {token_count}/{self.context_limit} ({usage_pct:.1f}%)]")

        if usage_pct > WARNING_THRESHOLD * 100:
            print("⚠️ 警告：上下文窗口使用超过 80%，对话可能被截断！")

        resp = client.chat.completions.create(
            model=MODEL,
            messages=self.history,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply


if __name__ == "__main__":
    agent = TokenAwareAgent(system_prompt="你是一个友善的助手。回答简洁。")

    # 正常对话
    agent.run("你好！")

    # 模拟长对话：重复发送长文本
    long_text = "请分析以下内容：" + "人工智能正在改变世界。" * 200
    agent.run(long_text)

    # 再次对话
    agent.run("总结一下我们的对话。")
