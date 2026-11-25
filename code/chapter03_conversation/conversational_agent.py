"""
项目：完整对话 Agent 类

整合本章所有能力：
- 多轮对话历史管理
- System Prompt 设计
- Token 感知
- 历史截断
- 状态追踪（可选）

这是我们在添加"工具"之前的最终形态。
"""

import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ConversationalAgent:
    """完整的对话 Agent —— 拥有记忆、Token 感知和截断能力"""

    def __init__(
        self,
        name: str = "小助手",
        system_prompt: str | None = None,
        model: str | None = None,
        max_history_tokens: int = 8000,
    ):
        self.name = name
        self.model = model or os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")
        self.max_history_tokens = max_history_tokens

        # System Prompt
        if system_prompt is None:
            system_prompt = (
                f"你是{name}，一个友善、有帮助的AI助手。\n"
                "回答简洁明了，在适当的时候使用列表或分段。"
            )
        self.system_prompt = system_prompt

        # 对话历史
        self.history: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

        # LLM 客户端
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )

        # Token 编码器
        self.encoder = tiktoken.encoding_for_model("gpt-4o")

        # 统计
        self.total_tokens_used = 0
        self.turn_count = 0

    # ===== 核心 API =====

    def run(self, user_input: str) -> str:
        """接收用户输入，返回 Agent 回复"""
        self.turn_count += 1
        self.history.append({"role": "user", "content": user_input})

        # Token 感知截断
        self._auto_truncate()

        # 调用 LLM
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content

        # 统计
        if resp.usage:
            self.total_tokens_used += resp.usage.total_tokens

        self.history.append({"role": "assistant", "content": reply})
        return reply

    # ===== Token 管理 =====

    def count_tokens(self) -> int:
        """计算当前历史的 token 总数"""
        total = 0
        for msg in self.history:
            total += 4 + len(self.encoder.encode(msg["content"]))
        return total + 2

    def _auto_truncate(self):
        """自动截断：保留最近的消息，始终保留 system prompt"""
        while self.count_tokens() > self.max_history_tokens:
            # 至少有 system + 一对 user/assistant
            if len(self.history) <= 3:
                break
            # 删除最旧的一对（跳过 system）
            del self.history[1:3]

    # ===== 工具方法 =====

    def stats(self) -> dict:
        return {
            "name": self.name,
            "turns": self.turn_count,
            "history_length": len(self.history),
            "token_count": self.count_tokens(),
            "total_tokens_used": self.total_tokens_used,
        }

    def reset(self):
        """重置对话历史"""
        self.history = [{"role": "system", "content": self.system_prompt}]
        self.turn_count = 0

    def show_history(self):
        """打印对话历史概要"""
        print(f"\n{'='*50}")
        print(f"  对话历史（共 {self.turn_count} 轮）")
        print(f"{'='*50}")
        for msg in self.history[1:]:  # 跳过 system
            role_label = {"user": "👤 你", "assistant": f"🤖 {self.name}"}
            label = role_label.get(msg["role"], msg["role"])
            content = msg["content"][:100].replace("\n", " ")
            print(f"{label}: {content}")


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    agent = ConversationalAgent(
        name="知识助手",
        system_prompt=(
            "你是一个知识渊博的AI助手。\n"
            "规则：\n"
            "1. 先给出直接答案\n"
            "2. 再用 1-2 句补充细节\n"
            "3. 如果涉及不确定的信息，明确说明"
        ),
    )

    questions = [
        "为什么天空是蓝色的？",
        "那为什么日落时是红色的？",
        "这和光的波长有什么关系？",
    ]

    for q in questions:
        print(f"\n{'─'*40}")
        print(f"👤: {q}")
        answer = agent.run(q)
        print(f"🤖: {answer}")

    print(f"\n{'='*50}")
    stats = agent.stats()
    print(f"对话轮数: {stats['turns']}")
    print(f"历史消息数: {stats['history_length']}")
    print(f"当前 Token 数: {stats['token_count']}")
    print(f"累计 Token 消耗: {stats['total_tokens_used']}")
