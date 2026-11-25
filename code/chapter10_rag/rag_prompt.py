"""
RAG Prompt 模板设计

学习目标：
1. 为不同场景设计 Prompt 模板
2. 将检索结果注入 Prompt
3. 引导模型合理利用检索到的知识
"""

# ============================================================
# 模板 1: 知识问答（带引用）
# ============================================================
QA_WITH_CITATION = """\
你是一个知识渊博的助手。请根据以下参考资料回答用户的问题。

要求：
1. 优先使用参考资料中的信息
2. 如果参考资料不足以回答，请明确说明
3. 在回答中标注信息来源（如 [来源: xxx]）

参考资料：
{context}

用户问题：{question}

请回答："""

# ============================================================
# 模板 2: 摘要总结
# ============================================================
SUMMARIZATION = """\
请根据以下资料，生成一个简洁的摘要。

要求：
- 篇幅：不超过 200 字
- 覆盖所有关键信息
- 使用流畅自然的中文

资料：
{context}

摘要："""

# ============================================================
# 模板 3: 对比分析
# ============================================================
COMPARISON = """\
你是一个技术分析师。请根据参考资料对比分析以下主题。

要求：
1. 列出相同点和不同点
2. 使用表格或列表形式（如有必要）
3. 给出你的判断或建议

参考资料：
{context}

分析主题：{question}

分析结果："""

# ============================================================
# 模板 4: 深入探究
# ============================================================
DEEP_DIVE = """\
你是一个研究助手。请基于参考资料深入分析以下问题。

要求：
1. 先给出核心结论
2. 展开详细解释
3. 补充参考资料中没有但相关的背景知识（如有）
4. 在结尾提出 1-2 个延伸思考问题

参考资料：
{context}

问题：{question}

分析："""


# ============================================================
# Prompt 组装器
# ============================================================
class RAGPromptBuilder:
    """RAG Prompt 组装器 —— 根据场景选择模板"""

    TEMPLATES = {
        "qa": QA_WITH_CITATION,
        "summary": SUMMARIZATION,
        "comparison": COMPARISON,
        "deep_dive": DEEP_DIVE,
    }

    @classmethod
    def build(
        cls,
        question: str,
        context: str,
        template: str = "qa",
    ) -> str:
        """
        组装完整的 RAG Prompt

        参数:
        - question: 用户问题
        - context: 检索到的上下文
        - template: 模板名称 (qa / summary / comparison / deep_dive)
        """
        template_str = cls.TEMPLATES.get(template, cls.TEMPLATES["qa"])
        return template_str.format(context=context, question=question)

    @classmethod
    def list_templates(cls) -> list[str]:
        return list(cls.TEMPLATES.keys())


# ============================================================
# 演示
# ============================================================
if __name__ == "__main__":
    # 模拟检索结果
    mock_context = """\
[来源: python_intro.txt]
Python 是一种解释型、面向对象的编程语言。Python 的设计哲学强调代码的可读性。

[来源: agent_intro.txt]
LLM 智能体是由大语言模型驱动的智能体，可以理解自然语言指令。
"""

    print("=" * 50)
    print("  RAG Prompt 模板演示")
    print("=" * 50)

    question = "Python 和 LLM Agent 有什么关系？"

    # 展示不同模板
    for template_name in RAGPromptBuilder.list_templates():
        print(f"\n{'='*50}")
        print(f"模板: {template_name}")
        print(f"{'='*50}")
        prompt = RAGPromptBuilder.build(
            question=question,
            context=mock_context,
            template=template_name,
        )
        print(prompt[:400])
        print("...")
