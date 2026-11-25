"""
上下文压缩技术

学习目标：
1. 实现截断压缩（按 token 截断）
2. 实现重要性过滤压缩
3. 实现 LLM 摘要压缩
4. 组合多种压缩策略
"""

import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv
from context_assembler import ContextItem

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


class ContextCompressor:
    """上下文压缩器"""

    def __init__(self):
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    # ---- 策略 1: 截断 ----

    def truncate(self, items: list[ContextItem], max_tokens: int) -> list[ContextItem]:
        """简单截断：按字符比例缩短每个长文本项"""
        result = []
        for item in items:
            tc = self.count_tokens(item.content)
            if tc <= max_tokens // max(len(items), 1):
                result.append(item)
            else:
                # 截断内容
                truncated_content = self._truncate_text(item.content, max_tokens // max(len(items), 1))
                result.append(ContextItem(
                    content=truncated_content,
                    ctx_type=item.ctx_type,
                    priority=item.priority,
                ))
        return result

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """按 token 截断文本"""
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = self.encoder.decode(tokens[:max_tokens])
        return truncated + "..."

    # ---- 策略 2: 重要性过滤 ----

    def filter_by_importance(self, items: list[ContextItem], threshold: float = 0.5) -> list[ContextItem]:
        """只保留重要性 >= threshold 的项"""
        return [it for it in items if it.priority >= threshold]

    # ---- 策略 3: LLM 摘要 ----

    def summarize_with_llm(self, items: list[ContextItem], target_tokens: int = 200) -> list[ContextItem]:
        """用 LLM 将上下文摘要为一段话"""
        # 拼接所有内容
        full_text = "\n---\n".join(f"[{it.ctx_type}] {it.content}" for it in items)

        if self.count_tokens(full_text) <= target_tokens:
            return items  # 已经够短，不需要摘要

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": f"将以下内容摘要为不超过 {target_tokens} tokens 的文本。保留所有关键信息。只输出摘要。"},
                {"role": "user", "content": full_text},
            ],
            temperature=0.2,
        )
        summary = resp.choices[0].message.content
        return [ContextItem(content=summary, ctx_type="knowledge", priority=0.9)]

    # ---- 策略 4: 混合压缩 ----

    def compress_hybrid(
        self, items: list[ContextItem], max_tokens: int, importance_threshold: float = 0.3,
    ) -> list[ContextItem]:
        """混合策略：先过滤低重要性，再截断，最后对剩余做摘要"""
        # Step 1: 过滤低重要性
        filtered = self.filter_by_importance(items, importance_threshold)

        # Step 2: 截断长文本
        truncated = self.truncate(filtered, max_tokens * 2)  # 先宽松截断

        # Step 3: 如果还是太长，用 LLM 摘要
        current_tokens = sum(self.count_tokens(it.content) for it in truncated)
        if current_tokens > max_tokens:
            summarized = self.summarize_with_llm(truncated, target_tokens=max_tokens)
            return summarized

        return truncated


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    compressor = ContextCompressor()

    # 创建一些上下文项
    items = [
        ContextItem("你是AI助手。" * 5, "system", 1.0),
        ContextItem("Python 是一种编程语言，由 Guido van Rossum 创建于 1991 年。它强调代码可读性，使用缩进来定义代码块。" * 3, "knowledge", 0.8),
        ContextItem("用户今天早上问了关于列表推导式的问题。" * 2, "memory", 0.6),
        ContextItem("昨天讨论过循环" * 10, "memory", 0.4),
        ContextItem("无关紧要的背景信息。" * 5, "history", 0.2),
    ]

    print("=" * 60)
    print("  原始上下文")
    print("=" * 60)
    total = sum(compressor.count_tokens(it.content) for it in items)
    print(f"  总 Token: {total}")
    for it in items:
        tc = compressor.count_tokens(it.content)
        print(f"  [{it.ctx_type}] p={it.priority:.1f} | {tc} tokens | {it.content[:50]}...")

    # 策略 1: 截断
    truncated = compressor.truncate(items, max_tokens=100)
    t1 = sum(compressor.count_tokens(it.content) for it in truncated)
    print(f"\n{'='*60}")
    print(f"  截断压缩 → {t1} tokens (原始 {total})")
    print(f"{'='*60}")

    # 策略 2: 重要性过滤
    filtered = compressor.filter_by_importance(items, threshold=0.5)
    t2 = sum(compressor.count_tokens(it.content) for it in filtered)
    print(f"\n  重要性过滤 (threshold=0.5) → {t2} tokens (原始 {total})")
    for it in filtered:
        print(f"  [{it.ctx_type}] p={it.priority:.1f}")

    # 策略 3: LLM 摘要
    print(f"\n{'='*60}")
    print(f"  LLM 摘要压缩（调用 LLM...）")
    print(f"{'='*60}")
    summarized = compressor.summarize_with_llm(items, target_tokens=100)
    t3 = sum(compressor.count_tokens(it.content) for it in summarized)
    print(f"  摘要结果 → {t3} tokens")
    print(f"  内容: {summarized[0].content[:200]}...")

    # 策略 4: 混合
    print(f"\n{'='*60}")
    print(f"  混合压缩（重要性过滤 + 截断 + 摘要）")
    print(f"{'='*60}")
    hybrid = compressor.compress_hybrid(items, max_tokens=100, importance_threshold=0.3)
    t4 = sum(compressor.count_tokens(it.content) for it in hybrid)
    print(f"  混合结果 → {t4} tokens")
