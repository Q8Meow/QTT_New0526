from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


CREATED_AT_UTC = "2026-06-22T00:00:00Z"
REPORT_VERSION = "PR168-MAP3-v4.0"
TOOL_NAME = "tools/build_pr168_map3.py"
GENERATED_ROOT = Path("docs/master_plan/generated")
MAP3_ROOT = GENERATED_ROOT / "map3"


AUTHORITY_FLAGS = {
    "manual_edit_allowed_flag": False,
    "live_authority_created_flag": False,
    "profit_evidence_created_flag": False,
    "source_truth_acceptance_created_flag": False,
    "connector_semantic_binding_created_flag": False,
    "private_state_access_created_flag": False,
    "cash_access_created_flag": False,
    "order_authority_created_flag": False,
    "quantum_backend_execution_flag": False,
    "quantum_advantage_claim_flag": False,
    "qtt_sha_or_atomicrows_hash_authority_flag": False,
}


def common_route(authority_class: str = "EXTERNAL_CANDIDATE_NON_PROOF") -> dict[str, Any]:
    return {
        "upstream_refs": [
            "PR168_MAP3_YOLO_SAFETY_GUARD",
            "PR168_MAP3_QKU_FORMULA_ID_INTAKE_SAFETY_GUARD",
        ],
        "source_refs": [],
        "repo_mining_refs": ["PR168_RP2_MAP2_identity_gap"],
        "formula_contract_refs": [],
        "data_requirement_refs": [],
        "unit_normalization_refs": [],
        "dry_run_receipt_refs": [],
        "downstream_consumers": [
            "PR168_RP2_REPLAY_PAPER_RECOMPUTE",
            "PR168_RANK2_EVIDENCE_RANKING",
            "PR165B_CONDITION_SCOPED_MEMORY",
            "PR162E_Q_QUANTUM_MAPPING",
            "DATA1B_MARKET_DATA_ACQUISITION_REPAIR",
            "SOURCE_EVIDENCE_REVIEW",
        ],
        "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2", "PR165-B", "PR162E-Q", "DATA1B"],
        "owning_agent": "PR168_MAP3_formula_intake_agent",
        "consumer_agents": [
            "PR168_RP2_agent",
            "PR168_RANK2_agent",
            "PR165B_memory_agent",
            "PR162EQ_quantum_agent",
            "DATA1B_repair_agent",
            "source_evidence_review_agent",
        ],
        "validator_refs": ["tools/validate_pr168_map3.py"],
        "test_refs": ["tests/pr168_map3/test_online_scout.py"],
        "authority_class": authority_class,
        "no_orphan_status": "NO_ORPHAN_LINKED",
        "terminal_by_nature_flag": False,
        "terminal_reason_code": None,
        "terminal_reason_if_terminal": None,
        "repair_route_if_gap": None,
        **AUTHORITY_FLAGS,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows_list:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    manifest = {
        "logical_report_id": f"PR168_MAP3_{path.stem}_manifest",
        "physical_filename": str(manifest_path).replace("\\", "/"),
        "row_shard_ref": str(path).replace("\\", "/"),
        "row_count": len(rows_list),
        "created_by_tool": TOOL_NAME,
        "created_at_utc": CREATED_AT_UTC,
        "report_version": REPORT_VERSION,
        **common_route("MAP3_ROW_SHARD_MANIFEST_NON_PROOF"),
    }
    write_json(manifest_path, manifest)
    return {
        "row_shard_ref": str(path).replace("\\", "/"),
        "manifest_ref": str(manifest_path).replace("\\", "/"),
        "row_count": len(rows_list),
    }


def report_payload(
    logical_report_id: str,
    physical_filename: str,
    records: list[dict[str, Any]],
    row_shard_refs: list[dict[str, Any]] | None = None,
    summary: dict[str, Any] | None = None,
    authority_class: str = "MAP3_REPORT_NON_PROOF",
) -> dict[str, Any]:
    route = common_route(authority_class)
    return {
        "logical_report_id": logical_report_id,
        "physical_filename": physical_filename,
        "alias_registry_ref": "docs/master_plan/generated/PR168_MAP3_FileAliases.report.json",
        "path_audit_ref": "docs/master_plan/generated/PR168_MAP3_PathAudit.report.json",
        "report_version": REPORT_VERSION,
        "created_by_tool": TOOL_NAME,
        "created_at_utc": CREATED_AT_UTC,
        "upstream_input_refs": route["upstream_refs"],
        "row_shard_refs_if_any": row_shard_refs or [],
        "data_provenance_refs": ["PR168_MAP3_OnlineScout_deep_structured_search_matrix"],
        "records": records,
        "summary": summary or {},
        **route,
    }
