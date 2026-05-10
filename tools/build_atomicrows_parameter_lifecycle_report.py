#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)

DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "atomic_rows"
    / "AtomicRowsParameterLifecycleRegistry.yaml"
)
DEFAULT_OUTPUT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterLifecycleReport.json"
)

REPORT_TYPE = "ATOMICROWS_PARAMETER_LIFECYCLE_REPORT"
REGISTRY_NAME = "AtomicRowsParameterLifecycleRegistry"
REGISTRY_MODEL = "PARAMETER_LIFECYCLE_ELIGIBILITY"
AUTHORITY_CLASS = "STATIC_LIFECYCLE_REGISTRY_ONLY_NOT_ATOMICROWS_BUNDLE_AUTHORITY"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
COMPLETE_COVERAGE_SENTINEL = "COMPLETE_PARAMETER_LIFECYCLE_REGISTRY"

LIFECYCLE_STATUSES = (
    "INVENTORY_ONLY",
    "RESEARCH_CANDIDATE",
    "SOURCE_EVIDENCE_REQUIRED",
    "RANGE_VALIDATED_STATIC_ONLY",
    "REPLAY_PAPER_CANDIDATE",
    "REPLAY_PAPER_VALIDATED",
    "OPTIMIZER_ELIGIBLE",
    "RUNTIME_ELIGIBLE",
    "LIVE_ELIGIBLE",
    "QUARANTINED_UNPROVEN",
    "RETIRED_NOT_USEFUL",
)

ENTRY_FIELDS = (
    "atomic_parameter_row_id",
    "row_pattern_id",
    "lifecycle_status",
    "parameter_family",
    "classical_or_quantum",
    "owner_section_id",
    "linked_capability_id",
    "unit",
    "scale",
    "allowed_range",
    "range_required",
    "default_value_policy",
    "source_authority_class",
    "evidence_required",
    "optimizer_eligibility",
    "runtime_eligibility",
    "live_eligibility",
    "research_route",
    "promotion_gate",
    "quarantine_reason",
    "retirement_reason",
    "authority_boundary",
)

AUTHORITY_BOUNDARY_FIELDS = (
    "creates_live_reachability",
    "creates_order_authority",
    "creates_runtime_cash_receipt",
    "creates_source_acceptance",
    "creates_connector_binding",
    "creates_atomicrows_bundle",
    "creates_profit_evidence",
    "reduces_blockers",
)

BLOCKED_FOR_ACTIVE_USE_STATUSES = {
    "RESEARCH_CANDIDATE",
    "SOURCE_EVIDENCE_REQUIRED",
    "QUARANTINED_UNPROVEN",
}


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _bool(value: Any) -> bool:
    return value is True


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_optimizer_eligibility(value: Any) -> dict[str, Any]:
    item = _mapping(value)
    return {
        "eligible": _bool(item.get("eligible")),
        "range_validated": _bool(item.get("range_validated")),
        "source_evidence_accepted": _bool(item.get("source_evidence_accepted")),
        "evidence_validated": _bool(item.get("evidence_validated")),
        "promotion_gate_validated": _bool(item.get("promotion_gate_validated")),
        "receipt_id": _string_or_none(item.get("receipt_id")),
        "blocking_reason": str(item.get("blocking_reason") or ""),
    }


def _normalize_runtime_eligibility(value: Any) -> dict[str, Any]:
    item = _mapping(value)
    return {
        "eligible": _bool(item.get("eligible")),
        "runtime_receipt_id": _string_or_none(item.get("runtime_receipt_id")),
        "blocking_reason": str(item.get("blocking_reason") or ""),
    }


def _normalize_live_eligibility(value: Any) -> dict[str, Any]:
    item = _mapping(value)
    return {
        "eligible": _bool(item.get("eligible")),
        "live_receipt_id": _string_or_none(item.get("live_receipt_id")),
        "owner_approval_receipt_id": _string_or_none(
            item.get("owner_approval_receipt_id")
        ),
        "blocking_reason": str(item.get("blocking_reason") or ""),
    }


def _normalize_authority_boundary(value: Any) -> dict[str, bool]:
    item = _mapping(value)
    return {field: _bool(item.get(field)) for field in AUTHORITY_BOUNDARY_FIELDS}


def _entry_identifier(entry: dict[str, Any]) -> str:
    row_id = entry.get("atomic_parameter_row_id")
    pattern_id = entry.get("row_pattern_id")
    if isinstance(row_id, str) and row_id:
        return row_id
    if isinstance(pattern_id, str) and pattern_id:
        return pattern_id
    return "<missing-row-id-or-pattern-id>"


def _normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: entry.get(field) for field in ENTRY_FIELDS}
    normalized["atomic_parameter_row_id"] = _string_or_none(
        normalized.get("atomic_parameter_row_id")
    )
    normalized["row_pattern_id"] = _string_or_none(normalized.get("row_pattern_id"))
    for field in (
        "lifecycle_status",
        "parameter_family",
        "classical_or_quantum",
        "owner_section_id",
        "linked_capability_id",
        "unit",
        "scale",
        "default_value_policy",
        "source_authority_class",
        "research_route",
        "promotion_gate",
    ):
        normalized[field] = str(normalized.get(field) or "")
    normalized["range_required"] = _bool(normalized.get("range_required"))
    normalized["evidence_required"] = _string_list(
        normalized.get("evidence_required")
    )
    normalized["optimizer_eligibility"] = _normalize_optimizer_eligibility(
        normalized.get("optimizer_eligibility")
    )
    normalized["runtime_eligibility"] = _normalize_runtime_eligibility(
        normalized.get("runtime_eligibility")
    )
    normalized["live_eligibility"] = _normalize_live_eligibility(
        normalized.get("live_eligibility")
    )
    normalized["quarantine_reason"] = _string_or_none(
        normalized.get("quarantine_reason")
    )
    normalized["retirement_reason"] = _string_or_none(
        normalized.get("retirement_reason")
    )
    normalized["authority_boundary"] = _normalize_authority_boundary(
        normalized.get("authority_boundary")
    )
    return normalized


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    registry = load_yaml_subset(path)
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise RegistryParseError("parameter lifecycle registry entries must be a list")
    return {
        "schema_version": registry.get("schema_version"),
        "registry_name": registry.get("registry_name"),
        "registry_model": registry.get("registry_model"),
        "authority_class": registry.get("authority_class"),
        "source_master_plan": registry.get("source_master_plan"),
        "final_expected_row_coverage": registry.get("final_expected_row_coverage"),
        "lifecycle_statuses": _string_list(registry.get("lifecycle_statuses")),
        "entries": [
            _normalize_entry(entry)
            for entry in entries
            if isinstance(entry, dict)
        ],
    }


def invalid_eligibility_claims(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for entry in entries:
        label = _entry_identifier(entry)
        status = entry.get("lifecycle_status")
        optimizer = _mapping(entry.get("optimizer_eligibility"))
        runtime = _mapping(entry.get("runtime_eligibility"))
        live = _mapping(entry.get("live_eligibility"))

        optimizer_eligible = optimizer.get("eligible") is True
        runtime_eligible = runtime.get("eligible") is True
        live_eligible = live.get("eligible") is True

        if status == "OPTIMIZER_ELIGIBLE" and not optimizer_eligible:
            failures.append(f"{label}: status claims optimizer eligibility")
        if status == "RUNTIME_ELIGIBLE" and not runtime_eligible:
            failures.append(f"{label}: status claims runtime eligibility")
        if status == "LIVE_ELIGIBLE" and not live_eligible:
            failures.append(f"{label}: status claims live eligibility")

        if status in BLOCKED_FOR_ACTIVE_USE_STATUSES and (
            optimizer_eligible or runtime_eligible or live_eligible
        ):
            failures.append(
                f"{label}: blocked lifecycle status may not be optimizer, runtime, "
                "or live eligible"
            )

        if optimizer_eligible:
            if status not in {
                "OPTIMIZER_ELIGIBLE",
                "RUNTIME_ELIGIBLE",
                "LIVE_ELIGIBLE",
            }:
                failures.append(
                    f"{label}: optimizer eligibility does not match lifecycle status"
                )
            for field in (
                "range_validated",
                "source_evidence_accepted",
                "evidence_validated",
                "promotion_gate_validated",
            ):
                if optimizer.get(field) is not True:
                    failures.append(
                        f"{label}: optimizer eligibility requires {field}=true"
                    )
            if entry.get("range_required") is True and entry.get("allowed_range") is None:
                failures.append(
                    f"{label}: optimizer eligibility requires an allowed_range"
                )
            if not entry.get("evidence_required"):
                failures.append(
                    f"{label}: optimizer eligibility requires evidence_required"
                )
            if not entry.get("promotion_gate"):
                failures.append(
                    f"{label}: optimizer eligibility requires a promotion_gate"
                )

        if runtime_eligible:
            if status not in {"RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE"}:
                failures.append(
                    f"{label}: runtime eligibility does not match lifecycle status"
                )
            if not optimizer_eligible:
                failures.append(f"{label}: runtime eligibility requires optimizer gate")
            if not runtime.get("runtime_receipt_id"):
                failures.append(
                    f"{label}: runtime eligibility requires runtime receipt"
                )
            if (
                entry.get("classical_or_quantum") == "QUANTUM"
                and not any(
                    "backend" in item.lower() or "provider" in item.lower()
                    for item in entry.get("evidence_required", [])
                )
            ):
                failures.append(
                    f"{label}: quantum runtime requires backend or provider evidence"
                )

        if live_eligible:
            if status != "LIVE_ELIGIBLE":
                failures.append(
                    f"{label}: live eligibility does not match lifecycle status"
                )
            if not runtime_eligible:
                failures.append(f"{label}: live eligibility requires runtime gate")
            if not live.get("live_receipt_id"):
                failures.append(f"{label}: live eligibility requires live receipt")
            if not live.get("owner_approval_receipt_id"):
                failures.append(
                    f"{label}: live eligibility requires owner approval receipt"
                )

        source_class = str(entry.get("source_authority_class") or "")
        if (
            entry.get("allowed_range") is not None
            and "ACCEPTED_SOURCE_EVIDENCE_PACKET_REQUIRED" in source_class
            and optimizer.get("source_evidence_accepted") is not True
        ):
            failures.append(
                f"{label}: source-dependent range requires accepted source evidence"
            )
    return failures


def _authority_boundary_all_false(entries: Sequence[dict[str, Any]]) -> bool:
    return all(
        entry.get("authority_boundary", {}).get(field) is False
        for entry in entries
        for field in AUTHORITY_BOUNDARY_FIELDS
    )


def _final_ready(
    registry: dict[str, Any],
    entries: Sequence[dict[str, Any]],
    invalid_claim_count: int,
) -> bool:
    if registry.get("final_expected_row_coverage") != COMPLETE_COVERAGE_SENTINEL:
        return False
    incomplete_statuses = {
        "INVENTORY_ONLY",
        "RESEARCH_CANDIDATE",
        "SOURCE_EVIDENCE_REQUIRED",
        "RANGE_VALIDATED_STATIC_ONLY",
        "REPLAY_PAPER_CANDIDATE",
        "QUARANTINED_UNPROVEN",
    }
    if any(entry.get("lifecycle_status") in incomplete_statuses for entry in entries):
        return False
    return invalid_claim_count == 0


def build_report(
    *,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    registry = load_registry(repo_root.resolve() / registry_path)
    entries = sorted(registry["entries"], key=_entry_identifier)
    statuses = Counter(entry["lifecycle_status"] for entry in entries)
    invalid_claim_count = len(invalid_eligibility_claims(entries))
    authority_boundary_all_false = _authority_boundary_all_false(entries)
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "registry_entry_count": len(entries),
        "parameter_family_count": len(
            {entry["parameter_family"] for entry in entries}
        ),
        "classical_entry_count": sum(
            1 for entry in entries if entry["classical_or_quantum"] == "CLASSICAL"
        ),
        "quantum_entry_count": sum(
            1 for entry in entries if entry["classical_or_quantum"] == "QUANTUM"
        ),
        "inventory_only_count": statuses.get("INVENTORY_ONLY", 0),
        "research_candidate_count": statuses.get("RESEARCH_CANDIDATE", 0),
        "source_evidence_required_count": statuses.get(
            "SOURCE_EVIDENCE_REQUIRED", 0
        ),
        "range_validated_static_only_count": statuses.get(
            "RANGE_VALIDATED_STATIC_ONLY", 0
        ),
        "replay_paper_candidate_count": statuses.get("REPLAY_PAPER_CANDIDATE", 0),
        "replay_paper_validated_count": statuses.get("REPLAY_PAPER_VALIDATED", 0),
        "optimizer_eligible_count": sum(
            1
            for entry in entries
            if entry["optimizer_eligibility"]["eligible"] is True
        ),
        "runtime_eligible_count": sum(
            1 for entry in entries if entry["runtime_eligibility"]["eligible"] is True
        ),
        "live_eligible_count": sum(
            1 for entry in entries if entry["live_eligibility"]["eligible"] is True
        ),
        "quarantined_unproven_count": statuses.get("QUARANTINED_UNPROVEN", 0),
        "retired_not_useful_count": statuses.get("RETIRED_NOT_USEFUL", 0),
        "invalid_eligibility_claim_count": invalid_claim_count,
        "final_ready": _final_ready(registry, entries, invalid_claim_count),
        "authority_boundary_all_false": authority_boundary_all_false,
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    report = build_report(
        repo_root=repo_root,
        registry_path=pathlib.Path(args.registry),
    )
    output = repo_root / pathlib.Path(args.out)
    write_report(report, output)
    print(
        "ATOMICROWS_PARAMETER_LIFECYCLE_REPORT_BUILT "
        f"entries={report['registry_entry_count']} "
        f"families={report['parameter_family_count']} "
        f"out={pathlib.Path(args.out)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
