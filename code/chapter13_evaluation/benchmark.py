"""
第 10 章：评估与持续改进 — Benchmark 评估框架

使用方式：
    python benchmark.py

此模块定义了一套可复用的评估工具，可对任意 Agent 进行 Benchmark 测试。
"""

import time
from typing import Any


# ============================================================
# 1. 评估指标
# ============================================================
def compute_accuracy(output: str, expected: str, match_type: str = "contains") -> float:
    """计算输出与期望的匹配度"""
    if match_type == "exact":
        return 1.0 if output.strip() == expected.strip() else 0.0
    elif match_type == "contains":
        return 1.0 if expected in output else 0.0
    else:
        raise ValueError(f"Unknown match_type: {match_type}")


def evaluate_with_metrics(agent: Any, task: str, expected: str) -> dict:
    """运行一次评估，收集多维指标"""
    start = time.time()
    output = agent.run(task)
    elapsed = time.time() - start

    return {
        "task": task,
        "output": output[:100],
        "expected": expected,
        "accuracy": compute_accuracy(output, expected),
        "response_time": round(elapsed, 2),
        "output_length": len(output),
    }


# ============================================================
# 2. Benchmark 数据集
# ============================================================
BENCHMARK: list[dict] = [
    {
        "task": "What is 2 + 2?",
        "expected": "4",
        "category": "math",
        "difficulty": "easy",
    },
    {
        "task": "翻译: Hello, how are you?",
        "expected": "你好",
        "category": "translation",
        "difficulty": "easy",
    },
    {
        "task": "用一句话解释什么是 API。",
        "expected": "",  # 开放性问题，使用 LLM 评分
        "category": "explanation",
        "difficulty": "medium",
    },
]


def run_benchmark(agent: Any, benchmark: list[dict]) -> list[dict]:
    """运行完整的 Benchmark"""
    results = []
    for item in benchmark:
        output = agent.run(item["task"])
        score = compute_accuracy(output, item["expected"]) if item["expected"] else None
        results.append({
            "task": item["task"][:40],
            "category": item["category"],
            "difficulty": item["difficulty"],
            "accuracy": score,
        })
    return results


def print_benchmark_report(results: list[dict]) -> None:
    """打印 Benchmark 报告"""
    print("\n" + "=" * 60)
    print("BENCHMARK REPORT")
    print("=" * 60)
    for r in results:
        acc_str = f"{r['accuracy']:.2f}" if r["accuracy"] is not None else "N/A"
        print(f"  [{r['category']:15s}] [{r['difficulty']:6s}] {r['task']:40s}  acc={acc_str}")

    scores = [r["accuracy"] for r in results if r["accuracy"] is not None]
    if scores:
        print(f"\n  平均准确率: {sum(scores) / len(scores):.2%}")


# ============================================================
# 3. 奖励函数（用于 RL 训练参考）
# ============================================================
class AgentReward:
    """Agent 奖励函数示例"""

    def compute(
        self,
        task_completed: bool,
        steps_taken: int,
        user_satisfaction: float | None = None,
    ) -> float:
        reward = 0.0

        if task_completed:
            reward += 1.0
        else:
            reward -= 0.5

        reward -= steps_taken * 0.05

        if user_satisfaction is not None:
            reward += user_satisfaction * 0.5

        return reward


# ============================================================
# 4. 自测
# ============================================================
if __name__ == "__main__":
    # 测试准确率计算
    assert compute_accuracy("The capital is Paris.", "Paris", "contains") == 1.0
    assert compute_accuracy("The capital is Paris.", "London", "contains") == 0.0
    assert compute_accuracy("4", "4", "exact") == 1.0
    print("✓ 准确率计算测试通过")

    # 测试奖励函数
    reward_fn = AgentReward()
    r1 = reward_fn.compute(task_completed=True, steps_taken=3)
    r2 = reward_fn.compute(task_completed=False, steps_taken=8)
    print(f"✓ 奖励函数测试: 成功={r1:.2f}, 失败={r2:.2f}")

    # 演示 Benchmark 报告（使用模拟数据）
    print("\n--- Benchmark 报告示例 ---")
    mock_results = [
        {"task": "What is 2+2?", "category": "math", "difficulty": "easy", "accuracy": 1.0},
        {"task": "翻译 Hello", "category": "translation", "difficulty": "easy", "accuracy": 0.8},
        {"task": "解释 API", "category": "explanation", "difficulty": "medium", "accuracy": None},
    ]
    print_benchmark_report(mock_results)
