"""
向量存储 —— 基于 TF-IDF 的文档向量化与相似度检索

学习目标：
1. 实现轻量 TF-IDF 向量化
2. 余弦相似度计算
3. 文档添加与检索
"""

import math
from collections import Counter
from typing import List, Tuple
from doc_loader import Document


class VectorStore:
    """
    基于 TF-IDF 的轻量向量存储

    不需要外部依赖，纯 Python 实现：
    - TF: 词在该文档中出现的频率
    - IDF: log(总文档数 / 包含该词的文档数)
    - 相似度: 余弦相似度
    """

    def __init__(self):
        self.documents: list[Document] = []
        # 每个文档的词频向量
        self.term_freqs: list[dict[str, float]] = []
        # IDF 值缓存
        self.idf_cache: dict[str, float] = {}
        # 词汇表（所有出现过的词）
        self.vocabulary: set[str] = set()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """简单的中英文分词"""
        import re
        # 提取中文和英文单词
        tokens = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", text.lower())
        return tokens

    def _compute_tf(self, tokens: list[str]) -> dict[str, float]:
        """计算词频 TF"""
        counter = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {word: count / total for word, count in counter.items()}

    def add_documents(self, documents: list[Document]) -> None:
        """添加文档到向量存储"""
        for doc in documents:
            self.documents.append(doc)
            tokens = self._tokenize(doc.content)
            self.vocabulary.update(tokens)
            self.term_freqs.append(self._compute_tf(tokens))

        # 重建 IDF 缓存
        self._rebuild_idf()

    def _rebuild_idf(self):
        """重建 IDF 缓存"""
        self.idf_cache = {}
        num_docs = len(self.documents)

        for word in self.vocabulary:
            # 计算包含该词的文档数
            doc_count = sum(1 for tf in self.term_freqs if word in tf)
            # IDF = log(总文档数 / 包含该词的文档数)
            self.idf_cache[word] = math.log((num_docs + 1) / (doc_count + 1)) + 1

    def _compute_tfidf_vector(self, tf: dict[str, float]) -> dict[str, float]:
        """计算 TF-IDF 向量"""
        return {
            word: tf_val * self.idf_cache.get(word, 0)
            for word, tf_val in tf.items()
        }

    @staticmethod
    def _cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
        """计算两个稀疏向量的余弦相似度"""
        # 找出共同的键
        common_keys = set(vec1.keys()) & set(vec2.keys())

        if not common_keys:
            return 0.0

        # 点积
        dot_product = sum(vec1[k] * vec2[k] for k in common_keys)

        # 模长
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> list[tuple[Document, float]]:
        """
        搜索与查询最相似的文档

        参数:
        - query: 查询文本
        - top_k: 返回前 k 个结果
        - min_similarity: 最小相似度阈值
        """
        # 查询向量化
        query_tokens = self._tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        query_tfidf = self._compute_tfidf_vector(query_tf)

        # 计算与每个文档的相似度
        scores = []
        for i, tf in enumerate(self.term_freqs):
            doc_tfidf = self._compute_tfidf_vector(tf)
            sim = self._cosine_similarity(query_tfidf, doc_tfidf)
            if sim >= min_similarity:
                scores.append((self.documents[i], sim))

        # 按相似度降序排列
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def stats(self) -> dict:
        return {
            "num_documents": len(self.documents),
            "vocabulary_size": len(self.vocabulary),
        }


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    from doc_loader import DocumentLoader
    from text_splitter import TextSplitter

    # 加载并分块文档
    loader = DocumentLoader
    splitter = TextSplitter(chunk_size=200, chunk_overlap=30)

    docs = []
    for filename in ["python_intro.txt", "agent_intro.txt", "tools_intro.txt"]:
        doc = loader.load_text(f"sample_docs/{filename}")
        docs.extend(splitter.split_document(doc))

    # 创建向量存储
    store = VectorStore()
    store.add_documents(docs)

    print("=" * 50)
    print("  向量存储演示")
    print("=" * 50)
    print(f"文档数: {store.stats()['num_documents']}")
    print(f"词汇量: {store.stats()['vocabulary_size']}")

    # 搜索
    queries = [
        "Python 是什么",
        "什么是智能体",
        "工具有什么作用",
    ]

    for query in queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        results = store.search(query, top_k=3)
        for doc, score in results:
            preview = doc.content[:80].replace("\n", " ")
            print(f"  [{score:.4f}] {doc.doc_id}: {preview}...")
