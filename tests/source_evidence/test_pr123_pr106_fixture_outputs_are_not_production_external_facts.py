from ._pr123_acceptance_helpers import execute, fixture, valid_candidate


def test_fixture_outputs_are_not_production_external_facts():
    suite = fixture()
    result = execute(valid_candidate())

    assert suite["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
    assert suite["production_external_fact_authority"] is False
    assert result.decision_receipt["production_external_fact_authority"] is False
    assert result.accepted_packet is not None
    assert result.accepted_ledger_record is not None
    assert result.accepted_packet["production_external_fact_authority"] is False
    assert result.accepted_ledger_record["production_external_fact_authority"] is False
