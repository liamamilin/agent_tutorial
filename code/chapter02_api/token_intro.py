"""
Token 概念入门

学习目标：
1. 理解什么是 Token
2. 使用 tiktoken 查看文本的 token 数量
3. 理解中英文 token 效率差异
"""

import tiktoken

# ============================================================
# 1. 加载编码器（GPT-4o 使用的 cl100k_base）
# ============================================================
encoder = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """计算一段文本的 token 数量"""
    return len(encoder.encode(text))


def show_tokens(text: str, label: str = ""):
    """展示文本和它的 token 分解"""
    tokens = encoder.encode(text)
    decoded = [encoder.decode([t]) for t in tokens]
    print(f"\n--- {label} ---")
    print(f"原文: {text}")
    print(f"Token 数: {len(tokens)}")
    print(f"Token 列表: {tokens}")
    print(f"Token 解码: {decoded}")


# ============================================================
# 2. 测试不同文本
# ============================================================
# 英文
show_tokens("Hello, how are you?", "英文短句")

# 中文
show_tokens("你好，最近怎么样？", "中文短句")

# 对比：相同含义
show_tokens("I love programming.", "英文")
show_tokens("我喜欢编程。", "中文")

# 代码
show_tokens("def hello(): print('world')", "代码")

# ============================================================
# 3. 长文本估算
# ============================================================
long_text = """
在这一章中，我们将学习如何调用大语言模型的 API。首先需要了解什么是 Token，
以及为什么 Token 数量对你来说很重要——它不仅影响模型的理解能力，
还直接决定了每次调用的费用。

Token 是模型处理文本的最小单位。对于英文来说，一个 Token 大约等于
3/4 个单词；对于中文来说，一个 Token 大约等于 0.5-1 个汉字。
这意味着相同含义的中文通常比英文消耗更多 Token。
"""
token_count = count_tokens(long_text)
print(f"\n--- 长文本 ---")
print(f"文本长度: {len(long_text)} 字符")
print(f"Token 数: {token_count}")
print(f"平均每字符 token 数: {token_count / len(long_text):.2f}")
