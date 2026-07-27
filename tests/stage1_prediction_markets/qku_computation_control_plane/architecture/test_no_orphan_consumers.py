from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
    ORACLE_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    build_tranche_a_coverage_manifest,
)


def test_every_implementation_has_oracle_vector_and_callable() -> None:
    assert set(IMPLEMENTATION_REGISTRY) == set(ORACLE_BY_MATH_ID)
    assert set(IMPLEMENTATION_REGISTRY) == set(GOLDEN_VECTOR_BY_MATH_ID)
    assert all(callable(row.callable) for row in IMPLEMENTATION_REGISTRY.values())
    assert all(row.golden_vector_id for row in IMPLEMENTATION_REGISTRY.values())
    assert all(
        row.specification_metadata.certified_formula
        and row.specification_metadata.domain_and_fail_closed_guards
        and row.specification_metadata.implementation_algorithm
        and row.specification_metadata.mandatory_comparator_or_reconciliation
        for row in IMPLEMENTATION_REGISTRY.values()
    )
    assert (
        IMPLEMENTATION_REGISTRY["MATH-15"]
        .specification_metadata.mandatory_comparator_or_reconciliation
        == "Hansen SPA and unadjusted best-candidate statistic"
    )
    assert (
        IMPLEMENTATION_REGISTRY["MATH-47"]
        .specification_metadata.domain_and_fail_closed_guards[0]
        == "Energy parity tolerance must be derived from coefficient scale "
        "and float precision."
    )
    manifest = build_tranche_a_coverage_manifest()
    assert all(row.consumer_refs for row in manifest.rows)
    assert all(
        row.no_orphan_disposition == "VALIDATED_AND_CONSUMED"
        for row in manifest.rows
    )
