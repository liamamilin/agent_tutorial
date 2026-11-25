(function () {
  const { register, shell, el } = window.AgentToys;

  // Appendix A: ELIZA 规则匹配实时体验台
  register("appa-eliza-bot", (root) => {
    const body = shell(root, {
      badge: "互动实验 A.1",
      title: "1966 年 ELIZA 规则匹配实时沙箱",
      subtitle: "输入一句中文，同时观察 ELIZA 的回复与背后命中的正则表达式及人称代词替换过程"
    });
    const rules = [
      { re: /我觉得(.*)/, tpl: "为什么你会觉得$1？", name: "匹配「我觉得…」" },
      { re: /我想要(.*)/, tpl: "如果真的得到了$1，对你意味着什么？", name: "匹配「我想要…」" },
      { re: /因为(.*)/, tpl: "这是唯一的原因吗？除了$1之外还有什么？", name: "匹配「因为…」" },
      { re: /(焦虑|压力|累|难过)/, tpl: "听起来你最近感到$1，能多说说是什么引发的吗？", name: "匹配情绪关键词" }
    ];
    let text = "我觉得学 Agent 很有趣";
    const row = el("div", { class: "toy-row" });
    const out = el("div", { class: "toy-log" });
    body.append(row, out);

    function reflect(s) {
      return s.replace(/我的/g, "你的").replace(/我/g, "你").trim();
    }

    function run(val) {
      text = val;
      let matched = null;
      let reply = "我明白了，能再多跟我聊聊这个想法吗？（兜底默认模板）";
      for (const r of rules) {
        const m = val.match(r.re);
        if (m) {
          matched = { rule: r.name, regex: String(r.re), capture: m[1] };
          reply = r.tpl.replace("$1", reflect(m[1] || ""));
          break;
        }
      }
      out.innerHTML = "";
      out.append(
        el("div", { class: "toy-step ok" }, el("span", { class: "toy-pill ok" }, "ELIZA 回复"), reply),
        el("div", { class: "toy-step info" },
          el("span", { class: "toy-pill info" }, "规则引擎透视"),
          matched
            ? `命中规则：${matched.rule}（${matched.regex}），捕获片段="${matched.capture}" → 代词反转后拼接模板。`
            : "未命中任何预设正则，退回通用兜底回复——这就是规则系统不具备真正语义理解的根本局限。"
        )
      );
    }

    const inp = el("input", { class: "toy-input", style: "flex:1;min-width:200px", value: text, onInput: (e) => run(e.target.value) });
    row.append(inp);
    ["我觉得学 Agent 很有趣", "我想要写出自己的智能体", "最近工作压力有点大", "今天午饭吃什么？"].forEach((p) => {
      row.appendChild(el("button", { class: "toy-btn", onClick: () => { inp.value = p; run(p); } }, p));
    });
    run(text);
  });

  // Appendix B: BPE 分词合并单步模拟器
  register("appb-bpe-stepper", (root) => {
    const body = shell(root, {
      badge: "互动实验 B.1",
      title: "BPE 子词合并（Byte Pair Encoding）单步模拟器",
      subtitle: "点击“执行下一步合并”，观察算法如何统计最高频相邻字符对并逐步构建词表"
    });
    const baseWords = [
      ["l", "o", "w", "</w>"],
      ["l", "o", "w", "</w>"],
      ["l", "o", "w", "e", "r", "</w>"],
      ["n", "e", "w", "e", "s", "t", "</w>"],
      ["w", "i", "d", "e", "s", "t", "</w>"]
    ];
    let step = 0;
    const ctrl = el("div", { class: "toy-row" });
    const info = el("div");
    const tokensBox = el("div", { class: "toy-log" });
    body.append(ctrl, info, tokensBox);

    function computeState(steps) {
      let words = baseWords.map((w) => [...w]);
      let lastMerge = null;
      for (let s = 0; s < steps; s++) {
        const counts = {};
        words.forEach((w) => {
          for (let i = 0; i < w.length - 1; i++) {
            const pair = `${w[i]} ${w[i + 1]}`;
            counts[pair] = (counts[pair] || 0) + 1;
          }
        });
        const best = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
        if (!best || best[1] < 2) break;
        const [a, b] = best[0].split(" ");
        lastMerge = { a, b, count: best[1], merged: a + b };
        words = words.map((w) => {
          const nw = [];
          for (let i = 0; i < w.length; i++) {
            if (i < w.length - 1 && w[i] === a && w[i + 1] === b) {
              nw.push(a + b);
              i++;
            } else {
              nw.push(w[i]);
            }
          }
          return nw;
        });
      }
      return { words, lastMerge };
    }

    function render() {
      const { words, lastMerge } = computeState(step);
      ctrl.innerHTML = "";
      ctrl.append(
        el("button", { class: "toy-btn", disabled: step === 0, onClick: () => { step--; render(); } }, "上一步"),
        el("button", { class: "toy-btn primary", disabled: step >= 6, onClick: () => { step++; render(); } }, "执行下一步合并"),
        el("button", { class: "toy-btn", onClick: () => { step = 0; render(); } }, "重置"),
        el("span", { class: "toy-note" }, `已执行合并：${step} / 6 步`)
      );
      info.innerHTML = "";
      info.appendChild(el("div", { class: "toy-step info" },
        el("span", { class: "toy-pill info" }, step === 0 ? "初始字符集" : `合并 #${step}`),
        lastMerge
          ? `最高频相邻对 ("${lastMerge.a}", "${lastMerge.b}") 出现 ${lastMerge.count} 次 → 合并为新 Token "${lastMerge.merged}"`
          : "所有单词先拆分为单字符与词尾标记 </w>，准备统计相邻频率。"
      ));
      tokensBox.innerHTML = "";
      words.forEach((w, i) => {
        tokensBox.appendChild(el("div", { class: "toy-tokens" },
          el("span", { class: "toy-pill" }, `词 #${i + 1}`),
          w.map((tok) => el("span", {
            class: "toy-tok",
            style: `background:${lastMerge && tok === lastMerge.merged ? "#dcfce7" : "#f1f5f9"}`
          }, tok))
        ));
      });
    }
    render();
  });
})();
