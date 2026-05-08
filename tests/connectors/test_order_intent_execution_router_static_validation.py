import copy
import json
from pathlib import Path

import pytest

from tools.validate_order_intent_execution_router_static import (
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    validate_order_intent_execution_router_fixture,
    validate_static_surface,
)

SCHEMA_PATH = Path("schemas/connectors/order_intent_execution_router_scaffolding.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/connectors/"
    "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def _intent(fixture: dict) -> dict:
    return fixture["order_intent_placeholders"][0]


def _gate(fixture: dict) -> dict:
    return fixture["execution_router_gate_placeholders"][0]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_order_intent_execution_router_static_validator_accepts_schema_and_fixture():
    assert validate_static_surface(schema_path=SCHEMA_PATH, fixture_path=FIXTURE_PATH) == []


def test_schema_uses_explicit_false_flag_defs_not_generic_false_map():
    schema = _schema()

    assert "false_flag_map" not in schema["$defs"]
    assert schema["properties"]["forbidden_action_flags"]["$ref"] == (
        "#/$defs/forbidden_action_flags"
    )
    assert schema["properties"]["fixture_no_claim_flags"]["$ref"] == (
        "#/$defs/fixture_no_claim_flags"
    )
    for def_name, expected_fields in {
        "forbidden_action_flags": FORBIDDEN_ACTION_FLAGS,
        "fixture_no_claim_flags": NO_CLAIM_FLAGS,
    }.items():
        definition = schema["$defs"][def_name]
        assert definition["additionalProperties"] is False
        assert set(definition["properties"]) == expected_fields
        assert set(definition["required"]) == expected_fields
        assert all(
            definition["properties"][field]["const"] is False
            for field in expected_fields
        )


@pytest.mark.parametrize(
    "mutate, expected_fragment",
    [
        (
            lambda schema: schema["$defs"]["forbidden_action_flags"].update(
                {"additionalProperties": {"const": False}}
            ),
            "forbidden_action_flags.additionalProperties",
        ),
        (
            lambda schema: schema["$defs"]["fixture_no_claim_flags"]["required"].remove(
                "creates_profit_evidence"
            ),
            "creates_profit_evidence",
        ),
        (
            lambda schema: schema["$defs"]["scope_flags"]["properties"][
                "runtime_use_allowed"
            ].update({"const": True}),
            "runtime_use_allowed",
        ),
        (
            lambda schema: schema["properties"]["mode"].update({"const": "OPTIONAL"}),
            "schema.properties.mode",
        ),
        (
            lambda schema: schema["$defs"]["source_required_order_semantics"][
                "properties"
            ]["order_type_semantics"].clear(),
            "order_type_semantics",
        ),
    ],
)
def test_schema_mutation_relaxations_fail_static_validation(
    tmp_path, mutate, expected_fragment
):
    schema = _schema()
    mutate(schema)
    schema_path = _write_json(tmp_path / "schema.json", schema)

    failures = validate_static_surface(schema_path=schema_path, fixture_path=FIXTURE_PATH)

    _assert_failure_contains(failures, expected_fragment)


def test_valid_synthetic_fixture_is_static_disabled_and_unbound():
    fixture = _fixture()

    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["deterministic_output"] is True
    assert fixture["runtime_resolver_snapshot_reference"] == "UNBOUND"
    assert _intent(fixture)["intent_state"] == "PLACEHOLDER_ONLY_NOT_RUNTIME_INTENT"
    assert _intent(fixture)["runtime_state"] == "DISABLED"
    assert _gate(fixture)["router_state"] == "GATE_PLACEHOLDER_ONLY_NOT_EXECUTABLE"
    assert _gate(fixture)["final_order_submission_authority_present"] is False
    assert validate_order_intent_execution_router_fixture(fixture) == []


def test_missing_required_authority_scope_flag_fails():
    fixture = _fixture()
    fixture["scope_flags"].pop("final_order_submission_authority_disabled")

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "final_order_submission_authority_disabled")


@pytest.mark.parametrize(
    "flag",
    [
        "runtime_enabled",
        "runtime_execution_enabled",
        "live_enabled",
        "order_execution_enabled",
        "profit_claim_enabled",
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "external_fact_acceptance_enabled",
        "connector_binding_enabled",
        "connector_semantic_binding_enabled",
        "private_state_fetch_enabled",
    ],
)
def test_runtime_live_order_profit_source_binding_and_private_state_flags_true_fail(flag):
    fixture = _fixture()
    fixture["forbidden_action_flags"][flag] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, flag)


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        fixture["forbidden_action_flags"][flag] = True

        failures = validate_order_intent_execution_router_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_every_no_claim_flag_fails_when_true():
    for flag in sorted(NO_CLAIM_FLAGS):
        fixture = _fixture()
        fixture["fixture_no_claim_flags"][flag] = True

        failures = validate_order_intent_execution_router_fixture(fixture)

        _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "field",
    [
        "submits_orders",
        "cancels_orders",
        "reduces_orders",
        "closes_orders",
        "replaces_orders",
        "amends_orders",
        "creates_final_order_release_authority",
    ],
)
def test_real_order_submission_cancel_reduce_close_replace_amend_authority_claims_fail(
    field,
):
    fixture = _fixture()
    fixture["fixture_no_claim_flags"][field] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, field)


def test_live_signer_path_claims_fail():
    fixture = _fixture()
    gate = _gate(fixture)
    gate["live_signer_path_reference"] = "SYNTHETIC_SIGNER_PATH_CLAIM"
    gate["live_signer_path_present"] = True
    fixture["forbidden_action_flags"]["live_signer_path_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_live_signer_path"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "live_signer_path_reference")
    _assert_failure_contains(failures, "live_signer_path_present")
    _assert_failure_contains(failures, "live_signer_path_enabled")
    _assert_failure_contains(failures, "creates_live_signer_path")


def test_venue_write_connectivity_claims_fail():
    fixture = _fixture()
    gate = _gate(fixture)
    gate["venue_write_connectivity_reference"] = "SYNTHETIC_WRITE_CONNECTIVITY_CLAIM"
    gate["venue_write_connectivity_present"] = True
    fixture["forbidden_action_flags"]["venue_write_connectivity_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_venue_write_connectivity"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "venue_write_connectivity_reference")
    _assert_failure_contains(failures, "venue_write_connectivity_present")
    _assert_failure_contains(failures, "venue_write_connectivity_enabled")
    _assert_failure_contains(failures, "creates_venue_write_connectivity")


def test_venue_specific_order_semantic_values_fail_unless_source_required_or_unbound():
    fixture = _fixture()
    intent = _intent(fixture)
    intent["source_required_order_intent_fields"]["order_type_semantics"] = "LIMIT"
    intent["source_required_order_intent_fields"]["order_side_semantics"] = "BUY"
    intent["venue_reference"] = "SYNTHETIC_POPULATED_VENUE_REFERENCE"
    intent["semantic_binding_state"] = "BOUND"

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "order_type_semantics")
    _assert_failure_contains(failures, "order_side_semantics")
    _assert_failure_contains(failures, "venue_reference")
    _assert_failure_contains(failures, "semantic_binding_state must be UNBOUND")


@pytest.mark.parametrize(
    "fragment",
    [
        "KALSHI",
        "POLYMARKET",
        "FORECASTX",
        "FORECASTEX",
        "IBKR",
        "HTTP",
        "HTTPS",
        "API",
        "ENDPOINT",
    ],
)
def test_real_venue_or_api_fragments_in_order_intent_ids_fail(fragment):
    fixture = _fixture()
    _intent(fixture)["intent_contract_id"] = f"SYNTHETIC_{fragment}_ORDER_INTENT"

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "forbidden live/source/private fragment")


def test_real_venue_or_api_fragments_in_non_reference_strings_fail():
    fixture = _fixture()
    fixture["validation_hook_ids"] = ["SYNTHETIC_API_ENDPOINT_HOOK"]

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "validation_hook_ids")
    _assert_failure_contains(failures, "endpoint")


def test_runtime_resolver_snapshot_claims_fail():
    fixture = _fixture()
    fixture["runtime_resolver_snapshot_reference"] = "SYNTHETIC_RUNTIME_SNAPSHOT_CLAIM"
    fixture["contains_runtime_resolver_snapshot"] = True
    fixture["forbidden_action_flags"]["runtime_resolver_snapshot_creation_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_resolver_snapshot"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_reference")
    _assert_failure_contains(failures, "contains_runtime_resolver_snapshot")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_enabled")
    _assert_failure_contains(failures, "creates_runtime_resolver_snapshot")


def test_replay_and_paper_execution_claims_fail():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["replay_execution_enabled"] = True
    fixture["forbidden_action_flags"]["paper_execution_enabled"] = True
    fixture["forbidden_action_flags"]["replay_result_packet_creation_enabled"] = True
    fixture["forbidden_action_flags"]["paper_result_packet_creation_enabled"] = True
    fixture["fixture_no_claim_flags"]["executes_replay"] = True
    fixture["fixture_no_claim_flags"]["executes_paper"] = True
    fixture["fixture_no_claim_flags"]["creates_replay_result"] = True
    fixture["fixture_no_claim_flags"]["creates_paper_result"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_enabled")
    _assert_failure_contains(failures, "paper_execution_enabled")
    _assert_failure_contains(failures, "replay_result_packet_creation_enabled")
    _assert_failure_contains(failures, "paper_result_packet_creation_enabled")
    _assert_failure_contains(failures, "executes_replay")
    _assert_failure_contains(failures, "executes_paper")
    _assert_failure_contains(failures, "creates_replay_result")
    _assert_failure_contains(failures, "creates_paper_result")


def test_runtime_cash_receipt_claims_fail():
    fixture = _fixture()
    fixture["contains_runtime_cash_receipt"] = True
    fixture["forbidden_action_flags"]["runtime_cash_receipt_creation_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_cash_receipts"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "contains_runtime_cash_receipt")
    _assert_failure_contains(failures, "runtime_cash_receipt_creation_enabled")
    _assert_failure_contains(failures, "creates_runtime_cash_receipts")


def test_fixture_has_no_live_private_real_source_or_profit_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()
    for fragment in {
        "://",
        "www.",
        "password",
        "account_id",
        "atomicrows.bundle",
        "owner_uploaded_private_doc_locator",
    }:
        assert fragment not in raw_text

    fixture = _fixture()
    frozen = copy.deepcopy(fixture)
    assert all(value is False for value in fixture["forbidden_action_flags"].values())
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())
    assert _intent(fixture)["order_payload_reference"] == "UNBOUND"
    assert _gate(fixture)["final_order_release_reference"] == "UNBOUND"
    assert _gate(fixture)["venue_write_connectivity_reference"] == "UNBOUND"
    assert _gate(fixture)["live_signer_path_reference"] == "UNBOUND"
    assert frozen == fixture
