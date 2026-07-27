from dataclasses import replace

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    SOURCE_RULE_011,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    CERTIFIED_SOURCE_STATES,
    assert_source_precedence,
)


def test_conflicts_are_terminal_and_duplicate_authority_fails_closed() -> None:
    assert all(
        row.conflict_resolution_state
        == "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE"
        for row in CERTIFIED_SOURCE_STATES
    )
    with pytest.raises(SourcePolicyError) as caught:
        assert_source_precedence(
            (CERTIFIED_SOURCE_STATES[0], CERTIFIED_SOURCE_STATES[0])
        )
    assert caught.value.reason_code is ReasonCode.SOURCE_CONFLICT
    assert not SOURCE_RULE_011.broad_regex_or_alias_matching_allowed
    assert not SOURCE_RULE_011.codex_source_selection_allowed


@pytest.mark.parametrize(
    ("field_name", "lookalike"),
    (
        ("research_completeness_state", "COMPLETE_"),
        (
            "research_completeness_state",
            "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING_SUFFIX",
        ),
        (
            "primary_source_completeness_state",
            "COMPLETE_PRIMARY_SOURCE_SUFFIX",
        ),
    ),
)
def test_completeness_terminals_reject_prefix_and_suffix_lookalikes(
    field_name: str,
    lookalike: str,
) -> None:
    with pytest.raises(SourcePolicyError):
        replace(
            CERTIFIED_SOURCE_STATES[0],
            **{field_name: lookalike},
        )
