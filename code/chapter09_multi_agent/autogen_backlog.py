"""
第 9 章：多智能体协作 — AutoGen 多 Agent 协作示例

使用方式：
    pip install autogen-agentchat "autogen-ext[openai]"
    python autogen_backlog.py

依赖：autogen-agentchat, autogen-ext[openai]
"""

import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ============================================================
# 工具函数：RICE 评分
# ============================================================
def rice_score(reach: int, impact: float, confidence: float, effort: float) -> float:
    """RICE = (Reach × Impact × Confidence) / Effort"""
    if effort <= 0:
        raise ValueError("effort must be > 0")
    if not (0 <= confidence <= 1):
        raise ValueError("confidence must be between 0 and 1")
    return (reach * impact * confidence) / effort


async def main():
    # ============================================================
    # 模型客户端（连接本地 Ollama）
    # ============================================================
    model_client = OpenAIChatCompletionClient(
        model="qwen3:14b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        temperature=0.3,
        model_info={
            "family": "llama",
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        },
    )

    # ============================================================
    # 主执行 Agent（产品负责人）
    # ============================================================
    primary = AssistantAgent(
        name="primary",
        model_client=model_client,
        tools=[rice_score],
        system_message=(
            "你是流程自动化产品负责人。\n"
            "任务：把候选流程自动化需求整理为可交付的优先级 Backlog。\n"
            "硬性约束：每一个候选项都必须调用 rice_score 计算 RICE。\n"
            "输出：Markdown 表格（含 RICE 排序）+ 实施计划 + 风险清单。\n"
            "结尾输出关键字：READY_FOR_REVIEW"
        ),
    )

    # ============================================================
    # 评审 Agent（收敛机制）
    # ============================================================
    critic = AssistantAgent(
        name="critic",
        model_client=model_client,
        system_message=(
            "你是严格的 Reviewer。\n"
            "检查：RICE 是否已计算、表格字段完整、实施计划可执行、\n"
            "风险与指标具体可量化。\n"
            "不满足：给出明确修改清单。全部满足：只回复 APPROVE。"
        ),
    )

    # ============================================================
    # 终止条件 & 团队
    # ============================================================
    termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat(
        participants=[primary, critic],
        termination_condition=termination,
    )

    # ============================================================
    # 任务
    # ============================================================
    task = """
请为以下流程自动化候选项制作优先级 Backlog（使用 RICE）：

候选项 A：客服工单分类与自动分派
- Reach=12000, Impact=1.2, Confidence=0.65, Effort=1.8

候选项 B：财务对账异常自动识别
- Reach=1800, Impact=2.2, Confidence=0.55, Effort=2.5

候选项 C：HR 入职材料自动校验
- Reach=600, Impact=0.9, Confidence=0.8, Effort=0.9
"""

    # ============================================================
    # 运行
    # ============================================================
    await Console(team.run_stream(task=task))
    await model_client.close()


if __name__ == "__main__":
    print("启动多 Agent 协作系统...")
    print("=" * 50)
    asyncio.run(main())
