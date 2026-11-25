"""
项目：完整的 RAG Agent

整合文档加载 → 分块 → 向量化 → 检索 → Prompt 组装 → LLM 回答

运行方式：
    python rag_agent.py
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

from doc_loader import DocumentLoader
from text_splitter import TextSplitter
from vector_store import VectorStore
from retriever import Retriever
from rag_prompt import RAGPromptBuilder

load_dotenv()


class RAGAgent:
    """完整的 RAG Agent —— 检索增强 + LLM 回答"""

    def __init__(
        self,
        name: str = "知识助手",
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        top_k: int = 3,
    ):
        self.name = name
        self.top_k = top_k

        # 初始化组件
        self.splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.store = VectorStore()
        self.retriever = None  # 在 index 后初始化

        # LLM 客户端
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )
        self.model = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")

        # 统计
        self.doc_count = 0

    # ===== 索引阶段 =====

    def index_file(self, filepath: str) -> int:
        """索引单个文件"""
        if filepath.endswith(".txt"):
            doc = DocumentLoader.load_text(filepath)
        elif filepath.endswith(".md"):
            doc = DocumentLoader.load_markdown(filepath)
        else:
            print(f"不支持的文件格式: {filepath}")
            return 0

        chunks = self.splitter.split_document(doc)
        self.store.add_documents(chunks)
        self.retriever = Retriever(self.store)
        self.doc_count += 1
        return len(chunks)

    def index_directory(self, directory: str) -> int:
        """索引目录中的所有文档"""
        docs = DocumentLoader.load_directory(directory)
        all_chunks = []
        for doc in docs:
            chunks = self.splitter.split_document(doc)
            all_chunks.extend(chunks)

        self.store.add_documents(all_chunks)
        self.retriever = Retriever(self.store)
        self.doc_count += len(docs)
        return len(all_chunks)

    # ===== 查询阶段 =====

    def ask(self, question: str, template: str = "qa") -> dict:
        """
        提问并获取回答

        返回: {"question": ..., "answer": ..., "sources": [...]}
        """
        if self.retriever is None:
            return {"question": question, "answer": "请先索引文档（调用 index_file 或 index_directory）。", "sources": []}

        # 1. 检索
        result = self.retriever.retrieve(question, top_k=self.top_k)
        context = self.retriever.format_context(result)

        # 2. 组装 Prompt
        prompt = RAGPromptBuilder.build(
            question=question,
            context=context,
            template=template,
        )

        # 3. 调用 LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        answer = response.choices[0].message.content

        # 4. 收集来源
        sources = list(set(
            doc.metadata.get("source", doc.doc_id)
            for doc, _ in result.documents
        ))

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(result.documents),
        }

    def run_interactive(self):
        """交互式问答循环"""
        print(f"\n{'='*50}")
        print(f"  {self.name} 已上线！(RAG 模式)")
        print(f"  已索引 {self.doc_count} 个文档")
        print(f"  输入 'quit' 退出")
        print(f"{'='*50}\n")

        while True:
            try:
                question = input("问: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not question:
                continue
            if question.lower() in ("quit", "exit", "退出"):
                print(f"{self.name}: 再见！")
                break

            result = self.ask(question)
            print(f"\n{self.name}: {result['answer']}")
            if result["sources"]:
                print(f"\n📚 参考来源: {', '.join(result['sources'])}")
            print()


# ============================================================
# 运行
# ============================================================
if __name__ == "__main__":
    agent = RAGAgent(name="知识助手")

    # 索引示例文档
    doc_dir = "sample_docs"
    if os.path.isdir(doc_dir):
        n = agent.index_directory(doc_dir)
        print(f"已索引 {n} 个文本块（来自 {agent.doc_count} 个文档）")

    # 交互式问答
    agent.run_interactive()
