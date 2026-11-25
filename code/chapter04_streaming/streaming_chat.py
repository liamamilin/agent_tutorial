"""
带 typing 效果的流式对话

学习目标：
1. 在 Agent 中集成流式输出
2. 实现逐字打印效果
3. 处理流式输出的终止条件
"""

import os
import sys
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
)
MODEL = os.getenv("LLM_MODEL_ID", "qwen2.5-coder:14b")


class StreamingAgent:
    """支持流式输出的对话 Agent"""

    def __init__(self, name: str, system_prompt: str | None = None):
        self.name = name
        self.system_prompt = system_prompt or f"你是{name}，一个友善的AI助手。"
        self.history: list[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]

    def run(self, user_input: str, stream: bool = True) -> str:
        """运行 Agent，支持流式和非流式两种模式"""
        self.history.append({"role": "user", "content": user_input})

        if stream:
            return self._run_streaming()
        else:
            return self._run_non_streaming()

    def _run_non_streaming(self) -> str:
        """非流式：等待完整回复"""
        print(f"{self.name}: ", end="", flush=True)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=self.history,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content
        print(reply)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def _run_streaming(self) -> str:
        """流式：逐字打印，模拟 typing 效果"""
        print(f"{self.name}: ", end="", flush=True)

        stream = client.chat.completions.create(
            model=MODEL,
            messages=self.history,
            temperature=0.7,
            stream=True,
        )

        full_reply = ""
        for chunk in stream:
            # 最后一个 chunk 可能只带 usage 而没有 choices，务必先判空
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            if delta.content:
                full_reply += delta.content
                print(delta.content, end="", flush=True)
                # 微小的延迟，增强 typing 效果（可选）
                # time.sleep(0.01)

        print()  # 换行
        self.history.append({"role": "assistant", "content": full_reply})
        return full_reply

    def run_interactive(self):
        """交互式对话循环（流式输出）"""
        print(f"\n{'='*50}")
        print(f"  {self.name} 已上线！（流式模式）")
        print(f"  输入 'quit' 退出，输入 '/ns' 切换非流式")
        print(f"{'='*50}\n")

        use_stream = True

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
            if user_input == "/ns":
                use_stream = not use_stream
                mode = "流式" if use_stream else "非流式"
                print(f"[已切换到{mode}模式]\n")
                continue

            self.run(user_input, stream=use_stream)
            print()


if __name__ == "__main__":
    agent = StreamingAgent(name="小助手")
    agent.run_interactive()
