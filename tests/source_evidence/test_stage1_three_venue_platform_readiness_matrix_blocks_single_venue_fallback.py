from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_three_venue_canary_eligibility_contract_check import (
    CANONICAL_PLATFORMS,
    PLATFORM_SCOPE_TYPE,
    READINESS_MATRIX_TYPE,
    validate_gate_case_record,
    validate_readiness_matrix_record,
)


READINESS_MATRIX_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
    "stage1_three_venue_platform_readiness_matrix.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/three_venue_canary_eligibility/"
    "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _matrix() -> dict:
    return copy.deepcopy(_fixture()["three_venue_platform_readiness_matrix_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["three_venue_canary_eligibility_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_readiness_matrix_schema_requires_all_three_platforms_and_blocks_fallback():
    schema = _load(READINESS_MATRIX_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["three_venue_platform_readiness_matrix_type"]["const"] == (
        READINESS_MATRIX_TYPE
    )
    assert props["platform_scope_type"]["const"] == PLATFORM_SCOPE_TYPE
    assert props["all_three_platforms_required_flag"]["const"] is True
    assert props["matrix_entries_non_live_flag"]["const"] is True
    assert props["matrix_entries_non_execution_flag"]["const"] is True
    assert props["silent_single_venue_fallback_allowed_flag"]["const"] is False
    assert props["partial_platform_launch_allowed_flag"]["const"] is False
    assert (
        props["partial_platform_launch_requires_future_owner_risk_reduction_override_flag"]["const"]
        is True
    )


def test_readiness_matrix_lists_three_synthetic_non_live_non_execution_placeholders():
    record = _matrix()

    assert record["platform_scope_type"] == PLATFORM_SCOPE_TYPE
    assert record["platform_scope_identities"] == CANONICAL_PLATFORMS
    assert [entry["platform_id"] for entry in record["platform_readiness_entries"]] == (
        CANONICAL_PLATFORMS
    )
    assert {entry["readiness_state"] for entry in record["platform_readiness_entries"]} <= {
        "BLOCKED_STATIC_CONTRACT_ONLY",
        "SOURCE_REQUIRED",
        "FUTURE_GATE_REQUIRED",
    }
    for entry in record["platform_readiness_entries"]:
        assert entry["synthetic_placeholder_only_flag"] is True
        assert entry["non_live_flag"] is True
        assert entry["non_execution_flag"] is True
        assert entry["connector_semantics_created_flag"] is False
        assert entry["live_api_reachability_created_flag"] is False
        assert entry["order_placement_authority_created_flag"] is False
        assert entry["runtime_cash_claim_created_flag"] is False
    assert validate_readiness_matrix_record(record) == []


def test_readiness_matrix_rejects_missing_or_noncanonical_platform_scope_and_silent_fallbacks():
    mutations = [
        ("missing KALSHI", ["POLYMARKET", "FORECASTEX_IBKR"], "platform_scope_identities"),
        ("missing POLYMARKET", ["KALSHI", "FORECASTEX_IBKR"], "platform_scope_identities"),
        ("missing FORECASTEX_IBKR", ["KALSHI", "POLYMARKET"], "platform_scope_identities"),
        (
            "noncanonical third venue",
            ["KALSHI", "POLYMARKET", "NONCANONICAL_THIRD_VENUE"],
            "platform_scope_identities",
        ),
    ]

    for _label, platforms, expected_fragment in mutations:
        record = _matrix()
        record["platform_scope_identities"] = platforms
        failures = validate_readiness_matrix_record(record)
        _assert_failure_contains(failures, expected_fragment)

    record = _matrix()
    record["platform_readiness_entries"] = record["platform_readiness_entries"][:1]
    failures = validate_readiness_matrix_record(record)
    _assert_failure_contains(failures, "platform_readiness_entries must contain exactly three")

    record = _matrix()
    record["silent_single_venue_fallback_allowed_flag"] = True
    record["partial_platform_launch_allowed_flag"] = True
    record["future_owner_risk_reduction_override_present_flag"] = True
    failures = validate_readiness_matrix_record(record)
    for fragment in [
        "silent_single_venue_fallback_allowed_flag",
        "partial_platform_launch_allowed_flag",
        "future_owner_risk_reduction_override_present_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_platform_missing_noncanonical_single_venue_and_partial_fallback():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_PLATFORM_MISSING_KALSHI": "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_KALSHI_MISSING",
        "BLOCKED_PLATFORM_MISSING_POLYMARKET": (
            "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_POLYMARKET_MISSING"
        ),
        "BLOCKED_PLATFORM_MISSING_FORECASTEX_IBKR": (
            "BLOCKED_CANARY_ELIGIBILITY_PLATFORM_FORECASTEX_IBKR_MISSING"
        ),
        "BLOCKED_NONCANONICAL_THIRD_VENUE_IDENTITY": (
            "BLOCKED_CANARY_ELIGIBILITY_NONCANONICAL_THIRD_VENUE"
        ),
        "BLOCKED_SINGLE_VENUE_FALLBACK_CLAIM": (
            "BLOCKED_CANARY_ELIGIBILITY_SINGLE_VENUE_FALLBACK_CLAIM"
        ),
        "BLOCKED_PARTIAL_PLATFORM_SILENT_FALLBACK_CLAIM": (
            "BLOCKED_CANARY_ELIGIBILITY_PARTIAL_PLATFORM_SILENT_FALLBACK_CLAIM"
        ),
    }

    for fixture_case, expected_state in expected.items():
        record = cases[fixture_case]
        assert record["expected_gate_state"] == expected_state
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []
