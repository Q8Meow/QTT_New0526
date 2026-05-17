from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import validate_atomicrows_parameter_agent_binding_consumer_gate as gate


REPO_ROOT = Path(".")
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_parameter_agent_binding_consumer_gate.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_parameter_agent_binding_consumer_gate.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingConsumerGate.report.json"
)
REGISTRY = Path("docs/master_plan/atomic_rows/AtomicRowsParameterAgentBindingRegistry.yaml")
BINDING_REPORT = Path("docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json")
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _attempt(attempt_id: str) -> dict:
    for attempt in _fixture()["attempted_access"]:
        if attempt["attempted_access_id"] == attempt_id:
            return attempt
    raise AssertionError(f"missing attempted access {attempt_id}")


def _assert_attempt(
    attempt_id: str,
    *,
    decision: str,
    blocked_reason: str | None,
    owner_override: bool,
) -> None:
    attempt = _attempt(attempt_id)
    assert attempt["access_decision"] == decision
    assert attempt["blocked_reason"] == blocked_reason
    assert attempt["owner_override_applied"] is owner_override
    if owner_override:
        assert attempt["blocks_qtt_when_owner_override_present"] is False
        assert attempt["owner_override_resolved_block"] is True


def test_schema_exists_and_validates_fixture_and_report():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        binding_report_path=BINDING_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert result.failures == ()
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["access_decision"]["enum"] == list(gate.ACCESS_DECISIONS)
    assert schema["$defs"]["binding_lookup_status"]["enum"] == list(
        gate.BINDING_LOOKUP_STATUSES
    )
    assert schema["$defs"]["agent_role"]["enum"] == list(gate.AGENT_ROLES)
    assert schema["$defs"]["consumer_class"]["enum"] == list(gate.CONSUMER_CLASSES)
    assert schema["$defs"]["agent_use_scope"]["enum"] == list(gate.AGENT_USE_SCOPES)
    assert schema["$defs"]["attempted_access"]["required"] == list(
        gate.ATTEMPT_FIELDS
    )
    assert schema["$defs"]["consumer_gate_report"]["required"] == list(
        gate._empty_report()
    )
    assert _report() == result.report


def test_validator_produces_deterministic_report():
    first = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        binding_report_path=BINDING_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )
    second = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        binding_report_path=BINDING_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
        output_path=REPORT,
    )

    assert first.failures == ()
    assert second.failures == ()
    assert first.report == second.report == _report()
    assert gate.serialize_report(first.report or {}) == gate.serialize_report(
        second.report or {}
    )


def test_binding_authorized_access_is_allowed():
    _assert_attempt(
        "attempt_006_allowed_risk_binding",
        decision="ALLOWED_BY_BINDING",
        blocked_reason=None,
        owner_override=False,
    )


@pytest.mark.parametrize(
    ("attempt_id", "decision", "blocked_reason", "owner_override"),
    [
        (
            "attempt_021_blocked_missing_binding_normal",
            "BLOCKED_MISSING_BINDING",
            "BLOCKED_MISSING_BINDING",
            False,
        ),
        (
            "attempt_015_allowed_missing_binding_owner_global_override",
            "ALLOWED_BY_OWNER_GLOBAL_OVERRIDE",
            "BLOCKED_MISSING_BINDING",
            True,
        ),
        (
            "attempt_022_blocked_unauthorized_agent_role_normal",
            "BLOCKED_UNAUTHORIZED_AGENT_ROLE",
            "BLOCKED_UNAUTHORIZED_AGENT_ROLE",
            False,
        ),
        (
            "attempt_016_allowed_unauthorized_role_agent_assignment_owner_approved",
            "ALLOWED_BY_AGENT_ASSIGNMENT_OWNER_APPROVED",
            "BLOCKED_UNAUTHORIZED_AGENT_ROLE",
            True,
        ),
        (
            "attempt_023_blocked_unauthorized_agent_id_normal",
            "BLOCKED_UNAUTHORIZED_AGENT_ID",
            "BLOCKED_UNAUTHORIZED_AGENT_ID",
            False,
        ),
        (
            "attempt_017_allowed_unauthorized_agent_id_owner_global_override",
            "ALLOWED_BY_OWNER_OVERRIDE_SATISFIED",
            "BLOCKED_UNAUTHORIZED_AGENT_ID",
            True,
        ),
        (
            "attempt_024_blocked_unauthorized_consumer_normal",
            "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
            "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
            False,
        ),
        (
            "attempt_018_allowed_unauthorized_consumer_owner_global_override",
            "ALLOWED_BY_OWNER_OVERRIDE_SATISFIED",
            "BLOCKED_UNAUTHORIZED_CONSUMER_CLASS",
            True,
        ),
        (
            "attempt_025_blocked_scope_mismatch_normal",
            "BLOCKED_SCOPE_MISMATCH",
            "BLOCKED_SCOPE_MISMATCH",
            False,
        ),
        (
            "attempt_019_allowed_scope_mismatch_owner_global_override",
            "ALLOWED_BY_OWNER_OVERRIDE_SATISFIED",
            "BLOCKED_SCOPE_MISMATCH",
            True,
        ),
    ],
)
def test_normal_blocks_and_owner_override_satisfaction_cases(
    attempt_id: str,
    decision: str,
    blocked_reason: str,
    owner_override: bool,
):
    _assert_attempt(
        attempt_id,
        decision=decision,
        blocked_reason=blocked_reason,
        owner_override=owner_override,
    )


@pytest.mark.parametrize(
    ("attempt_id", "decision", "blocked_reason"),
    [
        (
            "attempt_027_blocked_quarantined_normal_access",
            "BLOCKED_QUARANTINE",
            "BLOCKED_QUARANTINE",
        ),
        (
            "attempt_032_allowed_quarantine_review_binding",
            "ALLOWED_BY_QUARANTINE_REVIEW_BINDING",
            None,
        ),
        (
            "attempt_026_blocked_retired_normal_access",
            "BLOCKED_RETIRED",
            "BLOCKED_RETIRED",
        ),
        (
            "attempt_031_allowed_retired_binding_audit",
            "ALLOWED_BY_RETIREMENT_AUDIT_BINDING",
            None,
        ),
    ],
)
def test_quarantine_and_retirement_behavior(
    attempt_id: str,
    decision: str,
    blocked_reason: str | None,
):
    _assert_attempt(
        attempt_id,
        decision=decision,
        blocked_reason=blocked_reason,
        owner_override=False,
    )


@pytest.mark.parametrize(
    ("attempt_id", "decision"),
    [
        ("attempt_008_allowed_row_level_binding", "ALLOWED_BY_ROW_BINDING"),
        ("attempt_009_allowed_pattern_level_binding", "ALLOWED_BY_PATTERN_BINDING"),
        ("attempt_001_allowed_research_family_binding", "ALLOWED_BY_FAMILY_BINDING"),
        ("attempt_010_allowed_agent_id_level_binding", "ALLOWED_BY_AGENT_ID_BINDING"),
    ],
)
def test_row_pattern_family_and_agent_id_bindings_are_allowed(
    attempt_id: str,
    decision: str,
):
    _assert_attempt(
        attempt_id,
        decision=decision,
        blocked_reason=None,
        owner_override=False,
    )


def test_unknown_values_and_missing_parameter_identity_fail_closed_or_owner_resolve():
    _assert_attempt(
        "attempt_028_blocked_unknown_consumer_class",
        decision="BLOCKED_UNKNOWN_CONSUMER_CLASS",
        blocked_reason="BLOCKED_UNKNOWN_CONSUMER_CLASS",
        owner_override=False,
    )
    _assert_attempt(
        "attempt_029_blocked_unknown_agent_role",
        decision="BLOCKED_UNKNOWN_AGENT_ROLE",
        blocked_reason="BLOCKED_UNKNOWN_AGENT_ROLE",
        owner_override=False,
    )
    _assert_attempt(
        "attempt_030_blocked_unknown_parameter_target",
        decision="BLOCKED_PARAMETER_TARGET_UNKNOWN",
        blocked_reason="BLOCKED_PARAMETER_TARGET_UNKNOWN",
        owner_override=False,
    )
    _assert_attempt(
        "attempt_020_allowed_missing_target_owner_approved_missing_value",
        decision="ALLOWED_BY_OWNER_OVERRIDE_SATISFIED",
        blocked_reason="BLOCKED_PARAMETER_TARGET_UNKNOWN",
        owner_override=True,
    )


def test_static_runtime_live_quantum_and_profit_examples_create_no_real_artifacts():
    runtime = _attempt("attempt_034_proof_runtime_consumer_no_runtime_artifact")
    live = _attempt("attempt_033_proof_live_consumer_no_live_or_order_artifact")
    quantum = _attempt("attempt_035_proof_quantum_backend_no_backend_artifact")
    profit = _attempt("attempt_036_proof_no_profit_artifact_created")
    report = _report()

    assert runtime["requested_consumer_class"] == "RUNTIME_RESOLVER_INPUT"
    assert runtime["real_runtime_artifact_created"] is False
    assert live["requested_consumer_class"] == "LIVE_EXECUTION"
    assert live["real_live_artifact_created"] is False
    assert live["real_order_artifact_created"] is False
    assert quantum["requested_consumer_class"] == "QUANTUM_BACKEND_EXECUTION"
    assert quantum["real_quantum_backend_artifact_created"] is False
    assert profit["real_profit_artifact_created"] is False
    assert report["real_runtime_artifact_created"] is False
    assert report["real_live_artifact_created"] is False
    assert report["real_order_artifact_created"] is False
    assert report["real_quantum_backend_artifact_created"] is False
    assert report["real_profit_artifact_created"] is False


def test_no_atomicrows_bundle_or_hash_is_created():
    report = _report()

    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
    assert report["bundle_file_present"] is True
    assert report["bundle_sha_present"] is False


def test_owner_override_and_validation_authority_counts_are_nonblocking():
    report = _report()

    assert report["owner_override_access_attempt_count"] >= 8
    assert report["owner_override_access_allowed_count"] >= 8
    assert report["owner_override_access_blocked_count"] == 0
    assert report["validators_block_owner_override_count"] == 0
    assert report["codex_blocks_owner_override_count"] == 0
    assert report["qtt_agents_block_owner_override_count"] == 0
    assert report["generated_reports_block_owner_override_count"] == 0
    assert report["validation_gates_block_owner_override_count"] == 0


def test_report_counts_cover_required_access_surfaces():
    report = _report()

    assert report["attempted_access_count"] == 38
    assert report["allowed_access_count"] >= 20
    assert report["blocked_access_count"] >= 8
    assert report["runtime_consumer_access_allowed_count"] >= 1
    assert report["live_consumer_access_allowed_count"] >= 1
    assert report["quantum_backend_consumer_access_allowed_count"] >= 1
    assert report["optimizer_consumer_access_allowed_count"] >= 1
    assert report["risk_consumer_access_allowed_count"] >= 1
    assert report["sizing_consumer_access_allowed_count"] >= 1
    assert report["replay_paper_consumer_access_allowed_count"] >= 1
    assert report["source_evidence_consumer_access_allowed_count"] >= 1
    assert report["research_consumer_access_allowed_count"] >= 1


def test_uses_pull_request_number_as_authority_remains_false():
    report = _report()

    assert _attempt("attempt_038_proof_pull_request_numbers_not_authority")[
        "access_decision"
    ] == "ALLOWED_BY_ROW_BINDING"
    assert report["uses_pr_number_as_authority"] is False
    assert report["final_ready"] is False
    assert report["authority_boundary_all_false"] is True
