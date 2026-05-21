from .pr134_runtime_resolver_snapshot_support import assert_malformed


def test_pr134_rejects_missing_candidate_scope_lock_normalization_comparability_or_liquidity_dependency():
    assert_malformed("malformed_missing_candidate_scope_lock.v1.fixture.json", "MISSING_CANDIDATE_SCOPE_LOCK")
    assert_malformed("malformed_missing_contract_normalization_dependency.v1.fixture.json", "MISSING_CONTRACT_NORMALIZATION_DEPENDENCY")
    assert_malformed("malformed_missing_comparability_scope_dependency.v1.fixture.json", "MISSING_COMPARABILITY_SCOPE_DEPENDENCY")
    assert_malformed("malformed_missing_liquidity_scope_dependency.v1.fixture.json", "MISSING_LIQUIDITY_SCOPE_DEPENDENCY")
