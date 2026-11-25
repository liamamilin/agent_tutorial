"""
第 5 章：推理范式 — ReAct Agent

使用方式：
    python react_agent.py

依赖：openai, python-dotenv
配置：在 code/ 目录下创建 .env 文件
"""

import re
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. 工具定义
# ============================================================
def search_fact(query: str) -> str:
    """在本地知识库中查询事实"""
    fact_db = {
        "什么是智能体": "智能体（Agent）是一种能够感知环境、进行推理，并采取行动以达成目标的系统。",
        "智能体的核心组成": "智能体的核心组成包括：观察（Observation）、推理（Reasoning）、行动（Action）和记忆（Memory）。",
        "大语言模型和智能体的区别": "大语言模型主要负责生成文本，而智能体不仅能生成内容，还可以调用工具并执行行动。",
        "Transformer 的核心思想": "Transformer 的核心思想是使用注意力机制来建模序列，而不依赖循环结构。",
        "为什么智能体需要工具": "智能体需要工具来获取模型参数之外的信息或执行实际操作。",
    }

    def similarity(a: str, b: str) -> int:
        return len(set(a) & set(b))

    scores = [(k, similarity(query, k)) for k in fact_db]
    best = max(scores, key=lambda x: x[1])

    if best[1] >= 1:
        return f"FACT: {fact_db[best[0]]}"
    return "FACT: Not found"


# ============================================================
# 2. ToolExecutor
# ============================================================
class ToolExecutor:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, func) -> None:
        self._tools[name] = {"description": description, "func": func}

    def get_func(self, name: str):
        t = self._tools.get(name)
        return t["func"] if t else None

    def get_descriptions(self) -> str:
        if not self._tools:
            return "（当前无可用工具）"
        return "\n".join(
            f"- {name}: {info['description']}"
            for name, info in self._tools.items()
        )

    def execute(self, name: str, **kwargs) -> str:
        func = self.get_func(name)
        if func is None:
            return f"错误：未知工具 '{name}'"
        try:
            return func(**kwargs)
        except Exception as e:
            return f"工具执行错误: {e}"


# ============================================================
# 3. ReAct System Prompt
# ============================================================
REACT_PROMPT = """\
你是一个严格遵循 ReAct（Reason + Act）范式的智能体。

【核心原则】
1. 你只能通过 Action 行动
2. 任务完成的唯一方式是：Action: Finish[完整中文回答]

【可用工具】
{tool_descriptions}

【输出格式（每一步必须严格遵守）】
Thought: [分析当前状态、拆解任务、规划下一步]
Action: [具体行动，必须是以下格式之一]
- 工具调用（使用工具描述中的参数名）: tool_name(param_name="value")
- 任务完成: Finish[完整中文回答]

例如：
- search_fact(query="什么是智能体")
- Finish[智能体是...]

禁止在 Action 中添加 "工具调用:" 等前缀。

【FACT 收敛规则】
当 Observation 中出现 "FACT:" 开头的内容时，
这说明你已经获得了回答所需的全部关键信息。
你必须在下一步直接输出 Action: Finish[完整中文回答]。
"""


# ============================================================
# 4. 解析工具
# ============================================================
def extract_last_action(text: str) -> str | None:
    matches = re.findall(r"Action:\s*(.*)", text)
    return matches[-1].strip() if matches else None


def is_finish(action: str) -> bool:
    return action.startswith("Finish[")


def extract_finish(action: str) -> str | None:
    m = re.match(r"^Finish\[(.*)\]$", action, re.DOTALL)
    return m.group(1).strip() if m else None


def parse_tool_call(action: str) -> tuple[str | None, dict]:
    """解析工具调用：支持命名参数和位置参数"""
    # 清理前缀（如 "工具调用: "）
    action = re.sub(r'^.*?[:：]\s*', '', action).strip()

    m = re.match(r"(\w+)\((.*)\)", action)
    if not m:
        return None, {}
    tool_name = m.group(1)
    args_str = m.group(2).strip()

    # 尝试命名参数: key="value"
    named = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str))
    if named:
        return tool_name, named

    # 尝试位置参数: 提取引号内的值，按顺序匹配函数参数
    positional = re.findall(r'"([^"]*)"', args_str)
    if positional:
        # 获取函数参数名
        func = getattr(sys.modules[__name__], tool_name, None)
        if func and hasattr(func, '__code__'):
            param_names = func.__code__.co_varnames[:func.__code__.co_argcount]
            return tool_name, dict(zip(param_names, positional))
        else:
            # fallback: 用 arg0, arg1...
            return tool_name, {f"arg{i}": v for i, v in enumerate(positional)}

    return None, {}


def strip_think(text: str) -> str:
    """去除 DeepSeek-R1 等模型的 <think> 标签"""
    return re.sub(r"<think>[\s\S]*?</think>", "", text)


# ============================================================
# 5. LLM 客户端
# ============================================================
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


def call_llm(system_prompt: str, history: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": history},
        ],
        temperature=0.3,
    )
    return strip_think(resp.choices[0].message.content)


# ============================================================
# 6. ReAct 主循环
# ============================================================
def run_react_agent(user_query: str, executor: ToolExecutor, max_steps: int = 5) -> str | None:
    system_prompt = REACT_PROMPT.format(
        tool_descriptions=executor.get_descriptions()
    )
    history = [f"用户请求: {user_query}"]

    print(f"用户输入: {user_query}")
    print("=" * 50)

    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step} ---\n")
        prompt = "\n".join(history)
        llm_output = call_llm(system_prompt, prompt)
        print(f"模型输出:\n{llm_output}\n")
        history.append(llm_output)

        action = extract_last_action(llm_output)
        if action is None:
            history.append("Observation: 无法解析 Action")
            continue

        if is_finish(action):
            answer = extract_finish(action)
            if answer:
                print(f"✅ 任务完成:\n{answer}")
                return answer
            history.append("Observation: Finish 格式无效")
            continue

        tool_name, args = parse_tool_call(action)
        if tool_name is None:
            history.append(f"Observation: 无法解析工具调用: {action}")
            continue

        result = executor.execute(tool_name, **args)
        obs = f"Observation: {result}"
        print(f"{obs}\n" + "-" * 40)
        history.append(obs)

        # FACT 强制收敛
        if result.startswith("FACT:"):
            history.append("系统提示：已获得 FACT，请直接输出 Action: Finish[完整中文回答]。")

    print("⚠️ 达到最大步数")
    return None


# ============================================================
# 7. 运行
# ============================================================
if __name__ == "__main__":
    executor = ToolExecutor()
    executor.register("search_fact", "查询本地知识库中的事实信息", search_fact)

    print("=" * 50)
    run_react_agent("什么是智能体？", executor)
