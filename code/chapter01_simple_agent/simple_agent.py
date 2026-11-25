"""
第 1 章：认识智能体 — 最简对话 Agent

使用方式：
    python simple_agent.py

依赖：openai, python-dotenv
配置：在 code/ 目录下创建 .env 文件（参考 .env.example）
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# 从 code/ 目录加载 .env
load_dotenv()


class SimpleAgent:
    """最简 Agent：能对话、能记住历史"""

    def __init__(self, name: str, system_prompt: str = "你是一个有用的AI助手。"):
        self.name = name
        self.system_prompt = system_prompt
        self.history: list[dict] = []

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )
        self.model = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")

    def run(self, user_input: str) -> str:
        # 1. 将用户输入加入历史
        self.history.append({"role": "user", "content": user_input})

        # 2. 构建完整消息
        messages = [{"role": "system", "content": self.system_prompt}] + self.history

        # 3. 调用 LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        # 4. 提取回复并加入历史
        reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def get_history(self) -> list[dict]:
        return self.history


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    agent = SimpleAgent(name="小助手")

    print("=" * 50)
    print("Agent:", agent.run("你好，我叫小明。"))
    print()
    print("Agent:", agent.run("还记得我叫什么吗？"))
    print("=" * 50)
    print(f"对话历史共 {len(agent.get_history())} 条消息")
