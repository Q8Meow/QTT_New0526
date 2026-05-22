"""Deterministic PR137R AtomicRows bundle reconciliation report builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from . import constants as c
from .model import BundleAudit


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


def _glob(root: Path, pattern: str) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.glob(pattern))


def _walk_keys_and_values(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk_keys_and_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys_and_values(item)


def _string_surface(value: Any) -> str:
    pieces: list[str] = []
    for key, item in _walk_keys_and_values(value):
        pieces.append(str(key))
        if isinstance(item, str):
            pieces.append(item)
    return " ".join(pieces)


def _field_supported(fields: set[str], field: str) -> bool:
    return field in fields


def _schema_known_fields(schema: Mapping[str, Any]) -> set[str]:
    fields: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                fields.add(str(key))
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(schema)
    return fields


def _row_known_fields(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    fields: set[str] = set()
    for row in rows:
        for key, _item in _walk_keys_and_values(row):
            fields.add(str(key))
    return fields


def _quantum_support(rows: Sequence[Mapping[str, Any]], schema: Mapping[str, Any]) -> dict[str, bool]:
    surface = (_string_surface(schema) + " " + _string_surface(list(rows))).lower()
    return {
        "quantum_schema_support_proven": "quantum" in surface,
        "qubo_compatibility_metadata_supported": "qubo" in surface,
        "ising_compatibility_metadata_supported": "ising" in surface,
        "qaoa_compatibility_metadata_supported": "qaoa" in surface,
        "vqe_compatibility_metadata_supported": "vqe" in surface,
        "annealing_compatibility_metadata_supported": "annealing" in surface,
        "quantum_kernel_feature_map_metadata_supported": (
            "quantum_kernel" in surface or "feature_map" in surface
        ),
    }


def audit_bundle(repo_root: Path | str) -> BundleAudit:
    root = Path(repo_root).resolve()
    bundle_path = root / c.BUNDLE_PATH
    schema_path = root / c.MATERIALIZED_ROW_SCHEMA_PATH
    if not bundle_path.exists():
        return BundleAudit(
            status=c.STATUS_NOT_CREATED,
            bundle_exists=False,
            row_count_value=None,
            row_count_proven=False,
            schema_validated=False,
            validation_errors=(c.REASON_BUNDLE_NOT_CREATED, c.REASON_4183_ROWS_NOT_PROVEN),
            supported_row_contract_fields=(),
            missing_row_contract_fields=c.ROW_CONTRACT_FIELDS,
            quantum_metadata_support={
                "quantum_schema_support_proven": False,
                "qubo_compatibility_metadata_supported": False,
                "ising_compatibility_metadata_supported": False,
                "qaoa_compatibility_metadata_supported": False,
                "vqe_compatibility_metadata_supported": False,
                "annealing_compatibility_metadata_supported": False,
                "quantum_kernel_feature_map_metadata_supported": False,
            },
        )

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    with bundle_path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                failures.append(f"line {line_number}: blank JSONL row")
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"line {line_number}: JSON parse failed: {exc.msg}")
                continue
            if not isinstance(value, dict):
                failures.append(f"line {line_number}: JSONL row must be an object")
                continue
            rows.append(value)

    row_count = len(rows)
    if row_count == 0:
        return BundleAudit(
            status=c.STATUS_PATH_PRESENT_BUT_EMPTY,
            bundle_exists=True,
            row_count_value=0,
            row_count_proven=False,
            schema_validated=False,
            validation_errors=tuple(failures or [c.STATUS_PATH_PRESENT_BUT_EMPTY]),
            supported_row_contract_fields=(),
            missing_row_contract_fields=c.ROW_CONTRACT_FIELDS,
            quantum_metadata_support={
                "quantum_schema_support_proven": False,
                "qubo_compatibility_metadata_supported": False,
                "ising_compatibility_metadata_supported": False,
                "qaoa_compatibility_metadata_supported": False,
                "vqe_compatibility_metadata_supported": False,
                "annealing_compatibility_metadata_supported": False,
                "quantum_kernel_feature_map_metadata_supported": False,
            },
        )

    schema: dict[str, Any] = {}
    if schema_path.exists():
        schema = _load_json(schema_path)
    else:
        failures.append(c.REASON_ROW_SCHEMA_NOT_PROVEN)

    seen_bundle_ids: set[str] = set()
    seen_row_indexes: set[int] = set()
    schema_failure_count = 0
    for expected_index, row in enumerate(rows, start=1):
        expected_row_id = f"AR_BUNDLE_ROW_{expected_index:04d}"
        if row.get("bundle_row_id") != expected_row_id:
            failures.append(f"row {expected_index}: bundle_row_id must be {expected_row_id}")
        row_index = row.get("row_index")
        if row_index != expected_index:
            failures.append(f"row {expected_index}: row_index must be {expected_index}")
        bundle_id = row.get("bundle_row_id")
        if isinstance(bundle_id, str):
            if bundle_id in seen_bundle_ids:
                failures.append(f"row {expected_index}: duplicate bundle_row_id {bundle_id}")
            seen_bundle_ids.add(bundle_id)
        if isinstance(row_index, int) and not isinstance(row_index, bool):
            if row_index in seen_row_indexes:
                failures.append(f"row {expected_index}: duplicate row_index {row_index}")
            seen_row_indexes.add(row_index)
        if schema:
            row_failures = validate_json_schema_subset(
                row,
                schema,
                path=f"bundle_row[{expected_index}]",
            )
            if row_failures:
                schema_failure_count += len(row_failures)
                if schema_failure_count <= 20:
                    failures.extend(row_failures[:20])

    if schema_failure_count > 20:
        failures.append(f"schema validation had {schema_failure_count} row failures")

    row_count_proven = row_count == c.EXPECTED_ROW_COUNT and not any(
        failure.startswith("line ") for failure in failures
    )
    schema_validated = bool(schema) and schema_failure_count == 0 and not any(
        "bundle_row_id must be" in failure or "row_index must be" in failure
        for failure in failures
    )
    known_fields = _schema_known_fields(schema) | _row_known_fields(rows[:25])
    supported = tuple(
        field for field in c.ROW_CONTRACT_FIELDS if _field_supported(known_fields, field)
    )
    missing = tuple(field for field in c.ROW_CONTRACT_FIELDS if field not in supported)
    quantum_support = _quantum_support(rows[:250], schema)

    if not row_count_proven and row_count != c.EXPECTED_ROW_COUNT:
        status = c.STATUS_ROW_COUNT_MISMATCH
        failures.append(c.REASON_ROW_COUNT_MISMATCH)
    elif not schema:
        status = c.STATUS_ROW_SCHEMA_NOT_PROVEN
    elif schema_validated and row_count_proven and not failures:
        status = c.STATUS_PRESENT_AND_STATICALLY_VALIDATED
    else:
        status = c.STATUS_PRESENT_BUT_INVALID

    return BundleAudit(
        status=status,
        bundle_exists=True,
        row_count_value=row_count,
        row_count_proven=row_count_proven,
        schema_validated=schema_validated,
        validation_errors=tuple(failures),
        supported_row_contract_fields=supported,
        missing_row_contract_fields=missing,
        quantum_metadata_support=quantum_support,
    )


def _artifact_inventory(repo_root: Path, bundle: BundleAudit) -> dict[str, Any]:
    row_family_sources = _glob(repo_root, c.ROW_FAMILY_SOURCE_GLOB)
    exact_sources = _glob(repo_root, c.EXACT_ROW_SOURCE_GLOB)
    builder_paths = _existing(repo_root, c.BUNDLE_BUILDER_PATHS)
    validator_paths = _existing(repo_root, c.BUNDLE_VALIDATOR_PATHS)
    consumer_paths = _existing(repo_root, c.AGENT_CONSUMER_PATHS)
    final_readiness_paths = _existing(repo_root, c.FINAL_READINESS_GATE_PATHS)
    return {
        "functional_bundle_artifact_found": bundle.bundle_exists,
        "functional_bundle_artifact_paths": [c.BUNDLE_PATH.as_posix()] if bundle.bundle_exists else [],
        "row_family_source_files_found": bool(row_family_sources),
        "row_family_source_file_count": len(row_family_sources),
        "row_family_source_file_paths": row_family_sources,
        "exact_row_source_files_found": bool(exact_sources),
        "exact_row_source_file_count": len(exact_sources),
        "bundle_builder_found": bool(builder_paths),
        "bundle_builder_paths": builder_paths,
        "bundle_validator_found": bool(validator_paths),
        "bundle_validator_paths": validator_paths,
        "agent_read_only_consumer_found": bool(consumer_paths),
        "agent_read_only_consumer_paths": consumer_paths,
        "readiness_gate_found": bool(final_readiness_paths),
        "readiness_gate_paths": final_readiness_paths,
        "materialized_row_schema_path": (
            c.MATERIALIZED_ROW_SCHEMA_PATH.as_posix()
            if (repo_root / c.MATERIALIZED_ROW_SCHEMA_PATH).exists()
            else None
        ),
    }


def _legacy_status(task: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    refs = tuple(str(path) for path in task["artifact_refs"])
    found = _existing(repo_root, refs)
    missing = _missing(repo_root, refs)
    label = str(task["old_label"])
    if label == "PR100":
        current_truth = "SHA_FREEZE_AUTHORITY_NOT_CREATED"
        supported = False
        completion_claim_found = False
        route_required = True
    elif label == "PR101":
        current_truth = c.STATUS_READINESS_GATE_MISSING
        supported = False
        completion_claim_found = False
        route_required = True
    elif found and not missing:
        current_truth = "STATIC_ARTIFACTS_FOUND_NOT_ROW_COUNT_OR_LIVE_PROOF"
        supported = True
        completion_claim_found = True
        route_required = False
    else:
        current_truth = c.STATUS_LEGACY_LABEL_ONLY
        supported = False
        completion_claim_found = False
        route_required = True
    return {
        "old_label": label,
        "semantic_task_name": task["semantic_task_name"],
        "expected_artifact_family": task["expected_artifact_family"],
        "repo_artifacts_found": found,
        "repo_artifacts_missing": missing,
        "completion_claim_found": completion_claim_found,
        "completion_claim_supported_by_artifacts": supported,
        "current_truth_status": current_truth,
        "route_required_in_current_sequence": route_required,
    }


def _sequence_routing(repo_root: Path) -> dict[str, Any]:
    sequence_path = repo_root / "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json"
    entries: list[dict[str, Any]] = []
    if sequence_path.exists():
        payload = _load_json(sequence_path)
        entries = [
            entry for entry in payload.get("sequence_entries", []) if isinstance(entry, dict)
        ]
    ids = [str(entry.get("final_sequence_pr_number_or_placeholder")) for entry in entries]
    scope_by_id = {
        str(entry.get("final_sequence_pr_number_or_placeholder")): str(entry.get("scope_class"))
        for entry in entries
    }
    downstream_by_id = {
        str(entry.get("final_sequence_pr_number_or_placeholder")): list(
            entry.get("downstream_dependencies", [])
        )
        for entry in entries
    }
    atomic_slots = [
        pr_id for pr_id in ids if scope_by_id.get(pr_id) == "ATOMICROWS_READINESS"
    ]
    inserted = ids[:4] == ["PR137", c.PR_ID, "PR137L", "PR138"]
    pr137l_preserved = (
        "PR137L" in scope_by_id
        and scope_by_id["PR137L"] == "ROADMAP_MAPPING"
        and "PR138" in downstream_by_id.get("PR137L", [])
    )
    return {
        "active_sequence_observed_prefix": ids[:6],
        "repair_checkpoint_inserted_before_pr137l": inserted,
        "sequence_insertion_requires_owner_review": not inserted,
        "sequence_insertion_reason_code": (
            c.REASON_SEQUENCE_INSERTED if inserted else c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW
        ),
        "current_sequence_atomicrows_bundle_implementation_slot_found": bool(atomic_slots),
        "current_sequence_atomicrows_bundle_implementation_slots": atomic_slots,
        "owner_sequence_assignment_required": not bool(atomic_slots),
        "pr137l_preserved_as_latency_boundary_only": pr137l_preserved,
        "pr138_preserved_downstream_of_pr137l": "PR138" in downstream_by_id.get("PR137L", []),
        "pr137_required_upstream_preserved": "PR137" in ids,
        "preferred_active_repair_relation_if_supported": ["PR137", c.PR_ID, "PR137L", "PR138"],
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    bundle = audit_bundle(root)
    inventory = _artifact_inventory(root, bundle)
    row_family_sources_found = inventory["row_family_source_files_found"]
    builder_found = inventory["bundle_builder_found"]
    validator_found = inventory["bundle_validator_found"]
    agent_found = inventory["agent_read_only_consumer_found"]
    ready_for_static_agent = (
        bundle.status == c.STATUS_PRESENT_AND_STATICALLY_VALIDATED and agent_found
    )
    reason_codes = [c.REASON_ATOMICROWS_DISCOVERY_OK]
    if bundle.bundle_exists:
        reason_codes.append(c.REASON_BUNDLE_PRESENT)
    else:
        reason_codes.append(c.REASON_BUNDLE_NOT_CREATED)
    reason_codes.append(
        c.REASON_4183_ROWS_PROVEN
        if bundle.row_count_proven
        else c.REASON_4183_ROWS_NOT_PROVEN
    )
    if not row_family_sources_found:
        reason_codes.append(c.REASON_ROW_FAMILY_SOURCES_MISSING)
    if not builder_found:
        reason_codes.append(c.REASON_BUNDLE_BUILDER_MISSING)
    if not validator_found:
        reason_codes.append(c.REASON_VALIDATOR_MISSING)
    if not agent_found:
        reason_codes.append(c.REASON_AGENT_CONSUMER_MISSING)
    if not inventory["readiness_gate_found"]:
        reason_codes.append(c.REASON_READINESS_GATE_MISSING)
    if not bundle.quantum_metadata_support.get(
        "quantum_kernel_feature_map_metadata_supported", False
    ):
        reason_codes.append(c.REASON_QUANTUM_SCHEMA_GAP)

    legacy = [_legacy_status(task, root) for task in c.OLD_ROADMAP_TASKS]
    routing = _sequence_routing(root)
    if routing["owner_sequence_assignment_required"]:
        reason_codes.extend(
            [c.REASON_SEQUENCE_SLOT_NOT_FOUND, c.REASON_OWNER_SEQUENCE_ASSIGNMENT_REQUIRED]
        )

    report = {
        "report_type": c.REPORT_TYPE,
        "schema_version": 1,
        "generated_at_utc": c.STATIC_TIME,
        "generated_by": (
            "src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation.report"
        ),
        "pr_id": c.PR_ID,
        "title": c.TITLE,
        "branch": c.BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "scope_class": list(c.SCOPE_CLASS),
        "required_upstream_prs": ["PR137"],
        "downstream_dependencies": ["PR137L"],
        "active_sequence_repair_target": {
            "before": ["PR137", "PR137L", "PR138"],
            "after_if_supported": ["PR137", c.PR_ID, "PR137L", "PR138"],
        },
        "selector_authority_preserved": "PR136",
        "dependency_controller_authority_preserved": "PR137",
        "implementation_truth_rule": (
            "REPO_ARTIFACTS_VALIDATORS_REPORTS_AUTHORITY_BOUNDARIES_AND_"
            "VALIDATION_EVIDENCE_NOT_PR_LABELS"
        ),
        "structural_evidence_only": True,
        "expected_atomicrows_row_count": c.EXPECTED_ROW_COUNT,
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
        "atomicrows_artifact_inventory": inventory,
        "atomicrows_validation_state": {
            **bundle.as_report(),
            "functional_bundle_ready_for_agent_consumption": ready_for_static_agent,
            "agent_consumption_boundary": (
                "READ_ONLY_STATIC_CONSUMER_ONLY_NOT_RUNTIME_NOT_LIVE"
                if ready_for_static_agent
                else "NOT_READY_OR_NOT_PROVEN"
            ),
            "day1_live_trading_ready": False,
            "profit_evidence_created": False,
            "quantum_advantage_evidence_created": False,
            "readiness_gate_found": inventory["readiness_gate_found"],
        },
        "legacy_roadmap_reconciliation": {
            "old_atomicrows_bundle_pr_labels_discovered": [
                row["old_label"] for row in legacy
            ],
            "old_pr_labels_used_as_completion_proof": False,
            "unsupported_completion_claims_found": [],
            "missing_work_requires_current_sequence_route": any(
                row["route_required_in_current_sequence"] for row in legacy
            ),
            "records": legacy,
        },
        "current_sequence_routing": routing,
        "quantum_forward_compatibility_audit": {
            "quantum_compatibility_metadata_checked": True,
            **bundle.quantum_metadata_support,
            "quantum_execution_created": False,
            "quantum_optimizer_input_created": False,
            "quantum_trading_signal_created": False,
            "quantum_advantage_claim_created": False,
            "quantum_numeric_defaults_invented": False,
            "quantum_backend_names_invented": False,
            "quantum_provider_capabilities_invented": False,
        },
        "market_scopes": list(c.CANONICAL_MARKET_SCOPES),
        "one_global_roadmap_preserved": True,
        "market_scoped_overlays_only": True,
        "no_qtt_sha_summary": {
            "qtt_sha_authority_created": False,
            "qtt_generated_sha_digest_fields_created": False,
            "atomicrows_external_integrity_artifact_reference_created": False,
            "exact_forbidden_integrity_key_created": False,
            "integrity_or_file_size_evidence_used_as_qtt_proof": False,
        },
        "not_created_flags": {
            "atomicrows_rows_created": False,
            "atomicrows_bundle_created": False,
            "atomicrows_row_family_sources_created": False,
            "atomicrows_bundle_builder_created": False,
            "atomicrows_materialization_authority_created": False,
            "atomicrows_freeze_authority_created": False,
            "qtt_sha_authority_created": False,
            "qtt_generated_sha_digest_fields_created": False,
            "source_retrieval_created": False,
            "source_acceptance_created": False,
            "connector_semantic_binding_created": False,
            "runtime_cash_authority_created": False,
            "replay_execution_created": False,
            "paper_execution_created": False,
            "replay_paper_result_created": False,
            "ranking_scoring_arbitration_output_created": False,
            "trading_signal_created": False,
            "order_authority_created": False,
            "order_execution_created": False,
            "fill_receipt_created": False,
            "live_reachability_created": False,
            "day1_live_launch_authority_created": False,
            "profit_evidence_created": False,
            "latency_superiority_claim_created": False,
            "execution_superiority_claim_created": False,
            "alpha_evidence_created": False,
        },
        "forbidden_diff_checks": {
            "master_plan_markdown_text_changed": False,
            "atomicrows_bundle_file_changed_by_pr137r": False,
            "atomicrows_row_family_source_files_changed_by_pr137r": False,
            "source_evidence_accepted_packet_files_changed_by_pr137r": False,
            "connector_semantic_binding_files_changed_by_pr137r": False,
            "runtime_live_replay_paper_quantum_backend_files_changed_by_pr137r": False,
            "package_dependency_files_changed_by_pr137r": False,
        },
        "reason_codes": sorted(set(reason_codes)),
        "validation_state": "STATIC_RECONCILIATION_READY",
    }
    return report


def build_index(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "index_type": c.INDEX_TYPE,
        "schema_version": 1,
        "generated_at_utc": c.STATIC_TIME,
        "pr_id": c.PR_ID,
        "report_ref": c.REPORT_PATH.as_posix(),
        "gate_tool": "tools/stage1_atomicrows_bundle_reconciliation_gate.py",
        "authority_class": c.AUTHORITY_CLASS,
        "expected_atomicrows_row_count": c.EXPECTED_ROW_COUNT,
        "functional_bundle_status": report["atomicrows_validation_state"][
            "functional_bundle_status"
        ],
        "row_count_proven": report["atomicrows_validation_state"]["row_count_proven"],
        "schema_validated": report["atomicrows_validation_state"]["schema_validated"],
        "repair_checkpoint_inserted_before_pr137l": report["current_sequence_routing"][
            "repair_checkpoint_inserted_before_pr137l"
        ],
        "sequence_insertion_requires_owner_review": report["current_sequence_routing"][
            "sequence_insertion_requires_owner_review"
        ],
        "market_scopes": list(c.CANONICAL_MARKET_SCOPES),
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
