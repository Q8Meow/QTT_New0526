from __future__ import annotations

from enum import Enum


class AtomicRowsShaSystemDormancyState(str, Enum):
    SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED = (
        "SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED"
    )
    SHA_SYSTEM_REACTIVATION_OWNER_REQUESTED = (
        "SHA_SYSTEM_REACTIVATION_OWNER_REQUESTED"
    )
    SHA_SYSTEM_ACTIVE_OWNER_APPROVED = "SHA_SYSTEM_ACTIVE_OWNER_APPROVED"


ATOMICROWS_SHA_SYSTEM_DORMANCY_STATES = tuple(
    state.value for state in AtomicRowsShaSystemDormancyState
)

CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE = (
    AtomicRowsShaSystemDormancyState.SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED.value
)
EXPECTED_CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE = (
    AtomicRowsShaSystemDormancyState.SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED.value
)


def get_atomicrows_sha_system_dormancy_state() -> str:
    return CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE


def is_sha_system_dormant() -> bool:
    return (
        get_atomicrows_sha_system_dormancy_state()
        == AtomicRowsShaSystemDormancyState.SHA_SYSTEM_DORMANT_NON_PARTICIPATING_OWNER_CONTROLLED.value
    )


def is_sha_system_non_participating_for_final_readiness() -> bool:
    return is_sha_system_dormant()


def is_sha_generation_allowed() -> bool:
    return False


def is_sha_freeze_authority_allowed() -> bool:
    return False


def assert_sha_system_dormant_non_participating() -> None:
    if not is_sha_system_dormant():
        raise AssertionError(
            "SHA system must be dormant under owner-controlled non-participation"
        )
    if not is_sha_system_non_participating_for_final_readiness():
        raise AssertionError("SHA system must not participate in final readiness")


def assert_sha_generation_disabled() -> None:
    if is_sha_generation_allowed():
        raise AssertionError("SHA generation must remain disabled")


def assert_sha_freeze_authority_disabled() -> None:
    if is_sha_freeze_authority_allowed():
        raise AssertionError("SHA/freeze authority must remain disabled")


def assert_sha_dormancy_does_not_create_final_readiness() -> None:
    assert_sha_system_dormant_non_participating()


def assert_sha_dormancy_does_not_block_final_readiness() -> None:
    assert_sha_system_dormant_non_participating()


def assert_sha_reactivation_not_performed() -> None:
    if (
        get_atomicrows_sha_system_dormancy_state()
        != EXPECTED_CURRENT_ATOMICROWS_SHA_SYSTEM_DORMANCY_STATE
    ):
        raise AssertionError("SHA reactivation was performed in this PR")


def assert_sha_reactivation_requires_future_owner_approved_pr() -> None:
    if is_sha_generation_allowed() or is_sha_freeze_authority_allowed():
        raise AssertionError(
            "SHA reactivation requires a future owner-approved PR before enabling SHA"
        )
