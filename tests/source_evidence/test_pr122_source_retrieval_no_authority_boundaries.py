from __future__ import annotations

import json
from pathlib import Path

from tools import validate_source_evidence_retrieval_executor as validator
from src.qtt.source_evidence.retrieval import controller


STATE_MACHINE = Path(
    "src/qtt/source_evidence/retrieval/source_retrieval_state_machine.json"
)
TARGET_SCHEMA = Path(
    "schemas/source_evidence/retrieval/source_retrieval_target.schema.json"
)
MANIFEST_REPORT = Path(
    "docs/master_plan/source_evidence/generated/SourceEvidenceRetrievalManifest.report.json"
)
PR122_REPORT = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR122_SOURCE_EVIDENCE_RETRIEVAL_CONTROLLER_GATED_REPORT.json"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_no_accepted_source_packet_or_source_fact_created():
    report = _json(PR122_REPORT)

    assert report["accepted_source_fact_count"] == 0
    assert report["accepted_source_packet_created_count"] == 0
    assert report["candidate_packet_schema_created"] is False
    assert report["candidate_receipt_schema_created"] is True


def test_stage1_prediction_market_scope_only_and_forbidden_taxonomy_blocked():
    machine = _json(STATE_MACHINE)

    assert machine["active_stage1_platform_scopes"] == [
        "PREDICTION_MARKETS_GENERAL",
        "KALSHI",
        "POLYMARKET",
        "FORECASTEX_IBKR",
    ]
    assert machine["future_market_families"] == [
        "COMMODITIES",
        "CRYPTOCURRENCY",
        "EQUITIES",
        "ETFS",
        "FUTURES",
        "FX",
        "OPTIONS",
        "STOCKS",
    ]
    for value in (
        "OTHER",
        "UNKNOWN_MARKET",
        "ANY_OTHER_MARKET",
        "OTHER_OWNER_APPROVED_FUTURE_MARKET",
        "etc.",
    ):
        assert value in machine["forbidden_market_taxonomy_values"]

    assert controller.classify_market_scope("KALSHI") == "KALSHI"
    assert controller.classify_market_scope("STOCKS") == "STOCKS"
    assert (
        controller.classify_market_scope("BESPOKE_OWNER_NOTE")
        == "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE"
    )


def test_retrieval_manifest_requires_digest_locator_redaction_and_no_network():
    target_schema = _json(TARGET_SCHEMA)
    manifest_report = _json(MANIFEST_REPORT)
    required = set(target_schema["required"])

    assert {"digest_requirement", "locator_requirement", "redaction_requirement"} <= required
    assert manifest_report["manifest"]["external_network_fetch_default_enabled"] is False
    assert manifest_report["manifest"]["retrieval_targets"] == []
    assert manifest_report["manifest_validation_failures"] == []


def test_private_doc_unclear_access_quarantines_and_secret_like_values_redacted():
    redacted, detected = controller.redact_secret_like_values(
        "api_key=abc123 token=def456"
    )

    assert detected is True
    assert "abc123" not in redacted
    assert "def456" not in redacted
    assert controller.private_doc_access_state(False) == (
        "SOURCE_BLOCKED_PRIVATE_DOC_UNCLEAR_ACCESS_RIGHTS"
    )


def test_no_runtime_live_order_profit_or_connector_authority_created():
    report = _json(PR122_REPORT)

    assert report["connector_semantic_binding_created_count"] == 0
    assert report["runtime_resolver_snapshot_created_count"] == 0
    assert report["runtime_live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["runtime_cash_receipts_created_count"] == 0
    assert report["replay_paper_results_created_count"] == 0
    assert report["profit_evidence_created"] is False


def test_no_live_pretrade_runtime_module_imports_retrieval_executor():
    forbidden_imports = (
        "source_evidence.retrieval",
        "source_evidence_retrieval_executor",
    )
    runtime_like_parts = {"live", "pretrade", "runtime", "runtime_resolver"}

    for path in Path("src").rglob("*.py"):
        parts = {part.lower() for part in path.parts}
        if not runtime_like_parts.intersection(parts):
            continue
        text = path.read_text(encoding="utf-8")
        assert not any(item in text for item in forbidden_imports), path


def test_no_quantum_backend_or_simulator_execution_and_no_claims():
    report = _json(PR122_REPORT)

    assert report["quantum_backend_execution_count"] == 0
    assert report["quantum_simulator_execution_count"] == 0
    assert report["optimizer_execution_count"] == 0
    assert report["quantum_advantage_claim_created"] is False
    assert report["latency_superiority_claim_created"] is False
    assert report["execution_superiority_claim_created"] is False


def test_deterministic_generated_reports_are_byte_stable_in_memory():
    first = validator.build_reports(Path(".").resolve())
    second = validator.build_reports(Path(".").resolve())

    assert first == second
    assert {
        path: controller.canonical_digest(report) for path, report in first.items()
    } == {path: controller.canonical_digest(report) for path, report in second.items()}
