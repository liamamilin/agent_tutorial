(function () {
  const registry = {};

  function esc(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (k === "class") node.className = v;
        else if (k === "html") node.innerHTML = v;
        else if (k.startsWith("on") && typeof v === "function") {
          node.addEventListener(k.slice(2).toLowerCase(), v);
        } else if (v !== false && v !== null && v !== undefined) {
          node.setAttribute(k, v === true ? "" : String(v));
        }
      }
    }
    for (const c of children.flat()) {
      if (c === null || c === undefined || c === false) continue;
      node.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c);
    }
    return node;
  }

  function shell(root, { badge = "交互实验", title, subtitle }) {
    root.innerHTML = "";
    const header = el("div", { class: "toy-header" },
      el("div", null,
        el("div", { class: "toy-title-wrap" },
          el("span", { class: "toy-badge" }, badge),
          el("h4", { class: "toy-title" }, title)
        ),
        subtitle ? el("p", { class: "toy-subtitle" }, subtitle) : null
      )
    );
    const body = el("div", { class: "toy-body" });
    root.appendChild(header);
    root.appendChild(body);
    return body;
  }

  function mountNode(node) {
    if (node.dataset.mounted === "1") return;
    const id = node.dataset.toy;
    const fn = registry[id];
    if (!fn) return;
    node.dataset.mounted = "1";
    try {
      fn(node);
    } catch (err) {
      node.innerHTML = `<div class="toy-body"><div class="toy-step err">实验组件加载失败 (${esc(id)}): ${esc(err.message)}</div></div>`;
    }
  }

  function mountAll() {
    document.querySelectorAll(".agent-toy[data-toy]").forEach(mountNode);
  }

  function register(id, initFn) {
    registry[id] = initFn;
    if (document.readyState !== "loading") {
      document.querySelectorAll(`.agent-toy[data-toy="${id}"]`).forEach(mountNode);
    }
  }

  function initProgressBar() {
    if (document.getElementById("book-reading-progress")) return;
    const bar = document.createElement("div");
    bar.id = "book-reading-progress";
    document.body.appendChild(bar);
    const update = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      bar.style.width = max > 0 ? `${Math.min(100, (window.scrollY / max) * 100)}%` : "0%";
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    update();
  }

  function boot() {
    mountAll();
    initProgressBar();
  }

  window.AgentToys = { register, shell, el, esc, mountAll };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  window.addEventListener("load", boot);
})();
