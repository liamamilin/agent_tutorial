(function () {
  const { register, shell, el } = window.AgentToys;

  // 1.1 ChatBot vs Agent 对比模拟器
  register("ch01-chatbot-vs-agent", (root) => {
    const body = shell(root, {
      badge: "互动实验 1.1",
      title: "ChatBot vs Agent：面对真实任务的区别",
      subtitle: "选择一个需要外部信息或行动的任务，对比纯聊天模型与智能体的执行路径"
    });
    const tasks = [
      {
        label: "查上海明天天气并给穿衣建议",
        chatbot: [
          { type: "warn", tag: "直接生成", text: "“上海明天大概率是晴天，气温 18°C 左右，建议穿长袖。”" },
          { type: "err", tag: "隐患", text: "模型没有联网能力，天气数据完全是靠训练记忆“猜”的（幻觉）。" }
        ],
        agent: [
          { type: "info", tag: "思考 Thought", text: "用户问的是实时天气，我不能凭空猜测，需要调用天气工具。" },
          { type: "purple", tag: "行动 Action", text: "get_weather(city='上海', day='tomorrow')" },
          { type: "ok", tag: "观察 Observation", text: "返回：中雨，12°C–16°C，东北风 4 级。" },
          { type: "ok", tag: "最终回答", text: "上海明天有中雨且降温至 12–16°C，建议带伞并穿防风外套。" }
        ]
      },
      {
        label: "计算 10 万元年化 4.5% 复利 15 年后的本息",
        chatbot: [
          { type: "warn", tag: "心算生成", text: "“大约是 19.12 万元（实际精确值为 19.35 万元，存在算术误差）。”" },
          { type: "err", tag: "隐患", text: "LLM 按 Token 概率预测数字，复杂算术容易出现偏差。" }
        ],
        agent: [
          { type: "info", tag: "思考 Thought", text: "涉及多步浮点幂运算，应交给精确计算器工具执行。" },
          { type: "purple", tag: "行动 Action", text: "calculator(expr='100000 * (1 + 0.045) ** 15')" },
          { type: "ok", tag: "观察 Observation", text: "返回：193528.2443" },
          { type: "ok", tag: "最终回答", text: "15 年后本息合计为 193,528.24 元，累计复利收益 93,528.24 元。" }
        ]
      },
      {
        label: "检查项目目录里是否有未提交的代码",
        chatbot: [
          { type: "warn", tag: "无法执行", text: "“请在终端运行 git status 查看结果。”" },
          { type: "err", tag: "局限", text: "只能给建议，不能触达本地环境完成闭环。" }
        ],
        agent: [
          { type: "info", tag: "思考 Thought", text: "我需要检查当前 Git 工作区状态。" },
          { type: "purple", tag: "行动 Action", text: "run_shell(cmd='git status -s')" },
          { type: "ok", tag: "观察 Observation", text: "返回：M chapter2_api.qmd, ?? notes.md" },
          { type: "ok", tag: "最终回答", text: "当前有 1 个已修改文件（chapter2_api.qmd）和 1 个未跟踪文件（notes.md）。" }
        ]
      }
    ];
    let idx = 0;
    const btnRow = el("div", { class: "toy-row" });
    const grid = el("div", { class: "toy-grid-2" });
    body.append(btnRow, grid);

    function render() {
      btnRow.innerHTML = "";
      tasks.forEach((t, i) => {
        btnRow.appendChild(el("button", {
          class: `toy-btn ${i === idx ? "active" : ""}`,
          onClick: () => { idx = i; render(); }
        }, t.label));
      });
      const t = tasks[idx];
      grid.innerHTML = "";
      grid.append(
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "ChatBot（单次输入 → 输出）", el("span", { class: "toy-pill warn" }, "无闭环")),
          el("div", { class: "toy-log" }, t.chatbot.map((s) =>
            el("div", { class: `toy-step ${s.type}` }, el("span", { class: `toy-pill ${s.type}` }, s.tag), s.text)
          ))
        ),
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "Agent（感知 → 思考 → 行动 → 观察）", el("span", { class: "toy-pill ok" }, "闭环执行")),
          el("div", { class: "toy-log" }, t.agent.map((s) =>
            el("div", { class: `toy-step ${s.type}` }, el("span", { class: `toy-pill ${s.type}` }, s.tag), s.text)
          ))
        )
      );
    }
    render();
  });

  // 1.2 Agent Loop 单步调试器
  register("ch01-loop-stepper", (root) => {
    const body = shell(root, {
      badge: "互动实验 1.2",
      title: "Agent Loop 单步调试器",
      subtitle: "点击“下一步”观察 Agent 如何在多轮循环中逐步更新状态直至完成目标"
    });
    const steps = [
      { phase: "感知 Perceive", cls: "info", state: "goal='推荐北京今日适合的户外景点', obs=None", detail: "接收用户目标，初始化上下文与可用工具清单（weather, search_poi）。" },
      { phase: "思考 Thought #1", cls: "purple", state: "need='北京今日天气'", detail: "户外景点强依赖天气，必须先查天气再做推荐。" },
      { phase: "行动 Action #1", cls: "warn", state: "call=get_weather('北京')", detail: "发出结构化工具调用请求，暂停生成等待环境返回。" },
      { phase: "观察 Observation #1", cls: "ok", state: "weather='晴, 22°C, 空气优'", detail: "天气结果写入上下文，成为下一轮决策的事实依据。" },
      { phase: "思考 Thought #2", cls: "purple", state: "need='北京秋季/晴天户外景点'", detail: "天气极佳，调用景点检索工具获取高评分户外地点。" },
      { phase: "行动 Action #2", cls: "warn", state: "call=search_poi('北京', '户外')", detail: "检索到颐和园、奥林匹克森林公园、景山公园。" },
      { phase: "终止 Finish", cls: "ok", state: "status='DONE', steps=2", detail: "信息充分，停止循环并综合天气与景点信息输出最终建议。" }
    ];
    let cur = 0;
    const ctrl = el("div", { class: "toy-row" });
    const trace = el("div", { class: "toy-log" });
    const stateBox = el("pre", { class: "toy-code" });
    body.append(ctrl, stateBox, trace);

    function render() {
      ctrl.innerHTML = "";
      ctrl.append(
        el("button", { class: "toy-btn", disabled: cur === 0, onClick: () => { cur--; render(); } }, "上一步"),
        el("button", { class: "toy-btn primary", disabled: cur === steps.length - 1, onClick: () => { cur++; render(); } }, "下一步"),
        el("button", { class: "toy-btn", onClick: () => { cur = 0; render(); } }, "重置"),
        el("span", { class: "toy-note" }, `当前进度：${cur + 1} / ${steps.length}`)
      );
      stateBox.textContent = `// 当前 Agent 状态快照\nstep = ${cur + 1}\nphase = "${steps[cur].phase}"\nstate = { ${steps[cur].state} }`;
      trace.innerHTML = "";
      steps.slice(0, cur + 1).forEach((s, i) => {
        trace.appendChild(el("div", { class: `toy-step ${s.cls}` },
          el("span", { class: `toy-pill ${s.cls}` }, `${i + 1}. ${s.phase}`),
          s.detail
        ));
      });
    }
    render();
  });

  // 2.1 API 请求/响应透视镜
  register("ch02-api-anatomy", (root) => {
    const body = shell(root, {
      badge: "互动实验 2.1",
      title: "Chat Completions API 参数与采样透视镜",
      subtitle: "调节 temperature 与 max_tokens，实时观察请求载荷、概率分布与返回结构的变化"
    });
    let temp = 0.7;
    let maxTok = 120;
    let model = "qwen3:14b";
    const controls = el("div", { class: "toy-row" });
    const grid = el("div", { class: "toy-grid-2" });
    const distBox = el("div", { class: "toy-card" });
    body.append(controls, distBox, grid);

    function softmax(logits, t) {
      const eff = Math.max(t, 0.05);
      const scaled = logits.map((x) => x / eff);
      const m = Math.max(...scaled);
      const exps = scaled.map((x) => Math.exp(x - m));
      const sum = exps.reduce((a, b) => a + b, 0);
      return exps.map((e) => e / sum);
    }

    function render() {
      controls.innerHTML = "";
      const sel = el("select", { class: "toy-select", onChange: (e) => { model = e.target.value; render(); } },
        ["qwen3:14b", "gpt-4o-mini", "deepseek-chat"].map((m) => el("option", { value: m, selected: m === model }, m))
      );
      const tSlider = el("div", { class: "toy-slider-group" },
        el("div", { class: "toy-slider-label" }, el("span", null, "temperature（随机性）"), el("strong", null, temp.toFixed(1))),
        el("input", { type: "range", min: "0", max: "1.5", step: "0.1", value: temp, onInput: (e) => { temp = parseFloat(e.target.value); render(); } })
      );
      const mSlider = el("div", { class: "toy-slider-group" },
        el("div", { class: "toy-slider-label" }, el("span", null, "max_tokens（输出上限）"), el("strong", null, String(maxTok))),
        el("input", { type: "range", min: "20", max: "300", step: "20", value: maxTok, onInput: (e) => { maxTok = parseInt(e.target.value, 10); render(); } })
      );
      controls.append(sel, tSlider, mSlider);

      const candidates = [
        { tok: "智能体", logit: 3.4 },
        { tok: "程序", logit: 2.2 },
        { tok: "助手", logit: 1.9 },
        { tok: "生命体", logit: 0.7 }
      ];
      const probs = softmax(candidates.map((c) => c.logit), temp);
      distBox.innerHTML = "";
      distBox.appendChild(el("div", { class: "toy-card-title" },
        "下一个 Token 采样概率分布（句首：“Agent 本质上是一个能自主行动的 ___”）",
        el("span", { class: `toy-pill ${temp <= 0.3 ? "ok" : temp <= 0.9 ? "info" : "warn"}` },
          temp <= 0.3 ? "极度确定（适合代码/工具）" : temp <= 0.9 ? "平衡（适合对话）" : "高发散（适合创意）")
      ));
      candidates.forEach((c, i) => {
        const pct = (probs[i] * 100).toFixed(1);
        distBox.appendChild(el("div", { class: "toy-row", style: "margin-bottom:4px" },
          el("span", { class: "toy-pill", style: "min-width:64px;text-align:center" }, c.tok),
          el("div", { class: "toy-bar-track", style: "flex:1" },
            el("div", { class: "toy-bar-seg", style: `width:${pct}%;background:${i === 0 ? "#2563eb" : "#94a3b8"}` })
          ),
          el("span", { style: "font-family:var(--toy-mono);font-size:0.78rem;min-width:44px;text-align:right" }, `${pct}%`)
        ));
      });

      const truncated = maxTok < 60;
      const reqJson = JSON.stringify({
        model,
        temperature: temp,
        max_tokens: maxTok,
        messages: [{ role: "user", content: "用一句话解释什么是 Agent" }]
      }, null, 2);
      const resJson = JSON.stringify({
        id: "chatcmpl-demo-01",
        choices: [{
          index: 0,
          message: {
            role: "assistant",
            content: truncated
              ? "Agent 是能感知环境、自主规划并调用工具完成任务的..."
              : "Agent 是能感知环境、自主规划并调用工具完成任务的智能系统。"
          },
          finish_reason: truncated ? "length" : "stop"
        }],
        usage: { prompt_tokens: 18, completion_tokens: truncated ? maxTok : 29, total_tokens: 18 + (truncated ? maxTok : 29) }
      }, null, 2);

      grid.innerHTML = "";
      grid.append(
        el("div", { class: "toy-card" }, el("div", { class: "toy-card-title" }, "Request Payload"), el("pre", { class: "toy-code" }, reqJson)),
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "Response JSON", el("span", { class: `toy-pill ${truncated ? "warn" : "ok"}` }, truncated ? "finish_reason: length" : "finish_reason: stop")),
          el("pre", { class: "toy-code" }, resJson)
        )
      );
    }
    render();
  });

  // 2.2 中英文 Token 拆分与成本计算器
  register("ch02-token-cost", (root) => {
    const body = shell(root, {
      badge: "互动实验 2.2",
      title: "Token 切分直观感受与 API 成本估算",
      subtitle: "输入任意中英文或代码文本，观察近似 Token 切分粒度与不同模型的调用开销"
    });
    const presets = [
      "你好，请帮我查询明天上海的天气并给出穿衣建议。",
      "Hello, please check tomorrow's weather in Shanghai and suggest what to wear.",
      "def run_agent(prompt: str) -> str:\n    return client.chat(prompt)"
    ];
    let text = presets[0];
    const presetRow = el("div", { class: "toy-row" });
    const ta = el("textarea", { class: "toy-textarea", onInput: (e) => { text = e.target.value; update(); } }, text);
    const tokWrap = el("div", { class: "toy-tokens" });
    const metrics = el("div", { class: "toy-metric-grid" });
    body.append(presetRow, ta, tokWrap, metrics);

    presets.forEach((p, i) => {
      presetRow.appendChild(el("button", {
        class: "toy-btn",
        onClick: () => { text = p; ta.value = p; update(); }
      }, ["中文示例", "英文示例", "Python 代码"][i]));
    });

    const colors = ["#dbeafe", "#dcfce7", "#fef3c7", "#f3e8ff", "#fce7f3"];
    function approxTokenize(str) {
      const toks = [];
      const re = /[\u4e00-\u9fff]|[A-Za-z]+|\d+|[^\sA-Za-z\d\u4e00-\u9fff]+|\s+/g;
      let m;
      while ((m = re.exec(str)) !== null) {
        const s = m[0];
        if (/^\s+$/.test(s)) continue;
        if (/^[A-Za-z]{6,}$/.test(s)) {
          toks.push(s.slice(0, Math.ceil(s.length / 2)), s.slice(Math.ceil(s.length / 2)));
        } else {
          toks.push(s);
        }
      }
      return toks;
    }

    function update() {
      const toks = approxTokenize(text);
      tokWrap.innerHTML = "";
      toks.forEach((t, i) => {
        tokWrap.appendChild(el("span", { class: "toy-tok", style: `background:${colors[i % colors.length]}` }, t));
      });
      const n = toks.length;
      const chars = text.length || 1;
      metrics.innerHTML = "";
      [
        ["字符数", `${text.length}`],
        ["估算 Token 数", `${n}`],
        ["字符/Token 比", (chars / Math.max(n, 1)).toFixed(2)],
        ["调用 1 万次输入成本（按 $0.15/1M）", `$${((n * 10000 / 1e6) * 0.15).toFixed(4)}`]
      ].forEach(([l, v]) => {
        metrics.appendChild(el("div", { class: "toy-metric" },
          el("div", { class: "toy-metric-label" }, l),
          el("div", { class: "toy-metric-val" }, v)
        ));
      });
    }
    update();
  });

  // 3.1 Messages 角色与 System Prompt 实验室
  register("ch03-role-sandbox", (root) => {
    const body = shell(root, {
      badge: "互动实验 3.1",
      title: "System Prompt 与 Messages 数组透视",
      subtitle: "切换不同人设的 System Prompt，观察同一用户提问在相同上下文结构下的输出差异"
    });
    const personas = [
      {
        name: "严谨代码审查员",
        sys: "你是资深 Python 架构师。只指出关键缺陷、给出修复代码，不超过 3 点。",
        reply: "1. 缺少超时参数 timeout，网络挂起会阻塞线程。\n2. 未捕获 APIStatusError。\n修复：client.chat.completions.create(..., timeout=30)。"
      },
      {
        name: "苏格拉底导师",
        sys: "你从不直接给答案，而是用启发式问题引导学习者自己发现问题。",
        reply: "如果远程 API 突然无响应，你觉得这段同步调用的代码会发生什么？我们可以用哪个参数限制等待时间？"
      },
      {
        name: "极简 JSON 接口",
        sys: "严格输出 JSON：{\"severity\":\"high|mid|low\",\"issue\":\"...\"}，禁止任何解释。",
        reply: "{\"severity\": \"high\", \"issue\": \"Missing request timeout and exception handling\"}"
      }
    ];
    let idx = 0;
    const row = el("div", { class: "toy-row" });
    const grid = el("div", { class: "toy-grid-2" });
    body.append(row, grid);

    function render() {
      row.innerHTML = "";
      personas.forEach((p, i) => {
        row.appendChild(el("button", { class: `toy-btn ${i === idx ? "active" : ""}`, onClick: () => { idx = i; render(); } }, p.name));
      });
      const p = personas[idx];
      const payload = [
        { role: "system", content: p.sys },
        { role: "user", content: "帮我看看这段 API 调用有没有问题：resp = client.chat.completions.create(model='qwen3:14b', messages=msgs)" }
      ];
      grid.innerHTML = "";
      grid.append(
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "实际发送的 messages[]"),
          el("pre", { class: "toy-code" }, JSON.stringify(payload, null, 2))
        ),
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "模型回复（role: assistant）", el("span", { class: "toy-pill info" }, p.name)),
          el("div", { class: "toy-step ok", style: "white-space:pre-wrap" }, p.reply),
          el("p", { class: "toy-note", style: "margin-top:8px" }, "关键点：LLM 本身无状态，所谓“人设”和“记忆”都依赖你每次请求重新传入完整 messages 数组。")
        )
      );
    }
    render();
  });

  // 3.2 上下文窗口截断策略模拟器
  register("ch03-truncation-sim", (root) => {
    const body = shell(root, {
      badge: "互动实验 3.2",
      title: "对话历史截断策略模拟器",
      subtitle: "当历史消息超过 Token 预算（1000 tokens）时，对比三种常见裁剪策略的保留效果"
    });
    const msgs = [
      { role: "system", text: "你是旅行顾问，用户预算 5000 元、偏好人文景点。", tok: 180 },
      { role: "user", text: "第1轮：我想去京都玩 4 天。", tok: 140 },
      { role: "assistant", text: "第1轮答：建议安排清水寺、伏见稻荷与岚山。", tok: 210 },
      { role: "user", text: "第2轮：我不吃生鱼片，晚餐推荐什么？", tok: 160 },
      { role: "assistant", text: "第2轮答：可以尝试京料理豆腐宴、拉面与和牛寿喜烧。", tok: 220 },
      { role: "user", text: "第3轮：帮我把上述行程整理成预算表。", tok: 190 },
      { role: "assistant", text: "第3轮答：交通 1200 + 住宿 2200 + 餐饮 1100...", tok: 240 }
    ];
    let strategy = "keep_system";
    const row = el("div", { class: "toy-row" });
    const barWrap = el("div");
    const list = el("div", { class: "toy-log" });
    body.append(row, barWrap, list);

    const strategies = [
      { id: "fifo", name: "简单截断（丢弃最早）" },
      { id: "keep_system", name: "保留 System + 最近对话" },
      { id: "summary", name: "旧对话摘要压缩" }
    ];

    function render() {
      row.innerHTML = "";
      strategies.forEach((s) => {
        row.appendChild(el("button", { class: `toy-btn ${s.id === strategy ? "active" : ""}`, onClick: () => { strategy = s.id; render(); } }, s.name));
      });
      const budget = 1000;
      let kept = [];
      let summaryNote = null;
      if (strategy === "fifo") {
        let sum = 0;
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (sum + msgs[i].tok <= budget) { kept.unshift(i); sum += msgs[i].tok; }
        }
      } else if (strategy === "keep_system") {
        let sum = msgs[0].tok;
        kept.push(0);
        const tail = [];
        for (let i = msgs.length - 1; i >= 1; i--) {
          if (sum + msgs[i].tok <= budget) { tail.unshift(i); sum += msgs[i].tok; }
        }
        kept = [0, ...tail];
      } else {
        kept = [0, 5, 6];
        summaryNote = { role: "system", text: "[历史摘要 120 tok] 用户计划京都 4 日游（预算 5000，偏人文，不吃生鱼片）。", tok: 120 };
      }

      const used = kept.reduce((a, i) => a + msgs[i].tok, 0) + (summaryNote ? summaryNote.tok : 0);
      const total = msgs.reduce((a, m) => a + m.tok, 0);
      barWrap.innerHTML = "";
      barWrap.append(
        el("div", { class: "toy-slider-label", style: "margin-bottom:4px" },
          el("span", null, `原始总计 ${total} tokens → 裁剪后 ${used} / ${budget} tokens`),
          el("strong", null, strategy === "fifo" ? "警告：System Prompt 被挤掉了！" : strategy === "keep_system" ? "人设保留，第 1-2 轮饮食偏好丢失" : "人设 + 关键事实全部保留")
        ),
        el("div", { class: "toy-bar-track" },
          el("div", { class: "toy-bar-seg", style: `width:${Math.min(100, (used / budget) * 100)}%;background:${strategy === "fifo" ? "#dc2626" : "#059669"}` })
        )
      );

      list.innerHTML = "";
      msgs.forEach((m, i) => {
        const alive = kept.includes(i);
        list.appendChild(el("div", { class: `toy-step ${alive ? (m.role === "system" ? "info" : "ok") : "dim"}` },
          el("span", { class: `toy-pill ${alive ? "ok" : "err"}` }, `${m.role} · ${m.tok}t`),
          m.text
        ));
        if (i === 0 && summaryNote) {
          list.appendChild(el("div", { class: "toy-step purple" },
            el("span", { class: "toy-pill purple" }, "summary · 120t"),
            summaryNote.text
          ));
        }
      });
    }
    render();
  });

  // 4.1 非流式 vs 流式输出体验对比器
  register("ch04-streaming-race", (root) => {
    const body = shell(root, {
      badge: "互动实验 4.1",
      title: "非流式（Blocking）vs 流式（SSE）延迟体验对比",
      subtitle: "同时发起一次长回复生成，直观感受 TTFT（首字延迟）对用户体验的巨大差异"
    });
    const fullText = "流式输出并不会减少模型的总生成时间，但它通过 Server-Sent Events 把原本需要等待数秒的黑屏变成几十毫秒即开始逐字呈现的实时反馈，这是生产级 Agent 必备的交互底座。";
    let timer = null;
    const ctrl = el("div", { class: "toy-row" });
    const grid = el("div", { class: "toy-grid-2" });
    body.append(ctrl, grid);

    const blockBox = el("div", { class: "toy-step warn", style: "min-height:88px" }, "点击“开始对比测试”观察两种模式的响应节奏。");
    const streamBox = el("div", { class: "toy-step ok", style: "min-height:88px" }, "点击“开始对比测试”观察两种模式的响应节奏。");
    const blockStat = el("span", { class: "toy-pill warn" }, "TTFT: --");
    const streamStat = el("span", { class: "toy-pill ok" }, "TTFT: --");

    grid.append(
      el("div", { class: "toy-card" }, el("div", { class: "toy-card-title" }, "非流式（stream=False）", blockStat), blockBox),
      el("div", { class: "toy-card" }, el("div", { class: "toy-card-title" }, "流式输出（stream=True）", streamStat), streamBox)
    );

    const runBtn = el("button", { class: "toy-btn primary", onClick: start }, "开始对比测试");
    ctrl.append(runBtn, el("span", { class: "toy-note" }, "模拟生成速率：约 28 字符/秒，总耗时约 2.8 秒"));

    function start() {
      if (timer) clearInterval(timer);
      let pos = 0;
      const t0 = performance.now();
      blockBox.textContent = "⏳ 正在等待完整响应返回（用户只能看转圈）...";
      streamBox.textContent = "";
      blockStat.textContent = "TTFT: 等待中...";
      streamStat.textContent = "TTFT: 0.12s";
      runBtn.disabled = true;

      timer = setInterval(() => {
        pos += 2;
        streamBox.textContent = fullText.slice(0, pos) + (pos < fullText.length ? "▍" : "");
        if (pos >= fullText.length) {
          clearInterval(timer);
          const total = ((performance.now() - t0) / 1000).toFixed(2);
          blockBox.textContent = fullText;
          blockStat.textContent = `TTFT: ${total}s（=总耗时）`;
          streamStat.textContent = `TTFT: 0.12s | 总耗时: ${total}s`;
          runBtn.disabled = false;
        }
      }, 65);
    }
  });

  // 4.2 指数退避重试与降级熔断模拟器
  register("ch04-retry-backoff", (root) => {
    const body = shell(root, {
      badge: "互动实验 4.2",
      title: "错误处理、指数退避重试与模型降级模拟器",
      subtitle: "注入不同类型的 API 故障，观察健壮 Agent 何时重试、何时快速失败、何时切换备用模型"
    });
    const scenarios = [
      {
        name: "429 限流（第 3 次恢复）",
        events: [
          { cls: "warn", tag: "Attempt 1", text: "收到 HTTP 429 RateLimitError（可重试）→ 等待 1.1s（2^0 + jitter）" },
          { cls: "warn", tag: "Attempt 2", text: "再次收到 429 → 等待 2.3s（2^1 + jitter）" },
          { cls: "ok", tag: "Attempt 3", text: "请求成功（200 OK），总计耗时 3.8s，用户无感知恢复。" }
        ]
      },
      {
        name: "401 鉴权错误（不可重试）",
        events: [
          { cls: "err", tag: "Attempt 1", text: "收到 HTTP 401 AuthenticationError（API Key 无效）。" },
          { cls: "info", tag: "Fail Fast", text: "归类为不可重试错误：立即中止并抛出明确提示，避免白白重试浪费时间。" }
        ]
      },
      {
        name: "503 主模型宕机（触发降级）",
        events: [
          { cls: "warn", tag: "Attempt 1", text: "主模型 gpt-4o 返回 503 → 等待 1.0s 重试" },
          { cls: "warn", tag: "Attempt 2", text: "主模型仍 503 → 等待 2.2s 重试" },
          { cls: "err", tag: "Attempt 3", text: "主模型连续 3 次失败，触发降级策略（Fallback）。" },
          { cls: "purple", tag: "Fallback", text: "自动切换至备用模型 qwen3:14b（本地 Ollama），返回成功响应并写入告警日志。" }
        ]
      }
    ];
    let idx = 0;
    const row = el("div", { class: "toy-row" });
    const log = el("div", { class: "toy-log" });
    body.append(row, log);

    function render() {
      row.innerHTML = "";
      scenarios.forEach((s, i) => {
        row.appendChild(el("button", { class: `toy-btn ${i === idx ? "active" : ""}`, onClick: () => { idx = i; render(); } }, s.name));
      });
      log.innerHTML = "";
      scenarios[idx].events.forEach((e) => {
        log.appendChild(el("div", { class: `toy-step ${e.cls}` }, el("span", { class: `toy-pill ${e.cls}` }, e.tag), e.text));
      });
    }
    render();
  });
})();
