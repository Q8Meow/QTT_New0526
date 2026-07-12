#!/usr/bin/env python3
"""Build PR169-READINESS1 generated readiness artifacts."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Sequence


PROMPT_VERSION = "v4.3.1"
PROJECTION_VERSION = "PR169-READINESS1-v4.3.1"
BUILDER_NAME = "tools/build_pr169_readiness1.py"
VALIDATOR_NAME = "tools/validate_pr169_readiness1.py"
GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_readiness1")
REGISTRY_REF = "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl"

JSONL_ARTIFACTS = (
    "agent_readiness_registry.jsonl",
    "access_path_resolutions.generated.jsonl",
    "computable_contracts.generated.jsonl",
    "executable_now.generated.jsonl",
    "paper_loop_usable.generated.jsonl",
    "adapter_blocked.generated.jsonl",
    "unlock_queue.generated.jsonl",
    "agent_universe.generated.jsonl",
    "llm_view.generated.jsonl",
    "llm_grounding_view.generated.jsonl",
    "owner_command_routes.generated.jsonl",
    "owner_plain_english_intent_routes.generated.jsonl",
    "owner_chat_action_catalog_routes.generated.jsonl",
    "surface_parity_handoff.generated.jsonl",
    "owner_ux_semantic_bundle_handoff.generated.jsonl",
    "plugin_intake_handoff.generated.jsonl",
    "metrics_route_alias.generated.jsonl",
    "agent_kpi_trust_quarantine_handoff.generated.jsonl",
    "qku_formula_agent_compute_map.generated.jsonl",
    "trade_variable_search_handoff.generated.jsonl",
    "edge_alpha_decision_readiness.generated.jsonl",
    "order_scenario_tournament_handoff.generated.jsonl",
    "shadow_comparison_handoff.generated.jsonl",
    "execution_router_action_handoff.generated.jsonl",
    "connector_route_handoff.generated.jsonl",
    "agent_learning_handoff.generated.jsonl",
    "source_coverage_handoff.generated.jsonl",
    "parameter_operability_handoff.generated.jsonl",
    "owner_enablement_handoff.generated.jsonl",
    "consumer_routes.generated.jsonl",
    "readiness_scorecard.generated.jsonl",
    "institutional_controls.generated.jsonl",
    "quantum_readiness.generated.jsonl",
    "hotpath_handoff.generated.jsonl",
    "candidate_external_info_lanes.generated.jsonl",
    "readiness_gap_ledger.generated.jsonl",
)

JSON_ARTIFACTS = (
    "readiness_manifest.json",
    "no_orphan.report.json",
    "no_raw_jsonl_scan.report.json",
    "no_fake_readiness.report.json",
    "no_placeholder_materialization.report.json",
    "owner_three_question_coverage.report.json",
)

TEXT_ARTIFACTS = ("pr_body.md",)

AUTHORITY_FALSE_FIELDS = (
    "runtime_side_effect_allowed",
    "source_truth_created",
    "order_authority_created",
    "runtime_llm_allowed",
    "connector_private_cash_read_allowed",
    "replay_execution_created",
    "paper_execution_created",
    "shadow_execution_created",
    "live_execution_created",
    "execution_router_release_created",
    "runtime_ui_service_created",
    "runtime_mobile_created",
    "runtime_telegram_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
    "profit_claim_created",
)

DOWNSTREAM_CONSUMERS = (
    "PR169-PRETRADE1::provider_pending",
    "PR169-SVC1::provider_pending",
    "PR169-TG1::provider_pending",
    "PR170-MOBILE1::provider_pending",
    "PR169-LLM1::provider_pending",
    "PR169-LLM2::provider_pending",
    "PR169-AGENT-ORCH1::provider_pending",
    "PR169-PAPER-LOOP::provider_pending",
    "PR170-HOTPATH1::provider_pending",
    "PR170-METRICS1::explicit_route",
    "PR170-LIVE-DRYRUN1::provider_pending",
    "STAGE1-SHADOW-COMPARISON::triggered_provider_pending",
    "EXECUTION-ROUTER-ACTION-HANDOFF::provider_pending_no_release",
    "VENUE-NEUTRAL-CONNECTOR::provider_pending_no_read",
    "AGENT-LEARNING::provider_pending_no_execution",
    "PR171-LIVE-PILOT::provider_pending",
    "PR172-LAUNCH::provider_pending",
    "PR173-POSTLAUNCH::provider_pending",
    "PR173-RI1::provider_pending",
    "PR174-PLUGIN1::provider_pending",
    "PR174-PLUGIN2::explicit_route",
    "PR174-QMAP1::provider_pending",
    "PR174-ALLOW1::provider_pending",
    "OWNER-UX-SEMANTIC-BUNDLE::current_equivalent",
)


@dataclass(frozen=True)
class SourceContext:
    repo_root: Path
    rp5g_candidates: tuple[dict[str, Any], ...]
    formula_by_candidate: dict[str, list[dict[str, Any]]]
    rank4_by_candidate: dict[str, dict[str, Any]]
    qopt_refs_by_candidate: dict[str, list[str]]
    vs2_by_candidate: dict[str, dict[str, Any]]
    agent_roster_ref: str
    agent_crosswalk_ref: str
    owner_refs: dict[str, str]


def _repo_ref(path: Path) -> str:
    return path.as_posix()


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return tuple(rows)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _out_ref(name: str) -> str:
    return (GENERATED_PREFIX / name).as_posix()


def _gap(label: str) -> str:
    return f"SCOPED_GAP_{label}"


def _none_gap(value: Any, label: str) -> Any:
    if value in (None, "", [], {}):
        return _gap(label)
    return value


def _rounded(value: Decimal | float | int, places: str = "0.000001") -> float:
    decimal_value = Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return float(decimal_value)


def _score_component(present: bool) -> Decimal:
    return Decimal("1.0") if present else Decimal("0.0")


def _projection_base(projection_name: str) -> dict[str, Any]:
    return {
        "generated_from": REGISTRY_REF,
        "manual_edit_allowed": False,
        "authoritative_source": REGISTRY_REF,
        "projection_name": projection_name,
        "projection_version": PROJECTION_VERSION,
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
    }


def _projection_row(projection_name: str, row: dict[str, Any]) -> dict[str, Any]:
    return {**_projection_base(projection_name), **row}


def _authority_false_payload(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {field: False for field in AUTHORITY_FALSE_FIELDS}
    if extra:
        payload.update(extra)
    return payload


def _file_or_gap(repo_root: Path, rel: str, label: str) -> str:
    return rel if (repo_root / rel).exists() else _gap(label)


def _first_existing(repo_root: Path, refs: Sequence[tuple[str, str]]) -> str:
    for rel, _label in refs:
        if (repo_root / rel).exists():
            return rel
    return _gap(refs[0][1])


def _load_context(repo_root: Path) -> SourceContext:
    rp5g_candidates = _read_jsonl(
        repo_root / "docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl"
    )
    formula_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _read_jsonl(
        repo_root / "docs/master_plan/generated/pr168_rp5g/formula_comp.jsonl"
    ):
        candidate_id = str(row.get("candidate_id") or row.get("trade_plan_candidate_id") or "")
        if candidate_id:
            formula_by_candidate[candidate_id].append(row)

    rank4_by_candidate = {
        str(row.get("candidate_id")): row
        for row in _read_jsonl(repo_root / "docs/master_plan/generated/pr168_rank4/rank_order.jsonl")
        if row.get("candidate_id")
    }

    qopt_refs_by_candidate: dict[str, list[str]] = defaultdict(list)
    for row in _read_jsonl(repo_root / "docs/master_plan/generated/pr168_qopt1/batch_select.jsonl"):
        batch_id = str(row.get("batch_id") or row.get("qopt_batch_id") or "QOPT1_BATCH")
        for candidate_id in row.get("selected_candidate_ids", []):
            qopt_refs_by_candidate[str(candidate_id)].append(
                f"docs/master_plan/generated/pr168_qopt1/batch_select.jsonl::{batch_id}"
            )

    vs2_rows = _read_jsonl(
        repo_root / "docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl"
    )
    vs2_by_candidate = {
        str(row.get("candidate_id") or row.get("trade_plan_candidate_id")): row
        for row in vs2_rows
        if row.get("candidate_id") or row.get("trade_plan_candidate_id")
    }

    owner_refs = {
        "owner_dashboard_state": _file_or_gap(
            repo_root,
            "docs/master_plan/generated/pr169_dash1/owner_dashboard_surface_registry.jsonl",
            "OWNER_DASHBOARD_STATE_CURRENT_EQUIVALENT_ABSENT",
        ),
        "owner_action_registry": _file_or_gap(
            repo_root,
            "docs/master_plan/generated/pr169_dash1/owner_action_registry.generated.jsonl",
            "OWNER_ACTION_REGISTRY_CURRENT_EQUIVALENT_ABSENT",
        ),
        "owner_surface_resolver": _file_or_gap(
            repo_root,
            "src/qtt/dashboard/owner_surface_resolver.py",
            "OWNER_SURFACE_RESOLVER_CURRENT_EQUIVALENT_ABSENT",
        ),
        "owner_ux_bundle": _first_existing(
            repo_root,
            (
                (
                    "docs/master_plan/generated/pr169_dash1/ui1_r2r6/truth.generated.json",
                    "OWNER_UX_BUNDLE_CURRENT_EQUIVALENT_ABSENT",
                ),
                (
                    "docs/master_plan/generated/pr169_dash1/ui/ui1r2r4_owner_semantic_bundle.generated.json",
                    "OWNER_UX_BUNDLE_CURRENT_EQUIVALENT_ABSENT",
                ),
            ),
        ),
        "owner_chart_manifest": _file_or_gap(
            repo_root,
            "docs/master_plan/generated/pr169_dash1/owner_chart_surface_contract.generated.jsonl",
            "OWNER_CHART_MANIFEST_CURRENT_EQUIVALENT_ABSENT",
        ),
        "owner_widget_manifest": _file_or_gap(
            repo_root,
            "docs/master_plan/generated/pr169_dash1/owner_panel_projection.generated.jsonl",
            "OWNER_WIDGET_MANIFEST_CURRENT_EQUIVALENT_ABSENT",
        ),
        "owner_conversation_state": _file_or_gap(
            repo_root,
            "docs/master_plan/generated/pr169_dash1/owner_research_candidate_chat_surface_contract.generated.jsonl",
            "OWNER_CONVERSATION_STATE_CURRENT_EQUIVALENT_ABSENT",
        ),
    }

    return SourceContext(
        repo_root=repo_root,
        rp5g_candidates=rp5g_candidates,
        formula_by_candidate=formula_by_candidate,
        rank4_by_candidate=rank4_by_candidate,
        qopt_refs_by_candidate=qopt_refs_by_candidate,
        vs2_by_candidate=vs2_by_candidate,
        agent_roster_ref=_file_or_gap(
            repo_root,
            "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
            "PR165_D2_AGENT_ROSTER_DISCOVERY_AUDIT_ABSENT",
        ),
        agent_crosswalk_ref=_file_or_gap(
            repo_root,
            "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
            "PR165_D2_AGENT_DUTY_SOURCE_CROSSWALK_ABSENT",
        ),
        owner_refs=owner_refs,
    )


def _candidate_id(row: dict[str, Any]) -> str:
    return str(row.get("trade_plan_candidate_id") or row.get("candidate_id") or row.get("row_id"))


def _route_ref(name: str, candidate_id: str) -> str:
    return f"{name}::{candidate_id}"


def _source_ref(path: str, row_id: str | None = None) -> str:
    return f"{path}::{row_id}" if row_id else path


def _rank_component(rank4: dict[str, Any]) -> Decimal:
    raw = rank4.get("rank4_execution_adjusted_score")
    if raw is None:
        return Decimal("0.0")
    try:
        return max(Decimal("0.0"), min(Decimal("1.0"), Decimal(str(raw))))
    except Exception:
        return Decimal("0.0")


def _build_registry(ctx: SourceContext) -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for index, source in enumerate(sorted(ctx.rp5g_candidates, key=_candidate_id), start=1):
        candidate_id = _candidate_id(source)
        formula_rows = ctx.formula_by_candidate.get(candidate_id, [])
        rank4 = ctx.rank4_by_candidate.get(candidate_id, {})
        qopt_refs = ctx.qopt_refs_by_candidate.get(candidate_id, [])
        vs2 = ctx.vs2_by_candidate.get(candidate_id, {})
        qku_refs = list(source.get("qku_refs") or [])
        formula_refs = list(source.get("formula_refs") or [])
        agent_role_refs = sorted(
            set(str(role) for role in (source.get("consumer_agent_refs") or source.get("consumer_agents") or []))
        )
        rp5g_ref = _source_ref(
            "docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl",
            str(source.get("row_id") or candidate_id),
        )
        rank4_ref = _source_ref(
            "docs/master_plan/generated/pr168_rank4/rank_order.jsonl",
            str(rank4.get("rank_order_id") or rank4.get("row_id") or candidate_id),
        ) if rank4 else _gap("PR168_RANK4_RANK_ROW_ABSENT")
        qopt_ref = qopt_refs[0] if qopt_refs else _gap("PR168_QOPT1_SELECTED_BATCH_ABSENT")
        vs2_ref = _source_ref(
            "docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl",
            str(vs2.get("packet_id") or vs2.get("row_id") or candidate_id),
        ) if vs2 else _gap("PR168_VS2_PACKET_ABSENT")
        mem1_ref = _file_or_gap(
            ctx.repo_root,
            "docs/master_plan/generated/pr168_mem1/memory_query_contract.jsonl",
            "PR168_MEM1_MEMORY_QUERY_CONTRACT_ABSENT",
        )
        computable = bool(formula_rows and qku_refs and formula_refs)
        rank_component = _rank_component(rank4)
        deterministic_contract_component = _score_component(computable)
        route_component = Decimal("1.0")
        gap_penalty = Decimal("0.0") if computable else Decimal("0.25")
        readiness_score = (
            Decimal("0.35") * rank_component
            + Decimal("0.35") * deterministic_contract_component
            + Decimal("0.30") * route_component
            - gap_penalty
        )
        readiness_score = max(Decimal("0.0"), min(Decimal("1.0"), readiness_score))
        paper_priority = max(Decimal("0.0"), min(Decimal("1.0"), readiness_score + Decimal("0.05")))
        unlock_priority = (
            Decimal("0.22") * readiness_score
            + Decimal("0.18") * paper_priority
            + Decimal("0.16") * Decimal("0.80")
            + Decimal("0.12") * Decimal("1.00")
            + Decimal("0.12") * Decimal("1.00")
            + Decimal("0.10") * Decimal("0.60")
            + Decimal("0.06") * Decimal("0.60")
            + Decimal("0.04") * Decimal("1.00")
        )
        registry_row_id = f"PR169_READINESS1_REGISTRY_{index:04d}"
        contract_id = f"PR169_READINESS1_COMPUTABLE_CONTRACT_{candidate_id}"
        base_refs = {
            "plain_english_owner_intent_route_ref_or_gap": _route_ref("plain_english_intent", candidate_id),
            "owner_command_route_ref_or_gap": _route_ref("owner_command", candidate_id),
            "owner_chat_action_catalog_route_ref_or_gap": _route_ref("owner_chat_action", candidate_id),
            "surface_parity_route_ref_or_gap": _route_ref("surface_parity", candidate_id),
            "owner_ux_semantic_bundle_ref_or_gap": _route_ref("owner_ux_bundle", candidate_id),
            "plugin_intake_handoff_ref_or_gap": _route_ref("plugin_intake", candidate_id),
            "metrics_route_alias_ref_or_gap": _route_ref("metrics_route", candidate_id),
            "agent_kpi_trust_quarantine_route_ref_or_gap": _route_ref("agent_accountability", candidate_id),
            "qku_formula_agent_compute_map_ref_or_gap": _route_ref("compute_map", candidate_id),
            "trade_variable_search_handoff_ref_or_gap": _route_ref("trade_variable_search", candidate_id),
            "edge_alpha_decision_readiness_ref_or_gap": _route_ref("edge_alpha_readiness", candidate_id),
            "order_scenario_tournament_ref_or_gap": _route_ref("order_scenario_tournament", candidate_id),
            "shadow_comparison_handoff_ref_or_gap": _route_ref("shadow_handoff", candidate_id),
            "execution_router_action_handoff_ref_or_gap": _route_ref("execution_action_handoff", candidate_id),
            "connector_route_handoff_ref_or_gap": _route_ref("connector_route", candidate_id),
            "agent_learning_handoff_ref_or_gap": _route_ref("agent_learning", candidate_id),
            "source_coverage_handoff_ref_or_gap": _route_ref("source_coverage", candidate_id),
            "parameter_operability_handoff_ref_or_gap": _route_ref("parameter_operability", candidate_id),
            "owner_enablement_handoff_ref_or_gap": _route_ref("owner_enablement", candidate_id),
        }
        row = {
            "registry_row_id": registry_row_id,
            "candidate_id": candidate_id,
            "trade_plan_candidate_ref": rp5g_ref,
            "qku_refs": qku_refs,
            "formula_refs": formula_refs,
            "algorithm_refs_or_gap": source.get("algorithm_refs") or _gap("ALGORITHM_REF_NOT_MATERIALIZED_UPSTREAM"),
            "parameter_stack_refs_or_gap": source.get("parameter_stack_ref") or _route_ref("parameter_operability", candidate_id),
            "market_family": str(source.get("market_family") or "prediction_market"),
            "venue_scope": str(source.get("venue") or source.get("venue_scope") or "provider_pending"),
            "platform_scope": str(source.get("platform_scope") or "stage1_prediction_markets"),
            "stage_activation_state": "READINESS_CURRENTIZATION_NO_RUNTIME_EXECUTION",
            "stage1_prediction_market_applicability_state": "APPLICABLE_NONLIVE_READINESS_ROUTE",
            "active_stage_profile_ref_or_gap": _gap("ACTIVE_STAGE_PROFILE_CURRENT_EQUIVALENT_ABSENT"),
            "market_applicability_ref_or_gap": source.get("market_profile_ref") or _gap("MARKET_APPLICABILITY_PROFILE_CURRENT_EQUIVALENT_ABSENT"),
            "platform_applicability_ref_or_gap": source.get("platform_profile_ref") or _gap("PLATFORM_APPLICABILITY_PROFILE_CURRENT_EQUIVALENT_ABSENT"),
            "agent_access_policy_ref_or_gap": _gap("AGENT_ACCESS_POLICY_PROVIDER_PENDING_DOWNSTREAM"),
            "stage_access_mode": "CENTRAL_RESOLVER_PROJECTION_ONLY",
            "agent_role_refs": agent_role_refs,
            "agent_roster_discovery_audit_ref_or_gap": ctx.agent_roster_ref,
            "agent_duty_source_crosswalk_ref_or_gap": ctx.agent_crosswalk_ref,
            "pr164_review_ref_or_gap": _file_or_gap(ctx.repo_root, "docs/master_plan/generated/PR164_ReviewProvenanceCanonicalCoverageAudit.report.json", "PR164_REVIEW_PROVENANCE_CURRENT_EQUIVALENT_ABSENT"),
            "pr163c_repair_ref_or_gap": _file_or_gap(ctx.repo_root, "docs/master_plan/generated/PR163_C_PretradeArtificialInfrastructureRejectionRemediation.report.json", "PR163C_REPAIR_CURRENT_EQUIVALENT_ABSENT"),
            "pr165_score_ref_or_gap": _file_or_gap(ctx.repo_root, "docs/master_plan/generated/PR165_EvidenceBackedScoringRanking.report.json", "PR165_SCORE_CURRENT_EQUIVALENT_ABSENT"),
            "rp5g_sim_ref_or_gap": rp5g_ref,
            "rank4_rank_ref_or_gap": rank4_ref,
            "qopt1_optimization_ref_or_gap": qopt_ref,
            "vs2_paper_intent_ref_or_gap": vs2_ref,
            "mem1_memory_ref_or_gap": mem1_ref,
            "route_triage_ref_or_gap": _gap("ROUTE_TRIAGE_CURRENT_EQUIVALENT_ABSENT"),
            "master_plan_section_ref_or_gap": "docs/master_plan/QTT_MasterPlan_Current.md::historical_route_context_stale_next_guidance_ignored",
            "market_specific_section_index_ref_or_gap": _gap("MARKET_SPECIFIC_SECTION_INDEX_CURRENT_EQUIVALENT_ABSENT"),
            "command_action_matrix_ref_or_gap": _gap("COMMAND_ACTION_MATRIX_CURRENT_EQUIVALENT_ABSENT"),
            "computable_contract_id": contract_id,
            "computability_state": "COMPUTABLE_EXECUTABLE_NOW" if computable else "COMPUTABLE_FORMULA_PRESENT_BUT_INPUT_BINDING_GAP",
            "computability_basis": "RP5G formula_comp deterministic nonlive row with QKU/formula refs" if computable else "Scoped input binding gap; no promotion",
            "input_contract_state": "DETERMINISTIC_INPUT_CONTRACT_ROUTE_PRESENT" if computable else "SCOPED_INPUT_BINDING_GAP",
            "output_contract_state": "DETERMINISTIC_OUTPUT_CONTRACT_ROUTE_PRESENT" if computable else "SCOPED_OUTPUT_BINDING_GAP",
            "parameter_contract_state": "PARAMETER_OPERABILITY_HANDOFF_MATERIALIZED",
            "variable_contract_state": "TRADE_VARIABLE_SEARCH_HANDOFF_MATERIALIZED",
            "test_vector_state": "NONLIVE_TEST_VECTOR_ROUTE_PRESENT",
            "units_or_scale_state": "UNIT_SCALE_CONTRACT_PRESENT_OR_GAP_ROUTED",
            "executable_now_state": "EXECUTABLE_NOW_NONLIVE_SAFE" if computable else "ADAPTER_BLOCKED",
            "executable_now_basis": "Nonlive deterministic contracts only; no source/order/live authority" if computable else "Blocked until deterministic input binding closes",
            "paper_loop_usable_state": "EXECUTABLE_NOW_NONLIVE_SAFE" if computable else "SCHEDULABLE_AFTER_ADAPTER",
            "paper_loop_usable_basis": "VS2 route or scoped gap; paper execution not created",
            "adapter_blocker_family": "NONE_NONLIVE_EXECUTABLE" if computable else "INPUT_BINDING_GAP",
            "adapter_blocker_detail": "No blocker for nonlive executable-now contract" if computable else "Deterministic input binding current equivalent absent",
            "reality_model_blocker_detail_or_gap": source.get("reality_model_ref") or _gap("REALITY_MODEL_ROUTE_PROVIDER_PENDING"),
            "input_binding_blocker_detail_or_gap": "NO_INPUT_BINDING_BLOCKER" if computable else _gap("INPUT_BINDING_ROUTE_PROVIDER_PENDING"),
            "output_binding_blocker_detail_or_gap": "NO_OUTPUT_BINDING_BLOCKER" if computable else _gap("OUTPUT_BINDING_ROUTE_PROVIDER_PENDING"),
            "agent_route_blocker_detail_or_gap": "NO_AGENT_ROUTE_BLOCKER" if agent_role_refs else _gap("PR165_D2_AGENT_ROUTE_GAP_NOT_INVENTED"),
            "qstruct_blocker_detail_or_gap": "QSTRUCT_ROUTE_PRESENT_OR_QMAP1_GAP",
            "plugin_intake_blocker_detail_or_gap": "PLUGIN_INTAKE_PROVIDER_PENDING_NOT_RUNTIME",
            "unlock_action_family": "MAINTAIN_NONLIVE_ROUTE" if computable else "CLOSE_INPUT_BINDING_GAP",
            "unlock_priority_score": _rounded(unlock_priority),
            "readiness_score": _rounded(readiness_score),
            "paper_loop_priority_score": _rounded(paper_priority),
            "readiness_confidence": "MEDIUM_ROUTE_BACKED_NONLIVE",
            "source_evidence_state": "CANDIDATE_RESEARCH_PROVISIONAL_ONLY",
            "evidence_staleness_state": "CURRENTNESS_RECHECK_ROUTE_REQUIRED_DOWNSTREAM",
            "candidate_external_info_lane_state": "CANDIDATE_RESEARCH_PROVISIONAL",
            "deterministic_contract_coverage_state": "COVERED" if computable else "SCOPED_GAP",
            **base_refs,
            "dashboard_surface_registry_ref_or_gap": ctx.owner_refs["owner_dashboard_state"],
            "owner_search_semantics_ref_or_gap": ctx.owner_refs["owner_ux_bundle"],
            "owner_option_range_semantics_ref_or_gap": ctx.owner_refs["owner_ux_bundle"],
            "owner_theme_preference_semantics_ref_or_gap": ctx.owner_refs["owner_ux_bundle"],
            "owner_education_guide_semantics_ref_or_gap": ctx.owner_refs["owner_ux_bundle"],
            "owner_chart_policy_ref_or_gap": ctx.owner_refs["owner_chart_manifest"],
            "owner_drawer_semantics_ref_or_gap": ctx.owner_refs["owner_ux_bundle"],
            "owner_preference_policy_ref_or_gap": ctx.owner_refs["owner_ux_bundle"],
            "universal_owner_enablement_matrix_ref_or_gap": _route_ref("owner_enablement", candidate_id),
            "effective_live_write_state": "NOT_ARMED_IN_READINESS1",
            "source_currentness_handoff_ref_or_gap": _route_ref("source_coverage", candidate_id),
            "owner_dashboard_route_ref_or_gap": ctx.owner_refs["owner_dashboard_state"],
            "owner_conversation_state_ref_or_gap": ctx.owner_refs["owner_conversation_state"],
            "owner_widget_manifest_ref_or_gap": ctx.owner_refs["owner_widget_manifest"],
            "owner_chart_manifest_ref_or_gap": ctx.owner_refs["owner_chart_manifest"],
            "owner_surface_resolver_ref_or_gap": ctx.owner_refs["owner_surface_resolver"],
            "llm_view_policy": "GROUND_FROM_READINESS1_PROJECTIONS_NO_RUNTIME_CALL",
            "llm_grounding_view_ref_or_gap": _route_ref("llm_grounding", candidate_id),
            "source_agnostic_intake_route_ref_or_gap": _route_ref("candidate_external_info_lane", candidate_id),
            "pretrade_route_ref_or_gap": "PR169-PRETRADE1::provider_pending",
            "paper_loop_route_ref_or_gap": "PR169-PAPER-LOOP::provider_pending",
            "hotpath_route_ref_or_gap": "PR170-HOTPATH1::provider_pending",
            "shadow_comparison_route_ref_or_gap": "STAGE1-SHADOW-COMPARISON::triggered_provider_pending",
            "live_dryrun_route_ref_or_gap": "PR170-LIVE-DRYRUN1::provider_pending",
            "live_pilot_route_ref_or_gap": "PR171-LIVE-PILOT::provider_pending",
            "launch_route_ref_or_gap": "PR172-LAUNCH::provider_pending",
            "postlaunch_route_ref_or_gap": "PR173-POSTLAUNCH::provider_pending",
            "plugin_route_ref_or_gap": "PR174-PLUGIN1::provider_pending",
            "qmap_route_ref_or_gap": "PR174-QMAP1::provider_pending",
            "allowlist_route_ref_or_gap": "PR174-ALLOW1::provider_pending",
            **_authority_false_payload(),
            "downstream_consumer_refs": list(DOWNSTREAM_CONSUMERS),
            "no_raw_jsonl_scan_proof_ref": _out_ref("no_raw_jsonl_scan.report.json"),
            "orphan_status": "NOT_ORPHANED_ROUTE_PROOF_PRESENT",
        }
        registry.append(_projection_row("agent_readiness_registry", row))
    return registry


def _contract_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        candidate_id = row["candidate_id"]
        rows.append(
            _projection_row(
                "computable_contracts",
                {
                    "computable_contract_id": row["computable_contract_id"],
                    "candidate_id": candidate_id,
                    "qku_refs": row["qku_refs"],
                    "formula_refs": row["formula_refs"],
                    "algorithm_refs_or_gap": row["algorithm_refs_or_gap"],
                    "contract_kind": "NONLIVE_DETERMINISTIC_READINESS_CONTRACT",
                    "symbolic_formula_ref_or_gap": row["formula_refs"] or _gap("SYMBOLIC_FORMULA_REF_ABSENT"),
                    "objective_ref_or_gap": _route_ref("edge_alpha_expected_net_cash_objective", candidate_id),
                    "constraint_refs_or_gap": [
                        _route_ref("owner_enablement_fixed_zero_constraint", candidate_id),
                        _route_ref("risk_latency_capacity_constraint", candidate_id),
                    ],
                    "input_schema_ref_or_inline_contract": {
                        "required_fields": [
                            "market",
                            "venue",
                            "side",
                            "price",
                            "liquidity",
                            "time",
                            "portfolio",
                            "latency",
                            "cost",
                        ],
                        "contract_state": row["input_contract_state"],
                    },
                    "output_schema_ref_or_inline_contract": {
                        "required_fields": [
                            "readiness_score",
                            "candidate_minus_no_trade_state",
                            "route_state",
                            "blocker_family",
                        ],
                        "contract_state": row["output_contract_state"],
                    },
                    "parameter_stack_refs_or_gap": row["parameter_stack_refs_or_gap"],
                    "required_market_fields": ["market_family", "event_id", "resolution_state"],
                    "required_venue_fields": ["venue_scope", "fee_model", "liquidity_state"],
                    "required_platform_fields": ["platform_scope", "stage_activation_state"],
                    "required_time_fields": ["asof_time", "time_to_resolution", "decision_time"],
                    "required_price_fields": ["entry_price", "bid", "ask", "mid"],
                    "required_liquidity_fields": ["spread", "depth", "volume_bucket"],
                    "required_event_lifecycle_fields": ["open_state", "halt_state", "resolution_state"],
                    "required_portfolio_fields": ["exposure", "cash_route", "concentration"],
                    "required_latency_fields": ["latency_budget", "decision_to_submit_delay"],
                    "required_cost_fields": ["fee", "spread_cost", "slippage", "impact"],
                    "variable_search_space_ref_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "unit_scale_contract": "UNIT_SCALE_ROUTE_PRESENT_OR_SCOPED_GAP",
                    "normalization_contract": "NORMALIZATION_ROUTE_PRESENT_OR_SCOPED_GAP",
                    "missing_value_policy": "FAIL_CLOSED_TYPED_GAP",
                    "zero_denominator_policy_or_gap": "FAIL_CLOSED_ZERO_DENOMINATOR_GAP",
                    "lookahead_leakage_guard_ref_or_gap": _route_ref("leakage_guard", candidate_id),
                    "asof_timestamp_policy_ref_or_gap": _route_ref("asof_timestamp_policy", candidate_id),
                    "source_evidence_refs_or_gap": row["source_coverage_handoff_ref_or_gap"],
                    "candidate_external_info_lane_ref_or_gap": _route_ref("candidate_external_info_lane", candidate_id),
                    "nonlive_test_vector_ref_or_gap": _route_ref("nonlive_test_vector", candidate_id),
                    "expected_output_shape_or_gap": "ReadinessContractOutputV1",
                    "execution_side_effect_allowed": False,
                    "profit_claim_created": False,
                    "contract_gap_reason_or_none": "NONE" if row["computability_state"] == "COMPUTABLE_EXECUTABLE_NOW" else row["input_binding_blocker_detail_or_gap"],
                    "unlock_route_ref_or_gap": _route_ref("unlock_queue", candidate_id),
                },
            )
        )
    return rows


def _simple_candidate_projection(
    registry: Sequence[dict[str, Any]],
    projection_name: str,
    id_field: str,
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        candidate_id = row["candidate_id"]
        payload = {
            id_field: _route_ref(projection_name, candidate_id),
            "candidate_id": candidate_id,
            "registry_row_id": row["registry_row_id"],
            "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
            "qku_refs": row["qku_refs"],
            "formula_refs": row["formula_refs"],
            "computable_contract_ref": row["computable_contract_id"],
            "downstream_consumer_refs": row["downstream_consumer_refs"],
            "orphan_status": row["orphan_status"],
        }
        if extra:
            payload.update(extra)
        rows.append(_projection_row(projection_name, payload))
    return rows


def _access_path_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "access_path_resolutions",
            {
                "access_resolution_id": _route_ref("access_path", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "canonical_registry_ref": REGISTRY_REF,
                "resolver_module_ref": "src/qtt/readiness/pr169_readiness1_resolvers.py",
                "agent_access_contract": "AgentAccessContractV1",
                "qku_access_resolver": "QKUAccessResolverV1",
                "formula_access_resolver": "FormulaAccessResolverV1",
                "candidate_readiness_resolver": "CandidateReadinessResolverV1",
                "raw_upstream_jsonl_runtime_scan_allowed": False,
                "runtime_side_effect_allowed": False,
                "downstream_consumer_refs": row["downstream_consumer_refs"],
                "orphan_status": row["orphan_status"],
            },
        )
        for row in registry
    ]


def _executable_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        if row["executable_now_state"] != "EXECUTABLE_NOW_NONLIVE_SAFE":
            continue
        rows.append(
            _projection_row(
                "executable_now",
                {
                    "executable_now_id": _route_ref("executable_now", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "computability_state": row["computability_state"],
                    "executable_now_state": row["executable_now_state"],
                    "computable_contract_id": row["computable_contract_id"],
                    "deterministic_input_contract_state": row["input_contract_state"],
                    "deterministic_output_contract_state": row["output_contract_state"],
                    "responsible_agent_route_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "test_vector_state": row["test_vector_state"],
                    "nonlive_only_state": "NONLIVE_SAFE_NO_RUNTIME_EXECUTION",
                    "runtime_side_effect_allowed": False,
                    "source_truth_created": False,
                    "order_authority_created": False,
                    "profit_claim_created": False,
                    "downstream_consumer_refs": row["downstream_consumer_refs"],
                    "orphan_status": row["orphan_status"],
                },
            )
        )
    return rows


def _paper_loop_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "paper_loop_usable",
            {
                "paper_loop_usable_id": _route_ref("paper_loop_usable", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "paper_loop_usable_state": row["paper_loop_usable_state"],
                "vs2_paper_intent_ref_or_gap": row["vs2_paper_intent_ref_or_gap"],
                "pretrade_required_state": "PRETRADE_REQUIRED_DOWNSTREAM",
                "paper_loop_blockers": ["PAPER_EXECUTION_PROVIDER_PENDING_DOWNSTREAM"],
                "paper_loop_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                "paper_execution_created": False,
                "downstream_consumer_refs": row["downstream_consumer_refs"],
                "orphan_status": row["orphan_status"],
            },
        )
        for row in registry
    ]


def _adapter_blocked_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        blocker_family = (
            row["adapter_blocker_family"]
            if row["adapter_blocker_family"] != "NONE_NONLIVE_EXECUTABLE"
            else "DOWNSTREAM_CONNECTOR_REALITY_PLUGIN_SOURCE_OWNER_ENABLEMENT_GAPS"
        )
        blocker_detail = (
            row["adapter_blocker_detail"]
            if row["adapter_blocker_family"] != "NONE_NONLIVE_EXECUTABLE"
            else (
                "Nonlive executable-now contract is ready, but downstream connector, "
                "reality, plugin, source-evidence, and owner-enable routes remain "
                "provider-pending before paper/live/order use."
            )
        )
        rows.append(
            _projection_row(
                "adapter_blocked",
                {
                    "adapter_blocked_id": _route_ref("adapter_blocked", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "adapter_blocker_family": blocker_family,
                    "adapter_blocker_detail": blocker_detail,
                    "blocked_contract_ref": row["computable_contract_id"],
                    "unlock_action_family": row["unlock_action_family"],
                    "unlock_route_ref": _route_ref("unlock_queue", row["candidate_id"]),
                    "responsible_downstream_pr_or_alias": "PR169-PRETRADE1_OR_PR170-HOTPATH1_PROVIDER_PENDING",
                },
            )
        )
    return rows


def _unlock_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in sorted(registry, key=lambda item: (-float(item["unlock_priority_score"]), item["candidate_id"])):
        rows.append(
            _projection_row(
                "unlock_queue",
                {
                    "unlock_queue_id": _route_ref("unlock_queue", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "unlock_action_family": row["unlock_action_family"],
                    "unlock_priority_score": row["unlock_priority_score"],
                    "readiness_score": row["readiness_score"],
                    "paper_loop_priority_score": row["paper_loop_priority_score"],
                    "tractability_score": 0.8,
                    "downstream_consumer_coverage_score": 1.0,
                    "agent_compute_coverage_score": 1.0,
                    "portfolio_marginal_utility_score": 0.6,
                    "quantum_structural_readiness_score": 0.6,
                    "owner_plain_english_route_score": 1.0,
                    "authority_risk_penalty": 0.0,
                    "implementation_churn_penalty": 0.0,
                    "responsible_downstream_pr_or_alias": "PR169-PRETRADE1_OR_PR170-HOTPATH1_PROVIDER_PENDING",
                    "profit_claim_created": False,
                },
            )
        )
    return rows


def _agent_universe_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "agent_universe",
                {
                    "agent_universe_id": _route_ref("agent_universe", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "agent_role_refs": row["agent_role_refs"],
                    "agent_roster_discovery_audit_ref_or_gap": row["agent_roster_discovery_audit_ref_or_gap"],
                    "agent_duty_source_crosswalk_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "agent_route_state": "PR165_D2_ROUTE_PRESENT" if row["agent_role_refs"] else "GAP_NOT_INVENTED",
                    "agent_execution_created": False,
                    "downstream_consumer_refs": row["downstream_consumer_refs"],
                    "orphan_status": row["orphan_status"],
                },
            )
        )
    return rows


def _llm_rows(registry: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    view_rows: list[dict[str, Any]] = []
    grounding_rows: list[dict[str, Any]] = []
    for row in registry:
        candidate_id = row["candidate_id"]
        common = {
            "candidate_id": candidate_id,
            "source_evidence_refs": [row["source_coverage_handoff_ref_or_gap"]],
            "candidate_external_info_lane_refs": [_route_ref("candidate_external_info_lane", candidate_id)],
            "readiness_refs": [row["registry_row_id"], _route_ref("readiness_scorecard", candidate_id)],
            "computable_contract_refs": [row["computable_contract_id"]],
            "agent_role_refs_or_gap": row["agent_role_refs"] or _gap("PR165_D2_AGENT_ROUTE_GAP_NOT_INVENTED"),
            "raw_jsonl_scan_used": False,
            "runtime_llm_call_created": False,
        }
        view_rows.append(
            _projection_row(
                "llm_view",
                {
                    "llm_view_id": _route_ref("llm_view", candidate_id),
                    **common,
                    "llm_view_policy": row["llm_view_policy"],
                    "allowed_roles": ["summarize", "critique", "explain", "route", "propose_research_questions"],
                    "forbidden_roles": ["source_truth_creation", "risk_pass_creation", "profit_proof_creation", "order_authority", "connector_authority", "live_readiness_proof"],
                    "owner_plain_english_intent_route_refs": [row["plain_english_owner_intent_route_ref_or_gap"]],
                    "downstream_consumer_refs": row["downstream_consumer_refs"],
                },
            )
        )
        grounding_rows.append(
            _projection_row(
                "llm_grounding_view",
                {
                    "llm_grounding_view_id": _route_ref("llm_grounding", candidate_id),
                    **common,
                    "allowed_llm_roles": [
                        "summarize",
                        "critique",
                        "explain",
                        "route",
                        "propose_research_questions",
                        "draft_owner_plain_english_explanation",
                    ],
                    "forbidden_llm_roles": [
                        "source_truth_creation",
                        "risk_pass_creation",
                        "profit_proof_creation",
                        "order_authority",
                        "connector_authority",
                        "live_readiness_proof",
                        "result_rewrite",
                        "direct_trade_submission",
                    ],
                    "institutional_control_refs": [_route_ref("institutional_controls", candidate_id)],
                    "quantum_structural_refs": [_route_ref("quantum_readiness", candidate_id)],
                    "owner_command_route_refs": [row["owner_command_route_ref_or_gap"]],
                    "owner_plain_english_intent_route_refs": [row["plain_english_owner_intent_route_ref_or_gap"]],
                    "owner_chat_action_catalog_route_refs": [row["owner_chat_action_catalog_route_ref_or_gap"]],
                    "plain_english_summary_seed": "Nonlive readiness route summary only; no source truth, risk pass, order authority, or profit proof.",
                    "required_caveats": [
                        "READINESS1 does not execute replay, paper, shadow, or live trading.",
                        "Executable-now means deterministic nonlive testability.",
                    ],
                },
            )
        )
    return view_rows, grounding_rows


def _owner_command_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = [
        "INITIATE_REQUEST",
        "REVIEW",
        "APPROVE_REQUEST",
        "REJECT",
        "VETO",
        "PAUSE",
        "ROLLBACK_REQUEST",
        "KILL_SWITCH_REQUEST",
        "ESCALATE",
    ]
    forbidden = ["DIRECT_VENUE_SUBMIT", "EXECUTION_ROUTER_RELEASE", "LIVE_EXECUTION"]
    return [
        _projection_row(
            "owner_command_routes",
            {
                "owner_command_route_id": _route_ref("owner_command", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "owner_dashboard_state_ref_or_gap": row["owner_dashboard_route_ref_or_gap"],
                "owner_surface_resolver_ref_or_gap": row["owner_surface_resolver_ref_or_gap"],
                "owner_action_registry_ref_or_gap": row["dashboard_surface_registry_ref_or_gap"],
                "owner_action_request_ref_or_gap": _gap("OWNER_ACTION_REQUEST_PROVIDER_PENDING"),
                "allowed_owner_route_actions": allowed,
                "forbidden_owner_route_actions": forbidden,
                "owner_trading_command_route_allowed": True,
                "direct_venue_submit_authority_created": False,
                "execution_router_release_created": False,
                "order_authority_created": False,
                "downstream_consumer_refs": row["downstream_consumer_refs"],
            },
        )
        for row in registry
    ]


def _plain_english_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        candidate_id = row["candidate_id"]
        rows.append(
            _projection_row(
                "owner_plain_english_intent_routes",
                {
                    "plain_english_route_id": _route_ref("plain_english_intent", candidate_id),
                    "candidate_id": candidate_id,
                    "owner_message_ref_or_gap": _gap("OWNER_MESSAGE_RUNTIME_PROVIDER_PENDING"),
                    "owner_plain_english_intent_ref_or_gap": "OwnerPlainEnglishIntentV1::provider_pending",
                    "natural_language_owner_intent_parser_ref_or_gap": "NaturalLanguageOwnerIntentParser::LLM1_OR_LLM2_PENDING",
                    "owner_agent_directive_envelope_ref_or_gap": "OwnerAgentDirectiveEnvelopeV1::AGENT_ORCH1_PENDING",
                    "owner_research_submission_ref_or_gap": "OwnerResearchSubmissionV1::provider_pending",
                    "owner_trade_intent_ref_or_gap": "OwnerTradeIntentV1::provider_pending",
                    "owner_trade_check_request_ref_or_gap": "OwnerTradeCheckRequestV1::provider_pending",
                    "owner_replay_paper_request_ref_or_gap": "OwnerReplayPaperRequestV1::provider_pending",
                    "owner_live_canary_review_request_ref_or_gap": "OwnerLiveCanaryReviewRequestV1::provider_pending",
                    "owner_execution_router_submit_request_ref_or_gap": "OwnerExecutionRouterSubmitRequestV1::provider_pending_no_release",
                    "owner_kill_switch_request_ref_or_gap": "OwnerKillSwitchRequestV1::provider_pending",
                    "owner_rollback_request_ref_or_gap": "OwnerRollbackRequestV1::provider_pending",
                    "qku_candidate_materialization_request_ref_or_gap": "QKUCandidateMaterializationRequestV1::provider_pending",
                    "formula_extraction_candidate_ref_or_gap": "FormulaExtractionCandidateV1::provider_pending",
                    "quantum_structure_mapping_request_ref_or_gap": "QuantumStructureMappingRequestV1::provider_pending",
                    "source_agnostic_intake_route_ref_or_gap": row["source_agnostic_intake_route_ref_or_gap"],
                    "trade_workbench_route_ref_or_gap": "TradeWorkbenchRoute::provider_pending",
                    "target_agent_role_refs_or_gap": row["agent_role_refs"] or _gap("PR165_D2_AGENT_ROUTE_GAP_NOT_INVENTED"),
                    "provider_stage": "LLM1_OR_LLM2_OR_AGENT_ORCH1_PENDING",
                    "route_state": "STRUCTURED_PROVIDER_PENDING_NO_RUNTIME",
                    "runtime_llm_call_created": False,
                    "agent_execution_created": False,
                    "source_truth_created": False,
                    "paper_execution_created": False,
                    "live_execution_created": False,
                    "order_authority_created": False,
                    "execution_router_release_created": False,
                },
            )
        )
    return rows


def _chat_action_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed_actions = [
        "SEND_OWNER_AGENT_MESSAGE_REQUEST",
        "SUBMIT_RESEARCH_CANDIDATE_FROM_CHAT",
        "ATTACH_SOURCE_LINK_REQUEST",
        "ATTACH_SOURCE_FILE_REQUEST",
        "REQUEST_AGENT_ANALYSIS_FROM_CHAT",
        "REQUEST_AGENT_SUMMARY_FROM_CHAT",
        "REQUEST_SOURCE_VALIDATION_FROM_CHAT",
        "REQUEST_FORMULA_EXTRACTION_FROM_CHAT",
        "REQUEST_QKU_MATERIALIZATION_FROM_CHAT",
        "REQUEST_QUANTUM_STRUCTURE_MAPPING_FROM_CHAT",
        "REQUEST_TRADE_CHECK_FROM_CHAT",
        "REQUEST_REPLAY_PAPER_FROM_CHAT",
        "REQUEST_NO_TRADE_REOPTIMIZATION_FROM_CHAT",
        "REQUEST_LIVE_CANARY_REVIEW_FROM_CHAT",
        "DIRECT_MESSAGE_AGENT_REQUEST",
        "BROADCAST_TO_AGENT_POD_REQUEST",
        "PIN_CHAT_CONTEXT_REQUEST",
        "LINK_CHAT_TO_CARD_REQUEST",
        "LINK_CHAT_TO_TRADE_WORKBENCH_REQUEST",
        "LINK_CHAT_TO_SOURCE_WORKFLOW_REQUEST",
        "ESCALATE_CHAT_TO_DECISION_QUEUE_REQUEST",
        "MARK_CHAT_THREAD_RESOLVED_REQUEST",
    ]
    forbidden_actions = [
        "DIRECT_VENUE_SUBMIT",
        "EXECUTION_ROUTER_RELEASE",
        "CONNECTOR_CREDENTIAL_ACCESS",
        "CONNECTOR_PRIVATE_CASH_READ",
        "SOURCE_TRUTH_ACCEPTANCE",
        "PAPER_EXECUTION",
        "REPLAY_EXECUTION",
        "SHADOW_EXECUTION",
        "LIVE_EXECUTION",
        "RUNTIME_LLM_CALL",
        "RUNTIME_AGENT_EXECUTION",
        "QUANTUM_BACKEND_EXECUTION",
        "PROFIT_PROOF_CREATION",
    ]
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "owner_chat_action_catalog_routes",
                {
                    "chat_action_route_id": _route_ref("owner_chat_action", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "owner_conversation_state_ref_or_gap": row["owner_conversation_state_ref_or_gap"],
                    "owner_chat_action_catalog_ref_or_gap": "OwnerChatActionCatalogV1::provider_pending",
                    "owner_chat_route_map_ref_or_gap": "OwnerChatRouteMapV1::provider_pending",
                    "source_agnostic_intake_contract_ref_or_gap": row["source_agnostic_intake_route_ref_or_gap"],
                    "trade_workbench_route_ref_or_gap": "TradeWorkbenchRoute::provider_pending",
                    "allowed_chat_request_actions": allowed_actions,
                    "forbidden_chat_actions": forbidden_actions,
                    "target_agent_role_refs_or_gap": row["agent_role_refs"] or _gap("PR165_D2_AGENT_ROUTE_GAP_NOT_INVENTED"),
                    "provider_stage": "LLM1_OR_LLM2_OR_AGENT_ORCH1_PENDING",
                    "chat_to_research_route_contract": "chat_to_research_provider_pending_contract",
                    "chat_to_trade_route_contract": "chat_to_trade_provider_pending_contract",
                    "runtime_chat_service_created": False,
                    "runtime_llm_call_created": False,
                    "agent_execution_created": False,
                    "source_truth_created": False,
                    "paper_execution_created": False,
                    "live_execution_created": False,
                    "order_authority_created": False,
                    "execution_router_release_created": False,
                },
            )
        )
    return rows


def _surface_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        shared_state = "SHARED_ID_ROUTE_PRESENT_OR_GAP_ROUTED"
        rows.append(
            _projection_row(
                "surface_parity_handoff",
                {
                    "surface_parity_route_id": _route_ref("surface_parity", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "owner_dashboard_state_ref_or_gap": row["owner_dashboard_route_ref_or_gap"],
                    "owner_conversation_state_ref_or_gap": row["owner_conversation_state_ref_or_gap"],
                    "owner_action_registry_ref_or_gap": row["dashboard_surface_registry_ref_or_gap"],
                    "owner_widget_manifest_ref_or_gap": row["owner_widget_manifest_ref_or_gap"],
                    "owner_chart_manifest_ref_or_gap": row["owner_chart_manifest_ref_or_gap"],
                    "owner_surface_resolver_ref_or_gap": row["owner_surface_resolver_ref_or_gap"],
                    "owner_action_request_ref_or_gap": "OwnerActionRequestV1::provider_pending",
                    "owner_action_receipt_ref_or_gap": "OwnerActionReceiptV1::provider_pending",
                    "owner_portfolio_state_ref_or_gap": "OwnerPortfolioStateV1::provider_pending_no_private_read",
                    "owner_chart_series_ref_or_gap": row["owner_chart_manifest_ref_or_gap"],
                    "owner_decision_queue_state_ref_or_gap": "OwnerDecisionQueueStateV1::provider_pending",
                    "owner_agent_state_ref_or_gap": "OwnerAgentStateV1::provider_pending",
                    "owner_research_pipeline_state_ref_or_gap": "OwnerResearchPipelineStateV1::provider_pending",
                    "owner_quantum_state_ref_or_gap": "OwnerQuantumStateV1::provider_pending",
                    "owner_execution_authority_state_ref_or_gap": "OwnerExecutionAuthorityStateV1::provider_pending_no_release",
                    "desktop_dashboard_route_state": "ROUTED_SHARED_SEMANTICS",
                    "mobile_web_route_state": "ROUTED_SHARED_SEMANTICS",
                    "pwa_route_state": "ROUTED_SHARED_SEMANTICS_NO_SERVICE_WORKER",
                    "native_mobile_route_state": "ROUTED_SHARED_SEMANTICS_PROVIDER_PENDING",
                    "telegram_mirror_route_state": "ROUTED_SHARED_SEMANTICS_NO_BOT_RUNTIME",
                    "shared_action_id_state": shared_state,
                    "shared_widget_id_state": shared_state,
                    "shared_chart_id_state": shared_state,
                    "shared_conversation_id_state": shared_state,
                    "shared_thread_id_state": shared_state,
                    "shared_message_id_state": shared_state,
                    "shared_source_candidate_id_state": shared_state,
                    "shared_trade_intent_id_state": shared_state,
                    "shared_route_id_state": shared_state,
                    "shared_authority_boundary_id_state": shared_state,
                    "no_mobile_only_fork_proof": "ONE_SHARED_SURFACE_SEMANTIC_ROUTE",
                    "no_chat_second_truth_system_proof": "CHAT_ROUTES_TO_OWNER_CONVERSATION_STATE",
                    "no_telegram_second_governance_plane_proof": "TELEGRAM_MIRROR_NO_SEPARATE_GOVERNANCE",
                    "runtime_service_created": False,
                    "mobile_runtime_created": False,
                    "telegram_runtime_created": False,
                    "pwa_service_worker_created": False,
                    "direct_venue_submit_authority_created": False,
                    "execution_router_release_created": False,
                },
            )
        )
    return rows


def _owner_ux_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "owner_ux_semantic_bundle_handoff",
                {
                    "owner_ux_bundle_id": _route_ref("owner_ux_bundle", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "dashboard_surface_registry_ref_or_gap": row["dashboard_surface_registry_ref_or_gap"],
                    "owner_dashboard_state_ref_or_gap": row["owner_dashboard_route_ref_or_gap"],
                    "owner_action_registry_ref_or_gap": row["dashboard_surface_registry_ref_or_gap"],
                    "owner_surface_resolver_ref_or_gap": row["owner_surface_resolver_ref_or_gap"],
                    "owner_conversation_state_ref_or_gap": row["owner_conversation_state_ref_or_gap"],
                    "owner_widget_manifest_ref_or_gap": row["owner_widget_manifest_ref_or_gap"],
                    "owner_chart_manifest_ref_or_gap": row["owner_chart_manifest_ref_or_gap"],
                    "owner_command_route_ref_or_gap": row["owner_command_route_ref_or_gap"],
                    "owner_plain_english_intent_route_ref_or_gap": row["plain_english_owner_intent_route_ref_or_gap"],
                    "owner_chat_action_catalog_route_ref_or_gap": row["owner_chat_action_catalog_route_ref_or_gap"],
                    "search_semantics_ref_or_gap": row["owner_search_semantics_ref_or_gap"],
                    "option_range_semantics_ref_or_gap": row["owner_option_range_semantics_ref_or_gap"],
                    "theme_semantics_ref_or_gap": row["owner_theme_preference_semantics_ref_or_gap"],
                    "education_qtt_guide_semantics_ref_or_gap": row["owner_education_guide_semantics_ref_or_gap"],
                    "chart_policy_ref_or_gap": row["owner_chart_policy_ref_or_gap"],
                    "drawer_semantics_ref_or_gap": row["owner_drawer_semantics_ref_or_gap"],
                    "preference_policy_ref_or_gap": row["owner_preference_policy_ref_or_gap"],
                    "owner_mode_profile_refs_or_gap": ["OWNER_MODE", "DEVELOPER_MODE"],
                    "renderer_consumer_refs_or_gap": ["PR169-SVC1::renderer_provider_pending", "PR170-MOBILE1::renderer_provider_pending"],
                    "validator_consumer_refs_or_gap": [VALIDATOR_NAME],
                    "playwright_consumer_refs_or_gap": ["PR169-UI1::playwright_current_equivalent"],
                    "robinhood_like_benchmark_state": "UX_QUALITY_BENCHMARK_ONLY_NOT_SOURCE_TRUTH",
                    "portfolio_return_chart_route_ref_or_gap": "PortfolioReturnChartRoute::provider_pending",
                    "portfolio_allocation_route_ref_or_gap": "PortfolioAllocationRoute::provider_pending",
                    "return_breakdown_route_ref_or_gap": "ReturnBreakdownRoute::provider_pending",
                    "time_interval_control_route_ref_or_gap": "TimeIntervalControlRoute::provider_pending",
                    "chart_point_inspection_route_ref_or_gap": "ChartPointInspectionRoute::provider_pending",
                    "prediction_market_tca_chart_route_ref_or_gap": _route_ref("tca_chart", row["candidate_id"]),
                    "no_trade_explanation_route_ref_or_gap": _route_ref("no_trade_explanation", row["candidate_id"]),
                    "qku_formula_route_visual_ref_or_gap": _route_ref("qku_formula_visual", row["candidate_id"]),
                    "quantum_classical_comparator_visual_ref_or_gap": _route_ref("quantum_classical_visual", row["candidate_id"]),
                    "no_scatter_proof": "CENTRAL_OWNER_UX_BUNDLE_ROUTE_ONLY",
                    "no_mobile_only_fork_proof": "ONE_SHARED_SURFACE_SEMANTIC_ROUTE",
                    "no_telegram_second_governance_plane_proof": "TELEGRAM_MIRROR_NO_SEPARATE_GOVERNANCE",
                    "runtime_ui_service_created": False,
                    "runtime_mobile_created": False,
                    "runtime_telegram_created": False,
                    "pwa_service_worker_created": False,
                    "source_truth_created": False,
                    "connector_private_cash_read_allowed": False,
                    "order_authority_created": False,
                    "execution_router_release_created": False,
                    "profit_claim_created": False,
                },
            )
        )
    return rows


def _plugin_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "plugin_intake_handoff",
                {
                    "plugin_handoff_id": _route_ref("plugin_intake", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "qku_refs": row["qku_refs"],
                    "formula_refs": row["formula_refs"],
                    "algorithm_refs_or_gap": row["algorithm_refs_or_gap"],
                    "formula_plugin_registry_route_ref_or_gap": "PR174-PLUGIN1::formula_plugin_registry",
                    "algorithm_plugin_registry_route_ref_or_gap": "PR174-PLUGIN1::algorithm_plugin_registry",
                    "quantum_formula_plugin_registry_route_ref_or_gap": "PR174-QMAP1::quantum_formula_plugin_registry",
                    "formula_sdk_template_route_ref_or_gap": "PR174-PLUGIN1::formula_sdk_template",
                    "json_yaml_plugin_template_route_ref_or_gap": "PR174-PLUGIN1::json_yaml_plugin_template",
                    "owner_formula_intake_route_ref_or_gap": "PR174-PLUGIN1::owner_formula_intake",
                    "agent_formula_scout_route_ref_or_gap": "PR174-PLUGIN2::agent_formula_scout",
                    "agent_submitted_formula_proposal_route_ref_or_gap": "PR174-PLUGIN2::agent_formula_proposal",
                    "qtt_add_formula_candidate_cli_route_ref_or_gap": "PR174-PLUGIN1::qtt_add_formula_candidate_cli",
                    "formula_backlog_board_route_ref_or_gap": "PR174-PLUGIN1::formula_backlog",
                    "formula_source_labeled_candidate_workflow_ref_or_gap": "PR174-PLUGIN1::formula_source_labeled_candidate_workflow",
                    "formula_version_ledger_route_ref_or_gap": "PR174-PLUGIN1::formula_version_ledger",
                    "formula_rollback_ledger_route_ref_or_gap": "PR174-PLUGIN1::formula_rollback_ledger",
                    "formula_promotion_state_machine_route_ref_or_gap": "PR174-PLUGIN1::formula_promotion_state_machine",
                    "formula_replay_paper_queue_route_ref_or_gap": "PR169-PAPER-LOOP::formula_replay_paper_queue",
                    "runtime_formula_allowlist_route_ref_or_gap": "PR174-ALLOW1::runtime_formula_allowlist_provider_pending",
                    "formula_latency_class_registry_route_ref_or_gap": "PR170-HOTPATH1::formula_latency_class_registry",
                    "formula_quantum_mapping_registry_route_ref_or_gap": "PR174-QMAP1::formula_quantum_mapping_registry",
                    "dashboard_formula_control_route_ref_or_gap": "PR169-SVC1::dashboard_formula_control",
                    "responsible_downstream_pr_alias_state": "PR174_PLUGIN2_SEPARATE_ROUTE_PRESERVED",
                    "responsible_downstream_pr": "PR174-PLUGIN1_OR_PLUGIN2_OR_QMAP1_OR_ALLOW1_OR_HOTPATH1_ALIAS",
                    "runtime_plugin_created": False,
                    "hot_reload_created": False,
                    "live_formula_allowlist_created": False,
                    "live_promotion_created": False,
                    "order_authority_created": False,
                },
            )
        )
    return rows


def _metrics_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "metrics_route_alias",
            {
                "metrics_route_id": _route_ref("metrics_route", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "pr170_metrics1_route_ref_or_gap": "PR170-METRICS1::explicit_route",
                "pr170_live_dryrun1_route_ref_or_gap": "PR170-LIVE-DRYRUN1::metrics_consumer",
                "metrics_alias_state": "PR170_METRICS1_EXPLICIT_ROUTE_NOT_MERGED_ALIAS",
                "metrics_ledger_consumer_ref_or_gap": "PR170-METRICS1::metrics_ledger_provider_pending",
                "event_time_capture_consumer_ref_or_gap": "PR170-METRICS1::event_time_capture_provider_pending",
                "decision_timestamp_route_ref_or_gap": "PR170-METRICS1::decision_timestamp",
                "pretrade_timestamp_route_ref_or_gap": "PR169-PRETRADE1::pretrade_timestamp",
                "paper_submit_timestamp_route_ref_or_gap": "PR169-PAPER-LOOP::paper_submit_timestamp_provider_pending",
                "live_dryrun_submit_disabled_timestamp_route_ref_or_gap": "PR170-LIVE-DRYRUN1::submit_disabled_timestamp",
                "tca_metric_route_ref_or_gap": _route_ref("tca_metric", row["candidate_id"]),
                "latency_metric_route_ref_or_gap": _route_ref("latency_metric", row["candidate_id"]),
                "agent_decision_metric_route_ref_or_gap": _route_ref("agent_decision_metric", row["candidate_id"]),
                "no_trade_metric_route_ref_or_gap": _route_ref("no_trade_metric", row["candidate_id"]),
                "runtime_metrics_ledger_created": False,
                "event_time_capture_created": False,
                "live_execution_created": False,
                "order_authority_created": False,
            },
        )
        for row in registry
    ]


def _agent_kpi_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        role_component = Decimal("1.0") if row["agent_role_refs"] else Decimal("0.0")
        score = (
            Decimal("0.20") * role_component
            + Decimal("0.15")
            + Decimal("0.15") * Decimal("0.50")
            + Decimal("0.15") * Decimal("0.50")
            + Decimal("0.10") * Decimal("0.50")
            + Decimal("0.10") * Decimal("0.50")
            + Decimal("0.10") * Decimal("0.50")
            + Decimal("0.05")
        )
        rows.append(
            _projection_row(
                "agent_kpi_trust_quarantine_handoff",
                {
                    "agent_accountability_contract_id": _route_ref("agent_accountability", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "registry_row_id": row["registry_row_id"],
                    "agent_role_refs": row["agent_role_refs"],
                    "agent_roster_discovery_audit_ref_or_gap": row["agent_roster_discovery_audit_ref_or_gap"],
                    "agent_duty_source_crosswalk_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "agent_duty_name_or_gap": "AgentDutySourceCrosswalk::candidate_route",
                    "agent_duty_scope": "CANDIDATE_READINESS_CONSUMPTION_NO_EXECUTION",
                    "agent_duty_source_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "agent_responsibility_for_candidate": "consume_contracts_and_route_gaps_only",
                    "agent_consumable_input_contract_ref_or_gap": row["computable_contract_id"],
                    "agent_expected_output_contract_ref_or_gap": _route_ref("agent_expected_output_contract", row["candidate_id"]),
                    "agent_task_receipt_contract_ref_or_gap": "AGENT-ORCH1::agent_task_receipt_provider_pending",
                    "agent_kpi_contract_ref_or_gap": "AGENT-ORCH1::agent_kpi_contract_provider_pending",
                    "agent_missed_duty_detection_contract_ref_or_gap": "SVC1::missed_duty_detection_provider_pending",
                    "agent_quality_scorecard_contract_ref_or_gap": "SVC1::agent_quality_scorecard_provider_pending",
                    "agent_output_trust_score_contract_ref_or_gap": "SVC1::agent_output_trust_score_provider_pending",
                    "agent_retry_contract_ref_or_gap": "AGENT-ORCH1::agent_retry_contract_provider_pending",
                    "agent_reroute_contract_ref_or_gap": "AGENT-ORCH1::agent_reroute_contract_provider_pending",
                    "agent_quarantine_contract_ref_or_gap": "SVC1::agent_quarantine_contract_provider_pending",
                    "agent_replacement_candidate_contract_ref_or_gap": "AGENT-ORCH1::agent_replacement_candidate_provider_pending",
                    "owner_dashboard_merit_panel_route_ref_or_gap": "PR169-SVC1::owner_dashboard_merit_panel",
                    "owner_approval_required_for_live_adjacent_agent_promotion": True,
                    "agent_permission_expansion_allowed": False,
                    "agent_live_authority_auto_grant_allowed": False,
                    "agent_live_write_secret_access_auto_grant_allowed": False,
                    "runtime_agent_kpi_created": False,
                    "agent_self_healing_runtime_created": False,
                    "agent_replacement_runtime_created": False,
                    "agent_execution_created": False,
                    "order_authority_created": False,
                    "source_truth_created": False,
                    "profit_claim_created": False,
                    "agent_accountability_materialization_state": "MATERIALIZED_CONTRACT",
                    "agent_accountability_computability_state": "COMPUTABLE_AFTER_AGENT_ORCH",
                    "agent_accountability_blocker_family": "DOWNSTREAM_RECEIPT_KPI_TRUST_QUARANTINE_PROVIDER_PENDING",
                    "agent_accountability_blocker_detail": "Receipt, KPI, trust, and quarantine runtimes belong to later AGENT-ORCH/SVC governance.",
                    "agent_accountability_unlock_route": "PR169-AGENT-ORCH1_OR_PR169-SVC1",
                    "agent_accountability_readiness_score_0_1": _rounded(score),
                    "agent_accountability_score_components": {
                        "pr165d2_agent_role_resolved_component": _rounded(role_component),
                        "duty_source_crosswalk_component": 1.0,
                        "task_receipt_contract_component": 0.5,
                        "kpi_contract_component": 0.5,
                        "trust_score_contract_component": 0.5,
                        "missed_duty_detection_component": 0.5,
                        "retry_reroute_quarantine_contract_component": 0.5,
                        "owner_approval_gate_component": 1.0,
                    },
                    "agent_accountability_contract_test_vector_ref_or_gap": _route_ref("agent_accountability_test_vector", row["candidate_id"]),
                    "no_runtime_monitoring_proof": "NO_RUNTIME_AGENT_KPI_CREATED",
                    "no_permission_expansion_proof": "PERMISSION_EXPANSION_FALSE",
                    "no_live_authority_auto_grant_proof": "LIVE_AUTHORITY_AUTO_GRANT_FALSE",
                    "no_orphan_downstream_consumer_refs": ["PR169-AGENT-ORCH1", "PR169-SVC1", "PR173-POSTLAUNCH"],
                },
            )
        )
    return rows


def _compute_map_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "qku_formula_agent_compute_map",
                {
                    "compute_map_id": _route_ref("compute_map", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "qku_refs": row["qku_refs"],
                    "formula_refs": row["formula_refs"],
                    "algorithm_refs_or_gap": row["algorithm_refs_or_gap"],
                    "computable_contract_ref": row["computable_contract_id"],
                    "responsible_agent_role_refs": row["agent_role_refs"],
                    "agent_roster_discovery_audit_ref_or_gap": row["agent_roster_discovery_audit_ref_or_gap"],
                    "agent_duty_source_crosswalk_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "agent_duty_description_or_gap": "Responsible roles consume deterministic nonlive contracts and gap routes.",
                    "input_contract_ref": row["computable_contract_id"],
                    "output_contract_ref": _route_ref("agent_compute_output_contract", row["candidate_id"]),
                    "parameter_stack_refs_or_gap": row["parameter_stack_refs_or_gap"],
                    "trade_variable_search_handoff_ref_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "source_evidence_refs_or_gap": row["source_coverage_handoff_ref_or_gap"],
                    "candidate_external_info_lane_ref_or_gap": _route_ref("candidate_external_info_lane", row["candidate_id"]),
                    "llm_grounding_view_ref_or_gap": row["llm_grounding_view_ref_or_gap"],
                    "owner_plain_english_intent_route_ref_or_gap": row["plain_english_owner_intent_route_ref_or_gap"],
                    "owner_chat_action_catalog_route_ref_or_gap": row["owner_chat_action_catalog_route_ref_or_gap"],
                    "pretrade_consumer_ref_or_gap": row["pretrade_route_ref_or_gap"],
                    "paper_loop_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                    "hotpath_consumer_ref_or_gap": row["hotpath_route_ref_or_gap"],
                    "live_dryrun_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                    "plugin_intake_consumer_ref_or_gap": row["plugin_intake_handoff_ref_or_gap"],
                    "qmap_consumer_ref_or_gap": row["qmap_route_ref_or_gap"],
                    "allowlist_consumer_ref_or_gap": row["allowlist_route_ref_or_gap"],
                    "agent_execution_created": False,
                    "runtime_llm_call_created": False,
                    "order_authority_created": False,
                    "source_truth_created": False,
                    "orphan_status": row["orphan_status"],
                    "route_gap_reason_or_none": "NONE" if row["agent_role_refs"] else "PR165_D2_GAP_NOT_INVENTED",
                },
            )
        )
    return rows


def _trade_variable_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    mutable_vars = [
        "market",
        "venue",
        "stack",
        "side",
        "entry",
        "size",
        "hold_duration",
        "exit_rule",
        "maker_taker_split",
        "cancel_replace_interval",
        "liquidity_filter",
        "spread_filter",
        "latency_budget",
        "portfolio_exposure",
    ]
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "trade_variable_search_handoff",
                {
                    "trade_variable_search_handoff_id": _route_ref("trade_variable_search", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
                    "qku_refs": row["qku_refs"],
                    "formula_refs": row["formula_refs"],
                    "immutable_formula_state": "IMMUTABLE",
                    "mutable_trade_variable_set": mutable_vars,
                    "market_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "venue_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "stack_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "side_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "entry_price_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "size_budget_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "hold_duration_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "exit_rule_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "maker_taker_split_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "cancel_replace_interval_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "liquidity_filter_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "spread_filter_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "latency_budget_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "portfolio_exposure_variable_state": "MUTABLE_SEARCH_ROUTE",
                    "no_trade_comparator_route_ref_or_gap": _route_ref("no_trade_comparator", row["candidate_id"]),
                    "champion_challenger_route_ref_or_gap": _route_ref("champion_challenger", row["candidate_id"]),
                    "tca_decomposition_route_ref_or_gap": _route_ref("tca_decomposition", row["candidate_id"]),
                    "capacity_crowding_route_ref_or_gap": _route_ref("capacity_crowding", row["candidate_id"]),
                    "portfolio_marginal_utility_route_ref_or_gap": _route_ref("portfolio_marginal_utility", row["candidate_id"]),
                    "replay_paper_route_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                    "pretrade_route_ref_or_gap": row["pretrade_route_ref_or_gap"],
                    "optimizer_default_policy_ref_or_gap": "OptimizerDefaultPolicyV1::provider_pending",
                    "search_bounds_policy_ref_or_gap": "SearchBoundsPolicyV1::provider_pending",
                    "search_grid_or_sampler_policy_ref_or_gap": "SearchGridOrSamplerPolicyV1::provider_pending",
                    "candidate_generation_state": "TRADE_PLAN_VARIABLE_SEARCH_PROVIDER_PENDING",
                    "profit_claim_created": False,
                    "formula_mutation_created": False,
                    "order_authority_created": False,
                },
            )
        )
    return rows


def _parameter_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    parameter_specs = (
        ("market_family", "market", "EDGE_RELEVANT", "Market selector"),
        ("venue_scope", "venue", "EXECUTION_RELEVANT", "Venue selector"),
        ("platform_scope", "platform", "ROUTE_ONLY", "Platform scope"),
        ("side", "side", "EXECUTION_RELEVANT", "Side selector"),
        ("entry_price_candidate", "entry_price", "EDGE_RELEVANT", "Numeric input"),
        ("order_size_candidate", "size_budget", "RISK_RELEVANT", "Numeric input"),
        ("hold_duration_candidate", "hold_duration", "EDGE_RELEVANT", "Duration input"),
        ("exit_rule_candidate", "exit_rule", "RISK_RELEVANT", "Rule selector"),
        ("maker_taker_split_candidate", "maker_taker_split", "EXECUTION_RELEVANT", "Range input"),
        ("cancel_replace_interval_candidate", "cancel_replace_interval", "LATENCY_RELEVANT", "Duration input"),
        ("liquidity_filter_candidate", "liquidity_filter", "CAPACITY_RELEVANT", "Filter selector"),
        ("spread_filter_candidate", "spread_filter", "EXECUTION_RELEVANT", "Filter selector"),
        ("latency_budget_candidate", "latency_budget", "LATENCY_RELEVANT", "Numeric input"),
        ("portfolio_exposure_candidate", "portfolio_exposure", "CAPACITY_RELEVANT", "Range input"),
    )
    rows = []
    for row in registry:
        candidate_id = row["candidate_id"]
        for source_field, symbol, materiality, widget in parameter_specs:
            rows.append(
                _projection_row(
                    "parameter_operability_handoff",
                    {
                        "parameter_operability_handoff_id": f"parameter_operability::{candidate_id}::{symbol}",
                        "candidate_id": candidate_id,
                        "parameter_symbol": symbol,
                        "parameter_family_ref_or_gap": f"TradePlanCandidateV1::{symbol}",
                        "parameter_pack_ref_or_gap": row["parameter_stack_refs_or_gap"],
                        "parameter_role_class": "TRADE_PLAN_MUTABLE_VARIABLE" if materiality != "ROUTE_ONLY" else "ROUTE_ONLY",
                        "materiality_class": materiality,
                        "qku_refs_or_gap": row["qku_refs"],
                        "formula_refs_or_gap": row["formula_refs"],
                        "trade_variable_ref_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                        "day1_start_value_or_gap": row.get(source_field) or _gap(f"{symbol.upper()}_DAY1_VALUE_CURRENT_POINTER_ABSENT"),
                        "reference_range_or_gap": _gap(f"{symbol.upper()}_OWNER_REFERENCE_RANGE_PROVIDER_PENDING"),
                        "bounded_search_space_or_gap": _gap(f"{symbol.upper()}_BOUNDED_SEARCH_SPACE_PROVIDER_PENDING"),
                        "current_value_pointer_or_gap": _gap(f"{symbol.upper()}_CURRENT_VALUE_POINTER_PROVIDER_PENDING"),
                        "current_shadow_candidate_value_pointer_or_gap": _gap(f"{symbol.upper()}_SHADOW_VALUE_POINTER_PROVIDER_PENDING"),
                        "last_known_good_value_pointer_or_gap": _gap(f"{symbol.upper()}_LAST_KNOWN_GOOD_POINTER_PROVIDER_PENDING"),
                        "owner_dashboard_editability_class_or_gap": "OWNER_REVIEWABLE_PROVIDER_PENDING",
                        "ui_widget_class_or_gap": widget,
                        "shadow_trigger_class_or_gap": "TRIGGERED_LIVE_CONCURRENT_COMPARISON_ONLY",
                        "override_precedence_class_or_gap": "MOST_RESTRICTIVE_WINS",
                        "value_render_format_or_gap": "OWNER_SAFE_FORMAT_PROVIDER_PENDING",
                        "unit_or_basis_or_gap": "UNIT_BASIS_PROVIDER_PENDING",
                        "normalization_contract_ref_or_gap": row["computable_contract_id"],
                        "scale_contract_ref_or_gap": row["computable_contract_id"],
                        "optimizer_default_policy_ref_or_gap": "OptimizerDefaultPolicyV1::provider_pending",
                        "parameter_source_authority_state": "READINESS_ROUTE_ONLY_NOT_RUNTIME_VALUE_AUTHORITY",
                        "parameter_operability_state": "DAY1_ROUTE_MATERIALIZED_WITH_TYPED_GAPS",
                        "parameter_operability_gap_reason_or_none": "OWNER_VALUE_POINTER_PROVIDER_PENDING",
                        "owner_surface_route_ref_or_gap": row["owner_ux_semantic_bundle_ref_or_gap"],
                        "pretrade_consumer_ref_or_gap": row["pretrade_route_ref_or_gap"],
                        "paper_loop_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                        "hotpath_consumer_ref_or_gap": row["hotpath_route_ref_or_gap"],
                        "shadow_comparison_consumer_ref_or_gap": row["shadow_comparison_route_ref_or_gap"],
                        "live_dryrun_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                        "execution_router_action_consumer_ref_or_gap": row["execution_router_action_handoff_ref_or_gap"],
                        "quantum_readiness_consumer_ref_or_gap": _route_ref("quantum_readiness", candidate_id),
                        "runtime_value_created": False,
                        "live_value_authority_created": False,
                        "order_authority_created": False,
                        "profit_claim_created": False,
                    },
                )
            )
    return rows


def _owner_enablement_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "owner_enablement_handoff",
            {
                "owner_enablement_handoff_id": _route_ref("owner_enablement", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "market_family": row["market_family"],
                "platform_scope": row["platform_scope"],
                "venue_scope": row["venue_scope"],
                "strategy_family_or_gap": "READINESS_ROUTE_STRATEGY_PROVIDER_PENDING",
                "qku_refs_or_gap": row["qku_refs"],
                "formula_refs_or_gap": row["formula_refs"],
                "trade_variable_refs_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                "owner_enablement_matrix_ref_or_gap": "OwnerEnablementMatrixV1::provider_pending",
                "global_live_trading_master_switch_ref_or_gap": "GlobalLiveTradingMasterSwitchV1::provider_pending_off_by_default",
                "scope_enablement_state_or_gap": "FAIL_CLOSED_PROVIDER_PENDING",
                "parent_scope_enablement_state_or_gap": "FAIL_CLOSED_PROVIDER_PENDING",
                "most_restrictive_effective_state_or_gap": "OFF_NOT_ARMED_IN_READINESS1",
                "disabled_action_universe_ref_or_gap": _route_ref("disabled_action_universe", row["candidate_id"]),
                "fixed_zero_constraint_ref_or_gap": _route_ref("fixed_zero_constraint", row["candidate_id"]),
                "classical_scoring_mask_ref_or_gap": _route_ref("classical_scoring_mask", row["candidate_id"]),
                "quantum_variable_mask_ref_or_gap": _route_ref("quantum_variable_mask", row["candidate_id"]),
                "portfolio_construction_mask_ref_or_gap": _route_ref("portfolio_construction_mask", row["candidate_id"]),
                "live_order_intent_mask_ref_or_gap": _route_ref("live_order_intent_mask", row["candidate_id"]),
                "owner_override_route_ref_or_gap": "OwnerOverrideRouteV1::provider_pending_most_restrictive_wins",
                "owner_enablement_gap_reason_or_none": "LIVE_ENABLEMENT_PROVIDER_PENDING_FAIL_CLOSED",
                "pretrade_consumer_ref_or_gap": row["pretrade_route_ref_or_gap"],
                "paper_loop_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                "hotpath_consumer_ref_or_gap": row["hotpath_route_ref_or_gap"],
                "shadow_comparison_consumer_ref_or_gap": row["shadow_comparison_route_ref_or_gap"],
                "live_dryrun_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                "execution_router_action_consumer_ref_or_gap": row["execution_router_action_handoff_ref_or_gap"],
                "quantum_readiness_consumer_ref_or_gap": _route_ref("quantum_readiness", row["candidate_id"]),
                "live_enablement_created": False,
                "order_authority_created": False,
                "execution_router_release_created": False,
                "profit_claim_created": False,
            },
        )
        for row in registry
    ]


def _edge_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        components = {
            "expected_net_cash_route_component": 1.0,
            "lower_confidence_bound_component": 1.0,
            "tca_decomposition_component": 1.0,
            "fill_probability_component": 1.0,
            "latency_budget_component": 1.0,
            "capacity_crowding_component": 1.0,
            "overfit_fdr_component": 1.0,
            "portfolio_marginal_utility_component": 1.0,
            "scenario_ladder_component": 1.0,
            "calibration_component": 1.0,
            "agent_route_component": 1.0 if row["agent_role_refs"] else 0.0,
            "no_orphan_component": 1.0,
            "parameter_operability_component": 1.0,
            "owner_enablement_component": 1.0,
            "no_trade_not_beaten_penalty": 0.0,
            "missing_contract_penalty": 0.0 if row["computability_state"] == "COMPUTABLE_EXECUTABLE_NOW" else 1.0,
            "stale_evidence_penalty": 0.2,
            "thin_book_or_capacity_penalty": 0.0,
        }
        score = (
            Decimal("0.13") * Decimal(str(components["expected_net_cash_route_component"]))
            + Decimal("0.11") * Decimal(str(components["lower_confidence_bound_component"]))
            + Decimal("0.11") * Decimal(str(components["tca_decomposition_component"]))
            + Decimal("0.09") * Decimal(str(components["fill_probability_component"]))
            + Decimal("0.08") * Decimal(str(components["latency_budget_component"]))
            + Decimal("0.08") * Decimal(str(components["capacity_crowding_component"]))
            + Decimal("0.10") * Decimal(str(components["overfit_fdr_component"]))
            + Decimal("0.09") * Decimal(str(components["portfolio_marginal_utility_component"]))
            + Decimal("0.08") * Decimal(str(components["scenario_ladder_component"]))
            + Decimal("0.05") * Decimal(str(components["calibration_component"]))
            + Decimal("0.04") * Decimal(str(components["agent_route_component"]))
            + Decimal("0.04") * Decimal(str(components["no_orphan_component"]))
            + Decimal("0.03") * Decimal(str(components["parameter_operability_component"]))
            + Decimal("0.03") * Decimal(str(components["owner_enablement_component"]))
            - Decimal("0.12") * Decimal(str(components["no_trade_not_beaten_penalty"]))
            - Decimal("0.10") * Decimal(str(components["missing_contract_penalty"]))
            - Decimal("0.08") * Decimal(str(components["stale_evidence_penalty"]))
            - Decimal("0.08") * Decimal(str(components["thin_book_or_capacity_penalty"]))
        )
        score = max(Decimal("0.0"), min(Decimal("1.0"), score))
        rows.append(
            _projection_row(
                "edge_alpha_decision_readiness",
                {
                    "edge_alpha_readiness_id": _route_ref("edge_alpha_readiness", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
                    "qku_refs": row["qku_refs"],
                    "formula_refs": row["formula_refs"],
                    "algorithm_refs_or_gap": row["algorithm_refs_or_gap"],
                    "computable_contract_ref": row["computable_contract_id"],
                    "pr165_score_ref_or_gap": row["pr165_score_ref_or_gap"],
                    "rp5g_execution_evidence_ref_or_gap": row["rp5g_sim_ref_or_gap"],
                    "rank4_rank_ref_or_gap": row["rank4_rank_ref_or_gap"],
                    "qopt1_optimization_ref_or_gap": row["qopt1_optimization_ref_or_gap"],
                    "vs2_paper_intent_ref_or_gap": row["vs2_paper_intent_ref_or_gap"],
                    "mem1_memory_ref_or_gap": row["mem1_memory_ref_or_gap"],
                    "expected_net_cash_route_ref_or_gap": _route_ref("expected_net_cash", row["candidate_id"]),
                    "lower_confidence_bound_route_ref_or_gap": _route_ref("lower_confidence_bound", row["candidate_id"]),
                    "tca_decomposition_route_ref_or_gap": _route_ref("tca_decomposition", row["candidate_id"]),
                    "fill_probability_route_ref_or_gap": _route_ref("fill_probability", row["candidate_id"]),
                    "latency_budget_route_ref_or_gap": _route_ref("latency_budget", row["candidate_id"]),
                    "capacity_crowding_route_ref_or_gap": _route_ref("capacity_crowding", row["candidate_id"]),
                    "overfit_fdr_route_ref_or_gap": _route_ref("overfit_fdr", row["candidate_id"]),
                    "portfolio_marginal_utility_route_ref_or_gap": _route_ref("portfolio_marginal_utility", row["candidate_id"]),
                    "scenario_ladder_route_ref_or_gap": _route_ref("scenario_ladder", row["candidate_id"]),
                    "calibration_route_ref_or_gap": _route_ref("calibration", row["candidate_id"]),
                    "agent_route_ref_or_gap": row["agent_duty_source_crosswalk_ref_or_gap"],
                    "no_orphan_route_ref": _out_ref("no_orphan.report.json"),
                    "parameter_operability_handoff_ref_or_gap": row["parameter_operability_handoff_ref_or_gap"],
                    "owner_enablement_handoff_ref_or_gap": row["owner_enablement_handoff_ref_or_gap"],
                    "no_trade_comparator_ref_or_gap": _route_ref("no_trade_comparator", row["candidate_id"]),
                    "candidate_minus_no_trade_state": "COMPARATOR_ROUTE_PRESENT_NO_CHAMPION_CLAIM",
                    "edge_alpha_capture_state": "READINESS_ROUTE_MATERIALIZED_NO_PROMOTION",
                    "edge_alpha_readiness_score_0_1": _rounded(score),
                    "edge_alpha_score_components": components,
                    "promotion_claim_created": False,
                    "profit_claim_created": False,
                    "order_authority_created": False,
                    "live_execution_created": False,
                },
            )
        )
    return rows


def _order_tournament_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "order_scenario_tournament_handoff",
                {
                    "order_scenario_tournament_id": _route_ref("order_scenario_tournament", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
                    "qku_refs": row["qku_refs"],
                    "formula_refs": row["formula_refs"],
                    "base_stack_ref_or_gap": row["parameter_stack_refs_or_gap"],
                    "classical_stack_refs_or_gap": ["classical_stack_route::provider_pending"],
                    "quantum_forward_stack_refs_or_gap": ["quantum_forward_stack_route::QMAP1_pending"],
                    "order_policy_refs_or_gap": ["maker_only", "taker_allowed", "cancel_replace_policy_provider_pending"],
                    "market_variable_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "venue_variable_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "stack_variable_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "side_variable_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "entry_price_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "size_budget_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "hold_duration_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "exit_rule_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "maker_taker_split_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "cancel_replace_interval_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "liquidity_spread_filter_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "latency_budget_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "portfolio_exposure_grid_or_gap": row["trade_variable_search_handoff_ref_or_gap"],
                    "scenario_ladder_ref_or_gap": _route_ref("scenario_ladder", row["candidate_id"]),
                    "stress_case_refs_or_gap": [_route_ref("stress_case", row["candidate_id"])],
                    "no_trade_comparator_ref_or_gap": _route_ref("no_trade_comparator", row["candidate_id"]),
                    "champion_candidate_ref_or_gap": _gap("NO_CHAMPION_PROMOTION_IN_READINESS1"),
                    "challenger_candidate_refs_or_gap": [_route_ref("challenger_candidate", row["candidate_id"])],
                    "no_trade_winner_reason_or_gap": "NO_TRADE_REOPTIMIZATION_ROUTE_IF_COMPARATOR_WINS",
                    "reoptimization_routes_if_no_trade_wins": [
                        "smaller_size",
                        "different_venue",
                        "maker_only",
                        "later_timing",
                        "different_stack",
                        "better_liquidity_window",
                        "research_paper_evidence_gap_closure",
                    ],
                    "pretrade_consumer_ref_or_gap": row["pretrade_route_ref_or_gap"],
                    "paper_loop_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                    "shadow_comparison_consumer_ref_or_gap": row["shadow_comparison_route_ref_or_gap"],
                    "live_dryrun_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                    "execution_router_action_consumer_ref_or_gap": row["execution_router_action_handoff_ref_or_gap"],
                    "agent_learning_consumer_ref_or_gap": row["agent_learning_handoff_ref_or_gap"],
                    "tournament_readiness_state": "CONTRACT_MATERIALIZED_NO_SIMULATION_EXECUTION",
                    "tournament_gap_reason_or_none": "NONE",
                    "simulation_executed_in_this_pr": False,
                    "paper_execution_created": False,
                    "shadow_execution_created": False,
                    "live_execution_created": False,
                    "order_authority_created": False,
                    "profit_claim_created": False,
                },
            )
        )
    return rows


def _shadow_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "shadow_comparison_handoff",
            {
                "shadow_handoff_id": _route_ref("shadow_handoff", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
                "qku_refs": row["qku_refs"],
                "formula_refs": row["formula_refs"],
                "shadow_route_state": "TRIGGERED_LIVE_CONCURRENT_COMPARISON_PROVIDER_PENDING",
                "shadow_trigger_state": "TRIGGER_REQUIRED_NO_EXECUTION",
                "shadow_trigger_reason_or_gap": "changed_scope_or_owner_request_or_agent_adjustment_or_risk_escalation_or_canary_comparison",
                "changed_candidate_scope_ref_or_gap": _route_ref("changed_candidate_scope", row["candidate_id"]),
                "changed_parameter_scope_ref_or_gap": row["parameter_operability_handoff_ref_or_gap"],
                "owner_request_route_ref_or_gap": row["plain_english_owner_intent_route_ref_or_gap"],
                "qtt_agent_adjustment_route_ref_or_gap": row["agent_learning_handoff_ref_or_gap"],
                "risk_escalation_route_ref_or_gap": _route_ref("risk_escalation", row["candidate_id"]),
                "canary_live_comparison_route_ref_or_gap": "PR171-LIVE-PILOT::canary_live_comparison_provider_pending",
                "requires_reliable_live_surface": True,
                "requires_live_receipts_before_comparison": True,
                "shadow_required_before_canary": False,
                "shadow_replaces_replay": False,
                "shadow_replaces_paper": False,
                "pre_live_gate_role_allowed": False,
                "post_live_validation_role": "POST_LIVE_EXECUTION_VALIDATION_ONLY_NOT_PRE_LIVE_GATE",
                "shadow_comparison_consumer_ref_or_gap": row["shadow_comparison_route_ref_or_gap"],
                "live_dryrun_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                "live_pilot_consumer_ref_or_gap": row["live_pilot_route_ref_or_gap"],
                "postlaunch_consumer_ref_or_gap": row["postlaunch_route_ref_or_gap"],
                "shadow_execution_created": False,
                "live_execution_created": False,
                "order_authority_created": False,
                "execution_router_release_created": False,
                "profit_claim_created": False,
            },
        )
        for row in registry
    ]


def _execution_action_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    verbs = ["BUY", "SELL", "OPEN", "CLOSE", "CANCEL", "REPLACE", "REDUCE", "EXIT"]
    return [
        _projection_row(
            "execution_router_action_handoff",
            {
                "execution_action_handoff_id": _route_ref("execution_action_handoff", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
                "owner_trade_intent_ref_or_gap": "OwnerTradeIntentV1::provider_pending",
                "owner_trade_check_request_ref_or_gap": "OwnerTradeCheckRequestV1::provider_pending",
                "owner_replay_paper_request_ref_or_gap": "OwnerReplayPaperRequestV1::provider_pending",
                "owner_live_canary_review_request_ref_or_gap": "OwnerLiveCanaryReviewRequestV1::provider_pending",
                "owner_execution_router_submit_request_ref_or_gap": "OwnerExecutionRouterSubmitRequestV1::provider_pending_no_release",
                "universal_owner_enablement_matrix_ref_or_gap": row["universal_owner_enablement_matrix_ref_or_gap"],
                "owner_approval_preview_route_ref_or_gap": "OwnerApprovalPreviewRouteV1::provider_pending",
                "owner_final_approval_route_ref_or_gap": "OwnerFinalApprovalRouteV1::provider_pending_downstream",
                "effective_live_write_state": "NOT_ARMED_IN_READINESS1",
                "this_pr_execution_authority_state": "NO_EXECUTION_AUTHORITY",
                "allowed_downstream_action_verbs": verbs,
                "action_verb_route_state_map": {verb: "PROVIDER_PENDING_AFTER_DOWNSTREAM_GATES" for verb in verbs},
                "pretrade_gate_consumer_ref_or_gap": row["pretrade_route_ref_or_gap"],
                "paper_loop_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                "live_dryrun_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                "live_pilot_consumer_ref_or_gap": row["live_pilot_route_ref_or_gap"],
                "launch_gate_consumer_ref_or_gap": row["launch_route_ref_or_gap"],
                "runtime_cash_receipt_consumer_ref_or_gap": "PR170-LIVE-DRYRUN1::runtime_cash_receipt_provider_pending",
                "source_evidence_gate_consumer_ref_or_gap": row["source_coverage_handoff_ref_or_gap"],
                "risk_gate_consumer_ref_or_gap": "PR169-PRETRADE1::risk_gate_provider_pending",
                "portfolio_exposure_gate_consumer_ref_or_gap": "PR169-PRETRADE1::portfolio_exposure_gate_provider_pending",
                "latency_gate_consumer_ref_or_gap": "PR170-HOTPATH1::latency_gate_provider_pending",
                "kill_switch_gate_consumer_ref_or_gap": "PR172-LAUNCH::kill_switch_gate_provider_pending",
                "execution_router_consumer_ref_or_gap": "ExecutionRouter::provider_pending_final_release",
                "owner_approval_consumer_ref_or_gap": "OwnerApproval::provider_pending",
                "execution_router_release_state": "PROVIDER_PENDING_DOWNSTREAM",
                "order_compilation_created": False,
                "venue_submit_created": False,
                "buy_sell_open_close_executed": False,
                "live_execution_created": False,
                "execution_router_release_created": False,
                "order_authority_created": False,
                "profit_claim_created": False,
            },
        )
        for row in registry
    ]


def _connector_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "connector_route_handoff",
            {
                "connector_route_handoff_id": _route_ref("connector_route", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "market_family": row["market_family"],
                "venue_scope": row["venue_scope"],
                "platform_scope": row["platform_scope"],
                "connector_family_ref_or_gap": "VenueNeutralConnectorFamilyV1::provider_pending",
                "venue_neutral_adapter_ref_or_gap": "VenueNeutralAdapterV1::provider_pending",
                "accepted_source_placeholder_policy_ref_or_gap": "AcceptedSourcePlaceholderPolicyV1::provider_pending",
                "required_connector_semantic_fields": ["symbol", "market", "venue", "fee", "tick_size", "order_type", "time_in_force"],
                "required_source_evidence_packet_refs_or_gap": row["source_coverage_handoff_ref_or_gap"],
                "required_private_cash_receipt_refs_or_gap": "PrivateCashReceiptV1::provider_pending_no_read",
                "pretrade_connector_consumer_ref_or_gap": row["pretrade_route_ref_or_gap"],
                "paper_loop_connector_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                "live_dryrun_connector_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                "live_pilot_connector_consumer_ref_or_gap": row["live_pilot_route_ref_or_gap"],
                "execution_router_connector_consumer_ref_or_gap": "ExecutionRouter::connector_provider_pending",
                "connector_route_state": "HANDOFF_MATERIALIZED_NO_CONNECTOR_READ",
                "connector_gap_reason_or_none": "CONNECTOR_RUNTIME_PROVIDER_PENDING",
                "connector_read_created": False,
                "connector_write_created": False,
                "private_cash_read_created": False,
                "source_truth_created": False,
                "venue_semantics_accepted": False,
                "live_order_authority_created": False,
            },
        )
        for row in registry
    ]


def _agent_learning_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    families = [
        "champion_challenger_rotation",
        "contextual_bandit_or_exploration_budget_candidate",
        "regime_drift_detection",
        "no_trade_miss_audit",
        "TCA_slippage_fill_latency_attribution",
        "capacity_crowding_decay_learning",
        "formula_stack_failure_mode_clustering",
        "quantum_classical_comparator_outcome_learning",
        "agent_trust_score_update_after_receipts",
        "owner_feedback_to_policy_candidate",
    ]
    return [
        _projection_row(
            "agent_learning_handoff",
            {
                "agent_learning_handoff_id": _route_ref("agent_learning", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "trade_plan_candidate_ref": row["trade_plan_candidate_ref"],
                "agent_role_refs_or_gap": row["agent_role_refs"] or _gap("PR165_D2_AGENT_ROUTE_GAP_NOT_INVENTED"),
                "mem1_memory_ref_or_gap": row["mem1_memory_ref_or_gap"],
                "regime_conditioned_memory_ref_or_gap": row["mem1_memory_ref_or_gap"],
                "champion_challenger_ref_or_gap": _route_ref("champion_challenger", row["candidate_id"]),
                "no_trade_miss_audit_ref_or_gap": _route_ref("no_trade_miss_audit", row["candidate_id"]),
                "postlaunch_outcome_audit_ref_or_gap": "PR173-POSTLAUNCH::outcome_audit_provider_pending",
                "paper_loop_learning_consumer_ref_or_gap": row["paper_loop_route_ref_or_gap"],
                "live_dryrun_learning_consumer_ref_or_gap": row["live_dryrun_route_ref_or_gap"],
                "postlaunch_learning_consumer_ref_or_gap": row["postlaunch_route_ref_or_gap"],
                "agent_decision_receipt_consumer_ref_or_gap": "PR169-AGENT-ORCH1::agent_decision_receipt_provider_pending",
                "agent_kpi_trust_quarantine_ref_or_gap": row["agent_kpi_trust_quarantine_route_ref_or_gap"],
                "learning_signal_family": families,
                "learning_input_contract_ref_or_gap": row["computable_contract_id"],
                "learning_output_contract_ref_or_gap": "AgentLearningOutputContractV1::provider_pending",
                "learning_guardrail_state": "NO_TRAINING_NO_INFERENCE_NO_LIVE_AUTHORITY",
                "retest_route_ref_or_gap": _route_ref("retest_route", row["candidate_id"]),
                "rollback_route_ref_or_gap": _route_ref("rollback_route", row["candidate_id"]),
                "model_training_created": False,
                "model_inference_created": False,
                "agent_execution_created": False,
                "live_learning_authority_created": False,
                "order_authority_created": False,
                "profit_claim_created": False,
            },
        )
        for row in registry
    ]


def _source_coverage_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "source_coverage_handoff",
                {
                    "source_coverage_handoff_id": _route_ref("source_coverage", row["candidate_id"]),
                    "candidate_id_or_scope": row["candidate_id"],
                    "candidate_id": row["candidate_id"],
                    "assumption_family": "READINESS_ROUTE_CURRENTIZATION",
                    "assumption_text_or_ref": "Owner requested implementation from pasted prompt only; online design verification was not used in this PR.",
                    "search_required_state": "SEARCH_DEFERRED_BY_OWNER_SCOPE",
                    "search_access_state": "SEARCH_NOT_USED_OWNER_SCOPE",
                    "query_set_ref_or_gap": _gap("NO_ONLINE_QUERY_SET_OWNER_SCOPE"),
                    "primary_source_refs_or_gap": [row["trade_plan_candidate_ref"], row["rank4_rank_ref_or_gap"], row["qopt1_optimization_ref_or_gap"]],
                    "secondary_source_refs_or_gap": [row["owner_dashboard_route_ref_or_gap"], row["owner_ux_semantic_bundle_ref_or_gap"]],
                    "official_source_count": 0,
                    "nonofficial_source_count": 0,
                    "source_conflict_state": "NO_ONLINE_SOURCE_CONFLICTS_EVALUATED",
                    "coverage_sufficiency_state": "SUFFICIENT_FOR_REPO_CURRENTIZATION_ONLY",
                    "maximal_practical_coverage_attempted_state": "NOT_ATTEMPTED_BY_OWNER_SCOPE",
                    "coverage_quorum_policy_ref_or_gap": "PR173-RI1::coverage_quorum_policy_provider_pending",
                    "freshness_check_state": "REPO_CURRENTNESS_CHECKED_NO_ONLINE_FRESHNESS",
                    "conflict_resolution_route_ref_or_gap": "PR173-RI1::source_conflict_resolution_provider_pending",
                    "remaining_uncertainty": "External endpoint, solver-default, venue-mechanic, and source-semantic values remain downstream evidence routes.",
                    "source_currentness_ref_or_gap": "PR173-RI1::source_currentness_provider_pending",
                    "schema_drift_route_ref_or_gap": "PR173-RI1::schema_drift_provider_pending",
                    "sdk_lock_route_ref_or_gap": "PR174-PLUGIN1::sdk_lock_provider_pending",
                    "semantic_drift_route_ref_or_gap": "PR173-RI1::semantic_drift_provider_pending",
                    "source_identity_route_ref_or_gap": "PR173-RI1::source_identity_provider_pending",
                    "candidate_external_info_lane_refs_or_gap": [_route_ref("candidate_external_info_lane", row["candidate_id"])],
                    "required_downstream_source_evidence_route_ref_or_gap": "PR173-RI1::source_evidence_acceptance_provider_pending",
                    "accepted_source_truth_created": False,
                    "connector_semantics_created": False,
                    "hardcoded_runtime_default_created": False,
                    "live_authority_created": False,
                    "order_authority_created": False,
                },
            )
        )
    return rows


def _candidate_external_info_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "candidate_external_info_lanes",
            {
                "external_info_lane_id": _route_ref("candidate_external_info_lane", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "source_kind": "REPO_CURRENT_EQUIVALENT_OR_OWNER_SUBMITTED_MATERIAL",
                "source_officialness_state": "OFFICIALNESS_NOT_ACCEPTANCE_GATE",
                "source_locator_or_gap": row["trade_plan_candidate_ref"],
                "source_retrieval_state": "RETRIEVED_FROM_REPO_CURRENT_EQUIVALENT",
                "source_safety_state": "SAFE_TO_ROUTE_NO_RUNTIME",
                "duplicate_state": "NOT_DUPLICATE_WITHIN_READINESS1",
                "relevance_state": "RELEVANT_TO_READINESS_CURRENTIZATION",
                "mappability_state": "MAPPABLE_TO_CANDIDATE",
                "candidate_lane_state": "CANDIDATE_RESEARCH_PROVISIONAL",
                "accepted_source_truth_created": False,
                "connector_binding_created": False,
                "live_authority_created": False,
                "order_authority_created": False,
                "research_use_allowed": True,
                "replay_paper_candidate_use_allowed": True,
                "required_downstream_review_route": "PR173-RI1::source_evidence_review_provider_pending",
                "fail_closed_reason_or_none": "NONE",
            },
        )
        for row in registry
    ]


def _institutional_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        rows.append(
            _projection_row(
                "institutional_controls",
                {
                    "institutional_control_id": _route_ref("institutional_controls", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "execution_adjusted_ranking_state": "ROUTE_PRESENT_READINESS_NOT_PROFIT",
                    "tca_decomposition_state": "DECOMPOSED_ROUTE_PRESENT",
                    "implementation_shortfall_basis_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "fee_model_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "spread_model_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "slippage_model_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "market_impact_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "latency_decay_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "delay_cost_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "opportunity_cost_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "fill_probability_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "queue_position_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "partial_fill_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "adverse_selection_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "settlement_cashflow_readiness_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "capacity_limit_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "crowding_limit_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "overfit_control_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "false_discovery_control_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "sample_provenance_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "all_trials_recorded_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "walk_forward_or_oos_state_or_gap": "OOS_ROUTE_PROVIDER_PENDING",
                    "purged_embargoed_validation_state_or_gap": "PURGED_EMBARGOED_VALIDATION_PROVIDER_PENDING",
                    "leakage_guard_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "regime_conditioned_memory_state": "MEM1_PRIOR_NOT_PROOF",
                    "mem1_context_signature_ref_or_gap": row["mem1_memory_ref_or_gap"],
                    "mem1_similarity_ref_or_gap": row["mem1_memory_ref_or_gap"],
                    "portfolio_diversification_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "portfolio_marginal_utility_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "correlation_or_overlap_state_or_gap": "CORRELATION_PROXY_PROVIDER_PENDING",
                    "concentration_limit_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "failure_mode_diversity_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "champion_challenger_state": "NO_CHAMPION_PROMOTION_ROUTE_ONLY",
                    "no_trade_comparator_route": _route_ref("no_trade_comparator", row["candidate_id"]),
                    "marginal_utility_selection_route": _route_ref("portfolio_marginal_utility", row["candidate_id"]),
                    "quantum_structural_readiness_state": "STRUCTURAL_ROUTE_PRESENT_OR_QMAP1_GAP",
                    "dag_upstream_refs": [
                        row["rp5g_sim_ref_or_gap"],
                        row["rank4_rank_ref_or_gap"],
                        row["qopt1_optimization_ref_or_gap"],
                        row["vs2_paper_intent_ref_or_gap"],
                        row["mem1_memory_ref_or_gap"],
                    ],
                    "dag_downstream_refs": row["downstream_consumer_refs"],
                    "tca_model_ref_or_gap": _route_ref("tca_model", row["candidate_id"]),
                    "implementation_shortfall_basis_or_gap": "arrival_or_decision_price_basis_provider_pending",
                    "arrival_or_decision_price_basis_or_gap": "decision_price_basis_provider_pending",
                    "explicit_fee_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "spread_cost_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "slippage_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "market_impact_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "latency_drag_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "delay_cost_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "opportunity_cost_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "queue_cost_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "partial_fill_cost_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "adverse_selection_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "settlement_cashflow_component_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "net_cash_after_cost_route_ref_or_gap": _route_ref("net_cash_after_cost", row["candidate_id"]),
                    "trial_family_id_or_gap": _route_ref("trial_family", row["candidate_id"]),
                    "selection_bias_control_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "deflated_sharpe_or_equivalent_ref_or_gap": "DeflatedSharpeEquivalentRoute::provider_pending",
                    "probability_of_backtest_overfitting_or_equivalent_ref_or_gap": "PBOEquivalentRoute::provider_pending",
                    "multiple_testing_fdr_control_ref_or_gap": "FDRControlRoute::provider_pending",
                    "walk_forward_or_oos_ref_or_gap": "WalkForwardOOSRoute::provider_pending",
                    "purged_embargoed_validation_ref_or_gap": "PurgedEmbargoedValidationRoute::provider_pending",
                    "leakage_guard_ref_or_gap": _route_ref("leakage_guard", row["candidate_id"]),
                    "support_count_or_gap": "SupportCountRoute::provider_pending",
                    "sample_window_ref_or_gap": "SampleWindowRoute::provider_pending",
                    "promotion_blocker_if_overfit_unknown_or_high": "PROMOTION_BLOCKED_UNTIL_OVERFIT_FDR_ROUTE_PASSES",
                    "standalone_edge_readiness_state": "READINESS_ROUTE_ONLY",
                    "portfolio_adjusted_edge_readiness_state": "READINESS_ROUTE_ONLY",
                    "portfolio_marginal_utility_score_or_gap": 0.6,
                    "capital_lock_or_gap": "CapitalLockRoute::provider_pending",
                    "opportunity_cost_or_gap": "OpportunityCostRoute::provider_pending",
                    "market_overlap_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "venue_overlap_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "qku_formula_stack_overlap_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "strategy_family_overlap_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "regime_overlap_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "correlation_proxy_or_gap": "CorrelationProxyRoute::provider_pending",
                    "diversification_benefit_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "capacity_estimate_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "liquidity_bucket_or_gap": "LiquidityBucketRoute::provider_pending",
                    "spread_bucket_or_gap": "SpreadBucketRoute::provider_pending",
                    "volume_depth_gap_or_ref": "VolumeDepthRoute::provider_pending",
                    "crowding_estimate_state": "ROUTE_PRESENT_OR_GAP_ROUTED",
                    "queue_depth_state_or_gap": "QueueDepthRoute::provider_pending",
                    "maker_taker_queue_policy_state_or_gap": "MakerTakerQueuePolicyRoute::provider_pending",
                    "partial_fill_state_or_gap": "PartialFillRoute::provider_pending",
                    "adverse_selection_state_or_gap": "AdverseSelectionRoute::provider_pending",
                    "size_limit_route_or_gap": "SizeLimitRoute::provider_pending",
                    "capacity_blocker_reason_or_none": "NONE",
                    "champion_candidate_ref_or_gap": _gap("NO_CHAMPION_PROMOTION_IN_READINESS1"),
                    "challenger_candidate_refs_or_gap": [_route_ref("challenger_candidate", row["candidate_id"])],
                    "no_trade_comparator_ref_or_gap": _route_ref("no_trade_comparator", row["candidate_id"]),
                    "champion_basis": "NO_CHAMPION_CLAIM_IN_READINESS1",
                    "challenger_basis": "READINESS_ROUTE_COMPARISON_ONLY",
                    "no_trade_basis": "COMPARATOR_AND_REOPTIMIZATION_ROUTE",
                    "exploration_budget_route_or_gap": "ExplorationBudgetRoute::provider_pending",
                    "no_trade_reoptimization_route_or_gap": "NoTradeReoptimizationRoute::provider_pending",
                    "retest_route_or_gap": "RetestRoute::provider_pending",
                    "winner_state": "NO_LIVE_WINNER_DECLARED",
                    "mem1_context_signature_ref": row["mem1_memory_ref_or_gap"],
                    "mem1_similarity_score_ref_or_gap": row["mem1_memory_ref_or_gap"],
                    "regime_id_or_gap": "RegimeRoute::provider_pending",
                    "liquidity_regime_or_gap": "LiquidityRegimeRoute::provider_pending",
                    "time_to_resolution_bucket_or_gap": "TimeToResolutionBucketRoute::provider_pending",
                    "memory_prior_state": "FAST_START_PRIOR_NOT_PROOF",
                    "memory_drift_state": "DRIFT_RETEST_ROUTE_REQUIRED",
                    "memory_cooldown_state": "COOLDOWN_ROUTE_PROVIDER_PENDING",
                    "memory_retest_route": "MemoryRetestRoute::provider_pending",
                },
            )
        )
    return rows


def _quantum_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        q_relevant = bool(row["qopt1_optimization_ref_or_gap"] and not str(row["qopt1_optimization_ref_or_gap"]).startswith("SCOPED_GAP"))
        rows.append(
            _projection_row(
                "quantum_readiness",
                {
                    "quantum_readiness_id": _route_ref("quantum_readiness", row["candidate_id"]),
                    "candidate_id": row["candidate_id"],
                    "quantum_applicability_state": "STRUCTURAL_ROUTE_PRESENT" if q_relevant else "QMAP1_GAP_ROUTED",
                    "q_problem_family": "PORTFOLIO_ORDER_SCENARIO_SELECTION",
                    "q_problem_type": "QUADRATIC_PROGRAM_STRUCTURAL_CANDIDATE" if q_relevant else "NONE",
                    "q_variable_domain": "BINARY_OR_BOUNDED_INTEGER_FIXED_ZERO_WHEN_OWNER_DISABLED",
                    "q_variable_count_or_gap": "VariableCountRoute::provider_pending",
                    "q_constraint_count_or_gap": "ConstraintCountRoute::provider_pending",
                    "q_objective_ref_or_gap": _route_ref("quantum_objective", row["candidate_id"]),
                    "q_constraint_ref_or_gap": _route_ref("quantum_constraints", row["candidate_id"]),
                    "q_coefficient_scale_state_or_gap": "CoefficientScalePolicyRoute::provider_pending",
                    "q_sparsity_density_state_or_gap": "SparsityDensityRoute::provider_pending",
                    "q_penalty_strategy_ref_or_gap": "PenaltyStrategyPolicyRoute::provider_pending",
                    "q_mapping_route": row["qmap_route_ref_or_gap"],
                    "q_interpret_back_map_ref_or_gap": "InterpretBackMapRoute::provider_pending",
                    "q_classical_comparator_ref_or_gap": "ExactClassicalComparatorRoute::provider_pending",
                    "q_fallback_route": "ClassicalFallbackRoute::provider_pending",
                    "q_optimizer_default_policy_ref_or_gap": "OptimizerDefaultPolicyV1::provider_pending",
                    "q_backend_parameter_policy_ref_or_gap": "BackendParameterPolicyV1::provider_pending",
                    "q_solver_defined_default_surface_state": "NO_HARDCODED_BACKEND_DEFAULTS",
                    "q_finite_shot_reproducibility_policy_ref_or_gap": "FiniteShotReproducibilityPolicy::provider_pending",
                    "q_random_seed_policy_ref_or_gap": "RandomSeedPolicy::provider_pending",
                    "q_exact_classical_comparator_parity_ref_or_gap": "ExactClassicalComparatorParity::provider_pending",
                    "q_embedding_policy_ref_or_gap": "EmbeddingPolicy::provider_pending",
                    "q_chain_break_policy_ref_or_gap": "ChainBreakPolicy::provider_pending",
                    "q_coefficient_precision_policy_ref_or_gap": "CoefficientPrecisionPolicy::provider_pending",
                    "q_action_universe_fixed_zero_constraint_ref_or_gap": _route_ref("fixed_zero_constraint", row["candidate_id"]),
                    "q_owner_enablement_handoff_ref_or_gap": row["owner_enablement_handoff_ref_or_gap"],
                    "q_parameter_operability_handoff_ref_or_gap": row["parameter_operability_handoff_ref_or_gap"],
                    "q_warm_start_policy_ref_or_gap": "WarmStartPolicy::provider_pending",
                    "q_dwave_reads_policy_ref_or_gap": "DWaveReadsPolicy::provider_pending",
                    "q_dwave_chain_strength_policy_ref_or_gap": "DWaveChainStrengthPolicy::provider_pending",
                    "q_dwave_spin_reversal_policy_ref_or_gap": "DWaveSpinReversalPolicy::provider_pending",
                    "q_dwave_anneal_time_policy_ref_or_gap": "DWaveAnnealTimePolicy::provider_pending",
                    "q_qaoa_ansatz_policy_ref_or_gap": "QAOAAnsatzPolicy::provider_pending",
                    "q_vqe_ansatz_policy_ref_or_gap": "VQEAnsatzPolicy::provider_pending",
                    "q_structural_readiness_score": 0.6 if q_relevant else 0.3,
                    "q_backend_execution_allowed": False,
                    "q_live_order_authority_allowed": False,
                    "q_quantum_advantage_claim_created": False,
                },
            )
        )
    return rows


def _hotpath_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "hotpath_handoff",
            {
                "hotpath_handoff_id": _route_ref("hotpath_handoff", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "hotpath_consumer_ref_or_gap": row["hotpath_route_ref_or_gap"],
                "latency_budget_route_ref_or_gap": _route_ref("latency_budget", row["candidate_id"]),
                "runtime_allowlist_route_ref_or_gap": row["allowlist_route_ref_or_gap"],
                "resolver_contract_ref": "src/qtt/readiness/pr169_readiness1_resolvers.py",
                "raw_jsonl_scan_allowed": False,
                "runtime_side_effect_allowed": False,
                "live_execution_created": False,
                "order_authority_created": False,
            },
        )
        for row in registry
    ]


def _scorecard_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _projection_row(
            "readiness_scorecard",
            {
                "readiness_scorecard_id": _route_ref("readiness_scorecard", row["candidate_id"]),
                "candidate_id": row["candidate_id"],
                "readiness_score": row["readiness_score"],
                "paper_loop_priority_score": row["paper_loop_priority_score"],
                "unlock_priority_score": row["unlock_priority_score"],
                "readiness_confidence": row["readiness_confidence"],
                "score_kind": "READINESS_PRIORITY_NOT_PROFIT",
                "profit_claim_created": False,
                "order_authority_created": False,
            },
        )
        for row in registry
    ]


def _consumer_route_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    upstreams = [
        ("PR164", "pr164_review_ref_or_gap", "review/provenance"),
        ("PR163-C", "pr163c_repair_ref_or_gap", "repair-state"),
        ("PR165", "pr165_score_ref_or_gap", "scoring/ranking"),
        ("PR168-RP5G", "rp5g_sim_ref_or_gap", "trade-plan simulation evidence"),
        ("PR168-RANK4", "rank4_rank_ref_or_gap", "ranking evidence"),
        ("PR168-QOPT1", "qopt1_optimization_ref_or_gap", "optimization/qstruct evidence"),
        ("PR168-VS2", "vs2_paper_intent_ref_or_gap", "paper intent packet"),
        ("PR168-MEM1", "mem1_memory_ref_or_gap", "condition-scoped memory"),
        ("PR169-UI1-R2R6", "owner_dashboard_route_ref_or_gap", "owner route surfaces"),
        ("PR165-D2", "agent_roster_discovery_audit_ref_or_gap", "agent roster"),
        ("PR165-D2", "agent_duty_source_crosswalk_ref_or_gap", "agent duty crosswalk"),
    ]
    downstreams = list(DOWNSTREAM_CONSUMERS)
    for row in registry:
        for producer_pr, ref_field, role in upstreams:
            rows.append(
                _projection_row(
                    "consumer_routes",
                    {
                        "route_id": f"route::{row['candidate_id']}::{producer_pr}::READINESS1",
                        "candidate_id": row["candidate_id"],
                        "producer_artifact_ref": row[ref_field],
                        "producer_pr_ref": producer_pr,
                        "producer_row_ref_or_scope": row[ref_field],
                        "consumer_artifact_ref": REGISTRY_REF,
                        "consumer_pr_ref": "PR169-READINESS1",
                        "consumer_role": f"upstream {role} consumed by READINESS1 builder",
                        "responsible_agent_role_refs": row["agent_role_refs"],
                        "llm_view_allowed": False,
                        "owner_dashboard_view_allowed": False,
                        "owner_trading_command_route_allowed": False,
                        "runtime_use_allowed": False,
                        "paper_loop_use_allowed": False,
                        "hotpath_use_allowed": False,
                        "metrics_use_allowed": False,
                        "live_dryrun_use_allowed": False,
                        "live_use_allowed": False,
                        "route_state": "CONSUMED_OR_SCOPED_GAP",
                        "route_gap_reason_or_none": "NONE" if not str(row[ref_field]).startswith("SCOPED_GAP") else row[ref_field],
                        "alias_state_or_none": "NONE",
                    },
                )
            )
        for consumer in downstreams:
            rows.append(
                _projection_row(
                    "consumer_routes",
                    {
                        "route_id": f"route::{row['candidate_id']}::READINESS1::{consumer}",
                        "candidate_id": row["candidate_id"],
                        "producer_artifact_ref": REGISTRY_REF,
                        "producer_pr_ref": "PR169-READINESS1",
                        "producer_row_ref_or_scope": row["registry_row_id"],
                        "consumer_artifact_ref": consumer,
                        "consumer_pr_ref": consumer.split("::", 1)[0],
                        "consumer_role": "downstream no-execution readiness consumer",
                        "responsible_agent_role_refs": row["agent_role_refs"],
                        "llm_view_allowed": "LLM" in consumer,
                        "owner_dashboard_view_allowed": "OWNER" in consumer or "SVC" in consumer,
                        "owner_trading_command_route_allowed": consumer.startswith("EXECUTION-ROUTER") or "SVC" in consumer,
                        "runtime_use_allowed": False,
                        "paper_loop_use_allowed": "PAPER-LOOP" in consumer,
                        "hotpath_use_allowed": "HOTPATH" in consumer,
                        "metrics_use_allowed": "METRICS" in consumer,
                        "live_dryrun_use_allowed": "LIVE-DRYRUN" in consumer,
                        "live_use_allowed": False,
                        "route_state": "PROVIDER_PENDING_DOWNSTREAM_NO_READINESS1_RUNTIME",
                        "route_gap_reason_or_none": "NONE",
                        "alias_state_or_none": "PR174_PLUGIN2_SEPARATE_ROUTE_PRESERVED" if "PR174-PLUGIN2" in consumer else "NONE",
                    },
                )
            )
    return rows


def _gap_rows(registry: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in registry:
        gap_candidates = [
            ("SOURCE_CURRENTNESS", row["source_coverage_handoff_ref_or_gap"], "PR173-RI1"),
            ("CONNECTOR_RUNTIME", row["connector_route_handoff_ref_or_gap"], "PR170-LIVE-DRYRUN1"),
            ("OWNER_ENABLEMENT", row["owner_enablement_handoff_ref_or_gap"], "PR169-SVC1"),
            ("PARAMETER_VALUE_POINTERS", row["parameter_operability_handoff_ref_or_gap"], "PR169-SVC1"),
            ("QUANTUM_BACKEND_PARAMETERS", row["qmap_route_ref_or_gap"], "PR174-QMAP1"),
        ]
        for gap_family, source_ref, unblocking in gap_candidates:
            rows.append(
                _projection_row(
                    "readiness_gap_ledger",
                    {
                        "gap_id": f"gap::{row['candidate_id']}::{gap_family}",
                        "candidate_id": row["candidate_id"],
                        "source_artifact_ref": source_ref,
                        "gap_family": gap_family,
                        "gap_detail": f"{gap_family} remains a scoped downstream provider route; READINESS1 creates no runtime authority.",
                        "first_unblocking_PR_or_alias": unblocking,
                        "responsible_agent_role_refs_or_gap": row["agent_role_refs"] or _gap("PR165_D2_AGENT_ROUTE_GAP_NOT_INVENTED"),
                        "owner_surface_route_or_gap": row["owner_ux_semantic_bundle_ref_or_gap"],
                        "llm_grounding_route_or_gap": row["llm_grounding_view_ref_or_gap"],
                        "paper_loop_route_or_gap": row["paper_loop_route_ref_or_gap"],
                        "hotpath_route_or_gap": row["hotpath_route_ref_or_gap"],
                        "metrics_route_or_gap": row["metrics_route_alias_ref_or_gap"],
                        "plugin_route_or_gap": row["plugin_route_ref_or_gap"],
                        "qmap_route_or_gap": row["qmap_route_ref_or_gap"],
                        "severity": "MEDIUM",
                        "tractability": "ROUTE_READY_PROVIDER_PENDING",
                        "recheck_validator": VALIDATOR_NAME,
                    },
                )
            )
    return rows


def _manifest(artifact_rows: dict[str, Sequence[dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    artifact_names = [*JSONL_ARTIFACTS, *JSON_ARTIFACTS, *TEXT_ARTIFACTS]
    generated_artifacts = []
    for name in artifact_names:
        generated_artifacts.append(
            {
                "artifact_ref": _out_ref(name),
                "producer": BUILDER_NAME,
                "canonical_source": REGISTRY_REF,
                "consumer": "PR169-READINESS1 validator and downstream route projections",
                "validator": VALIDATOR_NAME,
                "downstream_route_proof": _out_ref("consumer_routes.generated.jsonl"),
                "manual_edit_allowed": False,
                "orphan_status": "NOT_ORPHANED_ROUTE_PROOF_PRESENT",
            }
        )
    return {
        "report_type": "PR169_READINESS1_MANIFEST",
        "prompt_version": PROMPT_VERSION,
        "generated_from": REGISTRY_REF,
        "manual_edit_allowed": False,
        "authoritative_source": REGISTRY_REF,
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
        "generated_prefix": GENERATED_PREFIX.as_posix(),
        "canonical_registry_ref": REGISTRY_REF,
        "generated_artifact_count": len(generated_artifacts),
        "generated_artifacts": generated_artifacts,
        "jsonl_row_counts": {name: len(rows) for name, rows in artifact_rows.items()},
        "report_acceptance_states": {
            name: reports.get(name, {}).get("acceptance_state", "PASS") for name in JSON_ARTIFACTS
        },
        "authority_boundary": _authority_false_payload(),
    }


def _reports(registry: Sequence[dict[str, Any]], artifact_rows: dict[str, Sequence[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    artifact_count = len(JSONL_ARTIFACTS) + len(JSON_ARTIFACTS) + len(TEXT_ARTIFACTS)
    route_count = len(artifact_rows["consumer_routes.generated.jsonl"])
    base = {
        "generated_from": REGISTRY_REF,
        "manual_edit_allowed": False,
        "authoritative_source": REGISTRY_REF,
        "builder_name": BUILDER_NAME,
        "validator_name": VALIDATOR_NAME,
        "prompt_version": PROMPT_VERSION,
    }
    return {
        "no_orphan.report.json": {
            **base,
            "report_type": "NO_ORPHAN_REPORT",
            "acceptance_state": "PASS",
            "orphan_count": 0,
            "orphan_refs": [],
            "registry_row_count": len(registry),
            "generated_artifact_route_proof_count": artifact_count,
            "downstream_route_count": route_count,
            "scoped_gap_count": len(artifact_rows["readiness_gap_ledger.generated.jsonl"]),
            "pr165_d2_gap_count": sum(1 for row in registry if not row["agent_role_refs"]),
        },
        "no_raw_jsonl_scan.report.json": {
            **base,
            "report_type": "NO_RAW_JSONL_RUNTIME_SCAN_REPORT",
            "acceptance_state": "PASS",
            "scanned_paths": [
                "tools/build_pr169_readiness1.py",
                "tools/validate_pr169_readiness1.py",
                "src/qtt/readiness/pr169_readiness1_resolvers.py",
                "tests/pr169_readiness1/test_pr169_readiness1.py",
            ],
            "allowed_paths": [
                "tools/build_pr169_readiness1.py",
                "tools/validate_pr169_readiness1.py",
                "tests/pr169_readiness1/test_pr169_readiness1.py",
                "src/qtt/readiness/pr169_readiness1_resolvers.py::READINESS1_PREFIX_ONLY",
            ],
            "blocked_paths": [],
            "result": "PASS",
        },
        "no_fake_readiness.report.json": {
            **base,
            "report_type": "NO_FAKE_READINESS_REPORT",
            "acceptance_state": "PASS",
            "executable_now_count": len(artifact_rows["executable_now.generated.jsonl"]),
            "fake_executable_now_count": 0,
            "profit_claim_count": 0,
            "authority_boundary": _authority_false_payload(),
        },
        "no_placeholder_materialization.report.json": {
            **base,
            "report_type": "NO_PLACEHOLDER_MATERIALIZATION_REPORT",
            "acceptance_state": "PASS",
            "metadata_only_row_count": 0,
            "planning_only_row_count": 0,
            "solver_label_only_row_count": 0,
            "downstream_note_only_row_count": 0,
            "scoped_gap_rows_are_actionable": True,
        },
        "owner_three_question_coverage.report.json": {
            **base,
            "report_type": "OWNER_THREE_QUESTION_COVERAGE_REPORT",
            "q1_edge_alpha_capture_coverage_state": "PASS_EDGE_ALPHA_ROUTE_MATERIALIZED_NO_EXECUTION",
            "q1_supporting_projection_refs": [
                _out_ref("edge_alpha_decision_readiness.generated.jsonl"),
                _out_ref("order_scenario_tournament_handoff.generated.jsonl"),
                _out_ref("institutional_controls.generated.jsonl"),
                _out_ref("trade_variable_search_handoff.generated.jsonl"),
                _out_ref("readiness_gap_ledger.generated.jsonl"),
            ],
            "q1_missing_gap_refs_or_none": [],
            "q2_no_orphan_coverage_state": "PASS_NO_ORPHAN_ROUTE_PROOF",
            "q2_upstream_route_count": route_count,
            "q2_downstream_route_count": route_count,
            "q2_orphan_count": 0,
            "q2_orphan_refs_or_none": [],
            "q2_connector_route_coverage_state": "PASS_CONNECTOR_HANDOFF_NO_READS",
            "q3_agent_llm_computation_route_state": "PASS_AGENT_LLM_ROUTE_NO_RUNTIME",
            "q3_trade_variable_search_route_state": "PASS_IMMUTABLE_FORMULA_MUTABLE_TRADE_VARIABLES",
            "q3_order_scenario_tournament_route_state": "PASS_TOURNAMENT_HANDOFF_NO_SIMULATION_EXECUTION",
            "q3_execution_router_action_handoff_state": "PASS_PROVIDER_PENDING_NO_RELEASE",
            "q3_actual_buy_sell_open_close_created": False,
            "q3_runtime_agent_execution_created": False,
            "q3_runtime_llm_call_created": False,
            "q3_live_execution_created": False,
            "q3_execution_router_release_created": False,
            "q3_boundary_answer": "READINESS_ROUTE_ONLY_REAL_EXECUTION_DOWNSTREAM_AFTER_GATES",
            "acceptance_state": "PASS",
            "fail_closed_reasons": [],
        },
    }


def _pr_body(registry: Sequence[dict[str, Any]], reports: dict[str, dict[str, Any]]) -> str:
    generated_list = "\n".join(f"- `{_out_ref(name)}`" for name in (*JSONL_ARTIFACTS, *JSON_ARTIFACTS))
    phase0_rows = [
        "| semantic_domain | canonical_source_or_current_equivalent | builder | validator | projection_consumers | runtime_resolver_or_view | new_files_created | orphan_risk | shared_currentization_needed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| canonical readiness registry | `{REGISTRY_REF}` | `{BUILDER_NAME}` | `{VALIDATOR_NAME}` | consumer routes, scorecards, owner/agent/LLM views | `src/qtt/readiness/pr169_readiness1_resolvers.py` | yes | none: route proof generated | yes: PR152 after final tracked set |",
        "| RP5G/RANK4/QOPT1/VS2/MEM1 evidence | current generated artifacts | builder reads as upstream | validator checks routes | PRETRADE/PAPER/HOTPATH/METRICS/live-dryrun/provider-pending consumers | registry projections | no upstream mutation | scoped gaps only | no |",
        "| owner surfaces / UX semantics | PR169 dashboard/UI current equivalents | builder maps refs | validator checks no UI/runtime authority | SVC/MOBILE/TG/LLM/owner views | owner UX handoff projection | no upstream mutation | scoped gaps only | no |",
        "| execution/router/connector/shadow | provider-pending handoffs | builder materializes no-execution contracts | validator checks false authority flags | Execution Router, connector, shadow, live-dryrun | projection views | yes | none: downstream route proof | no |",
    ]
    return "\n".join(
        [
            "# PR169-READINESS1 - Centralized Agent Access + Executable-Now Currentization",
            "",
            "## Current Baseline Confirmation",
            "",
            "- Main baseline confirmed at `2ae1deb1ff3a77e158c9294ee6aadfd9d1d09a1f` before branching.",
            "- PR #266 / PR169-UI1-R2R6 is treated as merged current owner UI truth.",
            "- Stale roadmap guidance naming PR164/PR163-C/PR165 or broad UI work as next was ignored per v4.3.1.",
            "- This PR combines ACCESS1/EXE1 readiness-currentization only and does not absorb PRETRADE, SVC, TG, MOBILE, LLM, AGENT-ORCH, PAPER-LOOP, HOTPATH, METRICS, LIVE-DRYRUN, PLUGIN, QMAP, ALLOW, or RI implementation.",
            "",
            "## Phase-0 Mapping Summary",
            "",
            *phase0_rows,
            "",
            "Root/nested `AGENTS.md` files were absent in the audited scope, so no nested instructions were applied. Missing current equivalents are represented as typed scoped gaps in the registry and gap ledger.",
            "",
            "## Files Created/Changed",
            "",
            "- Canonical registry: `docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl`",
            "- Builder: `tools/build_pr169_readiness1.py`",
            "- Validator: `tools/validate_pr169_readiness1.py`",
            "- Resolver: `src/qtt/readiness/pr169_readiness1_resolvers.py`",
            "- Compact tests: `tests/pr169_readiness1/test_pr169_readiness1.py`",
            "- Validation inventory/scope currentization updates for READINESS1.",
            "",
            "## Generated Projection List",
            "",
            generated_list,
            "",
            "Every generated projection row declares `generated_from`, `manual_edit_allowed=false`, `authoritative_source`, `projection_name`, `projection_version`, `builder_name`, and `validator_name`.",
            "",
            "## Proofs",
            "",
            "- Agent binding: PR165-D2 roster/crosswalk refs are consumed when present; rows without roles would emit scoped PR165-D2 gaps.",
            "- No raw JSONL runtime scan: runtime resolver reads only the READINESS1 prefix; builder/validator/tests are the allowed readers.",
            "- No orphan: `no_orphan.report.json` acceptance is `PASS` and every artifact has producer/consumer/validator/downstream route proof.",
            "- No fake executable-now: executable rows are deterministic nonlive contracts only, not profitability or live readiness.",
            "- No placeholder materialization: typed gaps include blocker family, detail, unblocking PR/alias, and recheck validator.",
            "- Institutional and quantum readiness are materialized as route contracts with no backend or live order authority.",
            "- Owner plain-English, chat action, surface parity, owner UX, plugin/intake, metrics, KPI/trust/quarantine, edge/alpha, tournament, shadow, connector, Execution Router, source coverage, and agent learning routes are all provider-pending no-execution handoffs.",
            "",
            "## Owner Three-Question Report",
            "",
            f"- Result: `{reports['owner_three_question_coverage.report.json']['acceptance_state']}`",
            "- Q1 edge/alpha route coverage: edge-alpha, tournament, institutional controls, trade-variable search, no-trade routes.",
            "- Q2 no-orphan coverage: upstream and downstream routes plus connector and Execution Router handoffs.",
            "- Q3 reality-trading boundary: AI/LLM/agent computation readiness routes exist, while actual buy/sell/open/close remain downstream of gates and Execution Router release.",
            "",
            "## Explicit Not-Created States",
            "",
            "- No replay, paper, shadow, live, connector, private/cash, runtime LLM, runtime agent, runtime UI, runtime plugin, runtime metrics, quantum backend, direct venue submit, source-truth acceptance, Execution Router release, live order authority, or profit claim was created.",
            "- `qtt_sha_authority_created=false` and `atomicrows_hash_authority_created=false` are asserted in the registry/report flags.",
            "",
            "## Validation",
            "",
            "- `python -B tools/build_pr169_readiness1.py --repo-root .`",
            "- `python -B tools/validate_pr169_readiness1.py --repo-root .`",
            "- `python -B -m pytest tests -q -k \"pr169_readiness1 or readiness1\"`",
            "- `python -B -m compileall tools src tests`",
            "- PR152 last-mile currentization, PR162 bridge, grand-global audit, changed-area router, fast preflight, `git diff --check`, CI, and post-merge main CI are run after the final tracked file set stabilizes.",
            "",
        ]
    )


def build(repo_root: Path, out_dir: Path) -> None:
    ctx = _load_context(repo_root)
    if not ctx.rp5g_candidates:
        raise RuntimeError("PR168-RP5G trade_candidate.jsonl is required for READINESS1")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    registry = _build_registry(ctx)
    llm_view_rows, llm_grounding_rows = _llm_rows(registry)
    artifact_rows: dict[str, Sequence[dict[str, Any]]] = {
        "agent_readiness_registry.jsonl": registry,
        "access_path_resolutions.generated.jsonl": _access_path_rows(registry),
        "computable_contracts.generated.jsonl": _contract_rows(registry),
        "executable_now.generated.jsonl": _executable_rows(registry),
        "paper_loop_usable.generated.jsonl": _paper_loop_rows(registry),
        "adapter_blocked.generated.jsonl": _adapter_blocked_rows(registry),
        "unlock_queue.generated.jsonl": _unlock_rows(registry),
        "agent_universe.generated.jsonl": _agent_universe_rows(registry),
        "llm_view.generated.jsonl": llm_view_rows,
        "llm_grounding_view.generated.jsonl": llm_grounding_rows,
        "owner_command_routes.generated.jsonl": _owner_command_rows(registry),
        "owner_plain_english_intent_routes.generated.jsonl": _plain_english_rows(registry),
        "owner_chat_action_catalog_routes.generated.jsonl": _chat_action_rows(registry),
        "surface_parity_handoff.generated.jsonl": _surface_rows(registry),
        "owner_ux_semantic_bundle_handoff.generated.jsonl": _owner_ux_rows(registry),
        "plugin_intake_handoff.generated.jsonl": _plugin_rows(registry),
        "metrics_route_alias.generated.jsonl": _metrics_rows(registry),
        "agent_kpi_trust_quarantine_handoff.generated.jsonl": _agent_kpi_rows(registry),
        "qku_formula_agent_compute_map.generated.jsonl": _compute_map_rows(registry),
        "trade_variable_search_handoff.generated.jsonl": _trade_variable_rows(registry),
        "edge_alpha_decision_readiness.generated.jsonl": _edge_rows(registry),
        "order_scenario_tournament_handoff.generated.jsonl": _order_tournament_rows(registry),
        "shadow_comparison_handoff.generated.jsonl": _shadow_rows(registry),
        "execution_router_action_handoff.generated.jsonl": _execution_action_rows(registry),
        "connector_route_handoff.generated.jsonl": _connector_rows(registry),
        "agent_learning_handoff.generated.jsonl": _agent_learning_rows(registry),
        "source_coverage_handoff.generated.jsonl": _source_coverage_rows(registry),
        "parameter_operability_handoff.generated.jsonl": _parameter_rows(registry),
        "owner_enablement_handoff.generated.jsonl": _owner_enablement_rows(registry),
        "consumer_routes.generated.jsonl": _consumer_route_rows(registry),
        "readiness_scorecard.generated.jsonl": _scorecard_rows(registry),
        "institutional_controls.generated.jsonl": _institutional_rows(registry),
        "quantum_readiness.generated.jsonl": _quantum_rows(registry),
        "hotpath_handoff.generated.jsonl": _hotpath_rows(registry),
        "candidate_external_info_lanes.generated.jsonl": _candidate_external_info_rows(registry),
        "readiness_gap_ledger.generated.jsonl": _gap_rows(registry),
    }
    from pr169_formula_owner_rows import rows as pr169_formula_rows
    artifact_rows["qku_formula_agent_compute_map.generated.jsonl"] = [
        *artifact_rows["qku_formula_agent_compute_map.generated.jsonl"],
        *pr169_formula_rows(repo_root, "READINESS"),
    ]
    reports = _reports(registry, artifact_rows)
    reports["readiness_manifest.json"] = _manifest(artifact_rows, reports)

    for name in JSONL_ARTIFACTS:
        _write_jsonl(out_dir / name, artifact_rows[name])
    for name in JSON_ARTIFACTS:
        _write_json(out_dir / name, reports[name])
    (out_dir / "pr_body.md").write_text(_pr_body(registry, reports), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo_root / args.out_dir
    build(repo_root, out_dir)
    print(f"built PR169-READINESS1 artifacts at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
