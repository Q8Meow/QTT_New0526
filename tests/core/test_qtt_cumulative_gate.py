from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import qtt_test_gate


def _report() -> dict:
    return qtt_test_gate.build_report(
        repo_root=Path("."),
        phase=qtt_test_gate.PHASE,
        strict_no_claim=True,
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_qtt_cumulative_gate_valid_static_report_passes():
    report = _report()

    assert report["status"] == "PASS"
    assert report["findings"] == []
    assert (
        qtt_test_gate.validate_qtt_test_gate_report(
            report,
            repo_root=Path("."),
            strict_no_claim=True,
        )
        == []
    )


def test_qtt_cumulative_gate_requires_stage1_runtime_scaffold_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "stage1_runtime_scaffold_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC_VALIDATION_OK"
    )


def test_qtt_cumulative_gate_requires_pr40_connector_semantic_binding_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "connector_semantic_binding_ledger_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr41_runtime_resolver_snapshot_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "runtime_resolver_snapshot_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr42_runtime_resolver_handoff_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "runtime_resolver_to_replay_paper_handoff_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_OK"
    )


def test_qtt_cumulative_gate_requires_pr43_concurrent_replay_paper_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "concurrent_replay_paper_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr44_dual_result_review_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"] == "dual_result_review_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_OK"


def test_qtt_cumulative_gate_requires_pr45_owner_live_promotion_review_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "owner_live_promotion_review_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_OK"
    )


def test_qtt_cumulative_gate_requires_pr46_three_venue_canary_eligibility_contract_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "three_venue_canary_eligibility_contract_gate_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert (
        receipt["validation_marker"]
        == "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_OK"
    )


def test_qtt_cumulative_gate_requires_pr47_implementation_coverage_ledger_receipt():
    report = _report()
    receipt = next(
        item
        for item in report["prior_gate_receipts"]
        if item["receipt_id"]
        == "master_plan_implementation_coverage_ledger_receipt_present"
    )

    assert receipt["satisfied"] is True
    assert receipt["status"] == "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
    assert receipt["validation_marker"] == "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_OK"


def test_qtt_cumulative_gate_represents_all_prior_receipts_or_static_bootstrap():
    report = _report()
    statuses = {item["receipt_id"]: item["status"] for item in report["prior_gate_receipts"]}

    assert statuses["owner_start_receipt_present_or_reported_missing"] == (
        "REQUIRED_PRIOR_GATE_REPORT_NOT_CREATED_STATIC_BOOTSTRAP"
    )
    assert statuses["master_plan_hash_receipt_present_or_reported_missing"] == (
        "REQUIRED_PRIOR_GATE_REPORT_NOT_CREATED_STATIC_BOOTSTRAP"
    )
    assert all(status != "MISSING_BLOCKED" for status in statuses.values())


def test_qtt_cumulative_gate_blocks_hidden_zip_authority(tmp_path):
    report = _report()
    zip_path = tmp_path / "hidden_authority.zip"
    zip_path.write_bytes(b"PK")

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=tmp_path,
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "hidden ZIP authority")


def test_qtt_cumulative_gate_blocks_direct_main_bypass_claim():
    report = _report()
    report["filesystem_claim_checks"]["direct_main_bypass_claim_present"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "direct_main_bypass_claim_present")


def test_qtt_cumulative_gate_blocks_atomicrows_invention_claim():
    report = _report()
    report["no_claim_flags"]["atomicrows_invention_claim"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "atomicrows_invention_claim")


def test_qtt_cumulative_gate_blocks_stale_generated_derivative_completion_claim():
    report = _report()
    report["no_claim_flags"]["stale_generated_derivative_completion_claim"] = True

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=Path("."),
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "stale_generated_derivative_completion_claim")


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails(tmp_path):
    report = _report()
    bundle_path = (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.jsonl"
    )
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("{}\n", encoding="utf-8")

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=tmp_path,
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle")


def test_actual_atomicrows_bundle_sha_existing_at_canonical_path_fails(tmp_path):
    report = _report()
    sha_path = (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomic_rows"
        / "AtomicRows.bundle.sha256"
    )
    sha_path.parent.mkdir(parents=True)
    sha_path.write_text("UNAUTHORIZED_STATIC_TEST_PLACEHOLDER\n", encoding="utf-8")

    failures = qtt_test_gate.validate_qtt_test_gate_report(
        report,
        repo_root=tmp_path,
        strict_no_claim=True,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle hash")


def test_qtt_cumulative_gate_validation_does_not_mutate_report():
    report = _report()
    frozen = copy.deepcopy(report)

    assert (
        qtt_test_gate.validate_qtt_test_gate_report(
            report,
            repo_root=Path("."),
            strict_no_claim=True,
        )
        == []
    )
    assert report == frozen


def test_qtt_generated_static_reports_create_no_authority():
    for path in [
        Path("docs/master_plan/generated/QTTTestGate.report.json"),
        Path("docs/master_plan/generated/LocalGateCommandMatrix.json"),
        Path("docs/master_plan/generated/FirstCodingPRHandoff.packet.json"),
    ]:
        report = json.loads(path.read_text(encoding="utf-8"))
        metadata = report["metadata"]
        assert metadata["authority_class"] == "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY"
        for field in qtt_test_gate.STATIC_AUTHORITY_FLAGS:
            assert metadata[field] is False


def test_qtt_test_gate_schema_is_closed_at_root():
    schema = json.loads(
        Path("src/qtt/core/schemas/qtt_test_gate_report.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "prior_gate_receipts" in schema["required"]
