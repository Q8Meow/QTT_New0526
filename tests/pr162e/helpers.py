from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED = REPO_ROOT / "docs/master_plan/generated"


def load_report(name: str) -> dict:
    path = GENERATED / name
    assert path.exists(), name
    return json.loads(path.read_text(encoding="utf-8"))


def records(name: str) -> list[dict]:
    return load_report(name)["records"]


def plugin_rows() -> list[dict]:
    return records("PR162E_PluginRegistry.report.json")


def forbidden_count_fields() -> tuple[str, ...]:
    return (
        "live_order_authority_count",
        "live_order_execution_count",
        "live_promotion_claim_count",
        "source_truth_acceptance_count",
        "connector_semantic_binding_count",
        "private_state_fetch_count",
        "runtime_cash_receipt_count",
        "profit_evidence_count",
        "quantum_backend_execution_count",
        "quantum_advantage_claim_count",
        "llm_hot_path_artifact_count",
        "llm_order_release_artifact_count",
        "llm_source_acceptance_artifact_count",
        "llm_result_rewrite_artifact_count",
        "qtt_sha_freeze_checksum_global_digest_authority_count",
        "atomicrows_bundle_sha_hash_checksum_authority_count",
    )
