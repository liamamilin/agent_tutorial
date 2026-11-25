(function () {
  const { register, shell, el } = window.AgentToys;

  // 5.1 Pydantic Schema 校验与自修复演练场
  register("ch05-schema-validator", (root) => {
    const body = shell(root, {
      badge: "互动实验 5.1",
      title: "Pydantic 结构化校验与错误回传修复",
      subtitle: "模拟 LLM 输出不同质量的 JSON，观察严格 Schema 校验如何拦下异常并引导模型自动修复"
    });
    const cases = [
      {
        name: "合法输出",
        raw: '{"city": "杭州", "days": 3, "budget": 2500}',
        ok: true,
        err: null,
        fixed: null
      },
      {
        name: "类型错误（days 为字符串）",
        raw: '{"city": "杭州", "days": "三天", "budget": 2500}',
        ok: false,
        err: "ValidationError: days -> Input should be a valid integer (got '三天')",
        fixed: '{"city": "杭州", "days": 3, "budget": 2500}'
      },
      {
        name: "缺失必填字段（缺 budget）",
        raw: '{"city": "杭州", "days": 3}',
        ok: false,
        err: "ValidationError: budget -> Field required",
        fixed: '{"city": "杭州", "days": 3, "budget": 3000}'
      },
      {
        name: "夹带 Markdown 废话",
        raw: '好的，这是结果：\n```json\n{"city": "杭州", "days": 3, "budget": 2500}\n```',
        ok: false,
        err: "JSONDecodeError: Expecting value at line 1 column 1（未开启 response_format=json_object）",
        fixed: '{"city": "杭州", "days": 3, "budget": 2500}'
      }
    ];
    let idx = 1;
    let repaired = false;
    const row = el("div", { class: "toy-row" });
    const out = el("div", { class: "toy-log" });
    body.append(row, out);

    function render() {
      row.innerHTML = "";
      cases.forEach((c, i) => {
        row.appendChild(el("button", { class: `toy-btn ${i === idx ? "active" : ""}`, onClick: () => { idx = i; repaired = false; render(); } }, c.name));
      });
      const c = cases[idx];
      out.innerHTML = "";
      out.appendChild(el("pre", { class: "toy-code" }, `// LLM 原始输出\n${c.raw}`));
      if (c.ok) {
        out.appendChild(el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "PASS"), "TripPlan(city='杭州', days=3, budget=2500) 校验通过，可直接交给下游函数使用。"));
      } else {
        out.appendChild(el("div", { class: "toy-step err" }, el("span", { class: "toy-pill err" }, "REJECT"), c.err));
        if (!repaired) {
          out.appendChild(el("button", { class: "toy-btn primary", onClick: () => { repaired = true; render(); } }, "将错误信息回传 LLM 触发自修复 →"));
        } else {
          out.appendChild(el("div", { class: "toy-step info" }, el("span", { class: "toy-pill info" }, "RETRY PROMPT"), `请修正上述报错并严格返回合法 JSON：${c.err}`));
          out.appendChild(el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "FIXED"), `二次输出校验通过：${c.fixed}`));
        }
      }
    }
    render();
  });

  // 5.2 Function Calling 协议路由模拟器
  register("ch05-fc-router", (root) => {
    const body = shell(root, {
      badge: "互动实验 5.2",
      title: "Function Calling 与 tool_choice 路由模拟器",
      subtitle: "组合不同用户提问与 tool_choice 策略，查看模型决定“直接回复”还是“发出 tool_calls”"
    });
    const queries = [
      { text: "北京今天天气怎么样？", needTool: true, fn: "get_weather", args: { city: "北京" }, direct: "我无法直接查看实时天气，请通过天气应用查询。" },
      { text: "用一句话解释什么是递归。", needTool: false, fn: "get_weather", args: { city: "未知" }, direct: "递归是函数直接或间接调用自身、将大问题拆解为同类小问题的求解方式。" }
    ];
    let qIdx = 0;
    let choice = "auto";
    const row = el("div", { class: "toy-row" });
    const box = el("div", { class: "toy-card" });
    body.append(row, box);

    function render() {
      row.innerHTML = "";
      queries.forEach((q, i) => {
        row.appendChild(el("button", { class: `toy-btn ${i === qIdx ? "active" : ""}`, onClick: () => { qIdx = i; render(); } }, q.text));
      });
      row.appendChild(el("select", { class: "toy-select", onChange: (e) => { choice = e.target.value; render(); } },
        [["auto", "tool_choice='auto'"], ["none", "tool_choice='none'"], ["required", "tool_choice='required'"]].map(([v, l]) =>
          el("option", { value: v, selected: v === choice }, l)
        )
      ));

      const q = queries[qIdx];
      const willCall = choice === "required" || (choice === "auto" && q.needTool);
      const result = willCall
        ? { finish_reason: "tool_calls", content: null, tool_calls: [{ id: "call_01", type: "function", function: { name: q.fn, arguments: JSON.stringify(q.args) } }] }
        : { finish_reason: "stop", content: q.direct, tool_calls: null };

      box.innerHTML = "";
      box.append(
        el("div", { class: "toy-card-title" },
          willCall ? "模型决定：发出结构化工具调用" : "模型决定：直接文本回复",
          el("span", { class: `toy-pill ${willCall ? "purple" : "ok"}` }, willCall ? "finish_reason: tool_calls" : "finish_reason: stop")
        ),
        el("pre", { class: "toy-code" }, JSON.stringify(result, null, 2)),
        choice === "required" && !q.needTool
          ? el("div", { class: "toy-step warn", style: "margin-top:8px" }, "注意：强行使用 required 会逼迫模型在不需要工具时也胡乱凑参数调用。")
          : null
      );
    }
    render();
  });

  // 6.1 ToolExecutor 工具注册与分发流水线
  register("ch06-tool-pipeline", (root) => {
    const body = shell(root, {
      badge: "互动实验 6.1",
      title: "ToolExecutor 工具注册表与调度流水线",
      subtitle: "开关不同工具的注册状态，运行“查成都天气并算3天住宿预算”，观察执行器如何动态响应"
    });
    const tools = [
      { id: "get_weather", name: "get_weather(city)", enabled: true, desc: "查询实时天气" },
      { id: "calculator", name: "calculator(expr)", enabled: true, desc: "精确数学计算" },
      { id: "search_hotel", name: "search_hotel(city)", enabled: false, desc: "查询酒店均价" }
    ];
    const toggles = el("div", { class: "toy-row" });
    const trace = el("div", { class: "toy-log" });
    body.append(toggles, trace);

    function render() {
      toggles.innerHTML = "";
      tools.forEach((t) => {
        toggles.appendChild(el("button", {
          class: `toy-btn ${t.enabled ? "active" : ""}`,
          onClick: () => { t.enabled = !t.enabled; render(); }
        }, `${t.enabled ? "✓" : "×"} ${t.name}`));
      });

      const activeNames = tools.filter((t) => t.enabled).map((t) => t.id);
      const hasW = activeNames.includes("get_weather");
      const hasC = activeNames.includes("calculator");
      const hasH = activeNames.includes("search_hotel");

      trace.innerHTML = "";
      trace.append(
        el("div", { class: "toy-step info" }, el("span", { class: "toy-pill info" }, "1. 注册表注入"), `当前已注册工具：[${activeNames.join(", ") || "无"}]`),
        hasW
          ? el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "2. 调用 get_weather"), "ToolExecutor 命中 get_weather('成都') → 返回：多云 19°C。")
          : el("div", { class: "toy-step err" }, el("span", { class: "toy-pill err" }, "2. 天气缺失"), "未注册 get_weather，Agent 无法获取实时天气，只能如实告知用户。"),
        hasH
          ? el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "3. 调用 search_hotel"), "命中 search_hotel('成都') → 返回：舒适型酒店均价 380 元/晚。")
          : el("div", { class: "toy-step warn" }, el("span", { class: "toy-pill warn" }, "3. 酒店均价估算"), "未注册 search_hotel，只能按经验假设 400 元/晚继续估算。"),
        hasC
          ? el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "4. 调用 calculator"), `calculator('${hasH ? 380 : 400} * 3') → 精确结果：${(hasH ? 380 : 400) * 3} 元。`)
          : el("div", { class: "toy-step warn" }, el("span", { class: "toy-pill warn" }, "4. 无计算器"), "未注册 calculator，只能由模型心算（复杂账单存在出错风险）。")
      );
    }
    render();
  });

  // 6.2 工具安全沙箱与风险拦截器
  register("ch06-tool-safety", (root) => {
    const body = shell(root, {
      badge: "互动实验 6.2",
      title: "工具安全护栏演练：如果缺少校验会发生什么？",
      subtitle: "开关安全护栏，测试 3 类典型 Agent 工具攻击/失控场景"
    });
    let guardOn = true;
    const tests = [
      {
        attack: "路径穿越：read_file('../../.env')",
        safeMsg: "已拦截：路径超出允许工作目录白名单，拒绝读取 .env 密钥文件。",
        unsafeMsg: "危险泄漏：工具直接把 OPENAI_API_KEY 原文返回给了对话上下文！"
      },
      {
        attack: "代码注入：calculator(\"__import__('os').system('rm -rf /')\")",
        safeMsg: "已拦截：使用 AST 白名单求值替代 eval()，检测到非法函数调用直接拒绝。",
        unsafeMsg: "严重漏洞：eval() 直接执行了系统命令！"
      },
      {
        attack: "死循环调用：连续 25 次重复调用 search('最新新闻')",
        safeMsg: "已熔断：触发 max_steps=8 步数上限，强制终止循环并返回当前已收集信息。",
        unsafeMsg: "预算失控：Agent 陷入死循环，持续消耗 Token 直到额度耗尽。"
      }
    ];
    const row = el("div", { class: "toy-row" });
    const log = el("div", { class: "toy-log" });
    body.append(row, log);

    function render() {
      row.innerHTML = "";
      row.append(
        el("button", { class: `toy-btn ${guardOn ? "active" : ""}`, onClick: () => { guardOn = true; render(); } }, "安全护栏：开启（推荐）"),
        el("button", { class: `toy-btn ${!guardOn ? "active" : ""}`, onClick: () => { guardOn = false; render(); } }, "安全护栏：关闭（裸奔）")
      );
      log.innerHTML = "";
      tests.forEach((t) => {
        log.appendChild(el("div", { class: `toy-step ${guardOn ? "ok" : "err"}` },
          el("span", { class: `toy-pill ${guardOn ? "ok" : "err"}` }, guardOn ? "BLOCKED" : "EXPOSED"),
          el("strong", null, t.attack),
          el("div", { style: "margin-top:3px" }, guardOn ? t.safeMsg : t.unsafeMsg)
        ));
      });
    }
    render();
  });

  // 7.1 三大推理范式对比演练场
  register("ch07-paradigm-compare", (root) => {
    const body = shell(root, {
      badge: "互动实验 7.1",
      title: "ReAct vs Plan-and-Solve vs Reflection 演练对比",
      subtitle: "针对同一复杂任务，切换三种推理范式并对比其执行步骤、LLM 调用次数与适用场景"
    });
    const modes = {
      react: {
        name: "ReAct（边想边做）",
        calls: "4 次 LLM + 2 次工具",
        best: "探索型、信息动态变化任务",
        steps: [
          ["info", "Thought 1", "先查目标城市的实时天气，再决定室内还是室外行程。"],
          ["purple", "Action 1", "get_weather('杭州') → 观察：小雨 16°C。"],
          ["info", "Thought 2", "下雨了！临时调整方向，改为搜索室内博物馆与茶馆。"],
          ["ok", "Answer", "输出雨天版杭州一日室内攻略。"]
        ]
      },
      plan: {
        name: "Plan-and-Solve（先规划后执行）",
        calls: "1 次规划 + 3 次子步骤",
        best: "结构清晰、多步骤拆解任务",
        steps: [
          ["purple", "Planner", "一次性制定蓝图：[1] 查交通 [2] 排上午/下午景点 [3] 汇总预算表。"],
          ["info", "Step 1", "执行子任务 1：高铁往返 146 元。"],
          ["info", "Step 2", "执行子任务 2：西湖博物馆 + 中国茶叶博物馆。"],
          ["ok", "Step 3", "按蓝图汇总完整预算与时间表（若中途遇突发雨天需重规划）。"]
        ]
      },
      reflect: {
        name: "Reflection（生成-反思-迭代）",
        calls: "3 次 LLM（初稿→评审→改稿）",
        best: "代码生成、写作、高准确率交付",
        steps: [
          ["info", "Draft", "生成第一版攻略（但遗漏了周一博物馆闭馆的限制）。"],
          ["warn", "Critique", "自我审查发现问题：目标日期是周一，两家博物馆均闭馆！"],
          ["ok", "Refine", "修正为周一开放的灵隐寺与南宋御街室内茶空间，质量分 62 → 92。"]
        ]
      }
    };
    let cur = "react";
    const row = el("div", { class: "toy-row" });
    const meta = el("div", { class: "toy-metric-grid" });
    const log = el("div", { class: "toy-log" });
    body.append(row, meta, log);

    function render() {
      row.innerHTML = "";
      Object.entries(modes).forEach(([k, m]) => {
        row.appendChild(el("button", { class: `toy-btn ${k === cur ? "active" : ""}`, onClick: () => { cur = k; render(); } }, m.name));
      });
      const m = modes[cur];
      meta.innerHTML = "";
      [["推理范式", m.name], ["典型调用开销", m.calls], ["最适用场景", m.best]].forEach(([l, v]) => {
        meta.appendChild(el("div", { class: "toy-metric" }, el("div", { class: "toy-metric-label" }, l), el("div", { class: "toy-metric-val", style: "font-size:0.86rem" }, v)));
      });
      log.innerHTML = "";
      m.steps.forEach(([cls, tag, text]) => {
        log.appendChild(el("div", { class: `toy-step ${cls}` }, el("span", { class: `toy-pill ${cls}` }, tag), text));
      });
    }
    render();
  });

  // 7.2 Reflection 自我反思迭代改进器
  register("ch07-reflection-loop", (root) => {
    const body = shell(root, {
      badge: "互动实验 7.2",
      title: "Reflection 迭代收敛曲线模拟器",
      subtitle: "逐轮推进“生成 → 评审 → 修正”，观察代码质量分与 Token 成本的边际收益"
    });
    const rounds = [
      { r: 1, score: 58, tokens: 420, code: "def fib(n):\n    return fib(n-1) + fib(n-2)", critique: "缺少基准终止条件（n<=1），直接运行会触发 RecursionError！" },
      { r: 2, score: 82, tokens: 890, code: "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)", critique: "功能正确但时间复杂度 O(2^n)，n=40 时极慢，且未处理负数输入。" },
      { r: 3, score: 96, tokens: 1380, code: "def fib(n: int) -> int:\n    if n < 0: raise ValueError('n >= 0')\n    a, b = 0, 1\n    for _ in range(n): a, b = b, a + b\n    return a", critique: "O(n) 时间、O(1) 空间、含类型注解与边界校验，达到 90 分阈值，提前终止！" }
    ];
    let idx = 0;
    const row = el("div", { class: "toy-row" });
    const metrics = el("div", { class: "toy-metric-grid" });
    const codeBox = el("pre", { class: "toy-code" });
    const note = el("div");
    body.append(row, metrics, codeBox, note);

    function render() {
      row.innerHTML = "";
      rounds.forEach((rd, i) => {
        row.appendChild(el("button", { class: `toy-btn ${i === idx ? "active" : ""}`, onClick: () => { idx = i; render(); } }, `第 ${rd.r} 轮`));
      });
      const rd = rounds[idx];
      metrics.innerHTML = "";
      [["当前轮次", `Round ${rd.r}/3`], ["质量评分", `${rd.score} / 100`], ["累计 Token", `${rd.tokens}`]].forEach(([l, v]) => {
        metrics.appendChild(el("div", { class: "toy-metric" }, el("div", { class: "toy-metric-label" }, l), el("div", { class: "toy-metric-val" }, v)));
      });
      codeBox.textContent = rd.code;
      note.innerHTML = "";
      note.appendChild(el("div", { class: `toy-step ${rd.score >= 90 ? "ok" : "warn"}` },
        el("span", { class: `toy-pill ${rd.score >= 90 ? "ok" : "warn"}` }, rd.score >= 90 ? "PASS >= 90" : "CRITIQUE"),
        rd.critique
      ));
    }
    render();
  });

  // 8.1 HelloAgents 积木式架构拼装台
  register("ch08-framework-blocks", (root) => {
    const body = shell(root, {
      badge: "互动实验 8.1",
      title: "HelloAgents 积木式框架拼装台",
      subtitle: "自由勾选框架模块，实时查看组合后的 Agent 能力与最简装配代码"
    });
    const mods = [
      { id: "llm", name: "HelloAgentsLLM（核心必选）", locked: true, on: true },
      { id: "tools", name: "ToolRegistry（工具插件）", locked: false, on: true },
      { id: "react", name: "ReActAgent（多步推理）", locked: false, on: true },
      { id: "memory", name: "MemoryManager（长期记忆）", locked: false, on: false }
    ];
    const row = el("div", { class: "toy-row" });
    const flow = el("div", { class: "toy-step info" });
    const code = el("pre", { class: "toy-code" });
    body.append(row, flow, code);

    function render() {
      row.innerHTML = "";
      mods.forEach((m) => {
        row.appendChild(el("button", {
          class: `toy-btn ${m.on ? "active" : ""}`,
          disabled: m.locked,
          onClick: () => { m.on = !m.on; render(); }
        }, `${m.on ? "✓" : "+"} ${m.name}`));
      });
      const on = (id) => mods.find((m) => m.id === id).on;
      const chain = ["User Input", on("memory") ? "Memory Recall" : null, on("react") ? "ReAct Loop" : "Single LLM Call", on("tools") ? "ToolRegistry" : null, "Final Answer"].filter(Boolean);
      flow.textContent = `当前数据流：${chain.join("  →  ")}`;

      const clsName = on("react") ? "ReActAgent" : "SimpleAgent";
      const lines = [
        `from hello_agents import HelloAgentsLLM, ${clsName}` + (on("tools") ? ", ToolRegistry" : ""),
        `llm = HelloAgentsLLM()`,
        on("tools") ? `tools = ToolRegistry().register(get_weather, calculator)` : null,
        `agent = ${clsName}(`,
        `    name="助手",`,
        `    llm=llm,`,
        on("tools") ? `    tool_registry=tools,` : null,
        on("memory") ? `    memory_enabled=True,` : null,
        `)`,
        `print(agent.run("帮我规划杭州周末行程"))`
      ].filter(Boolean).join("\n");
      code.textContent = lines;
    }
    render();
  });

  // 8.2 Agent 生命周期 Hook 追踪器
  register("ch08-lifecycle-hooks", (root) => {
    const body = shell(root, {
      badge: "互动实验 8.2",
      title: "框架生命周期 Hook 执行顺序追踪",
      subtitle: "理解为什么成熟框架要提供 Hook / Callback：在不改核心循环的前提下插入日志、计费与审计"
    });
    const hooks = [
      { id: "log", name: "日志记录 Hook", on: true },
      { id: "cost", name: "Token 计费 Hook", on: true },
      { id: "audit", name: "敏感词审计 Hook", on: false }
    ];
    const row = el("div", { class: "toy-row" });
    const log = el("div", { class: "toy-log" });
    body.append(row, log);

    function render() {
      row.innerHTML = "";
      hooks.forEach((h) => {
        row.appendChild(el("button", { class: `toy-btn ${h.on ? "active" : ""}`, onClick: () => { h.on = !h.on; render(); } }, `${h.on ? "✓" : "+"} ${h.name}`));
      });
      const on = (id) => hooks.find((h) => h.id === id).on;
      const events = [
        on("log") ? ["info", "on_run_start", "记录 trace_id=tr_9021 与用户输入长度"] : null,
        on("audit") ? ["warn", "before_llm", "扫描输入未发现密钥或敏感信息，放行"] : null,
        ["purple", "core.llm_call", "核心循环调用 LLM，返回 tool_call: get_weather"],
        on("cost") ? ["ok", "after_llm", "累计 prompt=128t, completion=42t（预估 $0.0001）"] : null,
        ["purple", "core.tool_exec", "核心循环执行 get_weather('上海')"],
        on("log") ? ["info", "on_run_end", "写入耗时 1.42s、状态 SUCCESS 至可观测面板"] : null
      ].filter(Boolean);
      log.innerHTML = "";
      events.forEach(([cls, tag, text]) => {
        log.appendChild(el("div", { class: `toy-step ${cls}` }, el("span", { class: `toy-pill ${cls}` }, tag), text));
      });
    }
    render();
  });
})();
