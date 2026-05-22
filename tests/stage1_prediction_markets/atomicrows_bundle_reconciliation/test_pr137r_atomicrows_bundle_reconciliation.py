from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation import constants as c
from src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation.report import (
    build_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation import (
    validator,
)
from src.qtt.stage1_prediction_markets.atomicrows_bundle_reconciliation.validator import (
    success_receipts_for_report,
    validate_report_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _clear_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in (
        "GITHUB_ACTIONS",
        "GITHUB_EVENT_NAME",
        "GITHUB_REF",
        "GITHUB_REF_NAME",
    ):
        monkeypatch.delenv(env_name, raising=False)


def _mock_git_stdout(
    monkeypatch: pytest.MonkeyPatch,
    responses: dict[tuple[str, ...], tuple[int, str, str]],
) -> None:
    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        key = tuple(args)
        if key not in responses:
            raise AssertionError(f"unexpected git command: {args}")
        return responses[key]

    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)


def _git_environment_responses(
    *,
    branch: str = c.BRANCH,
    head: str = f"{c.BASE_HEAD_PREFIX} baseline",
    branch_rc: int = 0,
    branch_err: str = "",
    head_rc: int = 0,
    head_err: str = "",
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    return {
        ("branch", "--show-current"): (branch_rc, branch, branch_err),
        ("log", "-1", "--oneline"): (head_rc, head, head_err),
    }


def _missing_bundle_report(monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(
        c,
        "BUNDLE_PATH",
        Path("docs/master_plan/atomic_rows/PR137R_missing_bundle_fixture.jsonl"),
    )
    return build_report(REPO_ROOT)


def _assert_valid(report: dict) -> None:
    outcome = validate_report_payload(report)
    assert outcome.ok, outcome.failures


def test_missing_bundle_is_truthfully_recorded_and_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)

    assert report["atomicrows_artifact_inventory"]["functional_bundle_artifact_found"] is False
    assert report["atomicrows_validation_state"]["functional_bundle_status"] == c.STATUS_NOT_CREATED
    _assert_valid(report)


def test_missing_4183_rows_is_truthfully_not_proven_and_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)

    assert report["atomicrows_validation_state"]["row_count_proven"] is False
    assert c.REASON_4183_ROWS_NOT_PROVEN in report["reason_codes"]
    _assert_valid(report)


def test_actual_repo_report_records_present_static_bundle_truth() -> None:
    report = build_report(REPO_ROOT)

    assert report["atomicrows_artifact_inventory"]["functional_bundle_artifact_found"] is True
    assert report["atomicrows_validation_state"]["functional_bundle_status"] == (
        c.STATUS_PRESENT_AND_STATICALLY_VALIDATED
    )
    assert report["atomicrows_validation_state"]["row_count_value"] == c.EXPECTED_ROW_COUNT
    assert report["atomicrows_validation_state"]["row_count_proven"] is True
    assert report["atomicrows_validation_state"]["schema_validated"] is True
    _assert_valid(report)


def test_old_pr97_pr101_labels_are_not_used_as_completion_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    legacy = report["legacy_roadmap_reconciliation"]

    assert legacy["old_pr_labels_used_as_completion_proof"] is False
    assert [row["old_label"] for row in legacy["records"]] == [
        "PR97",
        "PR98",
        "PR99",
        "PR100",
        "PR101",
    ]
    _assert_valid(report)


def test_report_preserves_pr136_pr137_pr137l_and_pr138_routing() -> None:
    report = build_report(REPO_ROOT)

    assert report["selector_authority_preserved"] == "PR136"
    assert report["dependency_controller_authority_preserved"] == "PR137"
    routing = report["current_sequence_routing"]
    assert routing["active_sequence_observed_prefix"][:3] == ["PR137", "PR137L", "PR138"]
    assert routing["pr137l_preserved_as_latency_boundary_only"] is True
    assert routing["pr138_preserved_downstream_of_pr137l"] is True
    assert "PR138" in routing["current_sequence_atomicrows_bundle_implementation_slots"]
    _assert_valid(report)


def test_report_uses_one_global_roadmap_and_canonical_market_scopes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)

    assert report["one_global_roadmap_preserved"] is True
    assert report["market_scopes"] == list(c.CANONICAL_MARKET_SCOPES)
    _assert_valid(report)


def test_report_uses_structural_evidence_only_and_is_deterministic() -> None:
    first = build_report(REPO_ROOT)
    second = build_report(REPO_ROOT)

    assert first == second
    assert first["structural_evidence_only"] is True
    forbidden_key = c.FORBIDDEN_GENERATED_INTEGRITY_KEY
    assert f'"{forbidden_key}"' not in json.dumps(first, sort_keys=True)
    _assert_valid(first)


def test_validator_success_receipts_are_deterministic() -> None:
    report = build_report(REPO_ROOT)

    assert success_receipts_for_report(report) == success_receipts_for_report(report)
    receipts = success_receipts_for_report(report)
    assert c.SUCCESS_RECEIPTS[0] in receipts
    assert c.RECEIPT_BUNDLE_VALID in receipts
    assert c.RECEIPT_ROWS_PROVEN in receipts


def test_quantum_compatibility_is_audit_only() -> None:
    report = build_report(REPO_ROOT)
    quantum = report["quantum_forward_compatibility_audit"]

    assert quantum["quantum_compatibility_metadata_checked"] is True
    assert quantum["quantum_execution_created"] is False
    assert quantum["quantum_optimizer_input_created"] is False
    assert quantum["quantum_trading_signal_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_numeric_defaults_invented"] is False
    _assert_valid(report)


def test_gate_emits_required_success_receipts() -> None:
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/138/merge",
            "GITHUB_REF_NAME": "138/merge",
        }
    )
    completed = subprocess.run(
        [sys.executable, "tools/stage1_atomicrows_bundle_reconciliation_gate.py", "--repo-root", "."],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    for receipt in c.SUCCESS_RECEIPTS:
        assert receipt in completed.stdout


def test_local_environment_wrong_branch_and_head_still_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(
            branch="wrong-pr137r-branch",
            head="2bec646 Merge 337c32ed53825c3c57e8e9ac00e9faaa819d2595 into f8859359f944462314f9c252ae91026ea52212c7",
        ),
    )

    outcome = validate_report_payload(
        build_report(REPO_ROOT),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not outcome.ok
    assert c.REASON_BASELINE_BRANCH_MISMATCH in outcome.failures
    assert c.REASON_BASELINE_HEAD_MISMATCH in outcome.failures
    assert outcome.receipts == ()


def test_github_actions_detached_merge_ref_accepts_branch_and_head_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/138/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "138/merge")
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(
            branch="",
            head="2bec646 Merge 337c32ed53825c3c57e8e9ac00e9faaa819d2595 into f8859359f944462314f9c252ae91026ea52212c7",
        ),
    )

    outcome = validate_report_payload(
        build_report(REPO_ROOT),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert c.REASON_BASELINE_BRANCH_MISMATCH not in outcome.failures
    assert c.REASON_BASELINE_HEAD_MISMATCH not in outcome.failures
    assert c.RECEIPT_CI_DETACHED_HEAD_MODE in outcome.receipts
    assert c.RECEIPT_CI_SHALLOW_FETCH_ANCESTRY_SKIPPED in outcome.receipts
    assert c.RECEIPT_CI_MERGE_REF_BASELINE_ACCEPTED in outcome.receipts


@pytest.mark.parametrize(
    ("section", "field", "value", "reason"),
    [
        ("atomicrows_validation_state", "functional_bundle_ready_for_agent_consumption", True, c.REASON_FALSE_COMPLETION_FORBIDDEN),
        ("atomicrows_validation_state", "day1_live_trading_ready", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("atomicrows_validation_state", "profit_evidence_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("atomicrows_validation_state", "quantum_advantage_evidence_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "atomicrows_rows_created", True, c.REASON_BUNDLE_GENERATION_FORBIDDEN),
        ("not_created_flags", "atomicrows_bundle_created", True, c.REASON_BUNDLE_GENERATION_FORBIDDEN),
        ("not_created_flags", "atomicrows_row_family_sources_created", True, c.REASON_BUNDLE_GENERATION_FORBIDDEN),
        ("not_created_flags", "atomicrows_bundle_builder_created", True, c.REASON_BUNDLE_GENERATION_FORBIDDEN),
        ("not_created_flags", "qtt_sha_authority_created", True, c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY),
        ("no_qtt_sha_summary", "exact_forbidden_integrity_key_created", True, c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY),
        ("no_qtt_sha_summary", "integrity_or_file_size_evidence_used_as_qtt_proof", True, c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY),
        ("forbidden_diff_checks", "master_plan_markdown_text_changed", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "source_retrieval_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "source_acceptance_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "connector_semantic_binding_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "replay_execution_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "paper_execution_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "replay_paper_result_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "ranking_scoring_arbitration_output_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "trading_signal_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "order_authority_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("not_created_flags", "order_execution_created", True, c.REASON_LIVE_ORDER_PROFIT_FORBIDDEN),
        ("quantum_forward_compatibility_audit", "quantum_execution_created", True, c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("quantum_forward_compatibility_audit", "quantum_numeric_defaults_invented", True, c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
    ],
)
def test_negative_authority_claims_fail(
    monkeypatch: pytest.MonkeyPatch,
    section: str,
    field: str,
    value: bool,
    reason: str,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report[section][field] = value

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert reason in outcome.failures


def test_claiming_bundle_ready_while_bundle_missing_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["atomicrows_validation_state"]["functional_bundle_status"] = (
        c.STATUS_PRESENT_AND_STATICALLY_VALIDATED
    )
    report["atomicrows_validation_state"]["row_count_proven"] = True
    report["atomicrows_validation_state"]["row_count_value"] = c.EXPECTED_ROW_COUNT
    report["atomicrows_validation_state"]["schema_validated"] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_FALSE_COMPLETION_FORBIDDEN in outcome.failures


def test_claiming_4183_rows_without_row_count_proof_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["atomicrows_artifact_inventory"]["functional_bundle_artifact_found"] = True
    report["atomicrows_validation_state"]["functional_bundle_status"] = (
        c.STATUS_PRESENT_AND_STATICALLY_VALIDATED
    )
    report["atomicrows_validation_state"]["row_count_value"] = c.EXPECTED_ROW_COUNT
    report["atomicrows_validation_state"]["row_count_proven"] = False
    report["atomicrows_validation_state"]["schema_validated"] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_4183_ROWS_NOT_PROVEN in outcome.failures


def test_claiming_agent_ready_without_consumer_path_fails() -> None:
    report = build_report(REPO_ROOT)
    report["atomicrows_validation_state"]["functional_bundle_ready_for_agent_consumption"] = True
    report["atomicrows_artifact_inventory"]["agent_read_only_consumer_found"] = False

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_AGENT_CONSUMER_MISSING in outcome.failures


def test_schema_validation_without_validator_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["atomicrows_validation_state"]["schema_validated"] = True
    report["atomicrows_artifact_inventory"]["bundle_validator_found"] = False

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_VALIDATOR_MISSING in outcome.failures


def test_old_pr_labels_as_artifact_proof_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["legacy_roadmap_reconciliation"]["old_pr_labels_used_as_completion_proof"] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_LEGACY_LABEL_ONLY in outcome.failures


def test_exact_forbidden_integrity_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    report = _missing_bundle_report(monkeypatch)
    report[c.FORBIDDEN_GENERATED_INTEGRITY_KEY] = "not allowed"

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY in outcome.failures


def test_noncanonical_third_venue_alias_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["market_scopes"] = ["PREDICTION_MARKETS_GENERAL", "KALSHI", "POLYMARKET", "FORECASTX"]

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_FORECASTEX_ALIAS_FORBIDDEN in outcome.failures


def test_disconnected_market_roadmap_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["one_global_roadmap_preserved"] = False

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN in outcome.failures


def test_dynamic_timestamp_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["generated_at_utc"] = "2026-05-22T00:00:00Z"

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_IDEMPOTENCY_FAILURE in outcome.failures


def test_claiming_repair_inserted_without_controller_sequence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    report["current_sequence_routing"]["repair_checkpoint_inserted_before_pr137l"] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_SEQUENCE_INSERTION_OWNER_REVIEW in outcome.failures


def test_report_copy_mutation_does_not_hide_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _missing_bundle_report(monkeypatch)
    mutated = copy.deepcopy(report)
    mutated["structural_evidence_only"] = False

    outcome = validate_report_payload(mutated)

    assert not outcome.ok
    assert c.REASON_NO_QTT_SHA_DIGEST_AUTHORITY in outcome.failures
