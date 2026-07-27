import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    BindingResolverV1,
    SOURCE_RULE_011,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    SourceBindingV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    CERTIFIED_SOURCE_STATES,
    assert_source_precedence,
)


def test_source_precedence_and_exact_claim_membership_are_closed() -> None:
    assert_source_precedence(CERTIFIED_SOURCE_STATES)
    expected = (
        "DIRECT_CURRENT_PRIMARY_PAGE_OVER_DIRECT_VERSIONED_CHANGELOG_OVER_"
        "PRIMARY_METHOD_PUBLISHER_OVER_CACHED_OR_SEARCH_REPRESENTATION"
    )
    assert {row.source_precedence for row in CERTIFIED_SOURCE_STATES} == {
        expected
    }
    claim = SOURCE_RULE_011.exact_claims[0]
    assert SOURCE_RULE_011.permits_exact_claim(
        claim,
        "SOURCE_CURRENTIZATION_OWNER",
    )
    assert not SOURCE_RULE_011.permits_exact_claim(
        claim + " altered",
        "SOURCE_CURRENTIZATION_OWNER",
    )


def test_source_binding_preserves_exact_certified_lineage() -> None:
    state = CERTIFIED_SOURCE_STATES[0]
    binding = SourceBindingV1(
        state.source_state_id,
        state.stable_source_identity,
        state.epoch,
        state.rights_and_use_state,
        state.ttl,
    )
    profile = BindingResolverV1.build(
        binding_id="source-binding-v1",
        version="1",
        inputs=(),
        sources=(binding,),
    )
    assert profile.source_bindings == (binding,)
    with pytest.raises(ContractValidationError):
        BindingResolverV1.build(
            binding_id="source-binding-v1",
            version="1",
            inputs=(),
            sources=(
                SourceBindingV1(
                    state.source_state_id,
                    state.stable_source_identity + "-altered",
                    state.epoch,
                    state.rights_and_use_state,
                    state.ttl,
                ),
            ),
        )
