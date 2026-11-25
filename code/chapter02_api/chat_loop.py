"""
项目：封装第一个带 LLM 的对话循环

学习目标：
1. 将 LLM 客户端集成到对话循环中
2. 实现基础的终端交互
3. 为下一章的完整 Agent 做铺垫
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class SimpleChatBot:
    """最简对话机器人 —— 能对话，但还没有 Agent 的所有能力"""

    def __init__(self, name: str = "小助手"):
        self.name = name
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        )
        self.model = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")
        self.system_prompt = f"你是{name}，一个友善、简洁的AI助手。回答尽量控制在3句话以内。"

    def reply(self, user_input: str) -> str:
        """根据用户输入返回回复"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    def run(self):
        """启动交互式对话循环"""
        print(f"\n{'=' * 50}")
        print(f"  {self.name} 已上线！输入 'quit' 退出")
        print(f"{'=' * 50}\n")

        while True:
            try:
                user_input = input("你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "退出"):
                print(f"{self.name}: 再见！")
                break

            reply = self.reply(user_input)
            print(f"{self.name}: {reply}\n")


if __name__ == "__main__":
    bot = SimpleChatBot(name="小助手")
    bot.run()
