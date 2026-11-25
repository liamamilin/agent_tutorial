"""
HelloAgents — Agent 抽象基类

所有 Agent 范式的统一入口。
"""

from abc import ABC, abstractmethod

from .message import Message
from .config import Config
from .llm import HelloAgentsLLM


class Agent(ABC):
    """Agent 抽象基类"""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: str | None = None,
        config: Config | None = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history: list[Message] = []

    # ===== 公开 API =====

    def run(self, input_text: str, **kwargs) -> str:
        """稳定入口：组装消息 → 调用执行 → 写入历史 → 截断历史"""
        messages = self._build_messages(input_text)

        if self.config.debug:
            print(f"\n[DEBUG] {self.name} messages:")
            for m in messages:
                print(f"  {m.compact()}")

        output = self._execute(messages, **kwargs)

        self.add_message(Message(role="user", content=input_text))
        self.add_message(Message(role="assistant", content=output))
        self._truncate_history()

        return output

    def add_message(self, message: Message) -> None:
        self._history.append(message)

    def get_history(self) -> list[Message]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()

    # ===== 子类实现 =====

    @abstractmethod
    def _execute(self, messages: list[Message], **kwargs) -> str:
        """子类实现核心逻辑"""
        ...

    # ===== 内部方法 =====

    def _build_messages(self, input_text: str) -> list[Message]:
        """组装 system + history + current user"""
        msgs: list[Message] = []
        if self.system_prompt:
            msgs.append(Message(role="system", content=self.system_prompt))
        msgs.extend(self._history)
        msgs.append(Message(role="user", content=input_text))
        return msgs

    def _truncate_history(self) -> None:
        limit = self.config.max_history_length
        if limit and len(self._history) > limit:
            self._history = self._history[-limit:]
