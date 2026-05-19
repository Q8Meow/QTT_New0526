from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    decisions_by_binding,
    manifest_records,
)


def test_pr126_accepts_fresh_fixture_binding_for_pr126_manifest():
    decision = decisions_by_binding()["PR126_BINDING_READY"]

    assert decision["implementation_gate_state"] == (
        "READY_FOR_PR126_FIXTURE_SCOPE_IMPLEMENTATION"
    )
    assert decision["decision_reason_code"] == "PR126_FIXTURE_SCOPE_IMPLEMENTATION_READY"

    manifests = manifest_records()
    assert len(manifests) == 1
    assert manifests[0]["source_connector_binding_ledger_record_id"] == "PR126_BINDING_READY"
    assert manifests[0]["fixture_authority_class"] == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
