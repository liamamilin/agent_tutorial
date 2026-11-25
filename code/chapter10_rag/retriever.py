"""
检索器 —— 包装向量存储，支持高级检索策略

学习目标：
1. 基础检索（top-k）
2. 结果去重与排序
3. 上下文格式化
"""

from typing import List, Tuple
from dataclasses import dataclass
from doc_loader import Document
from vector_store import VectorStore


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    documents: list[tuple[Document, float]]  # (文档, 相似度)
    total_found: int


class Retriever:
    """检索器 —— 在向量存储之上提供高级检索"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.01,
    ) -> RetrievalResult:
        """基础检索"""
        results = self.store.search(query, top_k=top_k, min_similarity=min_similarity)
        return RetrievalResult(
            query=query,
            documents=results,
            total_found=len(results),
        )

    def format_context(self, result: RetrievalResult, max_length: int = 2000) -> str:
        """
        将检索结果格式化为 LLM 可用的上下文字符串

        格式：
        [来源: doc_id]
        相关内容...
        """
        parts = []
        total_len = 0

        for doc, score in result.documents:
            source = doc.metadata.get("source", doc.doc_id)
            chunk_text = f"[来源: {source}]\n{doc.content}\n"
            if total_len + len(chunk_text) > max_length:
                break
            parts.append(chunk_text)
            total_len += len(chunk_text)

        if not parts:
            return "（未找到相关文档）"

        return "\n---\n".join(parts)


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    from doc_loader import DocumentLoader
    from text_splitter import TextSplitter

    # 构建索引（与 vector_store.py 演示相同）
    docs = []
    splitter = TextSplitter(chunk_size=200, chunk_overlap=30)
    for filename in ["python_intro.txt", "agent_intro.txt", "tools_intro.txt"]:
        doc = DocumentLoader.load_text(f"sample_docs/{filename}")
        docs.extend(splitter.split_document(doc))

    store = VectorStore()
    store.add_documents(docs)
    retriever = Retriever(store)

    print("=" * 50)
    print("  检索器演示")
    print("=" * 50)

    # 检索
    result = retriever.retrieve("Python 语言的特点", top_k=3)
    print(f"\n查询: {result.query}")
    print(f"找到 {result.total_found} 个结果:\n")

    for doc, score in result.documents:
        print(f"  [{score:.4f}] {doc.doc_id}")
        print(f"    内容: {doc.content[:100]}...")
        print()

    # 格式化上下文
    print("=" * 50)
    print("  格式化的上下文（可直接注入 Prompt）")
    print("=" * 50)
    context = retriever.format_context(result)
    print(context[:500] + "...")
