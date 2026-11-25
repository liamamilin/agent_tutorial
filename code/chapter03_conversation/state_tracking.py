"""
对话状态追踪 —— 让 Agent 记住用户偏好

学习目标：
1. 从对话中提取关键信息
2. 使用简单的结构化状态存储
3. 在回答中利用状态信息
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


class StatefulAgent:
    """带状态追踪的对话 Agent"""

    def __init__(self, name: str):
        self.name = name
        # 状态字典：在对话中逐步积累
        self.state: dict[str, str] = {}
        self.history: list[dict] = [
            {
                "role": "system",
                "content": (
                    f"你是{name}，一个细心的AI助手。\n"
                    "从对话中提取用户的关键信息（名字、偏好、目标等），"
                    "在后续回答中自然引用这些信息。\n"
                    "如果用户提到新的个人信息，主动确认并记录。"
                ),
            }
        ]

    def _extract_state(self, user_input: str, reply: str) -> dict:
        """用 LLM 从对话中提取状态信息"""
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "从以下对话中提取用户的关键信息。\n"
                        "以 JSON 格式返回，只包含你能确定的字段。\n"
                        "可用字段: name, city, job, hobby, goal, language\n"
                        "示例: {\"name\": \"小明\", \"city\": \"北京\"}"
                    ),
                },
                {"role": "user", "content": f"用户: {user_input}\n助手: {reply}"},
            ],
            temperature=0.0,
        )
        import json
        try:
            return json.loads(resp.choices[0].message.content)
        except json.JSONDecodeError:
            return {}

    def run(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        resp = client.chat.completions.create(
            model=MODEL,
            messages=self.history,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})

        # 提取状态
        extracted = self._extract_state(user_input, reply)
        self.state.update(extracted)

        return reply

    def get_state(self) -> dict:
        return dict(self.state)


if __name__ == "__main__":
    agent = StatefulAgent(name="细心助手")

    print("=" * 50)
    print("  状态追踪 Agent 演示")
    print("=" * 50)

    print(f"\n👤: 你好！我叫小明，我在北京工作。")
    print(f"🤖: {agent.run('你好！我叫小明，我在北京工作。')}")

    print(f"\n👤: 我最近在学 Python，目标是做一个网页应用。")
    print(f"🤖: {agent.run('我最近在学 Python，目标是做一个网页应用。')}")

    print(f"\n👤: 根据我的情况，推荐一个学习路线吧。")
    print(f"🤖: {agent.run('根据我的情况，推荐一个学习路线吧。')}")

    print(f"\n{'='*50}")
    print("提取的用户状态:")
    for key, value in agent.get_state().items():
        print(f"  {key}: {value}")
