from tests.source_evidence.pr127_execution_lifecycle_support import (
    artifacts,
    model_records,
    placeholder_records,
)


def test_pr127_lifecycle_fixtures_are_not_production_venue_facts():
    records = (
        model_records()
        + placeholder_records()
        + artifacts()["builder_report"]["phase_records"]
        + artifacts()["builder_report"]["transition_records"]
    )

    for record in records:
        assert record["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        assert record["production_execution_lifecycle_authority"] is False

    for phase in artifacts()["builder_report"]["phase_records"]:
        assert phase["execution_phase_state"] == "PR127_GENERIC_FIXTURE_PHASE_PENDING"
        assert phase["phase_family"].endswith("_FIXTURE")
    for transition in artifacts()["builder_report"]["transition_records"]:
        assert transition["execution_transition_state"] == (
            "PR127_GENERIC_FIXTURE_TRANSITION_PENDING"
        )
