#!/usr/bin/env python3
"""Validate PR169-AGENT-ORCH1 generated orchestration artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import build_pr169_agent_orch1 as builder  # noqa: E402


GENERATED_PREFIX = builder.GENERATED_PREFIX
REGISTRY_REF = builder.REGISTRY_REF
JSONL_ARTIFACTS = builder.JSONL_ARTIFACTS
JSON_REPORTS = builder.JSON_REPORTS
AUTHORITY_FALSE_FIELDS = builder.AUTHORITY_FALSE_FIELDS
LIVE_PATH_FALSE_FIELDS = builder.LIVE_PATH_FALSE_FIELDS
REQUIRED_BASENAME_MAX_CHARS = 56

REQUIRED_STATE_FIELDS = (
    "provider_state",
    "provider_stage",
    "freshness_state",
    "lifecycle_state",
    "activation_state",
    "timing_state",
    "downstream_owner",
    "authority_state",
    "source_authority_state",
    "queue_state",
    "task_state",
    "retry_state",
)

REGISTRY_REQUIRED_FIELDS = (
    "row_id",
    "object_type",
    "object_id",
    "object_version",
    "generated_from",
    "builder",
    "validator",
    "manual_edit_allowed",
    "svc1_ref_or_gap",
    "readiness_ref_or_gap",
    "pretrade_ref_or_gap",
    "mem1_ref_or_gap",
    "pr165_d2_roster_ref_or_gap",
    "pr165_d2_duty_ref_or_gap",
    "owner_action_ref_or_gap",
    "owner_cmd_ref_or_gap",
    "owner_receipt_ref_or_gap",
    "tradeplan_ref_or_gap",
    "pretrade_candidate_ref_or_gap",
    "no_trade_ref_or_gap",
    "qku_refs",
    "formula_refs",
    "algorithm_refs_or_gap",
    "computable_refs_or_gap",
    "exec_state_ref_or_gap",
    "paper_usable_ref_or_gap",
    "adapter_gap_ref_or_gap",
    "dag_ref",
    "node_ref",
    "edge_ref",
    "task_ref",
    "task_env_ref",
    "workflow_ref",
    "stage_ref",
    "handoff_ref_or_gap",
    "receipt_ref_or_gap",
    "task_class",
    "intelligence_lane",
    "tournament_role_ref_or_gap",
    "task_state",
    "queue_state",
    "priority_class",
    "priority_score_or_gap",
    "task_key",
    "dedupe_policy_ref_or_gap",
    "retry_state",
    "retry_count",
    "max_retry_count",
    "blocked_reason_or_none",
    "safe_next_route",
    "responsible_roles",
    "supporting_roles_or_gap",
    "escalation_roles_or_gap",
    "role_resolution_state",
    "role_gap_reason_or_none",
    "agent_pod_or_gap",
    "permission_scope_ref_or_gap",
    "retry_policy_ref_or_gap",
    "quarantine_ref_or_gap",
    "rank_ref_or_gap",
    "tca_ref_or_gap",
    "fdr_ref_or_gap",
    "portfolio_ref_or_gap",
    "capacity_ref_or_gap",
    "champion_ref_or_gap",
    "mem_prior_ref_or_gap",
    "utility_ref_or_gap",
    "scenario_ref_or_gap",
    "calibration_ref_or_gap",
    "notrade_margin_ref_or_gap",
    "quantum_ref_or_gap",
    "memory_scope",
    "memory_is_prior_not_proof",
    "memory_revalidation_required",
    "memory_update_receipt_created",
    "llm_task_ref_or_gap",
    "llm_grounding_ref_or_gap",
    "runtime_llm_call_created",
    "llm_source_truth_created",
    "llm_order_authority_created",
    "llm_profit_claim_created",
    "qstruct_ref_or_gap",
    "quadratic_program_ref_or_gap",
    "qubo_ref_or_gap",
    "bqm_ref_or_gap",
    "cqm_ref_or_gap",
    "ising_ref_or_gap",
    "qaoa_vqe_ref_or_gap",
    "classical_fallback_ref_or_gap",
    "quantum_backend_execution_created",
    "quantum_advantage_claim_created",
    "quantum_order_authority_created",
    "paper_prep_ref_or_gap",
    "hotpath_prep_ref_or_gap",
    "live_dryrun_ref_or_gap",
    "metrics_ref_or_gap",
    "postlaunch_ref_or_gap",
    "plugin_ref_or_gap",
    "qmap_ref_or_gap",
    "allow_ref_or_gap",
    "execution_router_ref_or_gap",
    "connector_ref_or_gap",
    "graph_node_refs_or_gap",
    "graph_edge_refs_or_gap",
    "graph_source_edges_or_gap",
    "graph_value_edges_or_gap",
    "graph_agent_edges_or_gap",
    "graph_validator_edges_or_gap",
    "graph_replay_paper_edges_or_gap",
    "graph_quantum_edges_or_gap",
    "graph_owner_review_edges_or_gap",
    "graph_route_state",
    "provider_state",
    "provider_stage",
    "freshness_state",
    "lifecycle_state",
    "activation_state",
    "timing_state",
    "downstream_owner",
    "authority_state",
    "source_authority_state",
    "projection_consumers",
    "orphan_status",
    "route_gap_reason_or_none",
    "validation_state",
    "fail_closed_reasons",
    "control_plane_only",
    "runtime_orchestration_created",
    "live_critical_path_allowed",
    "heavy_compute_live_path_allowed",
    "source_retrieval_live_path_allowed",
    "llm_call_live_path_allowed",
    "quantum_backend_live_path_allowed",
    "master_plan_compile_live_path_allowed",
    "paper_execution_created",
    "shadow_prep_ref_or_gap",
    "shadow_execution_created",
    "live_execution_created",
    "order_submission_created",
    "direct_venue_submit_created",
    "execution_router_release_created",
    "connector_read_created",
    "connector_write_created",
    "private_cash_read_created",
    "runtime_metrics_created",
    "runtime_plugin_created",
    "profit_claim_created",
    "qtt_sha_authority_created",
    "atomicrows_hash_authority_created",
)

QUEUE_STATES = builder.QUEUE_STATES


class ValidationError(RuntimeError):
    def __init__(self, failures: Sequence[str]) -> None:
        self.failures = tuple(failures)
        super().__init__("\n".join(self.failures))


def _assert(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def _read_jsonl(path: Path, failures: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        failures.append(f"Missing JSONL artifact: {path}")
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"Invalid JSONL row {path}:{line_number}: {exc}")
                continue
            if not isinstance(value, dict):
                failures.append(f"JSONL row is not an object: {path}:{line_number}")
                continue
            rows.append(value)
    return rows


def _read_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"Missing JSON report: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"Invalid JSON report {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        failures.append(f"JSON report is not an object: {path}")
        return {}
    return value


def _load_all(artifact_dir: Path, failures: list[str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    rows = {name: _read_jsonl(artifact_dir / name, failures) for name in JSONL_ARTIFACTS}
    reports = {name: _read_json(artifact_dir / name, failures) for name in JSON_REPORTS}
    return rows, reports


def _validate_filenames(artifact_dir: Path, failures: list[str]) -> None:
    for name in (*JSONL_ARTIFACTS, *JSON_REPORTS):
        base = Path(name).name
        _assert("future_" not in base.lower(), f"Generated filename contains future_: {name}", failures)
        _assert("_hint" not in base.lower(), f"Generated filename contains _hint: {name}", failures)
        _assert(len(base) <= REQUIRED_BASENAME_MAX_CHARS, f"Generated basename too long: {base}", failures)
    if artifact_dir.exists():
        for path in artifact_dir.iterdir():
            if not path.is_file():
                continue
            base = path.name
            _assert("future_" not in base.lower(), f"Generated filename contains future_: {path}", failures)
            _assert("_hint" not in base.lower(), f"Generated filename contains _hint: {path}", failures)


def _validate_registry(registry: Sequence[Mapping[str, Any]], failures: list[str]) -> dict[str, Mapping[str, Any]]:
    _assert(bool(registry), "registry.jsonl has no rows", failures)
    registry_by_id: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(registry, start=1):
        row_id = str(row.get("row_id", ""))
        _assert(bool(row_id), f"Registry row {index} lacks row_id", failures)
        if row_id:
            _assert(row_id not in registry_by_id, f"Duplicate registry row_id: {row_id}", failures)
            registry_by_id[row_id] = row
        for field in REGISTRY_REQUIRED_FIELDS:
            _assert(field in row, f"Registry row {row_id or index} missing field {field}", failures)
        for field in REQUIRED_STATE_FIELDS:
            _assert(bool(row.get(field)), f"Registry row {row_id or index} missing state field {field}", failures)
        _assert(row.get("generated_from") == REGISTRY_REF, f"Registry row {row_id} does not cite canonical registry source", failures)
        _assert(row.get("manual_edit_allowed") is False, f"manual_edit_allowed widened in {row_id}", failures)
        _assert(row.get("control_plane_only") is True, f"control_plane_only not true in {row_id}", failures)
        _assert(row.get("queue_state") in QUEUE_STATES, f"Unknown queue_state in {row_id}: {row.get('queue_state')}", failures)
        _assert(row.get("orphan_status") in {"NOT_ORPHAN", "SCOPED_GAP_ROUTED"}, f"Orphan status failed in {row_id}", failures)
        _assert(bool(row.get("projection_consumers")), f"Projection consumers missing in {row_id}", failures)
        _assert(bool(row.get("downstream_route_refs")), f"Downstream route refs missing in {row_id}", failures)
        _assert(bool(row.get("responsible_roles")), f"Responsible roles missing in {row_id}", failures)
        _assert(row.get("pr165_d2_roster_ref_or_gap") or row.get("role_gap_reason_or_none") == "PR165_D2_GAP", f"PR165-D2 roster/gap missing in {row_id}", failures)
        _assert(row.get("pr165_d2_duty_ref_or_gap") or row.get("role_gap_reason_or_none") == "PR165_D2_GAP", f"PR165-D2 duty/gap missing in {row_id}", failures)
        _assert(row.get("memory_is_prior_not_proof") is True, f"MEM1 prior flag missing in {row_id}", failures)
        _assert(row.get("memory_revalidation_required") is True, f"MEM1 revalidation flag missing in {row_id}", failures)
        _assert(row.get("memory_update_receipt_created") is False, f"Memory update receipt created in {row_id}", failures)
        for field in (*AUTHORITY_FALSE_FIELDS, *LIVE_PATH_FALSE_FIELDS):
            if field in row:
                _assert(row[field] is False, f"{field} widened in {row_id}", failures)
    return registry_by_id


def _validate_projection_derivation(
    rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]],
    registry_by_id: Mapping[str, Mapping[str, Any]],
    failures: list[str],
) -> None:
    for file_name in JSONL_ARTIFACTS:
        rows = rows_by_file[file_name]
        _assert(bool(rows), f"Projection missing rows: {file_name}", failures)
        if file_name == "registry.jsonl":
            continue
        for row in rows:
            row_id = str(row.get("source_registry_row_id") or "")
            _assert(row_id in registry_by_id, f"{file_name} row not derived from registry: {row_id}", failures)
            source = registry_by_id.get(row_id, {})
            for field in ("object_type", "object_id", "task_ref", "projection_file"):
                _assert(row.get(field) == source.get(field), f"{file_name} row {row_id} field {field} diverges from registry", failures)
            _assert(row.get("generated_from") == REGISTRY_REF, f"{file_name} row {row_id} lacks registry generated_from", failures)


def _validate_qku_formula(rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]], failures: list[str]) -> None:
    for file_name in ("qku_tasks.jsonl", "formula_tasks.jsonl", "access_proof.jsonl", "library_receipts.jsonl"):
        for row in rows_by_file[file_name]:
            row_id = row.get("row_id")
            _assert(bool(row.get("stage_profile_ref_or_gap")), f"{file_name} {row_id} missing stage profile", failures)
            _assert(bool(row.get("market_applicability_ref_or_gap")), f"{file_name} {row_id} missing market applicability", failures)
            _assert(bool(row.get("platform_filter_ref_or_gap")), f"{file_name} {row_id} missing platform filter", failures)
            _assert(bool(row.get("agent_duty_filter_ref_or_gap")), f"{file_name} {row_id} missing duty filter", failures)
            _assert(bool(row.get("executability_overlay_ref_or_gap")), f"{file_name} {row_id} missing executability overlay", failures)
            _assert(bool(row.get("context_filter_ref_or_gap")), f"{file_name} {row_id} missing context filter", failures)
            _assert(bool(row.get("mem1_filter_ref_or_gap")), f"{file_name} {row_id} missing MEM1 filter", failures)
            _assert(bool(row.get("selected_qku_refs")), f"{file_name} {row_id} missing selected QKUs", failures)
            _assert(bool(row.get("selected_formula_refs")), f"{file_name} {row_id} missing selected formulas", failures)
            _assert(row.get("full_library_access_used") is False, f"{file_name} {row_id} used full-library default", failures)
            _assert(bool(row.get("library_query_receipt_ref_or_gap")), f"{file_name} {row_id} missing library receipt route", failures)


def _validate_no_trade(rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]], failures: list[str]) -> None:
    for file_name in ("notrade_tasks.jsonl", "var_tune_tasks.jsonl", "stack_tasks.jsonl", "venue_side_tasks.jsonl", "source_refresh_tasks.jsonl", "retest_tasks.jsonl"):
        for row in rows_by_file[file_name]:
            row_id = row.get("row_id")
            _assert(row.get("terminal_no_trade") is False, f"{file_name} {row_id} created terminal no-trade", failures)
            routes = row.get("no_trade_recovery_route_refs") or []
            _assert(len(routes) >= 6, f"{file_name} {row_id} lacks recovery/retest/rotation routes", failures)
            _assert(any("variable" in str(route).lower() for route in routes), f"{file_name} {row_id} lacks variable tuning", failures)
            _assert(any("stack" in str(route).lower() for route in routes), f"{file_name} {row_id} lacks stack challenger", failures)
            _assert(any("venue" in str(route).lower() for route in routes), f"{file_name} {row_id} lacks venue/side rotation", failures)
            _assert(any("source" in str(route).lower() for route in routes), f"{file_name} {row_id} lacks source refresh", failures)
            _assert(any("retest" in str(route).lower() for route in routes), f"{file_name} {row_id} lacks retest route", failures)


def _validate_institutional(rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]], failures: list[str]) -> None:
    files = (
        "rank_tasks.jsonl",
        "tca_tasks.jsonl",
        "fdr_tasks.jsonl",
        "portfolio_tasks.jsonl",
        "capacity_tasks.jsonl",
        "champion_tasks.jsonl",
        "mem_prior_tasks.jsonl",
        "utility_tasks.jsonl",
        "scenario_tasks.jsonl",
        "calibration_tasks.jsonl",
    )
    for file_name in files:
        for row in rows_by_file[file_name]:
            for field in builder.INSTITUTIONAL_REFS:
                _assert(bool(row.get(field)), f"{file_name} {row.get('row_id')} missing institutional field {field}", failures)
            _assert(bool(row.get("quantum_ref_or_gap")), f"{file_name} {row.get('row_id')} missing quantum route", failures)
            _assert(bool(row.get("dag_ref")), f"{file_name} {row.get('row_id')} missing DAG route", failures)


def _validate_quantum(rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]], failures: list[str]) -> None:
    for row in rows_by_file["quantum_tasks.jsonl"]:
        row_id = row.get("row_id")
        for field in (
            "qstruct_ref_or_gap",
            "objective_route_ref_or_gap",
            "variable_route_ref_or_gap",
            "constraint_route_ref_or_gap",
            "penalty_route_ref_or_gap",
            "coefficient_scale_ref_or_gap",
            "quadratic_program_ref_or_gap",
            "qubo_ref_or_gap",
            "bqm_ref_or_gap",
            "cqm_ref_or_gap",
            "ising_ref_or_gap",
            "qaoa_vqe_route_ref_or_gap",
            "classical_fallback_ref_or_gap",
            "interpret_back_map_ref_or_gap",
            "qmap_owner_route_ref_or_gap",
            "paper_route_ref_or_gap",
            "hotpath_route_ref_or_gap",
        ):
            _assert(bool(row.get(field)), f"quantum_tasks {row_id} missing {field}", failures)
        _assert(row.get("quantum_backend_execution_created") is False, f"quantum backend execution in {row_id}", failures)
        _assert(row.get("quantum_advantage_claim_created") is False, f"quantum advantage claim in {row_id}", failures)
        _assert(row.get("quantum_order_authority_created") is False, f"quantum order authority in {row_id}", failures)


def _validate_prep_and_receipts(rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]], failures: list[str]) -> None:
    for row in rows_by_file["paper_prep.jsonl"]:
        row_id = row.get("row_id")
        _assert(bool(row.get("candidate_ref")), f"paper_prep {row_id} missing candidate ref", failures)
        _assert(bool(row.get("qku_formula_task_refs")), f"paper_prep {row_id} missing qku/formula task refs", failures)
        _assert(bool(row.get("risk_tca_task_refs")), f"paper_prep {row_id} missing risk/tca task refs", failures)
        _assert(row.get("paper_execution_created") is False, f"paper_prep {row_id} created paper execution", failures)
    for row in rows_by_file["hotpath_prep.jsonl"]:
        _assert(row.get("runtime_cache_created") is False, f"hotpath_prep {row.get('row_id')} created runtime cache", failures)
        _assert(row.get("fresh_snapshot_required") is True, f"hotpath_prep {row.get('row_id')} missing fresh snapshot requirement", failures)
    for row in rows_by_file["shadow_prep.jsonl"]:
        _assert(row.get("shadow_execution_created") is False, f"shadow_prep {row.get('row_id')} created shadow execution", failures)
        _assert(row.get("live_execution_created") is False, f"shadow_prep {row.get('row_id')} created live execution", failures)
        _assert(bool(row.get("paper_comparison_route_ref_or_gap")), f"shadow_prep {row.get('row_id')} missing paper comparison route", failures)
    for row in rows_by_file["live_prep.jsonl"]:
        _assert(row.get("live_execution_created") is False, f"live_prep {row.get('row_id')} created live execution", failures)
        _assert(row.get("execution_router_release_created") is False, f"live_prep {row.get('row_id')} created router release", failures)
    for file_name in ("task_receipts.jsonl", "decision_receipts.jsonl", "dispute_receipts.jsonl", "escalation_receipts.jsonl", "handoff_receipts.jsonl"):
        for row in rows_by_file[file_name]:
            _assert("CONTRACT" in str(row.get("receipt_class")), f"{file_name} {row.get('row_id')} is not contract-only", failures)
            _assert(row.get("runtime_side_effect_created") is False, f"{file_name} {row.get('row_id')} created runtime side effect", failures)
            _assert(row.get("fake_receipt_created") is False, f"{file_name} {row.get('row_id')} created fake receipt", failures)


def _validate_owner_and_tournament(repo_root: Path, rows_by_file: Mapping[str, Sequence[Mapping[str, Any]]], failures: list[str]) -> None:
    owner_actions = _read_jsonl(repo_root / "docs/master_plan/generated/pr169_svc1/owner_action_requests.generated.jsonl", failures)
    owner_task_actions = {row.get("owner_action_ref_or_gap") for row in rows_by_file["owner_cmd_tasks.jsonl"]}
    upstream_actions = {
        row.get("action_code") or row.get("action_id")
        for row in owner_actions
        if row.get("action_code") or row.get("action_id")
    }
    _assert(upstream_actions <= owner_task_actions, "Not every SVC1 owner action maps to owner_cmd_tasks", failures)
    _assert(len(rows_by_file["chat_tasks.jsonl"]) >= len(builder.PLAIN_ENGLISH_EXAMPLES), "Plain-English route examples missing", failures)
    for row in rows_by_file["owner_cmd_tasks.jsonl"]:
        _assert(row.get("owner_request_authority") is True, f"owner_cmd {row.get('row_id')} lacks request authority", failures)
        _assert(row.get("direct_venue_submit_authority") is False, f"owner_cmd {row.get('row_id')} gained direct submit authority", failures)
        _assert(row.get("execution_router_release_authority") is False, f"owner_cmd {row.get('row_id')} gained router release authority", failures)
    for row in rows_by_file["tournament_tasks.jsonl"]:
        roles = set(row.get("tournament_roles") or [])
        _assert(set(builder.TOURNAMENT_ROLES) <= roles, f"tournament task {row.get('row_id')} missing roles", failures)
        _assert(row.get("single_agent_self_authorization_allowed") is False, f"tournament task {row.get('row_id')} allows self-authorization", failures)


def _validate_reports(reports: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    manifest = reports.get("manifest.json") or {}
    artifact_files = {entry.get("file") for entry in manifest.get("artifact_manifest", [])}
    _assert(set(JSONL_ARTIFACTS) <= artifact_files, "Manifest does not map every JSONL artifact", failures)
    _assert(set(JSON_REPORTS) <= artifact_files, "Manifest does not map every JSON report", failures)
    _assert(manifest.get("canonical_registry_ref") == REGISTRY_REF, "Manifest canonical registry ref mismatch", failures)
    quality = reports.get("quality.report.json") or {}
    superseded = quality.get("superseded_content_check") or {}
    _assert(superseded.get("superseded_uploaded_text_preserved") is False, "Superseded text preservation flag failed", failures)
    _assert(superseded.get("superseded_uploaded_text_reference_count") == 0, "Superseded text reference count is nonzero", failures)
    for name, report in reports.items():
        _assert(report.get("pass") is not False, f"Report did not pass: {name}", failures)
        _assert(not report.get("fail_closed_reasons"), f"Report has fail_closed_reasons: {name}", failures)
        for field, count in (report.get("authority_true_counts") or {}).items():
            _assert(count == 0, f"{name} authority true count nonzero for {field}: {count}", failures)


def _validate_resolver_static(repo_root: Path, failures: list[str]) -> None:
    resolver_path = repo_root / "src/qtt/agents/pr169_agent_orch1_resolvers.py"
    _assert(resolver_path.exists(), "Resolver/API contract module missing", failures)
    if not resolver_path.exists():
        return
    text = resolver_path.read_text(encoding="utf-8")
    forbidden_fragments = (
        "pr169_svc1",
        "pr169_pretrade1",
        "pr169_readiness1",
        "pr168_mem1",
        "connector_read",
        "submit_order",
        "open_network",
        "llm_provider",
    )
    for fragment in forbidden_fragments:
        _assert(fragment not in text, f"Resolver contains forbidden runtime/upstream fragment: {fragment}", failures)
    _assert(".rglob(" not in text, "Resolver uses recursive raw scan", failures)
    _assert("requests." not in text, "Resolver appears to use network requests", failures)


def validate(repo_root: Path, artifact_dir: Path) -> None:
    root = repo_root.resolve()
    output_dir = root / artifact_dir
    failures: list[str] = []
    _assert(output_dir.exists(), f"Artifact directory missing: {output_dir}", failures)
    _validate_filenames(output_dir, failures)
    rows_by_file, reports = _load_all(output_dir, failures)
    registry_by_id = _validate_registry(rows_by_file.get("registry.jsonl", []), failures)
    _validate_projection_derivation(rows_by_file, registry_by_id, failures)
    _validate_qku_formula(rows_by_file, failures)
    _validate_no_trade(rows_by_file, failures)
    _validate_institutional(rows_by_file, failures)
    _validate_quantum(rows_by_file, failures)
    _validate_prep_and_receipts(rows_by_file, failures)
    _validate_owner_and_tournament(root, rows_by_file, failures)
    _validate_reports(reports, failures)
    _validate_resolver_static(root, failures)
    if failures:
        raise ValidationError(failures)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    validate(args.repo_root, args.artifact_dir)
    print("PR169-AGENT-ORCH1 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
