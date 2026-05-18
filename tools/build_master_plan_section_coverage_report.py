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

from tools.master_plan_ingest import build_section_manifest

DEFAULT_MASTER_PLAN = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
DEFAULT_REGISTRY = (
    pathlib.Path("docs")
    / "master_plan"
    / "completion"
    / "QTTSectionCoverageRegistry.yaml"
)
DEFAULT_OUTPUT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "MasterPlanSectionCoverageReport.json"
)

REPORT_TYPE = "MASTER_PLAN_SECTION_COVERAGE_REPORT"
REPORT_VERSION = "MASTER_PLAN_SECTION_COVERAGE_REPORT_V1"
REGISTRY_NAME = "QTTSectionCoverageRegistry"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
ALL_SECTIONS_SENTINEL = "__ALL_PARSER_VISIBLE_SECTIONS__"

AUTHORITY_BOUNDARY_FIELDS = (
    "creates_live_reachability",
    "creates_order_authority",
    "creates_runtime_cash_receipt",
    "creates_atomicrows_bundle",
    "creates_profit_evidence",
    "reduces_blockers",
)

LIST_FIELDS = (
    "owner_section_ids",
    "required_files",
    "required_tools",
    "required_schemas",
    "required_tests",
    "required_reports",
    "required_receipts",
    "validation_commands",
)

REGISTRY_ENTRY_FIELDS = (
    "capability_id",
    "owner_section_ids",
    "section_title_or_capability_title",
    "coverage_class",
    "current_status",
    "required_files",
    "required_tools",
    "required_schemas",
    "required_tests",
    "required_reports",
    "required_receipts",
    "research_route",
    "unblock_condition",
    "retirement_allowed",
    "authority_boundary",
    "validation_commands",
)

ROUTE_CLASSES = (
    "CAPABILITY_ROUTE",
    "POLICY_ROUTE",
    "SOURCE_EVIDENCE_ROUTE",
    "REPLAY_PAPER_ROUTE",
    "RUNTIME_ROUTE",
    "OWNER_ROUTE",
    "QUARANTINE_ROUTE",
    "RETIREMENT_ROUTE",
    "CONTROLLER_REFERENCED_ROUTE",
    "QUANTUM_FORWARD_OPTIMIZATION_ROUTE",
    "OPTIMIZER_ARBITRATION_ROUTE",
    "LATENCY_COST_ROUTE",
    "UNRESOLVED_DEFAULT_ROUTE",
)

ROUTE_MAP_FIELDS = (
    "route_map_id",
    "route_map_version",
    "authority_class",
    "repo_canonical_pr_label",
    "roadmap_pr_label",
    "semantic_task_id",
    "source_manifest_reference",
    "route_entries",
    "generated_report_path",
    "controller_decision_reference",
    "existing_artifact_discovery_result",
    "changed_file_list_by_artifact_family",
    "no_old_coverage_ledger_reintroduction_flag",
    "no_runtime_live_order_profit_authority_created_flag",
    "no_source_connector_replay_paper_authority_created_flag",
    "no_quantum_backend_or_simulator_execution_created_flag",
    "no_master_plan_text_mutation_flag",
)

ROUTE_ENTRY_FIELDS = (
    "section_id",
    "normalized_section_title",
    "current_route_class",
    "previous_route_class_or_default_state",
    "route_owner_artifact",
    "route_owner_reason_code",
    "controller_state_reference",
    "downstream_consumer_reference",
    "traceability_basis",
    "evidence_basis",
    "route_confidence_class",
    "no_authority_created_flag",
    "no_master_plan_text_mutation_flag",
    "no_old_coverage_ledger_flag",
    "unresolved_reason_code_when_applicable",
    "quantum_forward_metadata",
)

QUANTUM_FORWARD_METADATA_FIELDS = (
    "quantum_relevance_class",
    "future_controller_reference",
    "future_roadmap_consumer_labels",
    "no_backend_execution_flag",
    "no_simulator_execution_flag",
    "no_optimizer_runtime_execution_flag",
    "no_quantum_advantage_claim_flag",
    "no_profit_or_latency_superiority_claim_flag",
)


class RegistryParseError(ValueError):
    pass


def _strip_inline_comment(line: str) -> str:
    if not line.lstrip().startswith("#"):
        return line.rstrip()
    return ""


def _yaml_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise RegistryParseError(f"YAML subset requires two-space indents: {line!r}")
        lines.append((indent, line.strip()))
    return lines


def _parse_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value == "{}":
        return {}
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def _split_mapping_item(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise RegistryParseError(f"expected key/value mapping item: {content!r}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise RegistryParseError(f"empty mapping key in YAML line: {content!r}")
    return key, value.strip()


def _parse_block(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    actual_indent, content = lines[index]
    if actual_indent < indent:
        return {}, index
    if actual_indent != indent:
        raise RegistryParseError(
            f"unexpected indent {actual_indent}; expected {indent}: {content!r}"
        )
    if content.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_mapping(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while index < len(lines):
        actual_indent, content = lines[index]
        if actual_indent < indent:
            break
        if actual_indent != indent:
            raise RegistryParseError(
                f"unexpected indent {actual_indent}; expected {indent}: {content!r}"
            )
        if content.startswith("- "):
            break
        key, value = _split_mapping_item(content)
        index += 1
        if value:
            mapping[key] = _parse_scalar(value)
            continue
        if index >= len(lines) or lines[index][0] <= indent:
            mapping[key] = None
            continue
        child, index = _parse_block(lines, index, lines[index][0])
        mapping[key] = child
    return mapping, index


def _parse_list(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[Any], int]:
    values: list[Any] = []
    while index < len(lines):
        actual_indent, content = lines[index]
        if actual_indent < indent:
            break
        if actual_indent != indent or not content.startswith("- "):
            break
        item_text = content[2:].strip()
        index += 1
        if item_text and ":" in item_text:
            key, value = _split_mapping_item(item_text)
            item: dict[str, Any] = {key: _parse_scalar(value) if value else None}
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
                if not isinstance(child, dict):
                    raise RegistryParseError(
                        f"list item mapping child must be a mapping: {item_text!r}"
                    )
                item.update(child)
            values.append(item)
            continue
        if item_text:
            values.append(_parse_scalar(item_text))
            continue
        if index < len(lines) and lines[index][0] > indent:
            child, index = _parse_block(lines, index, lines[index][0])
            values.append(child)
        else:
            values.append(None)
    return values, index


def load_yaml_subset(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = _yaml_lines(text)
    if not lines:
        raise RegistryParseError(f"registry is empty: {path}")
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise RegistryParseError(f"unparsed YAML content remains at line index {index}")
    if not isinstance(value, dict):
        raise RegistryParseError(f"registry root must be a mapping: {path}")
    return value


def _as_posix(path: str | pathlib.Path) -> str:
    return pathlib.Path(path).as_posix()


def _list_value(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _list_value(value) if item is not None]


def _entry_with_defaults(entry: dict[str, Any], index: int) -> dict[str, Any]:
    normalized = {field: entry.get(field) for field in REGISTRY_ENTRY_FIELDS}
    for field in LIST_FIELDS:
        normalized[field] = _string_list(normalized.get(field))
    normalized["capability_id"] = str(normalized.get("capability_id") or "")
    normalized["section_title_or_capability_title"] = str(
        normalized.get("section_title_or_capability_title") or ""
    )
    normalized["coverage_class"] = str(normalized.get("coverage_class") or "")
    normalized["current_status"] = str(normalized.get("current_status") or "")
    normalized["research_route"] = str(normalized.get("research_route") or "")
    normalized["unblock_condition"] = str(normalized.get("unblock_condition") or "")
    normalized["retirement_allowed"] = bool(normalized.get("retirement_allowed"))
    normalized["quarantine_reason"] = str(entry.get("quarantine_reason") or "")
    normalized["retirement_reason"] = str(entry.get("retirement_reason") or "")
    normalized["static_safety_stub"] = str(entry.get("static_safety_stub") or "")
    normalized["owner_deferred"] = bool(entry.get("owner_deferred"))
    authority = entry.get("authority_boundary") or {}
    if not isinstance(authority, dict):
        authority = {}
    normalized["authority_boundary"] = {
        field: bool(authority.get(field)) for field in AUTHORITY_BOUNDARY_FIELDS
    }
    normalized["entry_index"] = index
    return normalized


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _quantum_metadata_with_defaults(value: Any) -> dict[str, Any]:
    metadata = _dict_value(value)
    normalized = {field: metadata.get(field) for field in QUANTUM_FORWARD_METADATA_FIELDS}
    normalized["quantum_relevance_class"] = str(
        normalized.get("quantum_relevance_class") or "NONE"
    )
    normalized["future_controller_reference"] = str(
        normalized.get("future_controller_reference") or ""
    )
    normalized["future_roadmap_consumer_labels"] = _string_list(
        normalized.get("future_roadmap_consumer_labels")
    )
    for field in (
        "no_backend_execution_flag",
        "no_simulator_execution_flag",
        "no_optimizer_runtime_execution_flag",
        "no_quantum_advantage_claim_flag",
        "no_profit_or_latency_superiority_claim_flag",
    ):
        normalized[field] = bool(normalized.get(field))
    return normalized


def _route_entry_with_defaults(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: entry.get(field) for field in ROUTE_ENTRY_FIELDS}
    for field in ROUTE_ENTRY_FIELDS:
        if field == "quantum_forward_metadata":
            continue
        if field.startswith("no_"):
            normalized[field] = bool(normalized.get(field))
        elif normalized.get(field) is None:
            normalized[field] = None
        else:
            normalized[field] = str(normalized[field])
    normalized["quantum_forward_metadata"] = _quantum_metadata_with_defaults(
        normalized.get("quantum_forward_metadata")
    )
    return normalized


def _route_map_with_defaults(value: Any) -> dict[str, Any]:
    route_map = _dict_value(value)
    normalized = {field: route_map.get(field) for field in ROUTE_MAP_FIELDS}
    for field in (
        "route_map_id",
        "route_map_version",
        "authority_class",
        "repo_canonical_pr_label",
        "roadmap_pr_label",
        "semantic_task_id",
        "source_manifest_reference",
        "generated_report_path",
        "controller_decision_reference",
    ):
        normalized[field] = str(normalized.get(field) or "")
    for field in (
        "no_old_coverage_ledger_reintroduction_flag",
        "no_runtime_live_order_profit_authority_created_flag",
        "no_source_connector_replay_paper_authority_created_flag",
        "no_quantum_backend_or_simulator_execution_created_flag",
        "no_master_plan_text_mutation_flag",
    ):
        normalized[field] = bool(normalized.get(field))
    route_entries = [
        _route_entry_with_defaults(entry)
        for entry in _list_value(route_map.get("route_entries"))
        if isinstance(entry, dict)
    ]
    normalized["route_entries"] = sorted(
        route_entries,
        key=lambda entry: (
            str(entry.get("section_id") or ""),
            str(entry.get("normalized_section_title") or ""),
        ),
    )
    normalized["existing_artifact_discovery_result"] = _dict_value(
        normalized.get("existing_artifact_discovery_result")
    )
    normalized["changed_file_list_by_artifact_family"] = _dict_value(
        normalized.get("changed_file_list_by_artifact_family")
    )
    return normalized


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    registry = load_yaml_subset(path)
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise RegistryParseError("registry entries must be a list")
    normalized_entries = [
        _entry_with_defaults(entry, index)
        for index, entry in enumerate(entries, start=1)
        if isinstance(entry, dict)
    ]
    return {
        "schema_version": registry.get("schema_version"),
        "registry_name": registry.get("registry_name"),
        "coverage_model": registry.get("coverage_model"),
        "route_map": _route_map_with_defaults(registry.get("route_map")),
        "entries": normalized_entries,
    }


def _section_owner_id(section: dict[str, Any]) -> str:
    canonical_id = section.get("canonical_id")
    if isinstance(canonical_id, str) and canonical_id:
        return canonical_id
    return f"SECTION_INDEX_{int(section['index']):06d}"


def _owner_id_matches(owner_id: str, section: dict[str, Any]) -> bool:
    if owner_id == ALL_SECTIONS_SENTINEL:
        return True
    section_id = _section_owner_id(section)
    canonical_id = section.get("canonical_id")
    if section_id == owner_id:
        return True
    return (
        isinstance(canonical_id, str)
        and canonical_id.startswith(f"{owner_id}.")
    )


def _owner_id_specificity(owner_id: str) -> int:
    if owner_id == ALL_SECTIONS_SENTINEL:
        return 0
    return len(owner_id)


def _matching_entries(
    section: dict[str, Any],
    entries: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    matches: list[tuple[int, str, dict[str, Any]]] = []
    for entry in entries:
        owner_ids = entry["owner_section_ids"]
        specificity = max(
            (_owner_id_specificity(owner_id) for owner_id in owner_ids if _owner_id_matches(owner_id, section)),
            default=-1,
        )
        if specificity >= 0:
            matches.append((specificity, entry["capability_id"], entry))
    return [entry for _, _, entry in sorted(matches, key=lambda item: (-item[0], item[1]))]


def _coverage_flags(coverage_class: str) -> dict[str, bool]:
    return {
        "codable": coverage_class
        in {
            "EXECUTABLE_IMPLEMENTATION",
            "STATIC_CONTRACT",
            "SOURCE_EVIDENCE_DEPENDENT",
            "RUNTIME_RECEIPT_DEPENDENT",
            "OWNER_APPROVAL_DEPENDENT",
        },
        "policy_only": coverage_class == "POLICY_ONLY",
        "static_contract_only": coverage_class == "STATIC_CONTRACT",
        "source_evidence_dependent": coverage_class == "SOURCE_EVIDENCE_DEPENDENT",
        "runtime_receipt_dependent": coverage_class == "RUNTIME_RECEIPT_DEPENDENT",
        "owner_approval_dependent": coverage_class == "OWNER_APPROVAL_DEPENDENT",
    }


def _section_record(
    section: dict[str, Any],
    entries: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    matches = _matching_entries(section, entries)
    if not matches:
        raise RegistryParseError(f"section has no coverage route: {section['title']}")
    primary = matches[0]
    record = {
        "section_index": int(section["index"]),
        "owner_section_id": _section_owner_id(section),
        "canonical_id": section.get("canonical_id"),
        "section_title": str(section["title"]),
        "level": int(section["level"]),
        "line": int(section["line"]),
        "parser_visible": True,
        "capability_id": primary["capability_id"],
        "matching_capability_ids": [entry["capability_id"] for entry in matches],
        "coverage_class": primary["coverage_class"],
        "current_status": primary["current_status"],
        "section_title_or_capability_title": primary[
            "section_title_or_capability_title"
        ],
        "required_files": list(primary["required_files"]),
        "required_tools": list(primary["required_tools"]),
        "required_schemas": list(primary["required_schemas"]),
        "required_tests": list(primary["required_tests"]),
        "required_reports": list(primary["required_reports"]),
        "required_receipts": list(primary["required_receipts"]),
        "research_route": primary["research_route"],
        "unblock_condition": primary["unblock_condition"],
        "quarantine_reason": primary["quarantine_reason"],
        "retirement_allowed": primary["retirement_allowed"],
        "retirement_reason": primary["retirement_reason"],
        "static_safety_stub": primary["static_safety_stub"],
        "owner_deferred": primary["owner_deferred"],
        "authority_boundary": dict(primary["authority_boundary"]),
        "validation_commands": list(primary["validation_commands"]),
    }
    record.update(_coverage_flags(primary["coverage_class"]))
    return record


def _all_authority_boundaries_false(entries: Sequence[dict[str, Any]]) -> bool:
    return all(
        entry["authority_boundary"].get(field) is False
        for entry in entries
        for field in AUTHORITY_BOUNDARY_FIELDS
    )


def _routed(entry: dict[str, Any]) -> bool:
    return any(
        [
            entry.get("research_route"),
            entry.get("unblock_condition"),
            entry.get("required_receipts"),
            entry.get("quarantine_reason"),
            entry.get("retirement_reason"),
            entry.get("static_safety_stub"),
        ]
    )


def _blocked_or_future(entry: dict[str, Any]) -> bool:
    status = entry["current_status"]
    return (
        status in {"NOT_STARTED", "PARTIAL", "RESEARCH_ROUTED", "QUARANTINED_UNPROVEN"}
        or status.startswith("BLOCKED_")
    )


def _coverage_summary(
    section_records: Sequence[dict[str, Any]],
    entries: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    status_counts = Counter(record["current_status"] for record in section_records)
    class_counts = Counter(record["coverage_class"] for record in section_records)
    default_count = sum(
        1
        for record in section_records
        if record["capability_id"] == "parser_visible_section_research_default"
    )
    incomplete_statuses = {
        "NOT_STARTED",
        "PARTIAL",
        "BLOCKED_SOURCE_EVIDENCE",
        "BLOCKED_REPLAY_PAPER_EVIDENCE",
        "BLOCKED_RUNTIME_RECEIPT",
        "BLOCKED_OWNER_APPROVAL",
        "RESEARCH_ROUTED",
        "QUARANTINED_UNPROVEN",
    }
    return {
        "parser_visible_section_count": len(section_records),
        "registry_entry_count": len(entries),
        "sections_with_specific_capability_count": len(section_records) - default_count,
        "sections_using_default_research_route_count": default_count,
        "status_counts": dict(sorted(status_counts.items())),
        "coverage_class_counts": dict(sorted(class_counts.items())),
        "blocked_or_future_entries_routed": all(
            _routed(entry) for entry in entries if _blocked_or_future(entry)
        ),
        "authority_boundary_all_false": _all_authority_boundaries_false(entries),
        "final_ready": not any(
            record["current_status"] in incomplete_statuses
            for record in section_records
        ),
    }


def _count_by(values: Sequence[str], allowed_values: Sequence[str]) -> dict[str, int]:
    counts = Counter(values)
    return {value: int(counts.get(value, 0)) for value in allowed_values}


def _route_map_summary(route_map: dict[str, Any]) -> dict[str, Any]:
    entries = route_map.get("route_entries", [])
    if not isinstance(entries, list):
        entries = []
    route_classes = [
        str(entry.get("current_route_class") or "")
        for entry in entries
        if isinstance(entry, dict)
    ]
    confidence_classes = [
        str(entry.get("route_confidence_class") or "")
        for entry in entries
        if isinstance(entry, dict)
    ]
    return {
        "repo_canonical_pr_label": route_map.get("repo_canonical_pr_label"),
        "roadmap_pr_label": route_map.get("roadmap_pr_label"),
        "semantic_task_id": route_map.get("semantic_task_id"),
        "controller_decision_reference": route_map.get("controller_decision_reference"),
        "artifact_family_decision": route_map.get(
            "existing_artifact_discovery_result", {}
        ).get("decision"),
        "changed_file_list_by_artifact_family": route_map.get(
            "changed_file_list_by_artifact_family", {}
        ),
        "route_entry_count": len(entries),
        "count_by_route_class": _count_by(route_classes, ROUTE_CLASSES),
        "count_by_route_confidence_class": dict(
            sorted(Counter(confidence_classes).items())
        ),
        "unresolved_default_count": route_classes.count("UNRESOLVED_DEFAULT_ROUTE"),
        "quantum_forward_route_count": route_classes.count(
            "QUANTUM_FORWARD_OPTIMIZATION_ROUTE"
        ),
        "optimizer_arbitration_route_count": route_classes.count(
            "OPTIMIZER_ARBITRATION_ROUTE"
        ),
        "latency_cost_route_count": route_classes.count("LATENCY_COST_ROUTE"),
        "old_coverage_ledger_reintroduction_flag": False,
        "master_plan_mutation_count": 0,
        "runtime_authority_created": False,
        "live_authority_created": False,
        "source_fact_acceptance_created": False,
        "connector_semantic_binding_created": False,
        "replay_paper_result_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "latency_superiority_evidence_created": False,
        "quantum_backend_simulator_optimizer_execution_created": False,
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    master_plan: pathlib.Path = DEFAULT_MASTER_PLAN,
    registry_path: pathlib.Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    root = repo_root.resolve()
    master_plan_path = root / master_plan
    registry_full_path = root / registry_path
    text = master_plan_path.read_text(encoding="utf-8")
    manifest = build_section_manifest(
        _as_posix(master_plan),
        text,
        file_size_bytes=master_plan_path.stat().st_size,
    )
    registry = load_registry(registry_full_path)
    entries = sorted(registry["entries"], key=lambda entry: entry["capability_id"])
    section_records = [
        _section_record(section, entries)
        for section in manifest["sections"]
    ]
    return {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "deterministic_output": True,
        "generated_by": "tools/build_master_plan_section_coverage_report.py",
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_documents": {
            "master_plan": _as_posix(master_plan),
            "registry": _as_posix(registry_path),
            "master_plan_line_count": manifest["line_count"],
            "master_plan_file_size_bytes": manifest["file_size_bytes"],
            "master_plan_section_count": manifest["section_count"],
            "master_plan_required_markers": manifest["required_markers"],
        },
        "registry": {
            "registry_name": registry["registry_name"],
            "schema_version": registry["schema_version"],
            "coverage_model": registry["coverage_model"],
            "entry_count": len(entries),
        },
        "route_map": registry["route_map"],
        "route_map_summary": _route_map_summary(registry["route_map"]),
        "authority_boundary": {
            field: False for field in AUTHORITY_BOUNDARY_FIELDS
        },
        "coverage_summary": _coverage_summary(section_records, entries),
        "coverage_entries": entries,
        "section_coverage": section_records,
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--master-plan", default=str(DEFAULT_MASTER_PLAN))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    report = build_report(
        repo_root=pathlib.Path(args.repo_root),
        master_plan=pathlib.Path(args.master_plan),
        registry_path=pathlib.Path(args.registry),
    )
    output = pathlib.Path(args.repo_root) / pathlib.Path(args.out)
    write_report(report, output)
    print(
        "MASTER_PLAN_SECTION_COVERAGE_REPORT_BUILT "
        f"sections={report['coverage_summary']['parser_visible_section_count']} "
        f"entries={report['registry']['entry_count']} out={pathlib.Path(args.out)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
