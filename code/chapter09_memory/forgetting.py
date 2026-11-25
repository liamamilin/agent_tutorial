"""
遗忘策略演示

三种核心遗忘策略：
1. 基于重要性：删除低于阈值的记忆
2. 基于时间：删除超过 N 天的记忆
3. 基于容量：保留最重要的 N%
"""

import time
from memory_manager import MemoryManager, MemoryType


def demo_forgetting():
    """演示三种遗忘策略"""

    # ============================================================
    # 准备测试数据
    # ============================================================
    def create_test_memories(mm: MemoryManager):
        """创建一组测试记忆（不同重要性、不同时间）"""
        # 高重要性
        mm.add("用户名叫张三", MemoryType.EPISODIC, importance=0.9)
        mm.add("张三学习 Python 3 个月了", MemoryType.EPISODIC, importance=0.8)
        mm.add("Python是编程语言", MemoryType.SEMANTIC, importance=0.95)

        # 中等重要性
        mm.add("张三问了关于函数的问题", MemoryType.EPISODIC, importance=0.5)
        mm.add("张三对机器学习感兴趣", MemoryType.EPISODIC, importance=0.6)

        # 低重要性
        mm.add("今天天气不错", MemoryType.EPISODIC, importance=0.1)
        mm.add("张三喝了咖啡", MemoryType.EPISODIC, importance=0.15)
        mm.add("临时笔记", MemoryType.SEMANTIC, importance=0.05)

        # 手动调整最早的两条时间戳（模拟旧记忆）
        old_time = time.time() - 40 * 86400  # 40天前
        if mm.episodic._episodes:
            mm.episodic._episodes[0]["timestamp"] = old_time
            mm.episodic._episodes[1]["timestamp"] = old_time + 86400

    # ============================================================
    # 策略 1: 基于重要性
    # ============================================================
    print("=" * 60)
    print("  策略 1: 基于重要性的遗忘")
    print("=" * 60)

    mm1 = MemoryManager()
    create_test_memories(mm1)
    print(f"遗忘前: {mm1.stats()}")
    removed = mm1.forget(strategy="importance_based", threshold=0.2)
    print(f"移除了 {removed} 条（重要性 < 0.2）")
    print(f"遗忘后: {mm1.stats()}")

    # ============================================================
    # 策略 2: 基于时间
    # ============================================================
    print("\n" + "=" * 60)
    print("  策略 2: 基于时间的遗忘")
    print("=" * 60)

    mm2 = MemoryManager()
    create_test_memories(mm2)
    print(f"遗忘前: {mm2.stats()}")
    removed = mm2.forget(strategy="time_based", max_age_days=30)
    print(f"移除了 {removed} 条（超过 30 天）")
    print(f"遗忘后: {mm2.stats()}")

    # ============================================================
    # 策略 3: 基于容量
    # ============================================================
    print("\n" + "=" * 60)
    print("  策略 3: 基于容量的遗忘")
    print("=" * 60)

    mm3 = MemoryManager()
    create_test_memories(mm3)
    print(f"遗忘前: {mm3.stats()}")
    removed = mm3.forget(strategy="capacity_based", threshold=0.5)  # 保留50%
    print(f"移除了 {removed} 条（只保留最重要的 50%）")
    print(f"遗忘后: {mm3.stats()}")


if __name__ == "__main__":
    demo_forgetting()
