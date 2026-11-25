(function () {
  const { register, shell, el } = window.AgentToys;

  // 9.1 三层记忆架构路由器
  register("ch09-memory-triad", (root) => {
    const body = shell(root, {
      badge: "互动实验 9.1",
      title: "三层记忆架构路由器（工作 / 情景 / 语义）",
      subtitle: "点击不同用户输入，观察 MemoryManager 如何把信息分类写入对应的记忆层"
    });
    const inputs = [
      { text: "“帮我算一下 238 × 17 等于多少”", layer: "working", reason: "仅当前会话临时计算，任务结束即可丢弃，不污染长期记忆。" },
      { text: "“上周五我和张总开会，确定了 Q3 预算上限是 50 万”", layer: "episodic", reason: "带有明确时间、人物和事件脉络，写入情景记忆（Episodic Memory）。" },
      { text: "“我叫林米，对花生严重过敏，写代码偏好 Python 类型注解”", layer: "semantic", reason: "长期稳定的个人事实与偏好，写入语义记忆（Semantic Memory），跨会话持久生效。" }
    ];
    const state = { working: ["当前任务上下文（TTL=本轮对话）"], episodic: [], semantic: [] };
    const row = el("div", { class: "toy-row" });
    const info = el("div");
    const grid = el("div", { class: "toy-grid-3" });
    body.append(row, info, grid);

    function feed(item) {
      if (!state[item.layer].includes(item.text)) state[item.layer].push(item.text);
      info.innerHTML = "";
      info.appendChild(el("div", { class: "toy-step info" }, el("span", { class: "toy-pill info" }, `路由至 ${item.layer.toUpperCase()}`), item.reason));
      renderCols();
    }

    inputs.forEach((item) => {
      row.appendChild(el("button", { class: "toy-btn", onClick: () => feed(item) }, `输入：${item.text.slice(0, 16)}…`));
    });
    row.appendChild(el("button", { class: "toy-btn", onClick: () => { state.working = ["当前任务上下文（TTL=本轮对话）"]; state.episodic = []; state.semantic = []; info.innerHTML = ""; renderCols(); } }, "清空"));

    function renderCols() {
      grid.innerHTML = "";
      [
        ["工作记忆 Working", "warn", state.working],
        ["情景记忆 Episodic", "purple", state.episodic],
        ["语义记忆 Semantic", "ok", state.semantic]
      ].forEach(([title, cls, items]) => {
        grid.appendChild(el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, title, el("span", { class: `toy-pill ${cls}` }, `${items.length} 条`)),
          items.length
            ? el("div", { class: "toy-log" }, items.map((t) => el("div", { class: `toy-step ${cls}` }, t)))
            : el("p", { class: "toy-note" }, "暂无记录，点击上方示例写入")
        ));
      });
    }
    renderCols();
  });

  // 9.2 艾宾浩斯遗忘曲线与记忆衰减调参器
  register("ch09-ebbinghaus-decay", (root) => {
    const body = shell(root, {
      badge: "互动实验 9.2",
      title: "记忆衰减与强化（遗忘曲线）调参器",
      subtitle: "拖动经过天数并尝试点击“触发回忆”，观察不同重要性记忆的留存率变化（低于 25% 触发淘汰）"
    });
    let days = 7;
    let boost = 0;
    const memories = [
      { name: "随口一问：今天星期几", imp: 0.25, baseHalf: 3 },
      { name: "会议纪要：上周需求评审", imp: 0.65, baseHalf: 14 },
      { name: "核心偏好：用户对花生过敏", imp: 0.98, baseHalf: 90 }
    ];
    const ctrl = el("div", { class: "toy-row" });
    const list = el("div", { class: "toy-log" });
    body.append(ctrl, list);

    function render() {
      ctrl.innerHTML = "";
      ctrl.append(
        el("div", { class: "toy-slider-group" },
          el("div", { class: "toy-slider-label" }, el("span", null, "已过去天数"), el("strong", null, `${days} 天`)),
          el("input", { type: "range", min: "0", max: "60", step: "1", value: days, onInput: (e) => { days = parseInt(e.target.value, 10); render(); } })
        ),
        el("button", { class: "toy-btn primary", onClick: () => { boost += 1; render(); } }, `模拟被检索强化 (+${boost} 次)`),
        el("button", { class: "toy-btn", onClick: () => { days = 7; boost = 0; render(); } }, "重置")
      );
      list.innerHTML = "";
      memories.forEach((m) => {
        const halfLife = m.baseHalf * (1 + boost * 0.45);
        const score = Math.min(1, m.imp * Math.exp(-days / halfLife) + (1 - Math.exp(-boost * 0.25)) * 0.15);
        const pct = Math.round(score * 100);
        const evicted = pct < 25;
        list.appendChild(el("div", { class: `toy-step ${evicted ? "dim" : pct > 60 ? "ok" : "warn"}` },
          el("div", { class: "toy-slider-label", style: "margin-bottom:4px" },
            el("span", null, `${m.name}（重要性 ${m.imp}）`),
            el("strong", null, evicted ? `${pct}% · 已遗忘淘汰` : `${pct}% · 保留中`)
          ),
          el("div", { class: "toy-bar-track" },
            el("div", { class: "toy-bar-seg", style: `width:${pct}%;background:${evicted ? "#dc2626" : pct > 60 ? "#059669" : "#d97706"}` })
          )
        ));
      });
    }
    render();
  });

  // 10.1 文档切分策略实验台
  register("ch10-chunking-lab", (root) => {
    const body = shell(root, {
      badge: "互动实验 10.1",
      title: "RAG 文档切分实验台（Chunk Size & Overlap）",
      subtitle: "调节块大小与重叠长度，观察长文档如何被切分以及重叠区如何防止语义被拦腰截断"
    });
    const doc = "RAG（检索增强生成）的核心流程分为离线索引与在线检索两阶段。离线阶段先加载文档，再按固定长度或语义边界切分为多个 Chunk，并计算向量存入索引库。在线阶段将用户问题向量化后检索 Top-K 相关片段，最后把这些片段拼入 Prompt，让模型基于真实依据生成回答，从而显著降低知识幻觉。";
    let size = 55;
    let overlap = 15;
    const ctrl = el("div", { class: "toy-row" });
    const out = el("div", { class: "toy-log" });
    body.append(ctrl, out);

    function render() {
      if (overlap >= size) overlap = Math.max(0, size - 10);
      ctrl.innerHTML = "";
      ctrl.append(
        el("div", { class: "toy-slider-group" },
          el("div", { class: "toy-slider-label" }, el("span", null, "chunk_size（字符）"), el("strong", null, String(size))),
          el("input", { type: "range", min: "30", max: "110", step: "5", value: size, onInput: (e) => { size = parseInt(e.target.value, 10); render(); } })
        ),
        el("div", { class: "toy-slider-group" },
          el("div", { class: "toy-slider-label" }, el("span", null, "chunk_overlap（重叠字符）"), el("strong", null, String(overlap))),
          el("input", { type: "range", min: "0", max: "40", step: "5", value: overlap, onInput: (e) => { overlap = parseInt(e.target.value, 10); render(); } })
        )
      );

      const chunks = [];
      const step = Math.max(10, size - overlap);
      for (let i = 0; i < doc.length; i += step) {
        chunks.push({ start: i, text: doc.slice(i, i + size) });
        if (i + size >= doc.length) break;
      }
      out.innerHTML = "";
      out.appendChild(el("p", { class: "toy-note" }, `原文 ${doc.length} 字 → 共切分为 ${chunks.length} 个 Chunk（重叠 ${overlap} 字）`));
      chunks.forEach((c, idx) => {
        out.appendChild(el("div", { class: "toy-step info" },
          el("span", { class: "toy-pill info" }, `Chunk #${idx + 1} [${c.start}:${c.start + c.text.length}]`),
          c.text
        ));
      });
    }
    render();
  });

  // 10.2 TF-IDF 检索与 Top-K 排序器
  register("ch10-tfidf-retriever", (root) => {
    const body = shell(root, {
      badge: "互动实验 10.2",
      title: "实时 TF-IDF 向量检索与 Top-K 过滤",
      subtitle: "输入或选择查询词，浏览器端实时计算余弦相似度并筛选注入 Prompt 的上下文片段"
    });
    const docs = [
      { id: "D1", text: "ReAct 范式通过 Thought-Action-Observation 循环交替推理与工具调用。" },
      { id: "D2", text: "RAG 通过文档切分、向量检索与 Top-K 片段注入来减少大模型幻觉。" },
      { id: "D3", text: "Function Calling 使用 JSON Schema 约束工具参数，比正则解析更可靠。" },
      { id: "D4", text: "艾宾浩斯遗忘曲线常用于长期记忆系统的权重衰减与淘汰策略。" }
    ];
    let query = "RAG 怎么减少幻觉";
    let topK = 2;
    const row = el("div", { class: "toy-row" });
    const list = el("div", { class: "toy-log" });
    body.append(row, list);

    function grams(s) {
      const clean = s.toLowerCase().replace(/[^\u4e00-\u9fffa-z0-9]/g, "");
      const arr = [];
      for (let i = 0; i < clean.length; i++) {
        arr.push(clean[i]);
        if (i + 1 < clean.length) arr.push(clean.slice(i, i + 2));
      }
      return arr;
    }
    function sim(a, b) {
      const ga = grams(a), gb = grams(b);
      const ca = {}, cb = {};
      ga.forEach((x) => ca[x] = (ca[x] || 0) + 1);
      gb.forEach((x) => cb[x] = (cb[x] || 0) + 1);
      let dot = 0, na = 0, nb = 0;
      Object.keys(ca).forEach((k) => { na += ca[k] * ca[k]; if (cb[k]) dot += ca[k] * cb[k]; });
      Object.keys(cb).forEach((k) => { nb += cb[k] * cb[k]; });
      return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
    }

    function render() {
      row.innerHTML = "";
      const inp = el("input", { class: "toy-input", style: "flex:1;min-width:180px", value: query, onInput: (e) => { query = e.target.value; update(); } });
      const sel = el("select", { class: "toy-select", onChange: (e) => { topK = parseInt(e.target.value, 10); update(); } },
        [1, 2, 3].map((k) => el("option", { value: k, selected: k === topK }, `Top-K = ${k}`))
      );
      row.append(inp, sel);
      ["RAG 怎么减少幻觉", "ReAct 工具调用循环", "记忆遗忘衰减"].forEach((q) => {
        row.appendChild(el("button", { class: "toy-btn", onClick: () => { query = q; inp.value = q; update(); } }, q));
      });
      update();
    }

    function update() {
      const ranked = docs.map((d) => ({ ...d, score: sim(query, d.text) })).sort((a, b) => b.score - a.score);
      list.innerHTML = "";
      ranked.forEach((d, i) => {
        const picked = i < topK;
        list.appendChild(el("div", { class: `toy-step ${picked ? "ok" : "dim"}` },
          el("span", { class: `toy-pill ${picked ? "ok" : ""}` }, `${d.id} · score=${d.score.toFixed(3)}${picked ? " · 注入 Prompt" : ""}`),
          d.text
        ));
      });
    }
    render();
  });

  // 11.1 Token 预算分配仪表盘
  register("ch11-token-budget", (root) => {
    const body = shell(root, {
      badge: "互动实验 11.1",
      title: "上下文窗口 Token 预算分配仪表盘（总容量 8,000）",
      subtitle: "调整各模块占用的 Token，观察上下文窗口如何被瓜分以及超限时应优先压缩哪一部分"
    });
    const parts = [
      { key: "sys", label: "System + Tools Schema", val: 1400, max: 3000, color: "#2563eb" },
      { key: "rag", label: "RAG 检索片段", val: 2200, max: 4500, color: "#7c3aed" },
      { key: "hist", label: "多轮对话历史", val: 2400, max: 5000, color: "#059669" },
      { key: "out", label: "预留输出空间（max_tokens）", val: 1200, max: 3000, color: "#d97706" }
    ];
    const limit = 8000;
    const bar = el("div", { class: "toy-bar-track", style: "height:18px" });
    const status = el("div");
    const sliders = el("div", { class: "toy-grid-2" });
    body.append(status, bar, sliders);

    function render() {
      const total = parts.reduce((a, p) => a + p.val, 0);
      const over = total > limit;
      status.innerHTML = "";
      status.appendChild(el("div", { class: `toy-step ${over ? "err" : "ok"}` },
        el("span", { class: `toy-pill ${over ? "err" : "ok"}` }, `${total} / ${limit} tokens`),
        over
          ? `超出预算 ${total - limit} tokens！建议优先压缩“多轮对话历史”或减少 RAG Top-K，切勿挤占 System 与输出预留。`
          : `预算健康，剩余可用余量 ${limit - total} tokens。`
      ));
      bar.innerHTML = "";
      parts.forEach((p) => {
        bar.appendChild(el("div", { class: "toy-bar-seg", style: `width:${Math.min(100, (p.val / Math.max(limit, total)) * 100)}%;background:${p.color}` }));
      });
      sliders.innerHTML = "";
      parts.forEach((p) => {
        sliders.appendChild(el("div", { class: "toy-card" },
          el("div", { class: "toy-slider-label" }, el("span", null, p.label), el("strong", null, `${p.val} t`)),
          el("input", { type: "range", min: "200", max: String(p.max), step: "100", value: p.val, style: "width:100%", onInput: (e) => { p.val = parseInt(e.target.value, 10); render(); } })
        ));
      });
    }
    render();
  });

  // 11.2 Prompt Prefix Caching 命中率模拟器
  register("ch11-kv-cache", (root) => {
    const body = shell(root, {
      badge: "互动实验 11.2",
      title: "Prompt 前缀缓存（KV Cache）顺序优化对比",
      subtitle: "对比“把动态时间/用户信息放最前”与“静态前缀置顶”，看看缓存命中率与成本差距"
    });
    let good = true;
    const row = el("div", { class: "toy-row" });
    const blocks = el("div", { class: "toy-log" });
    const metrics = el("div", { class: "toy-metric-grid" });
    body.append(row, blocks, metrics);

    function render() {
      row.innerHTML = "";
      row.append(
        el("button", { class: `toy-btn ${good ? "active" : ""}`, onClick: () => { good = true; render(); } }, "最佳实践：静态内容置顶"),
        el("button", { class: `toy-btn ${!good ? "active" : ""}`, onClick: () => { good = false; render(); } }, "反面案例：动态时间戳放开头")
      );
      const seq = good
        ? [
            { hit: true, name: "1. 固定 System Prompt（1200t）", note: "KV Cache 命中" },
            { hit: true, name: "2. 固定 Tools Schema（1800t）", note: "KV Cache 命中" },
            { hit: false, name: "3. 当前时间戳 + 用户提问（200t）", note: "仅计算尾部增量" }
          ]
        : [
            { hit: false, name: "1. 当前时间戳 23:41:09（20t）", note: "首段变动 → 后续缓存全部失效！" },
            { hit: false, name: "2. 固定 System Prompt（1200t）", note: "被迫全量重算" },
            { hit: false, name: "3. 固定 Tools Schema（1800t）", note: "被迫全量重算" }
          ];
      blocks.innerHTML = "";
      seq.forEach((b) => {
        blocks.appendChild(el("div", { class: `toy-step ${b.hit ? "ok" : "err"}` },
          el("span", { class: `toy-pill ${b.hit ? "ok" : "err"}` }, b.hit ? "CACHE HIT" : "RECOMPUTE"),
          `${b.name} — ${b.note}`
        ));
      });
      metrics.innerHTML = "";
      [
        ["前缀缓存命中率", good ? "93.8%" : "0.0%"],
        ["相对输入成本", good ? "约 0.25x" : "1.00x"],
        ["首字延迟（TTFT）", good ? "大幅降低" : "每次全量 Prefill"]
      ].forEach(([l, v]) => {
        metrics.appendChild(el("div", { class: "toy-metric" }, el("div", { class: "toy-metric-label" }, l), el("div", { class: "toy-metric-val" }, v)));
      });
    }
    render();
  });

  // 12.1 多智能体协作拓扑模拟器
  register("ch12-topology-sim", (root) => {
    const body = shell(root, {
      badge: "互动实验 12.1",
      title: "多智能体协作拓扑对比（流水线 / 辩论评审 / 主管路由）",
      subtitle: "选择不同协作拓扑，观察 PM、Coder、Reviewer 三个 Agent 如何传递消息与终止"
    });
    const topos = {
      seq: {
        name: "顺序流水线（Sequential）",
        steps: [
          ["info", "PM Agent", "拆解需求为 3 条验收标准 → 交给 Coder"],
          ["purple", "Coder Agent", "按验收标准实现核心代码 → 交给 QA"],
          ["ok", "QA Agent", "补充单元测试并输出最终交付件（终止）"]
        ]
      },
      debate: {
        name: "生成-评审循环（GroupChat）",
        steps: [
          ["purple", "Coder Agent", "提交第 1 版实现"],
          ["warn", "Reviewer Agent", "指出并发竞态隐患，要求修改（未满足 TERMINATE）"],
          ["purple", "Coder Agent", "加锁修复并补充压测"],
          ["ok", "Reviewer Agent", "复核通过，输出 TERMINATE 结束对话"]
        ]
      },
      manager: {
        name: "主管路由（Manager-Worker）",
        steps: [
          ["info", "Manager Agent", "分析任务：并行派发“前端原型”给 UI Agent、“接口开发”给 API Agent"],
          ["purple", "Workers 并行", "UI Agent 与 API Agent 各自在独立上下文中完成子任务"],
          ["ok", "Manager Agent", "汇总两份结果做集成校验并向用户汇报"]
        ]
      }
    };
    let cur = "seq";
    const row = el("div", { class: "toy-row" });
    const log = el("div", { class: "toy-log" });
    body.append(row, log);

    function render() {
      row.innerHTML = "";
      Object.entries(topos).forEach(([k, t]) => {
        row.appendChild(el("button", { class: `toy-btn ${k === cur ? "active" : ""}`, onClick: () => { cur = k; render(); } }, t.name));
      });
      log.innerHTML = "";
      topos[cur].steps.forEach(([cls, tag, text], i) => {
        log.appendChild(el("div", { class: `toy-step ${cls}` }, el("span", { class: `toy-pill ${cls}` }, `${i + 1}. ${tag}`), text));
      });
    }
    render();
  });

  // 12.2 Agent 交接上下文裁剪器
  register("ch12-handoff-inspector", (root) => {
    const body = shell(root, {
      badge: "互动实验 12.2",
      title: "多 Agent 交接（Handoff）：全量转发 vs 结构化摘要",
      subtitle: "理解为什么多智能体系统不能把上游所有原始聊天记录直接塞给下游 Agent"
    });
    let mode = "summary";
    const row = el("div", { class: "toy-row" });
    const box = el("div", { class: "toy-log" });
    body.append(row, box);

    function render() {
      row.innerHTML = "";
      row.append(
        el("button", { class: `toy-btn ${mode === "full" ? "active" : ""}`, onClick: () => { mode = "full"; render(); } }, "全量转发上游历史"),
        el("button", { class: `toy-btn ${mode === "summary" ? "active" : ""}`, onClick: () => { mode = "summary"; render(); } }, "结构化 Handoff 契约（推荐）")
      );
      box.innerHTML = "";
      if (mode === "full") {
        box.append(
          el("div", { class: "toy-step err" }, el("span", { class: "toy-pill err" }, "4,800 tokens"), "把 PM 与用户来回试探的 18 轮废话和被否决的旧方案全部发给 Coder。"),
          el("div", { class: "toy-step warn" }, "风险：Coder 容易被旧方案干扰，产生“需求幻觉”，且每多一个 Agent 成本呈平方级膨胀。")
        );
      } else {
        box.append(
          el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "320 tokens"), "仅移交结构化 JSON：{goal, constraints, acceptance_criteria, artifacts}。"),
          el("div", { class: "toy-step info" }, "收益：上下文降噪 93%，职责边界清晰，下游执行准确率显著提升。")
        );
      }
    }
    render();
  });

  // 13.1 Agent 评估指标矩阵
  register("ch13-eval-dashboard", (root) => {
    const body = shell(root, {
      badge: "互动实验 13.1",
      title: "Agent 版本评估对比矩阵（准确率 vs 延迟 vs 成本）",
      subtitle: "切换不同演进版本的 Agent，观察工程优化中的经典“不可能三角”权衡"
    });
    const versions = [
      { name: "v1 基础对话 Agent", pass: 52, tool: 0, lat: "1.1s", cost: "$0.0004", note: "最快最省，但遇到实时数据与复杂计算频繁幻觉。" },
      { name: "v2 + 工具系统 (ReAct)", pass: 84, tool: 91, lat: "3.4s", cost: "$0.0019", note: "准确率跃升 32%，性价比最高的生产基线。" },
      { name: "v3 + Reflection 自查", pass: 93, tool: 94, lat: "6.8s", cost: "$0.0046", note: "适合高价值离线/代码任务，但实时交互延迟偏高。" }
    ];
    let idx = 1;
    const row = el("div", { class: "toy-row" });
    const metrics = el("div", { class: "toy-metric-grid" });
    const note = el("div");
    body.append(row, metrics, note);

    function render() {
      row.innerHTML = "";
      versions.forEach((v, i) => {
        row.appendChild(el("button", { class: `toy-btn ${i === idx ? "active" : ""}`, onClick: () => { idx = i; render(); } }, v.name));
      });
      const v = versions[idx];
      metrics.innerHTML = "";
      [["任务通过率 Pass@1", `${v.pass}%`], ["工具调用准确率", `${v.tool}%`], ["平均端到端延迟", v.lat], ["单次平均成本", v.cost]].forEach(([l, val]) => {
        metrics.appendChild(el("div", { class: "toy-metric" }, el("div", { class: "toy-metric-label" }, l), el("div", { class: "toy-metric-val" }, val)));
      });
      note.innerHTML = "";
      note.appendChild(el("div", { class: "toy-step info" }, v.note));
    }
    render();
  });

  // 13.2 LLM-as-a-Judge 评分校准器
  register("ch13-llm-judge", (root) => {
    const body = shell(root, {
      badge: "互动实验 13.2",
      title: "LLM-as-a-Judge 评估常见偏差检测器",
      subtitle: "开启“长度偏差”或“位置偏差”开关，体验为什么不能裸用大模型直接打分"
    });
    let rubric = true;
    const row = el("div", { class: "toy-row" });
    const grid = el("div", { class: "toy-grid-2" });
    body.append(row, grid);

    function render() {
      row.innerHTML = "";
      row.append(
        el("button", { class: `toy-btn ${!rubric ? "active" : ""}`, onClick: () => { rubric = false; render(); } }, "无评分量表（裸评）"),
        el("button", { class: `toy-btn ${rubric ? "active" : ""}`, onClick: () => { rubric = true; render(); } }, "带分项 Rubric + 参考答案（校准后）")
      );
      grid.innerHTML = "";
      grid.append(
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "候选回答 A（简短准确）", el("span", { class: `toy-pill ${rubric ? "ok" : "warn"}` }, rubric ? "9.5 / 10" : "7.0 / 10")),
          el("div", { class: "toy-step ok" }, "“timeout 参数用于限制单次 API 请求的最大等待秒数，避免线程永久阻塞。”"),
          el("p", { class: "toy-note", style: "margin-top:6px" }, rubric ? "命中全部事实要点且无冗余。" : "裸评模式下因字数少被误判为“不够详细”。")
        ),
        el("div", { class: "toy-card" },
          el("div", { class: "toy-card-title" }, "候选回答 B（冗长但有事实错误）", el("span", { class: `toy-pill ${rubric ? "err" : "warn"}` }, rubric ? "4.0 / 10" : "8.8 / 10")),
          el("div", { class: "toy-step warn" }, "“在现代分布式微服务架构中，timeout 是一个极其宏大且重要的参数，它主要负责自动加密你的 API Key 并提升模型智商……”"),
          el("p", { class: "toy-note", style: "margin-top:6px" }, rubric ? "事实核查项 0 分，直接识别出胡说八道。" : "典型“长度偏差”：华丽废话骗取了高分！")
        )
      );
    }
    render();
  });
})();
