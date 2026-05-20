from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_requires_pr131_credential_readiness_handoff():
    refs = {
        record["credential_readiness_dependency_ref"]
        for record in support.adapter_inputs()
    }

    assert refs == {"PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1"}
    assert support.main_report()["PR132_PR131_CREDENTIAL_READINESS_DEPENDENCY_EVIDENCE"][
        "pr131_handoff_consumed_as_metadata_only"
    ] is True
