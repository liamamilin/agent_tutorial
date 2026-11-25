"""
上下文组装策略

学习目标：
1. 理解不同类型的上下文（system、memory、knowledge、instruction、history）
2. 实现优先级驱动的上下文组装
3. 实现分层上下文组装
4. 实现基于查询的动态上下文选择
"""

import os
import tiktoken
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Literal

# ============================================================
# 数据结构
# ============================================================

ContextType = Literal["system", "memory", "knowledge", "instruction", "history"]


@dataclass
class ContextItem:
    """上下文项"""
    content: str
    ctx_type: ContextType
    priority: float = 0.5  # 0.0-1.0，越高越重要
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def token_count(self, encoder) -> int:
        return len(encoder.encode(self.content))


# ============================================================
# 上下文组装器
# ============================================================

class ContextAssembler:
    """上下文组装器：按多种策略组装上下文"""

    def __init__(self, token_budget: int = 4000):
        self.token_budget = token_budget
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.items: List[ContextItem] = []

    def add(self, item: ContextItem):
        """添加上下文项"""
        self.items.append(item)

    def add_system(self, content: str, priority: float = 1.0):
        self.add(ContextItem(content, "system", priority))

    def add_memory(self, content: str, priority: float = 0.7):
        self.add(ContextItem(content, "memory", priority))

    def add_knowledge(self, content: str, priority: float = 0.8):
        self.add(ContextItem(content, "knowledge", priority))

    def add_instruction(self, content: str, priority: float = 0.9):
        self.add(ContextItem(content, "instruction", priority))

    def add_history(self, content: str, priority: float = 0.6):
        self.add(ContextItem(content, "history", priority))

    # ---- 策略 1: 基于优先级组装 ----

    def assemble_by_priority(self, query: str = "") -> List[ContextItem]:
        """按优先级从高到低组装，直到 token 预算耗尽"""
        sorted_items = sorted(self.items, key=lambda x: x.priority, reverse=True)
        return self._fit_budget(sorted_items)

    # ---- 策略 2: 分层组装 ----

    def assemble_layered(self) -> List[ContextItem]:
        """分层组装：核心 → 可选 → 背景"""
        result: List[ContextItem] = []

        # 第一层：核心上下文（priority >= 0.8）
        core = [it for it in self.items if it.priority >= 0.8]
        result = self._fit_budget(core)

        # 第二层：可选上下文（0.5 <= priority < 0.8）
        used_tokens = sum(it.token_count(self.encoder) for it in result)
        remaining = self.token_budget - used_tokens
        if remaining > 0:
            optional = [it for it in self.items if 0.5 <= it.priority < 0.8]
            for it in sorted(optional, key=lambda x: x.priority, reverse=True):
                tc = it.token_count(self.encoder)
                if tc <= remaining:
                    result.append(it)
                    remaining -= tc

        # 第三层：背景上下文（priority < 0.5）
        if remaining > 0:
            background = [it for it in self.items if it.priority < 0.5]
            for it in background:
                tc = it.token_count(self.encoder)
                if tc <= remaining:
                    result.append(it)
                    remaining -= tc

        return result

    # ---- 策略 3: 动态选择 ----

    def assemble_dynamic(self, query: str) -> List[ContextItem]:
        """根据查询关键词动态选择上下文类型"""
        query_lower = query.lower()

        # 定义关键词 → 上下文类型映射
        type_triggers = {
            "memory": ["记得", "以前", "上次", "历史", "过去"],
            "knowledge": ["什么是", "解释", "定义", "原理", "为什么"],
            "instruction": ["怎么做", "步骤", "方法", "流程"],
        }

        # 确定需要的类型
        needed_types: set[ContextType] = {"system"}  # system 始终需要
        for ctx_type, keywords in type_triggers.items():
            if any(kw in query_lower for kw in keywords):
                needed_types.add(ctx_type)  # type: ignore

        # 筛选匹配类型的项
        candidates = [it for it in self.items if it.ctx_type in needed_types]

        # 按优先级排序
        sorted_items = sorted(candidates, key=lambda x: x.priority, reverse=True)
        return self._fit_budget(sorted_items)

    # ---- 工具方法 ----

    def _fit_budget(self, items: List[ContextItem]) -> List[ContextItem]:
        """在 token 预算内选择尽可能多的项"""
        result = []
        total = 0
        for item in items:
            tc = item.token_count(self.encoder)
            if total + tc <= self.token_budget:
                result.append(item)
                total += tc
            else:
                break
        return result

    def token_usage(self, items: List[ContextItem]) -> int:
        return sum(it.token_count(self.encoder) for it in items)

    def to_messages(self, items: List[ContextItem]) -> list[dict]:
        """转换为 OpenAI messages 格式"""
        # 角色映射
        role_map = {
            "system": "system",
            "instruction": "system",
            "knowledge": "system",
            "memory": "user",
            "history": "user",
        }
        return [{"role": role_map[it.ctx_type], "content": it.content} for it in items]


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    assembler = ContextAssembler(token_budget=500)

    # 添加各种上下文
    assembler.add_system("你是一个智能学习助手。", priority=1.0)
    assembler.add_instruction("回答要简洁、准确、有步骤。", priority=0.9)
    assembler.add_knowledge("Python 是一种解释型编程语言。", priority=0.8)
    assembler.add_knowledge("Python 由 Guido van Rossum 于 1991 年创建。", priority=0.7)
    assembler.add_memory("用户小明昨天问过 Python 的基础语法。", priority=0.7)
    assembler.add_memory("小明的学习目标是 Web 开发。", priority=0.6)
    assembler.add_history("用户：我想学 Python。助手：Python 是个好选择！", priority=0.5)

    print("=" * 60)
    print("  策略 1: 优先级组装")
    print("=" * 60)
    result1 = assembler.assemble_by_priority()
    for item in result1:
        print(f"  [{item.ctx_type}] p={item.priority:.1f} | {item.content[:50]}...")
    print(f"  总 Token: {assembler.token_usage(result1)}")

    print(f"\n{'='*60}")
    print("  策略 2: 分层组装")
    print(f"{'='*60}")
    result2 = assembler.assemble_layered()
    for item in result2:
        print(f"  [{item.ctx_type}] p={item.priority:.1f} | {item.content[:50]}...")
    print(f"  总 Token: {assembler.token_usage(result2)}")

    print(f"\n{'='*60}")
    print("  策略 3: 动态选择（查询='什么是 Python'）")
    print(f"{'='*60}")
    result3 = assembler.assemble_dynamic("什么是 Python？")
    for item in result3:
        print(f"  [{item.ctx_type}] p={item.priority:.1f} | {item.content[:50]}...")
    print(f"  总 Token: {assembler.token_usage(result3)}")

    print(f"\n{'='*60}")
    print("  三种策略对比")
    print(f"{'='*60}")
    print(f"  优先级: {assembler.token_usage(result1)} tokens")
    print(f"  分层:   {assembler.token_usage(result2)} tokens")
    print(f"  动态:   {assembler.token_usage(result3)} tokens")
