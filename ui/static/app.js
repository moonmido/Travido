/* Travido UI: form -> workflow run -> live view of the state each agent writes. */

const NODE_W = 150;
const NODE_H = 46;

const LAYOUT = [
  { id: "constraint_builder", x: 300, y: 20,  label: "Constraint Builder", sub: "parse the form" },
  { id: "flight",             x: 90,  y: 130, label: "Flight Agent",     sub: "parallel" },
  { id: "hotel",              x: 305, y: 130, label: "Hotel Agent",      sub: "parallel" },
  { id: "destination_research", x: 520, y: 130, label: "Destination Research", sub: "parallel" },
  { id: "aggregator",         x: 300, y: 245, label: "Aggregator",       sub: "fan in" },
  { id: "transport",          x: 300, y: 335, label: "Transport Agent",  sub: "ground routes" },
  { id: "package_optimizer",  x: 300, y: 425, label: "Package Optimizer", sub: "loop target" },
  { id: "itinerary_planner",  x: 300, y: 515, label: "Itinerary Planner", sub: "day by day" },
  { id: "critic",             x: 300, y: 605, label: "Critic Agent",     sub: "problem?" },
  { id: "finalize",           x: 300, y: 690, label: "Package Output",   sub: "user answer" },
];

const EDGES = [
  ["constraint_builder", "flight"],
  ["constraint_builder", "hotel"],
  ["constraint_builder", "destination_research"],
  ["flight", "aggregator"],
  ["hotel", "aggregator"],
  ["destination_research", "aggregator"],
  ["aggregator", "transport"],
  ["transport", "package_optimizer"],
  ["package_optimizer", "itinerary_planner"],
  ["itinerary_planner", "critic"],
  ["critic", "finalize"],
];

const PARALLEL_BAND = { x: 60, y: 112, w: 640, h: 82 };

const state = {
  run: {
    running: false,
    jobId: null,
    source: null,
    merged: {},
    payloads: {},
    order: [],
    logs: [],
    failures: new Set(),
    completed: new Set(),
  },
};

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

/* ------------------------------------------------------------------ graph */

function nodeById(id) {
  return LAYOUT.find((n) => n.id === id);
}

function edgePath(from, to) {
  const a = nodeById(from);
  const b = nodeById(to);
  const x1 = a.x + NODE_W / 2;
  const y1 = a.y + NODE_H;
  const x2 = b.x + NODE_W / 2;
  const y2 = b.y;
  const mid = (y1 + y2) / 2;
  return `M ${x1} ${y1} C ${x1} ${mid}, ${x2} ${mid}, ${x2} ${y2}`;
}

function drawGraph() {
  const svg = $("#graph");
  svg.innerHTML = "";

  const ns = "http://www.w3.org/2000/svg";
  const mk = (tag, attrs) => {
    const node = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    return node;
  };

  const band = mk("rect", {
    x: PARALLEL_BAND.x, y: PARALLEL_BAND.y,
    width: PARALLEL_BAND.w, height: PARALLEL_BAND.h, class: "parallel-band",
  });
  svg.appendChild(band);

  const bandLabel = mk("text", { x: PARALLEL_BAND.x + 10, y: PARALLEL_BAND.y - 6, class: "edge-label" });
  bandLabel.textContent = "fan out / fan in";
  svg.appendChild(bandLabel);

  for (const [from, to] of EDGES) {
    svg.appendChild(mk("path", { d: edgePath(from, to), class: "edge", "data-edge": `${from}->${to}` }));
  }

  // critic -> package_optimizer feedback loop
  const critic = nodeById("critic");
  const opt = nodeById("package_optimizer");
  const loop = mk("path", {
    d: `M ${critic.x} ${critic.y + NODE_H / 2} C 90 ${critic.y + NODE_H / 2}, 90 ${opt.y + NODE_H / 2}, ${opt.x} ${opt.y + NODE_H / 2}`,
    class: "edge is-loop",
    "data-edge": "critic->package_optimizer",
  });
  svg.appendChild(loop);

  const loopLabel = mk("text", { x: 120, y: 560, class: "edge-label" });
  loopLabel.textContent = "needs revision";
  svg.appendChild(loopLabel);

  for (const spec of LAYOUT) {
    const g = mk("g", { class: "node", "data-node": spec.id, style: "cursor:pointer" });

    g.appendChild(mk("rect", { x: spec.x - 6, y: spec.y - 6, width: NODE_W + 12, height: NODE_H + 12, rx: 14, class: "node-ring" }));
    g.appendChild(mk("rect", { x: spec.x, y: spec.y, width: NODE_W, height: NODE_H, class: "node-box" }));

    const label = mk("text", { x: spec.x + NODE_W / 2, y: spec.y + 20, class: "node-label" });
    label.textContent = spec.label;
    g.appendChild(label);

    const sub = mk("text", { x: spec.x + NODE_W / 2, y: spec.y + 35, class: "node-sub" });
    sub.textContent = spec.sub;
    g.appendChild(sub);

    g.addEventListener("click", () => showNodeDetail(spec.id));
    svg.appendChild(g);
  }
}

function markNode(id, kind) {
  const g = document.querySelector(`[data-node="${id}"]`);
  if (!g) return;
  g.classList.remove("is-active", "is-done", "is-failed");
  if (kind) g.classList.add(kind);
}

function clearNodes() {
  document.querySelectorAll("[data-node]").forEach((g) => g.classList.remove("is-active", "is-done", "is-failed"));
  document.querySelectorAll("[data-edge]").forEach((p) => p.classList.remove("is-active"));
}

/* ------------------------------------------------------------- node panel */

function showNodeDetail(id) {
  const panel = $("#node-detail");
  const spec = nodeById(id);
  const payload = state.run.payloads[id];

  panel.innerHTML = "";
  panel.appendChild(el("h3", null, spec ? spec.label : id));
  panel.appendChild(el("p", "meta", `${id}  ·  ${spec ? spec.sub : "internal graph node"}`));

  if (!payload) {
    panel.appendChild(el("p", "meta", "not run yet"));
    panel.appendChild(el("pre", null, "{}"));
    return;
  }

  panel.appendChild(el("p", "meta", `${payload.keys.length} key(s) · ${payload.bytes} bytes · finished at ${payload.t}s`));
  panel.appendChild(el("pre", null, pretty(payload.preview)));
}

function pretty(text) {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

/* ------------------------------------------------------------- streaming */

function setStatus(kind, label) {
  const node = $("#status");
  node.className = `status status--${kind}`;
  node.textContent = label;
}

function log(line) {
  state.run.logs.push(line);
  $("#events-view").textContent = state.run.logs.join("\n");
}

function renderState() {
  $("#state-view").textContent = JSON.stringify(state.run.merged, null, 2);
}

function handleEvent(event) {
  if (event.type === "state") {
    state.run.merged = event.state || {};
    renderState();
    return;
  }

  if (event.type === "node") {
    markNode(event.node, "is-active");
    state.run.payloads[event.node] = event;

    for (const [from, to] of EDGES) {
      if (to === event.node) {
        document.querySelector(`[data-edge="${from}->${to}"]`)?.classList.add("is-active");
      }
    }
    if (event.node === "package_optimizer") {
      document.querySelector('[data-edge="critic->package_optimizer"]')?.classList.add("is-active");
    }

    markNode(event.node, event.keys.includes("node_errors") ? "is-failed" : "is-done");

    log(`[${String(event.t).padStart(6)}s] ${event.node.padEnd(22)} ${String(event.bytes).padStart(6)}B  ${event.keys.join(", ")}`);
    showNodeDetail(event.node);
    return;
  }

  if (event.type === "done") {
    markNode("finalize", "is-done");
    $("#result-view").textContent = event.final_response || "(empty)";
    log("");
    log(`=== done in ${event.t}s · iterations=${event.iteration} ===`);
    if (event.clarification_required) {
      log("! constraint builder asked for clarification");
    }
    if (event.node_errors && event.node_errors.length) {
      log(`! node errors: ${JSON.stringify(event.node_errors)}`);
    }
    switchTab("result");
    finish("done", "finished");
    return;
  }

  if (event.type === "error") {
    log(`!! ${event.message}`);
    showBanner(`${event.message}`, "banner--error");
    finish("error", "error");
    return;
  }

  if (event.type === "cancelled") {
    log("--- cancelled ---");
    finish("idle", "cancelled");
  }
}

function showBanner(text, cls = "banner") {
  document.querySelectorAll(".banner").forEach((b) => b.remove());
  const node = el("div", cls, text);
  document.querySelector(".panel--pipeline").prepend(node);
}

function finish(statusKind, label) {
  state.run.running = false;
  setStatus(statusKind, label);
  $("#run").disabled = false;
  $("#cancel").disabled = true;
  clearActiveEdges();
  renderState();
}

function clearActiveEdges() {
  document.querySelectorAll("[data-edge]").forEach((p) => p.classList.remove("is-active"));
  document.querySelectorAll("[data-node]").forEach((g) => g.classList.remove("is-active"));
}

/* ------------------------------------------------------------------ form */

function collectForm() {
  const form = $("#trip-form");
  const data = {};
  for (const [name, field] of Object.entries(form.elements)) {
    if (!name || field.disabled) continue;
    data[name] = field.type === "checkbox" ? field.checked : field.value;
  }
  return data;
}

async function runTrip(event) {
  event.preventDefault();
  if (state.run.running) return;

  state.run.merged = {};
  state.run.payloads = {};
  state.run.logs = [];
  state.run.completed = new Set();
  clearNodes();
  $("#result-view").textContent = "";
  $("#events-view").textContent = "";
  renderState();
  switchTab("live");

  setStatus("running", "planning");
  $("#run").disabled = true;
  $("#cancel").disabled = false;
  state.run.running = true;

  let started;
  try {
    const response = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectForm()),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);

    state.run.jobId = data.job_id;
    $("#query-box").textContent = data.query;
    log(`job ${data.job_id}`);
    log("");

    started = new EventSource(`/api/jobs/${data.job_id}/events`);
    state.run.source = started;

    started.onmessage = (e) => handleEvent(JSON.parse(e.data));
    started.onerror = () => {
      if (state.run.running) {
        setStatus("error", "stream lost");
        state.run.running = false;
        $("#run").disabled = false;
        $("#cancel").disabled = true;
      }
      started.close();
    };
  } catch (err) {
    showBanner(err.message, "banner--error");
    finish("error", "error");
  }
}

async function cancelRun() {
  if (!state.run.jobId) return;
  await fetch(`/api/jobs/${state.run.jobId}/cancel`, { method: "POST" });
  log("--- cancel requested ---");
}

function resetForm() {
  $("#trip-form").reset();
  clearNodes();
  state.run.merged = {};
  state.run.payloads = {};
  state.run.logs = [];
  renderState();
  $("#result-view").textContent = "";
  $("#events-view").textContent = "";
  setStatus("idle", "idle");
  showNodeDetail("constraint_builder");
}

/* ------------------------------------------------------------------ tabs */

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("tab--active", tab.dataset.tab === name);
  });
  $("#state-view").hidden = name !== "live";
  $("#result-view").hidden = name !== "result";
  $("#events-view").hidden = name !== "events";
}

/* ------------------------------------------------------------------ boot */

async function loadPolicies() {
  try {
    const data = await (await fetch("/api/graph")).json();
    const rows = Object.entries(data.policies)
      .map(([name, p]) => `<b>${name}</b> ${p.max_attempts}x / ${p.run_timeout}s`)
      .join("<br />");
    $("#policy-table").innerHTML = rows;
  } catch {
    $("#policy-table").textContent = "unavailable";
  }
}

function boot() {
  drawGraph();
  loadPolicies();
  $("#run").addEventListener("click", runTrip);
  $("#trip-form").addEventListener("submit", runTrip);
  $("#cancel").addEventListener("click", cancelRun);
  $("#reset").addEventListener("click", resetForm);
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
  showNodeDetail("constraint_builder");
  renderState();
}

boot();
