from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import pathlib
from typing import Any


class AtomicRowsBundleState(str, Enum):
    PRE_MATERIALIZATION = "PRE_MATERIALIZATION"
    POST_MATERIALIZATION_PRE_SHA = "POST_MATERIALIZATION_PRE_SHA"
    POST_SHA_FREEZE = "POST_SHA_FREEZE"


@dataclass(frozen=True)
class AtomicRowsBundleStateDefinition:
    bundle_jsonl_required: bool
    bundle_jsonl_allowed: bool
    bundle_sha_required: bool
    bundle_sha_allowed: bool
    sha_freeze_authority_allowed: bool
    final_readiness_allowed: bool


@dataclass(frozen=True)
class AtomicRowsBundlePaths:
    bundle_jsonl: pathlib.Path
    bundle_sha256: pathlib.Path
    bundle_jsonl_relative: pathlib.PurePosixPath
    bundle_sha256_relative: pathlib.PurePosixPath


@dataclass(frozen=True)
class AtomicRowsBundlePresence:
    bundle_jsonl_exists: bool
    bundle_sha256_exists: bool


CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)
BOUNDARY_STATE_CONTRACT = pathlib.PurePosixPath(
    "docs/master_plan/atomicrows/AtomicRowsBundleBoundaryStateContract.yaml"
)

ATOMICROWS_BUNDLE_STATE_DEFINITIONS: dict[
    AtomicRowsBundleState, AtomicRowsBundleStateDefinition
] = {
    AtomicRowsBundleState.PRE_MATERIALIZATION: AtomicRowsBundleStateDefinition(
        bundle_jsonl_required=False,
        bundle_jsonl_allowed=False,
        bundle_sha_required=False,
        bundle_sha_allowed=False,
        sha_freeze_authority_allowed=False,
        final_readiness_allowed=False,
    ),
    AtomicRowsBundleState.POST_MATERIALIZATION_PRE_SHA: (
        AtomicRowsBundleStateDefinition(
            bundle_jsonl_required=True,
            bundle_jsonl_allowed=True,
            bundle_sha_required=False,
            bundle_sha_allowed=False,
            sha_freeze_authority_allowed=False,
            final_readiness_allowed=False,
        )
    ),
    AtomicRowsBundleState.POST_SHA_FREEZE: AtomicRowsBundleStateDefinition(
        bundle_jsonl_required=True,
        bundle_jsonl_allowed=True,
        bundle_sha_required=True,
        bundle_sha_allowed=True,
        sha_freeze_authority_allowed=True,
        final_readiness_allowed=False,
    ),
}


def _coerce_state(expected_state: AtomicRowsBundleState | str) -> AtomicRowsBundleState:
    if isinstance(expected_state, AtomicRowsBundleState):
        return expected_state
    try:
        return AtomicRowsBundleState(str(expected_state))
    except ValueError as exc:
        allowed = ", ".join(state.value for state in AtomicRowsBundleState)
        raise ValueError(f"unknown AtomicRows bundle state {expected_state!r}; allowed: {allowed}") from exc


def _relative_path(path: pathlib.PurePosixPath) -> pathlib.Path:
    return pathlib.Path(*path.parts)


def canonical_atomicrows_bundle_paths(repo_root: pathlib.Path | str) -> AtomicRowsBundlePaths:
    root = pathlib.Path(repo_root).resolve()
    return AtomicRowsBundlePaths(
        bundle_jsonl=root / _relative_path(CANONICAL_ATOMICROWS_BUNDLE),
        bundle_sha256=root / _relative_path(CANONICAL_ATOMICROWS_BUNDLE_SHA),
        bundle_jsonl_relative=CANONICAL_ATOMICROWS_BUNDLE,
        bundle_sha256_relative=CANONICAL_ATOMICROWS_BUNDLE_SHA,
    )


def canonical_atomicrows_bundle_presence(
    repo_root: pathlib.Path | str,
) -> AtomicRowsBundlePresence:
    paths = canonical_atomicrows_bundle_paths(repo_root)
    return AtomicRowsBundlePresence(
        bundle_jsonl_exists=paths.bundle_jsonl.exists(),
        bundle_sha256_exists=paths.bundle_sha256.exists(),
    )


def expected_atomicrows_bundle_state_from_contract(
    repo_root: pathlib.Path | str,
) -> AtomicRowsBundleState:
    contract_path = pathlib.Path(repo_root).resolve() / _relative_path(BOUNDARY_STATE_CONTRACT)
    if not contract_path.exists():
        return AtomicRowsBundleState.PRE_MATERIALIZATION
    for line in contract_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("current_expected_state:"):
            _, raw_value = stripped.split(":", 1)
            return _coerce_state(raw_value.strip().strip("'\""))
    raise ValueError(f"current_expected_state missing from {BOUNDARY_STATE_CONTRACT}")


def _expected_presence(definition: AtomicRowsBundleStateDefinition) -> tuple[bool, bool]:
    return definition.bundle_jsonl_required, definition.bundle_sha_required


def _presence_failure(
    *,
    label: str,
    expected_state: AtomicRowsBundleState,
    presence: AtomicRowsBundlePresence,
    offending_path: pathlib.PurePosixPath,
    reason: str,
) -> str:
    return (
        f"{label}: {reason}; expected_state={expected_state.value}; "
        f"observed_bundle_jsonl_exists={presence.bundle_jsonl_exists}; "
        f"observed_bundle_sha256_exists={presence.bundle_sha256_exists}; "
        f"offending_path={offending_path.as_posix()}"
    )


def validate_atomicrows_bundle_state(
    repo_root: pathlib.Path | str,
    expected_state: AtomicRowsBundleState | str,
    label: str,
) -> list[str]:
    state = _coerce_state(expected_state)
    definition = ATOMICROWS_BUNDLE_STATE_DEFINITIONS[state]
    paths = canonical_atomicrows_bundle_paths(repo_root)
    presence = canonical_atomicrows_bundle_presence(repo_root)
    failures: list[str] = []

    if definition.bundle_jsonl_required and not presence.bundle_jsonl_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=paths.bundle_jsonl_relative,
                reason="canonical AtomicRows bundle is required but missing",
            )
        )
    if not definition.bundle_jsonl_allowed and presence.bundle_jsonl_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=paths.bundle_jsonl_relative,
                reason="canonical AtomicRows bundle must remain absent",
            )
        )
    if definition.bundle_sha_required and not presence.bundle_sha256_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=paths.bundle_sha256_relative,
                reason="canonical AtomicRows bundle hash is required but missing",
            )
        )
    if not definition.bundle_sha_allowed and presence.bundle_sha256_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=paths.bundle_sha256_relative,
                reason="canonical AtomicRows bundle hash must remain absent",
            )
        )
    return failures


def validate_current_atomicrows_bundle_state(
    repo_root: pathlib.Path | str,
    label: str,
) -> list[str]:
    return validate_atomicrows_bundle_state(
        repo_root,
        expected_atomicrows_bundle_state_from_contract(repo_root),
        label,
    )


def atomicrows_bundle_state_report(
    repo_root: pathlib.Path | str,
    expected_state: AtomicRowsBundleState | str,
) -> dict[str, Any]:
    state = _coerce_state(expected_state)
    definition = ATOMICROWS_BUNDLE_STATE_DEFINITIONS[state]
    paths = canonical_atomicrows_bundle_paths(repo_root)
    presence = canonical_atomicrows_bundle_presence(repo_root)
    expected_bundle, expected_sha = _expected_presence(definition)
    failures = validate_atomicrows_bundle_state(
        repo_root,
        state,
        "atomicrows_bundle_state_report",
    )
    return {
        "current_expected_state": state.value,
        "bundle_jsonl_path": paths.bundle_jsonl_relative.as_posix(),
        "bundle_sha256_path": paths.bundle_sha256_relative.as_posix(),
        "bundle_jsonl_exists": presence.bundle_jsonl_exists,
        "bundle_sha256_exists": presence.bundle_sha256_exists,
        "expected_bundle_jsonl_exists": expected_bundle,
        "expected_bundle_sha256_exists": expected_sha,
        "bundle_state_valid": (
            presence.bundle_jsonl_exists == expected_bundle
            if definition.bundle_jsonl_required or not definition.bundle_jsonl_allowed
            else True
        ),
        "sha_state_valid": (
            presence.bundle_sha256_exists == expected_sha
            if definition.bundle_sha_required or not definition.bundle_sha_allowed
            else True
        ),
        "state_definition": {
            "bundle_jsonl_required": definition.bundle_jsonl_required,
            "bundle_jsonl_allowed": definition.bundle_jsonl_allowed,
            "bundle_sha_required": definition.bundle_sha_required,
            "bundle_sha_allowed": definition.bundle_sha_allowed,
            "sha_freeze_authority_allowed": definition.sha_freeze_authority_allowed,
            "final_readiness_allowed": definition.final_readiness_allowed,
        },
        "validation_errors": failures,
    }
