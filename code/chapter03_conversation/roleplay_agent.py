"""
角色扮演 Agent

学习目标：
1. 设计一个带有鲜明人设的 Agent
2. 使用 System Prompt 定义行为和语气
3. 理解角色一致性在多轮对话中的挑战
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


class RoleplayAgent:
    """角色扮演 Agent —— 带人设的对话机器人"""

    def __init__(
        self,
        name: str,
        persona: str,
        tone_rules: str = "",
        boundaries: str = "",
    ):
        self.name = name
        self.history: list[dict] = []

        # 组装 System Prompt
        parts = [f"你是{name}。{persona}"]
        if tone_rules:
            parts.append(f"\n语气规则：{tone_rules}")
        if boundaries:
            parts.append(f"\n行为边界：{boundaries}")
        parts.append("\n始终保持角色一致性。不要跳出角色说'作为AI助手'之类的话。")

        self.system_prompt = "\n".join(parts)

        # 将 system 消息固定为历史的第一条
        self.history.append({"role": "system", "content": self.system_prompt})

    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        resp = client.chat.completions.create(
            model=MODEL,
            messages=self.history,
            temperature=0.8,  # 稍高温度让角色更生动
        )
        reply = resp.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def show_history(self):
        """展示对话历史（不含 system prompt 全文）"""
        for msg in self.history[1:]:  # 跳过 system prompt
            role_label = {"user": "👤", "assistant": f"🤖 {self.name}"}[msg["role"]]
            content = msg["content"][:80].replace("\n", " ")
            print(f"{role_label}: {content}...")


# ============================================================
# 测试：不同的角色设定
# ============================================================

# 角色 1：程序员导师
mentor = RoleplayAgent(
    name="老码农",
    persona="你是一个有 20 年经验的资深程序员，热爱用生活类比解释技术概念。",
    tone_rules="说话带点幽默，偶尔自嘲。喜欢用'你看啊'、'说白了就是'开头。",
    boundaries="只在编程和技术领域回答问题。如果被问其他问题，婉拒并引导回技术话题。",
)

# 角色 2：文学评论家
critic = RoleplayAgent(
    name="文学君",
    persona="你是一个饱读诗书的文学评论家，热爱古典文学和现代小说。",
    tone_rules="优雅、博学、偶尔引经据典。",
    boundaries="只讨论文学和阅读。拒绝回答与文学无关的问题。",
)


if __name__ == "__main__":
    print("=" * 50)
    print("  角色 1: 老码农")
    print("=" * 50)
    print(f"老码农: {mentor.chat('什么是递归？')}\n")
    print(f"老码农: {mentor.chat('再举个例子？')}\n")
    print(f"老码农: {mentor.chat('推荐一本小说')}\n")

    print("=" * 50)
    print("  角色 2: 文学君")
    print("=" * 50)
    print(f"文学君: {critic.chat('什么是递归？')}\n")
    print(f"文学君: {critic.chat('推荐一本小说')}\n")
