"""PR155 read-only orchestration preflight consumption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import read_json_object
from .models import OrchestrationPreflightResult


def _text_artifact_consumed(root: Path, rel_path: Path, failures: list[str]) -> bool:
    path = root / rel_path
    if not path.exists():
        failures.append(f"{c.PR155_ORCHESTRATION_ARTIFACT_MISSING}: {rel_path.as_posix()}")
        return False
    try:
        path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(
            f"{c.PR155_ORCHESTRATION_ARTIFACT_INVALID}: {rel_path.as_posix()}: {exc}"
        )
        return False
    return True


def _json_artifact(
    root: Path,
    key: str,
    rel_path: Path,
    payloads: dict[str, Mapping[str, Any]],
    failures: list[str],
) -> bool:
    path = root / rel_path
    if not path.exists():
        failures.append(f"{c.PR155_ORCHESTRATION_ARTIFACT_MISSING}: {rel_path.as_posix()}")
        return False
    try:
        payloads[key] = read_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(
            f"{c.PR155_ORCHESTRATION_ARTIFACT_INVALID}: {rel_path.as_posix()}: {exc}"
        )
        return False
    return True


def _crosswalk_payload(
    root: Path,
    payloads: dict[str, Mapping[str, Any]],
    failures: list[str],
) -> tuple[bool, dict[str, Any], str | None]:
    alias_path = root / c.PR136_SECTION_CROSSWALK_ALIAS_PATH
    successor_path = root / c.PR136_SECTION_CROSSWALK_SUCCESSOR_PATH
    alias_exists = alias_path.exists()
    successor_exists = successor_path.exists()
    selected_rel: Path | None = None
    alias_applied = False
    if alias_exists:
        selected_rel = c.PR136_SECTION_CROSSWALK_ALIAS_PATH
    elif successor_exists:
        selected_rel = c.PR136_SECTION_CROSSWALK_SUCCESSOR_PATH
        alias_applied = True
    else:
        failures.append(c.PR155_ORCHESTRATION_CROSSWALK_MISSING)
        return False, {
            "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
            "alias_exists": False,
            "successor_path": c.PR136_SECTION_CROSSWALK_SUCCESSOR_PATH.as_posix(),
            "successor_exists": False,
            "successor_used": False,
            "alias_resolution_applied": False,
        }, None

    consumed = _json_artifact(
        root,
        "section_crosswalk_or_successor",
        selected_rel,
        payloads,
        failures,
    )
    return consumed, {
        "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
        "alias_exists": alias_exists,
        "successor_path": c.PR136_SECTION_CROSSWALK_SUCCESSOR_PATH.as_posix(),
        "successor_exists": successor_exists,
        "selected_path": selected_rel.as_posix(),
        "successor_used": selected_rel == c.PR136_SECTION_CROSSWALK_SUCCESSOR_PATH,
        "alias_resolution_applied": alias_applied,
    }, selected_rel.as_posix()


def load_control_plane_preflight(repo_root: Path | str) -> OrchestrationPreflightResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    payloads: dict[str, Mapping[str, Any]] = {}
    consumed: list[str] = []
    missing: list[str] = []

    json_specs = (
        ("pr_identity_roster", c.ROSTER_PATH),
        ("roadmap_execution_state", c.ROADMAP_EXECUTION_STATE_PATH),
        ("route_triage", c.PR136_ROUTE_TRIAGE_PATH),
        ("market_specific_index", c.PR136_MARKET_INDEX_PATH),
        ("command_action_matrix", c.PR136_COMMAND_MATRIX_PATH),
        ("atomicrows_reconciliation", c.PR137R_RECONCILIATION_PATH),
        ("atomicrows_semantic_contract", c.PR138_SEMANTIC_CONTRACT_PATH),
    )
    for key, rel_path in json_specs:
        if _json_artifact(root, key, rel_path, payloads, failures):
            consumed.append(rel_path.as_posix())
        else:
            missing.append(rel_path.as_posix())

    for key, rel_path in (
        ("launch_readiness_roadmap", c.LAUNCH_READINESS_ROADMAP_PATH),
        ("launch_readiness_policy", c.LAUNCH_READINESS_POLICY_PATH),
    ):
        if _text_artifact_consumed(root, rel_path, failures):
            payloads[key] = {"artifact_path": rel_path.as_posix(), "text_consumed": True}
            consumed.append(rel_path.as_posix())
        else:
            missing.append(rel_path.as_posix())

    crosswalk_consumed, alias_resolution, selected_crosswalk = _crosswalk_payload(
        root,
        payloads,
        failures,
    )
    if crosswalk_consumed and selected_crosswalk is not None:
        consumed.append(selected_crosswalk)
        if alias_resolution["alias_resolution_applied"]:
            missing.append(c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix())
    else:
        missing.append(c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix())

    consumed_sorted = sorted(set(consumed))
    missing_sorted = sorted(set(missing))
    preflight = {
        "consumed_control_plane_artifacts": consumed_sorted,
        "missing_control_plane_artifacts": missing_sorted,
        "alias_resolution_applied": alias_resolution,
        "pr_identity_roster_consumed": c.ROSTER_PATH.as_posix() in consumed_sorted,
        "roadmap_execution_state_consumed": (
            c.ROADMAP_EXECUTION_STATE_PATH.as_posix() in consumed_sorted
        ),
        "launch_readiness_policy_consumed": (
            c.LAUNCH_READINESS_POLICY_PATH.as_posix() in consumed_sorted
        ),
        "route_triage_consumed": c.PR136_ROUTE_TRIAGE_PATH.as_posix() in consumed_sorted,
        "section_crosswalk_or_successor_consumed": crosswalk_consumed,
        "market_specific_index_consumed": (
            c.PR136_MARKET_INDEX_PATH.as_posix() in consumed_sorted
        ),
        "command_action_matrix_consumed": (
            c.PR136_COMMAND_MATRIX_PATH.as_posix() in consumed_sorted
        ),
        "atomicrows_reconciliation_consumed": (
            c.PR137R_RECONCILIATION_PATH.as_posix() in consumed_sorted
        ),
        "atomicrows_semantic_contract_consumed": (
            c.PR138_SEMANTIC_CONTRACT_PATH.as_posix() in consumed_sorted
        ),
        "pr155_allowed_to_continue": not failures,
        "preflight_block_codes": sorted(set(failures)),
        "orchestration_inputs_used_for_record_enrichment": list(
            c.ORCHESTRATION_ENRICHMENT_ARTIFACT_KEYS
        ),
    }
    return OrchestrationPreflightResult(
        preflight=preflight,
        payloads=payloads,
        failures=tuple(sorted(set(failures))),
    )
