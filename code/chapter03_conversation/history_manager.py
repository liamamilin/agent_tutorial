"""
多轮对话历史管理

学习目标：
1. 实现对话历史存储
2. 理解为什么每次请求要发送完整历史
3. 观察历史长度对回答的影响
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


class ConversationalAgent:
    """带对话历史的 Agent —— 真正"记住"上下文"""

    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        default_prompt = f"你是{name}，一个友善的AI助手。回答简洁、有帮助。"
        self.system_prompt = system_prompt or default_prompt
        # 历史用 dict 列表存储，第一项是 system 消息
        self.history: list[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]

    def run(self, user_input: str) -> str:
        # 1. 将用户输入加入历史
        self.history.append({"role": "user", "content": user_input})

        # 2. 将完整历史发送给模型
        resp = client.chat.completions.create(
            model=MODEL,
            messages=self.history,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content

        # 3. 将助手回复也加入历史
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def show_stats(self):
        """显示对话统计"""
        msgs = self.history[1:]  # 不含 system
        user_msgs = [m for m in msgs if m["role"] == "user"]
        print(f"\n对话统计: {len(user_msgs)} 轮, 共 {len(msgs)} 条消息")


# ============================================================
# 对比实验：有历史 vs 无历史
# ============================================================

# --- 无历史版本（每轮独立调用） ---
def call_without_history(user_input: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个友善的AI助手。"},
            {"role": "user", "content": user_input},
        ],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    print("=" * 60)
    print("  实验: 有历史 vs 无历史")
    print("=" * 60)

    # ---- 无历史 ----
    print("\n--- 无历史版本 ---")
    print(f"Q1: 我叫小明")
    print(f"A1: {call_without_history('我叫小明')}")
    print(f"Q2: 我叫什么名字？")
    print(f"A2: {call_without_history('我叫什么名字？')}")
    print("结果: 模型不记得你的名字 ❌")

    # ---- 有历史 ----
    print("\n--- 有历史版本 ---")
    agent = ConversationalAgent(name="小助手")
    print(f"Q1: 我叫小明")
    print(f"A1: {agent.run('我叫小明')}")
    print(f"Q2: 我叫什么名字？")
    print(f"A2: {agent.run('我叫什么名字？')}")
    print("结果: 模型记住了你的名字 ✅")
    agent.show_stats()
