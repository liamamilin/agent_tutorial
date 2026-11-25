"""
对话历史的截断策略

学习目标：
1. 实现三种截断策略
2. 理解各自的优缺点
3. 为后续的"上下文工程"（第11章）打基础
"""

import tiktoken
from typing import Literal

TruncateStrategy = Literal["sliding_window", "keep_first", "summary"]


class HistoryTruncator:
    """对话历史截断器"""

    def __init__(
        self,
        max_tokens: int = 4000,
        strategy: TruncateStrategy = "sliding_window",
    ):
        self.max_tokens = max_tokens
        self.strategy = strategy
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += 4 + len(self.encoder.encode(msg["content"]))
        return total + 2

    def truncate(self, history: list[dict]) -> list[dict]:
        """根据策略截断历史，始终保留 system 消息"""
        # system 消息永远不截断
        system = history[0] if history and history[0]["role"] == "system" else None
        msgs = history[1:] if system else history

        while self.count(history) > self.max_tokens and len(msgs) >= 2:
            if self.strategy == "sliding_window":
                # 滑动窗口：删除最旧的一对 user+assistant
                msgs = msgs[2:]
            elif self.strategy == "keep_first":
                # 保留首轮：从中间删除
                if len(msgs) > 4:
                    msgs = msgs[:2] + msgs[4:]
                else:
                    break
            else:
                break

            # 重建 history
            history = [system] + msgs if system else msgs

        return history


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    # 模拟一段长对话
    history = [
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "你好！" * 10},
        {"role": "assistant", "content": "你好！有什么可以帮你？" * 10},
        {"role": "user", "content": "讲个故事" * 50},
        {"role": "assistant", "content": "从前有座山..." * 50},
        {"role": "user", "content": "继续" * 10},
        {"role": "assistant", "content": "好的..." * 10},
    ]

    truncator = HistoryTruncator(max_tokens=500, strategy="sliding_window")

    print(f"截断前: {len(history)} 条消息, ~{truncator.count(history)} tokens")
    result = truncator.truncate(history)
    print(f"截断后: {len(result)} 条消息, ~{truncator.count(result)} tokens")

    # 确保 system 消息还在
    assert result[0]["role"] == "system", "System 消息应始终保留！"
    print("System 消息已保留 ✅")
