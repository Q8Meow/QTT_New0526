"""PR161A report indexes used by PR161B coverage matching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .candidate_normalizer import normalize_candidate_name
from .io import read_json, records


def build_pr161a_coverage_index(root: Path | str) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    payloads = {
        key: read_json(repo_root / path)
        for key, path in c.PR161A_REPORT_PATHS.items()
        if (repo_root / path).exists()
    }
    field_records = records(payloads.get("field_inventory", {}))
    atomicrows = records(payloads.get("atomicrows_entity", {}))
    pr154 = records(payloads.get("pr154_entity", {}))
    quantum_profiles = records(payloads.get("quantum_profiles", {}))
    quantum_formulas = records(payloads.get("quantum_formulas", {}))
    quantum_strategies = records(payloads.get("quantum_strategies", {}))
    quantum_replay = records(payloads.get("quantum_replay_queue", {}))
    replay = records(payloads.get("replay_queue", {}))
    return {
        "payloads": payloads,
        "field_records": field_records,
        "field_names": _field_names(field_records),
        "atomicrows": atomicrows,
        "atomicrow_ids": [str(record.get("row_id")) for record in atomicrows if record.get("row_id")],
        "pr154": pr154,
        "pr154_target_ids": [str(record.get("target_id")) for record in pr154 if record.get("target_id")],
        "quantum_profiles": quantum_profiles,
        "quantum_profiles_by_family": _quantum_by_family(quantum_profiles),
        "quantum_formulas": quantum_formulas,
        "quantum_formula_families": {
            normalize_candidate_name(str(record.get("formula_family") or "")): record
            for record in quantum_formulas
        },
        "quantum_strategies": quantum_strategies,
        "quantum_replay": quantum_replay,
        "replay_route_ids": [str(record.get("replay_paper_route_id")) for record in replay if record.get("replay_paper_route_id")],
        "final_summary": records(payloads.get("final_summary", {}))[0] if records(payloads.get("final_summary", {})) else {},
    }


def deterministic_pick(values: list[str], seed: str, *, width: int = 1) -> list[str]:
    if not values:
        return []
    start = sum(ord(char) for char in seed) % len(values)
    return [values[(start + offset) % len(values)] for offset in range(min(width, len(values)))]


def _field_names(field_records: list[dict[str, Any]]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for record in field_records:
        record_id = str(record.get("record_id"))
        for key in (
            "field_path",
            "field_name",
            "field_semantic_type",
            "parameter_role",
            "algorithm_family",
            "formula_expression",
            "optimizer_role",
        ):
            value = record.get(key)
            if value:
                output.setdefault(normalize_candidate_name(str(value)), []).append(record_id)
    return output


def _quantum_by_family(profiles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for profile in profiles:
        profile_type = str(profile.get("quantum_profile_type") or profile.get("candidate_family") or "")
        family = profile_type.split("_", 1)[0] if profile_type else "QUANTUM"
        if family == "QUANTUM":
            family = "ANNEALING" if "ANNEALING" in profile_type else "QUANTUM"
        if profile_type.startswith("HYBRID") or profile_type.startswith("OWNER"):
            family = "HYBRID"
        output.setdefault(family, []).append(profile)
    return output
