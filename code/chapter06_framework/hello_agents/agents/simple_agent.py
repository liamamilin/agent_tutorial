"""
HelloAgents — SimpleAgent

最简 Agent 实现：直接把 messages 交给 LLM。
"""

import os
import sys

try:
    # 作为包导入：python -m chapter06_framework.hello_agents.agents.simple_agent
    from ..core.agent import Agent
    from ..core.message import Message
except ImportError:
    # 作为脚本直接运行：python chapter06_framework/hello_agents/agents/simple_agent.py
    # 把 chapter06_framework/ 加进 sys.path，才能 import hello_agents
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from hello_agents.core.agent import Agent
    from hello_agents.core.message import Message


class SimpleAgent(Agent):
    """最简 Agent：直接把 messages 交给 LLM"""

    def _execute(self, messages: list[Message], **kwargs) -> str:
        return self.llm.invoke([m.to_dict() for m in messages], **kwargs)


# ============================================================
# 独立测试
# ============================================================
if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv

    # 确保能导入 hello_agents（从 code/ 目录运行时）
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    load_dotenv()

    from hello_agents.core.config import Config
    from hello_agents.core.llm import HelloAgentsLLM

    cfg = Config(debug=True, max_history_length=10)
    llm = HelloAgentsLLM()

    agent = SimpleAgent(
        name="助手",
        llm=llm,
        system_prompt="你是一个简洁的技术助教。",
        config=cfg,
    )

    print("=" * 50)
    print(agent.run("我叫Liam"))
    print(agent.run("我叫什么？"))
    print(f"\n历史消息数: {len(agent.get_history())}")
