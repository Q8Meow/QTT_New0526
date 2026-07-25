from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    CERTIFIED_SOURCE_STATES,
)


def test_source_pages_are_bound_as_atomic_facts_not_page_level_passes() -> None:
    facts = tuple(
        fact
        for source in CERTIFIED_SOURCE_STATES
        for fact in source.atomic_facts
    )
    assert facts
    assert len({fact.atomic_fact_id for fact in facts}) == len(facts)
    assert all(fact.fact for fact in facts)
    assert all(
        fact.result == "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE"
        for fact in facts
    )
    assert all(
        len(source.exact_claims) >= len(source.atomic_facts)
        and all(
            fact.atomic_fact_id.startswith(source.source_state_id + "::")
            for fact in source.atomic_facts
        )
        for source in CERTIFIED_SOURCE_STATES
    )
