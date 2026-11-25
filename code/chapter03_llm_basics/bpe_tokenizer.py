"""
第 3 章：LLM 基础 — BPE 分词算法

使用方式：
    python bpe_tokenizer.py

纯 Python 标准库。
"""

from collections import Counter


def get_stats(vocab: dict[str, int]) -> Counter:
    """统计所有相邻 token 对的频率"""
    pairs: Counter = Counter()
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[(symbols[i], symbols[i + 1])] += freq
    return pairs


def merge_vocab(pair: tuple[str, str], vocab: dict[str, int]) -> dict[str, int]:
    """合并指定 token 对"""
    bigram = " ".join(pair)
    replacement = "".join(pair)
    new_vocab: dict[str, int] = {}
    for word, freq in vocab.items():
        new_word = word.replace(bigram, replacement)
        new_vocab[new_word] = freq
    return new_vocab


# 迷你语料库（每个字符用空格分隔，</w> 表示词尾）
vocab: dict[str, int] = {
    "h u g </w>": 1,
    "p u g </w>": 1,
    "p u n </w>": 1,
    "b u n </w>": 1,
}

NUM_MERGES = 4

print("初始词表:", list(vocab.keys()))

for i in range(NUM_MERGES):
    pairs = get_stats(vocab)
    if not pairs:
        break
    best_pair = pairs.most_common(1)[0][0]
    print(f"第 {i + 1} 次合并: '{' '.join(best_pair)}' → '{''.join(best_pair)}'")
    vocab = merge_vocab(best_pair, vocab)

print("\n最终词表:", list(vocab.keys()))

# 对未见过的词 "bug" 演示分词过程
print("\n--- 演示 ---")
print("新词 'bug' 的分词思路：")
print("  1. 查找 'bug'  → 不在词表中")
print("  2. 查找 'bu'   → 不在词表中")
print("  3. 查找 'b'    → 在词表中 ✓")
print("  4. 查找 'ug'   → 在词表中 ✓")
print("  结果: ['b', 'ug']")
