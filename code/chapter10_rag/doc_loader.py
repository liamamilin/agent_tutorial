"""
文档加载器 —— 从多种格式加载文档

学习目标：
1. 加载 .txt 和 .md 文件
2. 统一的 Document 数据结构
3. 批量加载目录中的文档
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Document:
    """统一的文档数据结构"""
    content: str                              # 文档内容
    doc_id: str                               # 文档唯一标识
    metadata: dict = field(default_factory=dict)  # 来源、作者等元数据
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        preview = self.content[:60].replace("\n", " ")
        return f"Document({self.doc_id}: {preview}...)"


class DocumentLoader:
    """文档加载器 —— 支持多种文件格式"""

    @staticmethod
    def load_text(path: str) -> Document:
        """加载纯文本文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        doc_id = os.path.splitext(os.path.basename(path))[0]
        return Document(
            content=content.strip(),
            doc_id=doc_id,
            metadata={"source": path, "format": "text"},
        )

    @staticmethod
    def load_markdown(path: str) -> Document:
        """加载 Markdown 文件，去除格式标记"""
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        # 去除常见 Markdown 标记
        content = raw
        content = re.sub(r"#{1,6}\s+", "", content)     # 标题
        content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)  # 粗体
        content = re.sub(r"\*(.+?)\*", r"\1", content)     # 斜体
        content = re.sub(r"`{1,3}[^`]*`{1,3}", "", content)  # 行内代码
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)  # 链接
        content = re.sub(r"!\[.*\]\([^)]+\)", "", content)  # 图片

        doc_id = os.path.splitext(os.path.basename(path))[0]
        return Document(
            content=content.strip(),
            doc_id=doc_id,
            metadata={"source": path, "format": "markdown"},
        )

    @staticmethod
    def load_directory(directory: str) -> list[Document]:
        """批量加载目录中的所有 .txt 和 .md 文件"""
        docs = []
        for filename in sorted(os.listdir(directory)):
            path = os.path.join(directory, filename)
            if not os.path.isfile(path):
                continue
            if filename.endswith(".txt"):
                docs.append(DocumentLoader.load_text(path))
            elif filename.endswith(".md"):
                docs.append(DocumentLoader.load_markdown(path))
            else:
                continue
        return docs


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  文档加载器演示")
    print("=" * 50)

    # 加载单个文件
    doc = DocumentLoader.load_text("sample_docs/python_intro.txt")
    print(f"\n加载文本文件:")
    print(f"  ID: {doc.doc_id}")
    print(f"  来源: {doc.metadata['source']}")
    print(f"  内容长度: {len(doc.content)} 字符")
    print(f"  预览: {doc.content[:100]}...")

    # 批量加载目录
    print(f"\n批量加载 sample_docs/:")
    docs = DocumentLoader.load_directory("sample_docs")
    for d in docs:
        print(f"  - {d}")
    print(f"\n共加载 {len(docs)} 个文档")
