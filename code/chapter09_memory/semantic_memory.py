"""
语义记忆 (SemanticMemory)

特点：
- 存储抽象概念、知识和关系
- 知识图谱结构（实体—关系—值）
- 从文本中自动提取实体
- 图检索 + 关键词混合搜索

语义记忆就像人类的"巴黎是法国首都"——不依赖于特定时间地点的知识。
"""

import time
from collections import defaultdict


class SemanticMemory:
    """语义记忆：抽象知识和概念关系"""

    def __init__(self, max_facts: int = 200):
        self.max_facts = max_facts
        self._facts: list[dict] = []       # [{subject, relation, value, importance, timestamp}]
        self._entities: dict[str, set] = defaultdict(set)  # entity → {related_entity_1, ...}

    def add(
        self,
        content: str,
        importance: float = 0.5,
        knowledge_type: str = "factual",
        **metadata,
    ) -> None:
        """
        添加一条语义知识。
        自动尝试提取 (subject, relation, value) 三元组。
        """
        # 简单三元组提取
        triples = self._extract_triples(content)

        if not triples:
            # 无法提取三元组时，将整条作为单独的 fact
            triples = [("knowledge", "is", content)]

        for subject, relation, value in triples:
            if len(self._facts) >= self.max_facts:
                self._facts.sort(key=lambda f: f["importance"])
                self._facts = self._facts[-(self.max_facts - 1):]

            self._facts.append({
                "subject": subject,
                "relation": relation,
                "value": value,
                "importance": max(0.0, min(1.0, importance)),
                "timestamp": time.time(),
                "knowledge_type": knowledge_type,
                "metadata": metadata,
            })

            # 更新知识图谱
            self._entities[subject].add(value)
            self._entities[value].add(subject)

    def search(self, query: str, limit: int = 10, min_importance: float = 0.0) -> list[dict]:
        """搜索相关知识"""
        q_lower = query.lower()
        scored = []

        for fact in self._facts:
            if fact["importance"] < min_importance:
                continue

            # 关键词匹配
            fact_text = f"{fact['subject']} {fact['relation']} {fact['value']}".lower()
            q_words = set(q_lower.split())
            f_words = set(fact_text.split())

            if q_words:
                keyword_score = len(q_words & f_words) / max(len(q_words), 1)
            else:
                keyword_score = 1.0

            # 图相关度：查询词是否连接到事实中的实体
            graph_score = 0.0
            for word in q_words:
                if word in self._entities:
                    if fact["subject"] in self._entities[word] or fact["value"] in self._entities[word]:
                        graph_score = 0.5
                        break

            score = (keyword_score * 0.7 + graph_score * 0.3) * (0.5 + fact["importance"] * 0.5)
            scored.append((fact, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [fact for fact, _ in scored[:limit]]

    def get_entities(self) -> list[str]:
        """获取所有实体"""
        return list(self._entities.keys())

    def get_relations(self, entity: str) -> list[dict]:
        """获取与某个实体相关的所有事实"""
        entity_lower = entity.lower()
        return [
            f for f in self._facts
            if f["subject"].lower() == entity_lower or f["value"].lower() == entity_lower
        ]

    def size(self) -> int:
        return len(self._facts)

    def _extract_triples(self, text: str) -> list[tuple]:
        """
        简单三元组提取。
        识别中文中的 "A是B"、"A属于B"、"A能B" 等模式。
        """
        triples = []
        text = text.replace("：", ":").replace("，", ",").replace("。", ".")

        # 模式 1: "A 是 B" / "A 是一种 B"
        for sep in ["是一种", "是", "属于"]:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    value = parts[1].strip().rstrip("。，,.")
                    if subject and value:
                        triples.append((subject, "is_a", value))
                        break

        # 模式 2: "A 能 B" / "A 可以 B"
        for sep in ["能", "可以", "能够"]:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    value = parts[1].strip().rstrip("。，,.")
                    if subject and value:
                        triples.append((subject, "can", value))
                        break

        # 模式 3: "A 有 B" / "A 包含 B"
        for sep in ["有", "包含", "包括"]:
            if sep in text:
                parts = text.split(sep, 1)
                if len(parts) == 2:
                    subject = parts[0].strip()
                    value = parts[1].strip().rstrip("。，,.")
                    if subject and value:
                        triples.append((subject, "has", value))
                        break

        return triples


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  语义记忆 (SemanticMemory) 演示")
    print("=" * 60)

    sm = SemanticMemory()

    # 添加知识
    sm.add("Python 是一种解释型编程语言", importance=0.9)
    sm.add("Python 有简洁的语法", importance=0.7)
    sm.add("Python 能用于 Web 开发", importance=0.8)
    sm.add("Python 能用于数据科学", importance=0.8)
    sm.add("JavaScript 是一种编程语言", importance=0.7)
    sm.add("JavaScript 能用于前端开发", importance=0.8)

    print(f"\n总知识条数: {sm.size()}")
    print(f"实体列表: {sm.get_entities()}")

    # 搜索
    print("\n--- 搜索 'Python' ---")
    for fact in sm.search("Python", limit=5):
        print(f"  [{fact['importance']:.1f}] {fact['subject']} {fact['relation']} {fact['value']}")

    print("\n--- 搜索 '编程语言' ---")
    for fact in sm.search("编程语言", limit=5):
        print(f"  [{fact['importance']:.1f}] {fact['subject']} {fact['relation']} {fact['value']}")

    # 获取实体的关系
    print("\n--- 与 'Python' 相关的事实 ---")
    for fact in sm.get_relations("Python"):
        print(f"  {fact['subject']} {fact['relation']} {fact['value']}")
