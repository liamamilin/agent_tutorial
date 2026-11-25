"""
项目：上下文感知 Agent

整合本章所有能力：
- 上下文组装
- 上下文压缩
- Token 预算管理
- 上下文缓存

对比「无管理」vs「有管理」的上下文效果。
"""

import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

from context_assembler import ContextAssembler, ContextItem
from context_compressor import ContextCompressor
from token_budget import TokenBudget, TokenBudgetManager
from context_cache import ContextCache

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


class ContextAwareAgent:
    """上下文感知的对话 Agent"""

    def __init__(
        self,
        name: str = "助手",
        system_prompt: str = "你是一个有帮助的AI助手。",
        max_context_tokens: int = 4000,
        assembly_strategy: str = "priority",  # priority | layered | dynamic
        enable_cache: bool = True,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.max_context_tokens = max_context_tokens
        self.assembly_strategy = assembly_strategy
        self.enable_cache = enable_cache

        # 组件
        self.assembler = ContextAssembler(token_budget=max_context_tokens)
        self.compressor = ContextCompressor()
        self.budget_mgr = TokenBudgetManager(TokenBudget(total=max_context_tokens))
        self.cache = ContextCache(max_size=20) if enable_cache else None
        self.encoder = tiktoken.get_encoding("cl100k_base")

        # 对话历史
        self.history: list[ContextItem] = []

        # 统计
        self.total_tokens = 0

        # 初始化：添加 system prompt
        self.assembler.add_system(system_prompt, priority=1.0)

    def add_context(self, ctx_type, content: str, priority: float = 0.5):
        """添加持久上下文（如知识、指令）"""
        item = ContextItem(content, ctx_type, priority)
        self.assembler.add(item)

    def run(self, user_input: str) -> str:
        """运行 Agent"""
        # 1. 添加用户输入到历史
        self.history.append(ContextItem(user_input, "history", 0.6))

        # 2. 尝试缓存
        cached_context = None
        if self.cache:
            cached_context = self.cache.get(user_input, self.assembly_strategy)

        # 3. 组装上下文
        if cached_context:
            context_items = cached_context
            print("[命中缓存]")
        else:
            # 将历史也注册到 assembler（临时）
            for h in self.history[-6:]:  # 只保留最近 6 轮
                self.assembler.add(h)

            # 根据策略组装
            if self.assembly_strategy == "layered":
                context_items = self.assembler.assemble_layered()
            elif self.assembly_strategy == "dynamic":
                context_items = self.assembler.assemble_dynamic(user_input)
            else:
                context_items = self.assembler.assemble_by_priority(user_input)

            # 压缩超预算的上下文
            current_tokens = self.assembler.token_usage(context_items)
            if current_tokens > self.max_context_tokens:
                print(f"[上下文压缩: {current_tokens} → {self.max_context_tokens}]")
                context_items = self.compressor.compress_hybrid(
                    context_items, max_tokens=self.max_context_tokens, importance_threshold=0.3,
                )

            # 缓存结果
            if self.cache:
                self.cache.set(user_input, self.assembly_strategy, context_items)

        # 4. 转换为 messages 并调用 LLM
        messages = self.assembler.to_messages(context_items)
        messages.append({"role": "user", "content": user_input})

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content

        # 5. 更新统计
        if resp.usage:
            self.total_tokens += resp.usage.total_tokens

        # 6. 记录助手回复
        self.history.append(ContextItem(reply, "history", 0.5))

        return reply

    def stats(self):
        return {
            "total_tokens": self.total_tokens,
            "history_length": len(self.history),
            "cache_size": self.cache.size if self.cache else 0,
            "cache_hit_rate": f"{self.cache.hit_rate:.1%}" if self.cache else "N/A",
        }


# ============================================================
# 对比演示：无管理 vs 有管理
# ============================================================
class NaiveAgent:
    """无上下文管理的朴素 Agent（把所有上下文都塞进去）"""

    def __init__(self, name="朴素助手", system_prompt="你是AI助手。"):
        self.name = name
        self.system_prompt = system_prompt
        self.encoder = tiktoken.get_encoding("cl100k_base")
        # 把所有东西直接堆在 messages 里
        self.all_context = [{"role": "system", "content": system_prompt}]
        self.total_tokens = 0

    def add_context(self, content: str):
        self.all_context.append({"role": "user", "content": content})

    def run(self, user_input: str) -> str:
        messages = self.all_context + [{"role": "user", "content": user_input}]
        resp = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.7)
        reply = resp.choices[0].message.content
        if resp.usage:
            self.total_tokens += resp.usage.total_tokens
        return reply


if __name__ == "__main__":
    print("=" * 60)
    print("  上下文感知 Agent 对比演示")
    print("=" * 60)

    # ---- 朴素 Agent ----
    print("\n--- 朴素 Agent（无上下文管理）---")
    naive = NaiveAgent()
    # 模拟添加大量上下文
    for i in range(20):
        naive.add_context(f"这是第 {i} 条背景知识: Python 是一种广泛使用的编程语言。" * 3)

    reply = naive.run("什么是 Python？")
    print(f"回复: {reply[:100]}...")
    print(f"累计 Token: {naive.total_tokens}")

    # ---- 上下文感知 Agent ----
    print(f"\n--- 上下文感知 Agent（有管理）---")
    ctx_agent = ContextAwareAgent(
        name="智能助手",
        max_context_tokens=2000,
        assembly_strategy="priority",
        enable_cache=True,
    )
    # 添加相同的上下文
    for i in range(20):
        ctx_agent.add_context("knowledge", f"知识 {i}: Python 是一种编程语言。" * 3, priority=0.1 + i * 0.04)

    reply = ctx_agent.run("什么是 Python？")
    print(f"回复: {reply[:100]}...")
    print(f"累计 Token: {ctx_agent.total_tokens}")

    # 第二次相同查询 → 缓存命中
    reply = ctx_agent.run("什么是 Python？")
    print(f"\n第二次查询（应命中缓存）:")
    print(f"回复: {reply[:100]}...")

    stats = ctx_agent.stats()
    print(f"\n{'='*60}")
    print(f"  上下文感知 Agent 统计")
    print(f"{'='*60}")
    for k, v in stats.items():
        print(f"  {k}: {v}")
