from __future__ import annotations

import json
from pathlib import Path

from tools import build_master_plan_implementation_coverage_ledger as builder
from tools import validate_master_plan_implementation_coverage_ledger as validator


REPO_ROOT = Path(".")
LEDGER_PATH = Path("docs/master_plan/generated/MasterPlanImplementationCoverageLedger.json")
SCHEMA_PATH = Path(
    "schemas/master_plan/master_plan_implementation_coverage_ledger.schema.json"
)
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
ATOMICROWS_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
ATOMICROWS_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")

EXPECTED_STRONG_MARKERS = {
    38: "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_STATIC_VALIDATION_OK",
    39: "SOURCE_EVIDENCE_ACCEPTANCE_CONSUMER_CONTRACT_STATIC_VALIDATION_OK",
    40: "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_OK",
    41: "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_CHECK_OK",
    42: "STAGE1_RUNTIME_RESOLVER_TO_REPLAY_PAPER_HANDOFF_CHECK_OK",
    43: "STAGE1_CONCURRENT_REPLAY_PAPER_CONTRACT_CHECK_OK",
    44: "STAGE1_DUAL_RESULT_REVIEW_CONTRACT_CHECK_OK",
    45: "STAGE1_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_CHECK_OK",
    46: "STAGE1_THREE_VENUE_CANARY_ELIGIBILITY_CONTRACT_CHECK_OK",
}

EXPECTED_PR47_MARKERS = {
    "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_BUILT",
    "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_OK",
}

EXPECTED_PR48_MARKERS = {
    "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_BUILT",
    "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_OK",
}

AUTHORITY_FIELDS = [
    "ledger_is_master_plan_authority",
    "ledger_is_source_fact_authority",
    "ledger_is_connector_semantic_authority",
    "ledger_is_runtime_authority",
    "ledger_is_order_authority",
    "ledger_is_atomicrows_authority",
    "ledger_is_profit_evidence",
    "ledger_may_select_next_pr_without_master_plan_crosscheck",
]

PR_AUTHORITY_FLAGS = [
    "source_fact_acceptance_created_flag",
    "connector_semantics_populated_flag",
    "runtime_authority_created_flag",
    "runtime_resolver_snapshot_created_flag",
    "live_reachability_created_flag",
    "order_authority_created_flag",
    "atomicrows_bundle_created_flag",
    "atomicrows_sha_created_flag",
    "profit_claim_created_flag",
    "blocker_reduction_created_flag",
]


def _load_generated_ledger() -> dict:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_generated_ledger_validates_against_schema_and_fail_closed_validator():
    ledger = _load_generated_ledger()
    schema = _load_schema()

    assert validator.validate_ledger(
        ledger,
        schema,
        repo_root=REPO_ROOT,
        ledger_path=LEDGER_PATH,
    ) == []


def test_builder_output_is_deterministic_across_two_runs(tmp_path):
    first = builder.build_ledger(REPO_ROOT)
    second = builder.build_ledger(REPO_ROOT)

    first_out = tmp_path / "first.json"
    second_out = tmp_path / "second.json"
    builder.write_ledger(first, first_out)
    builder.write_ledger(second, second_out)

    assert first == second
    assert first_out.read_text(encoding="utf-8") == second_out.read_text(
        encoding="utf-8"
    )


def test_strong_pr_38_through_46_records_exist_with_expected_validation_markers():
    ledger = _load_generated_ledger()
    records = {record["pr_number"]: record for record in ledger["pr_records"]}

    assert sorted(EXPECTED_STRONG_MARKERS) == list(range(38, 47))
    for pr_number, marker in EXPECTED_STRONG_MARKERS.items():
        record = records[pr_number]
        assert record["review_status"] == "VERIFIED"
        assert marker in record["validation_markers"]
        assert record["master_plan_section_ids"]
        assert record["validator_tools"]


def test_pr_1_through_37_records_are_stable_review_required_tracking():
    ledger = _load_generated_ledger()
    records = {record["pr_number"]: record for record in ledger["pr_records"]}

    for pr_number in range(1, 38):
        record = records[pr_number]
        assert record["implementation_status"] == "REVIEW_REQUIRED"
        assert record["review_status"] == "SECTION_MAPPING_REQUIRES_OWNER_REVIEW"
        assert record["master_plan_section_ids"] == []
        assert record["branch_name_if_known"] is None
        assert record["local_commit_if_known"] is None
        assert record["merge_commit_if_known"] is None


def test_pr47_tracking_record_is_review_required_without_checkout_specific_metadata():
    ledger = _load_generated_ledger()
    records = {record["pr_number"]: record for record in ledger["pr_records"]}
    record = records[47]

    assert record["implementation_status"] == "TRACKING_ONLY"
    assert record["review_status"] == "SECTION_MAPPING_REQUIRES_OWNER_REVIEW"
    assert record["master_plan_section_ids"] == []
    assert record["branch_name_if_known"] is None
    assert record["local_commit_if_known"] is None
    assert record["merge_commit_if_known"] is None
    assert EXPECTED_PR47_MARKERS.issubset(set(record["validation_markers"]))
    assert "tools/build_master_plan_implementation_coverage_ledger.py" in record[
        "validator_tools"
    ]
    assert "tools/validate_master_plan_implementation_coverage_ledger.py" in record[
        "validator_tools"
    ]


def test_pr48_and_pr49_tracking_records_exist_without_checkout_specific_metadata():
    ledger = _load_generated_ledger()
    records = {record["pr_number"]: record for record in ledger["pr_records"]}

    assert ledger["coverage_summary"]["total_pr_records"] == 49

    pr48 = records[48]
    assert pr48["pr_title_or_subject"] == "Fix coverage ledger determinism"
    assert pr48["implementation_status"] == "TRACKING_ONLY"
    assert pr48["review_status"] == "VERIFIED"
    assert pr48["master_plan_section_ids"] == []
    assert pr48["branch_name_if_known"] is None
    assert pr48["local_commit_if_known"] is None
    assert pr48["merge_commit_if_known"] is None
    assert EXPECTED_PR48_MARKERS.issubset(set(pr48["validation_markers"]))
    assert "non-authoritative implementation coverage tracking only" in pr48[
        "master_plan_anchor_terms"
    ]

    pr49 = records[49]
    assert pr49["pr_title_or_subject"] == "Ignore validation temp artifacts"
    assert (
        pr49["implemented_subject"]
        == ".tmp/ gitignore hygiene for validation temp artifacts"
    )
    assert pr49["implementation_status"] == "TRACKING_ONLY"
    assert pr49["review_status"] == "VERIFIED"
    assert pr49["master_plan_section_ids"] == []
    assert pr49["branch_name_if_known"] is None
    assert pr49["local_commit_if_known"] is None
    assert pr49["merge_commit_if_known"] is None
    assert ".gitignore" in pr49["created_or_changed_paths"]


def test_validator_fails_closed_when_pr48_or_pr49_tracking_record_is_missing(tmp_path):
    ledger = builder.build_ledger(REPO_ROOT)
    ledger["pr_records"] = [
        record
        for record in ledger["pr_records"]
        if record["pr_number"] not in {48, 49}
    ]
    schema = _load_schema()

    failures = validator.validate_ledger(
        ledger,
        schema,
        repo_root=REPO_ROOT,
        ledger_path=tmp_path / "missing_tracking_records.json",
    )

    assert any("PR #1 through PR #49" in failure for failure in failures)


def test_ledger_authority_flags_remain_false_for_forbidden_authorities():
    ledger = _load_generated_ledger()

    for field in AUTHORITY_FIELDS:
        assert ledger["authority"][field] is False
    assert (
        ledger["authority"]["authority_class"]
        == "NON_AUTHORITATIVE_IMPLEMENTATION_COVERAGE_LEDGER"
    )
    assert ledger["authority"]["owner_review_required_for_uncertain_mapping"] is True

    for record in ledger["pr_records"]:
        for field in PR_AUTHORITY_FLAGS:
            assert record[field] is False
        boundary = record["authority_boundary"]
        assert boundary["creates_source_fact_acceptance"] is False
        assert boundary["populates_production_connector_semantics"] is False
        assert boundary["creates_runtime_resolver_snapshot"] is False
        assert boundary["creates_live_reachability"] is False
        assert boundary["creates_order_authority"] is False
        assert boundary["creates_atomicrows_bundle"] is False
        assert boundary["creates_profit_evidence"] is False


def test_future_pr_tracking_policy_requires_regeneration_and_master_plan_crosscheck():
    ledger = _load_generated_ledger()
    policy = ledger["future_pr_tracking_policy"]

    assert policy["future_pr_must_add_or_regenerate_ledger_coverage"] is True
    assert policy["ledger_does_not_replace_master_plan_crosscheck"] is True
    assert policy["ledger_may_not_select_next_pr_without_master_plan_crosscheck"] is True
    assert {
        "PR number",
        "section IDs",
        "validator marker",
        "generated report",
        "authority boundary",
        "next allowed consumer",
        "review required flag",
    }.issubset(set(policy["required_future_pr_fields"]))


def test_builder_does_not_mutate_master_plan_or_atomicrows_paths(tmp_path):
    before = MASTER_PLAN_PATH.read_bytes()
    output = tmp_path / "ledger.json"

    builder.write_ledger(builder.build_ledger(REPO_ROOT), output)

    assert MASTER_PLAN_PATH.read_bytes() == before
    assert not ATOMICROWS_BUNDLE.exists()
    assert not ATOMICROWS_SHA.exists()
