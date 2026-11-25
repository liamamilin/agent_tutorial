"""
HelloAgents — 消息系统

标准化的消息表示，支持与 OpenAI 格式互转。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


MessageRole = Literal["user", "assistant", "system", "tool"]


@dataclass
class Message:
    """框架内部的标准消息对象"""

    content: str
    role: MessageRole
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """转换为 OpenAI 兼容格式"""
        return {"role": self.role, "content": self.content}

    def compact(self, max_len: int = 120) -> str:
        """紧凑展示，用于日志和调试"""
        text = self.content.replace("\n", " ").strip()
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."
        return f"[{self.role}] {text}"
