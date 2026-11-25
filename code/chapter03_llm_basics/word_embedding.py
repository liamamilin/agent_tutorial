"""
第 3 章：LLM 基础 — 词嵌入与余弦相似度

使用方式：
    python word_embedding.py

纯 Python 标准库。
"""

import math


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_product = math.sqrt(sum(a * a for a in vec1)) * math.sqrt(sum(b * b for b in vec2))
    return dot_product / norm_product


# 二维词向量（简化示例）
embeddings = {
    "king":  [0.9, 0.8],
    "queen": [0.9, 0.2],
    "man":   [0.7, 0.9],
    "woman": [0.7, 0.3],
}

# 经典类比：king - man + woman ≈ queen
result_vec = [
    embeddings["king"][0] - embeddings["man"][0] + embeddings["woman"][0],
    embeddings["king"][1] - embeddings["man"][1] + embeddings["woman"][1],
]

sim = cosine_similarity(result_vec, embeddings["queen"])

print(f"king   = {embeddings['king']}")
print(f"man    = {embeddings['man']}")
print(f"woman  = {embeddings['woman']}")
print(f"queen  = {embeddings['queen']}")
print(f"\nking - man + woman = {result_vec}")
print(f"该结果与 'queen' 的余弦相似度: {sim:.4f}")
