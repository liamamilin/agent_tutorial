"""
第 2 章：智能体简史 — ELIZA 聊天机器人

使用方式：
    python eliza.py

纯 Python 标准库，无需额外依赖。
"""

import re
import random


# ============================================================
# 1. 规则库：模式 -> 响应模板列表
# ============================================================
RULES: dict[str, list[str]] = {
    r"I need (.*)": [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?",
    ],
    r"Why don'?t you ([^\?]*)\??": [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?",
    ],
    r"Why can'?t I ([^\?]*)\??": [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?",
    ],
    r"I am (.*)": [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?",
    ],
    r"I'?m (.*)": [
        "How does being {0} make you feel?",
        "Why do you think you're {0}?",
    ],
    r".* mother .*": [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?",
    ],
    r".* father .*": [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?",
    ],
    r".*": [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?",
    ],
}

# ============================================================
# 2. 代词转换表
# ============================================================
PRONOUN_SWAP: dict[str, str] = {
    "i": "you", "you": "i", "me": "you",
    "my": "your", "am": "are", "are": "am",
    "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will",
    "yours": "mine", "mine": "yours",
}


def swap_pronouns(phrase: str) -> str:
    """简单的代词互换"""
    words = phrase.lower().split()
    swapped = [PRONOUN_SWAP.get(w, w) for w in words]
    return " ".join(swapped)


def respond(user_input: str) -> str:
    """根据规则库生成回复"""
    for pattern, templates in RULES.items():
        match = re.match(pattern, user_input, re.IGNORECASE)
        if match:
            # 提取捕获组（如果有）
            captured = match.group(1) if match.lastindex else ""
            swapped = swap_pronouns(captured)
            # 随机选择一个模板并替换占位符
            template = random.choice(templates)
            return template.replace("{0}", swapped)
    return "I'm not sure I understand."


# ============================================================
# 主聊天循环
# ============================================================
def main():
    print("Therapist: Hello! How can I help you today?")
    print("(Type 'quit' to exit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        response = respond(user_input)
        print(f"Therapist: {response}")


if __name__ == "__main__":
    main()
