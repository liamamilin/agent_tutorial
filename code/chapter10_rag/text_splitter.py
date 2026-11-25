"""
文本分块器 —— 将长文档切分为适合检索的片段

学习目标：
1. 固定大小分块（带重叠）
2. 按段落分块
3. 理解 chunk_size 和 overlap 的影响
"""

from typing import List
from doc_loader import Document


class TextSplitter:
    """文本分块器 —— 多种分块策略"""

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        """
        参数:
        - chunk_size: 每个分块的目标字符数
        - chunk_overlap: 相邻分块的重叠字符数（保持上下文连续性）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_by_size(self, text: str) -> list[str]:
        """固定大小分块（带重叠）"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += (self.chunk_size - self.chunk_overlap)

        return chunks

    def split_by_paragraph(self, text: str) -> list[str]:
        """按段落分块（以双换行为分隔）"""
        paragraphs = text.split("\n\n")
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]

    def split_document(self, doc: Document, method: str = "size") -> list[Document]:
        """
        将 Document 分块，返回新的 Document 列表
        每个分块保留原始元数据并添加分块编号
        """
        if method == "size":
            chunks = self.split_by_size(doc.content)
        elif method == "paragraph":
            chunks = self.split_by_paragraph(doc.content)
        else:
            raise ValueError(f"未知分块方法: {method}")

        result = []
        for i, chunk in enumerate(chunks):
            result.append(Document(
                content=chunk,
                doc_id=f"{doc.doc_id}_chunk{i}",
                metadata={
                    **doc.metadata,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    "parent_doc_id": doc.doc_id,
                },
            ))
        return result


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    from doc_loader import DocumentLoader

    # 加载示例文档
    doc = DocumentLoader.load_text("sample_docs/agent_intro.txt")

    print("=" * 50)
    print("  文本分块演示")
    print("=" * 50)
    print(f"原始文档: {len(doc.content)} 字符\n")

    # 固定大小分块
    splitter = TextSplitter(chunk_size=150, chunk_overlap=30)
    chunks = splitter.split_document(doc, method="size")

    print(f"固定大小分块 (chunk_size=150, overlap=30):")
    print(f"  分块数: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  [{i}] {chunk.content[:80]}...")

    # 按段落分块
    print(f"\n按段落分块:")
    para_chunks = splitter.split_document(doc, method="paragraph")
    print(f"  分块数: {len(para_chunks)}")
    for i, chunk in enumerate(para_chunks):
        print(f"  [{i}] {chunk.content[:80]}...")
