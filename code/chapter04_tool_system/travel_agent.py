"""
第 4 章：工具系统 — 完整旅行助手 Agent

使用方式：
    python travel_agent.py

依赖：openai, python-dotenv, requests
配置：在 code/ 目录下创建 .env 文件
"""

import re
import os
from openai import OpenAI
from dotenv import load_dotenv

from tools import get_weather, get_attraction
from tool_executor import ToolExecutor

load_dotenv()

# ============================================================
# 1. System Prompt（工具调用协议）
# ============================================================
TOOL_SYSTEM_PROMPT = """\
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步解决问题。

# 可用工具:
{tool_descriptions}

# 行动格式:
你的回答必须严格遵循以下格式。首先是你的思考过程，然后是你执行的具体行动：

Thought: [你的思考过程和下一步计划]
Action: [具体行动，必须是以下格式之一]
- get_weather(city="城市名"): 查询天气
- get_attraction(city="城市名", weather="天气状况"): 推荐景点
- Finish[最终答案]: 当你已收集足够信息，输出最终答案。

每次回复只输出一对 Thought-Action。严格遵守格式，不要添加额外前缀。
"""

# ============================================================
# 2. LLM 客户端
# ============================================================
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


def call_llm(system_prompt: str, history_text: str) -> str:
    """调用 LLM，返回文本回复"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": history_text},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


# ============================================================
# 3. Action 解析
# ============================================================
def extract_last_action(text: str) -> str | None:
    """从 LLM 输出中提取最后一个 Action"""
    matches = re.findall(r"Action:\s*(.*)", text)
    return matches[-1].strip() if matches else None


def is_finish(action: str) -> bool:
    """判断是否是终止信号"""
    return action.startswith("Finish[")


def extract_finish_content(action: str) -> str | None:
    """提取 Finish[...] 中的最终答案"""
    match = re.match(r"^Finish\[(.*)\]$", action, re.DOTALL)
    return match.group(1).strip() if match else None


def parse_tool_call(action: str) -> tuple[str | None, dict[str, str]]:
    """解析工具调用：支持命名参数和位置参数"""
    # 清理前缀和反引号
    action = re.sub(r'^.*?[:：]\s*', '', action).strip()
    action = action.strip('`')

    m = re.match(r"(\w+)\((.*)\)", action)
    if not m:
        return None, {}
    tool_name = m.group(1)
    args_str = m.group(2).strip()

    # 尝试命名参数: key="value"
    named = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str))
    if named:
        return tool_name, named

    # 尝试位置参数
    positional = re.findall(r'"([^"]*)"', args_str)
    if positional:
        return tool_name, {f"arg{i}": v for i, v in enumerate(positional)}

    return None, {}


# ============================================================
# 4. Agent 主循环
# ============================================================
def run_agent(user_query: str, executor: ToolExecutor, max_steps: int = 5) -> str | None:
    """运行工具调用 Agent"""
    system_prompt = TOOL_SYSTEM_PROMPT.format(
        tool_descriptions=executor.get_descriptions()
    )
    history = [f"用户请求: {user_query}"]

    print(f"用户输入: {user_query}")
    print("=" * 50)

    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---\n")

        full_prompt = "\n".join(history)
        llm_output = call_llm(system_prompt, full_prompt)
        print(f"模型输出:\n{llm_output}\n")

        history.append(llm_output)

        # 解析 Action
        action = extract_last_action(llm_output)
        if action is None:
            history.append("Observation: 错误 - 未能解析到 Action。")
            continue

        # 检查终止信号
        if is_finish(action):
            answer = extract_finish_content(action)
            if answer:
                print(f"✅ 任务完成:\n{answer}")
                return answer
            history.append("Observation: Finish 格式无效，请重新输出。")
            continue

        # 解析并执行工具调用
        tool_name, args = parse_tool_call(action)
        if tool_name is None:
            history.append(f"Observation: 无法解析工具调用: {action}")
            continue

        result = executor.execute(tool_name, **args)
        observation = f"Observation: {result}"
        print(f"{observation}\n" + "-" * 40)
        history.append(observation)

    print("⚠️ 达到最大步数，Agent 未完成。")
    return None


# ============================================================
# 5. 运行
# ============================================================
if __name__ == "__main__":
    executor = ToolExecutor()
    executor.register("get_weather", "查询指定城市的实时天气", get_weather)
    executor.register("get_attraction", "根据城市和天气推荐景点", get_attraction)

    print("\n" + "=" * 50)
    run_agent(
        "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。",
        executor,
    )
