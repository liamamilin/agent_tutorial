"""
第 4 章：工具系统 — 工具注册与执行器

可独立使用，也可被 travel_agent.py 导入。
"""

from typing import Any, Callable


class ToolExecutor:
    """工具注册与执行器"""

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, name: str, description: str, func: Callable) -> None:
        """注册一个工具"""
        self._tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def get_func(self, name: str) -> Callable | None:
        """获取工具函数"""
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def get_descriptions(self) -> str:
        """获取所有工具的描述（用于注入 Prompt）"""
        if not self._tools:
            return "（当前无可用工具）"
        lines = [f"- {name}: {info['description']}"
                 for name, info in self._tools.items()]
        return "\n".join(lines)

    def execute(self, name: str, **kwargs) -> str:
        """执行工具调用"""
        func = self.get_func(name)
        if func is None:
            return f"错误：未知工具 '{name}'"
        try:
            return func(**kwargs)
        except Exception as e:
            return f"工具执行错误: {e}"


# ============================================================
# 独立测试
# ============================================================
if __name__ == "__main__":
    from tools import get_weather, get_attraction

    executor = ToolExecutor()
    executor.register("get_weather", "查询指定城市的实时天气", get_weather)
    executor.register("get_attraction", "根据城市和天气推荐景点", get_attraction)

    print("\n可用工具:")
    print(executor.get_descriptions())

    print("\n--- 执行 get_weather ---")
    print(executor.execute("get_weather", city="Beijing"))

    print("\n--- 执行 get_attraction ---")
    print(executor.execute("get_attraction", city="杭州", weather="晴"))
