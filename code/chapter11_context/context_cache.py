"""
上下文缓存

学习目标：
1. 缓存组装好的上下文，避免重复计算
2. LRU 淘汰策略
3. 缓存命中率统计
"""

from collections import OrderedDict
from typing import List, Optional
from context_assembler import ContextItem


class ContextCache:
    """简单的上下文缓存（LRU）"""

    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self._cache: OrderedDict[str, List[ContextItem]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _make_key(self, query: str, strategy: str) -> str:
        """生成缓存键"""
        # 取 query 的前 50 个字符 + 策略名
        prefix = query[:50].strip().lower()
        return f"{strategy}:{prefix}"

    def get(self, query: str, strategy: str) -> Optional[List[ContextItem]]:
        """获取缓存"""
        key = self._make_key(query, strategy)
        if key in self._cache:
            # LRU: 移到末尾
            self._cache.move_to_end(key)
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def set(self, query: str, strategy: str, items: List[ContextItem]):
        """设置缓存"""
        key = self._make_key(query, strategy)

        # 如果已存在，先删除（更新）
        if key in self._cache:
            del self._cache[key]

        # 如果缓存已满，淘汰最旧的
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # FIFO 淘汰

        self._cache[key] = items

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    @property
    def size(self) -> int:
        return len(self._cache)


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    from context_assembler import ContextAssembler

    cache = ContextCache(max_size=5)
    assembler = ContextAssembler(token_budget=500)
    assembler.add_system("你是AI助手。", 1.0)
    assembler.add_knowledge("Python 是一种编程语言。", 0.8)

    # 模拟多次查询
    queries = [
        "什么是 Python？",
        "什么是 Python？",     # 重复 → 缓存命中
        "Python 的特点？",
        "什么是 Python？",     # 重复 → 缓存命中
        "如何学习 Python？",
        "Python 的历史？",
        "什么是 Python？",     # 重复 → 缓存命中
    ]

    print("=" * 60)
    print("  上下文缓存演示（LRU）")
    print("=" * 60)

    for query in queries:
        strategy = "priority"
        cached = cache.get(query, strategy)

        if cached:
            print(f"  ✅ 缓存命中: \"{query}\"")
        else:
            print(f"  ❌ 缓存未命中: \"{query}\" → 计算并缓存")
            result = assembler.assemble_by_priority(query)
            cache.set(query, strategy, result)

    print(f"\n{'='*60}")
    print(f"  缓存统计")
    print(f"{'='*60}")
    print(f"  命中数: {cache.hits}")
    print(f"  未命中: {cache.misses}")
    print(f"  命中率: {cache.hit_rate:.1%}")
    print(f"  缓存大小: {cache.size}/{cache.max_size}")
