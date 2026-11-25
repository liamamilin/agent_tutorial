"""
第 3 章：LLM 基础 — N-gram 语言模型

使用方式：
    python ngram.py

纯 Python 标准库。
"""

# 示例语料库
corpus = "simple agent learns simple agent works"
tokens = corpus.split()
total_tokens = len(tokens)

# 第一步：计算 P(simple)
count_simple = tokens.count("simple")
p_simple = count_simple / total_tokens
print(f"第一步: P(simple) = {count_simple}/{total_tokens} = {p_simple:.3f}")

# 第二步：计算 P(agent | simple)
bigrams = list(zip(tokens[:-1], tokens[1:]))
count_simple_agent = bigrams.count(("simple", "agent"))
p_agent_given_simple = count_simple_agent / count_simple
print(f"第二步: P(agent|simple) = {count_simple_agent}/{count_simple} = {p_agent_given_simple:.3f}")

# 第三步：计算 P(learns | agent)
count_agent = tokens.count("agent")
count_agent_learns = bigrams.count(("agent", "learns"))
p_learns_given_agent = count_agent_learns / count_agent
print(f"第三步: P(learns|agent) = {count_agent_learns}/{count_agent} = {p_learns_given_agent:.3f}")

# 句子概率连乘
p_sentence = p_simple * p_agent_given_simple * p_learns_given_agent
print(f"\n最后: P('simple agent learns') ≈ {p_simple:.3f} × {p_agent_given_simple:.3f} × {p_learns_given_agent:.3f} = {p_sentence:.3f}")
