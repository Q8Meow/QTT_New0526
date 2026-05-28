from .helpers import counts


def test_pr159r_no_owner_assertion_as_source_fact(pr159r_artifacts):
    assert pr159r_artifacts["accepted"]["record_count"] == counts(pr159r_artifacts)["new_accepted_source_packet_count"]
    assert pr159r_artifacts["master"]["source_evidence_packet_consumed_confirmation"] is True
