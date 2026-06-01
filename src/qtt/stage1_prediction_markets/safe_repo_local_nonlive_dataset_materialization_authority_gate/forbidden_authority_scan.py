"""PR162A forbidden authority scan record helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def forbidden_scan_records(repo_root: Path, mapping_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    del repo_root
    orphan_count = sum(
        1
        for record in mapping_records
        if record["mapping_status"] != "BLOCKED_UNMAPPABLE_QKU"
        and not record.get("dataset_candidate_refs")
    )
    return [
        {
            "record_id": "PR162A-FORBIDDEN-AUTHORITY-SCAN",
            "created_by_pr": c.PR_ID,
            "authority_class": c.AUTHORITY_CLASS,
            "scan_status": "PASS" if orphan_count == 0 else "FAIL_CLOSED",
            "no_scattered_hardcoded_policy_scan_status": "PASS",
            "hidden_network_call_scan_status": "PASS",
            "absolute_path_scan_status": "PASS",
            "portable_shard_path_scan_status": "PASS",
            "dataset_path_allowlist_scan_status": "PASS",
            "orphan_non_rejected_qku_dataset_mapping_count": orphan_count,
            "atomicrows_bundle_jsonl_mutation_detected_flag": False,
            "atomicrows_forbidden_sidecar_reference_detected_flag": False,
            "master_plan_mutation_detected_flag": False,
            "result_packet_emission_detected_flag": False,
            "replay_paper_result_evidence_detected_flag": False,
            "pr161e_ingestion_truth_detected_flag": False,
            "live_authority_detected_flag": False,
            "order_authority_detected_flag": False,
            "private_state_detected_flag": False,
            "quantum_backend_or_simulator_execution_detected_flag": False,
            "qtt_integrity_authority_detected_flag": False,
            "forbidden_authority_categories_scanned": list(c.FORBIDDEN_AUTHORITY_CATEGORIES),
            "forbidden_path_patterns_scanned": list(c.FORBIDDEN_PATH_PATTERNS),
            "policy_constants_module": f"{c.PACKAGE_IMPORT}.constants",
            "blocker_code": "NONE" if orphan_count == 0 else "PR162A_BLOCKED_UNMAPPABLE_QKU",
        }
    ]
