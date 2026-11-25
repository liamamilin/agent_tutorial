"""
Token 预算管理

学习目标：
1. 为不同类型的上下文分配 token 预算
2. 动态追踪预算使用
3. 超预算时发出警告
"""

import tiktoken
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TokenBudget:
    """Token 预算配置"""
    total: int = 8000                     # 总预算
    system: int = 1500                    # system prompt 预算
    memory: int = 1000                    # 记忆上下文预算
    knowledge: int = 2000                 # 知识上下文预算
    instruction: int = 500                # 指令预算
    history: int = 2500                   # 对话历史预算
    reserve: int = 500                    # 保留余量


class TokenBudgetManager:
    """Token 预算管理器"""

    def __init__(self, budget: TokenBudget = TokenBudget()):
        self.budget = budget
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.usage: Dict[str, int] = {k: 0 for k in ["system", "memory", "knowledge", "instruction", "history"]}
        self.warnings: List[str] = []

    def count(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def allocate(self, ctx_type: str, content: str) -> bool:
        """尝试分配 token 预算给一段内容，返回是否成功"""
        tokens_needed = self.count(content)
        budget_limit = getattr(self.budget, ctx_type, 0)
        current_used = self.usage.get(ctx_type, 0)

        if current_used + tokens_needed <= budget_limit:
            self.usage[ctx_type] += tokens_needed
            return True
        else:
            self.warnings.append(
                f"⚠️ [{ctx_type}] 预算不足: 需要 {tokens_needed}, "
                f"已用 {current_used}, 上限 {budget_limit}"
            )
            return False

    def allocate_with_overflow(self, ctx_type: str, content: str) -> int:
        """分配 token，返回实际使用的 token 数（可能被截断）"""
        tokens_needed = self.count(content)
        budget_limit = getattr(self.budget, ctx_type, 0)
        current_used = self.usage.get(ctx_type, 0)
        available = max(0, budget_limit - current_used)

        if tokens_needed <= available:
            self.usage[ctx_type] += tokens_needed
            return tokens_needed

        # 超预算但可以截断
        if available > 0:
            self.usage[ctx_type] += available
            self.warnings.append(
                f"⚠️ [{ctx_type}] 内容被截断: {tokens_needed} → {available} tokens"
            )
            return available

        self.warnings.append(f"❌ [{ctx_type}] 预算已耗尽")
        return 0

    def status(self) -> dict:
        """返回预算使用状态"""
        total_used = sum(self.usage.values())
        return {
            "total_budget": self.budget.total,
            "total_used": total_used,
            "usage_pct": round(total_used / self.budget.total * 100, 1),
            "by_type": dict(self.usage),
            "warnings": self.warnings,
        }

    def print_status(self):
        """打印预算使用状态"""
        s = self.status()
        print(f"\n{'='*50}")
        print(f"  Token 预算状态")
        print(f"{'='*50}")
        print(f"  总预算: {s['total_budget']}")
        print(f"  已使用: {s['total_used']} ({s['usage_pct']}%)")
        print(f"\n  各类型使用:")
        for ctx_type, used in s["by_type"].items():
            limit = getattr(self.budget, ctx_type, 0)
            pct = used / limit * 100 if limit > 0 else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            print(f"    {ctx_type:12s}: {used:5d}/{limit:5d} [{bar}] {pct:.0f}%")

        if s["warnings"]:
            print(f"\n  警告:")
            for w in s["warnings"]:
                print(f"    {w}")


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    # 自定义预算
    budget = TokenBudget(
        total=4000,
        system=1000,
        memory=500,
        knowledge=1500,
        instruction=300,
        history=500,
        reserve=200,
    )

    manager = TokenBudgetManager(budget)

    # 模拟分配
    manager.allocate_with_overflow("system", "你是一个AI助手。" * 30)
    manager.allocate_with_overflow("memory", "用户偏好... " * 20)
    manager.allocate_with_overflow("knowledge", "Python 知识库... " * 80)
    manager.allocate_with_overflow("instruction", "回答要简洁。" * 10)
    manager.allocate_with_overflow("history", "之前的对话... " * 30)

    # 尝试超出预算
    manager.allocate_with_overflow("history", "更多对话历史... " * 50)

    manager.print_status()
