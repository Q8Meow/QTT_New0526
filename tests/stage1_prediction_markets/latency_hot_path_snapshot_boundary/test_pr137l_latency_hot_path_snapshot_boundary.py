from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary import (
    validator,
)
from src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary.report import (
    build_index,
    build_report,
)
from src.qtt.stage1_prediction_markets.latency_hot_path_snapshot_boundary.validator import (
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
    head_rc: int = 0,
    base_rc: int = 0,
    ancestor_rc: int = 0,
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    return {
        ("branch", "--show-current"): (branch_rc, branch, ""),
        ("log", "-1", "--oneline"): (head_rc, head, ""),
        ("rev-parse", "--verify", f"{c.BASE_HEAD_PREFIX}^{{commit}}"): (
            base_rc,
            c.BASE_HEAD_PREFIX,
            "",
        ),
        ("merge-base", "--is-ancestor", c.BASE_HEAD_PREFIX, "HEAD"): (
            ancestor_rc,
            "",
            "",
        ),
    }


def _valid_report() -> dict:
    return build_report(REPO_ROOT)


def _assert_valid(report: dict) -> None:
    outcome = validate_report_payload(report, repo_root=REPO_ROOT)
    assert outcome.ok, outcome.failures


def test_valid_pr137l_static_boundary_passes() -> None:
    report = _valid_report()

    assert report["pr_id"] == c.PR_ID
    assert report["authority_class"] == c.AUTHORITY_CLASS
    assert report["readiness_state"] == c.READINESS_STATE
    assert report["latency_scope"] == c.LATENCY_SCOPE
    _assert_valid(report)


def test_dependency_relation_pr137_to_pr137l_to_pr138_passes() -> None:
    report = _valid_report()
    chain = report["dependency_chain"]

    assert report["required_upstream_prs"] == ["PR137"]
    assert report["downstream_dependencies"] == ["PR138"]
    assert chain["active_sequence_observed_prefix"][:3] == ["PR137", c.PR_ID, "PR138"]
    assert chain["pr137_to_pr137l"] is True
    assert chain["pr137l_to_pr138"] is True
    assert chain["pr138_requires_pr137l"] is True
    assert chain["pr137r_active_sequence_node"] is False
    assert report["controller_mutation_decision"] == (
        c.REASON_CONTROLLER_MUTATION_SKIPPED_EXISTING_SEQUENCE_VALIDATED
    )
    _assert_valid(report)


def test_pr137l_consumes_pr137r_report_as_static_evidence() -> None:
    snapshot = _valid_report()["pr137r_static_evidence_snapshot"]

    assert snapshot["source_report"] == c.PR137R_REPORT_PATH.as_posix()
    assert snapshot["atomicrows_bundle_artifact_found"] is True
    assert snapshot["atomicrows_functional_bundle_status"] == (
        "PRESENT_AND_STATICALLY_VALIDATED"
    )
    assert snapshot["atomicrows_pr137l_usage"] == (
        "READ_ONLY_PRECOMPUTED_STATIC_EVIDENCE_SNAPSHOT_ONLY"
    )


def test_pr137l_records_atomicrows_4183_without_mutating_atomicrows() -> None:
    report = _valid_report()
    snapshot = report["pr137r_static_evidence_snapshot"]
    flags = report["not_created_flags"]

    assert snapshot["expected_atomicrows_row_count"] == 4183
    assert snapshot["atomicrows_row_count_proven"] is True
    assert snapshot["atomicrows_row_count_value"] == 4183
    assert flags["atomicrows_rows_created"] is False
    assert flags["atomicrows_bundle_created"] is False
    assert flags["atomicrows_bundle_edited"] is False
    _assert_valid(report)


def test_pr137l_records_atomicrows_final_readiness_missing_and_day1_false() -> None:
    snapshot = _valid_report()["pr137r_static_evidence_snapshot"]

    assert snapshot["atomicrows_final_readiness_gate_found"] is False
    assert snapshot["atomicrows_semantic_row_contract_complete"] is False
    assert snapshot["atomicrows_day1_live_trading_ready"] is False
    assert snapshot["atomicrows_profit_evidence_created"] is False
    assert snapshot["atomicrows_quantum_advantage_evidence_created"] is False


def test_pr137l_report_is_deterministic_and_schema_valid() -> None:
    first = _valid_report()
    second = _valid_report()

    assert first == second
    assert build_index(first) == build_index(second)
    text = json.dumps(first, sort_keys=True)
    assert f'"{c.FORBIDDEN_GENERATED_INTEGRITY_KEY}"' not in text
    _assert_valid(first)


def test_pr137l_market_scopes_are_exact_and_global_roadmap_only() -> None:
    report = _valid_report()

    assert report["market_scopes"] == list(c.CANONICAL_MARKET_SCOPES)
    assert report["global_roadmap_model"] == c.GLOBAL_ROADMAP_MODEL
    assert report["one_global_roadmap_preserved"] is True
    assert report["market_scoped_overlays_only"] is True
    assert report["market_specific_roadmap_forks_created"] is False
    _assert_valid(report)


def test_pr137l_live_path_boundary_allows_only_precomputed_snapshots() -> None:
    report = _valid_report()

    assert report["future_live_consumer_lanes"] == list(c.FUTURE_LIVE_CONSUMER_LANES)
    assert report["live_path_boundary"]["complexity_target"] == c.LATENCY_COMPLEXITY_TARGET
    assert all(report["live_path_boundary_constraints"].values())
    assert all(
        report["live_path_boundary"][field] is False
        for field in c.LIVE_PATH_REQUIRED_FALSE_FIELDS
    )
    _assert_valid(report)


def test_pr137l_quantum_metadata_is_future_ref_only() -> None:
    report = _valid_report()
    quantum = report["quantum_future_ref_metadata"]

    for field in c.QUANTUM_ALLOWED_TRUE_FIELDS:
        assert quantum[field] is True
    for field in c.QUANTUM_REQUIRED_FALSE_FIELDS:
        assert quantum[field] is False
    _assert_valid(report)


def test_pr137l_atomicrows_metadata_is_static_evidence_future_ref_only() -> None:
    report = _valid_report()
    atomicrows = report["atomicrows_future_ref_metadata"]

    for field in c.ATOMICROWS_ALLOWED_TRUE_FIELDS:
        assert atomicrows[field] is True
    for field in c.ATOMICROWS_REQUIRED_FALSE_FIELDS:
        assert atomicrows[field] is False
    _assert_valid(report)


def test_pr137l_structural_evidence_only_no_generated_integrity_authority() -> None:
    report = _valid_report()

    assert report["structural_evidence_only"] is True
    assert report["not_created_flags"]["qtt_sha_authority_created"] is False
    assert report["not_created_flags"]["qtt_generated_sha_digest_fields_created"] is False
    assert report["forbidden_diff_checks"]["exact_forbidden_integrity_key_created"] is False
    _assert_valid(report)


def test_pr137l_gate_passes_local_exact_base(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(monkeypatch, _git_environment_responses())

    outcome = validate_report_payload(
        _valid_report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert c.RECEIPT_LOCAL_BRANCH_DESCENDANT_BASELINE_ACCEPTED not in outcome.receipts


def test_pr137l_gate_passes_local_branch_descendant_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(
            head="d00df00 PR137L local descendant commit",
            base_rc=0,
            ancestor_rc=0,
        ),
    )

    outcome = validate_report_payload(
        _valid_report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert c.RECEIPT_LOCAL_BRANCH_DESCENDANT_BASELINE_ACCEPTED in outcome.receipts


def test_pr137l_gate_accepts_ci_detached_merge_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/137/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "137/merge")
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(
            branch="",
            head="merge-ref synthetic head",
            branch_rc=0,
            head_rc=0,
        ),
    )

    outcome = validate_report_payload(
        _valid_report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert outcome.ok, outcome.failures
    assert c.RECEIPT_CI_DETACHED_HEAD_MODE in outcome.receipts
    assert c.RECEIPT_CI_SHALLOW_FETCH_ANCESTRY_SKIPPED in outcome.receipts
    assert c.RECEIPT_CI_MERGE_REF_BASELINE_ACCEPTED in outcome.receipts


def test_pr137l_gate_fails_local_wrong_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(branch="wrong-pr137l-branch"),
    )

    outcome = validate_report_payload(
        _valid_report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not outcome.ok
    assert c.REASON_BASELINE_BRANCH_MISMATCH in outcome.failures


def test_pr137l_gate_fails_local_unrelated_head(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_ci_env(monkeypatch)
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(
            head="badcafe unrelated head",
            base_rc=0,
            ancestor_rc=1,
        ),
    )

    outcome = validate_report_payload(
        _valid_report(),
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not outcome.ok
    assert c.REASON_BASELINE_HEAD_MISMATCH in outcome.failures


def test_ci_detached_mode_does_not_bypass_substantive_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/137/merge")
    _mock_git_stdout(
        monkeypatch,
        _git_environment_responses(branch="", head="merge-ref synthetic head"),
    )
    report = _valid_report()
    report["implements_pr138"] = True

    outcome = validate_report_payload(
        report,
        repo_root=REPO_ROOT,
        enforce_environment=True,
    )

    assert not outcome.ok
    assert c.REASON_PR138_SCOPE_FORBIDDEN in outcome.failures
    assert outcome.receipts == ()


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (
            lambda report: report.__setitem__("required_upstream_prs", []),
            c.REASON_UPSTREAM_PR137_REQUIRED,
        ),
        (
            lambda report: report.__setitem__("static_evidence_dependencies", []),
            c.REASON_PR137R_STATIC_EVIDENCE_REQUIRED,
        ),
        (
            lambda report: report.__setitem__("downstream_dependencies", []),
            c.REASON_DOWNSTREAM_PR138_REQUIRED,
        ),
        (
            lambda report: report["dependency_chain"].__setitem__(
                "pr137l_occurrence_count", 2
            ),
            c.REASON_DUPLICATE_ENTRY_FORBIDDEN,
        ),
        (
            lambda report: report["dependency_chain"].__setitem__(
                "pr137_to_pr137l", False
            ),
            c.REASON_UPSTREAM_PR137_REQUIRED,
        ),
        (
            lambda report: report["dependency_chain"].__setitem__(
                "pr137l_to_pr138", False
            ),
            c.REASON_DOWNSTREAM_PR138_REQUIRED,
        ),
        (
            lambda report: report.__setitem__("implements_pr138", True),
            c.REASON_PR138_SCOPE_FORBIDDEN,
        ),
    ],
)
def test_dependency_and_pr138_scope_negative_cases_fail(mutator, reason: str) -> None:
    report = _valid_report()
    mutator(report)

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert reason in outcome.failures


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("source_report", "docs/master_plan/generated/MISSING_PR137R.report.json", c.REASON_PR137R_REPORT_REQUIRED),
        ("atomicrows_row_count_proven", False, c.REASON_PR137R_STATIC_EVIDENCE_CONTRADICTION),
        ("atomicrows_row_count_value", 0, c.REASON_PR137R_STATIC_EVIDENCE_CONTRADICTION),
        ("atomicrows_schema_validated", False, c.REASON_PR137R_STATIC_EVIDENCE_CONTRADICTION),
        ("atomicrows_final_readiness_gate_found", True, c.REASON_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN),
        ("atomicrows_day1_live_trading_ready", True, c.REASON_ATOMICROWS_DAY1_LIVE_READY_CLAIM_FORBIDDEN),
        ("atomicrows_profit_evidence_created", True, c.REASON_ATOMICROWS_BUNDLE_AS_PROFIT_EVIDENCE_FORBIDDEN),
        ("atomicrows_quantum_advantage_evidence_created", True, c.REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN),
    ],
)
def test_pr137r_static_evidence_negative_cases_fail(
    field: str,
    value: object,
    reason: str,
) -> None:
    report = _valid_report()
    report["pr137r_static_evidence_snapshot"][field] = value

    outcome = validate_report_payload(report, repo_root=REPO_ROOT)

    assert not outcome.ok
    assert reason in outcome.failures


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("runtime_execution_created", c.REASON_RUNTIME_AUTHORITY_FORBIDDEN),
        ("live_trading_authority_created", c.REASON_LIVE_AUTHORITY_FORBIDDEN),
        ("source_retrieval_created", c.REASON_SOURCE_RETRIEVAL_FORBIDDEN),
        ("source_acceptance_created", c.REASON_SOURCE_ACCEPTANCE_FORBIDDEN),
        ("accepted_source_evidence_packet_created", c.REASON_SOURCE_ACCEPTANCE_FORBIDDEN),
        ("connector_semantic_binding_created", c.REASON_CONNECTOR_BINDING_FORBIDDEN),
        ("credential_resolution_created", c.REASON_STATIC_BOUNDARY_ONLY),
        ("private_state_fetch_created", c.REASON_STATIC_BOUNDARY_ONLY),
        ("runtime_cash_authority_created", c.REASON_RUNTIME_AUTHORITY_FORBIDDEN),
        ("replay_execution_created", c.REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN),
        ("paper_execution_created", c.REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN),
        ("replay_result_created", c.REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN),
        ("paper_result_created", c.REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN),
        ("replay_paper_result_created", c.REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN),
        ("ranking_scoring_arbitration_output_created", c.REASON_ORDER_AUTHORITY_FORBIDDEN),
        ("trading_signal_created", c.REASON_ORDER_AUTHORITY_FORBIDDEN),
        ("order_intent_authority_created", c.REASON_ORDER_AUTHORITY_FORBIDDEN),
        ("order_authority_created", c.REASON_ORDER_AUTHORITY_FORBIDDEN),
        ("order_execution_created", c.REASON_ORDER_AUTHORITY_FORBIDDEN),
        ("fill_receipt_created", c.REASON_ORDER_AUTHORITY_FORBIDDEN),
        ("profit_evidence_created", c.REASON_PROFIT_EVIDENCE_FORBIDDEN),
        ("profit_claim_created", c.REASON_PROFIT_EVIDENCE_FORBIDDEN),
        ("latency_superiority_claim_created", c.REASON_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN),
        ("execution_superiority_claim_created", c.REASON_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN),
        ("alpha_evidence_created", c.REASON_ALPHA_EVIDENCE_FORBIDDEN),
        ("day1_live_launch_authority_created", c.REASON_LIVE_AUTHORITY_FORBIDDEN),
    ],
)
def test_runtime_live_source_connector_order_profit_claim_flags_fail(
    flag: str,
    reason: str,
) -> None:
    report = _valid_report()
    report["not_created_flags"][flag] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert reason in outcome.failures


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("backend_call_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("simulator_execution_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("qaoa_execution_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("vqe_execution_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("annealing_execution_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("qubo_solving_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("ising_solving_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("optimizer_input_allowed", c.REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN),
        ("quantum_optimizer_input_packet_allowed", c.REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN),
        ("trading_signal_allowed", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
        ("advantage_claim_allowed", c.REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN),
        ("numeric_parameter_values_created", c.REASON_QUANTUM_EXECUTION_FORBIDDEN),
    ],
)
def test_quantum_execution_optimizer_signal_advantage_or_parameters_fail(
    field: str,
    reason: str,
) -> None:
    report = _valid_report()
    report["quantum_future_ref_metadata"][field] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert reason in outcome.failures


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("atomicrows_rows_created", c.REASON_ATOMICROWS_MUTATION_FORBIDDEN),
        ("atomicrows_bundle_created", c.REASON_ATOMICROWS_MUTATION_FORBIDDEN),
        ("atomicrows_bundle_edited", c.REASON_ATOMICROWS_MUTATION_FORBIDDEN),
        ("atomicrows_row_family_sources_created", c.REASON_ATOMICROWS_MUTATION_FORBIDDEN),
        ("atomicrows_row_family_sources_edited", c.REASON_ATOMICROWS_MUTATION_FORBIDDEN),
        ("atomicrows_materialization_authority_created", c.REASON_ATOMICROWS_MATERIALIZATION_FORBIDDEN),
        ("atomicrows_final_readiness_authority_created", c.REASON_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN),
        ("atomicrows_qtt_sha_integrity_authority_created", c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN),
    ],
)
def test_atomicrows_mutation_materialization_or_final_readiness_flags_fail(
    flag: str,
    reason: str,
) -> None:
    report = _valid_report()
    report["not_created_flags"][flag] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert reason in outcome.failures


@pytest.mark.parametrize(
    "field",
    [
        "runtime_materialization_allowed",
        "atomicrows_runtime_materialization_allowed",
        "materialization_authority_created",
        "final_readiness_authority_created",
        "qtt_sha_integrity_authority_created",
    ],
)
def test_atomicrows_future_ref_forbidden_outputs_fail(field: str) -> None:
    report = _valid_report()
    report["atomicrows_future_ref_metadata"][field] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert outcome.failures


def test_noncanonical_forecastex_alias_fails() -> None:
    report = _valid_report()
    report["market_scopes"] = [
        "PREDICTION_MARKETS_GENERAL",
        "KALSHI",
        "POLYMARKET",
        "FORECASTX",
    ]

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_FORECASTEX_ALIAS_FORBIDDEN in outcome.failures


def test_market_specific_roadmap_fork_fails() -> None:
    report = _valid_report()
    report["one_global_roadmap_preserved"] = False

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN in outcome.failures


def test_generated_integrity_key_fails() -> None:
    report = _valid_report()
    report[c.FORBIDDEN_GENERATED_INTEGRITY_KEY] = "not allowed"

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN in outcome.failures


def test_disabled_atomicrows_integrity_artifact_reference_fails() -> None:
    report = _valid_report()
    report["bad_integrity_reference"] = (
        "AtomicRows.bundle." + c.FORBIDDEN_GENERATED_INTEGRITY_KEY
    )

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN in outcome.failures


@pytest.mark.parametrize("field", c.LIVE_PATH_REQUIRED_FALSE_FIELDS)
def test_live_path_forbidden_dependency_flags_fail(field: str) -> None:
    report = _valid_report()
    report["live_path_boundary"][field] = True

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN in outcome.failures


@pytest.mark.parametrize("field", c.LIVE_PATH_REQUIRED_TRUE_CONSTRAINTS)
def test_live_path_required_prohibitions_missing_fail(field: str) -> None:
    report = _valid_report()
    report["live_path_boundary_constraints"][field] = False

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN in outcome.failures


def test_dynamic_timestamp_fails_idempotency() -> None:
    report = _valid_report()
    report["generated_at_utc"] = "2026-05-22T00:00:00Z"

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_IDEMPOTENCY_FAILURE in outcome.failures


def test_report_copy_mutation_does_not_hide_failures() -> None:
    report = copy.deepcopy(_valid_report())
    report["structural_evidence_only"] = False

    outcome = validate_report_payload(report)

    assert not outcome.ok
    assert c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN in outcome.failures


def test_gate_tool_emits_required_success_receipts() -> None:
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/137/merge",
            "GITHUB_REF_NAME": "137/merge",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            "tools/stage1_latency_hot_path_snapshot_boundary_gate.py",
            "--repo-root",
            ".",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    for receipt in c.SUCCESS_RECEIPTS:
        assert receipt in completed.stdout
