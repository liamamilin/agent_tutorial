"""
第 5 章：推理范式 — Reflection Agent

使用方式：
    python reflection_agent.py

依赖：openai, python-dotenv
配置：在 code/ 目录下创建 .env 文件
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. LLM 客户端
# ============================================================
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


def call_llm(system_prompt: str, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


# ============================================================
# 2. Prompts
# ============================================================
ACTOR_PROMPT = "你是一个助手，请直接回答下面的问题。\n\n问题：\n{question}"

REFLECTION_PROMPT = """\
你是一个严格的审稿人。请对下面的回答进行反思和批评。

关注点（包括但不限于）：
- 是否遗漏重要方面
- 是否存在逻辑跳跃或模糊表述
- 是否有潜在风险或不严谨之处
- 是否可以更具体、更可执行

不要重写答案，只输出【问题清单】。

问题：{question}
回答：{answer}
"""

REWRITE_PROMPT = """\
你是一个改写助手。请基于下面的反思意见，对原始回答进行改进。

要求：
- 保留原有结构中合理的部分
- 明确修复反思中指出的问题
- 提供更清晰、可靠的最终回答

问题：{question}
原始回答：{answer}
反思意见：{reflection}
"""


# ============================================================
# 3. Reflection Agent 主流程
# ============================================================
def reflection_agent(question: str, verbose: bool = True) -> dict:
    """Reflection Agent：执行 → 反思 → 优化"""

    # 1. Actor：生成初始回答
    initial = call_llm(
        "You are an answering agent.",
        ACTOR_PROMPT.format(question=question),
    )
    if verbose:
        print("===== 初始回答 =====")
        print(initial, "\n")

    # 2. Reflector：找问题
    reflection = call_llm(
        "You are a reflection agent.",
        REFLECTION_PROMPT.format(question=question, answer=initial),
    )
    if verbose:
        print("===== 反思意见 =====")
        print(reflection, "\n")

    # 3. Rewriter：基于反思改进
    final = call_llm(
        "You are a rewriting agent.",
        REWRITE_PROMPT.format(
            question=question,
            answer=initial,
            reflection=reflection,
        ),
    )
    if verbose:
        print("===== 最终回答 =====")
        print(final, "\n")

    return {
        "question": question,
        "initial": initial,
        "reflection": reflection,
        "final": final,
    }


# ============================================================
# 4. 运行
# ============================================================
if __name__ == "__main__":
    result = reflection_agent(
        "一家公司想引入 AI 自动化客服流程，"
        "请分析是否适合自动化、主要风险和实施步骤。"
    )

    print("=" * 50)
    print("对比总结：")
    print(f"\n初稿长度: {len(result['initial'])} 字符")
    print(f"终稿长度: {len(result['final'])} 字符")
    print(f"\n反思意见摘要:\n{result['reflection'][:200]}...")
