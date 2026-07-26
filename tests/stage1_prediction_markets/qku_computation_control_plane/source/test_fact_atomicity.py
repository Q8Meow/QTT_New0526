from dataclasses import replace

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    AtomicFactTerminalStateV1,
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
        fact.result
        is AtomicFactTerminalStateV1.PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE
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


@pytest.mark.parametrize(
    "lookalike",
    (
        "BYPASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE",
        "NOT_PASS",
        "PASSIVE",
        "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE_SUFFIX",
    ),
)
def test_atomic_fact_terminal_rejects_every_pass_lookalike(
    lookalike: str,
) -> None:
    with pytest.raises(SourcePolicyError):
        replace(CERTIFIED_SOURCE_STATES[0].atomic_facts[0], result=lookalike)
