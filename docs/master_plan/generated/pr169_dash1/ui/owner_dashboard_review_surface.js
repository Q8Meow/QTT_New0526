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
  empty_states: { empty_states: [] },
  ui1r1_home: { hero_cards: [], quick_cards: [] },
  ui1r1_dev_mode: { diagnostics: [] },
  ui1r1_chart_manifest: { charts: [] },
  ui1r1_chat_contract: { prompt_chips: [] },
  ui1r1_chat_examples: { examples: [] },
  ui1r1_chat_routes: { routes: [] },
  ui1r1_order_sim: { owner_input_fields: [], preview_buttons: [], comparison_cards: [] },
  ui1r1_edge_alpha: { rows: [] },
  ui1r1_agent_disagreement: { rows: [] },
  ui1r1_parameter_tuning: { rows: [] },
  ui1r1_mobile_parity: { surfaces: [] },
  ui1r1_playwright: { screenshots: [] }
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
    "source_artifact_ref",
    "upstream_artifact_refs",
    "downstream_consumer_refs",
    "owner_action_refs",
    "linked_action_refs",
    "agent_role_refs_from_PR165_D2",
    "PR165_D2_agent_role_refs_or_gap",
    "linked_agent_role_refs",
    "validation_ref",
    "data_ref",
    "data_chart_source_ref",
    "artifact_path",
    "contract_ref",
    "registry_row_ref",
    "authority_boundary_ref",
    "authority_boundary",
    "activation_route",
    "provider_stage",
    "execution_adjusted_rank",
    "TCA_adjusted_expected_net_cash",
    "no_trade_reoptimization_route",
    "quantum_structural_readiness_status"
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
    ["Owner Mode", "Trading workstation"],
    ["Provider state", "Static generated boot data"],
    ["Runtime side effect", "false"],
    ["Execution Router", "provider-pending release route"],
    ["Data freshness", status.boot_data_generated_timestamp || meta.generated_at],
    ["Authority", "request previews only"]
  ];
  qs("#statusGrid").innerHTML = tiles.map(([name, value]) => `
    <div class="status-tile">
      <span class="eyebrow">${safe(name)}</span>
      <span class="value">${safe(label(value))}</span>
    </div>
  `).join("");
}

function renderOverview() {
  const home = DASHBOARD_DATA.ui1r1_home || {};
  const heroCards = asList(home.hero_cards);
  qs("#overviewCards").innerHTML = heroCards.map((row) => `
    <button class="metric-card card owner-hero-card" type="button" data-drawer="${safe(row.widget_id)}">
      <span class="eyebrow">${safe(label(row.widget_id))}</span>
      <span class="value">${safe(row.owner_value)}</span>
      <p>${safe(row.empty_state_reason)}</p>
      ${badge(row.provider_stage || "provider-pending", toneFor(row.provider_stage))}
    </button>
  `).join("");
  qsa("#overviewCards [data-drawer]").forEach((button, index) => {
    button.addEventListener("click", () => openDrawer(label(heroCards[index].widget_id), "Owner Home", heroCards[index]));
  });

  const quickCards = asList(home.quick_cards);
  qs("#homeQuickGrid").innerHTML = quickCards.map((row) => `
    <article class="card quick-card" data-search="${safe(row.title || row.row_id)}">
      <h3>${safe(row.title)}</h3>
      <p>${safe(row.activation_route || "OwnerSurfaceResolver route")}</p>
      ${badges(row, [row.row_id])}
    </article>
  `).join("");
  qsa("#homeQuickGrid .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Owner quick card", quickCards[index]));
  });

  qs("#homeDeveloperSummary").innerHTML = `
    <details class="dev-details">
      <summary>Developer Mode diagnostics</summary>
      <p>Registry counts, artifact paths, validator status, no-orphan detail, authority-boundary detail, and raw refs are secondary diagnostics.</p>
      <a class="inline-link" href="#developer-mode">Open Developer Mode</a>
    </details>
  `;
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

function chartSvg(row, index) {
  const kind = row.chart_kind || row.data_chart_kind || "line";
  const title = row.chart_title || row.chart_id || `chart ${index + 1}`;
  if (kind === "waterfall") {
    const labels = ["gross", "fee", "spread", "slippage", "impact", "latency", "net"];
    return `
      <svg class="chart-svg" viewBox="0 0 420 220" role="img" aria-label="${safe(title)} waterfall frame">
        <line x1="36" y1="182" x2="392" y2="182" class="axis"></line>
        <line x1="36" y1="28" x2="36" y2="182" class="axis"></line>
        ${labels.map((name, i) => {
          const x = 48 + i * 50;
          const h = [92, 36, 44, 52, 48, 38, 62][i];
          const y = 182 - h;
          const cls = i === 0 || i === 6 ? "bar-positive" : "bar-negative";
          return `<rect x="${x}" y="${y}" width="30" height="${h}" class="${cls}"><title>${safe(name)} provider-pending component</title></rect><text x="${x + 15}" y="204" text-anchor="middle">${safe(name)}</text>`;
        }).join("")}
      </svg>
    `;
  }
  if (kind === "donut") {
    return `
      <svg class="chart-svg donut-svg" viewBox="0 0 260 220" role="img" aria-label="${safe(title)} allocation frame">
        <circle cx="130" cy="110" r="70" class="donut-base"></circle>
        <path d="M130 40 A70 70 0 0 1 195 136" class="donut-seg seg-green"></path>
        <path d="M195 136 A70 70 0 0 1 96 171" class="donut-seg seg-blue"></path>
        <path d="M96 171 A70 70 0 0 1 130 40" class="donut-seg seg-purple"></path>
        <text x="130" y="112" text-anchor="middle">provider</text>
        <text x="130" y="132" text-anchor="middle">pending</text>
      </svg>
    `;
  }
  if (kind === "stacked_bar" || kind === "scoreboard" || kind === "bar") {
    return `
      <div class="dom-chart-bars" role="img" aria-label="${safe(title)} visual frame">
        ${["market", "venue", "agent", "QKU stack"].map((name, i) => `
          <div class="bar-row">
            <span>${safe(name)}</span>
            <div class="bar-track"><div class="bar-fill" style="--bar-width:${[72, 54, 44, 62][i]}%;--bar-color:${["var(--qtt-green)", "var(--qtt-blue)", "var(--qtt-purple)", "var(--qtt-orange)"][i]}"></div></div>
            <span>route</span>
          </div>
        `).join("")}
      </div>
    `;
  }
  if (kind === "dag") {
    return `
      <svg class="chart-svg dag-svg" viewBox="0 0 420 220" role="img" aria-label="${safe(title)} DAG frame">
        <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z"></path></marker></defs>
        ${[[70,60,"DASH1"],[205,60,"UI1"],[340,60,"Owner"],[140,150,"Agents"],[280,150,"Providers"]].map(([x,y,t]) => `<rect x="${x - 42}" y="${y - 22}" width="84" height="44" rx="8" class="node"></rect><text x="${x}" y="${y + 5}" text-anchor="middle">${safe(t)}</text>`).join("")}
        <line x1="112" y1="60" x2="163" y2="60" class="edge" marker-end="url(#arrow)"></line>
        <line x1="247" y1="60" x2="298" y2="60" class="edge" marker-end="url(#arrow)"></line>
        <line x1="205" y1="82" x2="150" y2="128" class="edge" marker-end="url(#arrow)"></line>
        <line x1="205" y1="82" x2="270" y2="128" class="edge" marker-end="url(#arrow)"></line>
      </svg>
    `;
  }
  return `
    <svg class="chart-svg" viewBox="0 0 420 220" role="img" aria-label="${safe(title)} line frame">
      <line x1="36" y1="182" x2="392" y2="182" class="axis"></line>
      <line x1="36" y1="28" x2="36" y2="182" class="axis"></line>
      <polyline points="42,156 98,126 154,138 210,88 266,106 322,72 382,92" class="series-line"></polyline>
      <polyline points="42,174 98,164 154,168 210,142 266,150 322,132 382,136" class="series-line muted-line"></polyline>
      ${[["42","156"],["98","126"],["154","138"],["210","88"],["266","106"],["322","72"],["382","92"]].map(([x, y], i) => `<circle cx="${x}" cy="${y}" r="5" class="series-point"><title>${safe(title)} route point ${i + 1}</title></circle>`).join("")}
      <text x="36" y="206">time</text>
      <text x="12" y="34">state</text>
    </svg>
  `;
}

function renderChartPanel(row, index) {
  const title = row.chart_title || row.chart_family || row.chart_id || row.widget_title || `chart ${index + 1}`;
  const chartId = row.data_chart_id || row.chart_id || idOf(row, `chart_${index + 1}`);
  const kind = row.data_chart_kind || row.chart_kind || "line";
  const renderState = row.data_chart_render_state || row.chart_render_state || "PROVIDER_PENDING_VISUAL_FRAME";
  const sourceRef = row.data_chart_source_ref || row.source_artifact_ref || label(row.source_artifact_refs);
  const providerStage = row.data_provider_stage || row.provider_stage || row.dataset_provider_stage || "PRETRADE1";
  return `
    <article class="chart-panel" data-search="${safe(title)}" data-chart-id="${safe(chartId)}" data-chart-kind="${safe(kind)}" data-chart-render-state="${safe(renderState)}" data-chart-source-ref="${safe(sourceRef)}" data-provider-stage="${safe(providerStage)}" data-authority-boundary="${safe(row.data_authority_boundary || row.authority_boundary || row.authority_boundary_ref || "")}">
      <h3>${safe(title)}</h3>
      <p>${safe(row.empty_state_policy || "Provider-pending visual frame with axes, legend, route refs, and no fabricated cash, fills, live positions, or PnL values.")}</p>
      <div class="mini-range" role="group" aria-label="${safe(title)} local range controls">
        ${(row.supported_time_ranges || []).slice(0, 7).map((range, i) => `<button class="seg-button ${i === 0 ? "active" : ""}" type="button" data-local-range="${safe(range)}" aria-pressed="${i === 0 ? "true" : "false"}">${safe(range)}</button>`).join("")}
      </div>
      <div class="chart-canvas provider-frame" role="img" aria-label="${safe(title)} chart contract">
        ${chartSvg(row, index)}
        <div class="provider-overlay">Provider-pending receipts. No fake values rendered.</div>
      </div>
      ${legendHtml()}
      ${badges(row, ["time ranges", "drilldown"])}
    </article>
  `;
}

function renderCharts() {
  const homeCards = asList(DASHBOARD_DATA.ui1r1_home && DASHBOARD_DATA.ui1r1_home.hero_cards);
  const chartRows = asList(DASHBOARD_DATA.ui1r1_chart_manifest && DASHBOARD_DATA.ui1r1_chart_manifest.charts);
  qs("#portfolioCards").innerHTML = homeCards.slice(0, 8).map((row) => `
    <button class="card allocation-card" type="button">
      <h3>${safe(label(row.widget_id))}</h3>
      <p>${safe(row.owner_value || row.empty_state_reason)}</p>
      ${badges(row)}
    </button>
  `).join("");
  qs("#portfolioCards").querySelectorAll(".card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Portfolio slot", homeCards[index]));
  });
  const rows = chartRows.length ? chartRows : asList(DASHBOARD_DATA.charts && DASHBOARD_DATA.charts.chart_families).slice(0, 10);
  qs("#chartGrid").innerHTML = rows.map(renderChartPanel).join("");
  qsa("#chartGrid .chart-panel").forEach((panel, index) => {
    panel.addEventListener("click", () => openDrawer(panel.querySelector("h3").textContent, "Chart drilldown", rows[index]));
  });
  qsa(".mini-range button").forEach((button) => {
    button.addEventListener("click", (event) => {
      const group = event.currentTarget.closest(".mini-range");
      qsa("button", group).forEach((item) => {
        item.classList.toggle("active", item === event.currentTarget);
        item.setAttribute("aria-pressed", item === event.currentTarget ? "true" : "false");
      });
    });
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
  const edge = asList(DASHBOARD_DATA.ui1r1_edge_alpha && DASHBOARD_DATA.ui1r1_edge_alpha.rows);
  qs("#edgeAlphaBoard").innerHTML = edge.map((row) => `
    <article class="card edge-card" data-candidate-id="${safe(row.candidate_id)}">
      <h3>${safe(row.candidate_id || "Execution-adjusted candidate")}</h3>
      <p>Execution-adjusted rank routes through TCA, fill probability, capacity/crowding, FDR, marginal utility, regime memory, no-trade, and quantum structural readiness refs.</p>
      <div class="edge-components">
        ${Object.entries(row.ranking_components || {}).slice(0, 9).map(([name, ref]) => `<span>${safe(label(name))}: ${safe(label(ref))}</span>`).join("")}
      </div>
      ${badges(row, ["not raw edge only", "no fake score"])}
    </article>
  `).join("");
  qsa("#edgeAlphaBoard .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Edge / Alpha Board", edge[index]));
  });

  const params = asList(DASHBOARD_DATA.ui1r1_parameter_tuning && DASHBOARD_DATA.ui1r1_parameter_tuning.rows);
  qs("#parameterControl").innerHTML = params.map((row) => `
    <article class="card parameter-card" data-parameter-id="${safe(row.parameter_id)}">
      <h3>${safe(row.parameter_name || row.parameter_id)}</h3>
      <p>${safe(row.current_live_value_slot)} · candidate: ${safe(row.candidate_value_slot)} · ${safe(row.editability_class)}</p>
      <div class="param-grid">
        <span>Range: ${safe(row.reference_range)}</span>
        <span>Affected: ${safe(label(row.affected_modules))}</span>
        <span>Approval: ${safe(label(row.owner_approval_required))}</span>
      </div>
      ${badges(row, ["atomic drilldown", "no live mutation"])}
    </article>
  `).join("");
  qsa("#parameterControl .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Parameter atomic drilldown", params[index]));
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

function inferIntentFamily(text) {
  const lower = text.toLowerCase();
  if (lower.includes("no-trade") || lower.includes("no trade")) {
    return lower.includes("why") || lower.includes("explain") ? "NO_TRADE_EXPLANATION_REQUEST" : "NO_TRADE_REOPTIMIZATION_REQUEST";
  }
  if (lower.includes("research") || lower.includes("article") || lower.includes("link")) return "RESEARCH_ANALYSIS_REQUEST";
  if (lower.includes("formula") || lower.includes("qku") || lower.includes("stack")) return "QKU_FORMULA_STACK_COMPARISON_REQUEST";
  if (lower.includes("replay") || lower.includes("paper")) return "REPLAY_PAPER_REQUEST";
  if (lower.includes("agent") && (lower.includes("disagree") || lower.includes("object"))) return "AGENT_DISAGREEMENT_QUESTION";
  if (lower.includes("cost") || lower.includes("tca") || lower.includes("slippage")) return "TCA_COST_EXPLANATION_REQUEST";
  if (lower.includes("risk") || lower.includes("capacity")) return "RISK_CAPACITY_EXPLANATION_REQUEST";
  if (lower.includes("parameter") || lower.includes("variable")) return "PARAMETER_TUNING_REQUEST";
  if (lower.includes("edge") || lower.includes("alpha") || lower.includes("rank")) return "EDGE_ALPHA_RANKING_REQUEST";
  if (lower.includes("live") || lower.includes("canary")) return "LIVE_CANARY_REVIEW_REQUEST_PREVIEW";
  if (lower.includes("kill")) return "KILL_SWITCH_REQUEST_PREVIEW";
  if (lower.includes("trade") || lower.includes("market") || lower.includes("best")) return "TRADE_CHECK_REQUEST";
  return "GENERAL_QTT_QUESTION_PROVIDER_PENDING";
}

function targetWorkspaceForIntent(intentFamily) {
  if (/TRADE|REPLAY|PAPER|NO_TRADE|PARAMETER|TCA|RISK|CAPACITY/.test(intentFamily)) return "Trade Workbench";
  if (/RESEARCH|SOURCE|FORMULA|QKU|QUANTUM/.test(intentFamily)) return "Research Intake";
  if (/AGENT/.test(intentFamily)) return "Agents";
  if (/EDGE|ALPHA/.test(intentFamily)) return "Edge / Alpha Board";
  return "Owner Home";
}

function buildOwnerIntentPreview(rawText) {
  const text = rawText.trim() || "Check this market for a positive expected net-cash trade.";
  const intentFamily = inferIntentFamily(text);
  const targetWorkspace = targetWorkspaceForIntent(intentFamily);
  const previewObjects = intentFamily.includes("RESEARCH")
    ? ["OwnerPlainEnglishIntentV1", "OwnerResearchSubmissionV1", "SourceCandidateV1", "FormulaExtractionCandidateV1"]
    : intentFamily.includes("QKU") || intentFamily.includes("FORMULA")
      ? ["OwnerPlainEnglishIntentV1", "QKUCandidateMaterializationRequestV1", "QuantumStructureMappingRequestV1"]
      : intentFamily.includes("NO_TRADE")
        ? ["OwnerPlainEnglishIntentV1", "NoTradeReoptimizationRequestPreviewV1", "TradePlanCandidateV1"]
        : ["OwnerPlainEnglishIntentV1", "OwnerTradeIntentV1", "OwnerTradeCheckRequestV1", "ReplayPaperRequestPreviewV1"];
  return {
    object_type: "OwnerPlainEnglishIntentV1",
    intent_id: `LOCAL_PREVIEW_${Date.now()}`,
    thread_id: targetWorkspace === "Research Intake" ? "OWNER_THREAD_RESEARCH_INTAKE" : "OWNER_THREAD_TRADE_WORKBENCH",
    owner_message_ref: "OwnerMessageV1::local_preview",
    raw_owner_text_excerpt: text.slice(0, 140),
    plain_english_summary: label(intentFamily),
    intent_family: intentFamily,
    confidence_label: text.length > 18 ? "HIGH_CONFIDENCE_PREVIEW" : "MEDIUM_CONFIDENCE_PREVIEW",
    clarifying_question_if_needed: text.length > 18
      ? "No clarification needed for this high-confidence preview."
      : "Which market, source, or candidate should QTT inspect?",
    target_workspace: targetWorkspace,
    owner_action_preview_refs: ["REQUEST_OWNER_REVIEW"],
    structured_request_preview_refs: previewObjects,
    agent_role_refs_from_PR165_D2_or_gap: ["dashboard_agent", "governance_agent", "commander_agent"],
    LLM_provider_stage_ref: "LLM1_PROVIDER_PENDING",
    agent_orchestration_provider_stage_ref: "AGENT_ORCH1_PROVIDER_PENDING",
    paper_loop_provider_stage_ref: "PAPER_LOOP_PROVIDER_PENDING",
    execution_router_provider_pending_ref: "Execution_Router_release_route_provider_pending",
    runtime_side_effect: false,
    authority_boundary_ref: "LOCAL_STATIC_NO_RUNTIME_NO_CREDENTIALS_NO_DIRECT_VENUE_SUBMIT_NO_EXECUTION_ROUTER_RELEASE"
  };
}

function renderIntentReceipt(preview) {
  const receipt = qs("#chatReceiptPreview");
  receipt.innerHTML = `
    <article class="card receipt-card" data-preview-object="OwnerPlainEnglishIntentV1">
      <h3>OwnerPlainEnglishIntentV1 preview</h3>
      <p>${safe(preview.plain_english_summary)} routes to ${safe(preview.target_workspace)}. QTT would ask provider-stage LLM/agent/paper services for evidence later; UI1 does not call them.</p>
      <div class="preview-grid">
        <span>Intent: ${safe(preview.intent_family)}</span>
        <span>Objects: ${safe(label(preview.structured_request_preview_refs))}</span>
        <span>Agents: ${safe(label(preview.agent_role_refs_from_PR165_D2_or_gap))}</span>
        <span>Runtime side effect: false</span>
      </div>
      ${badges(preview, ["provider-pending English response", "receipt preview"])}
    </article>
  `;
  receipt.querySelector(".receipt-card").addEventListener("click", () => openDrawer("OwnerPlainEnglishIntentV1 preview", "Chat route receipt", preview));
}

function renderChatAndTrade() {
  const chatContract = DASHBOARD_DATA.ui1r1_chat_contract || {};
  const examples = asList(DASHBOARD_DATA.ui1r1_chat_examples && DASHBOARD_DATA.ui1r1_chat_examples.examples);
  const routes = asList(DASHBOARD_DATA.ui1r1_chat_routes && DASHBOARD_DATA.ui1r1_chat_routes.routes);
  qs("#chatWorkspace").innerHTML = `
    <article class="card chat-composer-card" data-chat-composer="owner-plain-english" data-chat-runtime-side-effect="false" data-intent-parser="local-preview" data-provider-stage="LLM1">
      <h3>Plain-English QTT command</h3>
      <label class="field-label" for="ownerChatInput">Message</label>
      <textarea id="ownerChatInput" rows="5" placeholder="Ask QTT agents to research, analyze, compare, or check a trade...">Can QTT check this market and find the best trade?</textarea>
      <div class="control-row">
        <label>Agent pod <select id="chatAgentSelector"><option>All QTT Agents</option><option>Risk + TCA</option><option>Research + QKU</option><option>Quantum readiness</option></select></label>
        <label>Source family <select id="chatSourceFamily"><option>Auto route</option><option>Market or event page</option><option>Research article</option><option>Formula text</option></select></label>
      </div>
      <div class="control-row">
        <input id="chatLinkInput" type="url" aria-label="Link input" placeholder="Optional source link">
        <button id="chatAttachmentPreview" type="button">File preview</button>
      </div>
      <div class="chip-row prompt-chip-row">
        ${asList(chatContract.prompt_chips).map((chip) => `<button class="chip" type="button" data-chat-chip="${safe(chip)}">${safe(chip)}</button>`).join("")}
      </div>
      <button id="routePreviewButton" class="primary-command" type="button">Route Preview</button>
      ${badge("no runtime side effect", "red")} ${badge("local preview parser", "blue")}
    </article>
    <div id="chatReceiptPreview" class="chat-receipt-column"></div>
    <article class="card route-card">
      <h3>Chat-to-trade route</h3>
      <p>${safe(label((routes[0] || {}).route_chain || "OwnerPlainEnglishIntentV1 to Trade Workbench route"))}</p>
      ${badges(routes[0] || {}, ["Execution Router provider-pending"])}
    </article>
    <article class="card route-card">
      <h3>Chat-to-research route</h3>
      <p>${safe(label((routes[1] || {}).route_chain || "OwnerResearchSubmissionV1 to source/QKU route"))}</p>
      ${badges(routes[1] || {}, ["source truth not accepted"])}
    </article>
  `;
  const firstExample = examples[0] && examples[0].parsed_preview_output ? examples[0].parsed_preview_output : buildOwnerIntentPreview(qs("#ownerChatInput").value);
  renderIntentReceipt(firstExample);
  qsa("[data-chat-chip]").forEach((chip) => {
    chip.addEventListener("click", () => {
      qs("#ownerChatInput").value = chip.dataset.chatChip;
      renderIntentReceipt(buildOwnerIntentPreview(chip.dataset.chatChip));
    });
  });
  qs("#routePreviewButton").addEventListener("click", () => renderIntentReceipt(buildOwnerIntentPreview(qs("#ownerChatInput").value)));
  qsa("#chatWorkspace .route-card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Chat route preview", routes[index] || {}));
  });

  const workbench = DASHBOARD_DATA.ui1r1_order_sim || DASHBOARD_DATA.trade_workbench || {};
  const fields = asList(workbench.owner_input_fields);
  const buttons = asList(workbench.preview_buttons);
  const comparisons = asList(workbench.comparison_cards);
  qs("#tradeWorkbench").innerHTML = `
    <article class="card workbench-form-card" data-workbench-id="${safe(workbench.workbench_id || "OWNER_TRADE_WORKBENCH")}" data-owner-trade-intent-preview="OwnerTradeIntentV1" data-no-trade-comparator="true" data-champion-challenger-preview="true" data-tca-route="true" data-fdr-route="true" data-portfolio-marginal-utility-route="true" data-quantum-structural-readiness-route="true" data-execution-router-provider-pending="true">
      <h3>Order simulator preview</h3>
      <div class="workbench-fields">
        ${fields.map((row) => `
          <label>${safe(label(row.field_id))}
            <input data-trade-variable-field="${safe(row.field_id)}" value="${safe(row.current_value_slot || "")}" aria-label="${safe(row.field_id)}">
          </label>
        `).join("")}
      </div>
      <div class="chip-row action-row">
        ${buttons.map((row) => `<button class="chip" type="button" data-preview-button="${safe(row.button_id)}">${safe(label(row.button_id))}</button>`).join("")}
      </div>
      ${badge("local request preview only", "red")} ${badge("Execution Router provider-pending", "gray")}
    </article>
    ${comparisons.map((row) => `
      <article class="card comparison-card" data-comparison-card="${safe(row.card_id)}">
        <h3>${safe(label(row.card_id))}</h3>
        <p>${safe(row.route_ref)}. Score/value provider-pending; no fake PnL, fill, or live-position result.</p>
        ${badges(row, ["TradePlanCandidateV1"])}
      </article>
    `).join("")}
    <article class="card">
      <h3>No-trade reoptimization paths</h3>
      <p>${safe(label(workbench.no_trade_reoptimization_paths))}</p>
      ${badge("no-trade is comparator", "blue")}
    </article>
    <article class="card">
      <h3>Decision spine routes</h3>
      <p>${safe(label(Object.keys(workbench.decision_spine_refs || {}).slice(0, 10)))}</p>
      ${badge("institutional refs linked", "green")} ${badge("quantum readiness routed", "purple")}
    </article>
  `;
  qsa("#tradeWorkbench .card").forEach((card) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Trade Workbench", workbench));
  });
}

function renderAgentsAndContracts() {
  const disagreement = asList(DASHBOARD_DATA.ui1r1_agent_disagreement && DASHBOARD_DATA.ui1r1_agent_disagreement.rows);
  const agentRows = [
    ...disagreement,
    ...asList(DASHBOARD_DATA.agent_performance),
    ...asList(DASHBOARD_DATA.widget_manifest).filter((row) => /Agent|KPI|Trust|Quarantine|Replacement|Reroute/i.test(label(row.widget_title || row.widget_id))).slice(0, 12)
  ];
  qs("#agentOperations").innerHTML = agentRows.slice(0, 14).map((row) => `
    <article class="card agent-card" data-objection-type="${safe(row.objection_type || "")}">
      <h3>${safe(row.objection_type || row.widget_title || row.agent_id || row.chart_id || "Agent KPI / trust route")}</h3>
      <p>${safe(row.linked_evidence_ref_or_provider_pending_route || row.agent_role_refs_from_PR165_D2 || row.activation_route || "PR165-D2 role refs or explicit gap routes are rendered.")}</p>
      ${row.objection_type ? `<div class="bar-row"><span>Objection</span><div class="bar-track"><div class="bar-fill" style="--bar-width:66%;--bar-color:var(--qtt-orange)"></div></div><span>routed</span></div>` : ""}
      ${badges(row, row.objection_type ? ["no fake agent claim"] : [])}
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

function renderDeveloperMode() {
  const dev = DASHBOARD_DATA.ui1r1_dev_mode || {};
  const diagnostics = asList(dev.diagnostics);
  qs("#developerMode").innerHTML = `
    <details class="developer-details">
      <summary>Developer diagnostics</summary>
      <div class="developer-grid">
        ${diagnostics.map((row) => `
          <article class="card developer-card">
            <h3>${safe(label(row.diagnostic_id))}</h3>
            <p>${safe(label(row.value_ref))}</p>
            ${badge(row.owner_default === false ? "not Owner Mode primary" : "diagnostic", "gray")}
          </article>
        `).join("")}
      </div>
      <div class="table-shell raw-ref-table">
        <h3>Raw refs and report diagnostics</h3>
        <table>
          <thead><tr><th>Area</th><th>Ref</th><th>Owner default</th></tr></thead>
          <tbody>
            <tr><td>OwnerActionRegistry</td><td>owner_action_registry.generated.jsonl</td><td>false</td></tr>
            <tr><td>OwnerSurfaceResolver</td><td>src/qtt/dashboard/owner_surface_resolver.py</td><td>false</td></tr>
            <tr><td>No-orphan report</td><td>owner_dashboard_no_orphan.report.json</td><td>false</td></tr>
            <tr><td>Authority boundary</td><td>owner_dashboard_authority_boundary.report.json</td><td>false</td></tr>
            <tr><td>Playwright evidence</td><td>ui1r1_playwright.report.json</td><td>false</td></tr>
          </tbody>
        </table>
      </div>
    </details>
  `;
  qsa("#developerMode .card").forEach((card, index) => {
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Developer Mode", diagnostics[index] || dev));
  });
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
  renderDeveloperMode();
  wireNavigation();
  qs("#globalSearch").addEventListener("input", applySearch);
  qs("#closeDrawer").addEventListener("click", closeDrawer);
  qs("#openGlobalDrilldown").addEventListener("click", () => openDrawer("UI1 DASH1 renderer boundary", "Renderer, not replacement", DASHBOARD_DATA.authority_boundary));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawer();
  });
}

render();
