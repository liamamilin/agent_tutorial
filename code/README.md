# 《从零开始学习Agent》配套代码

本书配套 Python 代码按章节组织，每章脚本均可独立运行。

## 环境准备

```bash
pip install -r requirements.txt

# 复制并配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key 或本地 Ollama 配置
```

## 各章代码索引

| 章节 | 目录 | 核心主题 | 入口示例 |
|------|------|----------|---------|
| 第 1 章 | `chapter01_simple_agent/` | 最简对话 Agent | `python chapter01_simple_agent/simple_agent.py` |
| 第 2 章 | `chapter02_api/` | API 调用与可复用客户端 | `python chapter02_api/chat_loop.py` |
| 第 3 章 | `chapter03_conversation/` | 多轮对话、截断与状态追踪 | `python chapter03_conversation/conversational_agent.py` |
| 第 4 章 | `chapter04_streaming/` | 流式输出、重试、降级与日志 | `python chapter04_streaming/robust_agent.py` |
| 第 5 章 | `chapter05_structured/` | JSON / Pydantic / Function Calling | `python chapter05_structured/structured_agent.py` |
| 第 6 章 | `chapter04_tool_system/` | 工具系统与旅行助手 | `python chapter04_tool_system/travel_agent.py` |
| 第 7 章 | `chapter05_paradigms/` | ReAct / Plan-and-Solve / Reflection | `python chapter05_paradigms/react_agent.py` |
| 第 8 章 | `chapter06_framework/` | HelloAgents 轻量框架 | `pip install -e chapter06_framework` |
| 第 9 章 | `chapter09_memory/` | 工作/情景/语义记忆与遗忘 | `python chapter09_memory/memory_agent.py` |
| 第 10 章 | `chapter10_rag/` | 文档切分、TF-IDF 向量检索与 RAG | `python chapter10_rag/rag_agent.py` |
| 第 11 章 | `chapter11_context/` | 上下文组装、压缩、预算与缓存 | `python chapter11_context/context_agent.py` |
| 第 12 章 | `chapter09_multi_agent/` | AutoGen 多智能体协作 | `python chapter09_multi_agent/autogen_backlog.py` |
| 第 13 章 | `chapter13_evaluation/` | 评估指标与基准测试 | `python chapter13_evaluation/benchmark.py` |
| 附录 A | `chapter02_eliza/` | ELIZA 规则聊天机器人 | `python chapter02_eliza/eliza.py` |
| 附录 B | `chapter03_llm_basics/` | N-gram、词嵌入与 BPE 分词 | `python chapter03_llm_basics/bpe_tokenizer.py` |

## 依赖与注意事项

- **无需 LLM 即可运行**：第 13 章、附录 A、附录 B、部分工具/记忆/RAG 单元测试
- **需配置 `.env`**：第 1–11 章的完整 Agent 示例（支持 OpenAI 兼容接口或本地 Ollama）
- **多智能体示例**（第 12 章）：需额外安装 `autogen-agentchat` 与 `autogen-ext[openai]`，默认连接本地 Ollama（`localhost:11434`）

### `.env` 注释规则（python-dotenv）

```bash
# 整行注释：整行忽略
KEY=value
KEY=value        # 行尾注释：# 前必须有空格才会被剥离
KEY=value#注释   # 陷阱：# 前没空格，注释会变成值的一部分
KEY="value # x"  # 引号内的 # 不算注释
```

### 使用 OpenCode Go 网关时的自定义请求头

如果使用 `https://opencode.ai/inference/go/openai/v1`，需通过环境变量注入 `x-opencode-session`：

```bash
OPENAI_CUSTOM_HEADERS=x-opencode-session: 换成你的-uuid
```
