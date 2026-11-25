"""
记忆管理器 (MemoryManager)

统一调度和协调工作记忆、情景记忆、语义记忆。
提供一致的API来操作不同类型的记忆。
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from working_memory import WorkingMemory
from episodic_memory import EpisodicMemory
from semantic_memory import SemanticMemory


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass
class MemoryItem:
    """统一的记忆项数据结构"""
    content: str
    memory_type: MemoryType
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class MemoryManager:
    """
    记忆管理器：统一调度所有记忆类型

    设计原则：
    - 统一接口：一致的 API 操作不同类型记忆
    - 智能路由：根据类型自动路由到合适的记忆系统
    - 跨类型搜索：支持跨多种记忆类型统一搜索
    - 生命周期管理：自动管理添加、整合、遗忘
    """

    def __init__(self):
        self.working = WorkingMemory(max_capacity=50, ttl_seconds=1800)
        self.episodic = EpisodicMemory(max_capacity=200)
        self.semantic = SemanticMemory(max_facts=200)

    # ===== 添加 =====

    def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.WORKING,
        importance: float = 0.5,
        session_id: Optional[str] = None,
        **metadata,
    ) -> None:
        """添加一条记忆到指定类型"""
        if memory_type == MemoryType.WORKING:
            self.working.add(content, importance)
        elif memory_type == MemoryType.EPISODIC:
            self.episodic.add(content, importance, session_id, **metadata)
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic.add(content, importance, **metadata)

    # ===== 搜索 =====

    def search(
        self,
        query: str,
        memory_types: Optional[list[MemoryType]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        session_id: Optional[str] = None,
    ) -> list[MemoryItem]:
        """
        跨类型搜索记忆。

        Args:
            query: 搜索查询
            memory_types: 要搜索的记忆类型，None 表示全部
            limit: 返回数量上限
            min_importance: 最低重要性阈值
        """
        if memory_types is None:
            memory_types = [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC]

        all_results = []

        for mtype in memory_types:
            if mtype == MemoryType.WORKING:
                items = self.working.search(query, limit=limit, min_importance=min_importance)
                all_results.extend([
                    self._to_memory_item(item, MemoryType.WORKING)
                    for item in items
                ])
            elif mtype == MemoryType.EPISODIC:
                items = self.episodic.search(query, limit=limit, min_importance=min_importance, session_id=session_id)
                all_results.extend([
                    self._to_memory_item(item, MemoryType.EPISODIC)
                    for item in items
                ])
            elif mtype == MemoryType.SEMANTIC:
                items = self.semantic.search(query, limit=limit, min_importance=min_importance)
                all_results.extend([
                    self._to_memory_item(item, MemoryType.SEMANTIC)
                    for item in items
                ])

        # 按重要性排序
        all_results.sort(key=lambda x: x.importance, reverse=True)
        return all_results[:limit]

    # ===== 整合（Consolidation）=====

    def consolidate(
        self,
        from_type: MemoryType,
        to_type: MemoryType,
        importance_threshold: float = 0.7,
    ) -> int:
        """
        将一种记忆类型中的高重要性记忆提升到另一种类型。
        例：工作记忆中重要的信息 → 情景记忆
            情景记忆中重要的信息 → 语义记忆
        """
        count = 0

        if from_type == MemoryType.WORKING and to_type == MemoryType.EPISODIC:
            for item in self.working._items:
                if item["importance"] >= importance_threshold:
                    self.episodic.add(
                        content=item["content"],
                        importance=item["importance"],
                        event_type="consolidated_from_working",
                    )
                    count += 1

        elif from_type == MemoryType.EPISODIC and to_type == MemoryType.SEMANTIC:
            for ep in self.episodic._episodes:
                if ep["importance"] >= importance_threshold:
                    self.semantic.add(
                        content=ep["content"],
                        importance=ep["importance"],
                        knowledge_type="consolidated_from_episodic",
                    )
                    count += 1

        return count

    # ===== 遗忘 =====

    def forget(
        self,
        strategy: str = "importance_based",
        threshold: float = 0.2,
        max_age_days: int = 30,
    ) -> int:
        """
        执行遗忘策略。

        Args:
            strategy: "importance_based" | "time_based" | "capacity_based"
            threshold: 重要性阈值（importance_based）或保留比例（capacity_based）
            max_age_days: 最大保留天数（time_based）
        """
        total_removed = 0

        if strategy == "importance_based":
            # 删除低重要性记忆
            for memory in [self.episodic, self.semantic]:
                if hasattr(memory, '_episodes'):
                    old = len(memory._episodes)
                    memory._episodes = [e for e in memory._episodes if e["importance"] >= threshold]
                    total_removed += old - len(memory._episodes)
                if hasattr(memory, '_facts'):
                    old = len(memory._facts)
                    memory._facts = [f for f in memory._facts if f["importance"] >= threshold]
                    total_removed += old - len(memory._facts)

        elif strategy == "time_based":
            cutoff = time.time() - max_age_days * 86400
            for memory in [self.episodic, self.semantic]:
                if hasattr(memory, '_episodes'):
                    old = len(memory._episodes)
                    memory._episodes = [e for e in memory._episodes if e["timestamp"] > cutoff]
                    total_removed += old - len(memory._episodes)
                if hasattr(memory, '_facts'):
                    old = len(memory._facts)
                    memory._facts = [f for f in memory._facts if f["timestamp"] > cutoff]
                    total_removed += old - len(memory._facts)

        elif strategy == "capacity_based":
            # 按容量比例保留最重要的
            keep_ratio = max(0.0, min(1.0, threshold))
            for memory in [self.episodic, self.semantic]:
                if hasattr(memory, '_episodes'):
                    items = memory._episodes
                    items.sort(key=lambda x: x["importance"], reverse=True)
                    keep_count = max(1, int(len(items) * keep_ratio))
                    total_removed += len(items) - keep_count
                    memory._episodes = items[:keep_count]
                if hasattr(memory, '_facts'):
                    items = memory._facts
                    items.sort(key=lambda x: x["importance"], reverse=True)
                    keep_count = max(1, int(len(items) * keep_ratio))
                    total_removed += len(items) - keep_count
                    memory._facts = items[:keep_count]

        return total_removed

    # ===== 工具方法 =====

    def stats(self) -> dict:
        return {
            "working": self.working.size(),
            "episodic": self.episodic.size(),
            "semantic": self.semantic.size(),
        }

    def _to_memory_item(self, raw: dict, mtype: MemoryType) -> MemoryItem:
        return MemoryItem(
            content=raw.get("content", ""),
            memory_type=mtype,
            importance=raw.get("importance", 0.5),
            timestamp=raw.get("timestamp", time.time()),
            session_id=raw.get("session_id"),
            metadata=raw.get("metadata", {}),
        )


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  记忆管理器 (MemoryManager) 演示")
    print("=" * 60)

    mm = MemoryManager()

    # 添加不同类型的记忆
    mm.add("用户刚问了 Python 函数的问题", MemoryType.WORKING, importance=0.6)
    mm.add("用户名叫小明", MemoryType.WORKING, importance=0.9)
    mm.add("今天天气是晴天", MemoryType.WORKING, importance=0.3)

    mm.add("小明完成了第一个 Python 项目", MemoryType.EPISODIC, importance=0.8,
           session_id="session_1", event_type="milestone")
    mm.add("小明询问了关于类的问题", MemoryType.EPISODIC, importance=0.6,
           session_id="session_1", event_type="question")

    mm.add("Python 是一种编程语言", MemoryType.SEMANTIC, importance=0.9)
    mm.add("Python 能用于数据科学", MemoryType.SEMANTIC, importance=0.8)

    print(f"\n记忆统计: {mm.stats()}")

    # 跨类型搜索
    print("\n--- 搜索 'Python'（全部类型）---")
    for item in mm.search("Python", limit=5):
        print(f"  [{item.memory_type.value}] [{item.importance:.1f}] {item.content[:60]}")

    print("\n--- 搜索 '小明'（全部类型）---")
    for item in mm.search("小明", limit=5):
        print(f"  [{item.memory_type.value}] [{item.importance:.1f}] {item.content[:60]}")

    # 整合
    consolidated = mm.consolidate(
        from_type=MemoryType.WORKING,
        to_type=MemoryType.EPISODIC,
        importance_threshold=0.7,
    )
    print(f"\n整合: {consolidated} 条工作记忆 → 情景记忆")

    # 遗忘
    removed = mm.forget(strategy="importance_based", threshold=0.4)
    print(f"遗忘（重要性<0.4）: {removed} 条")

    print(f"整合+遗忘后统计: {mm.stats()}")
