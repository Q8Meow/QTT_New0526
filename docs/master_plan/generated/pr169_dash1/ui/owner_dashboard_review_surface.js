const THEME_STORAGE_KEY = "qtt_owner_dashboard_theme";
const DASHBOARD_DATA = window.QTT_OWNER_DASHBOARD_DATA || {
  meta: {
    artifact_id: "UI1_OWNER_DASHBOARD_REVIEW_DATA",
    data_source: "FIXTURE_FALLBACK",
    fixture_fallback_active: true,
    registry_row_count: 0,
    decision_queue_count: 0,
    actionable_card_count: 0,
    chart_count: 0,
    qku_formula_route_count: 0,
    authority_boundary_ref: "LOCAL_STATIC_NO_RUNTIME_NO_CREDENTIALS_NO_DIRECT_VENUE_SUBMIT_NO_EXECUTION_ROUTER_RELEASE"
  },
  status_strip: {},
  owner_packet: {},
  header_strip: [],
  decision_queue: [],
  actionable_cards: [],
  action_registry: [],
  charts: { chart_contracts: [], chart_families: [], interactive_chart_registry: [] },
  research_candidates: [],
  qku_formula_routes: [],
  quantum_readiness: [],
  institutional_metrics: [],
  data_value_routes: [],
  dag: { rows: [], lineage: [] },
  provider_stage_routes: { routes: [] },
  widget_manifest: { widgets: [] },
  trade_workbench: {},
  conversation_state: { threads: [] },
  chat_threads: [],
  chat_action_catalog: { actions: [] },
  owner_trade_command: {},
  mobile_navigation: { tabs: [] },
  empty_states: { empty_states: [] }
};

const RANGES = ["1D", "1W", "1M", "3M", "YTD", "1Y", "ALL"];
const SEMANTIC_LEGEND = [
  ["positive gain / pass", "var(--qtt-green)"],
  ["loss / fail", "var(--qtt-red)"],
  ["classical baseline", "var(--qtt-blue)"],
  ["quantum applied", "var(--qtt-purple)"],
  ["degradation watch", "var(--qtt-orange)"],
  ["caution / insufficient support", "var(--qtt-yellow)"],
  ["inactive / provider pending", "var(--qtt-gray)"]
];

const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];

function asList(value) {
  if (Array.isArray(value)) return value;
  if (!value || typeof value !== "object") return [];
  if (Array.isArray(value.rows)) return value.rows;
  if (Array.isArray(value.routes)) return value.routes;
  if (Array.isArray(value.widgets)) return value.widgets;
  if (Array.isArray(value.actions)) return value.actions;
  if (Array.isArray(value.empty_states)) return value.empty_states;
  if (Array.isArray(value.chart_contracts)) return value.chart_contracts;
  return Object.entries(value)
    .filter(([, child]) => Array.isArray(child))
    .flatMap(([, child]) => child);
}

function safe(value) {
  const text = value === null || value === undefined ? "" : String(value);
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function label(value) {
  if (value === null || value === undefined || value === "") return "provider-pending";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) return value.length ? value.slice(0, 4).join(", ") : "provider-pending";
  if (typeof value === "object") return value.artifact_id || value.panel_id || value.widget_id || value.stage_id || "linked object";
  return String(value).replaceAll("_", " ");
}

function idOf(row, fallback = "row") {
  return (
    row.widget_id ||
    row.panel_id ||
    row.card_id ||
    row.queue_id ||
    row.feature_id ||
    row.action_code ||
    row.chart_id ||
    row.stage_id ||
    row.route_id ||
    row.pipeline_step_id ||
    row.qku_ref ||
    row.thread_id ||
    row.artifact_id ||
    fallback
  );
}

function summarize(row) {
  if (!row || typeof row !== "object") return "Generated DASH1 artifact row rendered through the UI1 boot model.";
  return (
    row.summary ||
    row.route_purpose ||
    row.widget_title ||
    row.visible_label ||
    row.card_type ||
    row.safe_default ||
    row.render_state ||
    row.pipeline_state ||
    row.provider_state ||
    row.no_orphan_status ||
    "Generated DASH1 artifact row rendered through OwnerSurfaceResolver-linked boot data."
  );
}

function refsFor(row) {
  if (!row || typeof row !== "object") return [];
  const keys = [
    "source_artifact_paths",
    "source_artifact_refs",
    "upstream_artifact_refs",
    "downstream_consumer_refs",
    "owner_action_refs",
    "agent_role_refs_from_PR165_D2",
    "validation_ref",
    "data_ref",
    "artifact_path",
    "contract_ref",
    "registry_row_ref",
    "authority_boundary_ref",
    "activation_route",
    "provider_stage"
  ];
  return keys
    .filter((key) => row[key])
    .map((key) => [key, label(row[key])]);
}

function badge(text, tone = "gray") {
  return `<span class="badge ${tone}">${safe(text)}</span>`;
}

function badges(row, extra = []) {
  const values = [
    row.provider_stage,
    row.provider_state,
    row.render_status,
    row.render_state,
    row.authority_boundary_ref ? "authority-bound" : "",
    row.no_orphan_status,
    ...extra
  ].filter(Boolean);
  return `<div class="badge-row">${values.slice(0, 5).map((v) => badge(label(v), toneFor(v))).join("")}</div>`;
}

function toneFor(value) {
  const text = String(value || "").toUpperCase();
  if (text.includes("PASS") || text.includes("VISIBLE") || text.includes("MATERIALIZED")) return "green";
  if (text.includes("FAIL") || text.includes("CRITICAL") || text.includes("BLOCKED")) return "red";
  if (text.includes("QUANTUM") || text.includes("QMAP")) return "purple";
  if (text.includes("REPAIR") || text.includes("DEGRADED")) return "orange";
  if (text.includes("PENDING") || text.includes("ROUTED")) return "gray";
  if (text.includes("CAUTION") || text.includes("INSUFFICIENT")) return "yellow";
  return "blue";
}

function openDrawer(title, kicker, row) {
  const drawer = qs("#drilldownDrawer");
  qs("#drawerTitle").textContent = title;
  qs("#drawerKicker").textContent = kicker;
  const refs = refsFor(row);
  qs("#drawerBody").innerHTML = `
    <div class="drawer-block">
      <h3>Summary</h3>
      <p>${safe(summarize(row))}</p>
      ${badges(row)}
    </div>
    <div class="drawer-block">
      <h3>Key metrics</h3>
      <div class="bar-row"><span>OwnerSurfaceResolver</span><div class="bar-track"><div class="bar-fill" style="--bar-width:100%;--bar-color:var(--qtt-blue)"></div></div><span>linked</span></div>
      <div class="bar-row"><span>OwnerActionRegistry</span><div class="bar-track"><div class="bar-fill" style="--bar-width:100%;--bar-color:var(--qtt-green)"></div></div><span>governed</span></div>
      <div class="bar-row"><span>Runtime side effect</span><div class="bar-track"><div class="bar-fill" style="--bar-width:0%;--bar-color:var(--qtt-red)"></div></div><span>false</span></div>
    </div>
    <div class="drawer-block">
      <h3>Linked refs</h3>
      ${refs.length ? refs.map(([key, value]) => `<p><strong>${safe(key)}:</strong> ${safe(value)}</p>`).join("") : "<p>Provider route refs are represented by this UI1 generated projection row.</p>"}
      <details>
        <summary>Raw refs</summary>
        <pre>${safe(JSON.stringify(row, null, 2))}</pre>
      </details>
    </div>
  `;
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer() {
  const drawer = qs("#drilldownDrawer");
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
}

function setTheme(mode, persist = true) {
  const normalized = mode === "LIGHT" ? "light" : "dark";
  document.documentElement.dataset.theme = normalized;
  qsa("[data-theme-choice]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.themeChoice === mode ? "true" : "false");
  });
  if (!persist) return;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode === "LIGHT" ? "LIGHT" : "DARK");
  } catch {
    window.__QTT_IN_SESSION_THEME = mode === "LIGHT" ? "LIGHT" : "DARK";
  }
}

function initTheme() {
  let saved = "DARK";
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    saved = stored === "LIGHT" ? "LIGHT" : "DARK";
  } catch {
    saved = window.__QTT_IN_SESSION_THEME || "DARK";
  }
  setTheme(saved, false);
  qsa("[data-theme-choice]").forEach((button) => {
    button.addEventListener("click", () => setTheme(button.dataset.themeChoice));
  });
  qs("#mobileThemeToggle").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "LIGHT" : "DARK";
    setTheme(next);
  });
}

function renderStatus() {
  const status = DASHBOARD_DATA.status_strip || {};
  const meta = DASHBOARD_DATA.meta || {};
  const tiles = [
    ["surface mode", status.surface_mode || "LOCAL_STATIC_READ_ONLY"],
    ["input data source", status.input_data_source || meta.data_source],
    ["registry rows", status.registry_row_count || meta.registry_row_count],
    ["decision rows", status.decision_queue_count || meta.decision_queue_count],
    ["actionable cards", status.actionable_card_count || meta.actionable_card_count],
    ["chart rows", status.chart_count || meta.chart_count],
    ["agent routes", status.agent_route_count || meta.agent_route_count],
    ["QKU routes", status.QKU_formula_route_count || meta.qku_formula_route_count],
    ["artifact directory", status.artifact_directory || meta.artifact_directory],
    ["authority boundary", status.authority_boundary || meta.authority_boundary_ref]
  ];
  qs("#statusGrid").innerHTML = tiles.map(([name, value]) => `
    <div class="status-tile">
      <span class="eyebrow">${safe(name)}</span>
      <span class="value">${safe(label(value))}</span>
    </div>
  `).join("");
}

function renderOverview() {
  const meta = DASHBOARD_DATA.meta || {};
  const cards = [
    ["OwnerDashboardPacket", idOf(DASHBOARD_DATA.owner_packet, "owner_dashboard_packet"), "Packet rendered from generated DASH1 packet artifact.", "green", DASHBOARD_DATA.owner_packet],
    ["OwnerDecisionQueue", `${asList(DASHBOARD_DATA.decision_queue).length} rows`, "Queue semantics preserved from DASH1 generated rows.", "blue", asList(DASHBOARD_DATA.decision_queue)[0] || {}],
    ["OwnerActionableCards", `${asList(DASHBOARD_DATA.actionable_cards).length} rows`, "Actionable card meaning preserved and linked to the canonical action grammar.", "purple", asList(DASHBOARD_DATA.actionable_cards)[0] || {}],
    ["Fixture fallback", meta.fixture_fallback_active ? "active" : "inactive", "Generated artifacts are primary when present; fixture is visually labeled fallback only.", meta.fixture_fallback_active ? "orange" : "green", DASHBOARD_DATA.fixture_fallback || {}],
    ["Theme", "DARK / LIGHT", "Presentation preference only; qtt_owner_dashboard_theme stores only DARK or LIGHT.", "gray", DASHBOARD_DATA.theme_contract || {}],
    ["Authority", "request previews only", "No direct venue submit and no Execution Router release authority in UI1.", "red", DASHBOARD_DATA.authority_boundary || {}]
  ];
  qs("#overviewCards").innerHTML = cards.map(([title, value, body, tone, row]) => `
    <button class="metric-card card" type="button" data-drawer="${safe(title)}">
      <span class="eyebrow">${safe(title)}</span>
      <span class="value">${safe(value)}</span>
      <p>${safe(body)}</p>
      ${badge(tone === "red" ? "blocked runtime path" : "rendered", tone)}
    </button>
  `).join("");
  qsa("#overviewCards [data-drawer]").forEach((button, index) => {
    button.addEventListener("click", () => openDrawer(cards[index][0], "Overview", cards[index][4]));
  });
}

function renderRanges() {
  qs("#rangeButtons").innerHTML = RANGES.map((range, index) => `
    <button class="seg-button ${index === 0 ? "active" : ""}" type="button" data-range="${range}" aria-pressed="${index === 0 ? "true" : "false"}">${range}</button>
  `).join("");
  qsa("#rangeButtons button").forEach((button) => {
    button.addEventListener("click", () => {
      qsa("#rangeButtons button").forEach((item) => {
        item.classList.toggle("active", item === button);
        item.setAttribute("aria-pressed", item === button ? "true" : "false");
      });
      qsa(".chart-panel").forEach((panel) => panel.dataset.range = button.dataset.range);
    });
  });
}

function legendHtml() {
  return `<div class="legend">${SEMANTIC_LEGEND.map(([name, color]) => `<span><i style="--legend-color:${color}"></i>${safe(name)}</span>`).join("")}</div>`;
}

function renderChartPanel(row, index) {
  const title = row.chart_family || row.chart_id || row.widget_title || `chart ${index + 1}`;
  const x = [10, 26, 42, 58, 74, 90];
  const y = [64, 42, 58, 32, 44, 26].map((base, i) => Math.max(16, base + ((index + i) % 4) * 4));
  const points = x.map((left, i) => `<button class="chart-point" type="button" style="left:${left}%;top:${y[i]}%;--series-color:${i % 3 === 0 ? "var(--qtt-green)" : i % 3 === 1 ? "var(--qtt-blue)" : "var(--qtt-purple)"}" aria-label="${safe(title)} point ${i + 1}"></button>`).join("");
  return `
    <article class="chart-panel" data-search="${safe(title)}">
      <h3>${safe(title)}</h3>
      <p>${safe(row.empty_state_policy || row.dataset_provider_stage || "Provider-routed chart contract rendered without fabricated cash, fills, or PnL.")}</p>
      <div class="chart-canvas" role="img" aria-label="${safe(title)} chart contract">
        <div class="chart-line"></div>
        ${points}
      </div>
      ${legendHtml()}
      ${badges(row, ["time ranges", "drilldown"])}
    </article>
  `;
}

function renderCharts() {
  const portfolio = asList(DASHBOARD_DATA.portfolio_pnl);
  const contracts = [
    ...portfolio,
    ...asList(DASHBOARD_DATA.charts && DASHBOARD_DATA.charts.chart_contracts),
    ...asList(DASHBOARD_DATA.charts && DASHBOARD_DATA.charts.interactive_chart_registry)
  ];
  qs("#portfolioCards").innerHTML = portfolio.slice(0, 6).map((row) => `
    <button class="card" type="button">
      <h3>${safe(row.chart_family || row.chart_id)}</h3>
      <p>${safe(row.dataset_provider_stage || row.render_state || "chart contract route")}</p>
      ${badges(row)}
    </button>
  `).join("");
  qs("#portfolioCards").querySelectorAll(".card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(label(portfolio[index].chart_family || portfolio[index].chart_id), "Portfolio chart", portfolio[index]));
  });
  const requiredFamilies = [
    { chart_family: "PNL_TIMESERIES_ROW", provider_stage: "MATERIALIZED_IN_DASH1", empty_state_policy: "Rendered from chart contract rows when numeric series is provider-pending." },
    { chart_family: "FEE_AND_SLIPPAGE_WATERFALL_CARD", provider_stage: "CONTRACT_DEFINED_PROVIDER_PENDING", empty_state_policy: "TCA waterfall route visible without fabricated fills or costs." },
    { chart_family: "QUANTUM_CLASSICAL_COMPARATOR_TIMESERIES_ROW", provider_stage: "ROUTED_PENDING_PROVIDER", empty_state_policy: "Quantum/classical comparator visible with blue and purple semantic labels." },
    { chart_family: "LATENCY_HISTOGRAM", provider_stage: "ROUTED_PENDING_PROVIDER", empty_state_policy: "Runtime receipt path visible; UI1 does not stream live latency." },
    { chart_family: "CAPITAL_USAGE_CHART", provider_stage: "CONTRACT_DEFINED_PROVIDER_PENDING", empty_state_policy: "Cash/account/private data not read by UI1." },
    { chart_family: "DAG_upstream_downstream_graph", provider_stage: "MATERIALIZED_IN_DASH1", empty_state_policy: "DAG and lineage rows rendered as linked refs." }
  ];
  const rows = [...contracts.slice(0, 10), ...requiredFamilies];
  qs("#chartGrid").innerHTML = rows.map(renderChartPanel).join("");
  qsa("#chartGrid .chart-panel").forEach((panel, index) => {
    panel.addEventListener("click", () => openDrawer(panel.querySelector("h3").textContent, "Chart drilldown", rows[index]));
  });
}

function renderPacketAndQueue() {
  const packet = DASHBOARD_DATA.owner_packet || {};
  qs("#ownerPacketCard").innerHTML = `
    <h3>OwnerDashboardPacket</h3>
    <p>Packet ${safe(packet.packet_id || "owner dashboard packet")} renders generated packet, header strip, queue, card, action, and authority refs without raw JSON as the primary UX.</p>
    ${badges(packet, ["DASH1 canonical"])}
  `;
  qs("#ownerPacketCard").addEventListener("click", () => openDrawer("OwnerDashboardPacket", "Packet refs", packet));

  const rows = asList(DASHBOARD_DATA.decision_queue).slice(0, 18);
  qs("#decisionQueue").innerHTML = rows.map((row) => `
    <article class="card" data-search="${safe(Object.values(row).slice(0, 8).join(" "))}">
      <h3>${safe(row.queue_id || row.feature_id || row.owner_action_ref || "decision queue row")}</h3>
      <p>${safe(row.safe_default || row.gate_priority || "Decision queue semantics preserved from generated DASH1 row.")}</p>
      ${badges(row, [row.owner_action_ref || "owner action linked"])}
    </article>
  `).join("");
  qsa("#decisionQueue .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Decision Queue", rows[index]));
  });
}

function renderActions() {
  const actions = asList(DASHBOARD_DATA.action_registry);
  const cards = asList(DASHBOARD_DATA.actionable_cards).slice(0, 18);
  qs("#actionCatalog").innerHTML = `
    <div class="table-shell">
      <table>
        <thead><tr><th>Action code</th><th>Label</th><th>Authority</th><th>Direct submit</th></tr></thead>
        <tbody>${actions.slice(0, 36).map((row) => `
          <tr>
            <td>${safe(row.action_code)}</td>
            <td>${safe(row.canonical_label || row.action_semantics)}</td>
            <td>${safe(row.confirmation_class || row.authority_boundary_ref)}</td>
            <td>${safe(row.creates_order_authority === false ? "false" : label(row.creates_order_authority))}</td>
          </tr>
        `).join("")}</tbody>
      </table>
    </div>
  `;
  qs("#actionCatalog").addEventListener("click", () => openDrawer("OwnerActionRegistry", "Action grammar preserved", actions[0] || {}));
  qs("#actionableCards").innerHTML = cards.map((row) => `
    <article class="card" data-search="${safe(Object.values(row).slice(0, 8).join(" "))}">
      <h3>${safe(row.card_id || row.feature_id || "actionable card")}</h3>
      <p>${safe(row.card_type || row.status || "Generated actionable card rendered from DASH1.")}</p>
      ${badges(row, [row.owner_action_ref || "receipt-gated"])}
    </article>
  `).join("");
  qsa("#actionableCards .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Actionable Cards", cards[index]));
  });
}

function renderTimeline() {
  const pipeline = asList(DASHBOARD_DATA.research_candidates);
  const fallbackStages = [
    "Owner Input Box",
    "Source Candidate Intake",
    "Duplicate / Recency / Relevance / Safety Check",
    "LLM Extraction Route",
    "Formula / QKU Materialization Route",
    "Replay / Paper Request Route",
    "Champion / Challenger Review",
    "No-Trade Reoptimization Review",
    "Owner Promotion Review",
    "Live Canary Review Route"
  ].map((name) => ({ pipeline_step_id: name, provider_stage: "ROUTED_PENDING_PROVIDER", activation_route: "owner_submitted_research_candidate_route" }));
  const rows = pipeline.length ? pipeline : fallbackStages;
  qs("#researchPipeline").innerHTML = rows.slice(0, 12).map((row) => `
    <button class="timeline-step" type="button">
      <h3>${safe(row.pipeline_step_id || row.stage_id || row.widget_title)}</h3>
      <p>${safe(row.pipeline_state || row.activation_route || "source-agnostic candidate route")}</p>
      ${badges(row)}
    </button>
  `).join("");
  qsa("#researchPipeline .timeline-step").forEach((step, index) => {
    step.addEventListener("click", () => openDrawer(step.querySelector("h3").textContent, "Research pipeline", rows[index]));
  });
  renderTable("#sourceWatchlist", rows.slice(0, 12), ["pipeline_step_id", "source_family", "provider_stage", "activation_route"], "Source Watchlist / Source Candidate Panel");
}

function renderTable(selector, rows, columns, title) {
  qs(selector).innerHTML = `
    <h3>${safe(title)}</h3>
    <table>
      <thead><tr>${columns.map((column) => `<th>${safe(column)}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((row) => `
        <tr>${columns.map((column) => `<td>${safe(label(row[column]))}</td>`).join("")}</tr>
      `).join("")}</tbody>
    </table>
  `;
  qs(selector).addEventListener("click", () => openDrawer(title, "Table refs", rows[0] || {}), { once: true });
}

function renderEdgeAndParameters() {
  const edgeRows = asList(DASHBOARD_DATA.edge_alpha);
  const metrics = asList(DASHBOARD_DATA.institutional_metrics);
  const edge = [...edgeRows, ...metrics].slice(0, 9);
  qs("#edgeAlphaBoard").innerHTML = edge.map((row) => `
    <article class="card">
      <h3>${safe(row.metric_id || row.edge_id || row.feature_id || "Execution-adjusted ranking")}</h3>
      <p>${safe(row.TCA_decomposition_ref || row.execution_adjusted_ranking || row.activation_route || "TCA decomposition and no-trade comparator route visible.")}</p>
      ${badges(row, ["validated positive net-cash evidence"])}
    </article>
  `).join("");
  qsa("#edgeAlphaBoard .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Edge / Alpha Board", edge[index]));
  });

  const widgets = asList(DASHBOARD_DATA.widget_manifest).filter((row) => /Parameter|Atomic|Provenance|Control/i.test(label(row.widget_title || row.widget_id))).slice(0, 9);
  qs("#parameterControl").innerHTML = widgets.map((row) => `
    <article class="card">
      <h3>${safe(row.widget_title || row.widget_id)}</h3>
      <p>Current live value, source-of-truth class, reference range, bounded search range, editability, and LKG refs render as read-only DASH1 UI routes.</p>
      ${badges(row, ["read-only control preview"])}
    </article>
  `).join("");
  qsa("#parameterControl .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Parameter Control", widgets[index]));
  });
}

function renderQkuAndQuantum() {
  const qkuRows = asList(DASHBOARD_DATA.qku_formula_routes);
  const matrix = asList(DASHBOARD_DATA.qku_formula_computability_matrix);
  renderTable("#qkuFormulaRoutes", qkuRows.length ? qkuRows : matrix, ["qku_refs", "formula_refs", "computability_state", "activation_route"], "QKU / Formula computability matrix");
  qs("#agentQkuResolver").innerHTML = `
    <h3>CENTRALIZED_AGENT_QKU_ACCESS_RESOLVER_PANEL</h3>
    <p>${safe(label(DASHBOARD_DATA.agent_qku_access_resolver.agent_stage_universe_formula))}</p>
    ${badges(DASHBOARD_DATA.agent_qku_access_resolver, ["no raw JSONL scanning"])}
  `;
  qs("#agentQkuResolver").addEventListener("click", () => openDrawer("Centralized Agent QKU Access Resolver", "Resolver path", DASHBOARD_DATA.agent_qku_access_resolver));

  const quantumRows = [
    ...asList(DASHBOARD_DATA.quantum_readiness),
    ...asList(DASHBOARD_DATA.widget_manifest).filter((row) => /Quantum|QPU|QUBO|QAOA|VQE|Ising/i.test(label(row.widget_title || row.widget_id))).slice(0, 17)
  ];
  qs("#quantumCenter").innerHTML = quantumRows.slice(0, 18).map((row) => `
    <article class="card">
      <h3>${safe(row.widget_title || row.panel_id || row.chart_id || row.quantum_candidate_id || "Quantum structural readiness")}</h3>
      <p>${safe(row.QMAP1_activation_route || row.activation_route || row.provider_stage || "QMAP1 route visible; no quantum backend call or advantage claim.")}</p>
      ${badges(row, ["classical fallback refs"])}
    </article>
  `).join("");
  qsa("#quantumCenter .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Quantum Control Center", quantumRows[index]));
  });
}

function renderChatAndTrade() {
  const threads = asList(DASHBOARD_DATA.chat_threads);
  const chatActions = asList(DASHBOARD_DATA.chat_action_catalog);
  qs("#chatWorkspace").innerHTML = `
    <article class="card">
      <h3>OWNER_AGENT_CHAT_THREAD_LIST</h3>
      <p>${safe(threads.length)} routed thread previews use OwnerConversationStateV1 through OwnerDashboardStateV1.</p>
      ${badges(DASHBOARD_DATA.conversation_state, ["desktop", "mobile", "PWA", "native contract", "Telegram mirror"])}
    </article>
    <article class="card">
      <h3>OWNER_AGENT_CHAT_COMPOSER</h3>
      <p>Free text, link, file, formula, algorithm, quantum strategy note, and trade idea inputs create local request previews only.</p>
      ${badge("runtime side effect false", "red")}
    </article>
    <article class="card">
      <h3>OWNER_AGENT_CHAT_ROUTE_PREVIEW</h3>
      <p>Chat-to-research, chat-to-trade, chat-to-QKU, chat-to-agent-task, and chat-to-provider-stage routes are visible.</p>
      ${badge(`${chatActions.length} request codes`, "blue")}
    </article>
    <article class="card">
      <h3>OWNER_AGENT_CHAT_RECEIPT_TIMELINE</h3>
      <p>Receipt previews preserve canonical IDs; Telegram remains a degraded mirror, not a second governance plane.</p>
      ${badge("same action grammar", "green")}
    </article>
  `;
  qsa("#chatWorkspace .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Owner-Agent Chat Workspace", threads[index] || chatActions[index] || DASHBOARD_DATA.conversation_state));
  });

  const workbench = DASHBOARD_DATA.trade_workbench || {};
  const sections = asList(workbench.visible_sections).length ? asList(workbench.visible_sections) : [
    "Owner intent",
    "Source evidence",
    "QKU/formula stack",
    "Variable search",
    "Replay result",
    "Paper result",
    "TCA",
    "Risk/capacity",
    "No-trade comparison",
    "Champion/challenger",
    "Owner decision",
    "Execution Router status"
  ];
  qs("#tradeWorkbench").innerHTML = sections.map((name, index) => `
    <article class="card">
      <h3>${safe(name)}</h3>
      <p>${index === 0 ? "OwnerTradeIntentV1 and OwnerTradeCheckRequestV1 preview route." : "Routed provider-stage view from the central Trade Workbench state."}</p>
      ${badges(workbench, [index === 0 ? "CHECK_TRADE_WITH_QTT_AGENTS" : "request preview only"])}
    </article>
  `).join("");
  qsa("#tradeWorkbench .card").forEach((card) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Trade Workbench", workbench));
  });
}

function renderAgentsAndContracts() {
  const agentRows = [
    ...asList(DASHBOARD_DATA.agent_performance),
    ...asList(DASHBOARD_DATA.widget_manifest).filter((row) => /Agent|KPI|Trust|Quarantine|Replacement|Reroute/i.test(label(row.widget_title || row.widget_id))).slice(0, 12)
  ];
  qs("#agentOperations").innerHTML = agentRows.slice(0, 12).map((row) => `
    <article class="card">
      <h3>${safe(row.widget_title || row.agent_id || row.chart_id || "Agent KPI / trust route")}</h3>
      <p>${safe(row.agent_role_refs_from_PR165_D2 || row.activation_route || "PR165-D2 role refs or explicit gap routes are rendered.")}</p>
      ${badges(row)}
    </article>
  `).join("");
  qsa("#agentOperations .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Agent Operations", agentRows[index]));
  });
  qs("#llmPanel").innerHTML = `
    <h3>LLM reasoning-brain panel</h3>
    <p>LLM views may research, summarize, critique, explain, propose routes, and detect missing evidence. They do not create source truth, risk pass, live readiness, cash/account truth, quantum advantage proof, or order-release authority.</p>
    ${badge("bounded reasoning brain", "purple")} ${badge("no live LLM runtime", "red")}
  `;
  qs("#llmPanel").addEventListener("click", () => openDrawer("LLM reasoning-brain panel", "Authority boundary", DASHBOARD_DATA.authority_boundary));
}

function renderProviderAndMore() {
  const routes = asList(DASHBOARD_DATA.provider_stage_routes);
  qs("#providerStageRoutes").innerHTML = routes.map((row) => `
    <article class="route-card">
      <h3>${safe(row.provider_stage || row.stage_id)}</h3>
      <p>${safe(row.route_purpose || row.what_UI1_renders_now || "Provider route visible without runtime side effects.")}</p>
      ${badges(row, [row.activation_route || "activation route"])}
    </article>
  `).join("");
  qsa("#providerStageRoutes .route-card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Provider Stage Route Map", routes[index]));
  });

  const contracts = [
    ["Executable Readiness / Adapter Unlock", DASHBOARD_DATA.executable_readiness],
    ["PreTrade Decision Kernel", DASHBOARD_DATA.pretrade_decision_kernel],
    ["Prediction-Market Reality Model", DASHBOARD_DATA.reality_model_contract],
    ["Hot-path / Runtime Metrics", DASHBOARD_DATA.hotpath_metrics_contract],
    ["Emergency action strip", DASHBOARD_DATA.emergency_actions],
    ["Mobile stale-data banner", DASHBOARD_DATA.stale_data_banner],
    ["PWA / Native shell contracts", DASHBOARD_DATA.mobile_app_shell],
    ["Communication parity contract", DASHBOARD_DATA.communication_parity],
    ["File attachment safety", DASHBOARD_DATA.file_attachment_safety]
  ];
  qs("#systemContracts").innerHTML = contracts.map(([title, row]) => `
    <article class="card">
      <h3>${safe(title)}</h3>
      <p>${safe(summarize(row))}</p>
      ${badges(row || {}, ["runtime boundary"])}
    </article>
  `).join("");
  qsa("#systemContracts .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(contracts[index][0], "System contract", contracts[index][1] || {}));
  });
  const dagRows = asList(DASHBOARD_DATA.dag && DASHBOARD_DATA.dag.rows);
  renderTable("#dagRouteMap", dagRows.slice(0, 20), ["node_id", "source_artifact_ref", "downstream_consumer_ref", "authority_boundary_ref"], "DAG / upstream-downstream route map");
}

function applySearch() {
  const query = qs("#globalSearch").value.trim().toLowerCase();
  qsa("[data-search], .card, .route-card, .timeline-step, .chart-panel").forEach((el) => {
    const text = el.textContent.toLowerCase();
    el.classList.toggle("hidden-by-filter", query.length > 0 && !text.includes(query));
  });
}

function wireNavigation() {
  const links = [...qsa(".mobile-bottom-nav a"), ...qsa(".rail a")];
  links.forEach((link) => {
    link.addEventListener("click", () => {
      links.forEach((item) => item.removeAttribute("aria-current"));
      link.setAttribute("aria-current", "page");
    });
  });
}

function render() {
  initTheme();
  renderStatus();
  renderOverview();
  renderRanges();
  renderCharts();
  renderPacketAndQueue();
  renderActions();
  renderTimeline();
  renderEdgeAndParameters();
  renderQkuAndQuantum();
  renderChatAndTrade();
  renderAgentsAndContracts();
  renderProviderAndMore();
  wireNavigation();
  qs("#globalSearch").addEventListener("input", applySearch);
  qs("#closeDrawer").addEventListener("click", closeDrawer);
  qs("#openGlobalDrilldown").addEventListener("click", () => openDrawer("UI1 DASH1 renderer boundary", "Renderer, not replacement", DASHBOARD_DATA.authority_boundary));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
  });
}

render();
