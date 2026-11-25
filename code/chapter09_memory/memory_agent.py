"""
项目：带记忆的对话 Agent

整合记忆管理系统到对话 Agent 中：
- 自动从对话中提取重要信息并存储
- 回复前检索相关记忆
- 展示记忆如何增强对话质量
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from memory_manager import MemoryManager, MemoryType

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


class MemoryAgent:
    """带记忆的对话 Agent"""

    def __init__(self, name: str = "记忆助手"):
        self.name = name
        self.system_prompt = (
            f"你是{name}，一个细心的AI助手。\n"
            "你会记住用户告诉你的关键信息，并在后续对话中自然引用。\n"
            "回答简洁、有帮助。"
        )
        self.memory = MemoryManager()
        self.history: list[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.session_id = f"session_{id(self)}"

    def run(self, user_input: str) -> str:
        """处理用户输入并返回回复"""
        # 1. 检索相关记忆
        memories = self.memory.search(
            query=user_input,
            memory_types=[MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC],
            limit=5,
            min_importance=0.3,
        )

        # 2. 构建增强的系统提示（注入记忆上下文）
        memory_context = self._format_memories(memories)

        # 3. 调用 LLM
        messages = [self.history[0]]  # system prompt
        if memory_context:
            messages.append({
                "role": "system",
                "content": f"[相关记忆]\n{memory_context}",
            })
        messages.extend(self.history[1:])  # 对话历史
        messages.append({"role": "user", "content": user_input})

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content

        # 4. 更新对话历史
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": reply})

        # 5. 自动提取并存储记忆
        self._auto_remember(user_input, reply)

        return reply

    def _format_memories(self, memories) -> str:
        """格式化记忆列表为上下文字符串"""
        if not memories:
            return ""
        lines = []
        for mem in memories:
            type_label = {
                MemoryType.WORKING: "短期",
                MemoryType.EPISODIC: "事件",
                MemoryType.SEMANTIC: "知识",
            }.get(mem.memory_type, "其他")
            lines.append(f"[{type_label}] {mem.content}")
        return "\n".join(lines)

    def _auto_remember(self, user_input: str, reply: str):
        """
        自动从对话中提取关键信息并存储。
        使用 LLM 进行信息提取。
        """
        try:
            extract_resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "从以下对话中提取用户的关键个人信息。\n"
                            "以 JSON 格式返回，只包含你能确定的字段。\n"
                            "字段: name, interests, goals, preferences, other_facts\n"
                            "如果没有新信息，返回 {}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"用户: {user_input}\n助手: {reply}",
                    },
                ],
                temperature=0.0,
            )
            data = json.loads(extract_resp.choices[0].message.content)

            # 存储提取到的信息
            if "name" in data and data["name"]:
                self.memory.add(
                    f"用户名叫{data['name']}",
                    MemoryType.WORKING,
                    importance=0.9,
                    session_id=self.session_id,
                )
            if "interests" in data and data["interests"]:
                self.memory.add(
                    f"用户对{data['interests']}感兴趣",
                    MemoryType.WORKING,
                    importance=0.7,
                    session_id=self.session_id,
                )
            if "goals" in data and data["goals"]:
                self.memory.add(
                    f"用户的目标是{data['goals']}",
                    MemoryType.WORKING,
                    importance=0.8,
                    session_id=self.session_id,
                )
            if "preferences" in data and data["preferences"]:
                self.memory.add(
                    f"用户偏好{data['preferences']}",
                    MemoryType.WORKING,
                    importance=0.7,
                    session_id=self.session_id,
                )
            if "other_facts" in data and data["other_facts"]:
                # other_facts 可能是列表或字符串
                facts = data["other_facts"]
                if isinstance(facts, str):
                    facts = [facts]
                for fact in facts:
                    self.memory.add(
                        str(fact),
                        MemoryType.EPISODIC,
                        importance=0.6,
                        session_id=self.session_id,
                        event_type="extracted_fact",
                    )

            # 定期整合：将重要工作记忆提升为情景记忆
            self.memory.consolidate(
                MemoryType.WORKING,
                MemoryType.EPISODIC,
                importance_threshold=0.8,
            )

        except Exception:
            pass  # 记忆提取失败不影响主对话

    def stats(self) -> dict:
        return {
            "name": self.name,
            "history_length": len(self.history),
            "memory_stats": self.memory.stats(),
        }

    def reset_conversation(self):
        """重置对话（保留记忆）"""
        self.history = [{"role": "system", "content": self.system_prompt}]


# ============================================================
# 演示：对比有记忆 vs 无记忆
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  带记忆的 Agent 演示")
    print("=" * 60)

    agent = MemoryAgent(name="记忆助手")

    # 模拟多轮对话
    conversations = [
        "你好！我叫李华，我在上海工作。",
        "我最近在学 Python，目标是做数据分析。",
        "平时我喜欢跑步和看电影。",
        "根据我的情况，推荐一些学习资源吧。",
        "还记得我的工作和兴趣爱好吗？",
    ]

    for i, user_msg in enumerate(conversations, 1):
        print(f"\n👤 (第{i}轮): {user_msg}")
        reply = agent.run(user_msg)
        print(f"🤖: {reply[:120]}...")

    # 显示统计
    print(f"\n{'='*60}")
    stats = agent.stats()
    print(f"对话轮数: {len(agent.history) // 2}")
    print(f"记忆统计: {stats['memory_stats']}")

    # 检索所有关于用户的记忆
    print(f"\n所有用户相关记忆:")
    for item in agent.memory.search("李华 上海 Python 跑步", limit=10):
        print(f"  [{item.memory_type.value}] [{item.importance:.1f}] {item.content[:70]}")
