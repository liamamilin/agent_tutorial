"""
第 5 章：推理范式 — Plan-and-Solve Agent

使用方式：
    python plan_and_solve.py

依赖：openai, python-dotenv
配置：在 code/ 目录下创建 .env 文件
"""

import re
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
PLAN_PROMPT = """\
你是一个规划器。请为以下问题生成一个可执行的解决计划。

规划原则：
1. 每一步都是必要的，不允许冗余
2. 步骤必须是线性的、可顺序执行的
3. 每一步描述"要做什么"，而不是结论
4. 使用编号列表（1. 2. 3. ...）

问题：
{question}
"""

ACTION_PROMPT = """\
你是一个执行器。请严格执行给定计划中的当前步骤。

全局约束：
- 不允许新增、删除或重排步骤
- 不允许提前或总结后续步骤

完整计划：
{plan}

当前步骤：
{step}

原始问题：
{question}

请只完成当前步骤的内容。
"""


# ============================================================
# 3. Plan-and-Solve 主流程
# ============================================================
def plan_and_solve(question: str, verbose: bool = True) -> dict:
    """Plan-and-Solve 主流程"""

    # ---- 规划阶段 ----
    plan_text = call_llm(
        "You are a planning agent.",
        PLAN_PROMPT.format(question=question),
    )

    # 提取编号步骤
    steps = re.findall(r"^\s*\d+\.\s*(.+)", plan_text, re.MULTILINE)

    if verbose:
        print("===== PLAN =====")
        print(plan_text)

    # ---- 执行阶段 ----
    results = []
    for i, step in enumerate(steps, 1):
        if verbose:
            print(f"\n--- 执行步骤 {i}: {step} ---")

        result = call_llm(
            "You are an execution agent.",
            ACTION_PROMPT.format(
                plan=plan_text,
                step=step,
                question=question,
            ),
        )
        results.append({"step": step, "output": result.strip()})

        if verbose:
            print(result.strip())

    return {"question": question, "plan": plan_text, "steps": results}


# ============================================================
# 4. 运行
# ============================================================
if __name__ == "__main__":
    result = plan_and_solve(
        "一家公司想引入 AI 自动化客服流程，请分析是否适合自动化、主要风险和实施步骤。"
    )

    print("\n" + "=" * 50)
    print("最终汇总：")
    for s in result["steps"]:
        print(f"\n--- {s['step']} ---")
        print(s["output"])
