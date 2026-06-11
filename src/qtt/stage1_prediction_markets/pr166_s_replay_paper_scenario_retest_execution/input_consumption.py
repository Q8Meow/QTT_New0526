"""Input discovery and consumption audit for PR166-S."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import authority_zero_counts
from .central_vocab import (
    AUTHORITY_BOUNDARY_REF,
    DEFAULT_NO_ORPHAN_STATUS,
    DOWNSTREAM_PR_ROUTES,
    PR_ID,
    UPSTREAM_PR_REFS,
    VALIDATION_STATUS,
)
from .deterministic_ids import ordinal_ref, stable_ref
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class InputDiscovery:
    required_inputs: tuple[str, ...]
    missing_required_inputs: tuple[str, ...]
    optional_present: dict[str, tuple[str, ...]]
    optional_missing: dict[str, tuple[str, ...]]


def discover_inputs(repo_root: Path) -> InputDiscovery:
    required_inputs = tuple(p.normalize_repo_ref(rel) for rel in p.REQUIRED_INPUTS)
    missing_required = tuple(
        rel for rel in required_inputs if not p.resolve_repo_relative(repo_root, rel).exists()
    )
    optional_present: dict[str, tuple[str, ...]] = {}
    optional_missing: dict[str, tuple[str, ...]] = {}
    for group, refs in p.OPTIONAL_INPUT_GROUPS.items():
        normalized = tuple(p.normalize_repo_ref(ref) for ref in refs)
        present = tuple(ref for ref in normalized if p.resolve_repo_relative(repo_root, ref).exists())
        missing = tuple(ref for ref in normalized if not p.resolve_repo_relative(repo_root, ref).exists())
        optional_present[group] = present
        optional_missing[group] = missing
    return InputDiscovery(required_inputs, missing_required, optional_present, optional_missing)


def source_inputs(discovery: InputDiscovery) -> list[str]:
    inputs = list(discovery.required_inputs)
    for refs in discovery.optional_present.values():
        inputs.extend(refs)
    return sorted(dict.fromkeys(inputs))


def row_contract(
    *,
    row_id: str,
    source_artifact_ref: str,
    source_row_ref: str,
    computed_by_module: str,
    owning_agent: str,
    consuming_agent: str,
    downstream_action_type: str,
    replay_paper_scope: str = "REPLAY_PAPER_ONLY",
    downstream_pr_route: str = "score_memory_refresh_PR",
    downstream_artifact_route: str = "PR166_S_FinalSummary.report.json",
    no_orphan_status: str = DEFAULT_NO_ORPHAN_STATUS,
    computation_formula_ref: str = "PR166_S_DETERMINISTIC_REPLAY_PAPER_FORMULA",
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "source_artifact_ref": source_artifact_ref,
        "source_row_ref": source_row_ref,
        "source_field_ref": "candidate_packet_id",
        "computed_by_module": computed_by_module,
        "computation_formula_ref": computation_formula_ref,
        "owning_agent": owning_agent,
        "consuming_agent": consuming_agent,
        "downstream_pr_route": downstream_pr_route,
        "downstream_artifact_route": downstream_artifact_route,
        "downstream_action_type": downstream_action_type,
        "replay_paper_scope": replay_paper_scope,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "no_orphan_status": no_orphan_status,
        "upstream_pr_refs": list(UPSTREAM_PR_REFS),
        "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
        "upstream_artifact_refs": [source_artifact_ref],
        "downstream_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
        "downstream_artifact_refs": [downstream_artifact_route],
        "validator": "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
        "validator_ref": "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
        "manifest_entry_ref": "PR166_S_ReportManifest.report.json",
        "manifest_ref": "PR166_S_ReportManifest.report.json",
        "validation_status": VALIDATION_STATUS,
        "created_by_pr": PR_ID,
        **authority_zero_counts(),
    }


def build_input_consumption_records(discovery: InputDiscovery) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, rel in enumerate(discovery.required_inputs, start=1):
        status = "REQUIRED_INPUT_CONSUMED" if rel not in discovery.missing_required_inputs else "REQUIRED_INPUT_CONSUMPTION_FAILURE"
        row_id = ordinal_ref("PR166_S_INPUT_CONSUMPTION", index)
        records.append(
            {
                "input_consumption_id": row_id,
                "source_artifact_ref": rel,
                "input_requirement_type": "REQUIRED_PR165_PR165B_PR165C_PR165D_PR208_INPUT",
                "consumption_status": status,
                "execution_use": "CANONICAL_SELECTED_BATCH_EXECUTION_INPUT",
                "source_authority_label": "UPSTREAM_QTT_GENERATED_ARTIFACT",
                "upstream_artifact_identity_ref": stable_ref("PR166_S_INPUT_ARTIFACT", rel),
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref=rel,
                    source_row_ref=rel,
                    computed_by_module="input_consumption",
                    owning_agent="replay_agent",
                    consuming_agent="paper_agent",
                    downstream_action_type="selected-batch replay/paper input consumption",
                    downstream_artifact_route="PR166_S_SelectedBatchConsumptionRegistry.report.json",
                ),
            }
        )
    start = len(records) + 1
    for offset, group in enumerate(sorted(discovery.optional_present), start=start):
        present = list(discovery.optional_present[group])
        missing = list(discovery.optional_missing[group])
        row_id = ordinal_ref("PR166_S_INPUT_CONSUMPTION", offset)
        records.append(
            {
                "input_consumption_id": row_id,
                "optional_input_group": group,
                "present_artifact_refs": present,
                "missing_artifact_refs": missing,
                "input_requirement_type": "OPTIONAL_REPLAY_PAPER_INPUT",
                "consumption_status": "OPTIONAL_INPUT_PRESENT_CANDIDATE_ONLY" if present else "OPTIONAL_INPUT_MISSING_WITH_REPLAY_PAPER_ROUTE",
                "execution_use": "BOUNDED_REPLAY_PAPER_ASSUMPTION_CONTEXT" if missing else "REPO_LOCAL_CANDIDATE_CONTEXT",
                "source_authority_label": "CANDIDATE_OR_PROVISIONAL_REPLAY_PAPER_INPUT",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref=",".join(present or missing),
                    source_row_ref=group,
                    computed_by_module="input_consumption",
                    owning_agent="replay_agent",
                    consuming_agent="governance_agent",
                    downstream_action_type="optional input receipt routing",
                    downstream_pr_route="DATASET_COMPLETION_ROUTE" if missing else "score_memory_refresh_PR",
                    downstream_artifact_route="PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
                    no_orphan_status=(
                        "CONNECTED_DOWNSTREAM_WITH_OPTIONAL_INPUT_RECEIPT"
                        if missing
                        else DEFAULT_NO_ORPHAN_STATUS
                    ),
                ),
            }
        )
    return records


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or []:
        rows.extend(records_from_payload(read_json(p.resolve_repo_relative(repo_root, shard_path))))
    return rows


def try_load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    path = repo_root / p.GENERATED_DIR / filename
    if not path.exists():
        return []
    return load_report_records(repo_root, filename)


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row}


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if key in row:
            grouped.setdefault(str(row[key]), []).append(row)
    return grouped
