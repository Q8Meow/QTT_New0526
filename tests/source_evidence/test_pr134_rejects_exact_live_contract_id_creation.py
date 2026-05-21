from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_exact_live_contract_id_creation():
    assert_malformed("malformed_exact_live_contract_id_created.v1.fixture.json", "EXACT_LIVE_CONTRACT_ID_CREATED")
