# 《从零开始学习Agent》

> 动手构建你的第一个智能体 —— 从 30 行代码到多智能体与评估体系，每章配可运行 Python 代码与浏览器内交互式实验台。

- **在线阅读**：https://liamamilin.github.io/agent_tutorial/
- **代码目录**：[`code/`](code/)

## 目录概览

1. **基础对话 Agent**（第 1–4 章）：认识智能体、LLM API、多轮对话与状态管理、流式输出与工程健壮性
2. **Agent 能力扩展**（第 5–8 章）：结构化输出与 Function Calling、工具系统、推理范式（ReAct / Plan-and-Solve / Reflection）、自建轻量框架
3. **进阶能力**（第 9–13 章）：记忆系统、RAG 检索增强、上下文工程、多智能体协作、评估与基准测试
4. **附录**：Agent 发展简史（ELIZA）、大语言模型原理基础（N-gram / 词嵌入 / BPE）

## 本地预览与构建

需安装 [Quarto](https://quarto.org/docs/get-started/)：

```bash
# 本地实时预览
quarto preview

# 构建 HTML 书籍到 _book/
quarto render --to html
```

## 配套代码运行

```bash
cd code
pip install -r requirements.txt
cp .env.example .env
# 在 .env 中填入你的 API Key 或本地 Ollama 配置
python chapter01_simple_agent/simple_agent.py
```

## 自动部署

本项目已配置 [`.github/workflows/publish.yml`](.github/workflows/publish.yml)。在 GitHub 仓库的 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions** 后，每次推送到 `main` 分支都会自动渲染并发布到 GitHub Pages。
