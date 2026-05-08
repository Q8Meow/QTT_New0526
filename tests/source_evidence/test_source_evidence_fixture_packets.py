import json
from pathlib import Path


FIXTURE_DIR = Path("tests/fixtures/source_evidence")
SCHEMA_PATH = Path("schemas/source_evidence/source_evidence.schema.json")
SYNTHETIC_AUTHORITY_CLASS = "SYNTHETIC_NON_AUTHORITATIVE_EXAMPLE_NOT_SOURCE_FACT"
REQUIRED_FIXTURE_NO_CLAIM_FLAGS = {
    "retrieves_source_facts",
    "accepts_source_facts",
    "creates_accepted_source_evidence",
    "unlocks_connector_semantics",
    "creates_runtime_cash_receipts",
    "creates_live_reachability",
    "executes_orders",
    "creates_profit_evidence",
}
SCHEMA_NO_CLAIM_FLAGS = {
    "external_fact_authority",
    "source_retrieval_authority",
    "source_acceptance_execution_authority",
    "accepted_packet_creation_authority",
    "connector_binding_authority",
    "runtime_authority",
    "runtime_cash_fetch_authority",
    "private_state_fetch_authority",
    "order_execution_authority",
    "replay_paper_live_execution_authority",
    "network_io_authority",
    "sha_freeze_authority",
    "profit_claim_authority",
}
EXPECTED_FIXTURE_NAMES = {
    "synthetic_candidate_source_packet.v1.fixture.json",
    "synthetic_accepted_source_packet.v1.fixture.json",
    "synthetic_target_field_ledger.v1.fixture.json",
    "synthetic_conflict_materiality_revalidation.v1.fixture.json",
}
SURFACE_FIXTURE_MAP = {
    "synthetic_candidate_source_packet.v1.fixture.json": ("candidate_source_packet",),
    "synthetic_accepted_source_packet.v1.fixture.json": ("accepted_source_packet",),
    "synthetic_target_field_ledger.v1.fixture.json": ("target_field_ledger_record",),
    "synthetic_conflict_materiality_revalidation.v1.fixture.json": (
        "conflict_metadata",
        "materiality_metadata",
        "revalidation_metadata",
    ),
}
FORBIDDEN_TEXT_FRAGMENTS = {
    "http://",
    "https://",
    "kalshi.com",
    "polymarket.com",
    "ibkr.com",
    "interactivebrokers.com",
    "owner_uploaded_private_doc_locator",
    "private_doc_quarantined_pending_access_attestation",
    "file://",
    "api_key",
    "secret_key",
    "live_key",
    "pk_live",
    "sk_live",
    "-----begin",
}
CONNECTOR_UNLOCK_FIELDS = {
    "unlocks_connector_semantics",
    "candidate_packet_may_unlock_connector_semantics",
    "connector_unlock_authority",
    "connector_semantic_binding_allowed_flag",
}


def _fixture_paths() -> list[Path]:
    paths = sorted(FIXTURE_DIR.glob("*.fixture.json"))
    assert {path.name for path in paths} == EXPECTED_FIXTURE_NAMES
    return paths


def _load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixtures() -> dict[str, dict]:
    return {path.name: _load_fixture(path) for path in _fixture_paths()}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def test_source_evidence_fixtures_parse_as_json():
    for path in _fixture_paths():
        parsed = _load_fixture(path)
        assert isinstance(parsed, dict)
        assert parsed["fixture_id"].startswith("SYNTHETIC_PR5_")


def test_fixtures_include_synthetic_authority_and_no_claim_flags():
    for fixture in _fixtures().values():
        assert fixture["example_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
        assert fixture["fixture_authority_class"] == (
            "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_SOURCE_FACT"
        )
        assert fixture["mode"] == "SOURCE_REQUIRED"
        assert fixture["execution"] == "DISABLED"

        fixture_flags = fixture["fixture_no_claim_flags"]
        assert set(fixture_flags) == REQUIRED_FIXTURE_NO_CLAIM_FLAGS
        assert all(value is False for value in fixture_flags.values())

        schema_flags = fixture["no_claim_flags"]
        assert set(schema_flags) == SCHEMA_NO_CLAIM_FLAGS
        assert all(value is False for value in schema_flags.values())


def test_fixture_surfaces_match_schema_required_fields_without_schema_dependency():
    schema_defs = _schema()["$defs"]

    for fixture_name, surface_names in SURFACE_FIXTURE_MAP.items():
        fixture = _fixtures()[fixture_name]
        for surface_name in surface_names:
            surface = fixture[surface_name]
            required = set(schema_defs[surface_name]["required"])
            assert required.issubset(surface)


def test_fixtures_do_not_embed_real_source_or_secret_locators():
    for path in _fixture_paths():
        raw_text = path.read_text(encoding="utf-8").lower()
        for fragment in FORBIDDEN_TEXT_FRAGMENTS:
            assert fragment not in raw_text

        fixture = _load_fixture(path)
        for key, value in _walk(fixture):
            if "locator" not in key.lower() or not isinstance(value, str):
                continue
            assert "://" not in value
            assert "\\" not in value
            assert value.startswith("SYNTHETIC_") or value == (
                "OWNER_UNSET_PENDING_OFFICIAL_SOURCE_DISCOVERY"
            )


def test_fixtures_never_enable_external_or_runtime_authority():
    for fixture in _fixtures().values():
        for key, value in _walk(fixture):
            if key.endswith("_authority") and isinstance(value, bool):
                assert value is False
            if key in CONNECTOR_UNLOCK_FIELDS:
                assert value is False


def test_accepted_source_fixture_cannot_be_mistaken_for_real_acceptance_authority():
    fixture = _fixtures()["synthetic_accepted_source_packet.v1.fixture.json"]
    packet = fixture["accepted_source_packet"]

    assert fixture["synthetic_acceptance_authority_flags"] == {
        "real_accepted_source_authority": False,
        "external_fact_acceptance_authority": False,
        "connector_unlock_authority": False,
    }
    assert fixture["fixture_no_claim_flags"]["accepts_source_facts"] is False
    assert fixture["fixture_no_claim_flags"]["creates_accepted_source_evidence"] is False
    assert packet["packet_type"] == "ACCEPTED_SOURCE_PACKET_SCHEMA_ONLY"
    assert packet["schema_authority_class"] == (
        "ACCEPTED_PACKET_SCHEMA_ONLY_NOT_RUNTIME_NOT_CONNECTOR_BINDING"
    )
    assert packet["no_claim_flags"]["external_fact_authority"] is False
    assert packet["no_claim_flags"]["accepted_packet_creation_authority"] is False
    assert packet["no_connector_semantic_population_flag"] is True
    assert packet["no_live_reachability_flag"] is True
    assert packet["no_order_execution_flag"] is True
    assert packet["no_runtime_cash_claim_flag"] is True
    assert packet["no_blocker_reduction_or_profit_claim_flag"] is True


def test_target_field_ledger_fixture_is_synthetic_and_not_bindable():
    fixture = _fixtures()["synthetic_target_field_ledger.v1.fixture.json"]
    record = fixture["target_field_ledger_record"]

    assert record["ledger_record_id"].startswith("SYNTHETIC_PR5_")
    assert record["venue_id"] == "NOT_VENUE_SPECIFIC"
    assert record["target_field_path"] == "synthetic_target.synthetic_field"
    assert record["connector_semantic_binding_allowed_flag"] is False
    assert record["blocked_reason_when_not_bindable"] == "STATIC_PR4_SCHEMA_ONLY_NOT_BINDABLE"
    assert fixture["fixture_no_claim_flags"]["unlocks_connector_semantics"] is False


def test_conflict_materiality_revalidation_fixture_is_review_only_and_non_runtime():
    fixture = _fixtures()["synthetic_conflict_materiality_revalidation.v1.fixture.json"]
    conflict = fixture["conflict_metadata"]
    materiality = fixture["materiality_metadata"]
    revalidation = fixture["revalidation_metadata"]

    assert fixture["review_only_state"] == (
        "OWNER_OR_RISK_REVIEW_REQUIRED_STATIC_FIXTURE_ONLY_NOT_RUNTIME"
    )
    assert conflict["owner_or_risk_review_required"] is True
    assert conflict["block_code_when_unresolved"] == (
        "BLOCKED_ACCEPTED_PACKET_UNRESOLVED_CONFLICT"
    )
    assert materiality["owner_or_risk_review_required"] is True
    assert materiality["new_binding_blocked_when_material"] is True
    assert revalidation["source_change_event_trigger_required"] is True
    assert revalidation["stale_or_superseded_packet_blocks_new_connector_binding"] is True
    assert revalidation["fresh_revalidation_state_required_before_new_connector_binding"] is True
    assert fixture["fixture_no_claim_flags"]["creates_runtime_cash_receipts"] is False
    assert fixture["fixture_no_claim_flags"]["creates_live_reachability"] is False
    assert fixture["fixture_no_claim_flags"]["executes_orders"] is False
