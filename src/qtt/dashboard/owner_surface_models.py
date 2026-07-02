"""Shared constants and JSON helpers for the PR169-DASH1 owner surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


PR_ID = "PR169-DASH1"
REGISTRY_FILENAME = "owner_dashboard_surface_registry.jsonl"
REGISTRY_REF = REGISTRY_FILENAME
GENERATED_FROM = REGISTRY_FILENAME
AUTHORITATIVE_SOURCE = REGISTRY_FILENAME
PRODUCER_TOOL = "tools/build_pr169_dash1_owner_dashboard.py"
VALIDATOR_REF = "tools/validate_pr169_dash1_owner_dashboard.py"
VALIDATION_MARKER = "PR169_DASH1_OWNER_DASHBOARD_VALIDATION_OK"
AUTHORITY_BOUNDARY_REF = (
    "PR169_DASH1_AUTHORITY_BOUNDARY::NO_DASHBOARD_RUNTIME_NO_ORDER_NO_PRIVATE_READS"
)
NO_ORPHAN_REF = "owner_dashboard_no_orphan.report.json"

LIFECYCLE_STATES = frozenset(
    {
        "MATERIALIZED_IN_DASH1",
        "CONTRACT_DEFINED_PROVIDER_PENDING",
        "ROUTED_PENDING_PROVIDER",
        "BLOCKED_BY_AUTHORITY_BOUNDARY",
        "OUT_OF_SCOPE_FOR_DASH1",
    }
)

V4_ROUTE_LABELS = frozenset(
    {
        "TG1",
        "READINESS1",
        "PRETRADE1",
        "LLM1",
        "LLM2",
        "AGENT-ORCH1",
        "PAPER-LOOP",
        "HOTPATH1",
        "LIVE-DRYRUN1",
        "LIVE-PILOT",
        "LAUNCH",
        "POSTLAUNCH",
        "RI1",
        "PLUGIN1",
        "QMAP1",
        "ALLOW1",
    }
)

REGISTRY_REQUIRED_FIELDS = (
    "feature_id",
    "feature_kind",
    "canonical_label",
    "legacy_aliases",
    "panel_id",
    "packet_layer",
    "card_type",
    "action_code_refs",
    "owner_view_purpose",
    "owner_control_purpose",
    "lifecycle_state",
    "provider_stage",
    "target_stage",
    "owning_stage_or_pr",
    "activation_route",
    "provider_contract_ref",
    "v4_route_label",
    "legacy_route_aliases",
    "upstream_artifact_refs",
    "downstream_consumer_refs",
    "agent_role_refs_from_PR165_D2",
    "responsible_agent_role",
    "consumer_agent_role",
    "fallback_route_if_role_missing",
    "agent_route_validation_ref",
    "reasoning_brain_view_policy",
    "telegram_projection_policy",
    "dashboard_projection_policy",
    "external_fact_receipt_policy",
    "source_workflow_policy",
    "live_state_display_policy",
    "cash_private_snapshot_policy",
    "shadow_mode_display_policy",
    "edge_alpha_capture_policy",
    "chart_surface_policy",
    "qku_route_policy",
    "formula_route_policy",
    "candidate_route_policy",
    "quantum_structural_readiness_policy",
    "institutional_metric_policy",
    "authority_boundary_refs",
    "qku_formula_immutability_policy",
    "trade_plan_variable_policy",
    "qtt_sha_policy",
    "atomicrows_sha_policy",
    "quantum_backend_policy",
    "profit_guarantee_policy",
    "no_orphan_status",
    "validation_ref",
)

PROJECTION_TRACE_FIELDS = (
    "generated_from",
    "manual_edit_allowed",
    "authoritative_source",
    "registry_row_ref",
)

FORBIDDEN_AGENT_FIELDS = frozenset(
    {
        "master_plan_source_status",
        "currentization_reason",
        "stale_currentization_status",
        "stale_logic_reason",
        "imported_from_stale_master_plan_flag",
        "codex_scratchpad",
        "chain_of_thought",
    }
)

FORBIDDEN_STRING_MARKERS = frozenset(
    {
        "paper_submit_authority",
        "shadow_execution_authority",
        "live_order_authority",
        "connector_writes",
        "private_state_reads",
        "cash_account_reads",
        "source_truth_acceptance_engine",
        "telegram_bot_runtime",
        "llm_runtime",
        "quantum_backend_execution",
        "quantum_advantage_claim",
        "profit_guarantee=true",
        "qtt_generated_sha",
        "atomicrows_hash_sha_authority",
    }
)

REQUIRED_JSONL_OUTPUTS = (
    "owner_dashboard_packet.generated.jsonl",
    "owner_header_strip.generated.jsonl",
    "owner_decision_queue.generated.jsonl",
    "owner_actionable_card.generated.jsonl",
    "owner_action_registry.generated.jsonl",
    "owner_review_policy.generated.jsonl",
    "owner_safe_action_policy.generated.jsonl",
    "owner_action_receipt_template.generated.jsonl",
    "owner_audit_trail_seed.generated.jsonl",
    "owner_approval_ladder.generated.jsonl",
    "owner_confirmation_class.generated.jsonl",
    "owner_kill_switch_surface.generated.jsonl",
    "owner_global_authority_policy.generated.jsonl",
    "owner_source_panel_contract.generated.jsonl",
    "owner_live_cash_private_display_contract.generated.jsonl",
    "owner_shadow_mode_display_contract.generated.jsonl",
    "owner_reasoning_brain_view_contract.generated.jsonl",
    "owner_edge_alpha_capture_view.generated.jsonl",
    "owner_qku_formula_candidate_route_view.generated.jsonl",
    "owner_quantum_structural_readiness_view.generated.jsonl",
    "owner_institutional_metric_view.generated.jsonl",
    "owner_chart_surface_contract.generated.jsonl",
    "owner_chart_panel_projection.generated.jsonl",
    "owner_data_value_route_map.generated.jsonl",
    "owner_agent_intelligence_route_view.generated.jsonl",
    "owner_execution_authority_ladder_view.generated.jsonl",
    "owner_panel_projection.generated.jsonl",
    "owner_telegram_projection.generated.jsonl",
    "owner_agent_route_projection.generated.jsonl",
    "owner_llm_view_projection.generated.jsonl",
    "owner_downstream_route_projection.generated.jsonl",
    "owner_dashboard_feature_coverage.generated.jsonl",
    "owner_dashboard_legacy_alias_index.generated.jsonl",
    "owner_dashboard_exact_panel_id_index.generated.jsonl",
    "owner_surface_contract.generated.jsonl",
    "owner_surface_projection_manifest.generated.jsonl",
    "owner_notify_transport_registry.generated.jsonl",
    "lineage.generated.jsonl",
    "dag.generated.jsonl",
    "owner_interactive_dashboard_surface.generated.jsonl",
    "owner_interactive_chart_registry.generated.jsonl",
    "owner_chart_dataset_contract.generated.jsonl",
    "owner_chart_timescale_registry.generated.jsonl",
    "owner_agent_performance_chart_view.generated.jsonl",
    "owner_portfolio_pnl_chart_view.generated.jsonl",
    "owner_research_candidate_intake_contract.generated.jsonl",
    "owner_research_candidate_chat_surface_contract.generated.jsonl",
    "owner_research_candidate_pipeline_view.generated.jsonl",
    "owner_research_candidate_evidence_route.generated.jsonl",
    "owner_research_candidate_formula_extraction_route.generated.jsonl",
    "owner_research_candidate_qku_materialization_route.generated.jsonl",
    "owner_research_candidate_replay_paper_route.generated.jsonl",
    "owner_research_candidate_promotion_route.generated.jsonl",
)

REQUIRED_JSON_OUTPUTS = (
    "read_receipt.json",
    "owner_dashboard_registry_manifest.json",
    "owner_dashboard_no_orphan.report.json",
    "owner_dashboard_authority_boundary.report.json",
    "owner_dashboard_ui_manifest.json",
    "validation_summary.report.json",
)

REQUIRED_UI_OUTPUTS = (
    "ui/owner_dashboard_review_surface.html",
    "ui/owner_dashboard_review_surface.js",
    "ui/owner_dashboard_review_surface.css",
    "ui/fixtures/owner_dashboard_demo_data.json",
)


def registry_row_ref(feature_id: str) -> str:
    return f"{REGISTRY_FILENAME}::{feature_id}"


def projection_trace(feature_id: str) -> dict[str, Any]:
    return {
        "generated_from": GENERATED_FROM,
        "manual_edit_allowed": False,
        "authoritative_source": AUTHORITATIVE_SOURCE,
        "registry_row_ref": registry_row_ref(feature_id),
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no} is not a JSON object")
        rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def repo_posix(path: Path | str) -> str:
    return str(path).replace("\\", "/")
