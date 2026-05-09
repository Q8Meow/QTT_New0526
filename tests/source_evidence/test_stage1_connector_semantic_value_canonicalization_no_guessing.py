from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_connector_semantic_value_canonicalize import (
    VALID_CANONICALIZATION_STATE,
    validate_canonicalization_record,
    validate_canonicalization_fixture,
)


FIXTURE = Path(
    "tests/fixtures/source_evidence/connector_semantic_binding/"
    "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
)
CANONICALIZATION_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_value_canonicalization.schema.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _canonicalization_by_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["semantic_value_canonicalization_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_semantic_value_canonicalization_schema_encodes_no_guessing_rules():
    schema = json.loads(CANONICALIZATION_SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]

    assert props["canonicalization_may_convert_representation_but_may_not_change_meaning"]["const"] is True
    assert props["canonicalization_requires_accepted_source_evidence_export_record"]["const"] is True
    assert props["canonicalization_requires_target_field_acceptance_ledger_record"]["const"] is True
    assert props["canonicalization_requires_source_to_connector_field_binding_record"]["const"] is True
    assert props["canonicalization_requires_explicit_value_type_unit_scale_and_scope"]["const"] is True
    assert props["canonicalization_may_not_zero_fill_missing_value"]["const"] is True
    assert props["canonicalization_may_not_use_owner_policy_value_when_source_packet_required"]["const"] is True
    assert props["canonicalization_may_not_use_runtime_observed_value_when_source_packet_required"]["const"] is True
    assert props["canonicalization_failure_blocks_binding_packet_creation"]["const"] is True


def test_semantic_value_canonicalization_never_changes_meaning():
    record = copy.deepcopy(_canonicalization_by_case()["VALID_SYNTHETIC_BINDING_NONLIVE_ONLY"])
    assert record["bound_value_original"] != record["bound_value_canonical"]
    assert (
        record["semantic_meaning_preservation_key_original"]
        == record["semantic_meaning_preservation_key_canonical"]
    )
    assert validate_canonicalization_record(record) == []

    record["semantic_meaning_preservation_key_canonical"] = "SYNTHETIC_DIFFERENT_MEANING"
    failures = validate_canonicalization_record(record)

    _assert_failure_contains(failures, "may not change semantic meaning")


def test_canonicalization_blocks_missing_unit_scale_scope_guessing_zero_fill_owner_value_and_runtime_value_misuse():
    records = _canonicalization_by_case()
    assert validate_canonicalization_fixture(_fixture(), repo_root=Path(".")) == []

    missing_unit = copy.deepcopy(records["VALID_SYNTHETIC_BINDING_NONLIVE_ONLY"])
    missing_unit["bound_value_unit_or_scale"] = ""
    _assert_failure_contains(
        validate_canonicalization_record(missing_unit),
        "bound_value_unit_or_scale",
    )

    missing_scope = copy.deepcopy(records["VALID_SYNTHETIC_BINDING_NONLIVE_ONLY"])
    missing_scope["bound_value_scope"] = "MISSING_SCOPE"
    _assert_failure_contains(
        validate_canonicalization_record(missing_scope),
        "bound_value_scope",
    )

    zero_fill = records["BLOCKED_ZERO_FILL_INVENTED_MISSING_VALUE_ATTEMPT"]
    assert zero_fill["canonicalization_state"] == "BLOCKED_ZERO_FILL"
    assert zero_fill["binding_packet_creation_allowed_flag"] is False
    assert zero_fill["semantic_value_invention_attempt_flag"] is True
    assert zero_fill["zero_fill_missing_value_attempt_flag"] is True

    owner_policy = records["BLOCKED_OWNER_POLICY_SUBSTITUTION_ATTEMPT"]
    assert owner_policy["canonicalization_state"] == "BLOCKED_OWNER_POLICY_SUBSTITUTION"
    assert owner_policy["owner_policy_substitution_attempt_flag"] is True
    assert owner_policy["binding_packet_creation_allowed_flag"] is False

    runtime_observed = records["BLOCKED_RUNTIME_OBSERVED_VALUE_SUBSTITUTION_ATTEMPT"]
    assert runtime_observed["canonicalization_state"] == "BLOCKED_RUNTIME_OBSERVED_SUBSTITUTION"
    assert runtime_observed["runtime_observed_value_substitution_attempt_flag"] is True
    assert runtime_observed["binding_packet_creation_allowed_flag"] is False

    guessed_as_valid = copy.deepcopy(zero_fill)
    guessed_as_valid["canonicalization_state"] = VALID_CANONICALIZATION_STATE
    guessed_as_valid["binding_packet_creation_allowed_flag"] = True
    failures = validate_canonicalization_record(guessed_as_valid)
    _assert_failure_contains(failures, "zero-fill")


def test_canonicalization_rejects_candidate_source_evidence_as_accepted_evidence():
    record = copy.deepcopy(_canonicalization_by_case()["BLOCKED_SCHEMA_ERROR_BINDING"])
    assert record["source_value_origin"] == "CANDIDATE_SOURCE_EVIDENCE_PACKET_NOT_ACCEPTED"
    assert record["canonicalization_state"] == "BLOCKED_SCHEMA_ERROR"
    assert record["binding_packet_creation_allowed_flag"] is False

    record["canonicalization_state"] = VALID_CANONICALIZATION_STATE
    record["binding_packet_creation_allowed_flag"] = True
    record["blocker_codes"] = []
    failures = validate_canonicalization_record(record)

    _assert_failure_contains(failures, "candidate source evidence")
