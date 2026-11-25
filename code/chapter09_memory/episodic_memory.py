"""
情景记忆 (EpisodicMemory)

特点：
- 存储具体事件和经历
- 保留时间序列关系
- 支持会话级检索
- 时间衰减评分公式

情景记忆就像人类的"昨天午餐吃了什么"——具体的、带时间标记的事件。
"""

import time
import math
from typing import Optional


class EpisodicMemory:
    """情景记忆：存储具体事件和经历"""

    def __init__(self, max_capacity: int = 200):
        self.max_capacity = max_capacity
        self._episodes: list[dict] = []

    def add(
        self,
        content: str,
        importance: float = 0.5,
        session_id: Optional[str] = None,
        event_type: str = "general",
        **metadata,
    ) -> None:
        """记录一个情景事件"""
        if len(self._episodes) >= self.max_capacity:
            # 驱逐最不重要且最旧的
            self._episodes.sort(key=lambda e: e["importance"])
            self._episodes = self._episodes[-(self.max_capacity - 1):]

        self._episodes.append({
            "content": content,
            "importance": max(0.0, min(1.0, importance)),
            "timestamp": time.time(),
            "session_id": session_id,
            "event_type": event_type,
            "metadata": metadata,
        })

    def search(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> list[dict]:
        """搜索情景记忆"""
        scored = []
        q_words = set(query.lower().split()) if query else set()

        for ep in self._episodes:
            if ep["importance"] < min_importance:
                continue
            if session_id and ep["session_id"] != session_id:
                continue
            if event_type and ep["event_type"] != event_type:
                continue

            # 关键词匹配度
            ep_words = set(ep["content"].lower().split())
            if q_words:
                keyword_score = len(q_words & ep_words) / max(len(q_words), 1)
            else:
                keyword_score = 1.0

            # 时间近因性（越新越相关）
            age_hours = (time.time() - ep["timestamp"]) / 3600
            recency = math.exp(-age_hours / 168)  # 半衰期：7天

            # 综合评分
            score = (keyword_score * 0.7 + recency * 0.3) * (0.5 + ep["importance"] * 0.5)
            scored.append((ep, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [ep for ep, _ in scored[:limit]]

    def get_by_session(self, session_id: str, limit: int = 50) -> list[dict]:
        """按会话ID获取所有事件"""
        episodes = [ep for ep in self._episodes if ep["session_id"] == session_id]
        episodes.sort(key=lambda e: e["timestamp"])
        return episodes[:limit]

    def get_recent(self, n: int = 10) -> list[dict]:
        """获取最近 N 条记录"""
        sorted_eps = sorted(self._episodes, key=lambda e: e["timestamp"], reverse=True)
        return sorted_eps[:n]

    def size(self) -> int:
        return len(self._episodes)


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  情景记忆 (EpisodicMemory) 演示")
    print("=" * 60)

    em = EpisodicMemory(max_capacity=100)

    # 模拟对话中的事件
    em.add("用户询问了 Python 函数定义", importance=0.6,
           session_id="session_1", event_type="question")
    em.add("助手解释了函数定义并给出示例", importance=0.5,
           session_id="session_1", event_type="answer")
    em.add("用户表示理解了，继续问类", importance=0.7,
           session_id="session_1", event_type="feedback")
    em.add("助手讲解了 Python 类的基础", importance=0.6,
           session_id="session_1", event_type="answer")
    em.add("用户完成了第一个 Python 项目", importance=0.9,
           session_id="session_2", event_type="milestone")

    print(f"\n总事件数: {em.size()}")

    # 按会话检索
    print("\n--- session_1 的所有事件 ---")
    for ep in em.get_by_session("session_1"):
        print(f"  [{ep['event_type']}] {ep['content']}")

    # 搜索
    print("\n--- 搜索 'Python' ---")
    for ep in em.search("Python 函数", limit=3):
        print(f"  [{ep['importance']:.1f}] {ep['content']}")

    # 最近事件
    print("\n--- 最近 3 条 ---")
    for ep in em.get_recent(3):
        print(f"  [{ep['event_type']}] {ep['content']}")
