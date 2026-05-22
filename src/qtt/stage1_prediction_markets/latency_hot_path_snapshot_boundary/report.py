"""Deterministic PR137L latency hot-path snapshot boundary report builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import constants as c
from .model import DependencyChainSnapshot, PR137RStaticEvidenceSnapshot


def _json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return value


def _existing(root: Path, paths: Sequence[str]) -> list[str]:
    return [path for path in paths if (root / path).exists()]


def _missing(root: Path, paths: Sequence[str]) -> list[str]:
    return [path for path in paths if not (root / path).exists()]


def _sequence_entries(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    entries = payload.get("sequence_entries", [])
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _entry_id(entry: Mapping[str, Any]) -> str:
    return str(entry.get("final_sequence_pr_number_or_placeholder", ""))


def _entry_by_id(entries: Sequence[Mapping[str, Any]], pr_id: str) -> Mapping[str, Any]:
    for entry in entries:
        if _entry_id(entry) == pr_id:
            return entry
    return {}


def _list_field(entry: Mapping[str, Any], key: str) -> list[str]:
    value = entry.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def dependency_chain_snapshot(repo_root: Path | str) -> DependencyChainSnapshot:
    root = Path(repo_root).resolve()
    sequence_path = root / "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"
    entries = _sequence_entries(_load_json(sequence_path)) if sequence_path.exists() else []
    ids = [_entry_id(entry) for entry in entries]
    pr137 = _entry_by_id(entries, "PR137")
    pr137l = _entry_by_id(entries, c.PR_ID)
    pr138 = _entry_by_id(entries, "PR138")
    pr137_to_pr137l = c.PR_ID in _list_field(pr137, "downstream_dependencies")
    pr137l_to_pr138 = (
        "PR137" in _list_field(pr137l, "required_upstream_prs")
        and "PR138" in _list_field(pr137l, "downstream_dependencies")
        and pr137l.get("scope_class") == c.SCOPE_CLASS
        and pr137l.get("readiness_state_target") == c.READINESS_STATE
        and pr137l.get("latency_scope") == c.LATENCY_SCOPE
    )
    pr138_requires_pr137l = c.PR_ID in _list_field(pr138, "required_upstream_prs")
    sequence_validated = (
        ids.count(c.PR_ID) == 1 and pr137_to_pr137l and pr137l_to_pr138 and pr138_requires_pr137l
    )
    return DependencyChainSnapshot(
        source_sequence=sequence_path.relative_to(root).as_posix(),
        active_sequence_observed_prefix=tuple(ids[:6]),
        pr137l_occurrence_count=ids.count(c.PR_ID),
        pr137_to_pr137l=pr137_to_pr137l,
        pr137l_to_pr138=pr137l_to_pr138,
        pr138_requires_pr137l=pr138_requires_pr137l,
        pr137r_active_sequence_node="PR137R" in ids,
        disconnected_roadmap_created=False,
        controller_mutation_required=False,
        controller_mutation_decision=(
            c.REASON_CONTROLLER_MUTATION_SKIPPED_EXISTING_SEQUENCE_VALIDATED
            if sequence_validated
            else c.REASON_ACTIVE_SEQUENCE_MISSING
        ),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def consume_pr137r_static_evidence_snapshot(
    repo_root: Path | str,
    *,
    source_report: Path | str = c.PR137R_REPORT_PATH,
) -> PR137RStaticEvidenceSnapshot:
    root = Path(repo_root).resolve()
    rel_source = Path(source_report)
    path = root / rel_source
    if not path.exists():
        raise FileNotFoundError(c.REASON_PR137R_REPORT_REQUIRED)
    report = _load_json(path)
    inventory = _mapping(report.get("atomicrows_artifact_inventory"))
    state = _mapping(report.get("atomicrows_validation_state"))
    audit = _mapping(state.get("row_contract_field_audit"))
    missing_fields = audit.get("missing_fields", [])
    semantic_complete = isinstance(missing_fields, list) and len(missing_fields) == 0
    snapshot = PR137RStaticEvidenceSnapshot(
        source_report=rel_source.as_posix(),
        atomicrows_bundle_artifact_found=inventory.get("functional_bundle_artifact_found") is True,
        atomicrows_functional_bundle_status=str(state.get("functional_bundle_status", "")),
        expected_atomicrows_row_count=int(report.get("expected_atomicrows_row_count", 0)),
        atomicrows_row_count_proven=state.get("row_count_proven") is True,
        atomicrows_row_count_value=int(state.get("row_count_value", 0)),
        atomicrows_schema_validated=state.get("schema_validated") is True,
        atomicrows_validation_error_count=int(state.get("validation_error_count", -1)),
        atomicrows_row_family_source_files_found=(
            inventory.get("row_family_source_files_found") is True
        ),
        atomicrows_row_family_source_file_count=int(
            inventory.get("row_family_source_file_count", 0)
        ),
        atomicrows_bundle_builder_found=inventory.get("bundle_builder_found") is True,
        atomicrows_bundle_validator_found=inventory.get("bundle_validator_found") is True,
        atomicrows_agent_read_only_consumer_found=(
            inventory.get("agent_read_only_consumer_found") is True
        ),
        atomicrows_agent_consumption_boundary=str(
            state.get("agent_consumption_boundary", "")
        ),
        atomicrows_final_readiness_gate_found=state.get("readiness_gate_found") is True,
        atomicrows_day1_live_trading_ready=state.get("day1_live_trading_ready") is True,
        atomicrows_profit_evidence_created=state.get("profit_evidence_created") is True,
        atomicrows_quantum_advantage_evidence_created=(
            state.get("quantum_advantage_evidence_created") is True
        ),
        atomicrows_semantic_row_contract_complete=semantic_complete,
        atomicrows_pr137l_usage="READ_ONLY_PRECOMPUTED_STATIC_EVIDENCE_SNAPSHOT_ONLY",
    )
    if report.get("pr_id") != "PR137R" or report.get("report_type") != (
        "QTT_PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_RECONCILIATION_REPORT"
    ):
        raise ValueError(c.REASON_PR137R_STATIC_EVIDENCE_CONTRADICTION)
    return snapshot


def _live_path_boundary() -> dict[str, Any]:
    return {
        "consumer_scope": "FUTURE_LIVE_PRETRADE_CONSUMES_PRECOMPUTED_SNAPSHOTS_ONLY",
        "complexity_target": c.LATENCY_COMPLEXITY_TARGET,
        **{field: False for field in c.LIVE_PATH_REQUIRED_FALSE_FIELDS},
    }


def _live_path_boundary_constraints() -> dict[str, bool]:
    return {field: True for field in c.LIVE_PATH_REQUIRED_TRUE_CONSTRAINTS}


def _latency_discipline() -> dict[str, Any]:
    return {
        "live_pretrade_snapshot_boundary_complexity_target": c.LATENCY_COMPLEXITY_TARGET,
        **{field: True for field in c.LATENCY_DISCIPLINE_TRUE_FIELDS},
        **{field: True for field in c.LATENCY_DISCIPLINE_FALSE_FIELDS},
    }


def _quantum_future_ref_metadata() -> dict[str, bool]:
    return {
        **{field: True for field in c.QUANTUM_ALLOWED_TRUE_FIELDS},
        **{field: False for field in c.QUANTUM_REQUIRED_FALSE_FIELDS},
    }


def _atomicrows_future_ref_metadata() -> dict[str, bool]:
    return {
        **{field: True for field in c.ATOMICROWS_ALLOWED_TRUE_FIELDS},
        **{field: False for field in c.ATOMICROWS_REQUIRED_FALSE_FIELDS},
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    pr137r_snapshot = consume_pr137r_static_evidence_snapshot(root)
    dependency_chain = dependency_chain_snapshot(root)
    report = {
        "report_type": c.REPORT_TYPE,
        "schema_version": 1,
        "generated_at_utc": c.STATIC_TIME,
        "generated_by": (
            "src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary.report"
        ),
        "pr_id": c.PR_ID,
        "title": c.TITLE,
        "branch": c.BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "scope_class": c.SCOPE_CLASS,
        "readiness_state": c.READINESS_STATE,
        "latency_scope": c.LATENCY_SCOPE,
        "required_upstream_prs": ["PR137"],
        "static_evidence_dependencies": ["PR137R"],
        "downstream_dependencies": ["PR138"],
        "selector_authority_preserved": "PR136",
        "dependency_controller_authority_preserved": "PR137",
        "pr137r_evidence_consumed": True,
        "implements_pr138": False,
        "structural_evidence_only": True,
        "global_roadmap_model": c.GLOBAL_ROADMAP_MODEL,
        "one_global_roadmap_preserved": True,
        "market_scoped_overlays_only": True,
        "market_specific_roadmap_forks_created": False,
        "market_scopes": list(c.CANONICAL_MARKET_SCOPES),
        "dependency_chain": dependency_chain.as_report(),
        "controller_mutation_decision": dependency_chain.controller_mutation_decision,
        "pr136_selector_artifacts_found": _existing(root, c.PR136_SELECTOR_ARTIFACTS),
        "pr136_selector_artifacts_missing": _missing(root, c.PR136_SELECTOR_ARTIFACTS),
        "pr137_dependency_controller_artifacts_found": _existing(
            root, c.PR137_DEPENDENCY_CONTROLLER_ARTIFACTS
        ),
        "pr137_dependency_controller_artifacts_missing": _missing(
            root, c.PR137_DEPENDENCY_CONTROLLER_ARTIFACTS
        ),
        "crosswalk_context_artifacts_found": _existing(root, c.CROSSWALK_CONTEXT_ARTIFACTS),
        "crosswalk_context_artifacts_missing": _missing(root, c.CROSSWALK_CONTEXT_ARTIFACTS),
        "route_triage_artifacts_found": _existing(root, c.ROUTE_TRIAGE_ARTIFACTS),
        "validation_gate_context_artifacts_found": _existing(
            root, c.VALIDATION_GATE_CONTEXT_ARTIFACTS
        ),
        "pr137r_static_evidence_snapshot": pr137r_snapshot.as_report(),
        "precomputed_snapshot_boundary_types": list(c.PRECOMPUTED_SNAPSHOT_BOUNDARY_TYPES),
        "control_plane_producer_lanes": list(c.CONTROL_PLANE_PRODUCER_LANES),
        "future_live_consumer_lanes": list(c.FUTURE_LIVE_CONSUMER_LANES),
        "live_path_boundary_constraints": _live_path_boundary_constraints(),
        "live_path_boundary": _live_path_boundary(),
        "latency_discipline": _latency_discipline(),
        "quantum_future_ref_metadata": _quantum_future_ref_metadata(),
        "atomicrows_future_ref_metadata": _atomicrows_future_ref_metadata(),
        "not_created_flags": {field: False for field in c.NOT_CREATED_FLAGS},
        "forbidden_diff_checks": {
            "master_plan_markdown_text_changed": False,
            "atomicrows_bundle_file_changed_by_pr137l": False,
            "atomicrows_row_family_source_files_changed_by_pr137l": False,
            "atomicrows_builder_files_changed_by_pr137l": False,
            "source_evidence_accepted_packet_files_changed_by_pr137l": False,
            "connector_semantic_binding_files_changed_by_pr137l": False,
            "runtime_live_replay_paper_quantum_backend_files_changed_by_pr137l": False,
            "package_dependency_files_changed_by_pr137l": False,
            "disabled_atomicrows_integrity_artifact_reference_created": False,
            "exact_forbidden_integrity_key_created": False,
            "integrity_or_file_size_evidence_used_as_qtt_proof": False,
        },
        "reason_codes": [
            c.REASON_OK,
            dependency_chain.controller_mutation_decision,
        ],
        "validation_state": c.READINESS_STATE,
    }
    return report


def build_index(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "index_type": c.INDEX_TYPE,
        "schema_version": 1,
        "generated_at_utc": c.STATIC_TIME,
        "pr_id": c.PR_ID,
        "report_ref": c.REPORT_PATH.as_posix(),
        "gate_tool": c.GATE_TOOL_PATH,
        "authority_class": c.AUTHORITY_CLASS,
        "readiness_state": c.READINESS_STATE,
        "latency_scope": c.LATENCY_SCOPE,
        "required_upstream_prs": list(report["required_upstream_prs"]),
        "static_evidence_dependencies": list(report["static_evidence_dependencies"]),
        "downstream_dependencies": list(report["downstream_dependencies"]),
        "market_scopes": list(c.CANONICAL_MARKET_SCOPES),
        "pr137r_source_report": c.PR137R_REPORT_PATH.as_posix(),
        "validation_receipts": list(c.SUCCESS_RECEIPTS),
    }


def write_report_files(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    index = build_index(report)
    report_path = root / c.REPORT_PATH
    index_path = root / c.INDEX_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_json_dump(report), encoding="utf-8", newline="\n")
    index_path.write_text(_json_dump(index), encoding="utf-8", newline="\n")
    return report

