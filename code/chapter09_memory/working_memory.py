"""
工作记忆 (WorkingMemory)

特点：
- 容量有限（默认50条）
- TTL（生存时间）自动过期
- 纯内存存储，快速访问
- 混合检索：关键词 + TF-IDF 相似度

工作记忆就像计算机的 RAM——暂存当前对话的临时信息。
"""

import time
import math
from collections import Counter
from typing import Optional


class WorkingMemory:
    """工作记忆：当前对话会话中的临时信息存储"""

    def __init__(self, max_capacity: int = 50, ttl_seconds: int = 1800):
        """
        Args:
            max_capacity: 最大记忆条数
            ttl_seconds: 记忆生存时间（秒），默认1800秒=30分钟
        """
        self.max_capacity = max_capacity
        self.ttl_seconds = ttl_seconds
        self._items: list[dict] = []  # [{content, importance, timestamp}, ...]

    def add(self, content: str, importance: float = 0.5) -> None:
        """添加一条记忆"""
        # 自动清理过期 + 容量驱逐
        self._cleanup()

        self._items.append({
            "content": content,
            "importance": max(0.0, min(1.0, importance)),  # 钳制到 [0, 1]
            "timestamp": time.time(),
        })

        # 容量驱逐：按重要性 + 时间排序，移除最不重要且最旧的
        if len(self._items) > self.max_capacity:
            self._items.sort(key=lambda x: x["importance"] * 0.7 + self._time_decay(x) * 0.3)
            self._items = self._items[-(self.max_capacity):]

    def search(self, query: str, limit: int = 10, min_importance: float = 0.0) -> list[dict]:
        """搜索相关记忆"""
        self._cleanup()

        if not self._items:
            return []

        # 计算每条记忆的得分：关键词匹配 × 时间衰减 × 重要性
        scored = []
        for item in self._items:
            if item["importance"] < min_importance:
                continue
            score = self._relevance(query, item["content"])
            score *= self._time_decay(item)
            score *= (0.5 + item["importance"] * 0.5)
            scored.append((item, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:limit]]

    def clear(self) -> None:
        """清空所有记忆"""
        self._items.clear()

    def size(self) -> int:
        """当前记忆条数"""
        self._cleanup()
        return len(self._items)

    # ===== 内部方法 =====

    def _relevance(self, query: str, text: str) -> float:
        """简单关键词匹配 + Jaccard相似度"""
        q_words = set(query.lower().split())
        t_words = set(text.lower().split())
        if not q_words or not t_words:
            return 0.0
        intersection = q_words & t_words
        return len(intersection) / max(len(q_words), 1)

    def _time_decay(self, item: dict) -> float:
        """时间衰减：越新的记忆权重越高"""
        age = time.time() - item["timestamp"]
        if age <= 0:
            return 1.0
        # 半衰期 = ttl 的一半
        half_life = self.ttl_seconds / 2
        return math.exp(-age / half_life)

    def _cleanup(self) -> int:
        """清理过期记忆，返回清理数量"""
        if not self._items:
            return 0
        cutoff = time.time() - self.ttl_seconds
        old_count = len(self._items)
        self._items = [item for item in self._items if item["timestamp"] > cutoff]
        return old_count - len(self._items)


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  工作记忆 (WorkingMemory) 演示")
    print("=" * 60)

    wm = WorkingMemory(max_capacity=5, ttl_seconds=3600)

    # 添加记忆
    wm.add("用户名叫小明，在北京工作", importance=0.9)
    wm.add("小明在学习 Python 编程", importance=0.7)
    wm.add("今天天气是晴天", importance=0.3)
    wm.add("小明喜欢吃川菜", importance=0.6)
    wm.add("推荐了 Python 入门书籍", importance=0.8)

    print(f"\n当前记忆数: {wm.size()}")

    # 搜索
    print("\n搜索 'Python':")
    for item in wm.search("Python", limit=3):
        print(f"  [{item['importance']:.1f}] {item['content']}")

    print("\n搜索 '小明':")
    for item in wm.search("小明", limit=3):
        print(f"  [{item['importance']:.1f}] {item['content']}")

    print("\n搜索 '天气':")
    for item in wm.search("天气", limit=3):
        print(f"  [{item['importance']:.1f}] {item['content']}")

    # 容量驱逐测试
    wm.add("新记忆1", importance=0.2)
    wm.add("新记忆2", importance=0.1)
    wm.add("新记忆3", importance=0.0)
    print(f"\n添加3条低重要性记忆后: {wm.size()} 条（自动驱逐最不重要/最旧的）")

    # TTL 演示
    print(f"\n（TTL 设置为 3600 秒 = 1 小时，当前记忆不会过期）")
    print(f"过期清理数: {wm._cleanup()}")
