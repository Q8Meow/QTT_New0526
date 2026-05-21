from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_live_candidate_discovery_import_or_contract_selection():
    assert_malformed("malformed_live_candidate_discovery_created.v1.fixture.json", "LIVE_CANDIDATE_DISCOVERY_CREATED")
    assert_malformed("malformed_live_candidate_import_created.v1.fixture.json", "LIVE_CANDIDATE_IMPORT_CREATED")
    assert_malformed("malformed_live_contract_selection_created.v1.fixture.json", "LIVE_CONTRACT_SELECTION_CREATED")
