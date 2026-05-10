from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import validate_qtt_owner_global_override_authority as gate


REPO_ROOT = Path(".")
GLOBAL_SCHEMA = Path("schemas/governance/qtt_owner_global_override_authority.schema.json")
RECEIPT_SCHEMA = Path("schemas/governance/qtt_owner_override_receipt.schema.json")
APPROVAL_REQUEST_SCHEMA = Path("schemas/governance/qtt_owner_approval_request.schema.json")
POLICY = Path("docs/master_plan/governance/QTTOwnerGlobalOverrideAuthority.yaml")
AUTHORITY_FIXTURE = Path(
    "tests/fixtures/governance/"
    "synthetic_qtt_owner_global_override_authority.v1.fixture.json"
)
RECEIPT_FIXTURE = Path(
    "tests/fixtures/governance/synthetic_qtt_owner_override_receipt.v1.fixture.json"
)
APPROVAL_REQUEST_FIXTURE = Path(
    "tests/fixtures/governance/synthetic_qtt_owner_approval_request.v1.fixture.json"
)
REPORT = Path("docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(AUTHORITY_FIXTURE)


def _case_by_class() -> dict[str, dict]:
    return {
        record["requirement_class"]: record
        for record in _fixture()["requirement_satisfaction_cases"]
    }


def test_owner_global_override_static_surface_validates_and_report_is_deterministic():
    failures, report = gate.validate_static_surface(
        repo_root=REPO_ROOT,
        report_path=REPORT,
    )
    assert failures == []
    assert report == _load(REPORT)

    second = gate.build_report(
        fixture=_fixture(),
        receipt_fixture=_load(RECEIPT_FIXTURE),
        approval_request_fixture=_load(APPROVAL_REQUEST_FIXTURE),
        receipt_schema_present=RECEIPT_SCHEMA.exists(),
        approval_request_schema_present=APPROVAL_REQUEST_SCHEMA.exists(),
    )
    assert second == report
    assert second["generated_at_utc"] == gate.DETERMINISTIC_CREATED_AT


def test_schemas_policy_and_fixture_include_all_owner_tokens_options_domains_and_classes():
    schema = _load(GLOBAL_SCHEMA)
    receipt_schema = _load(RECEIPT_SCHEMA)
    request_schema = _load(APPROVAL_REQUEST_SCHEMA)
    fixture = _fixture()
    policy, policy_failures = gate._parse_policy_yaml(POLICY)

    assert policy_failures == []
    assert set(gate.OWNER_APPROVED_VALUE_TOKENS).issubset(
        schema["$defs"]["owner_approved_value_token"]["enum"]
    )
    assert set(gate.OWNER_APPROVED_VALUE_TOKENS).issubset(
        receipt_schema["$defs"]["owner_approved_value_token"]["enum"]
    )
    assert set(gate.OWNER_APPROVED_VALUE_TOKENS).issubset(
        request_schema["$defs"]["owner_approved_value_token"]["enum"]
    )
    assert set(gate.OWNER_DECISION_OPTIONS).issubset(policy["owner_decision_options"])
    assert set(gate.REQUIRED_DOMAINS).issubset(fixture["covered_domains"])
    assert set(gate.REQUIRED_REQUIREMENT_CLASSES).issubset(
        fixture["covered_requirement_classes"]
    )


def test_owner_override_is_accepted_across_all_covered_domains_and_requirement_classes():
    fixture = _fixture()
    cases = fixture["requirement_satisfaction_cases"]
    assert len(cases) == len(gate.REQUIRED_REQUIREMENT_CLASSES)

    seen_classes = {record["requirement_class"] for record in cases}
    seen_domains = {record["domain"] for record in cases}
    assert set(gate.REQUIRED_REQUIREMENT_CLASSES).issubset(seen_classes)
    assert set(gate.REQUIRED_DOMAINS).issubset(seen_domains)

    for record in cases:
        assert record["owner_override_allowed"] is True
        assert record["owner_override_applied"] is True
        assert record["blocks_qtt_when_owner_override_present"] is False
        assert record["final_qtt_internal_status"] == "OWNER_OVERRIDE_SATISFIED"
        assert record["owner_override_satisfaction_basis"] in gate.OWNER_APPROVED_VALUE_TOKENS
        assert record["owner_approved_value"] in gate.OWNER_APPROVED_VALUE_TOKENS


def test_validators_do_not_block_owner_override_when_normal_artifacts_are_absent():
    source_case = _case_by_class()["SOURCE_EVIDENCE_REQUIREMENT_SATISFACTION"]

    assert source_case["owner_override_satisfaction_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert source_case["externally_verified_status"] == "OWNER_APPROVED_NOT_EXTERNALLY_VERIFIED"
    assert source_case["artifact_exists_status"] is False
    assert source_case["receipt_exists_status"] is False
    assert source_case["blocks_qtt_when_owner_override_present"] is False
    assert source_case["final_qtt_internal_status"] == "OWNER_OVERRIDE_SATISFIED"

    mutated = copy.deepcopy(source_case)
    mutated["blocks_qtt_when_owner_override_present"] = True
    fixture = _fixture()
    fixture["requirement_satisfaction_cases"][12] = mutated
    failures = gate.validate_authority_fixture(fixture)
    assert any("blocks_qtt_when_owner_override_present must be false" in item for item in failures)


def test_source_final_validation_and_missing_value_blockers_support_owner_global_override():
    cases = _case_by_class()
    assert (
        cases["SOURCE_EVIDENCE_REQUIREMENT_SATISFACTION"][
            "owner_override_satisfaction_basis"
        ]
        == "OWNER_GLOBAL_OVERRIDE"
    )
    assert (
        cases["FINAL_READINESS_BLOCKER_REQUIREMENT"]["owner_override_satisfaction_basis"]
        == "OWNER_GLOBAL_OVERRIDE"
    )
    assert (
        cases["VALIDATION_GATE_REQUIREMENT"]["owner_override_satisfaction_basis"]
        == "OWNER_GLOBAL_OVERRIDE"
    )
    assert (
        cases["MISSING_REQUIRED_VALUE_REQUIREMENT"]["owner_override_satisfaction_basis"]
        == "OWNER_GLOBAL_OVERRIDE"
    )
    assert cases["MISSING_REQUIRED_VALUE_REQUIREMENT"]["owner_approved_value"] == "OWNER_APPROVED"


def test_chatgpt_codex_validators_gates_reports_and_qtt_agents_have_no_owner_authority():
    fixture = _fixture()
    report = _load(REPORT)
    for field in gate.AUTHORITY_FALSE_FIELDS:
        assert fixture[field] is False
        assert report[field] is False
    for count_field in [
        "validators_block_owner_override_count",
        "codex_blocks_owner_override_count",
        "qtt_agents_block_owner_override_count",
        "chatgpt_blocks_owner_override_count",
        "generated_reports_block_owner_override_count",
        "validation_gates_block_owner_override_count",
    ]:
        assert report[count_field] == 0


def test_agents_may_create_approval_requests_but_may_not_approve_for_owner():
    fixture = _load(APPROVAL_REQUEST_FIXTURE)
    requests = fixture["owner_approval_requests"]

    assert {
        request["requesting_agent"] for request in requests
    } == {
        "SYNTHETIC_ATOMICROWS_AGENT",
        "SYNTHETIC_SOURCE_EVIDENCE_AGENT",
        "SYNTHETIC_OPTIMIZER_AGENT",
        "SYNTHETIC_RUNTIME_AGENT",
        "SYNTHETIC_LIVE_CANARY_AGENT",
    }
    for request in requests:
        assert request["owner_decision_pending"] is True
        assert request["agent_may_approve_for_owner"] is False
        assert request["codex_may_approve_for_owner"] is False
        assert request["chatgpt_may_approve_for_owner"] is False
        assert request["future_dashboard_menu_supported"] is True


def test_future_dashboard_menu_is_static_foundation_only_not_runtime_ui():
    authority_fixture = _fixture()
    approval_fixture = _load(APPROVAL_REQUEST_FIXTURE)
    report = _load(REPORT)

    assert authority_fixture["future_dashboard_menu_supported"] is True
    assert report["future_dashboard_menu_supported"] is True
    assert approval_fixture["no_claim_flags"]["creates_dashboard_ui"] is False
    assert approval_fixture["no_claim_flags"]["creates_runtime_service"] is False
    assert approval_fixture["no_claim_flags"]["creates_live_trading_execution"] is False


def test_owner_override_receipt_foundation_includes_required_static_scopes():
    receipt_fixture = _load(RECEIPT_FIXTURE)
    scopes = {
        receipt["approval_scope"]
        for receipt in receipt_fixture["owner_override_receipts"]
    }

    assert {"GLOBAL", "DOMAIN", "PARAMETER_FAMILY", "ROW", "AGENT", "REQUIREMENT", "VALUE"}.issubset(scopes)
    for receipt in receipt_fixture["owner_override_receipts"]:
        assert receipt["authority"] == "OWNER_GLOBAL_OVERRIDE"
        assert receipt["created_by_owner"] is True
        assert receipt["blocks_qtt_when_owner_override_present"] is False
        assert receipt["deterministic_created_at_utc"] == gate.DETERMINISTIC_CREATED_AT
        assert receipt["receipt_status"] == "SYNTHETIC_STATIC_FOUNDATION_NOT_REAL_RUNTIME_RECEIPT"


def test_report_uses_no_pr_number_authority_and_preserves_static_boundaries():
    report = _load(REPORT)
    fixture = _fixture()

    assert report["uses_pr_number_as_authority"] is False
    assert report["authority_boundary_all_false"] is True
    assert fixture["authority_boundary"]["uses_pr_number_as_authority"] is False
    for field in gate.AUTHORITY_BOUNDARY_FALSE_FIELDS:
        assert fixture["authority_boundary"][field] is False
