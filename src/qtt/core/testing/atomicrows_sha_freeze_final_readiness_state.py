from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import pathlib
from typing import Any


class AtomicRowsShaFreezeFinalReadinessState(str, Enum):
    BUNDLE_MATERIALIZED_PRE_SHA_FREEZE = "BUNDLE_MATERIALIZED_PRE_SHA_FREEZE"
    SHA_FREEZE_AUTHORIZED_PRE_FINAL_READINESS = (
        "SHA_FREEZE_AUTHORIZED_PRE_FINAL_READINESS"
    )
    FINAL_READINESS_AUTHORIZED = "FINAL_READINESS_AUTHORIZED"


@dataclass(frozen=True)
class AtomicRowsShaFreezeFinalReadinessStateDefinition:
    bundle_jsonl_required: bool
    bundle_jsonl_row_count_required: int
    bundle_sha256_required: bool
    bundle_sha256_allowed: bool
    sha_freeze_authority_required: bool
    sha_freeze_authority_allowed: bool
    freeze_receipt_required: bool
    freeze_receipt_allowed: bool
    final_readiness_required: bool
    final_readiness_allowed: bool
    live_trading_allowed: bool
    runtime_live_authority_allowed: bool
    order_authority_allowed: bool
    source_connector_authority_allowed: bool
    runtime_cash_authority_allowed: bool
    backend_authority_allowed: bool
    profit_evidence_allowed: bool
    quantum_backend_authority_allowed: bool
    replay_paper_execution_allowed: bool
    optimizer_execution_allowed: bool
    scoring_ranking_selection_execution_allowed: bool


@dataclass(frozen=True)
class AtomicRowsShaFreezeFinalReadinessAuthorityPath:
    path: pathlib.Path
    relative: pathlib.PurePosixPath
    artifact_kind: str
    future_only: bool
    must_not_exist_in_current_state: bool
    created_by_future_pr_only: bool


@dataclass(frozen=True)
class AtomicRowsShaFreezeFinalReadinessPaths:
    bundle_jsonl: pathlib.Path
    bundle_sha256: pathlib.Path
    bundle_jsonl_relative: pathlib.PurePosixPath
    bundle_sha256_relative: pathlib.PurePosixPath
    artifact_authority_paths: tuple[AtomicRowsShaFreezeFinalReadinessAuthorityPath, ...]


@dataclass(frozen=True)
class AtomicRowsShaFreezeFinalReadinessPresence:
    bundle_jsonl_exists: bool
    bundle_sha256_exists: bool
    sha_freeze_authority_exists: bool
    freeze_receipt_exists: bool
    final_readiness_exists: bool
    existing_sha_freeze_authority_paths: tuple[pathlib.PurePosixPath, ...]
    existing_freeze_receipt_paths: tuple[pathlib.PurePosixPath, ...]
    existing_final_readiness_paths: tuple[pathlib.PurePosixPath, ...]
    existing_forbidden_current_artifact_paths: tuple[pathlib.PurePosixPath, ...]


@dataclass(frozen=True)
class AtomicRowsBundleJsonlValidation:
    exists: bool
    valid: bool
    row_count: int
    expected_row_count: int
    errors: tuple[str, ...]


EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT = 4183
CANONICAL_ATOMICROWS_BUNDLE = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
)
CANONICAL_ATOMICROWS_BUNDLE_SHA = pathlib.PurePosixPath(
    "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
)
SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT = pathlib.PurePosixPath(
    "docs/master_plan/atomicrows/AtomicRowsShaFreezeFinalReadinessStateContract.yaml"
)

_FUTURE_ONLY = {
    "future_only": True,
    "must_not_exist_in_current_state": True,
    "created_by_future_pr_only": True,
}

BUILTIN_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_AUTHORITY_PATHS: tuple[
    dict[str, Any], ...
] = (
    {
        "path": CANONICAL_ATOMICROWS_BUNDLE_SHA.as_posix(),
        "artifact_kind": "bundle_sha256",
        **_FUTURE_ONLY,
    },
    {
        "path": "docs/master_plan/atomicrows/AtomicRowsBundleSHAFreezeAuthority.yaml",
        "artifact_kind": "sha_freeze_authority",
        **_FUTURE_ONLY,
    },
    {
        "path": (
            "docs/master_plan/generated/"
            "AtomicRowsBundleSHAFreezeAuthority.report.json"
        ),
        "artifact_kind": "sha_freeze_authority",
        **_FUTURE_ONLY,
    },
    {
        "path": "docs/master_plan/atomicrows/AtomicRowsBundleFreezeAuthority.yaml",
        "artifact_kind": "freeze_receipt",
        **_FUTURE_ONLY,
    },
    {
        "path": "docs/master_plan/atomic_rows/AtomicRowsBundleFreezeAuthority.yaml",
        "artifact_kind": "freeze_receipt",
        **_FUTURE_ONLY,
    },
    {
        "path": "docs/master_plan/atomicrows/AtomicRowsFullBundleFinalReadinessGate.yaml",
        "artifact_kind": "final_readiness",
        **_FUTURE_ONLY,
    },
    {
        "path": (
            "docs/master_plan/generated/"
            "AtomicRowsFullBundleFinalReadinessGate.report.json"
        ),
        "artifact_kind": "final_readiness",
        **_FUTURE_ONLY,
    },
)

ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS: dict[
    AtomicRowsShaFreezeFinalReadinessState,
    AtomicRowsShaFreezeFinalReadinessStateDefinition,
] = {
    AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE: (
        AtomicRowsShaFreezeFinalReadinessStateDefinition(
            bundle_jsonl_required=True,
            bundle_jsonl_row_count_required=EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
            bundle_sha256_required=False,
            bundle_sha256_allowed=False,
            sha_freeze_authority_required=False,
            sha_freeze_authority_allowed=False,
            freeze_receipt_required=False,
            freeze_receipt_allowed=False,
            final_readiness_required=False,
            final_readiness_allowed=False,
            live_trading_allowed=False,
            runtime_live_authority_allowed=False,
            order_authority_allowed=False,
            source_connector_authority_allowed=False,
            runtime_cash_authority_allowed=False,
            backend_authority_allowed=False,
            profit_evidence_allowed=False,
            quantum_backend_authority_allowed=False,
            replay_paper_execution_allowed=False,
            optimizer_execution_allowed=False,
            scoring_ranking_selection_execution_allowed=False,
        )
    ),
    AtomicRowsShaFreezeFinalReadinessState.SHA_FREEZE_AUTHORIZED_PRE_FINAL_READINESS: (
        AtomicRowsShaFreezeFinalReadinessStateDefinition(
            bundle_jsonl_required=True,
            bundle_jsonl_row_count_required=EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
            bundle_sha256_required=True,
            bundle_sha256_allowed=True,
            sha_freeze_authority_required=True,
            sha_freeze_authority_allowed=True,
            freeze_receipt_required=True,
            freeze_receipt_allowed=True,
            final_readiness_required=False,
            final_readiness_allowed=False,
            live_trading_allowed=False,
            runtime_live_authority_allowed=False,
            order_authority_allowed=False,
            source_connector_authority_allowed=False,
            runtime_cash_authority_allowed=False,
            backend_authority_allowed=False,
            profit_evidence_allowed=False,
            quantum_backend_authority_allowed=False,
            replay_paper_execution_allowed=False,
            optimizer_execution_allowed=False,
            scoring_ranking_selection_execution_allowed=False,
        )
    ),
    AtomicRowsShaFreezeFinalReadinessState.FINAL_READINESS_AUTHORIZED: (
        AtomicRowsShaFreezeFinalReadinessStateDefinition(
            bundle_jsonl_required=True,
            bundle_jsonl_row_count_required=EXPECTED_ATOMICROWS_BUNDLE_ROW_COUNT,
            bundle_sha256_required=True,
            bundle_sha256_allowed=True,
            sha_freeze_authority_required=True,
            sha_freeze_authority_allowed=True,
            freeze_receipt_required=True,
            freeze_receipt_allowed=True,
            final_readiness_required=True,
            final_readiness_allowed=True,
            live_trading_allowed=False,
            runtime_live_authority_allowed=False,
            order_authority_allowed=False,
            source_connector_authority_allowed=False,
            runtime_cash_authority_allowed=False,
            backend_authority_allowed=False,
            profit_evidence_allowed=False,
            quantum_backend_authority_allowed=False,
            replay_paper_execution_allowed=False,
            optimizer_execution_allowed=False,
            scoring_ranking_selection_execution_allowed=False,
        )
    ),
}

_CURRENT_STATE_FORBIDDEN_TRUE_FIELDS = (
    "bundle_sha256_required",
    "bundle_sha256_allowed",
    "sha_freeze_authority_required",
    "sha_freeze_authority_allowed",
    "freeze_receipt_required",
    "freeze_receipt_allowed",
    "final_readiness_required",
    "final_readiness_allowed",
    "live_trading_allowed",
    "runtime_live_authority_allowed",
    "order_authority_allowed",
    "source_connector_authority_allowed",
    "runtime_cash_authority_allowed",
    "backend_authority_allowed",
    "profit_evidence_allowed",
    "quantum_backend_authority_allowed",
    "replay_paper_execution_allowed",
    "optimizer_execution_allowed",
    "scoring_ranking_selection_execution_allowed",
)


def _coerce_state(
    expected_state: AtomicRowsShaFreezeFinalReadinessState | str,
) -> AtomicRowsShaFreezeFinalReadinessState:
    if isinstance(expected_state, AtomicRowsShaFreezeFinalReadinessState):
        return expected_state
    try:
        return AtomicRowsShaFreezeFinalReadinessState(str(expected_state))
    except ValueError as exc:
        allowed = ", ".join(state.value for state in AtomicRowsShaFreezeFinalReadinessState)
        raise ValueError(
            "unknown AtomicRows SHA/freeze/final-readiness state "
            f"{expected_state!r}; allowed: {allowed}"
        ) from exc


def _relative_path(path: pathlib.PurePosixPath) -> pathlib.Path:
    return pathlib.Path(*path.parts)


def _to_bool(value: str, default: bool) -> bool:
    normalized = value.strip().strip("'\"").lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return default


def _entry_from_mapping(
    repo_root: pathlib.Path,
    value: dict[str, Any],
) -> AtomicRowsShaFreezeFinalReadinessAuthorityPath | None:
    path_value = value.get("path")
    artifact_kind = value.get("artifact_kind")
    if not isinstance(path_value, str) or not path_value:
        return None
    if not isinstance(artifact_kind, str) or not artifact_kind:
        return None
    relative = pathlib.PurePosixPath(path_value)
    return AtomicRowsShaFreezeFinalReadinessAuthorityPath(
        path=repo_root / _relative_path(relative),
        relative=relative,
        artifact_kind=artifact_kind,
        future_only=bool(value.get("future_only", True)),
        must_not_exist_in_current_state=bool(
            value.get("must_not_exist_in_current_state", True)
        ),
        created_by_future_pr_only=bool(value.get("created_by_future_pr_only", True)),
    )


def _artifact_paths_from_contract(
    repo_root: pathlib.Path,
) -> tuple[AtomicRowsShaFreezeFinalReadinessAuthorityPath, ...]:
    contract_path = repo_root / _relative_path(SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT)
    if not contract_path.exists():
        return ()
    entries: list[dict[str, Any]] = []
    in_block = False
    current: dict[str, Any] | None = None
    for raw_line in contract_path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("artifact_authority_paths:"):
            in_block = True
            continue
        if in_block and raw_line and not raw_line.startswith(" "):
            break
        if not in_block:
            continue
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- path:"):
            if current:
                entries.append(current)
            current = {"path": stripped.split(":", 1)[1].strip().strip("'\"")}
            continue
        if current is not None and ":" in stripped:
            key, raw_value = stripped.split(":", 1)
            raw_value = raw_value.strip()
            if key in {
                "future_only",
                "must_not_exist_in_current_state",
                "created_by_future_pr_only",
            }:
                current[key] = _to_bool(raw_value, True)
            else:
                current[key] = raw_value.strip("'\"")
    if current:
        entries.append(current)

    parsed = [
        entry
        for item in entries
        if (entry := _entry_from_mapping(repo_root, item)) is not None
    ]
    return tuple(parsed)


def _builtin_artifact_paths(
    repo_root: pathlib.Path,
) -> tuple[AtomicRowsShaFreezeFinalReadinessAuthorityPath, ...]:
    parsed = [
        entry
        for item in BUILTIN_ATOMICROWS_SHA_FREEZE_FINAL_READINESS_AUTHORITY_PATHS
        if (entry := _entry_from_mapping(repo_root, item)) is not None
    ]
    return tuple(parsed)


def canonical_atomicrows_sha_freeze_paths(
    repo_root: pathlib.Path | str,
) -> AtomicRowsShaFreezeFinalReadinessPaths:
    root = pathlib.Path(repo_root).resolve()
    contract_paths = _artifact_paths_from_contract(root)
    return AtomicRowsShaFreezeFinalReadinessPaths(
        bundle_jsonl=root / _relative_path(CANONICAL_ATOMICROWS_BUNDLE),
        bundle_sha256=root / _relative_path(CANONICAL_ATOMICROWS_BUNDLE_SHA),
        bundle_jsonl_relative=CANONICAL_ATOMICROWS_BUNDLE,
        bundle_sha256_relative=CANONICAL_ATOMICROWS_BUNDLE_SHA,
        artifact_authority_paths=contract_paths or _builtin_artifact_paths(root),
    )


def discover_atomicrows_sha_freeze_final_readiness_authority_paths(
    repo_root: pathlib.Path | str,
) -> tuple[AtomicRowsShaFreezeFinalReadinessAuthorityPath, ...]:
    return canonical_atomicrows_sha_freeze_paths(repo_root).artifact_authority_paths


def canonical_atomicrows_sha_freeze_presence(
    repo_root: pathlib.Path | str,
) -> AtomicRowsShaFreezeFinalReadinessPresence:
    paths = canonical_atomicrows_sha_freeze_paths(repo_root)
    existing_sha_freeze = tuple(
        entry.relative
        for entry in paths.artifact_authority_paths
        if entry.artifact_kind == "sha_freeze_authority" and entry.path.exists()
    )
    existing_freeze_receipts = tuple(
        entry.relative
        for entry in paths.artifact_authority_paths
        if entry.artifact_kind == "freeze_receipt" and entry.path.exists()
    )
    existing_final_readiness = tuple(
        entry.relative
        for entry in paths.artifact_authority_paths
        if entry.artifact_kind == "final_readiness" and entry.path.exists()
    )
    existing_forbidden = tuple(
        entry.relative
        for entry in paths.artifact_authority_paths
        if entry.must_not_exist_in_current_state and entry.path.exists()
    )
    return AtomicRowsShaFreezeFinalReadinessPresence(
        bundle_jsonl_exists=paths.bundle_jsonl.exists(),
        bundle_sha256_exists=paths.bundle_sha256.exists(),
        sha_freeze_authority_exists=bool(existing_sha_freeze),
        freeze_receipt_exists=bool(existing_freeze_receipts),
        final_readiness_exists=bool(existing_final_readiness),
        existing_sha_freeze_authority_paths=existing_sha_freeze,
        existing_freeze_receipt_paths=existing_freeze_receipts,
        existing_final_readiness_paths=existing_final_readiness,
        existing_forbidden_current_artifact_paths=existing_forbidden,
    )


def expected_atomicrows_sha_freeze_final_readiness_state_from_contract(
    repo_root: pathlib.Path | str,
) -> AtomicRowsShaFreezeFinalReadinessState:
    contract_path = (
        pathlib.Path(repo_root).resolve()
        / _relative_path(SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT)
    )
    if not contract_path.exists():
        return AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE
    for line in contract_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("current_expected_state:"):
            _, raw_value = stripped.split(":", 1)
            return _coerce_state(raw_value.strip().strip("'\""))
    raise ValueError(
        "current_expected_state missing from "
        f"{SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT}"
    )


def _bundle_jsonl_validation(
    path: pathlib.Path,
    expected_row_count: int,
) -> AtomicRowsBundleJsonlValidation:
    if not path.exists():
        return AtomicRowsBundleJsonlValidation(
            exists=False,
            valid=False,
            row_count=0,
            expected_row_count=expected_row_count,
            errors=("canonical AtomicRows bundle is required but missing",),
        )

    raw = path.read_bytes()
    errors: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("canonical AtomicRows bundle must not include UTF-8 BOM")
    if b"\r\n" in raw or b"\r" in raw:
        errors.append("canonical AtomicRows bundle must use LF-only line endings")
    if not raw.endswith(b"\n"):
        errors.append("canonical AtomicRows bundle must end with LF")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return AtomicRowsBundleJsonlValidation(
            exists=True,
            valid=False,
            row_count=0,
            expected_row_count=expected_row_count,
            errors=tuple([*errors, f"canonical AtomicRows bundle must be UTF-8: {exc}"]),
        )

    lines = text.splitlines()
    blank_lines = [index for index, line in enumerate(lines, start=1) if not line.strip()]
    if blank_lines:
        first = blank_lines[0]
        errors.append(f"canonical AtomicRows bundle must not contain blank rows; first_blank_line={first}")

    row_count = sum(1 for line in lines if line.strip())
    parsed_rows = 0
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"canonical AtomicRows bundle line {line_number} invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(
                f"canonical AtomicRows bundle line {line_number} must be a JSON object"
            )
            continue
        parsed_rows += 1
    if row_count != expected_row_count:
        errors.append(
            "canonical AtomicRows bundle row count must be "
            f"{expected_row_count}, observed {row_count}"
        )
    if parsed_rows != row_count:
        errors.append(
            "canonical AtomicRows bundle parsed JSON object count must match "
            f"non-empty row count; parsed={parsed_rows}; non_empty={row_count}"
        )

    return AtomicRowsBundleJsonlValidation(
        exists=True,
        valid=not errors,
        row_count=row_count,
        expected_row_count=expected_row_count,
        errors=tuple(errors),
    )


def _state_definition_dict(
    definition: AtomicRowsShaFreezeFinalReadinessStateDefinition,
) -> dict[str, bool | int]:
    return {
        "bundle_jsonl_required": definition.bundle_jsonl_required,
        "bundle_jsonl_row_count_required": definition.bundle_jsonl_row_count_required,
        "bundle_sha256_required": definition.bundle_sha256_required,
        "bundle_sha256_allowed": definition.bundle_sha256_allowed,
        "sha_freeze_authority_required": definition.sha_freeze_authority_required,
        "sha_freeze_authority_allowed": definition.sha_freeze_authority_allowed,
        "freeze_receipt_required": definition.freeze_receipt_required,
        "freeze_receipt_allowed": definition.freeze_receipt_allowed,
        "final_readiness_required": definition.final_readiness_required,
        "final_readiness_allowed": definition.final_readiness_allowed,
        "live_trading_allowed": definition.live_trading_allowed,
        "runtime_live_authority_allowed": definition.runtime_live_authority_allowed,
        "order_authority_allowed": definition.order_authority_allowed,
        "source_connector_authority_allowed": definition.source_connector_authority_allowed,
        "runtime_cash_authority_allowed": definition.runtime_cash_authority_allowed,
        "backend_authority_allowed": definition.backend_authority_allowed,
        "profit_evidence_allowed": definition.profit_evidence_allowed,
        "quantum_backend_authority_allowed": definition.quantum_backend_authority_allowed,
        "replay_paper_execution_allowed": definition.replay_paper_execution_allowed,
        "optimizer_execution_allowed": definition.optimizer_execution_allowed,
        "scoring_ranking_selection_execution_allowed": (
            definition.scoring_ranking_selection_execution_allowed
        ),
    }


def _presence_failure(
    *,
    label: str,
    expected_state: AtomicRowsShaFreezeFinalReadinessState,
    presence: AtomicRowsShaFreezeFinalReadinessPresence,
    offending_path: pathlib.PurePosixPath,
    reason: str,
) -> str:
    return (
        f"{label}: {reason}; expected_state={expected_state.value}; "
        f"observed_bundle_jsonl_exists={presence.bundle_jsonl_exists}; "
        f"observed_bundle_sha256_exists={presence.bundle_sha256_exists}; "
        f"observed_sha_freeze_authority_exists={presence.sha_freeze_authority_exists}; "
        f"observed_freeze_receipt_exists={presence.freeze_receipt_exists}; "
        f"observed_final_readiness_exists={presence.final_readiness_exists}; "
        f"offending_path={offending_path.as_posix()}"
    )


def _first_path_for_kind(
    paths: AtomicRowsShaFreezeFinalReadinessPaths,
    artifact_kind: str,
) -> pathlib.PurePosixPath:
    for entry in paths.artifact_authority_paths:
        if entry.artifact_kind == artifact_kind:
            return entry.relative
    return paths.bundle_sha256_relative


def validate_atomicrows_sha_freeze_final_readiness_state(
    repo_root: pathlib.Path | str,
    expected_state: AtomicRowsShaFreezeFinalReadinessState | str,
    label: str,
) -> list[str]:
    state = _coerce_state(expected_state)
    definition = ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS[state]
    paths = canonical_atomicrows_sha_freeze_paths(repo_root)
    presence = canonical_atomicrows_sha_freeze_presence(repo_root)
    failures: list[str] = []

    if definition.bundle_jsonl_required:
        bundle = _bundle_jsonl_validation(
            paths.bundle_jsonl,
            definition.bundle_jsonl_row_count_required,
        )
        for error in bundle.errors:
            failures.append(
                _presence_failure(
                    label=label,
                    expected_state=state,
                    presence=presence,
                    offending_path=paths.bundle_jsonl_relative,
                    reason=error,
                )
            )

    if definition.bundle_sha256_required and not presence.bundle_sha256_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=paths.bundle_sha256_relative,
                reason="canonical AtomicRows bundle hash is required but missing",
            )
        )
    if not definition.bundle_sha256_allowed and presence.bundle_sha256_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=paths.bundle_sha256_relative,
                reason="canonical AtomicRows bundle hash must remain absent",
            )
        )

    if (
        definition.sha_freeze_authority_required
        and not presence.sha_freeze_authority_exists
    ):
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=_first_path_for_kind(paths, "sha_freeze_authority"),
                reason="SHA/freeze authority artifact is required but missing",
            )
        )
    if (
        not definition.sha_freeze_authority_allowed
        and presence.sha_freeze_authority_exists
    ):
        for offending in presence.existing_sha_freeze_authority_paths:
            failures.append(
                _presence_failure(
                    label=label,
                    expected_state=state,
                    presence=presence,
                    offending_path=offending,
                    reason="SHA/freeze authority artifact must remain absent",
                )
            )

    if definition.freeze_receipt_required and not presence.freeze_receipt_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=_first_path_for_kind(paths, "freeze_receipt"),
                reason="freeze receipt is required but missing",
            )
        )
    if not definition.freeze_receipt_allowed and presence.freeze_receipt_exists:
        for offending in presence.existing_freeze_receipt_paths:
            failures.append(
                _presence_failure(
                    label=label,
                    expected_state=state,
                    presence=presence,
                    offending_path=offending,
                    reason="freeze receipt must remain absent",
                )
            )

    if definition.final_readiness_required and not presence.final_readiness_exists:
        failures.append(
            _presence_failure(
                label=label,
                expected_state=state,
                presence=presence,
                offending_path=_first_path_for_kind(paths, "final_readiness"),
                reason="final-readiness artifact is required but missing",
            )
        )
    if not definition.final_readiness_allowed and presence.final_readiness_exists:
        for offending in presence.existing_final_readiness_paths:
            failures.append(
                _presence_failure(
                    label=label,
                    expected_state=state,
                    presence=presence,
                    offending_path=offending,
                    reason="final-readiness artifact must remain absent",
                )
            )

    if state is AtomicRowsShaFreezeFinalReadinessState.BUNDLE_MATERIALIZED_PRE_SHA_FREEZE:
        definition_map = _state_definition_dict(definition)
        for field in _CURRENT_STATE_FORBIDDEN_TRUE_FIELDS:
            if definition_map[field] is True:
                failures.append(
                    _presence_failure(
                        label=label,
                        expected_state=state,
                        presence=presence,
                        offending_path=SHA_FREEZE_FINAL_READINESS_STATE_CONTRACT,
                        reason=f"current-state authority field {field} must remain false",
                    )
                )

    return failures


def validate_current_atomicrows_sha_freeze_final_readiness_state(
    repo_root: pathlib.Path | str,
    label: str,
) -> list[str]:
    return validate_atomicrows_sha_freeze_final_readiness_state(
        repo_root,
        expected_atomicrows_sha_freeze_final_readiness_state_from_contract(repo_root),
        label,
    )


def atomicrows_sha_freeze_final_readiness_state_report(
    repo_root: pathlib.Path | str,
    expected_state: AtomicRowsShaFreezeFinalReadinessState | str,
) -> dict[str, Any]:
    state = _coerce_state(expected_state)
    definition = ATOMICROWS_SHA_FREEZE_FINAL_READINESS_STATE_DEFINITIONS[state]
    paths = canonical_atomicrows_sha_freeze_paths(repo_root)
    presence = canonical_atomicrows_sha_freeze_presence(repo_root)
    bundle = _bundle_jsonl_validation(
        paths.bundle_jsonl,
        definition.bundle_jsonl_row_count_required,
    )
    failures = validate_atomicrows_sha_freeze_final_readiness_state(
        repo_root,
        state,
        "atomicrows_sha_freeze_final_readiness_state_report",
    )
    forbidden_artifact_checks = {
        entry.relative.as_posix(): {
            "artifact_kind": entry.artifact_kind,
            "future_only": entry.future_only,
            "must_not_exist_in_current_state": entry.must_not_exist_in_current_state,
            "created_by_future_pr_only": entry.created_by_future_pr_only,
            "exists": entry.path.exists(),
            "expected_exists": False
            if entry.must_not_exist_in_current_state
            else entry.path.exists(),
            "valid": (not entry.path.exists())
            if entry.must_not_exist_in_current_state
            else True,
        }
        for entry in paths.artifact_authority_paths
    }
    return {
        "current_expected_state": state.value,
        "bundle_jsonl_path": paths.bundle_jsonl_relative.as_posix(),
        "bundle_sha256_path": paths.bundle_sha256_relative.as_posix(),
        "bundle_jsonl_exists": presence.bundle_jsonl_exists,
        "bundle_sha256_exists": presence.bundle_sha256_exists,
        "bundle_row_count": bundle.row_count,
        "expected_bundle_row_count": definition.bundle_jsonl_row_count_required,
        "bundle_jsonl_valid": bundle.valid,
        "bundle_sha256_expected_absent": not definition.bundle_sha256_required,
        "bundle_sha256_forbidden_absent": (
            not presence.bundle_sha256_exists
            if not definition.bundle_sha256_allowed
            else True
        ),
        "sha_freeze_authority_created": presence.sha_freeze_authority_exists,
        "freeze_receipt_created": presence.freeze_receipt_exists,
        "final_readiness_created": presence.final_readiness_exists,
        "state_definition": _state_definition_dict(definition),
        "artifact_authority_paths": [
            {
                "path": entry.relative.as_posix(),
                "artifact_kind": entry.artifact_kind,
                "future_only": entry.future_only,
                "must_not_exist_in_current_state": entry.must_not_exist_in_current_state,
                "created_by_future_pr_only": entry.created_by_future_pr_only,
            }
            for entry in paths.artifact_authority_paths
        ],
        "forbidden_artifact_checks": forbidden_artifact_checks,
        "validation_errors": failures,
    }
