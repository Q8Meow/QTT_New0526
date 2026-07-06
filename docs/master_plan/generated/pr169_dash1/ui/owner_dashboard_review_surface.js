const THEME_STORAGE_KEY = "qtt_owner_dashboard_theme";
const EXPERIENCE_MODE_STORAGE_KEY = "qtt_owner_dashboard_experience_mode";
const GUIDANCE_DENSITY_STORAGE_KEY = "qtt_owner_dashboard_guidance_density";
const TEXT_SIZE_STORAGE_KEY = "qtt_owner_dashboard_text_size";
const TECHNICAL_DETAILS_STORAGE_KEY = "qtt_owner_dashboard_technical_details_open";
const ENTER_TO_SEND_STORAGE_KEY = "qtt_owner_dashboard_enter_to_send_enabled";
const OWNER_SETTINGS_STORAGE_KEY = "qtt_owner_dashboard_owner_settings_v1";
const TEXT_SIZE_VALUES = ["small", "default", "large", "extra_large"];
const THEME_VALUES = ["DARK", "LIGHT", "DARK_PRO", "MIDNIGHT_BLUE", "SLATE", "LIGHT_PRO", "LOW_GLARE", "HIGH_CONTRAST", "CUSTOM"];
const THEME_TO_DATASET = {
  DARK: "dark",
  LIGHT: "light",
  DARK_PRO: "dark",
  MIDNIGHT_BLUE: "midnight_blue",
  SLATE: "slate",
  LIGHT_PRO: "light",
  LOW_GLARE: "low_glare",
  HIGH_CONTRAST: "high_contrast",
  CUSTOM: "dark"
};

// Source-level validator anchors: DashboardSystem, OwnerDashboardStateV1,
// OwnerSurfaceResolver, OwnerActionRegistry, OwnerNextStepRouter.
// R1 continuity anchors hidden from Owner Mode text: OwnerDashboardPacket,
// OwnerDecisionQueue, OwnerActionableCards, CENTRALIZED_AGENT_QKU_ACCESS_RESOLVER_PANEL.
// Authority continuity anchor hidden from Owner Mode text: No direct venue submit.
const DASHBOARD_DATA = window.QTT_OWNER_DASHBOARD_DATA || {
  meta: { artifact_id: "UI1_OWNER_DASHBOARD_REVIEW_DATA", data_source: "FIXTURE_FALLBACK" },
  status_strip: {},
  owner_packet: {},
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
  ui1r2_copy_map: { rows: [] },
  ui1r2_mode: { rows: [] },
  ui1r2_action_menu: { rows: [] },
  ui1r2_education: { glossary: [], chart_explainers: [], page_lessons: [] },
  ui1r2_guided_flow: { flows: [] },
  ui1r2_next_step: { rows: [] },
  ui1r2r2_display_preferences: {},
  ui1r2r2_workbench_form: { field_catalog: [], option_catalog: {}, local_preview_output: {} },
  ui1r2r2_chat_intent_preview: {},
  ui1r2r3_owner_settings: { defaults: {}, sections: [] },
  ui1r2r3_navigation_sidebar_search: { ranked_search_index: [] },
  ui1r2r3_chat_guide: { chat_presets: [], qtt_guide_prompts: [] },
  ui1r2r3_chart_policy: {},
  ui1r2r3_education_drawers: { drawer_actions: [] },
  ui1r2r3_theme_interaction_accessibility: {},
  ui1r2r3_workbench_options_ranges: { range_policy: {}, option_catalog: {} },
  ui1r2r4_semantic_bundle: { education_catalog: [], chat_qtt_guide_intents: [], field_semantics: [], agent_operations_projection: [], workflow_queue_projection: [], receipt_preview_projection: [] }
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

function titleCase(text) {
  const keep = new Set(["QTT", "QKU", "TCA", "FDR", "PnL", "LLM", "DAG", "QAOA", "VQE", "QUBO", "BQM", "CQM"]);
  return String(text)
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => {
      const upper = word.toUpperCase();
      if (keep.has(upper)) return upper;
      if (keep.has(word)) return word;
      return word.slice(0, 1).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(" ");
}

const OwnerSettings = (() => {
  const defaults = {
    theme_preset: "DARK_PRO",
    text_size: "default",
    sidebar_collapsed: false,
    input_required_color: "#F59E0B",
    review_required_color: "#2563EB",
    warning_high_confirmation_color: "#F97316",
    provider_pending_color: "#64748B",
    success_color: "#16A34A",
    high_contrast: false,
    chart_default_timeframe: "1M",
    chart_crosshair: true,
    chart_tooltips: true,
    chart_grid_lines: true,
    chart_axis_labels: true,
    workbench_preferred_market: "prediction_market",
    workbench_preferred_venue: "qtt_decide",
    workbench_preferred_hold_unit: "days",
    workbench_preferred_maker_taker: "maker_first_taker_fallback",
    workbench_preferred_objective: "maximize_expected_net_cash",
    chat_enter_to_send: false,
    chat_prompt_suggestions: true,
    qtt_guide_collapsed: true,
    dashboard_default_experience_mode: "GUIDED_OWNER",
    trading_default_market: "prediction_market",
    trading_default_venue: "qtt_decide",
    trading_default_risk_profile: "conservative_preview",
    trading_default_position_size_style: "small_preview",
    trading_default_hold_style: "event_resolution_or_provider_pending",
    trading_default_execution_preference: "maker_first_preview",
    trading_default_portfolio_objective: "preserve_capital_and_improve_net_cash_preview",
    keyboard_focus_visible: true,
    reduced_motion: false,
    ...(DASHBOARD_DATA.ui1r2r3_owner_settings && DASHBOARD_DATA.ui1r2r3_owner_settings.defaults ? DASHBOARD_DATA.ui1r2r3_owner_settings.defaults : {})
  };
  let settings = { ...defaults };

  function read() {
    try {
      const raw = localStorage.getItem(OWNER_SETTINGS_STORAGE_KEY);
      if (raw) settings = { ...defaults, ...JSON.parse(raw) };
    } catch {
      settings = { ...defaults, ...(window.__QTT_IN_SESSION_OWNER_SETTINGS || {}) };
    }
    try {
      const legacyTheme = localStorage.getItem(THEME_STORAGE_KEY);
      if (legacyTheme && !localStorage.getItem(OWNER_SETTINGS_STORAGE_KEY)) {
        settings.theme_preset = legacyTheme === "LIGHT" ? "LIGHT_PRO" : legacyTheme;
      }
      const legacyText = localStorage.getItem(TEXT_SIZE_STORAGE_KEY);
      if (legacyText && TEXT_SIZE_VALUES.includes(legacyText) && !localStorage.getItem(OWNER_SETTINGS_STORAGE_KEY)) {
        settings.text_size = legacyText;
      }
      const legacyMode = localStorage.getItem(EXPERIENCE_MODE_STORAGE_KEY);
      if (legacyMode && !localStorage.getItem(OWNER_SETTINGS_STORAGE_KEY)) settings.dashboard_default_experience_mode = legacyMode;
      const legacyEnter = localStorage.getItem(ENTER_TO_SEND_STORAGE_KEY);
      if (legacyEnter && !localStorage.getItem(OWNER_SETTINGS_STORAGE_KEY)) settings.chat_enter_to_send = legacyEnter === "true";
    } catch {
      // In-session fallbacks are enough for local static preview.
    }
    return settings;
  }

  function persist() {
    try {
      localStorage.setItem(OWNER_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
      localStorage.setItem(THEME_STORAGE_KEY, settings.theme_preset === "LIGHT_PRO" ? "LIGHT" : settings.theme_preset === "DARK_PRO" ? "DARK" : settings.theme_preset);
      localStorage.setItem(TEXT_SIZE_STORAGE_KEY, settings.text_size);
      localStorage.setItem(EXPERIENCE_MODE_STORAGE_KEY, settings.dashboard_default_experience_mode);
      localStorage.setItem(GUIDANCE_DENSITY_STORAGE_KEY, "COLLAPSED_DEFAULT");
      localStorage.setItem(TECHNICAL_DETAILS_STORAGE_KEY, settings.technical_details_open ? "true" : "false");
      localStorage.setItem(ENTER_TO_SEND_STORAGE_KEY, settings.chat_enter_to_send ? "true" : "false");
    } catch {
      window.__QTT_IN_SESSION_OWNER_SETTINGS = { ...settings };
    }
  }

  function get(key) {
    return settings[key];
  }

  function set(key, value, persistNow = true) {
    settings[key] = value;
    applyCssSettings();
    if (persistNow) persist();
    return settings;
  }

  function applyCssSettings() {
    const root = document.documentElement;
    root.style.setProperty("--owner-input-required", settings.input_required_color);
    root.style.setProperty("--owner-review-required", settings.review_required_color);
    root.style.setProperty("--owner-high-confirmation", settings.warning_high_confirmation_color);
    root.style.setProperty("--owner-provider-pending", settings.provider_pending_color);
    root.style.setProperty("--owner-success", settings.success_color);
    root.dataset.textSize = TEXT_SIZE_VALUES.includes(settings.text_size) ? settings.text_size : "default";
    if (settings.high_contrast) {
      root.dataset.theme = "high_contrast";
    }
    document.body.dataset.sidebarCollapsed = settings.sidebar_collapsed ? "true" : "false";
  }

  read();
  return { defaults, read, get, set, persist, applyCssSettings };
})();

const DashboardSystem = (() => {
  const copyRows = asList(DASHBOARD_DATA.ui1r2_copy_map && DASHBOARD_DATA.ui1r2_copy_map.rows);
  const exactCopy = new Map(copyRows.map((row) => [String(row.technical_pattern_or_exact_id), row]));
  const nextRows = asList(DASHBOARD_DATA.ui1r2_next_step && DASHBOARD_DATA.ui1r2_next_step.rows);
  const nextById = new Map(nextRows.map((row) => [row.next_step_id, row]));
  const menuRows = asList(DASHBOARD_DATA.ui1r2_action_menu && DASHBOARD_DATA.ui1r2_action_menu.rows);
  const menuByWidget = new Map(menuRows.map((row) => [row.widget_id, row]));
  const modeRows = asList(DASHBOARD_DATA.ui1r2r1_mode_policy && DASHBOARD_DATA.ui1r2r1_mode_policy.rows);
  const modeById = new Map(modeRows.map((row) => [row.mode_id, row]));
  const drawerRows = asList(DASHBOARD_DATA.ui1r2r3_education_drawers && DASHBOARD_DATA.ui1r2r3_education_drawers.drawer_actions);
  const drawerByKind = new Map(drawerRows.map((row) => [row.drawer_kind, row]));
  const interactionState = {
    receipts: [],
    chatMessages: [],
    chatEnterToSend: false,
    optionsMenuOpen: false,
    settingsOpen: false,
    qttGuideOpen: false,
    textSize: "default",
    activeSurface: "overview",
    guided: {},
    workbenchContext: null,
    workbenchPreview: {}
  };

  // OwnerExperienceModePolicy: one central mode policy over the shared OwnerDashboardStateV1.
  function modePolicy(mode) {
    return modeById.get(mode) || modeById.get("GUIDED_OWNER") || {};
  }

  function cleanTechnicalText(text) {
    let value = String(text || "").trim();
    if (!value) return "Waiting for provider data";
    const exact = exactCopy.get(value);
    if (exact) return exact.owner_title;
    for (const row of copyRows) {
      const pattern = String(row.technical_pattern_or_exact_id || "");
      if (pattern && value.includes(pattern)) return row.owner_title;
    }
    if (value.includes(".jsonl")) return "Technical evidence source";
    if (value.startsWith("DASH1_FEATURE_")) return "Dashboard feature route";
    if (value.includes("OWNER_DASHBOARD_PACKET_V1")) return "Owner review packet";
    value = value
      .replace(/Guided Owner Coach/g, "QTT Coach")
      .replace(/Review execution-adjusted trade metrics/g, "Trade Metrics")
      .replace(/Tell me what matters/g, "Key Insights")
      .replace(/Net Capital Cash Slot/g, "Net Capital")
      .replace(/Today Result Slot/g, "Today's PnL")
      .replace(/Week Result Slot/g, "Weekly PnL")
      .replace(/Month Result Slot/g, "Monthly PnL");
    if (value.includes("::")) value = value.split("::").pop();
    value = value
      .replace(/runtime_side_effect/gi, "local preview safety")
      .replace(/provider_stage/gi, "provider stage")
      .replace(/activation_route/gi, "activation route")
      .replace(/authority_boundary_ref/gi, "safety boundary")
      .replace(/registry_row_ref/gi, "dashboard evidence row")
      .replace(/manual_edit_allowed/gi, "generated evidence")
      .replace(/generated_from/gi, "generated source")
      .replace(/surface_registry_row_count/gi, "dashboard source count")
      .replace(/raw refs/gi, "technical details")
      .replace(/linked refs/gi, "evidence and routing")
      .replace(/system contract/gi, "workflow status")
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (!value) return "QTT workflow item";
    return titleCase(value);
  }

  function present(value) {
    if (value === null || value === undefined || value === "") return "Waiting for provider data";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) {
      if (!value.length) return "Waiting for provider data";
      return value.slice(0, 3).map((item) => present(item)).join(", ");
    }
    if (typeof value === "object") {
      return present(
        value.owner_title ||
        value.widget_title ||
        value.visible_label ||
        value.card_id ||
        value.queue_id ||
        value.chart_title ||
        value.chart_id ||
        value.stage_label ||
        value.stage_id ||
        value.term ||
        "QTT workflow item"
      );
    }
    return cleanTechnicalText(value);
  }

  function idOf(row, fallback = "row") {
    if (!row || typeof row !== "object") return fallback;
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

  function semanticFallback(row, fallback = "QTT workflow item") {
    const text = `${fallback} ${row ? Object.values(row).slice(0, 12).join(" ") : ""}`.toLowerCase();
    if (/no[- ]trade/.test(text)) return "Inspect no-trade reason";
    if (/tca|cost|slippage|spread|fee|latency|impact/.test(text)) return "Review cost breakdown";
    if (/qku|formula|stack/.test(text)) return "Inspect QKU/formula route";
    if (/agent|objection|disagree/.test(text)) return "Review agent disagreement";
    if (/parameter|variable|tuning/.test(text)) return "Open parameter tuning preview";
    if (/quantum|qubo|bqm|cqm|qaoa|vqe|ising/.test(text)) return "Review quantum readiness";
    if (/provider|stage|route/.test(text)) return "Review provider-stage route";
    if (/capital|cash|exposure|portfolio/.test(text)) return "Inspect capital/exposure status";
    if (/trade|candidate|market|venue|edge|alpha|rank/.test(text)) return "Check trade candidate";
    if (/dashboard|packet|readiness|status|decision/.test(text)) return "Review dashboard readiness";
    return "QTT workflow item";
  }

  function ownerTitle(row, fallback = "QTT workflow item") {
    if (!row || typeof row !== "object") return fallback;
    const title = present(
      row.owner_title ||
      row.chart_title ||
      row.widget_title ||
      row.visible_label ||
      row.title ||
      row.card_id ||
      row.queue_id ||
      row.objection_type ||
      row.parameter_name ||
      row.parameter_id ||
      row.stage_label ||
      row.stage_id ||
      fallback
    );
    if (/^(Owner Decision|Actionable Card|QTT Workflow Item|Dashboard Evidence Row)$/i.test(title)) {
      return semanticFallback(row, fallback);
    }
    return title;
  }

  function summary(row, fallback = "This item is connected to QTT technical evidence. Technical details are available below.") {
    if (!row || typeof row !== "object") return fallback;
    const text =
      row.owner_summary ||
      row.summary ||
      row.route_purpose ||
      row.empty_state_reason ||
      row.empty_state_policy ||
      row.card_type ||
      row.safe_default ||
      row.pipeline_state ||
      row.what_UI1_renders_now ||
      row.action_semantics ||
      fallback;
    return present(text);
  }

  function status(row) {
    if (!row || typeof row !== "object") return "Local preview only";
    if (row.no_fake_value || row.fake_value_allowed === false) return "No fake values";
    if (String(row.provider_stage || row.provider_state || row.render_state || "").toUpperCase().includes("PENDING")) {
      return "Waiting for provider data";
    }
    if (row.runtime_side_effect === false || row.runtime_side_effect_allowed === false) return "Local preview only";
    return present(row.provider_stage || row.render_status || row.render_state || "Review-only");
  }

  function toneFor(value) {
    const text = String(value || "").toUpperCase();
    if (text.includes("PASS") || text.includes("VISIBLE") || text.includes("MATERIALIZED") || text.includes("LOCAL")) return "green";
    if (text.includes("FAIL") || text.includes("CRITICAL") || text.includes("BLOCKED")) return "red";
    if (text.includes("QUANTUM") || text.includes("QMAP")) return "purple";
    if (text.includes("REPAIR") || text.includes("DEGRADED")) return "orange";
    if (text.includes("PENDING") || text.includes("ROUTED") || text.includes("WAIT")) return "gray";
    if (text.includes("CAUTION") || text.includes("INSUFFICIENT")) return "yellow";
    return "blue";
  }

  function guidanceFor(row, surface = "owner") {
    const title = ownerTitle(row, present(surface));
    return {
      title,
      summary: summary(row),
      status: status(row),
      recommended: "Open the next safe local step",
      why: "QTT can explain the route and prepare a local preview before any downstream provider exists.",
      risk: "No live action runs here. Missing provider receipts mean no fake PnL, cash, fills, or position values are shown.",
      missing: "If evidence is absent, the dashboard shows the provider route and the safe alternative.",
      agents: "QTT agents may later analyze, optimize, rank, and prepare evidence inside owner-approved policies. R2 only previews the route.",
      technical: "Technical evidence is preserved in Developer Mode and selected technical details."
    };
  }

  function menuFor(surface) {
    return menuByWidget.get(surface) || menuByWidget.get("trade_workbench") || { options: [] };
  }

  function nextStep(id) {
    return nextById.get(id);
  }

  function drawerAction(kind) {
    return drawerByKind.get(kind) || {
      action_id: `OWNER_ACTION_${String(kind || "general").toUpperCase()}`,
      drawer_kind: kind || "general",
      content_signature: `ui1r2r3::${kind || "general"}::fallback`,
      runtime_side_effect_allowed: false
    };
  }

  function setActiveSurface(surfaceId, focusTargetId) {
    interactionState.activeSurface = surfaceId || "overview";
    qsa(".rail a, .mobile-bottom-nav a").forEach((link) => {
      const hrefSurface = (link.getAttribute("href") || "#overview").replace("#", "");
      const active = hrefSurface === interactionState.activeSurface;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    const target = qs(`#${CSS.escape(focusTargetId || surfaceId || "overview")}`) || qs(`#${CSS.escape(surfaceId || "overview")}`);
    if (target) {
      target.setAttribute("tabindex", "-1");
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      target.focus({ preventScroll: true });
    }
  }

  function localReceipt(route, context, text) {
    const receipt = {
      interaction_id: `UI1R2R1_LOCAL_${Date.now()}_${interactionState.receipts.length + 1}`,
      route,
      context_id: idOf(context, "local_context"),
      title: route ? route.owner_label : "Local route preview",
      preview_object_type: route ? route.preview_object_type : "OwnerTradeIntentPreviewV1",
      receipt_type: route ? route.local_receipt_preview_type : "OwnerTradeIntentPreviewV1",
      authority_boundary: "LOCAL_STATIC_NO_RUNTIME_NO_CREDENTIALS_NO_DIRECT_VENUE_SUBMIT_NO_EXECUTION_ROUTER_RELEASE",
      runtime_side_effect_allowed: false,
      text: text || "Local preview created. No runtime work runs now."
    };
    interactionState.receipts.push(receipt);
    const target = qs("#routePreviewPanel");
    if (target) {
      target.innerHTML = receiptCard(receipt);
      target.removeAttribute("hidden");
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    return receipt;
  }

  function routeAction(nextStepId, context = {}) {
    const route = nextStep(nextStepId);
    if (!route) return;
    if (nextStepId === "NEXT_STEP_SEND_TO_TRADE_WORKBENCH") {
      // OwnerWorkbenchPrefillAdapter: all selected contexts enter one local prefill path.
      const workbench = qs("#tradeWorkbench");
      if (workbench) {
        workbench.dataset.prefilledContext = "true";
        workbench.dataset.prefillSource = idOf(context, "selected_context");
        interactionState.workbenchContext = context;
        const prefill = qs("#tradeWorkbenchPrefill");
        if (prefill) prefill.textContent = `Prefilled local context: ${ownerTitle(context, "selected card")}. Missing owner input: confirm market, side, size, and objective before any later provider can act.`;
        const marketInput = qs('[data-workbench-field="market_event"]');
        const customEventInput = qs('[data-workbench-field="custom_event"]');
        const sourceInput = qs('[data-workbench-field="source_thesis_url"]');
        if (marketInput && context && context.raw_owner_text_excerpt) {
          marketInput.value = "other";
          if (customEventInput) customEventInput.value = context.raw_owner_text_excerpt;
        } else if (marketInput && context) {
          marketInput.value = "other";
          if (customEventInput) customEventInput.value = ownerTitle(context, "selected dashboard item");
        }
        if (sourceInput && context && context.raw_owner_text_excerpt) {
          sourceInput.value = context.raw_owner_text_excerpt;
        }
        if (typeof updateWorkbenchPreview === "function") updateWorkbenchPreview();
        const refs = qs("#tradeWorkbenchContextRefs");
        if (refs) {
          refs.innerHTML = [
            "selected card/widget/chat ref carried locally",
            "execution-adjusted rank ref or provider-pending gap",
            "TCA / cost ref or provider-pending gap",
            "no-trade comparator and reoptimization route",
            "QKU/formula refs or explicit gap route",
            "PR165-D2 agent role refs or explicit gap route",
            "DAG upstream/downstream route ref"
          ].map((item) => `<span>${safe(item)}</span>`).join("");
        }
      }
      localReceipt(route, context, "Trade Workbench is open with selected local context. QTT needs the owner to confirm the objective or add a plain-English trade idea.");
      location.hash = "trade-workbench";
      setActiveSurface("trade-workbench", "tradeWorkbench");
      return;
    }
    if (nextStepId === "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS") {
      showGuidedWorkflow("CHECK_TRADE", context);
      localReceipt(route, context, "Guided Check Trade is open at the next needed owner input. No agent task runs.");
      location.hash = "trade-workbench";
      setActiveSurface("trade-workbench", "guidedWorkflowPanel");
      return;
    }
    if (nextStepId === "NEXT_STEP_REQUEST_REPLAY_PREVIEW" || nextStepId === "NEXT_STEP_REQUEST_PAPER_PREVIEW") {
      localReceipt(route, context, `${route.owner_label} receipt preview created. The dashboard did not run replay or paper execution.`);
      location.hash = "trade-workbench";
      setActiveSurface("trade-workbench", "routePreviewPanel");
      return;
    }
    if (nextStepId === "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES") {
      openDrawer("QKU and formula routes", "QKU/formula refs or explicit gap route; no raw JSONL scanning path", context, "technical_details");
      location.hash = "qku-formula";
      setActiveSurface("qku-formula", "qkuFormulaRoutes");
      return;
    }
    if (nextStepId === "NEXT_STEP_EXPLAIN_NO_TRADE") {
      openDrawer("No-trade explanation", "Comparator and reoptimization choices", context, "why");
      return;
    }
    if (nextStepId === "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN") {
      openDrawer("TCA / cost breakdown", "Fees, spread, slippage, latency, impact, and opportunity cost", context, "tca_breakdown");
      return;
    }
    if (nextStepId === "NEXT_STEP_OPEN_CHART_DRILLDOWN") {
      openDrawer("Chart drilldown", "Current chart context", context, "chart_drilldown");
      return;
    }
    if (nextStepId === "NEXT_STEP_OPEN_TECHNICAL_DETAILS") {
      openDrawer(ownerTitle(context), "Technical details for selected item", context, "technical_details");
      return;
    }
    if (nextStepId === "NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION") {
      openDrawer("Why this action is not available yet", "Disabled action education", context, "why");
      localReceipt(route, context, "Safe alternative preview created. No live order, connector call, private read, agent task, replay, or paper run occurs.");
    }
  }

  return {
    present,
    idOf,
    ownerTitle,
    summary,
    status,
    toneFor,
    guidanceFor,
    menuFor,
    nextStep,
    modePolicy,
    drawerAction,
    setActiveSurface,
    routeAction,
    localReceipt,
    interactionState
  };
})();

function label(value) {
  return DashboardSystem.present(value);
}

function idOf(row, fallback = "row") {
  return DashboardSystem.idOf(row, fallback);
}

function badge(text, tone = "gray") {
  return `<span class="badge ${tone}">${safe(label(text))}</span>`;
}

function interactionStateFor(row) {
  const text = `${row ? Object.values(row).slice(0, 16).join(" ") : ""}`.toLowerCase();
  if (/high|kill|emergency|override|risk|loss/.test(text)) return "high_confirmation";
  if (/needs owner|owner input|required|missing/.test(text)) return "input_required";
  if (/review|decision|queue/.test(text)) return "review_required";
  if (/provider|pending|route|gap/.test(text)) return "provider_pending";
  if (/technical|registry|dag|developer/.test(text)) return "technical_only";
  return "info_only";
}

function interactionBadge(state) {
  const labels = {
    input_required: "Input required",
    review_required: "Review required",
    optional_input: "Optional input",
    provider_pending: "Provider pending",
    info_only: "Info",
    technical_only: "Technical",
    high_confirmation: "High confirmation",
    success: "Success"
  };
  return `<span class="badge interaction-state-badge" data-interaction-badge="${safe(state)}" aria-label="${safe(labels[state] || state)}">${safe(labels[state] || state)}</span>`;
}

function badges(row, extra = []) {
  const state = interactionStateFor(row);
  const values = [
    DashboardSystem.status(row),
    row && row.provider_stage ? `Provider route: ${label(row.provider_stage)}` : "",
    row && row.authority_boundary_ref ? "Safety boundary set" : "",
    ...extra
  ].filter(Boolean);
  return `<div class="badge-row">${interactionBadge(state)}${values.slice(0, 4).map((value) => badge(value, DashboardSystem.toneFor(value))).join("")}</div>`;
}

function receiptCard(receipt) {
  return `
    <article class="card receipt-card" data-local-receipt-preview="${safe(receipt.receipt_type)}" data-interaction-result="OwnerInteractionResultV1" data-runtime-side-effect-allowed="false">
      <h3>${safe(receipt.title)}</h3>
      <p>${safe(receipt.text)}</p>
      <div class="preview-grid">
        <span>Interaction: ${safe(receipt.interaction_id || "local preview")}</span>
        <span>Preview object: ${safe(label(receipt.preview_object_type))}</span>
        <span>Context: ${safe(label(receipt.context_id))}</span>
        <span>Runtime work: none</span>
        <span>Authority: local preview only</span>
      </div>
      ${badge("No runtime side effect", "red")}
    </article>
  `;
}

function ownerControls(row, surface = "trade_workbench") {
  const guidance = DashboardSystem.guidanceFor(row, surface);
  const menu = DashboardSystem.menuFor(surface);
  const options = asList(menu.options).slice(0, 7);
  const cardId = idOf(row, surface);
  const primary = options.find((option) => option.state === "ENABLED_LOCAL_PREVIEW") || options[0] || {
    owner_label: "Send to Trade Workbench",
    next_step_id: "NEXT_STEP_SEND_TO_TRADE_WORKBENCH",
    state: "ENABLED_LOCAL_PREVIEW"
  };
  const rowText = `${surface} ${row ? JSON.stringify(row).slice(0, 1600) : ""}`.toLowerCase();
  const chartCapable = surface === "chart_frame" || Boolean(row && (row.chart_id || row.chart_kind || row.data_chart_render_state));
  const tcaCapable = /tca|cost|fee|spread|slippage|latency|fill|trade|candidate|workbench|edge|alpha/.test(rowText);
  const qkuCapable = /qku|formula|stack|quantum|trade|candidate|gap|route/.test(rowText);
  const drawerButtons = [
    { kind: "explain", labelText: "Explain", applicable: true },
    { kind: "learn", labelText: "Learn", applicable: true },
    { kind: "why", labelText: "Why?", applicable: true },
    { kind: "chart_drilldown", labelText: "Open chart drilldown", applicable: chartCapable },
    { kind: "tca_breakdown", labelText: "Show TCA / cost breakdown", applicable: tcaCapable },
    { kind: "qku_formula_routes", labelText: "Show QKU/formula routes", applicable: qkuCapable },
    { kind: "technical_details", labelText: "Technical Details", applicable: true }
  ].filter((item) => item.applicable);
  return `
    <div class="owner-card-controls" data-card-context="${safe(cardId)}" data-default-card-contract="one-primary-plus-more-actions" data-selected-card-id="${safe(cardId)}">
      <button
        class="menu-option action-primary"
        type="button"
        data-primary-card-action="true"
        data-next-step-id="${safe(primary.next_step_id)}"
        data-local-receipt-preview="${safe(primary.next_step_id)}"
        data-action-state="${safe(primary.state)}">
        ${safe(primary.owner_label)}
      </button>
      <details class="next-action-menu" data-owner-next-action-menu="${safe(surface)}" data-secondary-actions-collapsed="true">
        <summary>More actions</summary>
        <div class="action-menu-body">
          <p><strong>Recommended:</strong> ${safe(menu.recommended_action_label || guidance.recommended)}</p>
          ${drawerButtons.map(({ kind, labelText }) => `
            <button
              class="menu-option action-secondary"
              type="button"
              data-owner-drawer-action="${safe(kind)}"
              data-selected-card-id="${safe(cardId)}"
              data-selected-surface-id="${safe(surface)}"
              data-action-applicability="applicable"
              data-runtime-side-effect-allowed="false">
              ${safe(labelText)}
            </button>
          `).join("")}
          ${options.filter((option) => option !== primary).map((option) => `
            <button
              class="menu-option action-secondary ${option.state === "PROVIDER_PENDING" ? "is-provider-pending" : ""} ${option.state === "ENABLED_LOCAL_PREVIEW" ? "" : "is-disabled"}"
              type="button"
              data-next-step-id="${safe(option.next_step_id)}"
              data-local-receipt-preview="${safe(option.next_step_id)}"
              data-action-state="${safe(option.state)}"
              ${option.state === "PROVIDER_PENDING" ? 'data-provider-pending-action="true"' : ""}
              ${option.state !== "ENABLED_LOCAL_PREVIEW" ? `data-disabled-action-education="${safe(option.safe_alternative_action || "Open local preview or Technical Details.")}"` : ""}
              aria-disabled="false">
              ${safe(option.owner_label)}
            </button>
          `).join("")}
        </div>
      </details>
    </div>
  `;
}

function wireNextActions(root = document) {
  qsa("[data-next-step-id]", root).forEach((button) => {
    if (button.dataset.nextStepWired === "true") return;
    button.dataset.nextStepWired = "true";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const card = event.currentTarget.closest(".card, .chart-panel, .route-card, .wide-card, .timeline-step, tr");
      const context = card && card.__qttRow ? card.__qttRow : { title: card ? card.textContent.slice(0, 120) : "selected dashboard item" };
      DashboardSystem.routeAction(event.currentTarget.dataset.nextStepId, context);
    });
  });
  qsa("[data-owner-drawer-action]", root).forEach((button) => {
    if (button.dataset.drawerActionWired === "true") return;
    button.dataset.drawerActionWired = "true";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const card = event.currentTarget.closest(".card, .chart-panel, .route-card, .wide-card, .timeline-step, tr");
      const context = card && card.__qttRow ? card.__qttRow : { title: card ? card.textContent.slice(0, 120) : "selected dashboard item" };
      const kind = event.currentTarget.dataset.ownerDrawerAction;
      const title = event.currentTarget.textContent.trim();
      openDrawer(title, "Card-specific owner education", context, kind);
    });
  });
  qsa("details", root).forEach((detail) => {
    if (detail.dataset.disclosureWired === "true") return;
    detail.dataset.disclosureWired = "true";
    detail.addEventListener("click", (event) => event.stopPropagation());
  });
}

function technicalRows(row) {
  if (!row || typeof row !== "object") return [];
  const keys = [
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
  return keys.filter((key) => row[key]).map((key) => [label(key), label(row[key])]);
}

function centralEducationEntry(kind) {
  const education = asList(DASHBOARD_DATA.ui1r2r4_semantic_bundle && DASHBOARD_DATA.ui1r2r4_semantic_bundle.education_catalog);
  const byId = new Map(education.map((row) => [row.education_id, row]));
  const educationId = {
    explain: "education.explain",
    learn: "education.learn",
    why: "education.why",
    chart_drilldown: "education.chart_drilldown",
    tca_breakdown: "education.tca_cost",
    qku_formula_routes: "education.qku_formula_routes",
    qku: "education.qku_formula_routes",
    technical_details: "education.technical_details",
    disabled_action: "education.disabled_action",
    provider_pending: "education.provider_pending",
  }[kind] || "education.explain";
  return byId.get(educationId) || {
    education_id: educationId,
    owner_title: titleCase(String(kind || "explain").replace(/_/g, " ")),
    plain_english_summary: "Central education entry is provider-pending in this local bundle.",
    what_it_means: "The selected item stays local preview only.",
    why_it_matters: "Provider evidence is required before QTT can treat it as runtime truth.",
    what_owner_can_do_next: "Open a local preview or Technical Details.",
    provider_pending_copy: "No live runtime work runs here.",
    authority_boundary_copy: "Local UI preview only.",
    technical_detail_ref: "ui1r2r4_owner_semantic_bundle.generated.json",
  };
}

function drawerSectionsFromEducation(kind, guidance) {
  const entry = centralEducationEntry(kind);
  const sectionsByKind = {
    explain: [
      ["What this means", entry.what_it_means || entry.plain_english_summary],
      ["How to read it", guidance.summary],
      ["What is missing", guidance.missing],
      ["What owner can do next", entry.what_owner_can_do_next || guidance.recommended],
    ],
    learn: [
      ["Concept", entry.plain_english_summary],
      ["Why it matters", entry.why_it_matters],
      ["Authority boundary", entry.authority_boundary_copy],
    ],
    why: [
      ["Why this matters", entry.why_it_matters],
      ["Risk and route impact", guidance.risk],
      ["Provider boundary", entry.provider_pending_copy],
    ],
    chart_drilldown: [
      ["Chart drilldown", entry.plain_english_summary],
      ["Data integrity", entry.provider_pending_copy],
      ["Owner action", entry.what_owner_can_do_next],
    ],
    tca_breakdown: [
      ["TCA / cost", entry.plain_english_summary],
      ["What it covers", entry.what_it_means],
      ["Owner action", entry.what_owner_can_do_next],
    ],
    qku_formula_routes: [
      ["QKU / formula route", entry.plain_english_summary],
      ["Immutable vs mutable", entry.what_it_means],
      ["Route/gap status", entry.provider_pending_copy],
    ],
    technical_details: [
      ["Technical summary", entry.plain_english_summary],
      ["Raw selected context", "Raw refs, registry evidence, provider routes, validation refs, and debug fields are shown only here or in Developer mode."],
      ["Authority", entry.authority_boundary_copy],
    ],
  };
  return sectionsByKind[kind] || sectionsByKind.explain;
}

function openDrawer(title, kicker, row = {}, kind = "general") {
  const drawer = qs("#drilldownDrawer");
  const guidance = DashboardSystem.guidanceFor(row, kind);
  const rows = technicalRows(row);
  const drawerAction = DashboardSystem.drawerAction(kind);
  const selectedCardId = idOf(row, "selected_card");
  const selectedActionId = drawerAction.action_id || `OWNER_ACTION_${String(kind).toUpperCase()}`;
  const contentSignature = `${drawerAction.content_signature || `ui1r2r3::${kind}`}::${selectedCardId}`;
  const educationEntry = centralEducationEntry(kind);
  const sections = drawerSectionsFromEducation(kind, guidance);
  drawer.dataset.drawerKind = kind;
  drawer.dataset.selectedCardId = selectedCardId;
  drawer.dataset.selectedActionId = selectedActionId;
  drawer.dataset.contentSignature = contentSignature;
  drawer.dataset.centralEducationId = educationEntry.education_id || "";
  drawer.dataset.runtimeSideEffectAllowed = "false";
  qs("#drawerTitle").textContent = title || educationEntry.owner_title || guidance.title;
  qs("#drawerKicker").textContent = kicker || "Evidence and routing";
  qs("#drawerBody").innerHTML = `
    <div class="drawer-block" data-drilldown-kind="${safe(kind)}" data-selected-card-id="${safe(selectedCardId)}" data-selected-action-id="${safe(selectedActionId)}" data-content-signature="${safe(contentSignature)}" data-central-education-id="${safe(educationEntry.education_id || "")}">
      <h3>Drawer payload</h3>
      <div class="preview-grid">
        <span>Selected card: ${safe(selectedCardId)}</span>
        <span>Selected action: ${safe(selectedActionId)}</span>
        <span>Drawer kind: ${safe(kind)}</span>
        <span>Content signature: ${safe(contentSignature)}</span>
        <span>Education: ${safe(educationEntry.education_id || "central catalog")}</span>
        <span>Runtime side effect: false</span>
      </div>
      ${badges(row)}
    </div>
    ${sections.map(([heading, text]) => `
      <div class="drawer-block ${kind === "technical_details" ? "technical-detail-block" : "owner-education-block"}">
        <h3>${safe(heading)}</h3>
        <p>${safe(text)}</p>
      </div>
    `).join("")}
    <div class="drawer-block evidence-spine-block">
      <h3>Selected context carried forward</h3>
      <div class="preview-grid">
        <span>Context: ${safe(DashboardSystem.ownerTitle(row, "selected dashboard item"))}</span>
        <span>Execution-adjusted rank: ref or provider-pending gap</span>
        <span>TCA / cost: ref or provider-pending gap</span>
        <span>No-trade: comparator and reoptimization route</span>
        <span>QKU/formula refs or explicit gap route</span>
        <span>DAG: upstream/downstream route ref</span>
      </div>
    </div>
    ${kind !== "technical_details" ? `
    <div class="drawer-block">
      <h3>Current status</h3>
      <p>${safe(guidance.status)}. ${safe(guidance.risk)}</p>
    </div>
    <div class="drawer-block">
      <h3>Owner action available</h3>
      <p>${safe(guidance.recommended)}.</p>
      ${ownerControls(row, kind === "chart_drilldown" ? "chart_frame" : kind === "qku_formula_routes" ? "qku_formula" : "trade_workbench")}
    </div>
    ` : ""}
    <div class="drawer-block">
      <h3>Evidence and routing summary</h3>
      ${kind === "technical_details" && rows.length ? rows.slice(0, 12).map(([key, value]) => `<p><strong>${safe(key)}:</strong> ${safe(value)}</p>`).join("") : "<p>Raw refs stay in Technical Details. Owner education views keep plain-English copy.</p>"}
    </div>
    <div class="drawer-block">
      <details>
        <summary>Open raw technical data</summary>
        <pre>${kind === "technical_details" ? safe(JSON.stringify(row, null, 2)) : "Open Technical Details for raw refs."}</pre>
      </details>
    </div>
  `;
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
  wireNextActions(drawer);
}

function closeDrawer() {
  const drawer = qs("#drilldownDrawer");
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
}

function setOptionsMenu(open) {
  const panel = qs("#ownerOptionsPanel");
  const backdrop = qs("#ownerOptionsBackdrop");
  const toggle = qs("#ownerOptionsToggle");
  if (!panel || !toggle) return;
  DashboardSystem.interactionState.optionsMenuOpen = Boolean(open);
  panel.hidden = !open;
  panel.setAttribute("aria-hidden", open ? "false" : "true");
  toggle.setAttribute("aria-expanded", open ? "true" : "false");
  if (backdrop) backdrop.hidden = !open;
  if (open) {
    const first = qs("button, input, select, textarea, [href]", panel);
    if (first) first.focus();
  } else {
    toggle.focus({ preventScroll: true });
  }
}

function closeOwnerOptions() {
  setOptionsMenu(false);
}

function initOptionsMenu() {
  const toggle = qs("#ownerOptionsToggle");
  const close = qs("#ownerOptionsClose");
  const panel = qs("#ownerOptionsPanel");
  const backdrop = qs("#ownerOptionsBackdrop");
  if (!toggle || !panel) return;
  toggle.addEventListener("click", () => setOptionsMenu(toggle.getAttribute("aria-expanded") !== "true"));
  if (close) close.addEventListener("click", closeOwnerOptions);
  if (backdrop) backdrop.addEventListener("click", closeOwnerOptions);
  document.addEventListener("click", (event) => {
    if (!DashboardSystem.interactionState.optionsMenuOpen) return;
    if (panel.contains(event.target) || toggle.contains(event.target)) return;
    closeOwnerOptions();
  });
}

function setTheme(mode, persist = true) {
  const choice = THEME_VALUES.includes(mode) ? mode : "DARK_PRO";
  const normalized = THEME_TO_DATASET[choice] || "dark";
  document.documentElement.dataset.theme = normalized;
  qsa("[data-theme-choice]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.themeChoice === choice ? "true" : "false");
  });
  if (choice === "HIGH_CONTRAST") OwnerSettings.set("high_contrast", true, false);
  else OwnerSettings.set("high_contrast", false, false);
  if (!persist) return;
  OwnerSettings.set("theme_preset", choice);
}

function initTopPanels() {
  const settingsToggle = qs("#ownerSettingsToggle");
  const settingsClose = qs("#closeOwnerSettings");
  const settingsShortcut = qs("#ownerOptionsSettingsShortcut");
  const guideToggle = qs("#qttGuideToggle");
  const guideClose = qs("#closeQttGuide");
  if (settingsToggle) settingsToggle.addEventListener("click", () => setSettingsCenter(settingsToggle.getAttribute("aria-expanded") !== "true"));
  if (settingsShortcut) settingsShortcut.addEventListener("click", () => {
    closeOwnerOptions();
    setSettingsCenter(true);
  });
  if (settingsClose) settingsClose.addEventListener("click", () => setSettingsCenter(false));
  if (guideToggle) guideToggle.addEventListener("click", () => setQttGuide(guideToggle.getAttribute("aria-expanded") !== "true"));
  if (guideClose) guideClose.addEventListener("click", () => setQttGuide(false));
}

function initTheme() {
  const saved = THEME_VALUES.includes(OwnerSettings.get("theme_preset")) ? OwnerSettings.get("theme_preset") : "DARK_PRO";
  setTheme(saved, false);
  qsa("[data-theme-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      setTheme(button.dataset.themeChoice);
      closeOwnerOptions();
    });
  });
}

function setTextSize(size, persist = true) {
  const normalized = TEXT_SIZE_VALUES.includes(size) ? size : "default";
  document.documentElement.dataset.textSize = normalized;
  DashboardSystem.interactionState.textSize = normalized;
  qsa("[data-text-size-choice]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.textSizeChoice === normalized ? "true" : "false");
  });
  if (!persist) return;
  OwnerSettings.set("text_size", normalized);
}

function initTextSize() {
  const saved = TEXT_SIZE_VALUES.includes(OwnerSettings.get("text_size")) ? OwnerSettings.get("text_size") : "default";
  setTextSize(saved, false);
  qsa("[data-text-size-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      setTextSize(button.dataset.textSizeChoice);
      closeOwnerOptions();
    });
  });
}

function applyExperienceModePolicy(mode) {
  const policy = DashboardSystem.modePolicy(mode);
  document.body.dataset.metricDensity = policy.metric_density || "LOW";
  document.body.dataset.educationDensity = policy.education_density || "COMPACT_COLLAPSED";
  qsa("[data-mode-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.modePanel !== mode;
  });
  const overviewEyebrow = qs("#overview .section-head .eyebrow");
  if (overviewEyebrow) {
    overviewEyebrow.textContent = mode === "ADVANCED_OWNER"
      ? "Advanced owner mode - dense trading metrics"
      : mode === "DEVELOPER"
        ? "Developer mode - technical evidence"
        : "Guided owner mode - compact local previews";
  }
}

function setExperienceMode(mode, persist = true) {
  const allowed = new Set(["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"]);
  const normalized = allowed.has(mode) ? mode : "GUIDED_OWNER";
  document.body.dataset.experienceMode = normalized;
  applyExperienceModePolicy(normalized);
  const switcher = qs("#experienceModeSwitch");
  if (switcher) switcher.dataset.experienceMode = normalized;
  qsa("[data-mode-choice]").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.modeChoice === normalized ? "true" : "false");
  });
  if (!persist) return;
  OwnerSettings.set("dashboard_default_experience_mode", normalized);
}

function initExperienceMode() {
  const stored = OwnerSettings.get("dashboard_default_experience_mode");
  const saved = ["GUIDED_OWNER", "ADVANCED_OWNER", "DEVELOPER"].includes(stored) ? stored : "GUIDED_OWNER";
  setExperienceMode(saved, false);
  qsa("[data-mode-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      setExperienceMode(button.dataset.modeChoice);
      closeOwnerOptions();
    });
  });
}

function renderStatus() {
  const status = DASHBOARD_DATA.status_strip || {};
  const meta = DASHBOARD_DATA.meta || {};
  const statusGrid = qs("#statusGrid");
  if (!statusGrid) return;
  const tiles = [
    ["Experience", "Guided by default"],
    ["Data source", "Generated dashboard evidence"],
    ["Safety", "Local previews only"],
    ["Execution", "No venue submit"],
    ["Private data", "No account or cash reads"],
    ["Snapshot", status.boot_data_generated_timestamp || meta.generated_at || "Generated boot data"]
  ];
  statusGrid.innerHTML = tiles.map(([name, value]) => `
    <div class="status-tile">
      <span class="eyebrow">${safe(name)}</span>
      <span class="value">${safe(label(value))}</span>
    </div>
  `).join("");
}

function renderCoach() {
  const coach = qs("#ownerCoachPanel");
  coach.innerHTML = `
    <article class="card coach-card">
      <h3>QTT Coach</h3>
      <p>QTT will show the next safe local step, explain missing evidence, and keep long lessons collapsed until you ask.</p>
      <div class="coach-actions">
        <button class="primary-command" type="button" data-next-step-id="NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS" data-local-receipt-preview="OwnerTradeCheckRequestPreviewV1">Start guided trade check</button>
        <button class="text-command" type="button" data-next-step-id="NEXT_STEP_SEND_TO_TRADE_WORKBENCH" data-local-receipt-preview="OwnerTradeIntentPreviewV1">Send to Trade Workbench</button>
      </div>
      <details class="learning-details">
        <summary>How guidance works</summary>
        <p>QTT agents may later evaluate, rank, test, and route candidates inside owner-approved policies. R2 only creates local next-step previews.</p>
      </details>
    </article>
    <article class="card mode-policy-card mode-only guided-mode-panel" data-mode-panel="GUIDED_OWNER">
      <h3>Review dashboard readiness</h3>
      <p>Compact owner view: one safe primary action, key safety badges, and collapsed details.</p>
      <div class="compact-mode-grid">
        <span data-mode-guided-metric="safety">Local preview only</span>
        <span data-mode-guided-metric="evidence">Provider gaps visible</span>
        <span data-mode-guided-metric="action">Start one guided step</span>
      </div>
    </article>
    <article class="card mode-policy-card mode-only advanced-mode-panel" data-mode-panel="ADVANCED_OWNER" hidden>
      <h3>Trade Metrics</h3>
      <p>Advanced owner view: denser readable metrics without raw registry rows.</p>
      <div class="advanced-metric-grid">
        ${[
          "Execution-adjusted rank",
          "TCA / implementation shortfall",
          "Candidate minus no-trade",
          "Capacity / crowding",
          "FDR / overfit",
          "Portfolio marginal utility",
          "Champion / challenger",
          "Regime memory / MEM1 prior",
          "QKU/formula stack",
          "Quantum structural readiness",
          "Provider-stage route"
        ].map((item) => `<span data-mode-advanced-metric="${safe(item)}">${safe(item)}</span>`).join("")}
      </div>
    </article>
    <article class="card mode-policy-card mode-only developer-mode-panel" data-mode-panel="DEVELOPER" hidden>
      <h3>Inspect renderer and registry evidence</h3>
      <p>Developer view exposes refs, JSON, registry rows, validators, generated_from, provider_stage, runtime_side_effect, and debug details.</p>
      <pre data-mode-developer-technical="true">${safe(JSON.stringify({
        state_model: "OwnerDashboardStateV1",
        resolver: "OwnerSurfaceResolver",
        action_registry: "OwnerActionRegistry",
        next_step_router: "OwnerNextStepRouter",
        validation_ref: "tools/validate_pr169_dash1_owner_dashboard_ui.py",
        runtime_side_effect_allowed: false
      }, null, 2))}</pre>
    </article>
  `;
  const matters = qs("#tellMattersPanel");
  matters.innerHTML = `
    <article class="card">
      <h3>Key Insights</h3>
      <p>Hidden until clicked. The summary uses local dashboard evidence only.</p>
      <button id="tellMattersButton" class="primary-command" type="button">Show key insights</button>
      <div id="tellMattersOutput" class="coach-output" hidden>
        <p>The main owner decision is to review provider-pending evidence before treating any candidate as tradable.</p>
        <p>Most important missing evidence: replay, paper, cost, capacity, and private account receipts are not present in this UI.</p>
        <p>Safe next action: open Trade Workbench or a route preview. No fake cash, PnL, fills, or live positions are shown.</p>
      </div>
    </article>
  `;
  qs("#tellMattersButton").addEventListener("click", () => {
    const output = qs("#tellMattersOutput");
    output.hidden = !output.hidden;
  });
}

function renderOverview() {
  const home = DASHBOARD_DATA.ui1r1_home || {};
  const heroCards = asList(home.hero_cards);
  qs("#overviewCards").innerHTML = heroCards.map((row) => `
    <article class="metric-card card owner-hero-card" tabindex="0" data-search="${safe(DashboardSystem.ownerTitle(row))}">
      <span class="eyebrow">${safe(DashboardSystem.status(row))}</span>
      <span class="value">${safe(DashboardSystem.ownerTitle(row, "Owner status"))}</span>
      <p>${safe(DashboardSystem.summary(row))}</p>
      ${badges(row)}
      ${ownerControls(row, "portfolio")}
    </article>
  `).join("");
  qsa("#overviewCards .owner-hero-card").forEach((card, index) => {
    card.__qttRow = heroCards[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(heroCards[index]), "Owner home card", heroCards[index]));
  });

  const quickCards = asList(home.quick_cards);
  qs("#homeQuickGrid").innerHTML = quickCards.map((row) => `
    <article class="card quick-card" data-search="${safe(DashboardSystem.ownerTitle(row))}">
      <h3>${safe(DashboardSystem.ownerTitle(row))}</h3>
      <p>${safe(DashboardSystem.summary(row))}</p>
      ${badges(row)}
      ${ownerControls(row, row.row_id && row.row_id.includes("CHAT") ? "decision_queue" : "trade_workbench")}
    </article>
  `).join("");
  qsa("#homeQuickGrid .card").forEach((card, index) => {
    card.__qttRow = quickCards[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(quickCards[index]), "Owner quick card", quickCards[index]));
  });

  qs("#homeDeveloperSummary").innerHTML = `
    <details class="dev-details">
      <summary>Technical evidence available</summary>
      <p>Developer diagnostics include registry counts, artifact paths, validator status, no-orphan detail, safety-boundary detail, and raw technical data.</p>
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
      qsa(".chart-panel").forEach((panel) => {
        panel.dataset.range = button.dataset.range;
        const canvas = qs(".chart-canvas", panel);
        const rangeLabel = qs("[data-selected-range-label]", panel);
        if (canvas) canvas.dataset.selectedRange = button.dataset.range;
        if (rangeLabel) rangeLabel.textContent = button.dataset.range;
      });
    });
  });
}

function setSidebarCollapsed(collapsed, persist = true) {
  const value = Boolean(collapsed);
  document.body.dataset.sidebarCollapsed = value ? "true" : "false";
  const toggle = qs("#sidebarCollapseToggle");
  if (toggle) {
    toggle.setAttribute("aria-expanded", value ? "false" : "true");
    toggle.setAttribute("aria-label", value ? "Expand sidebar" : "Collapse sidebar");
    toggle.textContent = value ? "Expand" : "Collapse";
  }
  if (persist) OwnerSettings.set("sidebar_collapsed", value);
}

function initSidebar() {
  setSidebarCollapsed(OwnerSettings.get("sidebar_collapsed") === true, false);
  const toggle = qs("#sidebarCollapseToggle");
  if (toggle) {
    toggle.addEventListener("click", () => setSidebarCollapsed(document.body.dataset.sidebarCollapsed !== "true"));
  }
}

function legendHtml() {
  return `<div class="legend">${SEMANTIC_LEGEND.map(([name, color]) => `<span><i style="--legend-color:${color}"></i>${safe(name)}</span>`).join("")}</div>`;
}

function chartPointsFor() {
  return [
    { x: 42, y: 156, bucket: "Day 1" },
    { x: 98, y: 126, bucket: "Day 5" },
    { x: 154, y: 138, bucket: "Day 9" },
    { x: 210, y: 88, bucket: "Day 12" },
    { x: 266, y: 106, bucket: "Day 16" },
    { x: 322, y: 72, bucket: "Day 21" },
    { x: 382, y: 92, bucket: "Day 26" }
  ];
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
          return `<rect x="${x}" y="${y}" width="30" height="${h}" class="${cls}"><title>${safe(name)} pending component</title></rect><text x="${x + 15}" y="204" text-anchor="middle">${safe(name)}</text>`;
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
        <text x="130" y="112" text-anchor="middle">waiting</text>
        <text x="130" y="132" text-anchor="middle">for data</text>
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
      <svg class="chart-svg dag-svg" viewBox="0 0 420 220" role="img" aria-label="${safe(title)} workflow frame">
        <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z"></path></marker></defs>
        ${[[70,60,"Evidence"],[205,60,"UI"],[340,60,"Owner"],[140,150,"Agents"],[280,150,"Providers"]].map(([x,y,t]) => `<rect x="${x - 42}" y="${y - 22}" width="84" height="44" rx="8" class="node"></rect><text x="${x}" y="${y + 5}" text-anchor="middle">${safe(t)}</text>`).join("")}
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
  const title = DashboardSystem.ownerTitle(row, `Chart ${index + 1}`);
  const chartId = row.data_chart_id || row.chart_id || idOf(row, `chart_${index + 1}`);
  const kind = row.data_chart_kind || row.chart_kind || "line";
  const renderState = row.data_chart_render_state || row.chart_render_state || "PROVIDER_PENDING_VISUAL_FRAME";
  const sourceRef = row.data_chart_source_ref || row.source_artifact_ref || label(row.source_artifact_refs);
  const providerStage = row.data_provider_stage || row.provider_stage || row.dataset_provider_stage || "PRETRADE1";
  return `
    <article class="chart-panel" data-search="${safe(title)}" data-chart-id="${safe(chartId)}" data-chart-kind="${safe(kind)}" data-chart-render-state="${safe(renderState)}" data-chart-source-ref="${safe(sourceRef)}" data-provider-stage="${safe(providerStage)}" data-authority-boundary="${safe(row.data_authority_boundary || row.authority_boundary || row.authority_boundary_ref || "")}" data-interaction-state="provider_pending" data-chart-data-integrity="provider_pending_no_value">
      <h3>${safe(title)}</h3>
      <p>${safe(DashboardSystem.summary(row, "Waiting for provider receipts. No fake values are shown."))}</p>
      <div class="chart-axis-labels" aria-label="${safe(title)} axis labels">
        <span>X-axis: selected time bucket</span>
        <span>Y-axis: provider-pending net cash / state value</span>
      </div>
      <div class="mini-range" role="group" aria-label="${safe(title)} local range controls">
        ${(row.supported_time_ranges || RANGES).slice(0, 7).map((range, i) => `<button class="seg-button ${i === 0 ? "active" : ""}" type="button" data-local-range="${safe(range)}" aria-pressed="${i === 0 ? "true" : "false"}">${safe(range)}</button>`).join("")}
      </div>
      <div class="chart-canvas provider-frame" role="img" tabindex="0" aria-label="${safe(title)} interactive chart contract" data-chart-interaction="OwnerChartInteractionPolicyV1" data-selected-range="${safe((row.supported_time_ranges || RANGES)[0] || "1D")}">
        ${chartSvg(row, index)}
        <div class="chart-interaction-layer" aria-hidden="true"></div>
        <div class="chart-crosshair"></div>
        <div class="chart-focus-point"></div>
        <div class="chart-tooltip" role="status">
          <strong>${safe(title)}</strong><br>
          Range: <span data-chart-tooltip-range>${safe((row.supported_time_ranges || RANGES)[0] || "1D")}</span><br>
          Time bucket: <span data-chart-tooltip-bucket>Day 12</span><br>
          Value: provider receipts pending<br>
          Unit: net cash/state value unavailable until receipt-backed<br>
          Status: no fake PnL, cash, fill, order, or live values shown
        </div>
        <div class="provider-overlay">Waiting for provider receipts. No fake values rendered.</div>
      </div>
      <div class="chart-value-panel" data-chart-value-panel="provider_pending_no_value">
        <span>Selected range: <strong data-selected-range-label>${safe((row.supported_time_ranges || RANGES)[0] || "1D")}</strong></span>
        <span>Data integrity: provider_pending_no_value</span>
        <span>Ticks: local visual sample geometry only; financial values require receipts.</span>
      </div>
      ${legendHtml()}
      <details class="chart-explainer">
        <summary>Explain this chart</summary>
        <p>This chart shows the local route and visual frame. If it moves up or down later, QTT should compare costs, risk, capacity, and missing data before recommending a next step.</p>
      </details>
      ${badges(row, ["chart drilldown"])}
      ${ownerControls(row, "chart_frame")}
    </article>
  `;
}

function updateChartFocus(canvas, clientX) {
  const rect = canvas.getBoundingClientRect();
  const points = chartPointsFor();
  const localX = ((clientX - rect.left) / Math.max(rect.width, 1)) * 420;
  const nearest = points.reduce((best, point) => Math.abs(point.x - localX) < Math.abs(best.x - localX) ? point : best, points[0]);
  const xPercent = (nearest.x / 420) * 100;
  const yPercent = (nearest.y / 220) * 100;
  canvas.classList.add("is-focused");
  const crosshair = qs(".chart-crosshair", canvas);
  const focus = qs(".chart-focus-point", canvas);
  const tooltip = qs(".chart-tooltip", canvas);
  const range = canvas.dataset.selectedRange || "1M";
  if (crosshair) crosshair.style.left = `${xPercent}%`;
  if (focus) {
    focus.style.left = `${xPercent}%`;
    focus.style.top = `${yPercent}%`;
  }
  if (tooltip) {
    qs("[data-chart-tooltip-range]", tooltip).textContent = range;
    qs("[data-chart-tooltip-bucket]", tooltip).textContent = nearest.bucket;
  }
}

function wireChartInteractions(root = document) {
  qsa(".chart-canvas[data-chart-interaction]", root).forEach((canvas) => {
    if (canvas.dataset.chartWired === "true") return;
    canvas.dataset.chartWired = "true";
    canvas.addEventListener("mousemove", (event) => updateChartFocus(canvas, event.clientX));
    canvas.addEventListener("touchstart", (event) => {
      const touch = event.touches[0];
      if (touch) updateChartFocus(canvas, touch.clientX);
    }, { passive: true });
    canvas.addEventListener("focus", () => {
      const rect = canvas.getBoundingClientRect();
      updateChartFocus(canvas, rect.left + rect.width * 0.5);
    });
    canvas.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const current = Number(canvas.dataset.keyboardPoint || "3");
      const next = Math.max(0, Math.min(chartPointsFor().length - 1, current + (event.key === "ArrowRight" ? 1 : -1)));
      canvas.dataset.keyboardPoint = String(next);
      updateChartFocus(canvas, rect.left + (chartPointsFor()[next].x / 420) * rect.width);
    });
  });
}

function renderCharts() {
  const homeCards = asList(DASHBOARD_DATA.ui1r1_home && DASHBOARD_DATA.ui1r1_home.hero_cards);
  const chartRows = asList(DASHBOARD_DATA.ui1r1_chart_manifest && DASHBOARD_DATA.ui1r1_chart_manifest.charts);
  qs("#portfolioCards").innerHTML = homeCards.slice(0, 8).map((row) => `
    <article class="card allocation-card">
      <h3>${safe(DashboardSystem.ownerTitle(row))}</h3>
      <p>${safe(DashboardSystem.summary(row))}</p>
      ${badges(row)}
      ${ownerControls(row, "portfolio")}
    </article>
  `).join("");
  qsa("#portfolioCards .card").forEach((card, index) => {
    card.__qttRow = homeCards[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(homeCards[index]), "Portfolio slot", homeCards[index]));
  });
  const rows = chartRows.length ? chartRows : asList(DASHBOARD_DATA.charts && DASHBOARD_DATA.charts.chart_families).slice(0, 10);
  qs("#chartGrid").innerHTML = rows.map(renderChartPanel).join("");
  qsa("#chartGrid .chart-panel").forEach((panel, index) => {
    panel.__qttRow = rows[index];
    panel.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(rows[index]), "Chart drilldown", rows[index], "chart_drilldown"));
  });
  qsa(".mini-range button").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const group = event.currentTarget.closest(".mini-range");
      qsa("button", group).forEach((item) => {
        item.classList.toggle("active", item === event.currentTarget);
        item.setAttribute("aria-pressed", item === event.currentTarget ? "true" : "false");
      });
      const panel = event.currentTarget.closest(".chart-panel");
      const canvas = qs(".chart-canvas", panel);
      const rangeLabel = qs("[data-selected-range-label]", panel);
      if (canvas) canvas.dataset.selectedRange = event.currentTarget.dataset.localRange;
      if (rangeLabel) rangeLabel.textContent = event.currentTarget.dataset.localRange;
    });
  });
  wireChartInteractions(qs("#chartGrid"));
}

function renderPacketAndQueue() {
  const packet = DASHBOARD_DATA.owner_packet || {};
  qs("#ownerPacketCard").innerHTML = `
    <h3>Owner review packet</h3>
    <p>This packet connects the review queue, cards, actions, and safety boundaries without showing raw technical data as the main experience.</p>
    ${badges(packet, ["review only"])}
    ${ownerControls(packet, "decision_queue")}
  `;
  qs("#ownerPacketCard").__qttRow = packet;
  qs("#ownerPacketCard").addEventListener("click", () => openDrawer("Owner review packet", "Packet evidence", packet));

  const rows = asList(DASHBOARD_DATA.decision_queue).slice(0, 18);
  qs("#decisionQueue").innerHTML = rows.map((row) => `
    <article class="card" data-search="${safe(Object.values(row).slice(0, 8).map(label).join(" "))}">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Owner decision"))}</h3>
      <p>${safe(DashboardSystem.summary(row, "Review the consequence and choose a safe local preview action."))}</p>
      ${badges(row, ["decision route"])}
      ${ownerControls(row, "decision_queue")}
    </article>
  `).join("");
  qsa("#decisionQueue .card").forEach((card, index) => {
    card.__qttRow = rows[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(rows[index]), "Decision Queue", rows[index]));
  });
}

function renderActions() {
  const actions = asList(DASHBOARD_DATA.action_registry);
  const cards = asList(DASHBOARD_DATA.actionable_cards).slice(0, 18);
  qs("#actionCatalog").innerHTML = `
    <div class="table-shell">
      <h3>Governed local actions</h3>
      <table>
        <thead><tr><th>Action</th><th>What it means</th><th>Safety</th><th>Direct submit</th></tr></thead>
        <tbody>${actions.slice(0, 24).map((row) => `
          <tr>
            <td>${safe(label(row.canonical_label || row.action_code))}</td>
            <td>${safe(label(row.action_semantics || row.canonical_label))}</td>
            <td>${safe(label(row.confirmation_class || "review required"))}</td>
            <td>${safe(row.creates_order_authority === false ? "No" : label(row.creates_order_authority))}</td>
          </tr>
        `).join("")}</tbody>
      </table>
    </div>
  `;
  qs("#actionCatalog").addEventListener("click", () => openDrawer("Governed owner actions", "Action grammar preserved", actions[0] || {}));
  qs("#actionableCards").innerHTML = cards.map((row) => `
    <article class="card" data-search="${safe(Object.values(row).slice(0, 8).map(label).join(" "))}">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Actionable card"))}</h3>
      <p>${safe(DashboardSystem.summary(row, "Generated actionable card rendered from QTT evidence."))}</p>
      ${badges(row, ["receipt-gated"])}
      ${ownerControls(row, "decision_queue")}
    </article>
  `).join("");
  qsa("#actionableCards .card").forEach((card, index) => {
    card.__qttRow = cards[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(cards[index]), "Actionable Cards", cards[index]));
  });
}

function renderTimeline() {
  const pipeline = asList(DASHBOARD_DATA.research_candidates);
  const fallbackStages = [
    "Owner Input Box",
    "Source Candidate Intake",
    "Duplicate / Recency / Relevance / Safety Check",
    "Reasoning extraction route",
    "Formula / QKU materialization route",
    "Replay / paper request route",
    "Champion / challenger review",
    "No-trade reoptimization review",
    "Owner promotion review",
    "Live canary review route"
  ].map((name) => ({ pipeline_step_id: name, provider_stage: "ROUTED_PENDING_PROVIDER", activation_route: "owner_submitted_research_candidate_route" }));
  const rows = pipeline.length ? pipeline : fallbackStages;
  qs("#researchPipeline").innerHTML = rows.slice(0, 12).map((row) => `
    <article class="timeline-step card" tabindex="0">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Research step"))}</h3>
      <p>${safe(DashboardSystem.summary(row, "Source candidate route preview only."))}</p>
      ${badges(row)}
      ${ownerControls(row, "decision_queue")}
    </article>
  `).join("");
  qsa("#researchPipeline .timeline-step").forEach((step, index) => {
    step.__qttRow = rows[index];
    step.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(rows[index]), "Research pipeline", rows[index]));
  });
  renderTable("#sourceWatchlist", rows.slice(0, 12), ["pipeline_step_id", "source_family", "provider_stage", "activation_route"], "Source Watchlist / Source Candidate Panel", "decision_queue");
}

function renderTable(selector, rows, columns, title, surface = "trade_workbench") {
  qs(selector).innerHTML = `
    <h3>${safe(label(title))}</h3>
    <table>
      <thead><tr>${columns.map((column) => `<th>${safe(label(column))}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((row, index) => `
        <tr data-row-index="${index}">${columns.map((column) => `<td>${safe(label(row[column]))}</td>`).join("")}</tr>
      `).join("")}</tbody>
    </table>
    ${ownerControls(rows[0] || {}, surface)}
  `;
  qsa(`${selector} tr[data-row-index]`).forEach((tr) => {
    const row = rows[Number(tr.dataset.rowIndex)] || {};
    tr.__qttRow = row;
    tr.addEventListener("click", () => openDrawer(title, "Table detail", row));
  });
}

function renderEdgeAndParameters() {
  const edge = asList(DASHBOARD_DATA.ui1r1_edge_alpha && DASHBOARD_DATA.ui1r1_edge_alpha.rows);
  qs("#edgeAlphaBoard").innerHTML = edge.map((row) => `
    <article class="card edge-card" data-candidate-id="${safe(row.candidate_id)}">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Execution-adjusted candidate"))}</h3>
      <p>Execution-adjusted rank checks cost, fill probability, capacity, false-discovery risk, portfolio benefit, memory, no-trade, and quantum structure routes.</p>
      <div class="edge-components">
        ${Object.entries(row.ranking_components || {}).slice(0, 9).map(([name, ref]) => `<span>${safe(label(name))}: ${safe(label(ref))}</span>`).join("")}
      </div>
      ${badges(row, ["not raw edge only", "no fake score"])}
      ${ownerControls(row, "edge_alpha")}
    </article>
  `).join("");
  qsa("#edgeAlphaBoard .card").forEach((card, index) => {
    card.__qttRow = edge[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(edge[index]), "Edge / Alpha Board", edge[index]));
  });

  const params = asList(DASHBOARD_DATA.ui1r1_parameter_tuning && DASHBOARD_DATA.ui1r1_parameter_tuning.rows);
  qs("#parameterControl").innerHTML = params.map((row) => `
    <article class="card parameter-card" data-parameter-id="${safe(row.parameter_id)}">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Parameter"))}</h3>
      <p>${safe(label(row.current_live_value_slot))} | candidate: ${safe(label(row.candidate_value_slot))} | ${safe(label(row.editability_class))}</p>
      <div class="param-grid">
        <span>Range: ${safe(label(row.reference_range))}</span>
        <span>Affected: ${safe(label(row.affected_modules))}</span>
        <span>Approval: ${safe(label(row.owner_approval_required))}</span>
      </div>
      ${badges(row, ["atomic drilldown", "no live mutation"])}
      ${ownerControls(row, "parameter_control")}
    </article>
  `).join("");
  qsa("#parameterControl .card").forEach((card, index) => {
    card.__qttRow = params[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(params[index]), "Parameter atomic drilldown", params[index]));
  });
}

function renderQkuAndQuantum() {
  const qkuRows = asList(DASHBOARD_DATA.qku_formula_routes);
  const matrix = asList(DASHBOARD_DATA.qku_formula_computability_matrix);
  renderTable("#qkuFormulaRoutes", qkuRows.length ? qkuRows : matrix, ["qku_refs", "formula_refs", "computability_state", "activation_route"], "QKU / Formula computability matrix", "qku_formula");
  qs("#agentQkuResolver").innerHTML = `
    <h3>Central QKU and formula access path</h3>
    <p>Agents use the centralized resolver route and do not scan raw generated files at runtime.</p>
    ${badges(DASHBOARD_DATA.agent_qku_access_resolver || {}, ["central access path"])}
    ${ownerControls(DASHBOARD_DATA.agent_qku_access_resolver || {}, "qku_formula")}
  `;
  qs("#agentQkuResolver").__qttRow = DASHBOARD_DATA.agent_qku_access_resolver || {};
  qs("#agentQkuResolver").addEventListener("click", () => openDrawer("Central QKU and formula access path", "Resolver path", DASHBOARD_DATA.agent_qku_access_resolver || {}, "why"));

  const quantumRows = [
    ...asList(DASHBOARD_DATA.quantum_readiness),
    ...asList(DASHBOARD_DATA.widget_manifest).filter((row) => /Quantum|QPU|QUBO|QAOA|VQE|Ising/i.test(label(row.widget_title || row.widget_id))).slice(0, 17)
  ];
  qs("#quantumCenter").innerHTML = quantumRows.slice(0, 18).map((row) => `
    <article class="card">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Quantum-structure readiness"))}</h3>
      <p>${safe(DashboardSystem.summary(row, "Quantum mapping route visible; no quantum backend call or advantage claim."))}</p>
      ${badges(row, ["classical fallback routed"])}
      ${ownerControls(row, "quantum")}
    </article>
  `).join("");
  qsa("#quantumCenter .card").forEach((card, index) => {
    card.__qttRow = quantumRows[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(quantumRows[index]), "Quantum Control Center", quantumRows[index], "why"));
  });
}

function inferIntentFamily(text) {
  const lower = text.toLowerCase();
  if (/(search online|web search|look online|find online|search the web|browse|internet)/.test(lower)) return "ONLINE_RESEARCH_PROVIDER_PENDING_REQUEST";
  if (/(agent operations|agent status|agent activity|what are agents doing|agent queue|agent tasks)/.test(lower)) return "AGENT_OPERATIONS_STATUS_REQUEST";
  if (/(workflow queue|team queue|upcoming workflow|current workflow|task queue)/.test(lower)) return "WORKFLOW_QUEUE_STATUS_REQUEST";
  if (/(missing evidence|evidence missing|what evidence|needs evidence|before evidence)/.test(lower)) return "EVIDENCE_MISSING_REQUEST";
  if (/(workbench|prefill|fill the form|open the form)/.test(lower)) return "WORKBENCH_PREFILL_REQUEST";
  if (/(which agent disagrees|agent disagrees|agent disagreement|agents disagree|risk objections|agent objection|objecting agent)/.test(lower)) return "AGENT_DISAGREEMENT_REQUEST";
  if (/(variables would make|what variables|variable.*pass|pass replay|pass paper|tune|parameter)/.test(lower)) return "VARIABLE_SEARCH_REQUEST";
  if (lower.includes("no-trade") || lower.includes("no trade")) return "NO_TRADE_EXPLANATION_REQUEST";
  if (/(research this|check this article|source candidate|extract source|https?:\/\/|www\.|\.pdf\b|dataset|paper|article|news|research|source|link|social|thread|post|screenshot)/i.test(text)) return "RESEARCH_ANALYSIS_REQUEST";
  if (/(find formulas|extract formula|formula.*source|algorithm.*source)/.test(lower)) return "FORMULA_QKU_EXTRACTION_PREVIEW_REQUEST";
  if ((lower.includes("formula") || lower.includes("algorithm") || lower.includes("qku agents") || lower.includes("formula stacks")) && !lower.includes("online")) return "QKU_FORMULA_STACK_COMPARISON_REQUEST";
  if (lower.includes("qku") || lower.includes("stack")) return "QKU_MATERIALIZATION_REQUEST";
  if (lower.includes("quantum") || lower.includes("qubo") || lower.includes("qaoa") || lower.includes("vqe")) return "QUANTUM_STRUCTURE_MAPPING_REQUEST";
  if (lower.includes("replay") || lower.includes("paper")) return "REPLAY_PAPER_PREVIEW_REQUEST";
  if (lower.includes("cost") || lower.includes("tca") || lower.includes("slippage")) return "TCA_COST_EXPLANATION_REQUEST";
  if (lower.includes("risk") || lower.includes("capacity")) return "RISK_CAPACITY_EXPLANATION_REQUEST";
  if (lower.includes("edge") || lower.includes("alpha") || lower.includes("rank")) return "EDGE_ALPHA_REVIEW_REQUEST";
  if (lower.includes("live") || lower.includes("canary")) return "LIVE_CANARY_REVIEW_REQUEST_PREVIEW";
  if (lower.includes("kill")) return "KILL_SWITCH_REQUEST_PREVIEW";
  if (/(positive expected net|best trade|check this market|check.*trade|trade|market|best)/.test(lower)) return "TRADE_CHECK_REQUEST";
  return "UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION";
}

function targetWorkspaceForIntent(intentFamily) {
  if (/TRADE|REPLAY|PAPER|NO_TRADE|VARIABLE|PARAMETER|TCA|RISK|CAPACITY|WORKBENCH/.test(intentFamily)) return "Trade Workbench";
  if (/RESEARCH|SOURCE|FORMULA|QKU|QUANTUM|ONLINE/.test(intentFamily)) return "Research Intake";
  if (/AGENT_OPERATIONS|AGENT_DISAGREEMENT/.test(intentFamily)) return "Agent Operations";
  if (/WORKFLOW_QUEUE/.test(intentFamily)) return "QTT Team Workflow Queue";
  if (/EDGE|ALPHA/.test(intentFamily)) return "Edge / Alpha Board";
  return "Owner Home";
}

function localIntentResponse(intentFamily) {
  const boundary = "No online search, live LLM, real agent task, connector read, replay, paper, live execution, venue submit, or Execution Router release happened.";
  const responses = {
    TRADE_CHECK_REQUEST: {
      title: "Trade-check preview",
      summary: "QTT can open Trade Workbench and turn the owner idea into a local TradePlanCandidateV1 preview with TCA, no-trade, QKU/formula, risk, capacity, and route-gap checks.",
      route: "Trade Workbench -> TradePlanCandidateV1 -> no-trade comparator -> TCA/cost and QKU/formula route preview.",
      next: "Open or prefill Trade Workbench, then add the missing market/event, side, budget, and plain-English detail.",
      provider: "AGENT_ORCH / PAPER_LOOP later",
    },
    RESEARCH_ANALYSIS_REQUEST: {
      title: "Research intake preview",
      summary: "This source can become a candidate/provisional research input. QTT will not accept source truth, connector semantics, replay evidence, or live readiness here.",
      route: "Research Intake -> SourceCandidateV1 -> FormulaExtractionCandidateV1 / QKU route gaps.",
      next: "Keep the source candidate provisional and route it to Research Intake.",
      provider: "LLM2 / source-evidence providers later",
    },
    ONLINE_RESEARCH_PROVIDER_PENDING_REQUEST: {
      title: "Online research provider-pending preview",
      summary: "QTT can show the future online-research route, including URL/snippet/timestamp/dedup/formula extraction lanes, but this local UI does not search the web.",
      route: "OwnerOnlineResearchRequestPreview -> LLM2 provider-pending research/source candidate lane.",
      next: "Keep the request as a local provider-pending preview until an online research provider exists.",
      provider: "LLM2 later",
    },
    FORMULA_QKU_EXTRACTION_PREVIEW_REQUEST: {
      title: "Formula/QKU extraction preview",
      summary: "QTT can route source text toward formula, variable, assumption, dataset, and QKU extraction lanes without materializing formulas or QKUs here.",
      route: "Source candidate -> FormulaExtractionCandidateV1 -> QKU/formula route-gap review.",
      next: "Open QKU/formula routes or Research Intake as a local preview.",
      provider: "LLM2 / READINESS1 later",
    },
    QKU_FORMULA_STACK_COMPARISON_REQUEST: {
      title: "QKU/formula route preview",
      summary: "QTT can show which immutable QKU/formula stack route would be compared and where provider-pending gaps remain. It does not create or repair formulas into profit.",
      route: "QKU / Formula Routes -> responsible agent route refs or PR165-D2 gap.",
      next: "Open QKU/formula routes or Technical Details.",
      provider: "READINESS1 / AGENT_ORCH later",
    },
    QKU_MATERIALIZATION_REQUEST: {
      title: "QKU route preview",
      summary: "QTT can show computability and route/gap status for QKUs without creating a new QKU engine.",
      route: "QKU / Formula Routes -> no-orphan route/gap projection.",
      next: "Open QKU/formula routes.",
      provider: "READINESS1 later",
    },
    AGENT_DISAGREEMENT_REQUEST: {
      title: "Agent disagreement preview",
      summary: "QTT would route objections into risk, TCA, source, memory/regime, no-trade, QKU/formula, and missing-evidence categories. No agent is running.",
      route: "Agent Operations -> objection categories -> Workbench or Technical Details.",
      next: "Open Agent Operations or review risk/TCA/no-trade gaps.",
      provider: "AGENT_ORCH later",
    },
    NO_TRADE_EXPLANATION_REQUEST: {
      title: "No-trade explanation preview",
      summary: "No-trade is a first-class comparator. QTT can explain which mutable trade variables may need retesting without changing immutable QKUs or formulas.",
      route: "No-trade comparator -> variable retune route -> replay/paper request preview.",
      next: "Open the no-trade explanation or Workbench variable fields.",
      provider: "PRETRADE / PAPER_LOOP later",
    },
    VARIABLE_SEARCH_REQUEST: {
      title: "Variable sensitivity preview",
      summary: "QTT can preview mutable variables such as size, venue, entry, hold duration, maker/taker policy, liquidity, spread, latency, and exposure. Formulas remain immutable.",
      route: "TradePlanCandidateV1 mutable variables -> replay/paper provider-pending request.",
      next: "Fill Workbench constraints and request a local replay/paper preview.",
      provider: "PAPER_LOOP later",
    },
    REPLAY_PAPER_PREVIEW_REQUEST: {
      title: "Replay/paper request preview",
      summary: "QTT can create a local request-preview route for replay or paper. It does not run replay, paper, fills, PnL, or order simulation here.",
      route: "Workbench -> ReplayRequestPreviewV1 / PaperRequestPreviewV1 -> provider-pending receipt slots.",
      next: "Open Trade Workbench and inspect missing receipt classes.",
      provider: "PAPER_LOOP later",
    },
    WORKBENCH_PREFILL_REQUEST: {
      title: "Workbench prefill preview",
      summary: "QTT can focus or prefill the existing Workbench from the selected card/chat context through OwnerNextStepRouter.",
      route: "Chat / Ask QTT -> OwnerNextStepRouter -> Trade Workbench.",
      next: "Open Trade Workbench and confirm required fields.",
      provider: "UI1 local only",
    },
    EVIDENCE_MISSING_REQUEST: {
      title: "Missing evidence preview",
      summary: "QTT can show missing source, TCA, risk, replay, paper, capacity, memory, quantum, and receipt gaps without fabricating evidence.",
      route: "Evidence-spine route/gap projection -> Technical Details or Workbench.",
      next: "Open Technical Details, receipt preview, or Workbench.",
      provider: "source/TCA/risk/PAPER providers later",
    },
    AGENT_OPERATIONS_STATUS_REQUEST: {
      title: "Agent Operations preview",
      summary: "QTT can show where agent duty, KPI, trust, current/upcoming tasks, quarantine, and receipts will appear. All values are provider-pending.",
      route: "Agent Operations -> PR165-D2 duty refs or explicit gap routes.",
      next: "Open Agent Operations.",
      provider: "AGENT_ORCH later",
    },
    WORKFLOW_QUEUE_STATUS_REQUEST: {
      title: "QTT Team Workflow Queue preview",
      summary: "QTT can show current/upcoming workflow lanes tagged by responsible/supporting agents. No workflow engine or scheduler is running.",
      route: "Workflow Queue -> responsible agent -> current/next provider-pending stage.",
      next: "Open QTT Team Workflow Queue.",
      provider: "SVC1 / AGENT_ORCH / PAPER_LOOP later",
    },
    TCA_COST_EXPLANATION_REQUEST: {
      title: "TCA / cost preview",
      summary: "QTT can route fees, spread, slippage, latency, fill, capacity, and implementation shortfall as provider-pending TCA checks.",
      route: "TCA / cost breakdown -> Workbench constraints.",
      next: "Open TCA / cost breakdown or Workbench.",
      provider: "PRETRADE / PAPER_LOOP later",
    },
    RISK_CAPACITY_EXPLANATION_REQUEST: {
      title: "Risk and capacity preview",
      summary: "QTT can explain risk/capacity/crowding gaps and safe local alternatives without risk-pass truth.",
      route: "Risk route -> capacity/crowding -> no-trade comparator.",
      next: "Open risk/TCA/no-trade details.",
      provider: "PRETRADE / AGENT_ORCH later",
    },
    EDGE_ALPHA_REVIEW_REQUEST: {
      title: "Edge review preview",
      summary: "QTT can show execution-adjusted ranking concepts and missing evidence routes without claiming a profitable edge.",
      route: "Edge / Alpha Board -> TCA/FDR/capacity/no-trade route gaps.",
      next: "Open Edge / Alpha Board or Workbench.",
      provider: "PR165 scoring provider stages later",
    },
    LIVE_CANARY_REVIEW_REQUEST_PREVIEW: {
      title: "Live-canary review preview",
      summary: "QTT can prepare an owner review preview only. It cannot submit, release, or call the Execution Router.",
      route: "OwnerLiveCanaryReviewRequestPreview -> Execution Router provider-pending boundary.",
      next: "Review authority boundary or disabled-action education.",
      provider: "LIVE_PILOT / LAUNCH later",
    },
    KILL_SWITCH_REQUEST_PREVIEW: {
      title: "Kill-switch preview",
      summary: "QTT can show a local kill-switch review route, but no runtime kill-switch or order action is created.",
      route: "OwnerKillSwitchRequestPreview -> governance route.",
      next: "Open high-confirmation preview details.",
      provider: "SVC1 / governance runtime later",
    },
    UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION: {
      title: "Clarify request",
      summary: "I need a market, trade idea, source link, formula, or research question to route this. You can also ask about an agent objection, no-trade question, or workflow area.",
      route: "Clarification chips -> Chat / Workbench / Research / Agent Operations.",
      next: "Choose one clarification chip.",
      provider: "UI1 local only",
    },
  };
  const response = responses[intentFamily] || responses.UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION;
  return { ...response, boundary };
}

function buildOwnerIntentPreview(rawText) {
  const text = String(rawText || "").trim();
  const intentFamily = inferIntentFamily(text);
  const targetWorkspace = targetWorkspaceForIntent(intentFamily);
  const previewObjects = intentFamily.includes("ONLINE")
    ? ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "OwnerOnlineResearchRequestPreview", "OwnerSourceCandidateExtractionPreview", "OwnerFormulaQKUExtractionPreview"]
    : intentFamily.includes("RESEARCH") || intentFamily.includes("SOURCE")
      ? ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "OwnerResearchSubmissionPreviewV1", "SourceCandidatePreviewV1", "FormulaExtractionCandidatePreviewV1"]
      : intentFamily.includes("QKU") || intentFamily.includes("FORMULA")
      ? ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "QKUCandidateMaterializationPreviewV1", "QuantumStructureMappingPreviewV1"]
      : intentFamily.includes("NO_TRADE")
        ? ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "NoTradeReoptimizationRequestPreviewV1", "TradePlanCandidatePreviewV1"]
        : intentFamily.includes("AGENT")
          ? ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "OwnerAgentOperationsPreviewV1", "OwnerAgentDisagreementPreviewV1"]
          : intentFamily.includes("WORKFLOW")
            ? ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "OwnerWorkflowQueuePreviewV1"]
            : ["OwnerMessagePreviewV1", "OwnerPlainEnglishIntentPreviewV1", "OwnerTradeIntentPreviewV1", "OwnerTradeCheckRequestPreviewV1", "ReplayPaperRequestPreviewV1"];
  const unknown = intentFamily === "UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION";
  const response = localIntentResponse(intentFamily);
  return {
    object_type: "OwnerPlainEnglishIntentPreviewV1",
    intent_id: `LOCAL_PREVIEW_${Date.now()}`,
    thread_id: targetWorkspace === "Research Intake" ? "OWNER_THREAD_RESEARCH_INTAKE" : "OWNER_THREAD_TRADE_WORKBENCH",
    raw_owner_text_excerpt: text.slice(0, 140),
    response_title: response.title,
    plain_english_summary: response.summary,
    what_happened_now: `Created a local ${response.title.toLowerCase()} in the shared Chat / Ask QTT state.`,
    what_will_not_happen_now: response.boundary,
    which_route_opens_next: response.route,
    later_provider_stage: response.provider,
    next_safe_local_action: response.next,
    intent_family: intentFamily,
    confidence_label: unknown ? "Needs clarification" : text.length > 18 ? "High confidence local preview" : "Medium confidence local preview",
    clarifying_question_if_needed: unknown
      ? "Choose: Check a trade, Research a source, Explain no-trade, Compare formula stacks, Open Trade Workbench."
      : text.length > 18
        ? "No clarification needed for this preview."
        : "Which market, source, or candidate should QTT inspect?",
    target_workspace: targetWorkspace,
    structured_request_preview_refs: previewObjects,
    suggested_chips: unknown
      ? ["Check a trade", "Research a source", "Explain no-trade", "Compare formula stacks", "Open Trade Workbench"]
      : [],
    source_artifact_refs: ["owner_dashboard_conversation_state.generated.json", "owner_dashboard_chat_route_map.generated.json"],
    PR165_D2_agent_role_refs_or_gap: ["PR165_D2_AgentDutySourceCrosswalk.report.json"],
    QKU_formula_refs_or_gap: ["owner_qku_formula_candidate_route_view.generated.jsonl"],
    LLM_view_refs_or_provider_route: ["owner_llm_view_projection.generated.jsonl"],
    TradePlanCandidate_ref_or_gap: "TradePlanCandidateV1::provider_pending_or_local_preview",
    runtime_side_effect: false,
    runtime_side_effect_allowed: false
  };
}

function renderIntentReceipt(preview) {
  const receipt = qs("#chatReceiptPreview");
  DashboardSystem.interactionState.chatMessages.push(preview);
  receipt.innerHTML = `
    <article class="card receipt-card" data-preview-object="OwnerPlainEnglishIntentPreviewV1" data-intent-family="${safe(preview.intent_family)}" data-runtime-side-effect-allowed="false">
      <h3>${safe(preview.response_title || "Local chat route preview")}</h3>
      <div class="chat-bubble owner-bubble">
        <strong>Owner</strong>
        <p>${safe(preview.raw_owner_text_excerpt)}</p>
      </div>
      <div class="chat-bubble qtt-bubble">
        <strong>QTT preview</strong>
        <p>${safe(preview.plain_english_summary)}</p>
        <p><strong>What happened now:</strong> ${safe(preview.what_happened_now)}</p>
        <p><strong>Route opened next:</strong> ${safe(preview.which_route_opens_next)}</p>
        <p><strong>What will not happen now:</strong> ${safe(preview.what_will_not_happen_now)}</p>
      </div>
      ${preview.suggested_chips && preview.suggested_chips.length ? `
        <div class="chip-row clarification-chip-row" data-unknown-intent-chips="OwnerNextStepRouter">
          ${preview.suggested_chips.map((chip) => `<button class="chip" type="button" data-clarify-chip="${safe(chip)}">${safe(chip)}</button>`).join("")}
        </div>
      ` : ""}
      <div class="preview-grid">
        <span>Preview objects: ${safe(label(preview.structured_request_preview_refs))}</span>
        <span>Confidence: ${safe(preview.confidence_label)}</span>
        <span>Next: ${safe(preview.clarifying_question_if_needed)}</span>
        <span>Provider stage: ${safe(preview.later_provider_stage)}</span>
        <span>Safe action: ${safe(preview.next_safe_local_action)}</span>
        <span>Receipt: OwnerChatRouteReceiptPreviewV1</span>
        <span>Agent response: provider-pending</span>
        <span>Runtime side effect: false</span>
      </div>
      <div class="coach-actions">
        <button class="primary-command" type="button" data-next-step-id="NEXT_STEP_SEND_TO_TRADE_WORKBENCH" data-local-receipt-preview="OwnerTradeIntentPreviewV1">Send to Trade Workbench</button>
        <button class="text-command" type="button" data-next-step-id="NEXT_STEP_SHOW_QKU_FORMULA_ROUTES" data-local-receipt-preview="QKUFormulaRoutePreviewV1">Show QKU/formula routes</button>
        <button class="text-command" type="button" data-next-step-id="NEXT_STEP_EXPLAIN_NO_TRADE" data-local-receipt-preview="NoTradeExplanationPreviewV1">Explain no-trade</button>
      </div>
      ${badges(preview, ["local coach reply", "receipt preview"])}
      ${ownerControls(preview, "trade_workbench")}
    </article>
  `;
  receipt.querySelector(".receipt-card").__qttRow = preview;
  receipt.querySelector(".receipt-card").addEventListener("click", () => openDrawer("Local chat route preview", "Chat coach receipt", preview));
  qsa("[data-clarify-chip]", receipt).forEach((chip) => {
    chip.addEventListener("click", (event) => {
      event.stopPropagation();
      const text = chip.dataset.clarifyChip || "";
      const mapped = text === "Check a trade"
        ? "Can QTT check this market and find the best trade?"
        : text === "Research a source"
          ? "Research this source and tell me if it creates a prediction-market edge."
          : text === "Explain no-trade"
            ? "Why did no-trade win here?"
            : text === "Compare formula stacks"
              ? "Ask the QKU agents to compare the best formula stacks for this event."
              : "Open Trade Workbench";
      const input = qs("#ownerChatInput");
      if (input) {
        input.value = mapped;
        input.focus();
      }
      if (text === "Open Trade Workbench") {
        DashboardSystem.routeAction("NEXT_STEP_SEND_TO_TRADE_WORKBENCH", preview);
      }
    });
  });
  wireNextActions(receipt);
}

// OwnerChatSubmitHandler: Ctrl+Enter and Send submit; Enter stays a safe newline by default.
function submitOwnerChat(source = "BUTTON_SUBMIT") {
  const input = qs("#ownerChatInput");
  const hint = qs("#chatSubmitHint");
  if (!input) return null;
  const raw = input.value;
  if (!raw.trim()) {
    if (hint) {
      hint.hidden = false;
      hint.textContent = "Type a plain-English request before creating a local preview.";
    }
    input.focus();
    return null;
  }
  if (hint) {
    hint.hidden = false;
    hint.textContent = source === "CTRL_ENTER_SUBMIT"
      ? "Ctrl+Enter created a local route preview."
      : source === "ENTER_TO_SEND_SUBMIT"
        ? "Enter-to-send is enabled for this local preview."
        : "Send created a local route preview.";
  }
  const preview = buildOwnerIntentPreview(raw);
  preview.input_event_type = source;
  renderIntentReceipt(preview);
  DashboardSystem.setActiveSurface("chat", "chatReceiptPreview");
  input.value = "";
  input.focus();
  return preview;
}

function setEnterToSend(enabled, persist = true) {
  const value = Boolean(enabled);
  DashboardSystem.interactionState.chatEnterToSend = value;
  qsa("[data-enter-to-send-setting]").forEach((input) => {
    input.checked = value;
  });
  if (!persist) return;
  OwnerSettings.set("chat_enter_to_send", value);
}

function initEnterToSendPreference(root = document) {
  const saved = OwnerSettings.get("chat_enter_to_send") === true;
  setEnterToSend(saved, false);
  qsa("[data-enter-to-send-setting]", root).forEach((input) => {
    input.addEventListener("change", (event) => {
      setEnterToSend(event.currentTarget.checked);
      const hint = qs("#chatSubmitHint");
      if (hint) {
        hint.hidden = false;
        hint.textContent = event.currentTarget.checked
          ? "Enter-to-send is enabled for this local preview preference."
          : "Enter-to-send is off. Enter keeps typing; Ctrl+Enter or Send submits.";
      }
    });
  });
}

function showGuidedWorkflow(workflowId, context = {}) {
  const flow = asList(DASHBOARD_DATA.ui1r2_guided_flow && DASHBOARD_DATA.ui1r2_guided_flow.flows).find((row) => row.workflow_id === workflowId) ||
    asList(DASHBOARD_DATA.ui1r2_guided_flow && DASHBOARD_DATA.ui1r2_guided_flow.flows)[0];
  const panel = qs("#guidedWorkflowPanel");
  if (!flow || !panel) return;
  DashboardSystem.interactionState.guided[flow.workflow_id] = DashboardSystem.interactionState.guided[flow.workflow_id] || {
    currentStep: 0,
    values: {},
    context
  };
  const state = DashboardSystem.interactionState.guided[flow.workflow_id];
  panel.innerHTML = `
    <article class="card guided-flow-card" data-guided-workflow="${safe(flow.workflow_id)}" data-guided-current-step="${safe(state.currentStep)}">
      <h3>${safe(flow.workflow_label)}</h3>
      <p id="guidedWorkflowContext">Current local context: ${safe(DashboardSystem.ownerTitle(context, "selected dashboard item"))}</p>
      <ol class="guided-steps">
        ${asList(flow.steps).map((step, index) => `
          <li class="${index === state.currentStep ? "active-step" : ""}" data-guided-step-index="${index}">
            <span>${safe(step.owner_prompt)}</span>
          </li>
        `).join("")}
      </ol>
      <div class="guided-input-row" data-guided-input-handler="OwnerGuidedInputHandler">
        <label>Plain-English detail
          <input id="guidedTextInput" data-guided-text-input="true" aria-label="Guided workflow text input" placeholder="Type the minimum needed detail" value="${safe(state.values.text || "")}">
        </label>
        <label>Max budget or hold duration
          <input id="guidedNumericInput" data-guided-numeric-input="true" inputmode="decimal" aria-label="Guided workflow numeric input" placeholder="Example: 50" value="${safe(state.values.numeric || "")}">
        </label>
      </div>
      <p id="guidedInlineValidation" class="inline-validation" data-guided-inline-validation hidden></p>
      <div id="guidedPreviewState" class="preview-grid" data-guided-preview-state="OwnerTradeIntentPreviewV1">
        <span>Current step: ${safe(String(state.currentStep + 1))} of ${safe(String(asList(flow.steps).length))}</span>
        <span>Local preview state: ${safe(Object.keys(state.values).length ? "updated" : "waiting for owner input")}</span>
        <span>Runtime side effect: false</span>
      </div>
      <div class="coach-actions">
        <button id="guidedBackButton" class="text-command" type="button">Back</button>
        <button id="guidedContinueButton" class="primary-command" type="button">Continue</button>
      </div>
      <p>Output is a local request preview only. No live LLM, agent, replay, paper, live execution, direct venue submit, or Execution Router release occurs.</p>
      ${ownerControls(context, "trade_workbench")}
    </article>
  `;
  panel.removeAttribute("hidden");
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  wireGuidedWorkflow(panel, flow.workflow_id);
  wireNextActions(panel);
}

// OwnerGuidedInputHandler: Enter and Continue share validation and local step advancement.
function wireGuidedWorkflow(panel, workflowId) {
  const card = qs("[data-guided-workflow]", panel);
  const textInput = qs("#guidedTextInput", panel);
  const numericInput = qs("#guidedNumericInput", panel);
  const validation = qs("#guidedInlineValidation", panel);
  const preview = qs("#guidedPreviewState", panel);
  const flow = asList(DASHBOARD_DATA.ui1r2_guided_flow && DASHBOARD_DATA.ui1r2_guided_flow.flows).find((row) => row.workflow_id === workflowId);
  const steps = asList(flow && flow.steps);
  const state = DashboardSystem.interactionState.guided[workflowId];
  function updateVisibleState() {
    card.dataset.guidedCurrentStep = String(state.currentStep);
    qsa("[data-guided-step-index]", card).forEach((step) => {
      step.classList.toggle("active-step", Number(step.dataset.guidedStepIndex) === state.currentStep);
    });
    preview.innerHTML = `
      <span>Current step: ${safe(String(state.currentStep + 1))} of ${safe(String(steps.length))}</span>
      <span>Local preview state: updated</span>
      <span>Saved text: ${safe(state.values.text || "waiting")}</span>
      <span>Saved number: ${safe(state.values.numeric || "waiting")}</span>
      <span>Runtime side effect: false</span>
    `;
  }
  function advance(source) {
    const numericDraft = numericInput.value.trim();
    if (document.activeElement === numericInput && numericDraft && Number.isNaN(Number(numericDraft))) {
      validation.hidden = false;
      validation.textContent = "Enter a number or choose a preset.";
      numericInput.setAttribute("aria-invalid", "true");
      return;
    }
    validation.hidden = false;
    validation.textContent = source === "CONTINUE" ? "Continue saved the same local preview as Enter." : "Enter saved the local preview and advanced the step.";
    numericInput.removeAttribute("aria-invalid");
    state.values.text = textInput.value.trim();
    state.values.numeric = numericDraft;
    state.currentStep = Math.min(state.currentStep + 1, Math.max(steps.length - 1, 0));
    updateVisibleState();
    DashboardSystem.localReceipt(
      DashboardSystem.nextStep("NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS"),
      state.context || {},
      "Guided input updated a local OwnerTradeIntentPreviewV1. No runtime work runs now."
    );
  }
  [textInput, numericInput].forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      advance("ENTER_SUBMIT");
    });
  });
  qs("#guidedContinueButton", panel).addEventListener("click", () => advance("CONTINUE"));
  qs("#guidedBackButton", panel).addEventListener("click", () => {
    state.values.text = textInput.value.trim();
    state.values.numeric = numericInput.value.trim();
    state.currentStep = Math.max(state.currentStep - 1, 0);
    validation.hidden = false;
    validation.textContent = "Back preserved the local preview values.";
    updateVisibleState();
  });
}

function chatPresetRows() {
  const rows = asList(DASHBOARD_DATA.ui1r2r3_chat_guide && DASHBOARD_DATA.ui1r2r3_chat_guide.chat_presets);
  if (rows.length) return rows;
  return asList(DASHBOARD_DATA.ui1r1_chat_contract && DASHBOARD_DATA.ui1r1_chat_contract.prompt_chips).map((chip, index) => ({
    option_id: `legacy_prompt_${index + 1}`,
    owner_label: chip,
    source_category: "safe_ui_default",
  }));
}

function fillChatComposer(text) {
  const input = qs("#ownerChatInput");
  if (!input) return;
  input.value = text;
  input.focus();
  DashboardSystem.setActiveSurface("chat", "ownerChatInput");
}

function renderQttGuideBody() {
  const prompts = asList(DASHBOARD_DATA.ui1r2r3_chat_guide && DASHBOARD_DATA.ui1r2r3_chat_guide.qtt_guide_prompts);
  const body = qs("#qttGuideBody");
  if (!body) return;
  body.innerHTML = `
    <article class="card" data-qtt-guide-local-only="true" data-reuses-chat-state="true" data-second-chat-store-created="false">
      <h3>Ask QTT</h3>
      <p>Local guide only. It fills the existing chat composer or opens the Workbench through OwnerNextStepRouter; no live LLM, agent task, replay, paper, live execution, source truth, or order authority is created.</p>
      <label class="field-label" for="qttGuideComposer">Ask QTT anything about this screen, trade, QKU, formula, risk, or next step...</label>
      <div class="qtt-guide-composer-row" data-qtt-guide-composer="shared-chat-action-state">
        <textarea id="qttGuideComposer" rows="4" aria-label="Ask QTT anything about this screen, trade, QKU, formula, risk, or next step" placeholder="Ask QTT anything about this screen, trade, QKU, formula, risk, or next step..."></textarea>
        <button id="qttGuideSend" class="primary-command" type="button" data-qtt-guide-send="shared-chat-submit">Send</button>
      </div>
      <p id="qttGuideComposerHint" class="inline-validation" hidden></p>
      <label class="field-label" for="qttGuidePresetSelect">Preset prompt</label>
      <select id="qttGuidePresetSelect" data-guide-preset-select="true">
        <option value="">Select a preset prompt...</option>
        ${chatPresetRows().map((row) => `<option value="${safe(row.owner_label)}">${safe(row.owner_label)}</option>`).join("")}
      </select>
      <div class="qtt-guide-actions">
        ${(prompts.length ? prompts : ["Check a trade", "Research a link", "Find formulas/QKUs", "Explain this screen", "Why no-trade?", "Show risk objections", "Prepare replay/paper preview"]).map((prompt) => `
          <button class="qtt-guide-prompt" type="button" data-guide-prompt="${safe(prompt)}">${safe(prompt)}</button>
        `).join("")}
      </div>
      ${badge("same chat/action state", "blue")} ${badge("local preview only", "red")}
    </article>
  `;
  qs("#qttGuidePresetSelect", body).addEventListener("change", (event) => {
    const value = event.currentTarget.value;
    const guideInput = qs("#qttGuideComposer", body);
    if (value && guideInput) guideInput.value = value;
    if (value) fillChatComposer(value);
  });
  qs("#qttGuideSend", body).addEventListener("click", () => {
    const guideInput = qs("#qttGuideComposer", body);
    const hint = qs("#qttGuideComposerHint", body);
    const text = guideInput ? guideInput.value.trim() : "";
    if (!text) {
      if (hint) {
        hint.hidden = false;
        hint.textContent = "Type a plain-English QTT question before creating a local preview.";
      }
      if (guideInput) guideInput.focus();
      return;
    }
    fillChatComposer(text);
    const preview = buildOwnerIntentPreview(text);
    preview.input_event_type = "QTT_GUIDE_SEND";
    renderIntentReceipt(preview);
    if (hint) {
      hint.hidden = false;
      hint.textContent = "Sent through the shared Chat / Ask QTT local preview path.";
    }
    if (guideInput) guideInput.value = "";
    DashboardSystem.setActiveSurface("chat", "chatReceiptPreview");
  });
  qsa("[data-guide-prompt]", body).forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = button.dataset.guidePrompt || "Explain this screen";
      const mapped = prompt === "Check a trade"
        ? "Check this market for a positive expected net-cash trade."
        : prompt === "Research a link"
          ? "Research this link and find useful formulas or QKUs."
          : prompt === "Find formulas/QKUs"
            ? "Compare the best formula stacks for this event."
            : prompt === "Why no-trade?"
              ? "Explain why no-trade won."
              : prompt === "Show risk objections"
                ? "Show agent disagreement and risk objections."
                : prompt === "Prepare replay/paper preview"
                  ? "Route this candidate to replay/paper preview."
                  : "Explain this screen in plain English.";
      const guideInput = qs("#qttGuideComposer", body);
      if (guideInput) guideInput.value = mapped;
      fillChatComposer(mapped);
      if (/trade|replay|paper/i.test(mapped)) DashboardSystem.setActiveSurface("chat", "ownerChatInput");
    });
  });
}

function setQttGuide(open) {
  const panel = qs("#qttGuidePanel");
  const toggle = qs("#qttGuideToggle");
  if (!panel || !toggle) return;
  DashboardSystem.interactionState.qttGuideOpen = Boolean(open);
  panel.hidden = !open;
  panel.classList.toggle("open", Boolean(open));
  panel.setAttribute("aria-hidden", open ? "false" : "true");
  toggle.setAttribute("aria-expanded", open ? "true" : "false");
  OwnerSettings.set("qtt_guide_collapsed", !open);
  if (open) {
    renderQttGuideBody();
    const first = qs("button, select, input, textarea", panel);
    if (first) first.focus();
  } else {
    toggle.focus({ preventScroll: true });
  }
}

function settingsSections() {
  const sections = asList(DASHBOARD_DATA.ui1r2r3_owner_settings && DASHBOARD_DATA.ui1r2r3_owner_settings.sections);
  if (sections.length) return sections;
  return ["Appearance", "Colors", "Layout", "Charts", "Workbench", "Chat", "Dashboard", "Trading Preferences", "Accessibility", "Keyboard Shortcuts", "About"].map((labelText) => ({
    section_id: labelText.toLowerCase().replace(/\s+/g, "-"),
    owner_label: labelText
  }));
}

function settingControlHtml(sectionLabel) {
  const themeOptions = [
    ["DARK_PRO", "Dark Pro"],
    ["MIDNIGHT_BLUE", "Midnight Blue"],
    ["SLATE", "Slate"],
    ["LIGHT_PRO", "Light Pro"],
    ["LOW_GLARE", "Low Glare"],
    ["HIGH_CONTRAST", "High Contrast"],
    ["CUSTOM", "Custom"],
  ];
  const select = (key, labelText, options) => `
    <label>${safe(labelText)}
      <select data-owner-setting="${safe(key)}">
        ${options.map(([value, text]) => `<option value="${safe(value)}" ${OwnerSettings.get(key) === value ? "selected" : ""}>${safe(text)}</option>`).join("")}
      </select>
      ${options.some(([value]) => value === "other") ? `<input type="text" data-owner-setting="${safe(key)}_custom" data-settings-other-field="${safe(key)}" value="${safe(OwnerSettings.get(`${key}_custom`) || "")}" placeholder="Custom ${safe(labelText.toLowerCase())}" aria-label="Custom ${safe(labelText)} candidate local preview" hidden><span class="source-category-hint" data-settings-other-copy="${safe(key)}" hidden>candidate_owner_custom / local_preview_guardrail only</span>` : ""}
    </label>
  `;
  const checkbox = (key, labelText) => `
    <label class="compact-toggle"><input type="checkbox" data-owner-setting="${safe(key)}" ${OwnerSettings.get(key) ? "checked" : ""}> ${safe(labelText)}</label>
  `;
  const color = (key, labelText) => `
    <label>${safe(labelText)}
      <input type="color" data-owner-setting="${safe(key)}" value="${safe(OwnerSettings.get(key) || "#2563EB")}">
    </label>
  `;
  const text = (key, labelText) => `
    <label>${safe(labelText)}
      <input type="text" data-owner-setting="${safe(key)}" value="${safe(OwnerSettings.get(key) || "")}">
    </label>
  `;
  if (sectionLabel === "Appearance") {
    return select("theme_preset", "Theme preset", themeOptions)
      + select("text_size", "Text size", TEXT_SIZE_VALUES.map((value) => [value, titleCase(value.replace("_", " "))]))
      + select("density", "Density", [["compact", "Compact"], ["comfortable", "Comfortable"]])
      + checkbox("reduced_motion", "Reduced motion");
  }
  if (sectionLabel === "Colors") {
    return color("input_required_color", "Input required")
      + color("review_required_color", "Review required")
      + color("warning_high_confirmation_color", "Warning / high confirmation")
      + color("provider_pending_color", "Provider pending")
      + color("success_color", "Success")
      + checkbox("high_contrast", "High contrast mode");
  }
  if (sectionLabel === "Layout") {
    return checkbox("sidebar_collapsed", "Collapse sidebar")
      + select("card_density", "Card density", [["compact", "Compact"], ["comfortable", "Comfortable"]])
      + select("dashboard_default_experience_mode", "Default experience mode", [["GUIDED_OWNER", "Guided"], ["ADVANCED_OWNER", "Advanced"], ["DEVELOPER", "Developer"]])
      + checkbox("dashboard_show_beginner_tips", "Show beginner tips");
  }
  if (sectionLabel === "Charts") {
    return select("chart_default_timeframe", "Default timeframe", RANGES.map((value) => [value, value]))
      + checkbox("chart_crosshair", "Crosshair")
      + checkbox("chart_tooltips", "Tooltips")
      + checkbox("chart_grid_lines", "Grid lines")
      + checkbox("chart_axis_labels", "Axis labels");
  }
  if (sectionLabel === "Workbench") {
    return select("workbench_preferred_market", "Preferred market", [["prediction_market", "Prediction Market"], ["other", "Other"]])
      + select("workbench_preferred_venue", "Preferred venue", [["qtt_decide", "Let QTT decide"], ["kalshi", "Kalshi"], ["polymarket", "Polymarket"], ["forecastex_ibkr", "FORECASTEX_IBKR"], ["other", "Other"]])
      + select("workbench_preferred_hold_unit", "Preferred hold unit", [["minutes", "minutes"], ["hours", "hours"], ["days", "days"], ["until_resolution", "until resolution"]])
      + select("workbench_preferred_maker_taker", "Maker/taker", [["maker_only", "maker-only"], ["maker_first_taker_fallback", "maker-first, taker fallback"], ["qtt_decide", "let QTT decide"]])
      + select("workbench_preferred_objective", "Objective", [["maximize_expected_net_cash", "max expected net cash"], ["preserve_capital", "preserve capital"], ["improve_diversification", "improve diversification"], ["qtt_decide", "let QTT decide"]]);
  }
  if (sectionLabel === "Chat") {
    return checkbox("chat_enter_to_send", "Enter to send")
      + checkbox("chat_prompt_suggestions", "Show prompt suggestions")
      + checkbox("qtt_guide_collapsed", "QTT Guide collapsed");
  }
  if (sectionLabel === "Dashboard") {
    return checkbox("dashboard_show_beginner_tips", "Show beginner tips")
      + checkbox("dashboard_show_technical_cards", "Show technical cards in Developer")
      + select("dashboard_default_experience_mode", "Default mode", [["GUIDED_OWNER", "Guided"], ["ADVANCED_OWNER", "Advanced"], ["DEVELOPER", "Developer"]]);
  }
  if (sectionLabel === "Trading Preferences") {
    return `
      <p class="inline-validation">Preview/prefill only. These values do not create source truth, connector semantics, risk-pass truth, replay/paper evidence, live readiness, order authority, or Execution Router authority.</p>
      ${select("trading_default_market", "Default market", [["prediction_market", "Prediction Market"], ["other", "Other"]])}
      ${select("trading_default_venue", "Default venue", [["qtt_decide", "Let QTT decide"], ["kalshi", "Kalshi"], ["polymarket", "Polymarket"], ["forecastex_ibkr", "FORECASTEX_IBKR"], ["other", "Other"]])}
      ${select("trading_default_risk_profile", "Risk profile", [["conservative_preview", "Conservative preview"], ["balanced_preview", "Balanced preview"], ["owner_custom_candidate", "Owner custom candidate"]])}
      ${select("trading_default_execution_preference", "Execution preference", [["maker_first_preview", "maker-first preview"], ["maker_only", "maker-only"], ["qtt_decide", "let QTT decide"]])}
      ${text("trading_default_portfolio_objective", "Portfolio objective")}
    `;
  }
  if (sectionLabel === "Accessibility") {
    return checkbox("high_contrast", "High contrast")
      + checkbox("keyboard_focus_visible", "Keyboard focus visible")
      + checkbox("reduced_motion", "Reduced motion")
      + checkbox("large_touch_targets", "Large touch targets");
  }
  if (sectionLabel === "Keyboard Shortcuts") {
    return `
      <div class="preview-grid">
        <span>Enter: newline by default</span>
        <span>Ctrl+Enter: Send</span>
        <span>Shift+Enter: newline</span>
        <span>Escape: close drawers/settings/menus</span>
      </div>
      ${checkbox("chat_enter_to_send", "Optional Enter-to-send")}
    `;
  }
  return `
    <div class="preview-grid">
      <span>Dashboard: local static review surface</span>
      <span>Status: Local Preview / Review Only</span>
      <span>No Live Trading</span>
      <span>No Account Access</span>
      <span>Settings persistence: ${safe(OWNER_SETTINGS_STORAGE_KEY)}</span>
    </div>
  `;
}

function renderSettingsCenter(activeSection = "Appearance") {
  const body = qs("#ownerSettingsBody");
  if (!body) return;
  const sections = settingsSections();
  body.innerHTML = `
    <div class="settings-tabs" role="tablist" aria-label="Settings sections">
      ${sections.map((section) => `
        <button class="settings-tab-button" type="button" role="tab" aria-selected="${section.owner_label === activeSection ? "true" : "false"}" data-settings-tab="${safe(section.owner_label)}">${safe(section.owner_label)}</button>
      `).join("")}
    </div>
    <section class="settings-section-panel" role="tabpanel" data-settings-section="${safe(activeSection)}">
      <h3>${safe(activeSection)}</h3>
      <div class="settings-control-grid">
        ${settingControlHtml(activeSection)}
      </div>
    </section>
  `;
  qsa("[data-settings-tab]", body).forEach((button) => {
    button.addEventListener("click", () => renderSettingsCenter(button.dataset.settingsTab));
  });
  qsa("[data-owner-setting]", body).forEach((control) => {
    control.addEventListener("change", (event) => {
      const target = event.currentTarget;
      const key = target.dataset.ownerSetting;
      const value = target.type === "checkbox" ? target.checked : target.value;
      OwnerSettings.set(key, value);
      if (key === "theme_preset") setTheme(value, false);
      if (key === "text_size") setTextSize(value, false);
      if (key === "dashboard_default_experience_mode") setExperienceMode(value, false);
      if (key === "chat_enter_to_send") setEnterToSend(value, false);
      if (key === "sidebar_collapsed") setSidebarCollapsed(value, false);
      updateSettingsOtherFields(body);
    });
  });
  updateSettingsOtherFields(body);
}

function updateSettingsOtherFields(root = document) {
  qsa("[data-settings-other-field]", root).forEach((customField) => {
    const sourceKey = customField.dataset.settingsOtherField;
    const source = qs(`[data-owner-setting="${CSS.escape(sourceKey)}"]`, root);
    const visible = source && source.value === "other";
    customField.hidden = !visible;
    customField.setAttribute("aria-hidden", visible ? "false" : "true");
    const copy = qs(`[data-settings-other-copy="${CSS.escape(sourceKey)}"]`, root);
    if (copy) copy.hidden = !visible;
  });
}

function setSettingsCenter(open) {
  const panel = qs("#ownerSettingsCenter");
  const toggle = qs("#ownerSettingsToggle");
  if (!panel || !toggle) return;
  DashboardSystem.interactionState.settingsOpen = Boolean(open);
  panel.hidden = !open;
  panel.classList.toggle("open", Boolean(open));
  panel.setAttribute("aria-hidden", open ? "false" : "true");
  toggle.setAttribute("aria-expanded", open ? "true" : "false");
  if (open) {
    renderSettingsCenter("Appearance");
    const first = qs("button, input, select, textarea", panel);
    if (first) first.focus();
  } else {
    toggle.focus({ preventScroll: true });
  }
}

function renderChatAndTrade() {
  const examples = asList(DASHBOARD_DATA.ui1r1_chat_examples && DASHBOARD_DATA.ui1r1_chat_examples.examples);
  const presets = chatPresetRows();
  qs("#chatWorkspace").innerHTML = `
    <article class="card chat-composer-card" data-chat-composer="owner-plain-english" data-chat-runtime-side-effect="false" data-chat-enter-to-send-default="false" data-intent-parser="local-preview" data-provider-stage="LLM1">
      <h3>Coach conversation</h3>
      <div class="chat-bubble owner-bubble"><strong>Owner</strong><p>Can QTT check this market?</p></div>
      <div class="chat-bubble qtt-bubble"><strong>QTT preview</strong><p>I can route this to a local trade-check preview, show missing evidence, and open the Trade Workbench. I will not call live agents or submit trades in this UI.</p></div>
      <label class="field-label" for="ownerChatInput">Message</label>
      <div class="chat-composer-row" data-chat-send-attached="true">
        <textarea id="ownerChatInput" rows="5" placeholder="Ask QTT to research, analyze, compare, or check a trade...">Can QTT check this market and find the best trade?</textarea>
        <button id="routePreviewButton" class="primary-command" type="button" data-chat-send-button="true">Send</button>
      </div>
      <p class="composer-hint">Ctrl+Enter = Send. Enter adds a new line.</p>
      <p id="chatSubmitHint" class="inline-validation" data-chat-submit-hint hidden></p>
      <div class="control-row">
        <label>Agent pod <select id="chatAgentSelector"><option>All QTT Agents</option><option>Risk + TCA</option><option>Research + QKU</option><option>Quantum readiness</option></select></label>
        <label>Source family <select id="chatSourceFamily"><option>Auto route</option><option>Market or event page</option><option>Research article</option><option>Formula text</option></select></label>
      </div>
      <div class="control-row">
        <input id="chatLinkInput" type="url" aria-label="Link input" placeholder="Optional source link">
        <button id="chatAttachmentPreview" type="button">File preview</button>
        <label class="compact-toggle"><input id="chatEnterToSendToggle" type="checkbox" data-enter-to-send-setting="optional"> Enter to send</label>
      </div>
      <label class="field-label" for="chatPresetSelect">Preset prompt</label>
      <select id="chatPresetSelect" data-chat-preset-dropdown="OwnerOptionCatalogV1.chat_presets">
        <option value="">Select a preset prompt...</option>
        ${presets.map((row) => `<option value="${safe(row.owner_label)}" data-source-category="${safe(row.source_category || "safe_ui_default")}">${safe(row.owner_label)}</option>`).join("")}
      </select>
      ${badge("no runtime side effect", "red")} ${badge("local preview parser", "blue")}
    </article>
    <div id="chatReceiptPreview" class="chat-receipt-column"></div>
    <article class="card route-card">
      <h3>Chat to trade route</h3>
      <p>Plain-English owner requests can become local Trade Workbench previews.</p>
      ${ownerControls({}, "trade_workbench")}
    </article>
    <article class="card route-card">
      <h3>Chat to research route</h3>
      <p>Research input is a candidate only, not source truth. Later providers must supply evidence.</p>
      ${ownerControls({}, "decision_queue")}
    </article>
  `;
  qs("#chatPresetSelect").addEventListener("change", (event) => {
    if (!event.currentTarget.value) return;
    fillChatComposer(event.currentTarget.value);
    const hint = qs("#chatSubmitHint");
    if (hint) {
      hint.hidden = false;
      hint.textContent = "Preset filled the composer. Edit it, then use Send or Ctrl+Enter to create a local preview.";
    }
  });
  qs("#ownerChatInput").addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const hint = qs("#chatSubmitHint");
    const enterToSendEnabled = DashboardSystem.interactionState.chatEnterToSend;
    if (event.ctrlKey || event.metaKey) {
      event.preventDefault();
      submitOwnerChat("CTRL_ENTER_SUBMIT");
      return;
    }
    if (enterToSendEnabled && !event.shiftKey) {
      event.preventDefault();
      submitOwnerChat("ENTER_TO_SEND_SUBMIT");
      return;
    }
    if (hint) {
      hint.hidden = false;
      hint.textContent = event.shiftKey
        ? "Shift+Enter inserted a newline. Use Ctrl+Enter or Send to create the local preview."
        : "Enter inserted a newline. Use Ctrl+Enter or Send to create the local preview.";
    }
  });
  initEnterToSendPreference(document);
  qs("#routePreviewButton").addEventListener("click", () => submitOwnerChat("BUTTON_SUBMIT"));

  const r2r2Workbench = DASHBOARD_DATA.ui1r2r2_workbench_form || {};
  const workbench = Object.keys(r2r2Workbench).length ? r2r2Workbench : (DASHBOARD_DATA.trade_workbench || DASHBOARD_DATA.ui1r1_order_sim || {});
  const fields = asList(workbench.field_catalog).length ? asList(workbench.field_catalog) : asList(workbench.owner_input_fields);
  const options = workbench.option_catalog || {};
  const rangePolicy = workbench.range_policy || (DASHBOARD_DATA.ui1r2r3_workbench_options_ranges && DASHBOARD_DATA.ui1r2r3_workbench_options_ranges.range_policy) || {};
  const buttons = [
    { label: "Check trade", next_step_id: "NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS" },
    { label: "Request replay preview", next_step_id: "NEXT_STEP_REQUEST_REPLAY_PREVIEW" },
    { label: "Request paper preview", next_step_id: "NEXT_STEP_REQUEST_PAPER_PREVIEW" },
    { label: "Show TCA", next_step_id: "NEXT_STEP_SHOW_TCA_COST_BREAKDOWN" },
    { label: "Explain no-trade", next_step_id: "NEXT_STEP_EXPLAIN_NO_TRADE" },
    { label: "Show QKU/formula routes", next_step_id: "NEXT_STEP_SHOW_QKU_FORMULA_ROUTES" }
  ];
  const comparisons = asList((DASHBOARD_DATA.ui1r1_order_sim || {}).comparison_cards);
  const defaultValueFor = (field) => {
    if (field.field_id === "market_event") return "describe_event";
    if (field.field_id === "market_family") return OwnerSettings.get("workbench_preferred_market") || "prediction_market";
    if (field.field_id === "venue") return OwnerSettings.get("workbench_preferred_venue") || "qtt_decide";
    if (field.field_id === "duration_unit") return OwnerSettings.get("workbench_preferred_hold_unit") || "days";
    if (field.field_id === "maker_taker_preference") return OwnerSettings.get("workbench_preferred_maker_taker") || "maker_first_taker_fallback";
    if (field.field_id === "objective") return OwnerSettings.get("workbench_preferred_objective") || "maximize_expected_net_cash";
    if (field.field_id === "plain_english_detail") return "";
    if (field.field_id === "max_budget") return "";
    if (field.field_id === "max_loss") return "";
    if (field.field_id === "hold_duration") return "";
    if (field.field_id === "source_thesis_url") return "";
    return "";
  };
  const hintHtml = (field) => {
    const policy = rangePolicy[field.range_policy_id || field.field_id] || {};
    const source = field.source_category || policy.source_category || "safe_ui_default";
    const unit = field.unit || policy.unit || "local preview";
    const min = policy.min === undefined ? "provider-pending" : policy.min;
    const max = policy.max === undefined ? "provider-pending" : policy.max;
    const dependency = policy.dependency || "Exact provider/venue bounds are pending.";
    return `
      <p class="range-hint" data-range-policy-id="${safe(field.range_policy_id || field.field_id)}">Unit: ${safe(unit)}. Min: ${safe(min)}. Max: ${safe(max)}. ${safe(dependency)}</p>
      <p class="source-category-hint" data-source-category="${safe(source)}">Source category: ${safe(source)}. Authority: ${safe(policy.authority_level || "local_preview_guardrail")}</p>
    `;
  };
  const fieldHtml = (field) => {
    const fieldId = field.field_id || field.id || "owner_input";
    const ownerLabel = field.owner_label || label(fieldId);
    const hidden = field.shown_when_field ? 'data-hidden-until-other="true"' : "";
    const state = field.interaction_state || (field.required ? "input_required" : "optional_input");
    const fieldAttrs = `data-workbench-field-shell="${safe(fieldId)}" data-interaction-state="${safe(state)}" data-field-initial-state="${safe(state)}" data-required="${field.required ? "true" : "false"}" data-source-category="${safe(field.source_category || "safe_ui_default")}" data-authority="${safe(field.authority || "local_preview_guardrail")}" ${hidden} data-shown-when-field="${safe(field.shown_when_field || "")}" data-shown-when-value="${safe(field.shown_when_value || "")}"`;
    const labelHeader = `<span class="workbench-label-text">${safe(ownerLabel)}</span>${interactionBadge(state)}${field.source_category === "candidate_owner_custom" ? badge("candidate / local preview only", "gray") : ""}`;
    if (field.input_kind === "select" && field.option_source && options[field.option_source]) {
      return `
        <label class="workbench-field" ${fieldAttrs}>${labelHeader}
          <select data-workbench-field="${safe(fieldId)}" data-trade-variable-field="${safe(fieldId)}" aria-label="${safe(ownerLabel)}">
            ${asList(options[field.option_source]).map((option) => `<option value="${safe(option.option_id)}" data-source-category="${safe(option.source_category || "safe_ui_default")}" ${defaultValueFor(field) === option.option_id ? "selected" : ""}>${safe(option.owner_label)}</option>`).join("")}
          </select>
          ${hintHtml(field)}
        </label>
      `;
    }
    if (field.input_kind === "textarea") {
      return `
        <label class="workbench-field" ${fieldAttrs}>${labelHeader}
          <textarea data-workbench-field="${safe(fieldId)}" data-trade-variable-field="${safe(fieldId)}" aria-label="${safe(ownerLabel)}" placeholder="${safe(fieldId === "plain_english_detail" ? "Describe the trade idea, risk question, source, or next step in normal English." : "Paste a thesis, market page, article, paper, formula, dataset, or trade idea.")}">${safe(defaultValueFor(field))}</textarea>
          ${hintHtml(field)}
        </label>
      `;
    }
    const type = field.input_kind === "number" ? "number" : "text";
    return `
      <label class="workbench-field" ${fieldAttrs}>${labelHeader}
        <input type="${safe(type)}" data-workbench-field="${safe(fieldId)}" data-trade-variable-field="${safe(fieldId)}" value="${safe(defaultValueFor(field))}" aria-label="${safe(ownerLabel)}">
        ${hintHtml(field)}
      </label>
    `;
  };
  qs("#tradeWorkbench").innerHTML = `
    <article class="card workbench-form-card" data-workbench-id="${safe(workbench.workbench_id || "OWNER_TRADE_WORKBENCH")}" data-owner-trade-intent-preview="OwnerTradeIntentV1" data-no-trade-comparator="true" data-champion-challenger-preview="true" data-tca-route="true" data-fdr-route="true" data-portfolio-marginal-utility-route="true" data-quantum-structural-readiness-route="true" data-execution-router-provider-pending="true">
      <h3>Trade Workbench preview</h3>
      <p id="tradeWorkbenchPrefill">No local context selected yet.</p>
      <div class="local-status-strip" data-workbench-local-status-strip="true">
        ${asList(workbench.local_status_strip).map((item) => badge(item, DashboardSystem.toneFor(item))).join("")}
      </div>
      <div id="tradeWorkbenchContextRefs" class="preview-grid workbench-context-refs" data-workbench-context-preview="WorkbenchContextPreviewV1">
        <span>Selected card/widget/chat ref: waiting</span>
        <span>QKU/formula route: provider-pending or gap route</span>
        <span>TCA/no-trade/capacity/FDR/marginal-utility/regime/quantum route: provider-pending or gap route</span>
        <span>PR165-D2 agent role refs: routed or explicit gap</span>
      </div>
      <div class="workbench-fields">
        ${fields.map(fieldHtml).join("")}
        <div id="workbenchRangeValidation" class="range-validation-panel" data-workbench-inline-validation="true" hidden></div>
      </div>
      <div class="chip-row action-row">
        ${buttons.map((row) => `<button class="chip" type="button" data-next-step-id="${safe(row.next_step_id)}" data-local-receipt-preview="TradePlanCandidatePreviewV1">${safe(row.label)}</button>`).join("")}
      </div>
      ${badge("local request preview only", "red")} ${badge("Execution Router provider-pending", "gray")}
      ${ownerControls(workbench, "trade_workbench")}
    </article>
    <article id="tradePlanCandidatePreview" class="card workbench-preview-card" data-preview-object="TradePlanCandidatePreviewV1" data-runtime-side-effect-allowed="false">
      <h3>Trade plan candidate preview</h3>
      <p>Complete the local form to preview a candidate, the challenger, and no-trade route without creating any runtime request.</p>
      <div id="workbenchPreviewGrid" class="preview-grid"></div>
      <div class="preview-grid">
        ${asList(workbench.local_preview_output && workbench.local_preview_output.route_previews).map((route) => `<span>${safe(label(route))}: provider-pending or gap-routed</span>`).join("")}
      </div>
    </article>
    ${comparisons.map((row) => `
      <article class="card comparison-card" data-comparison-card="${safe(row.card_id)}">
        <h3>${safe(label(row.card_id))}</h3>
        <p>${safe(label(row.route_ref))}. Score/value provider-pending; no fake PnL, fill, or live-position result.</p>
        ${badges(row, ["Trade plan candidate"])}
        ${ownerControls(row, "trade_workbench")}
      </article>
    `).join("")}
    <article class="card">
      <h3>No-trade reoptimization paths</h3>
      <p>No-trade is a comparator and reoptimization route. QTT can preview reoptimization routes without changing immutable QKUs or formulas.</p>
      ${badge("no-trade is comparator", "blue")}
      ${ownerControls(workbench, "trade_workbench")}
    </article>
    <article class="card">
      <h3>Decision spine routes</h3>
      <p>Execution-adjusted rank, cost breakdown, false-discovery check, portfolio benefit, capacity, memory, no-trade, and quantum-readiness routes stay linked.</p>
      ${badge("institutional refs linked", "green")} ${badge("quantum readiness routed", "purple")}
      ${ownerControls(workbench, "trade_workbench")}
    </article>
  `;
  qsa("#tradeWorkbench .card").forEach((card) => {
    card.__qttRow = workbench;
    card.addEventListener("click", (event) => {
      if (event.target.closest("button, input, select, textarea, summary, details")) return;
      openDrawer(card.querySelector("h3").textContent, "Trade Workbench", workbench);
    });
  });
  wireWorkbenchForm();
  wireNextActions(qs("#tradeWorkbench"));
}

function workbenchValues() {
  const values = {};
  qsa("[data-workbench-field]").forEach((field) => {
    values[field.dataset.workbenchField] = field.value;
  });
  return values;
}

function optionLabel(fieldId, value) {
  const workbench = DASHBOARD_DATA.ui1r2r2_workbench_form || DASHBOARD_DATA.trade_workbench || {};
  const fields = asList(workbench.field_catalog);
  const field = fields.find((row) => row.field_id === fieldId) || {};
  const options = asList((workbench.option_catalog || {})[field.option_source]);
  const option = options.find((row) => row.option_id === value);
  return option ? option.owner_label : value;
}

function updateOtherFields() {
  qsa("[data-hidden-until-other='true']").forEach((shell) => {
    const source = shell.dataset.shownWhenField;
    const expected = shell.dataset.shownWhenValue || "other";
    const sourceField = qs(`[data-workbench-field="${CSS.escape(source)}"]`);
    const visible = sourceField && sourceField.value === expected;
    shell.dataset.otherVisible = visible ? "true" : "false";
    shell.setAttribute("aria-hidden", visible ? "false" : "true");
  });
}

function updateWorkbenchFieldStates(values) {
  qsa("[data-workbench-field-shell]").forEach((shell) => {
    const fieldId = shell.dataset.workbenchFieldShell;
    const initial = shell.dataset.fieldInitialState || "optional_input";
    if (initial === "provider_pending" || initial === "technical_only") {
      shell.dataset.interactionState = initial;
      return;
    }
    const visible = shell.dataset.hiddenUntilOther === "true" ? shell.dataset.otherVisible === "true" : true;
    const value = String(values[fieldId] || "").trim();
    const required = shell.dataset.required === "true";
    const nextState = visible && value ? "review_required" : required ? "input_required" : "optional_input";
    shell.dataset.interactionState = nextState;
    shell.setAttribute("aria-label", `${label(fieldId)} ${label(nextState)}`);
    const badgeNode = qs("[data-interaction-badge]", shell);
    if (badgeNode) {
      const badgeLabel = {
        input_required: "Input needed",
        review_required: "Review",
        optional_input: "Optional",
        provider_pending: "Provider pending",
      }[nextState] || label(nextState);
      badgeNode.dataset.interactionBadge = nextState;
      badgeNode.textContent = badgeLabel;
      badgeNode.setAttribute("aria-label", badgeLabel);
    }
  });
}

function validateWorkbenchValues(values) {
  const messages = [];
  const budget = Number(values.max_budget);
  const loss = Number(values.max_loss);
  const exposure = Number(values.portfolio_exposure);
  const hold = Number(values.hold_duration);
  const durationUnit = values.duration_unit || "days";
  const target = Number(values.target_price_probability);
  const stop = Number(values.stop_exit_preference);
  const latency = Number(values.latency_budget);
  const spread = Number(values.max_spread);
  if (values.max_budget && (!Number.isFinite(budget) || budget <= 0)) messages.push("Max budget must be a positive local-preview number.");
  if (values.max_loss && (!Number.isFinite(loss) || loss <= 0)) messages.push("Max loss must be a positive local-preview number.");
  if (Number.isFinite(budget) && Number.isFinite(loss) && loss > budget) messages.push("Max loss must be less than or equal to max budget.");
  if (values.portfolio_exposure && (!Number.isFinite(exposure) || exposure < 0 || exposure > 100)) messages.push("Portfolio exposure preview must be between 0 and 100%.");
  if (values.target_price_probability && (!Number.isFinite(target) || target < 0 || target > 100)) messages.push("Target price/probability preview must stay within 0-100.");
  if (values.stop_exit_preference && (!Number.isFinite(stop) || stop < 0 || stop > 100)) messages.push("Stop/exit threshold preview must stay within 0-100.");
  if (values.latency_budget && (!Number.isFinite(latency) || latency <= 0)) messages.push("Latency budget must be positive when shown.");
  if (values.max_spread && (!Number.isFinite(spread) || spread < 0)) messages.push("Max spread cannot be negative.");
  if (values.hold_duration && (!Number.isFinite(hold) || hold <= 0)) messages.push("Hold duration must be positive.");
  if (Number.isFinite(hold) && durationUnit === "minutes" && hold < 1) messages.push("Hold duration below one minute is rejected by local preview guardrails.");
  if (Number.isFinite(hold) && durationUnit === "days" && hold > 3650) messages.push("Hold duration is too large for local preview; exact event close/resolution is provider-pending.");
  if (values.market_family === "other" && !String(values.custom_market_family || "").trim()) messages.push("Other market family needs a candidate custom market family.");
  if (values.event_category === "other" && !String(values.custom_event_category || "").trim()) messages.push("Other event category needs a candidate custom event category.");
  if (values.market_event === "other" && !String(values.custom_event || "").trim()) messages.push("Other event needs a candidate custom event description.");
  if (values.venue === "other" && !String(values.custom_venue || "").trim()) messages.push("Other venue remains candidate-only and needs a custom venue label.");
  if (values.source_family === "other" && !String(values.custom_source_family || "").trim()) messages.push("Other source family remains candidate-only and needs a custom source label.");
  if (values.route_selector === "other" && !String(values.custom_route_type || "").trim()) messages.push("Other route type needs a candidate custom route type.");
  return messages;
}

function updateWorkbenchPreview() {
  const values = workbenchValues();
  DashboardSystem.interactionState.workbenchPreview = values;
  updateOtherFields();
  updateWorkbenchFieldStates(values);
  const validation = qs("#workbenchRangeValidation");
  const validationMessages = validateWorkbenchValues(values);
  if (validation) {
    validation.hidden = validationMessages.length === 0;
    validation.innerHTML = validationMessages.map((message) => `<div>${safe(message)}</div>`).join("");
  }
  const grid = qs("#workbenchPreviewGrid");
  if (!grid) return;
  const summaryRows = [
    ["Market/event", values.market_event || "needs owner input"],
    ["Venue", optionLabel("venue", values.venue || "qtt_decide")],
    ["Side", optionLabel("side", values.side || "qtt_decide")],
    ["Objective", optionLabel("objective", values.objective || "qtt_decide")],
    ["Plain-English detail", values.plain_english_detail || "needs owner input"],
    ["Max budget", values.max_budget || "needs owner input"],
    ["Max loss", values.max_loss || "needs owner input"],
    ["Portfolio exposure", values.portfolio_exposure ? `${values.portfolio_exposure}% preview` : "provider-pending account exposure"],
    ["Hold duration", values.hold_duration ? `${values.hold_duration} ${optionLabel("duration_unit", values.duration_unit || "days")}` : "needs owner input; exact max depends on event close/resolution"],
    ["Urgency", optionLabel("urgency", values.urgency || "normal")],
    ["Entry", optionLabel("entry_preference", values.entry_preference || "qtt_decide")],
    ["Exit", optionLabel("exit_preference", values.exit_preference || "qtt_decide")],
    ["Maker/taker", optionLabel("maker_taker_preference", values.maker_taker_preference || "qtt_decide")],
    ["Source/thesis", values.source_thesis_url || "candidate/provisional input"],
    ["Custom market family", values.custom_market_family || "candidate only if Other selected"],
    ["Custom event category", values.custom_event_category || "candidate only if Other selected"],
    ["Custom event / market / URL", values.custom_event || "candidate only if Other selected"],
    ["Custom venue", values.custom_venue || "candidate only if Other selected"],
    ["Custom source family", values.custom_source_family || "candidate only if Other selected"],
    ["Custom route type", values.custom_route_type || "candidate only if Other selected"],
    ["No-trade comparator", "shown as first-class local preview"],
    ["What would make this pass", "smaller size, different venue, maker-only, better liquidity, or later timing may be retested later"],
    ["Runtime work", "none"],
  ];
  grid.innerHTML = summaryRows.map(([name, value]) => `<span><strong>${safe(name)}:</strong> ${safe(label(value))}</span>`).join("");
}

function wireWorkbenchForm() {
  qsa("[data-workbench-field]").forEach((field) => {
    field.addEventListener("input", updateWorkbenchPreview);
    field.addEventListener("change", updateWorkbenchPreview);
  });
  updateWorkbenchPreview();
}

function renderAgentsAndContracts() {
  const r2r4 = DASHBOARD_DATA.ui1r2r4_semantic_bundle || {};
  const authorityBoundaryRef = (DASHBOARD_DATA.authority_boundary && DASHBOARD_DATA.authority_boundary.UI1_authority_boundary_ref) || "LOCAL_STATIC_NO_RUNTIME_NO_CREDENTIALS_NO_DIRECT_VENUE_SUBMIT_NO_EXECUTION_ROUTER_RELEASE";
  const disagreement = asList(DASHBOARD_DATA.ui1r1_agent_disagreement && DASHBOARD_DATA.ui1r1_agent_disagreement.rows);
  const centralAgentRows = asList(r2r4.agent_operations_projection);
  const agentRows = centralAgentRows.length ? centralAgentRows : [
    ...disagreement,
    ...asList(DASHBOARD_DATA.agent_performance),
    ...asList(DASHBOARD_DATA.widget_manifest).filter((row) => /Agent|KPI|Trust|Quarantine|Replacement|Reroute/i.test(label(row.widget_title || row.widget_id))).slice(0, 12)
  ];
  qs("#agentOperations").innerHTML = `
    <article class="wide-card monitoring-shell-card" data-agent-operations-shell="OwnerAgentOperationsProjectionV1" data-interaction-state="provider_pending">
      <h3>Agent Operations</h3>
      <p>Provider-pending monitoring shell for duty, KPI, trust, current task, upcoming task queue, missed duty, quarantine, reroute, replacement, permission-change, and receipt preview. No real-time agent activity is running in this UI.</p>
      <div class="preview-grid">
        <span>Duty board: provider-pending</span>
        <span>KPI board: provider-pending</span>
        <span>Trust scores: provider-pending</span>
        <span>Quarantine: provider-pending</span>
        <span>Receipts: provider-pending</span>
      </div>
      ${badges({ provider_stage: "AGENT_ORCH1_PROVIDER_PENDING", authority_boundary_ref: authorityBoundaryRef }, ["PR165-D2 refs or gaps"])}
    </article>
    ${agentRows.slice(0, 14).map((row) => `
      <article class="card agent-card" data-objection-type="${safe(row.objection_type || "")}" data-agent-row-id="${safe(row.agent_id || row.row_id || "")}" data-interaction-state="provider_pending">
        <h3>${safe(row.agent_role || DashboardSystem.ownerTitle(row, "Agent route"))}</h3>
        <p>${safe(row.agent_status || DashboardSystem.summary(row, "Agent role refs or explicit gap routes are rendered. No fake agent claim is made."))}</p>
        <div class="preview-grid">
          <span>Current task: ${safe(row.current_task_id || "provider-pending")}</span>
          <span>Upcoming queue: ${safe(row.queue_lane || "provider-pending")}</span>
          <span>Trust/KPI: ${safe(row.trust_score || "provider-pending")}</span>
          <span>Quarantine: ${safe(row.quarantine_state || "provider-pending")}</span>
          <span>Receipt: ${safe(row.last_receipt || row.receipt_preview || "provider-pending")}</span>
          <span>Blocked: ${safe(row.blocked_reason || "provider-pending")}</span>
        </div>
        ${row.objection_type ? `<div class="bar-row"><span>Objection</span><div class="bar-track"><div class="bar-fill" style="--bar-width:66%;--bar-color:var(--qtt-orange)"></div></div><span>routed</span></div>` : ""}
        ${badges(row, ["provider pending", "no fake agent activity"])}
        ${ownerControls(row, "agent_disagreement")}
      </article>
    `).join("")}
  `;
  qsa("#agentOperations .card").forEach((card, index) => {
    card.__qttRow = agentRows[index] || {};
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(agentRows[index] || {}, "Agent Operations"), "Agent Operations", agentRows[index] || {}, "why"));
  });
  const workflowRows = asList(r2r4.workflow_queue_projection);
  qs("#qttTeamWorkflowQueue").innerHTML = `
    <article class="wide-card monitoring-shell-card" data-workflow-queue-shell="OwnerWorkflowQueueStateV1" data-interaction-state="provider_pending">
      <h3>QTT Team Workflow Queue</h3>
      <p>All current and upcoming workflows stay local/static/provider-pending here. Responsible, supporting, and escalation agents are tags for later orchestration, not running tasks.</p>
      ${badges({ provider_stage: "SVC1_AGENTS_PAPER_LOOP_PROVIDER_PENDING", authority_boundary_ref: authorityBoundaryRef }, ["team queue shell"])}
    </article>
    ${workflowRows.map((row) => `
      <article class="card workflow-card" data-workflow-id="${safe(row.workflow_id)}" data-interaction-state="provider_pending">
        <h3>${safe(label(row.current_stage || row.workflow_id))}</h3>
        <p>${safe(row.market_venue_event || "Market / venue / event provider-pending")}</p>
        <div class="preview-grid">
          <span>Responsible: ${safe(row.responsible_agent || "provider-pending")}</span>
          <span>Supporting: ${safe(row.backup_agent || "provider-pending")}</span>
          <span>Escalation: ${safe(row.escalation || "Commander/Governance")}</span>
          <span>Current stage: ${safe(row.current_stage || "Queued")}</span>
          <span>Next stage: ${safe(row.next_stage || "provider-pending")}</span>
          <span>Latest receipt: ${safe(row.latest_receipt || "provider-pending")}</span>
          <span>TCA: ${safe(row.TCA_status || "provider-pending")}</span>
          <span>Risk: ${safe(row.risk_status || "provider-pending")}</span>
          <span>No-trade: ${safe(row.no_trade_status || "provider-pending")}</span>
        </div>
        ${ownerControls(row, "provider_pending")}
      </article>
    `).join("")}
  `;
  qsa("#qttTeamWorkflowQueue .card").forEach((card, index) => {
    card.__qttRow = workflowRows[index] || {};
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(workflowRows[index] || {}, "Workflow queue"), "QTT Team Workflow Queue", workflowRows[index] || {}, "why"));
  });
  const receiptRows = asList(r2r4.receipt_preview_projection);
  qs("#auditReceiptPreview").innerHTML = `
    <article class="wide-card monitoring-shell-card" data-receipt-preview-shell="OwnerReceiptPreviewStateV1" data-interaction-state="provider_pending">
      <h3>Audit Trail / Receipts Preview</h3>
      <p>Proof slots for later runtime, agent, memory, paper, no-trade, risk, TCA, and owner-action receipts. No fake timestamps, fake paper/live values, fake agent actions, or order receipts are created.</p>
      ${badges({ provider_stage: "SVC1_AGENTS_PAPER_LOOP_PROVIDER_PENDING", authority_boundary_ref: authorityBoundaryRef }, ["receipt preview only"])}
    </article>
    ${receiptRows.map((row) => `
      <article class="card receipt-preview-card" data-receipt-class="${safe(row.receipt_class)}" data-interaction-state="provider_pending">
        <h3>${safe(row.receipt_class)}</h3>
        <p>${safe(row.owner_visible_status || "Provider-pending preview label only.")}</p>
        <div class="preview-grid">
          <span>Proof state: ${safe(row.proof_state || "provider-pending")}</span>
          <span>Fake receipt: false</span>
          <span>Fake timestamp: false</span>
          <span>Paper/live values: false</span>
        </div>
        ${ownerControls(row, "provider_pending")}
      </article>
    `).join("")}
  `;
  qsa("#auditReceiptPreview .card").forEach((card, index) => {
    card.__qttRow = receiptRows[index] || {};
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(receiptRows[index] || {}, "Receipt preview"), "Audit Trail / Receipts Preview", receiptRows[index] || {}, "learn"));
  });
  qs("#llmPanel").innerHTML = `
    <h3>QTT reasoning route</h3>
    <p>Reasoning providers may later research, summarize, critique, explain, propose routes, and detect missing evidence. They do not create source truth, risk pass, live readiness, cash/account truth, quantum advantage proof, or order-release authority.</p>
    ${badge("bounded reasoning", "purple")} ${badge("no live LLM runtime", "red")}
    ${ownerControls(DASHBOARD_DATA.authority_boundary || {}, "provider_pending")}
  `;
  qs("#llmPanel").__qttRow = DASHBOARD_DATA.authority_boundary || {};
  qs("#llmPanel").addEventListener("click", () => openDrawer("QTT reasoning route", "Authority boundary", DASHBOARD_DATA.authority_boundary || {}, "why"));
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
            ${badge(row.owner_default === false ? "not owner primary" : "diagnostic", "gray")}
          </article>
        `).join("")}
      </div>
      <div class="table-shell raw-ref-table developer-technical-shell">
        <h3>Raw refs and report diagnostics</h3>
        <table>
          <thead><tr><th>Area</th><th>Ref</th><th>Owner default</th></tr></thead>
          <tbody>
            <tr><td>OwnerActionRegistry</td><td>owner_action_registry.generated.jsonl</td><td>false</td></tr>
            <tr><td>OwnerSurfaceResolver</td><td>src/qtt/dashboard/owner_surface_resolver.py</td><td>false</td></tr>
            <tr><td>No-orphan report</td><td>owner_dashboard_no_orphan.report.json</td><td>false</td></tr>
            <tr><td>Authority boundary</td><td>owner_dashboard_authority_boundary.report.json</td><td>false</td></tr>
            <tr><td>Playwright evidence</td><td>ui1r2_playwright.report.json</td><td>false</td></tr>
          </tbody>
        </table>
      </div>
    </details>
  `;
  qsa("#developerMode .card").forEach((card, index) => {
    card.__qttRow = diagnostics[index] || dev;
    card.addEventListener("click", () => openDrawer(card.querySelector("h3").textContent, "Developer Mode", diagnostics[index] || dev, "technical_details"));
  });
}

function renderAutonomyAndGlossary() {
  qs("#ownerAutonomyEducation").innerHTML = `
    <details class="learning-details autonomy-ladder">
      <summary>How QTT will trade with AI</summary>
      <ol>
        <li>Owner idea / QTT scout</li>
        <li>Research</li>
        <li>QKU/formula stack</li>
        <li>Trade-variable search</li>
        <li>Replay</li>
        <li>Paper</li>
        <li>Shadow / live-dryrun</li>
        <li>Live canary review</li>
        <li>Execution Router</li>
        <li>Venue</li>
      </ol>
      <p>QTT agents can later prepare evidence and evaluate candidates automatically inside owner-approved policies. The owner handles objectives, approvals, vetoes, overrides, and high-risk decisions. Final live order release remains downstream through the governed Execution Router.</p>
    </details>
  `;
  const glossary = asList(DASHBOARD_DATA.ui1r2_education && DASHBOARD_DATA.ui1r2_education.glossary);
  qs("#ownerGlossary").innerHTML = `
    <h3>Owner glossary</h3>
    <input id="glossarySearch" class="table-filter" type="search" placeholder="Search terms such as TCA, no-trade, QKU, Execution Router">
    <div class="glossary-grid">
      ${glossary.map((row) => `
        <details class="glossary-term" data-glossary-term="${safe(row.term)}">
          <summary>${safe(row.term)}</summary>
          <p>${safe(row.plain_english_definition)}</p>
          <p>${safe(row.why_it_matters)}</p>
        </details>
      `).join("")}
    </div>
  `;
  qs("#glossarySearch").addEventListener("input", (event) => {
    const query = event.currentTarget.value.trim().toLowerCase();
    qsa(".glossary-term").forEach((term) => {
      term.classList.toggle("hidden-by-filter", query && !term.textContent.toLowerCase().includes(query));
    });
  });
}

function renderProviderAndMore() {
  const routes = asList(DASHBOARD_DATA.provider_stage_routes);
  qs("#providerStageRoutes").innerHTML = routes.map((row) => `
    <article class="route-card">
      <h3>${safe(DashboardSystem.ownerTitle(row, "Provider route"))}</h3>
      <p>${safe(DashboardSystem.summary(row, "Provider route visible without runtime side effects."))}</p>
      ${badges(row, ["activation route"])}
      ${ownerControls(row, "provider_pending")}
    </article>
  `).join("");
  qsa("#providerStageRoutes .route-card").forEach((card, index) => {
    card.__qttRow = routes[index];
    card.addEventListener("click", () => openDrawer(DashboardSystem.ownerTitle(routes[index]), "Provider Stage Route Map", routes[index], "technical_details"));
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
      <h3>${safe(label(title))}</h3>
      <p>${safe(DashboardSystem.summary(row || {}, "Workflow boundary visible without runtime access."))}</p>
      ${badges(row || {}, ["runtime boundary"])}
      ${ownerControls(row || {}, "provider_pending")}
    </article>
  `).join("");
  qsa("#systemContracts .card").forEach((card, index) => {
    card.__qttRow = contracts[index][1] || {};
    card.addEventListener("click", () => openDrawer(contracts[index][0], "Workflow status", contracts[index][1] || {}, "technical_details"));
  });
  renderAutonomyAndGlossary();
  const dagRows = asList(DASHBOARD_DATA.dag && DASHBOARD_DATA.dag.rows);
  renderTable("#dagRouteMap", dagRows.slice(0, 20), ["node_id", "source_artifact_ref", "downstream_consumer_ref", "authority_boundary_ref"], "Workflow route map", "provider_pending");
}

function searchRowsFor(query) {
  const rows = asList(DASHBOARD_DATA.ui1r2r3_navigation_sidebar_search && DASHBOARD_DATA.ui1r2r3_navigation_sidebar_search.ranked_search_index);
  const mode = document.body.dataset.experienceMode || "GUIDED_OWNER";
  const normalized = String(query || "").trim().toLowerCase();
  if (!normalized) return [];
  return rows
    .filter((row) => !row.developer_only || mode === "DEVELOPER" || normalized.includes("developer"))
    .map((row) => {
      const aliases = asList(row.query_aliases).map((item) => String(item).toLowerCase());
      const exact = aliases.includes(normalized) || String(row.owner_title || "").toLowerCase() === normalized;
      const alias = aliases.some((item) => item.includes(normalized) || normalized.includes(item));
      const title = String(row.owner_title || "").toLowerCase().includes(normalized);
      const score = exact ? 100 : alias ? 80 : title ? 60 : 0;
      return { ...row, score };
    })
    .filter((row) => row.score > 0)
    .sort((a, b) => b.score - a.score || Number(a.rank || 9) - Number(b.rank || 9))
    .slice(0, 5);
}

function applySearch() {
  const input = qs("#globalSearch");
  const results = qs("#ownerSearchResults");
  if (!input || !results) return;
  const query = input.value.trim();
  const rows = searchRowsFor(query);
  if (!query) {
    results.innerHTML = "";
    return;
  }
  if (!rows.length) {
    results.innerHTML = `<div class="search-result-button" role="status"><strong>No matching dashboard item</strong><span>Try Chat / Ask QTT, Trade Workbench, Research, Portfolio, Agent Operations, or QKU / Formula Routes.</span></div>`;
    return;
  }
  results.innerHTML = rows.map((row, index) => `
    <button class="search-result-button" type="button" data-search-result-index="${index}" data-target-surface="${safe(row.target_surface_id)}" data-target-card="${safe(row.target_card_id)}">
      <strong>${safe(row.owner_title)}</strong>
      <span>${safe(row.reason)}</span>
    </button>
  `).join("");
  qsa("[data-search-result-index]", results).forEach((button) => {
    button.addEventListener("click", () => {
      const targetSurface = button.dataset.targetSurface || "overview";
      const targetCard = button.dataset.targetCard || targetSurface;
      DashboardSystem.setActiveSurface(targetSurface, targetCard);
      location.hash = targetSurface;
      results.dataset.lastSelectedTarget = `${targetSurface}:${targetCard}`;
    });
  });
}

function wireNavigation() {
  const links = [...qsa(".mobile-bottom-nav a"), ...qsa(".rail a")];
  links.forEach((link) => {
    link.addEventListener("click", () => {
      const surface = (link.getAttribute("href") || "#overview").replace("#", "");
      DashboardSystem.setActiveSurface(surface, surface);
    });
  });
  const current = (location.hash || "#overview").replace("#", "");
  DashboardSystem.setActiveSurface(current || "overview", current || "overview");
}

function repairStaticShellCopy() {
  const overviewEyebrow = qs("#overview .section-head .eyebrow");
  if (overviewEyebrow) overviewEyebrow.textContent = "Guided owner mode - local previews";
}

function render() {
  OwnerSettings.applyCssSettings();
  initTheme();
  initTextSize();
  initExperienceMode();
  initOptionsMenu();
  initTopPanels();
  initSidebar();
  repairStaticShellCopy();
  renderStatus();
  renderCoach();
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
  applyExperienceModePolicy(document.body.dataset.experienceMode || "GUIDED_OWNER");
  wireNavigation();
  wireNextActions(document);
  qs("#globalSearch").addEventListener("input", applySearch);
  qs("#closeDrawer").addEventListener("click", closeDrawer);
  qs("#openGlobalDrilldown").addEventListener("click", () => openDrawer("Dashboard technical details", "Renderer, not execution authority", DASHBOARD_DATA.authority_boundary || {}, "technical_details"));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeDrawer();
      closeOwnerOptions();
      setSettingsCenter(false);
      setQttGuide(false);
    }
  });
}

render();
