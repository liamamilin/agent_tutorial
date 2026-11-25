"""
HelloAgents — 配置系统

集中管理框架运行参数，支持环境变量覆盖。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Config:
    """框架统一配置"""

    # LLM 相关
    temperature: float = 0.7
    max_tokens: int | None = None

    # 历史管理
    max_history_length: int = 100
    truncate_strategy: str = "drop_oldest"

    # 调试
    debug: bool = False

    # 扩展
    extra: dict[str, Any] = field(default_factory=dict)

    def with_updates(self, **kwargs) -> "Config":
        """返回带有更新字段的新 Config（不可变风格）"""
        data = {k: v for k, v in self.__dict__.items() if k != "extra"}
        extra = dict(self.extra)
        for k, v in kwargs.items():
            if k in data:
                data[k] = v
            else:
                extra[k] = v
        data["extra"] = extra
        return Config(**data)
