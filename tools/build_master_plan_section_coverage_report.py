#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import pathlib
import re
import sys
from typing import Any, Iterable, Sequence

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
DEFAULT_ROADMAP_INDEX = (
    pathlib.Path("docs") / "roadmap" / "QTT_PRs_Roadmap_Index_v1_0.json"
)
DEFAULT_BLUEPRINT_INDEX = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
DEFAULT_CONTROLLER = (
    pathlib.Path("docs")
    / "roadmap"
    / "QTT_Roadmap_Execution_State_Controller_v1_0.json"
)
DEFAULT_ROSTER = (
    pathlib.Path("docs") / "roadmap" / "QTT_PR_Identity_Roster_v1_0.json"
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
    "CONNECTOR_SEMANTIC_ROUTE",
    "REPLAY_PAPER_ROUTE",
    "RUNTIME_ROUTE",
    "RUNTIME_CASH_ROUTE",
    "OWNER_ROUTE",
    "GOVERNANCE_ROUTE",
    "RISK_ROUTE",
    "DASHBOARD_OWNER_SURFACE_ROUTE",
    "RESEARCH_ROUTE",
    "QUARANTINE_ROUTE",
    "RETIREMENT_ROUTE",
    "CONTROLLER_REFERENCED_ROUTE",
    "QUANTUM_FORWARD_OPTIMIZATION_ROUTE",
    "QUANTUM_BACKEND_ROUTE",
    "OPTIMIZER_ARBITRATION_ROUTE",
    "LATENCY_COST_ROUTE",
    "MARKET_EXPANSION_ROUTE",
    "CROSS_MARKET_ROUTE",
    "UNRESOLVED_DEFAULT_ROUTE",
)

ROUTE_CONFIDENCE_CLASSES = (
    "EXACT_PR119_ROUTE_ENTRY",
    "EXACT_CONTROLLER_REFERENCE",
    "EXACT_ROADMAP_INDEX_REFERENCE",
    "EXACT_BLUEPRINT_INDEX_REFERENCE",
    "EXACT_ROADMAP_BLUEPRINT_REFERENCE",
    "EXACT_ARTIFACT_REFERENCE",
    "EXACT_SCHEMA_REFERENCE",
    "EXACT_VALIDATOR_REFERENCE",
    "EXACT_TOOL_REFERENCE",
    "EXACT_REPORT_REFERENCE",
    "EXACT_MASTER_PLAN_SECTION_REFERENCE",
    "EXACT_MARKET_TOKEN_REFERENCE",
    "EXACT_STAGE_REFERENCE",
    "PARENT_CAPABILITY_RULE_REFERENCE",
    "DEFAULT_RESEARCH_ROUTE",
    "UNRESOLVED_EXPLICITLY",
    "OWNER_POLICY_REFERENCE",
)

PARENT_CAPABILITY_GROUP_IDS = (
    "CODEX_BUILD_DOCTRINE_AND_TRACEABILITY",
    "MASTER_PLAN_SECTION_COVERAGE_AND_COMPLETION",
    "SOURCE_EVIDENCE_AND_ACCEPTED_FACTS",
    "CONNECTOR_SEMANTIC_BINDING_AND_VENUE_NORMALIZATION",
    "RUNTIME_RESOLVER_AND_SNAPSHOT_INPUT_IDENTITY",
    "REPLAY_PAPER_DUAL_RESULT_AND_OWNER_REVIEW",
    "RUNTIME_CASH_PRIVATE_STATE_AND_EXPOSURE",
    "ORDER_INTENT_EXECUTION_ROUTER_AND_PRETRADE_GATES",
    "ATOMICROWS_PARAMETER_ALGORITHM_AGENT_INVENTORY",
    "EDGE_STACK_SCORING_SELECTION_AND_HANDOFF",
    "QUANTUM_POLICY_APPLICABILITY_OPTIMIZATION_AND_BACKEND",
    "LATENCY_COST_SLIPPAGE_AND_EXECUTION_QUALITY",
    "DASHBOARD_OWNER_APPROVAL_AND_GOVERNANCE",
    "RESEARCH_INTAKE_EXTERNAL_REPO_AND_NEURAL_SIGNAL",
    "MARKET_EXPANSION_AND_CROSS_MARKET_ADAPTATION",
    "RISK_LIMIT_KILL_SWITCH_AND_POST_TRADE_SAFETY",
    "LAUNCH_RUNBOOK_CANARY_ARBITRAGE_AND_LIVE_PROMOTION",
    "QUARANTINE_RETIREMENT_AND_NEGATIVE_EVIDENCE",
    "UNRESOLVED_RESEARCH_DEFAULT",
)

UNRESOLVED_REASON_CODES = (
    "NO_EXACT_ARTIFACT_OWNER_FOUND",
    "NO_EXACT_CONTROLLER_REFERENCE_FOUND",
    "NO_EXACT_ROADMAP_BLUEPRINT_CONTROLLER_OWNER_FOUND",
    "AMBIGUOUS_SECTION_SCOPE",
    "TITLE_SIMILARITY_ONLY_NOT_ALLOWED",
    "MARKET_RELEVANCE_UNRESOLVED",
    "WOULD_REQUIRE_MASTER_PLAN_MUTATION",
    "WOULD_REQUIRE_RUNTIME_OR_LIVE_AUTHORITY",
    "WOULD_REQUIRE_SOURCE_OR_CONNECTOR_AUTHORITY",
    "WOULD_REQUIRE_REPLAY_OR_PAPER_RESULT",
    "WOULD_REQUIRE_QUANTUM_BACKEND_OR_OPTIMIZER_EXECUTION",
    "WOULD_REINTRODUCE_OLD_COVERAGE_LEDGER",
    "OUT_OF_SCOPE_FOR_PR119",
    "OUT_OF_SCOPE_FOR_PR120",
)

MARKET_STAGE_CLASSES = (
    "STAGE_1_ACTIVE_SCOPE",
    "STAGE_2_CANDIDATE_SCOPE",
    "LATER_STAGE_CANDIDATE_SCOPE",
    "CROSS_MARKET_FOUNDATION_SCOPE",
    "OWNER_REVIEW_REQUIRED_SCOPE",
)

MARKET_SCOPE_CONFIDENCE_CLASSES = (
    "EXACT_OWNER_POLICY_REFERENCE",
    "EXACT_MASTER_PLAN_MARKET_REFERENCE",
    "EXACT_VENUE_ID_REFERENCE",
    "EXACT_ROADMAP_BLUEPRINT_REFERENCE",
    "EXACT_ARTIFACT_REFERENCE",
    "CROSS_MARKET_GENERIC_REFERENCE",
    "OWNER_REVIEW_REQUIRED",
)

MARKET_RELEVANCE_CLASSES = (
    "DIRECT_MARKET_SECTION",
    "DIRECT_VENUE_SECTION",
    "CROSS_MARKET_FOUNDATION",
    "SOURCE_EVIDENCE_FOR_MARKET",
    "CONNECTOR_OR_RUNTIME_FOR_MARKET",
    "REPLAY_PAPER_OR_LAUNCH_FOR_MARKET",
    "QUANTUM_OR_OPTIMIZER_FOR_MARKET",
    "RISK_OR_LATENCY_FOR_MARKET",
    "OWNER_DASHBOARD_OR_GOVERNANCE_FOR_MARKET",
    "RESEARCH_SIGNAL_FOR_MARKET",
    "MARKET_RELEVANCE_UNRESOLVED",
)

PR_LABEL_RE = re.compile(r"\bPR\s*#(\d+)\b")

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

COMMAND_FAMILIES = (
    "COVERAGE_TRIAGE_COMMAND",
    "PARENT_CAPABILITY_COMMAND",
    "COMMAND_MATRIX_COMMAND",
    "SOURCE_EVIDENCE_COMMAND",
    "CONNECTOR_SEMANTIC_COMMAND",
    "RUNTIME_RESOLVER_COMMAND",
    "RUNTIME_CASH_COMMAND",
    "REPLAY_PAPER_COMMAND",
    "OWNER_REVIEW_COMMAND",
    "LIVE_LAUNCH_GATED_COMMAND",
    "ORDER_INTENT_GATED_COMMAND",
    "RISK_SAFETY_COMMAND",
    "DASHBOARD_OWNER_SURFACE_COMMAND",
    "RESEARCH_INTAKE_COMMAND",
    "ATOMICROWS_INVENTORY_COMMAND",
    "EDGE_SELECTION_SCORING_COMMAND",
    "QUANTUM_POLICY_COMMAND",
    "QUANTUM_FORWARD_OPTIMIZATION_COMMAND",
    "QUANTUM_BACKEND_GATED_COMMAND",
    "LATENCY_COST_COMMAND",
    "MARKET_INDEX_COMMAND",
    "FUTURE_MARKET_DEFERRED_COMMAND",
    "QUARANTINE_COMMAND",
    "RETIREMENT_COMMAND",
    "UNRESOLVED_RESEARCH_COMMAND",
)

COMMAND_SCOPE_CLASSES = (
    "STATIC_CONTROL_PLANE_ONLY",
    "STATIC_REPORTING_ONLY",
    "STATIC_INDEX_ONLY",
    "STATIC_VALIDATION_ONLY",
    "FUTURE_SOURCE_WORKFLOW_GATED",
    "FUTURE_CONNECTOR_BINDING_GATED",
    "FUTURE_RUNTIME_GATED",
    "FUTURE_REPLAY_PAPER_GATED",
    "FUTURE_OWNER_REVIEW_GATED",
    "FUTURE_LIVE_LAUNCH_GATED",
    "FUTURE_QUANTUM_BACKEND_GATED",
    "FUTURE_MARKET_EXPANSION_GATED",
    "OWNER_REVIEW_REQUIRED",
)

COMMAND_AUTHORITY_CLASSES = (
    "NO_EXECUTION_AUTHORITY",
    "NO_RUNTIME_AUTHORITY",
    "NO_SOURCE_RETRIEVAL_AUTHORITY",
    "NO_SOURCE_ACCEPTANCE_AUTHORITY",
    "NO_CONNECTOR_BINDING_AUTHORITY",
    "NO_REPLAY_PAPER_RESULT_AUTHORITY",
    "NO_ORDER_AUTHORITY",
    "NO_LIVE_AUTHORITY",
    "NO_PROFIT_EVIDENCE_AUTHORITY",
    "NO_QUANTUM_BACKEND_AUTHORITY",
    "NO_MARKET_LAUNCH_AUTHORITY",
    "FUTURE_OWNER_APPROVAL_REQUIRED",
)

COMMAND_OWNER_CLASSES = (
    "CODEX_STATIC_BUILDER",
    "VALIDATION_GATE_BUILDER",
    "SOURCE_EVIDENCE_AGENT_FUTURE",
    "CONNECTOR_AGENT_FUTURE",
    "RUNTIME_RESOLVER_AGENT_FUTURE",
    "REPLAY_PAPER_AGENT_FUTURE",
    "OWNER_REVIEW_AGENT_FUTURE",
    "RISK_AGENT_FUTURE",
    "DASHBOARD_AGENT_FUTURE",
    "QUANTUM_AGENT_FUTURE",
    "LATENCY_EXECUTION_QUALITY_AGENT_FUTURE",
    "MARKET_EXPANSION_AGENT_FUTURE",
    "OWNER_REVIEW_REQUIRED",
)

COMMAND_CONSUMER_CLASSES = (
    "VALIDATION_REPORT_CONSUMER",
    "STATIC_ROADMAP_BLUEPRINT_CONSUMER",
    "FUTURE_SOURCE_WORKFLOW_CONSUMER",
    "FUTURE_CONNECTOR_CONSUMER",
    "FUTURE_RUNTIME_CONSUMER",
    "FUTURE_REPLAY_PAPER_CONSUMER",
    "FUTURE_OWNER_REVIEW_CONSUMER",
    "FUTURE_LIVE_LAUNCH_CONSUMER",
    "FUTURE_ORDER_INTENT_CONSUMER",
    "FUTURE_QUANTUM_CONSUMER",
    "FUTURE_LATENCY_CONSUMER",
    "FUTURE_MARKET_EXPANSION_CONSUMER",
    "OWNER_REVIEW_REQUIRED_CONSUMER",
)

COMMAND_STATUSES = (
    "STATIC_COMMAND_INTENT_RECORDED",
    "FUTURE_GATED_COMMAND_INTENT_RECORDED",
    "OWNER_REVIEW_REQUIRED_COMMAND_INTENT_RECORDED",
    "UNRESOLVED_COMMAND_INTENT_RECORDED",
    "DEFERRED_FUTURE_MARKET_COMMAND_INTENT_RECORDED",
)

STATIC_ALLOWED_OPERATIONS = (
    "READ_CROSSWALK",
    "READ_ROUTE_MAP",
    "READ_MARKET_INDEX",
    "GENERATE_STATIC_REPORT",
    "RUN_STATIC_VALIDATOR",
    "CLASSIFY_UNRESOLVED",
    "QUEUE_OWNER_REVIEW",
    "REFERENCE_CONTROLLER_STATE",
    "REFERENCE_ROADMAP_BLUEPRINT",
)

FUTURE_GATED_OPERATIONS = (
    "FUTURE_SOURCE_RETRIEVAL",
    "FUTURE_SOURCE_ACCEPTANCE",
    "FUTURE_CONNECTOR_BINDING",
    "FUTURE_RUNTIME_SNAPSHOT",
    "FUTURE_RUNTIME_CASH_RECEIPT",
    "FUTURE_REPLAY_EXECUTION",
    "FUTURE_PAPER_EXECUTION",
    "FUTURE_OWNER_REVIEW_RECEIPT",
    "FUTURE_LIVE_CANARY",
    "FUTURE_ORDER_INTENT",
    "FUTURE_ORDER_EXECUTION",
    "FUTURE_QUANTUM_BACKEND_RECEIPT",
    "FUTURE_OPTIMIZER_EXECUTION",
    "FUTURE_MARKET_EXPANSION",
    "FUTURE_STAGE2_MARKET_SELECTION",
)

COMMAND_BLOCK_REASONS = (
    "STATIC_CONTROL_PLANE_ONLY",
    "FUTURE_SOURCE_RETRIEVAL_REQUIRES_PR105",
    "SOURCE_FACT_ACCEPTANCE_NOT_CREATED",
    "CONNECTOR_BINDING_REQUIRES_FUTURE_PR",
    "RUNTIME_AUTHORITY_REQUIRES_FUTURE_PR",
    "RUNTIME_CASH_RECEIPT_REQUIRES_FUTURE_PR",
    "REPLAY_PAPER_RESULT_REQUIRES_FUTURE_PR",
    "ORDER_AUTHORITY_REQUIRES_FUTURE_PR",
    "LIVE_AUTHORITY_REQUIRES_OWNER_APPROVAL",
    "PROFIT_EVIDENCE_NOT_CREATED",
    "LATENCY_SUPERIORITY_EVIDENCE_NOT_CREATED",
    "QUANTUM_BACKEND_EXECUTION_REQUIRES_FUTURE_CONTROLLER_STATE",
    "QUANTUM_SIMULATOR_EXECUTION_NOT_CREATED",
    "OPTIMIZER_RUNTIME_EXECUTION_NOT_CREATED",
    "MARKET_LAUNCH_AUTHORITY_NOT_CREATED",
    "STAGE2_MARKET_SELECTION_NOT_CREATED",
    "FUTURE_MARKET_SCOPE_DEFERRED",
    "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE",
    "NO_EXACT_ARTIFACT_OWNER_FOUND",
    "NO_OPEN_ENDED_MARKET_TAXONOMY_ALLOWED",
    "MASTER_PLAN_TEXT_MUTATION_FORBIDDEN",
    "OLD_COVERAGE_LEDGER_FORBIDDEN",
    "IMPLEMENTATION_COMPLETION_NOT_CLAIMED",
    "LAUNCH_READINESS_NOT_CLAIMED",
)

EXPLICIT_FUTURE_MARKET_CANDIDATE_FAMILIES = (
    "STOCKS",
    "CRYPTOCURRENCY",
    "FUTURES",
    "OPTIONS",
    "EQUITIES",
    "ETFS",
    "FX",
    "COMMODITIES",
)

FORBIDDEN_MARKET_TAXONOMY_VALUES = (
    "ETC",
    "OTHER",
    "OTHER_MARKETS",
    "MISC_MARKETS",
    "GENERAL_MARKETS",
    "UNKNOWN_MARKET",
    "ANY_OTHER_MARKET",
    "OTHER_OWNER_APPROVED_FUTURE_MARKET",
)

CENTRAL_CONFIG_FIELDS = (
    "roadmap_crosswalk_config",
    "command_matrix_config",
    "route_class_enum",
    "route_confidence_class_enum",
    "parent_capability_group_enum",
    "unresolved_reason_code_enum",
    "market_taxonomy",
    "command_family_enum",
    "command_scope_class_enum",
    "command_authority_class_enum",
    "command_owner_class_enum",
    "command_consumer_class_enum",
    "command_status_enum",
    "static_allowed_operation_enum",
    "future_gated_operation_enum",
    "command_block_reason_enum",
    "explicit_future_market_candidate_family_enum",
    "forbidden_market_taxonomy_value_enum",
    "owner_review_future_market_scope_classification",
    "route_class_to_command_family_rules",
    "parent_capability_to_command_family_rules",
    "market_scope_to_command_rules",
    "quantum_command_rules",
    "latency_command_rules",
    "source_connector_runtime_replay_live_command_rules",
    "stage1_prediction_market_only_rules",
    "future_market_deferral_rules",
    "no_open_ended_market_taxonomy_rules",
    "authority_boundary_defaults",
    "exact_pr119_route_preservation_rules",
    "roadmap_blueprint_controller_mapping_rules",
    "market_relevance_mapping_rules",
    "deterministic_sorting_rules",
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


def _central_config_with_defaults(registry: dict[str, Any]) -> dict[str, Any]:
    config = {field: registry.get(field) for field in CENTRAL_CONFIG_FIELDS}
    config["roadmap_crosswalk_config"] = _dict_value(
        config.get("roadmap_crosswalk_config")
    )
    config["command_matrix_config"] = _dict_value(
        config.get("command_matrix_config")
    )
    config["route_class_enum"] = _string_list(config.get("route_class_enum")) or list(
        ROUTE_CLASSES
    )
    config["route_confidence_class_enum"] = _string_list(
        config.get("route_confidence_class_enum")
    ) or list(ROUTE_CONFIDENCE_CLASSES)
    config["parent_capability_group_enum"] = [
        item
        for item in _list_value(config.get("parent_capability_group_enum"))
        if isinstance(item, dict)
    ]
    config["unresolved_reason_code_enum"] = _string_list(
        config.get("unresolved_reason_code_enum")
    ) or list(UNRESOLVED_REASON_CODES)
    config["market_taxonomy"] = [
        item
        for item in _list_value(config.get("market_taxonomy"))
        if isinstance(item, dict)
    ]
    config["command_family_enum"] = _string_list(
        config.get("command_family_enum")
    ) or list(COMMAND_FAMILIES)
    config["command_scope_class_enum"] = _string_list(
        config.get("command_scope_class_enum")
    ) or list(COMMAND_SCOPE_CLASSES)
    config["command_authority_class_enum"] = _string_list(
        config.get("command_authority_class_enum")
    ) or list(COMMAND_AUTHORITY_CLASSES)
    config["command_owner_class_enum"] = _string_list(
        config.get("command_owner_class_enum")
    ) or list(COMMAND_OWNER_CLASSES)
    config["command_consumer_class_enum"] = _string_list(
        config.get("command_consumer_class_enum")
    ) or list(COMMAND_CONSUMER_CLASSES)
    config["command_status_enum"] = _string_list(
        config.get("command_status_enum")
    ) or list(COMMAND_STATUSES)
    config["static_allowed_operation_enum"] = _string_list(
        config.get("static_allowed_operation_enum")
    ) or list(STATIC_ALLOWED_OPERATIONS)
    config["future_gated_operation_enum"] = _string_list(
        config.get("future_gated_operation_enum")
    ) or list(FUTURE_GATED_OPERATIONS)
    config["command_block_reason_enum"] = _string_list(
        config.get("command_block_reason_enum")
    ) or list(COMMAND_BLOCK_REASONS)
    config["explicit_future_market_candidate_family_enum"] = _string_list(
        config.get("explicit_future_market_candidate_family_enum")
    ) or list(EXPLICIT_FUTURE_MARKET_CANDIDATE_FAMILIES)
    config["forbidden_market_taxonomy_value_enum"] = _string_list(
        config.get("forbidden_market_taxonomy_value_enum")
    ) or list(FORBIDDEN_MARKET_TAXONOMY_VALUES)
    config["owner_review_future_market_scope_classification"] = _dict_value(
        config.get("owner_review_future_market_scope_classification")
    )
    config["route_class_to_command_family_rules"] = [
        item
        for item in _list_value(config.get("route_class_to_command_family_rules"))
        if isinstance(item, dict)
    ]
    config["parent_capability_to_command_family_rules"] = [
        item
        for item in _list_value(config.get("parent_capability_to_command_family_rules"))
        if isinstance(item, dict)
    ]
    config["market_scope_to_command_rules"] = _dict_value(
        config.get("market_scope_to_command_rules")
    )
    config["quantum_command_rules"] = _dict_value(config.get("quantum_command_rules"))
    config["latency_command_rules"] = _dict_value(config.get("latency_command_rules"))
    config["source_connector_runtime_replay_live_command_rules"] = _dict_value(
        config.get("source_connector_runtime_replay_live_command_rules")
    )
    config["stage1_prediction_market_only_rules"] = _dict_value(
        config.get("stage1_prediction_market_only_rules")
    )
    config["future_market_deferral_rules"] = _dict_value(
        config.get("future_market_deferral_rules")
    )
    config["no_open_ended_market_taxonomy_rules"] = _dict_value(
        config.get("no_open_ended_market_taxonomy_rules")
    )
    config["authority_boundary_defaults"] = _dict_value(
        config.get("authority_boundary_defaults")
    )
    config["exact_pr119_route_preservation_rules"] = _dict_value(
        config.get("exact_pr119_route_preservation_rules")
    )
    config["roadmap_blueprint_controller_mapping_rules"] = _dict_value(
        config.get("roadmap_blueprint_controller_mapping_rules")
    )
    config["market_relevance_mapping_rules"] = _dict_value(
        config.get("market_relevance_mapping_rules")
    )
    config["deterministic_sorting_rules"] = _dict_value(
        config.get("deterministic_sorting_rules")
    )
    return config


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
        "central_config": _central_config_with_defaults(registry),
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


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _labels_from_text(value: Any) -> list[str]:
    labels: set[str] = set()
    if isinstance(value, str):
        for match in PR_LABEL_RE.finditer(value):
            labels.add(f"PR #{int(match.group(1))}")
    elif isinstance(value, list):
        for item in value:
            labels.update(_labels_from_text(item))
    elif isinstance(value, dict):
        for item in value.values():
            labels.update(_labels_from_text(item))
    return _sort_pr_labels(labels)


def _sort_pr_labels(labels: Iterable[str]) -> list[str]:
    def key(label: str) -> tuple[int, str]:
        match = PR_LABEL_RE.search(label)
        return (int(match.group(1)) if match else 10**9, label)

    return sorted({str(label) for label in labels if label}, key=key)


def _roadmap_index_by_label(roadmap_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry.get("delivery_label")): entry
        for entry in _list_value(roadmap_index.get("pr_entries"))
        if isinstance(entry, dict) and entry.get("delivery_label")
    }


def _blueprint_index_by_label(blueprint_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry.get("delivery_label")): entry
        for entry in _list_value(blueprint_index.get("entries"))
        if isinstance(entry, dict) and entry.get("delivery_label")
    }


def _controller_by_label(
    controller: dict[str, Any],
) -> dict[str, tuple[str, dict[str, Any]]]:
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for index, entry in enumerate(_list_value(controller.get("roadmap_range_currentization"))):
        if isinstance(entry, dict) and entry.get("roadmap_pr_label"):
            result[str(entry["roadmap_pr_label"])] = (
                f"docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json#/roadmap_range_currentization/{index}",
                entry,
            )
    return result


def _roster_entry(entries: Sequence[dict[str, Any]], label: str) -> dict[str, Any]:
    for entry in entries:
        if entry.get("repo_canonical_pr_label") == label:
            return entry
    return {}


def _parent_group_lookup(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    groups = {}
    for group in config.get("parent_capability_group_enum", []):
        if isinstance(group, dict) and group.get("parent_capability_group_id"):
            groups[str(group["parent_capability_group_id"])] = group
    return groups


def _rule_list(config: dict[str, Any]) -> list[dict[str, Any]]:
    rules = config.get("roadmap_blueprint_controller_mapping_rules", {})
    return [
        item
        for item in _list_value(rules.get("parent_capability_rules"))
        if isinstance(item, dict)
    ]


def _section_id(section: dict[str, Any]) -> str:
    canonical_id = section.get("canonical_id")
    if isinstance(canonical_id, str) and canonical_id:
        return canonical_id
    return f"SECTION_INDEX_{int(section['index']):06d}"


def _normalized_token_text(section: dict[str, Any]) -> str:
    return f"{section.get('canonical_id') or ''} {section.get('title') or ''}".lower()


def _token_matches(text: str, token: str) -> bool:
    token = token.lower()
    if not token:
        return False
    return token in text


def _matching_parent_rule(
    section: dict[str, Any],
    rules: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    text = _normalized_token_text(section)
    for rule in rules:
        tokens = _string_list(rule.get("match_tokens_any"))
        if any(_token_matches(text, token) for token in tokens):
            return rule
    return None


def _group_for_route_class(
    route_class: str,
    rules: Sequence[dict[str, Any]],
    default_group: str,
) -> str:
    for rule in rules:
        if rule.get("route_class") == route_class and rule.get("parent_capability_group_id"):
            return str(rule["parent_capability_group_id"])
    return default_group


def _row_authority_boundary(config: dict[str, Any]) -> dict[str, bool]:
    defaults = config.get("authority_boundary_defaults", {})
    fields = (
        "runtime_authority_created",
        "live_authority_created",
        "source_fact_acceptance_created",
        "connector_semantic_binding_created",
        "replay_paper_result_created",
        "paper_result_created",
        "order_authority_created",
        "profit_evidence_created",
        "latency_superiority_evidence_created",
        "quantum_backend_or_simulator_execution_created",
        "optimizer_runtime_execution_created",
        "market_launch_authority_created",
        "stage2_launch_authority_created",
    )
    return {field: bool(defaults.get(field, False)) for field in fields}


def _semantic_task_ids_for_labels(
    labels: Sequence[str],
    blueprint_by_label: dict[str, dict[str, Any]],
    current_label: str,
    current_semantic_task_id: str,
) -> list[str]:
    values: list[str] = []
    for label in labels:
        if label == current_label:
            values.append(current_semantic_task_id)
            continue
        semantic = blueprint_by_label.get(label, {}).get("semantic_task_id")
        if semantic:
            values.append(str(semantic))
    return sorted(dict.fromkeys(values))


def _controller_refs_for_labels(
    labels: Sequence[str],
    controller_by_label: dict[str, tuple[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for label in labels:
        item = controller_by_label.get(label)
        if item is None:
            continue
        path, entry = item
        refs.append(
            {
                "roadmap_pr_label": label,
                "blueprint_pr_label": entry.get("blueprint_pr_label"),
                "title": entry.get("title"),
                "controller_state": entry.get("controller_state"),
                "next_allowed_action_class": entry.get("next_allowed_action_class"),
                "controller_entry_reference": path,
            }
        )
    return refs


def _market_confidence_for_entry(market: dict[str, Any]) -> str:
    return str(market.get("market_scope_confidence_class") or "OWNER_REVIEW_REQUIRED")


def _market_relevance_class(route_class: str, market_id: str) -> str:
    if market_id == "OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE":
        return "MARKET_RELEVANCE_UNRESOLVED"
    if market_id == "CROSS_MARKET_FOUNDATION":
        return "CROSS_MARKET_FOUNDATION"
    if market_id in {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"}:
        return "DIRECT_VENUE_SECTION"
    if route_class == "SOURCE_EVIDENCE_ROUTE":
        return "SOURCE_EVIDENCE_FOR_MARKET"
    if route_class in {"CONNECTOR_SEMANTIC_ROUTE", "RUNTIME_ROUTE", "RUNTIME_CASH_ROUTE"}:
        return "CONNECTOR_OR_RUNTIME_FOR_MARKET"
    if route_class == "REPLAY_PAPER_ROUTE":
        return "REPLAY_PAPER_OR_LAUNCH_FOR_MARKET"
    if route_class in {
        "QUANTUM_FORWARD_OPTIMIZATION_ROUTE",
        "QUANTUM_BACKEND_ROUTE",
        "OPTIMIZER_ARBITRATION_ROUTE",
    }:
        return "QUANTUM_OR_OPTIMIZER_FOR_MARKET"
    if route_class in {"RISK_ROUTE", "LATENCY_COST_ROUTE"}:
        return "RISK_OR_LATENCY_FOR_MARKET"
    if route_class in {
        "OWNER_ROUTE",
        "GOVERNANCE_ROUTE",
        "DASHBOARD_OWNER_SURFACE_ROUTE",
    }:
        return "OWNER_DASHBOARD_OR_GOVERNANCE_FOR_MARKET"
    if route_class == "RESEARCH_ROUTE":
        return "RESEARCH_SIGNAL_FOR_MARKET"
    return "DIRECT_MARKET_SECTION"


def _market_relevance(
    section: dict[str, Any],
    section_id: str,
    route_class: str,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    text = _normalized_token_text(section)
    taxonomy = [
        item for item in config.get("market_taxonomy", []) if isinstance(item, dict)
    ]
    matches: list[dict[str, Any]] = []
    for market in taxonomy:
        market_id = str(market.get("market_id") or "")
        if market_id == "OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE":
            continue
        tokens = _string_list(market.get("match_tokens"))
        matched_tokens = [token for token in tokens if _token_matches(text, token)]
        if not matched_tokens:
            continue
        matches.append(
            {
                "market_id": market_id,
                "market_relevance_class": _market_relevance_class(route_class, market_id),
                "evidence_basis": (
                    f"exact market token(s) {', '.join(matched_tokens)} in section {section_id}"
                ),
                "confidence_class": _market_confidence_for_entry(market),
                "owner_review_required_flag": False,
                "no_launch_authority_created_flag": True,
            }
        )

    if any(match["market_id"] in {"KALSHI", "POLYMARKET", "FORECASTEX_IBKR"} for match in matches):
        if not any(match["market_id"] == "PREDICTION_MARKETS_GENERAL" for match in matches):
            matches.insert(
                0,
                {
                    "market_id": "PREDICTION_MARKETS_GENERAL",
                    "market_relevance_class": "DIRECT_MARKET_SECTION",
                    "evidence_basis": (
                        f"stage-1 prediction-market venue token in section {section_id}"
                    ),
                    "confidence_class": "EXACT_MASTER_PLAN_MARKET_REFERENCE",
                    "owner_review_required_flag": False,
                    "no_launch_authority_created_flag": True,
                },
            )

    if matches:
        order = {str(market.get("market_id")): index for index, market in enumerate(taxonomy)}
        return sorted(matches, key=lambda item: order.get(item["market_id"], 10**9))

    return [
        {
            "market_id": "OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE",
            "market_relevance_class": "MARKET_RELEVANCE_UNRESOLVED",
            "evidence_basis": (
                f"no exact market token or venue/platform ID found for section {section_id}"
            ),
            "confidence_class": "OWNER_REVIEW_REQUIRED",
            "owner_review_required_flag": True,
            "no_launch_authority_created_flag": True,
        }
    ]


def _build_crosswalk_rows(
    *,
    manifest: dict[str, Any],
    registry: dict[str, Any],
    roadmap_index: dict[str, Any],
    blueprint_index: dict[str, Any],
    controller: dict[str, Any],
) -> list[dict[str, Any]]:
    config = registry["central_config"]
    crosswalk_config = config["roadmap_crosswalk_config"]
    current_label = str(crosswalk_config.get("roadmap_pr_label") or "PR #103")
    current_blueprint_label = str(crosswalk_config.get("blueprint_pr_label") or current_label)
    current_semantic_task_id = str(
        crosswalk_config.get("semantic_task_id")
        or "ROADMAP-MASTER-PLAN-COVERAGE-PARENT-CAPABILITY-CONSOLIDATION"
    )
    rules = _rule_list(config)
    groups = _parent_group_lookup(config)
    default_group = "UNRESOLVED_RESEARCH_DEFAULT"
    exact_routes = {
        str(entry.get("section_id")): entry
        for entry in registry["route_map"].get("route_entries", [])
        if isinstance(entry, dict) and entry.get("section_id")
    }
    roadmap_by_label = _roadmap_index_by_label(roadmap_index)
    blueprint_by_label = _blueprint_index_by_label(blueprint_index)
    controller_labels = _controller_by_label(controller)
    sections = manifest["sections"]
    rows: list[dict[str, Any]] = []

    for zero_index, section in enumerate(sections):
        section_id = _section_id(section)
        next_section = sections[zero_index + 1] if zero_index + 1 < len(sections) else None
        end_line = (
            int(next_section["line"]) - 1
            if isinstance(next_section, dict)
            else int(manifest["line_count"])
        )
        exact_route = exact_routes.get(section_id)
        if exact_route is not None:
            route_class = str(exact_route["current_route_class"])
            route_confidence = "EXACT_PR119_ROUTE_ENTRY"
            parent_group_id = _group_for_route_class(route_class, rules, default_group)
            exact_route_source = f"PR119_EXACT_ROUTE_ENTRY:{section_id}"
            downstream_refs = [str(exact_route.get("downstream_consumer_reference") or "")]
            labels = _labels_from_text(downstream_refs)
            labels.extend(
                _labels_from_text(
                    exact_route.get("quantum_forward_metadata", {}).get(
                        "future_roadmap_consumer_labels"
                    )
                )
            )
            roadmap_labels = _sort_pr_labels(labels or [current_label])
            unresolved_reason = exact_route.get("unresolved_reason_code_when_applicable")
            route_owner_artifacts = [str(exact_route.get("route_owner_artifact") or "")]
            controller_refs = _controller_refs_for_labels(roadmap_labels, controller_labels)
            if exact_route.get("controller_state_reference"):
                controller_refs.append(
                    {
                        "roadmap_pr_label": None,
                        "blueprint_pr_label": None,
                        "title": None,
                        "controller_state": None,
                        "next_allowed_action_class": None,
                        "controller_entry_reference": str(
                            exact_route.get("controller_state_reference")
                        ),
                    }
                )
        else:
            rule = _matching_parent_rule(section, rules)
            if rule is None:
                route_class = "UNRESOLVED_DEFAULT_ROUTE"
                route_confidence = "UNRESOLVED_EXPLICITLY"
                parent_group_id = default_group
                exact_route_source = "UNRESOLVED_DEFAULT_ROUTE:NO_EXACT_ARTIFACT_OWNER_FOUND"
                unresolved_reason = "NO_EXACT_ARTIFACT_OWNER_FOUND"
            else:
                route_class = str(rule.get("route_class") or "UNRESOLVED_DEFAULT_ROUTE")
                parent_group_id = str(rule.get("parent_capability_group_id") or default_group)
                route_confidence = str(
                    rule.get("route_confidence_class")
                    or (
                        "DEFAULT_RESEARCH_ROUTE"
                        if route_class == "RESEARCH_ROUTE"
                        else "PARENT_CAPABILITY_RULE_REFERENCE"
                    )
                )
                exact_route_source = f"PARENT_CAPABILITY_RULE_REFERENCE:{rule.get('rule_id')}"
                unresolved_reason = (
                    "NO_EXACT_ARTIFACT_OWNER_FOUND"
                    if route_class == "UNRESOLVED_DEFAULT_ROUTE"
                    else None
                )
            roadmap_labels = [current_label]
            downstream_refs = [
                f"{current_label} - {crosswalk_config.get('title')}"
            ]
            route_owner_artifacts = [
                "docs/master_plan/completion/QTTSectionCoverageRegistry.yaml",
                "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
                "docs/master_plan/generated/SectionManifest.json",
            ]
            controller_refs = _controller_refs_for_labels(roadmap_labels, controller_labels)

        blueprint_labels = [
            label
            for label in roadmap_labels
            if label == current_blueprint_label or label in blueprint_by_label
        ]
        if current_label in roadmap_labels and current_blueprint_label not in blueprint_labels:
            blueprint_labels.append(current_blueprint_label)
        blueprint_labels = _sort_pr_labels(blueprint_labels)
        semantic_task_ids = _semantic_task_ids_for_labels(
            roadmap_labels,
            blueprint_by_label,
            current_label,
            current_semantic_task_id,
        )
        group = groups.get(parent_group_id, {})
        market_relevance = _market_relevance(section, section_id, route_class, config)
        row = {
            "document_order_index": int(section["index"]),
            "section_id": section_id,
            "normalized_section_title": str(section["title"]),
            "section_manifest_reference": (
                f"docs/master_plan/generated/SectionManifest.json#/sections/{zero_index}"
            ),
            "section_position_source": "tools/master_plan_ingest.py SectionManifest",
            "section_start_line_or_position_if_available": int(section["line"]),
            "section_end_line_or_position_if_available": end_line,
            "parent_capability_group_id": parent_group_id,
            "parent_capability_group_title": str(
                group.get("parent_capability_group_title") or parent_group_id
            ),
            "current_route_class": route_class,
            "route_confidence_class": route_confidence,
            "exact_route_source": exact_route_source,
            "roadmap_pr_labels": roadmap_labels,
            "blueprint_pr_labels": blueprint_labels,
            "semantic_task_ids": semantic_task_ids,
            "controller_state_references": controller_refs,
            "downstream_consumer_references": [
                ref for ref in dict.fromkeys(downstream_refs) if ref
            ],
            "route_owner_artifacts": [
                artifact for artifact in dict.fromkeys(route_owner_artifacts) if artifact
            ],
            "required_validators": [
                "tools/validate_master_plan_section_coverage.py",
                "tools/validate_qtt_master_plan_section_coverage_triage_routes.py",
                "tools/validate_qtt_master_plan_section_roadmap_crosswalk.py",
            ],
            "required_reports": [
                "docs/master_plan/generated/MasterPlanSectionCoverageReport.json"
            ],
            "market_relevance": market_relevance,
            "authority_boundary": _row_authority_boundary(config),
            "unresolved_reason_code_when_applicable": unresolved_reason,
            "owner_review_required_flag": bool(
                unresolved_reason
                or any(item["owner_review_required_flag"] for item in market_relevance)
            ),
            "no_master_plan_text_mutation_flag": True,
            "no_old_coverage_ledger_flag": True,
            "no_runtime_live_order_profit_authority_created_flag": True,
            "no_source_connector_replay_paper_authority_created_flag": True,
            "no_quantum_backend_or_simulator_execution_created_flag": True,
            "no_market_launch_authority_created_flag": True,
        }
        if section_id in roadmap_by_label:
            row["roadmap_index_reference"] = roadmap_by_label[section_id]
        rows.append(row)
    return rows


def _count_list_values(rows: Sequence[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for value in row.get(field, []):
            counts[str(value)] += 1
    return dict(sorted(counts.items(), key=lambda item: _sort_pr_labels([item[0]])[0]))


def _controller_state_counts(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for ref in row.get("controller_state_references", []):
            state = ref.get("controller_state") if isinstance(ref, dict) else None
            if state:
                counts[str(state)] += 1
    return dict(sorted(counts.items()))


def _crosswalk_summary(
    *,
    rows: Sequence[dict[str, Any]],
    manifest: dict[str, Any],
    config: dict[str, Any],
    roster: dict[str, Any],
) -> dict[str, Any]:
    section_ids = [_section_id(section) for section in manifest["sections"]]
    row_ids = [str(row["section_id"]) for row in rows]
    duplicates = sorted(
        section_id for section_id, count in Counter(row_ids).items() if count > 1
    )
    missing = sorted(set(section_ids) - set(row_ids))
    route_classes = [str(row["current_route_class"]) for row in rows]
    route_confidences = [str(row["route_confidence_class"]) for row in rows]
    parent_groups = [str(row["parent_capability_group_id"]) for row in rows]
    pr119 = _roster_entry(
        [entry for entry in roster.get("entries", []) if isinstance(entry, dict)],
        "PR119",
    )
    crosswalk_config = config["roadmap_crosswalk_config"]
    pr119_evidence = dict(
        _dict_value(crosswalk_config.get("pr119_github_audit_currentization_evidence"))
    )
    pr119_evidence.update(
        {
            "roster_github_pr_number": pr119.get("github_pr_number"),
            "roster_github_audit_url": pr119.get("github_audit_url"),
            "roster_github_title": pr119.get("github_title"),
            "roster_current_status": pr119.get("current_status"),
            "roster_branch_name": pr119.get("branch_name"),
            "roster_same_number_mismatch_recorded": pr119.get(
                "same_number_mismatch_recorded"
            ),
        }
    )
    return {
        "repo_canonical_pr_label": crosswalk_config.get("repo_canonical_pr_label"),
        "roadmap_pr_label": crosswalk_config.get("roadmap_pr_label"),
        "blueprint_pr_label": crosswalk_config.get("blueprint_pr_label"),
        "semantic_task_id": crosswalk_config.get("semantic_task_id"),
        "title": crosswalk_config.get("title"),
        "pr119_github_audit_currentization_evidence": pr119_evidence,
        "controller_decision_reference": crosswalk_config.get(
            "controller_decision_reference"
        ),
        "artifact_family_decision": crosswalk_config.get("artifact_family_decision"),
        "section_manifest_parser_visible_section_count": int(
            manifest["section_count"]
        ),
        "all_section_crosswalk_row_count": len(rows),
        "missing_section_count": len(missing),
        "duplicate_section_count": len(duplicates),
        "missing_section_ids": missing,
        "duplicate_section_ids": duplicates,
        "ordering_matches_section_manifest": row_ids == section_ids,
        "route_class_counts": _count_by(
            route_classes, config.get("route_class_enum", ROUTE_CLASSES)
        ),
        "route_confidence_counts": _count_by(
            route_confidences,
            config.get("route_confidence_class_enum", ROUTE_CONFIDENCE_CLASSES),
        ),
        "parent_capability_group_counts": _count_by(
            parent_groups,
            [
                str(group.get("parent_capability_group_id"))
                for group in config.get("parent_capability_group_enum", [])
                if isinstance(group, dict)
            ],
        ),
        "roadmap_pr_label_coverage_counts": _count_list_values(
            rows, "roadmap_pr_labels"
        ),
        "blueprint_pr_label_coverage_counts": _count_list_values(
            rows, "blueprint_pr_labels"
        ),
        "controller_state_coverage_counts": _controller_state_counts(rows),
        "unresolved_default_count": route_classes.count("UNRESOLVED_DEFAULT_ROUTE"),
        "quantum_route_count": route_classes.count(
            "QUANTUM_FORWARD_OPTIMIZATION_ROUTE"
        )
        + route_classes.count("QUANTUM_BACKEND_ROUTE"),
        "optimizer_route_count": route_classes.count("OPTIMIZER_ARBITRATION_ROUTE"),
        "latency_route_count": route_classes.count("LATENCY_COST_ROUTE"),
        "source_evidence_route_count": route_classes.count("SOURCE_EVIDENCE_ROUTE"),
        "connector_route_count": route_classes.count("CONNECTOR_SEMANTIC_ROUTE"),
        "runtime_route_count": route_classes.count("RUNTIME_ROUTE")
        + route_classes.count("RUNTIME_CASH_ROUTE"),
        "replay_paper_route_count": route_classes.count("REPLAY_PAPER_ROUTE"),
        "owner_governance_route_count": route_classes.count("OWNER_ROUTE")
        + route_classes.count("GOVERNANCE_ROUTE")
        + route_classes.count("DASHBOARD_OWNER_SURFACE_ROUTE"),
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
        "market_launch_authority_created": False,
        "deterministic_output": True,
    }


def _rule_by_route_class(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(rule.get("route_class")): rule
        for rule in config.get("route_class_to_command_family_rules", [])
        if isinstance(rule, dict) and rule.get("route_class")
    }


def _parent_command_overrides(config: dict[str, Any]) -> dict[str, str]:
    return {
        str(rule.get("parent_capability_group_id")): str(rule.get("command_family"))
        for rule in config.get("parent_capability_to_command_family_rules", [])
        if isinstance(rule, dict)
        and rule.get("parent_capability_group_id")
        and rule.get("command_family")
    }


def _stage1_market_ids(config: dict[str, Any]) -> list[str]:
    rules = config.get("stage1_prediction_market_only_rules", {})
    ids = _string_list(_dict_value(rules).get("stage1_active_market_ids"))
    return ids or [
        "PREDICTION_MARKETS_GENERAL",
        "KALSHI",
        "POLYMARKET",
        "FORECASTEX_IBKR",
    ]


def _future_market_family_tokens() -> dict[str, tuple[str, ...]]:
    return {
        "STOCKS": ("stock", "stocks"),
        "CRYPTOCURRENCY": ("cryptocurrency", "crypto", "bitcoin", "ethereum"),
        "FUTURES": ("futures",),
        "OPTIONS": ("options",),
        "EQUITIES": ("equity", "equities"),
        "ETFS": ("etf", "etfs"),
        "FX": ("fx", "foreign exchange"),
        "COMMODITIES": ("commodity", "commodities"),
    }


def _explicit_future_market_families(
    row: dict[str, Any],
    config: dict[str, Any],
) -> list[str]:
    allowed = set(
        config.get(
            "explicit_future_market_candidate_family_enum",
            EXPLICIT_FUTURE_MARKET_CANDIDATE_FAMILIES,
        )
    )
    text = str(row.get("normalized_section_title") or "").lower()
    matches: list[str] = []
    for family, tokens in _future_market_family_tokens().items():
        if family not in allowed:
            continue
        if any(_token_matches(text, token) for token in tokens):
            matches.append(family)
    return [family for family in EXPLICIT_FUTURE_MARKET_CANDIDATE_FAMILIES if family in matches]


def _is_market_related_without_known_scope(
    row: dict[str, Any],
    *,
    stage1_market_ids: set[str],
    explicit_families: Sequence[str],
) -> bool:
    if explicit_families:
        return False
    market_ids = {
        str(item.get("market_id"))
        for item in row.get("market_relevance", [])
        if isinstance(item, dict) and item.get("market_id")
    }
    if market_ids & stage1_market_ids:
        return False
    if market_ids - {"OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE"}:
        return False
    title = str(row.get("normalized_section_title") or "").lower()
    market_tokens = (
        "market",
        "venue",
        "exchange",
        "broker",
        "orderbook",
        "liquidity",
        "contract",
    )
    return any(_token_matches(title, token) for token in market_tokens)


def _command_profile_for_family(command_family: str) -> dict[str, str]:
    profiles = {
        "COMMAND_MATRIX_COMMAND": (
            "STATIC_CONTROL_PLANE_ONLY",
            "NO_EXECUTION_AUTHORITY",
            "CODEX_STATIC_BUILDER",
            "VALIDATION_REPORT_CONSUMER",
        ),
        "ATOMICROWS_INVENTORY_COMMAND": (
            "STATIC_INDEX_ONLY",
            "NO_EXECUTION_AUTHORITY",
            "CODEX_STATIC_BUILDER",
            "STATIC_ROADMAP_BLUEPRINT_CONSUMER",
        ),
        "EDGE_SELECTION_SCORING_COMMAND": (
            "STATIC_REPORTING_ONLY",
            "NO_EXECUTION_AUTHORITY",
            "CODEX_STATIC_BUILDER",
            "STATIC_ROADMAP_BLUEPRINT_CONSUMER",
        ),
        "ORDER_INTENT_GATED_COMMAND": (
            "FUTURE_RUNTIME_GATED",
            "NO_ORDER_AUTHORITY",
            "RISK_AGENT_FUTURE",
            "FUTURE_ORDER_INTENT_CONSUMER",
        ),
        "LIVE_LAUNCH_GATED_COMMAND": (
            "FUTURE_LIVE_LAUNCH_GATED",
            "NO_LIVE_AUTHORITY",
            "RISK_AGENT_FUTURE",
            "FUTURE_LIVE_LAUNCH_CONSUMER",
        ),
        "FUTURE_MARKET_DEFERRED_COMMAND": (
            "FUTURE_MARKET_EXPANSION_GATED",
            "NO_MARKET_LAUNCH_AUTHORITY",
            "MARKET_EXPANSION_AGENT_FUTURE",
            "FUTURE_MARKET_EXPANSION_CONSUMER",
        ),
        "MARKET_INDEX_COMMAND": (
            "STATIC_INDEX_ONLY",
            "NO_MARKET_LAUNCH_AUTHORITY",
            "CODEX_STATIC_BUILDER",
            "STATIC_ROADMAP_BLUEPRINT_CONSUMER",
        ),
    }
    scope, authority, owner, consumer = profiles.get(
        command_family,
        (
            "STATIC_CONTROL_PLANE_ONLY",
            "NO_EXECUTION_AUTHORITY",
            "CODEX_STATIC_BUILDER",
            "STATIC_ROADMAP_BLUEPRINT_CONSUMER",
        ),
    )
    return {
        "command_scope_class": scope,
        "command_authority_class": authority,
        "command_owner_class": owner,
        "command_consumer_class": consumer,
    }


def _future_operations_for_command(command_family: str) -> list[str]:
    mapping = {
        "SOURCE_EVIDENCE_COMMAND": [
            "FUTURE_SOURCE_RETRIEVAL",
            "FUTURE_SOURCE_ACCEPTANCE",
        ],
        "CONNECTOR_SEMANTIC_COMMAND": ["FUTURE_CONNECTOR_BINDING"],
        "RUNTIME_RESOLVER_COMMAND": ["FUTURE_RUNTIME_SNAPSHOT"],
        "RUNTIME_CASH_COMMAND": [
            "FUTURE_RUNTIME_SNAPSHOT",
            "FUTURE_RUNTIME_CASH_RECEIPT",
        ],
        "REPLAY_PAPER_COMMAND": [
            "FUTURE_REPLAY_EXECUTION",
            "FUTURE_PAPER_EXECUTION",
        ],
        "OWNER_REVIEW_COMMAND": ["FUTURE_OWNER_REVIEW_RECEIPT"],
        "DASHBOARD_OWNER_SURFACE_COMMAND": ["FUTURE_OWNER_REVIEW_RECEIPT"],
        "LIVE_LAUNCH_GATED_COMMAND": ["FUTURE_LIVE_CANARY"],
        "ORDER_INTENT_GATED_COMMAND": [
            "FUTURE_ORDER_INTENT",
            "FUTURE_ORDER_EXECUTION",
        ],
        "QUANTUM_FORWARD_OPTIMIZATION_COMMAND": [
            "FUTURE_QUANTUM_BACKEND_RECEIPT",
            "FUTURE_OPTIMIZER_EXECUTION",
        ],
        "QUANTUM_BACKEND_GATED_COMMAND": ["FUTURE_QUANTUM_BACKEND_RECEIPT"],
        "FUTURE_MARKET_DEFERRED_COMMAND": [
            "FUTURE_MARKET_EXPANSION",
            "FUTURE_STAGE2_MARKET_SELECTION",
        ],
    }
    return list(mapping.get(command_family, []))


def _block_reasons_for_command(
    command_family: str,
    *,
    unresolved_reason: Any,
    owner_review_future_market_scope: bool,
) -> list[str]:
    reasons = [
        "STATIC_CONTROL_PLANE_ONLY",
        "MASTER_PLAN_TEXT_MUTATION_FORBIDDEN",
        "OLD_COVERAGE_LEDGER_FORBIDDEN",
        "IMPLEMENTATION_COMPLETION_NOT_CLAIMED",
        "LAUNCH_READINESS_NOT_CLAIMED",
    ]
    by_family = {
        "SOURCE_EVIDENCE_COMMAND": [
            "FUTURE_SOURCE_RETRIEVAL_REQUIRES_PR105",
            "SOURCE_FACT_ACCEPTANCE_NOT_CREATED",
        ],
        "CONNECTOR_SEMANTIC_COMMAND": ["CONNECTOR_BINDING_REQUIRES_FUTURE_PR"],
        "RUNTIME_RESOLVER_COMMAND": ["RUNTIME_AUTHORITY_REQUIRES_FUTURE_PR"],
        "RUNTIME_CASH_COMMAND": [
            "RUNTIME_AUTHORITY_REQUIRES_FUTURE_PR",
            "RUNTIME_CASH_RECEIPT_REQUIRES_FUTURE_PR",
        ],
        "REPLAY_PAPER_COMMAND": ["REPLAY_PAPER_RESULT_REQUIRES_FUTURE_PR"],
        "ORDER_INTENT_GATED_COMMAND": ["ORDER_AUTHORITY_REQUIRES_FUTURE_PR"],
        "LIVE_LAUNCH_GATED_COMMAND": ["LIVE_AUTHORITY_REQUIRES_OWNER_APPROVAL"],
        "OWNER_REVIEW_COMMAND": ["LIVE_AUTHORITY_REQUIRES_OWNER_APPROVAL"],
        "DASHBOARD_OWNER_SURFACE_COMMAND": ["LIVE_AUTHORITY_REQUIRES_OWNER_APPROVAL"],
        "LATENCY_COST_COMMAND": [
            "PROFIT_EVIDENCE_NOT_CREATED",
            "LATENCY_SUPERIORITY_EVIDENCE_NOT_CREATED",
        ],
        "QUANTUM_FORWARD_OPTIMIZATION_COMMAND": [
            "QUANTUM_BACKEND_EXECUTION_REQUIRES_FUTURE_CONTROLLER_STATE",
            "QUANTUM_SIMULATOR_EXECUTION_NOT_CREATED",
            "OPTIMIZER_RUNTIME_EXECUTION_NOT_CREATED",
        ],
        "QUANTUM_BACKEND_GATED_COMMAND": [
            "QUANTUM_BACKEND_EXECUTION_REQUIRES_FUTURE_CONTROLLER_STATE",
            "QUANTUM_SIMULATOR_EXECUTION_NOT_CREATED",
        ],
        "FUTURE_MARKET_DEFERRED_COMMAND": [
            "MARKET_LAUNCH_AUTHORITY_NOT_CREATED",
            "STAGE2_MARKET_SELECTION_NOT_CREATED",
            "FUTURE_MARKET_SCOPE_DEFERRED",
        ],
        "MARKET_INDEX_COMMAND": [
            "MARKET_LAUNCH_AUTHORITY_NOT_CREATED",
            "STAGE2_MARKET_SELECTION_NOT_CREATED",
        ],
    }
    reasons.extend(by_family.get(command_family, []))
    if unresolved_reason:
        reasons.append("NO_EXACT_ARTIFACT_OWNER_FOUND")
    if owner_review_future_market_scope:
        reasons.append("OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE")
        reasons.append("NO_OPEN_ENDED_MARKET_TAXONOMY_ALLOWED")
    return [reason for reason in dict.fromkeys(reasons)]


def _command_status(
    command_family: str,
    command_scope_class: str,
    owner_review_required: bool,
) -> str:
    if command_family == "UNRESOLVED_RESEARCH_COMMAND":
        return "UNRESOLVED_COMMAND_INTENT_RECORDED"
    if command_family == "FUTURE_MARKET_DEFERRED_COMMAND":
        return "DEFERRED_FUTURE_MARKET_COMMAND_INTENT_RECORDED"
    if owner_review_required:
        return "OWNER_REVIEW_REQUIRED_COMMAND_INTENT_RECORDED"
    if command_scope_class.startswith("FUTURE_"):
        return "FUTURE_GATED_COMMAND_INTENT_RECORDED"
    return "STATIC_COMMAND_INTENT_RECORDED"


def _quantum_command_relevance(row: dict[str, Any], command_family: str) -> str:
    route_class = str(row.get("current_route_class") or "")
    title = str(row.get("normalized_section_title") or "").lower()
    if route_class == "QUANTUM_BACKEND_ROUTE":
        return "TRUE_QUANTUM_BACKEND_FUTURE_GATED"
    if route_class == "OPTIMIZER_ARBITRATION_ROUTE":
        return "HYBRID_CLASSICAL_QUANTUM_ARBITRATION_FUTURE_GATED"
    if "portfolio" in title or "candidate-set" in title or "candidate set" in title:
        return "PORTFOLIO_CANDIDATE_SET_OPTIMIZATION_FUTURE_GATED"
    if "qubo" in title or "ising" in title:
        return "QUBO_ISING_FORMULATION_FUTURE_GATED"
    if "qaoa" in title or "vqe" in title or "anneal" in title:
        return "QAOA_VQE_ANNEALING_FUTURE_GATED"
    if route_class == "QUANTUM_FORWARD_OPTIMIZATION_ROUTE":
        return "QUANTUM_APPLICABILITY_METADATA_ONLY"
    if command_family == "QUANTUM_POLICY_COMMAND":
        return "QUANTUM_POLICY_METADATA_ONLY"
    if "quantum" in title:
        return "QUANTUM_APPLICABILITY_METADATA_ONLY"
    if route_class == "LATENCY_COST_ROUTE" and "quantum" in title:
        return "LATENCY_AWARE_QUANTUM_PATH_FUTURE_GATED"
    return "NONE"


def _quantum_command_metadata(
    row: dict[str, Any],
    command_family: str,
    future_labels: Sequence[str],
    controller_reference: str,
) -> dict[str, Any]:
    return {
        "quantum_command_relevance_class": _quantum_command_relevance(
            row, command_family
        ),
        "future_controller_reference": controller_reference,
        "future_roadmap_consumer_labels": list(future_labels),
        "no_backend_execution_flag": True,
        "no_simulator_execution_flag": True,
        "no_optimizer_runtime_execution_flag": True,
        "no_quantum_advantage_claim_flag": True,
        "no_profit_or_latency_superiority_claim_flag": True,
    }


def _latency_command_metadata(row: dict[str, Any], command_family: str) -> dict[str, Any]:
    relevance = (
        "LATENCY_COST_METADATA_ONLY"
        if str(row.get("current_route_class")) == "LATENCY_COST_ROUTE"
        or command_family == "LATENCY_COST_COMMAND"
        else "NONE"
    )
    return {
        "latency_command_relevance_class": relevance,
        "no_latency_superiority_claim_flag": True,
        "no_profit_or_latency_superiority_claim_flag": True,
    }


def _source_runtime_command_metadata(command_family: str) -> dict[str, Any]:
    classes: list[str] = []
    if command_family == "SOURCE_EVIDENCE_COMMAND":
        classes.append("SOURCE_EVIDENCE_FUTURE_GATED")
    if command_family == "CONNECTOR_SEMANTIC_COMMAND":
        classes.append("CONNECTOR_SEMANTIC_FUTURE_GATED")
    if command_family in {"RUNTIME_RESOLVER_COMMAND", "RUNTIME_CASH_COMMAND"}:
        classes.append("RUNTIME_FUTURE_GATED")
    if command_family == "REPLAY_PAPER_COMMAND":
        classes.append("REPLAY_PAPER_FUTURE_GATED")
    if command_family in {"LIVE_LAUNCH_GATED_COMMAND", "ORDER_INTENT_GATED_COMMAND"}:
        classes.append("LIVE_ORDER_FUTURE_GATED")
    return {
        "source_connector_runtime_relevance_classes": classes or ["NONE"],
        "no_source_retrieval_flag": True,
        "no_source_fact_acceptance_flag": True,
        "no_connector_semantic_binding_flag": True,
        "no_runtime_authority_flag": True,
        "no_replay_paper_result_flag": True,
        "no_live_or_order_authority_flag": True,
    }


def _command_matrix_row(
    row: dict[str, Any],
    *,
    zero_index: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    route_rules = _rule_by_route_class(config)
    parent_overrides = _parent_command_overrides(config)
    route_class = str(row.get("current_route_class") or "")
    rule = route_rules.get(route_class, {})
    command_family = str(rule.get("command_family") or "UNRESOLVED_RESEARCH_COMMAND")
    if route_class != "UNRESOLVED_DEFAULT_ROUTE":
        command_family = parent_overrides.get(
            str(row.get("parent_capability_group_id") or ""), command_family
        )

    stage1_ids = set(_stage1_market_ids(config))
    market_ids = [
        str(item.get("market_id"))
        for item in row.get("market_relevance", [])
        if isinstance(item, dict) and item.get("market_id")
    ]
    stage1_market_ids = [market_id for market_id in _stage1_market_ids(config) if market_id in market_ids]
    explicit_families = _explicit_future_market_families(row, config)
    owner_review_future_market_scope = _is_market_related_without_known_scope(
        row,
        stage1_market_ids=stage1_ids,
        explicit_families=explicit_families,
    )
    if explicit_families:
        command_family = "FUTURE_MARKET_DEFERRED_COMMAND"
    elif route_class == "CROSS_MARKET_ROUTE":
        command_family = "MARKET_INDEX_COMMAND"
    elif owner_review_future_market_scope and command_family not in {
        "MARKET_INDEX_COMMAND",
        "FUTURE_MARKET_DEFERRED_COMMAND",
    }:
        command_family = "UNRESOLVED_RESEARCH_COMMAND"

    profile = dict(rule)
    if command_family != rule.get("command_family"):
        profile.update(_command_profile_for_family(command_family))
    command_scope_class = str(
        profile.get("command_scope_class") or "STATIC_CONTROL_PLANE_ONLY"
    )
    command_authority_class = str(
        profile.get("command_authority_class") or "NO_EXECUTION_AUTHORITY"
    )
    command_owner_class = str(profile.get("command_owner_class") or "CODEX_STATIC_BUILDER")
    command_consumer_class = str(
        profile.get("command_consumer_class") or "STATIC_ROADMAP_BLUEPRINT_CONSUMER"
    )

    future_labels = _sort_pr_labels(
        set(_string_list(row.get("roadmap_pr_labels")))
        | set(_string_list(row.get("blueprint_pr_labels")))
        | {"PR #104"}
    )
    roadmap_labels = _sort_pr_labels(set(_string_list(row.get("roadmap_pr_labels"))) | {"PR #104"})
    blueprint_labels = _sort_pr_labels(set(_string_list(row.get("blueprint_pr_labels"))) | {"PR #104"})
    controller_refs = list(row.get("controller_state_references", []))
    controller_reference = str(
        config.get("command_matrix_config", {}).get("controller_decision_reference")
        or "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json#/roadmap_range_currentization/3"
    )
    if not any(
        isinstance(item, dict)
        and item.get("controller_entry_reference") == controller_reference
        for item in controller_refs
    ):
        controller_refs.append(
            {
                "roadmap_pr_label": "PR #104",
                "blueprint_pr_label": "PR #104",
                "title": "Master-plan section coverage command matrix",
                "controller_state": "CONTROL_PLANE_STATE_REFERENCED_BY_CONTROLLER",
                "next_allowed_action_class": "FUTURE_REPO_PR_REQUIRED_BEFORE_MATERIALIZATION",
                "controller_entry_reference": controller_reference,
            }
        )

    static_ops = [
        "READ_CROSSWALK",
        "READ_ROUTE_MAP",
        "GENERATE_STATIC_REPORT",
        "RUN_STATIC_VALIDATOR",
        "REFERENCE_CONTROLLER_STATE",
        "REFERENCE_ROADMAP_BLUEPRINT",
    ]
    if stage1_market_ids or explicit_families or owner_review_future_market_scope:
        static_ops.append("READ_MARKET_INDEX")
    unresolved_reason = row.get("unresolved_reason_code_when_applicable")
    owner_review_required = bool(
        row.get("owner_review_required_flag")
        or owner_review_future_market_scope
        or command_family == "UNRESOLVED_RESEARCH_COMMAND"
    )
    if owner_review_required:
        static_ops.extend(["CLASSIFY_UNRESOLVED", "QUEUE_OWNER_REVIEW"])
    static_ops = [operation for operation in STATIC_ALLOWED_OPERATIONS if operation in set(static_ops)]
    future_ops = _future_operations_for_command(command_family)
    block_reasons = _block_reasons_for_command(
        command_family,
        unresolved_reason=unresolved_reason,
        owner_review_future_market_scope=owner_review_future_market_scope,
    )

    return {
        "document_order_index": int(row["document_order_index"]),
        "section_id": str(row["section_id"]),
        "crosswalk_reference": {
            "report_path": "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
            "json_pointer": f"#/roadmap_crosswalk/rows/{zero_index}",
            "section_id": str(row["section_id"]),
            "document_order_index": int(row["document_order_index"]),
        },
        "parent_capability_group_id": str(row.get("parent_capability_group_id") or ""),
        "current_route_class": route_class,
        "command_family": command_family,
        "command_scope_class": command_scope_class,
        "command_authority_class": command_authority_class,
        "command_owner_class": command_owner_class,
        "command_consumer_class": command_consumer_class,
        "command_status": _command_status(
            command_family, command_scope_class, owner_review_required
        ),
        "static_allowed_now_operations": static_ops,
        "future_gated_operations": future_ops,
        "block_reason_codes": block_reasons,
        "future_pr_labels": future_labels,
        "roadmap_pr_labels": roadmap_labels,
        "blueprint_pr_labels": blueprint_labels,
        "controller_state_references": controller_refs,
        "required_validators": [
            "tools/validate_master_plan_section_coverage.py",
            "tools/validate_qtt_master_plan_section_coverage_triage_routes.py",
            "tools/validate_qtt_master_plan_section_roadmap_crosswalk.py",
            "tools/validate_qtt_master_plan_section_coverage_command_matrix.py",
        ],
        "required_reports": [
            "docs/master_plan/generated/MasterPlanSectionCoverageReport.json"
        ],
        "required_artifacts": [
            "docs/master_plan/completion/QTTSectionCoverageRegistry.yaml",
            "schemas/master_plan/master_plan_section_coverage_report.schema.json",
            "tools/build_master_plan_section_coverage_report.py",
            "tools/validate_master_plan_section_coverage.py",
        ],
        "market_scope_summary": {
            "market_ids": market_ids,
            "stage1_active_market_ids": stage1_market_ids,
            "explicit_future_market_candidate_families": explicit_families,
            "owner_review_future_market_scope_classification": (
                "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE"
                if owner_review_future_market_scope
                else None
            ),
            "forbidden_market_taxonomy_values_detected": [],
            "no_market_launch_authority_created_flag": True,
            "no_stage2_market_selection_created_flag": True,
        },
        "stage1_prediction_market_relevance": (
            "STAGE1_PREDICTION_MARKET_RELEVANT"
            if stage1_market_ids
            else "NOT_STAGE1_PREDICTION_MARKET_RELEVANT"
        ),
        "future_market_relevance": (
            "FUTURE_MARKET_PLANNING_DEFERRED"
            if explicit_families
            else (
                "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE"
                if owner_review_future_market_scope
                else "NOT_FUTURE_MARKET_RELEVANT"
            )
        ),
        "explicit_future_market_candidate_family_when_applicable": explicit_families,
        "owner_review_future_market_scope_classification_when_applicable": (
            "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE"
            if owner_review_future_market_scope
            else None
        ),
        "quantum_forward_command_metadata": _quantum_command_metadata(
            row, command_family, future_labels, controller_reference
        ),
        "latency_command_metadata": _latency_command_metadata(row, command_family),
        "source_connector_runtime_command_metadata": _source_runtime_command_metadata(
            command_family
        ),
        "owner_review_required_flag": owner_review_required,
        "unresolved_reason_code_when_applicable": unresolved_reason,
        "no_command_execution_flag": True,
        "no_runtime_live_order_profit_authority_created_flag": True,
        "no_source_connector_replay_paper_authority_created_flag": True,
        "no_quantum_backend_or_simulator_execution_created_flag": True,
        "no_market_launch_authority_created_flag": True,
        "no_open_ended_future_market_taxonomy_flag": True,
        "no_master_plan_text_mutation_flag": True,
        "no_old_coverage_ledger_flag": True,
    }


def _build_command_matrix_rows(
    rows: Sequence[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _command_matrix_row(row, zero_index=index, config=config)
        for index, row in enumerate(rows)
    ]


def _command_matrix_summary(
    *,
    command_rows: Sequence[dict[str, Any]],
    crosswalk_rows: Sequence[dict[str, Any]],
    manifest: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    section_ids = [_section_id(section) for section in manifest["sections"]]
    row_ids = [str(row["section_id"]) for row in command_rows]
    duplicates = sorted(
        section_id for section_id, count in Counter(row_ids).items() if count > 1
    )
    missing = sorted(set(section_ids) - set(row_ids))
    command_families = [str(row["command_family"]) for row in command_rows]
    command_scopes = [str(row["command_scope_class"]) for row in command_rows]
    command_authorities = [str(row["command_authority_class"]) for row in command_rows]
    command_owners = [str(row["command_owner_class"]) for row in command_rows]
    stage1_ids = _stage1_market_ids(config)
    stage1_counts = {
        market_id: sum(
            market_id
            in row.get("market_scope_summary", {}).get("stage1_active_market_ids", [])
            for row in command_rows
        )
        for market_id in stage1_ids
    }
    future_family_counts = {
        family: sum(
            family
            in row.get(
                "explicit_future_market_candidate_family_when_applicable", []
            )
            for row in command_rows
        )
        for family in config.get(
            "explicit_future_market_candidate_family_enum",
            EXPLICIT_FUTURE_MARKET_CANDIDATE_FAMILIES,
        )
    }
    forbidden_count = sum(
        len(
            row.get("market_scope_summary", {}).get(
                "forbidden_market_taxonomy_values_detected", []
            )
        )
        for row in command_rows
    )
    quantum_rows = [
        row
        for row in command_rows
        if row["quantum_forward_command_metadata"][
            "quantum_command_relevance_class"
        ]
        != "NONE"
    ]
    optimizer_count = sum(
        "FUTURE_OPTIMIZER_EXECUTION" in row.get("future_gated_operations", [])
        or "OPTIMIZER" in row["quantum_forward_command_metadata"][
            "quantum_command_relevance_class"
        ]
        or "ARBITRATION" in row["quantum_forward_command_metadata"][
            "quantum_command_relevance_class"
        ]
        for row in command_rows
    )
    latency_count = sum(
        row["latency_command_metadata"]["latency_command_relevance_class"] != "NONE"
        for row in command_rows
    )
    return {
        "repo_canonical_pr_label": config["command_matrix_config"].get(
            "repo_canonical_pr_label"
        ),
        "roadmap_pr_label": config["command_matrix_config"].get("roadmap_pr_label"),
        "blueprint_pr_label": config["command_matrix_config"].get(
            "blueprint_pr_label"
        ),
        "semantic_task_id": config["command_matrix_config"].get("semantic_task_id"),
        "title": config["command_matrix_config"].get("title"),
        "pr120_github_audit_currentization_evidence": config[
            "command_matrix_config"
        ].get("pr120_github_audit_currentization_evidence", {}),
        "controller_decision_reference": config["command_matrix_config"].get(
            "controller_decision_reference"
        ),
        "blueprint_decision_reference": config["command_matrix_config"].get(
            "blueprint_decision_reference"
        ),
        "artifact_family_decision": config["command_matrix_config"].get(
            "artifact_family_decision"
        ),
        "compact_normalized_command_matrix_flag": bool(
            config["command_matrix_config"].get(
                "compact_normalized_command_matrix_flag"
            )
        ),
        "section_manifest_parser_visible_section_count": int(
            manifest["section_count"]
        ),
        "pr120_crosswalk_row_count": len(crosswalk_rows),
        "command_matrix_row_count": len(command_rows),
        "missing_section_count": len(missing),
        "duplicate_section_count": len(duplicates),
        "missing_section_ids": missing,
        "duplicate_section_ids": duplicates,
        "ordering_matches_crosswalk_document_order": row_ids
        == [str(row["section_id"]) for row in crosswalk_rows]
        == section_ids,
        "command_family_counts": _count_by(
            command_families, config.get("command_family_enum", COMMAND_FAMILIES)
        ),
        "command_scope_class_counts": _count_by(
            command_scopes,
            config.get("command_scope_class_enum", COMMAND_SCOPE_CLASSES),
        ),
        "command_authority_class_counts": _count_by(
            command_authorities,
            config.get(
                "command_authority_class_enum", COMMAND_AUTHORITY_CLASSES
            ),
        ),
        "command_owner_class_counts": _count_by(
            command_owners,
            config.get("command_owner_class_enum", COMMAND_OWNER_CLASSES),
        ),
        "static_allowed_now_operation_counts": _count_list_values(
            command_rows, "static_allowed_now_operations"
        ),
        "future_gated_operation_counts": _count_list_values(
            command_rows, "future_gated_operations"
        ),
        "route_class_counts": _count_by(
            [str(row["current_route_class"]) for row in command_rows],
            config.get("route_class_enum", ROUTE_CLASSES),
        ),
        "parent_capability_group_counts": _count_by(
            [str(row["parent_capability_group_id"]) for row in command_rows],
            [
                str(group.get("parent_capability_group_id"))
                for group in config.get("parent_capability_group_enum", [])
                if isinstance(group, dict)
            ],
        ),
        "roadmap_pr_label_consumer_counts": _count_list_values(
            command_rows, "roadmap_pr_labels"
        ),
        "blueprint_pr_label_consumer_counts": _count_list_values(
            command_rows, "blueprint_pr_labels"
        ),
        "controller_state_consumer_counts": _controller_state_counts(command_rows),
        "unresolved_command_count": command_families.count(
            "UNRESOLVED_RESEARCH_COMMAND"
        ),
        "owner_review_required_command_count": sum(
            bool(row.get("owner_review_required_flag")) for row in command_rows
        ),
        "stage1_prediction_market_command_count": sum(
            bool(
                row.get("market_scope_summary", {}).get("stage1_active_market_ids")
            )
            for row in command_rows
        ),
        "stage1_prediction_market_command_counts": stage1_counts,
        "future_market_deferred_command_count": command_families.count(
            "FUTURE_MARKET_DEFERRED_COMMAND"
        ),
        "explicit_future_market_family_command_counts": future_family_counts,
        "owner_review_required_future_market_scope_count": sum(
            row.get(
                "owner_review_future_market_scope_classification_when_applicable"
            )
            == "OWNER_REVIEW_REQUIRED_FUTURE_MARKET_SCOPE"
            for row in command_rows
        ),
        "forbidden_market_taxonomy_value_count": forbidden_count,
        "kalshi_command_count": stage1_counts.get("KALSHI", 0),
        "polymarket_command_count": stage1_counts.get("POLYMARKET", 0),
        "forecastex_ibkr_command_count": stage1_counts.get("FORECASTEX_IBKR", 0),
        "prediction_markets_general_command_count": stage1_counts.get(
            "PREDICTION_MARKETS_GENERAL", 0
        ),
        "quantum_command_count": len(quantum_rows),
        "optimizer_command_count": optimizer_count,
        "latency_command_count": latency_count,
        "source_evidence_command_count": command_families.count(
            "SOURCE_EVIDENCE_COMMAND"
        ),
        "connector_command_count": command_families.count(
            "CONNECTOR_SEMANTIC_COMMAND"
        ),
        "runtime_command_count": command_families.count(
            "RUNTIME_RESOLVER_COMMAND"
        )
        + command_families.count("RUNTIME_CASH_COMMAND"),
        "replay_paper_command_count": command_families.count("REPLAY_PAPER_COMMAND"),
        "owner_governance_command_count": command_families.count(
            "OWNER_REVIEW_COMMAND"
        )
        + command_families.count("DASHBOARD_OWNER_SURFACE_COMMAND")
        + command_families.count("RISK_SAFETY_COMMAND"),
        "old_coverage_ledger_reintroduction_flag": False,
        "master_plan_mutation_count": 0,
        "runtime_authority_created": False,
        "live_authority_created": False,
        "source_retrieval_created": False,
        "source_fact_acceptance_created": False,
        "connector_semantic_binding_created": False,
        "replay_paper_result_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "latency_superiority_evidence_created": False,
        "quantum_backend_simulator_optimizer_execution_created": False,
        "market_launch_authority_created": False,
        "stage2_market_selection_created": False,
        "deterministic_output": True,
    }


def _group_section_ids(
    rows: Sequence[dict[str, Any]],
    field: str,
    allowed_values: Sequence[str],
) -> dict[str, list[str]]:
    grouped = {value: [] for value in allowed_values}
    for row in rows:
        value = str(row.get(field) or "")
        if value in grouped:
            grouped[value].append(str(row["section_id"]))
    return grouped


def _group_by_future_pr(rows: Sequence[dict[str, Any]]) -> dict[str, list[str]]:
    labels: dict[str, list[str]] = {}
    for row in rows:
        for label in row.get("roadmap_pr_labels", []):
            if label == "PR #103":
                continue
            labels.setdefault(str(label), []).append(str(row["section_id"]))
    return {label: labels[label] for label in _sort_pr_labels(labels)}


def _market_section_index(
    rows: Sequence[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    taxonomy = [
        item for item in config.get("market_taxonomy", []) if isinstance(item, dict)
    ]
    route_classes = list(config.get("route_class_enum", ROUTE_CLASSES))
    parent_groups = [
        str(group.get("parent_capability_group_id"))
        for group in config.get("parent_capability_group_enum", [])
        if isinstance(group, dict)
    ]
    rows_by_market: dict[str, list[dict[str, Any]]] = {
        str(market.get("market_id")): [] for market in taxonomy
    }
    for row in rows:
        for relevance in row.get("market_relevance", []):
            market_id = str(relevance.get("market_id"))
            rows_by_market.setdefault(market_id, []).append(row)

    stage_order = {value: index for index, value in enumerate(MARKET_STAGE_CLASSES)}
    markets: list[dict[str, Any]] = []
    for market in sorted(
        taxonomy,
        key=lambda item: (
            stage_order.get(str(item.get("market_stage_class")), 10**9),
            str(item.get("market_id")),
        ),
    ):
        market_id = str(market.get("market_id"))
        market_rows = rows_by_market.get(market_id, [])
        section_ids = [str(row["section_id"]) for row in market_rows]
        grouped_by_route = _group_section_ids(
            market_rows, "current_route_class", route_classes
        )
        grouped_by_parent = _group_section_ids(
            market_rows, "parent_capability_group_id", parent_groups
        )
        live_launch_sections = [
            str(row["section_id"])
            for row in market_rows
            if any(
                token in str(row.get("normalized_section_title", "")).lower()
                for token in ("live", "launch", "canary", "day-1", "day1")
            )
        ]
        markets.append(
            {
                "market_id": market_id,
                "market_display_name": str(market.get("market_display_name") or market_id),
                "market_stage_class": str(market.get("market_stage_class") or ""),
                "market_scope_confidence_class": _market_confidence_for_entry(market),
                "evidence_basis": str(market.get("evidence_basis") or ""),
                "related_section_ids": section_ids,
                "related_sections_grouped_by_route_class": grouped_by_route,
                "related_sections_grouped_by_parent_capability": grouped_by_parent,
                "related_sections_grouped_by_future_pr_label": _group_by_future_pr(
                    market_rows
                ),
                "source_evidence_sections": grouped_by_route.get(
                    "SOURCE_EVIDENCE_ROUTE", []
                ),
                "connector_sections": grouped_by_route.get(
                    "CONNECTOR_SEMANTIC_ROUTE", []
                ),
                "runtime_cash_sections": grouped_by_route.get("RUNTIME_CASH_ROUTE", []),
                "replay_paper_sections": grouped_by_route.get("REPLAY_PAPER_ROUTE", []),
                "live_launch_sections": live_launch_sections,
                "risk_sections": grouped_by_route.get("RISK_ROUTE", []),
                "latency_sections": grouped_by_route.get("LATENCY_COST_ROUTE", []),
                "quantum_sections": (
                    grouped_by_route.get("QUANTUM_FORWARD_OPTIMIZATION_ROUTE", [])
                    + grouped_by_route.get("QUANTUM_BACKEND_ROUTE", [])
                    + grouped_by_route.get("OPTIMIZER_ARBITRATION_ROUTE", [])
                ),
                "dashboard_owner_sections": (
                    grouped_by_route.get("OWNER_ROUTE", [])
                    + grouped_by_route.get("GOVERNANCE_ROUTE", [])
                    + grouped_by_route.get("DASHBOARD_OWNER_SURFACE_ROUTE", [])
                ),
                "research_sections": grouped_by_route.get("RESEARCH_ROUTE", []),
                "unresolved_sections": grouped_by_route.get(
                    "UNRESOLVED_DEFAULT_ROUTE", []
                ),
                "required_future_roadmap_pr_labels": _sort_pr_labels(
                    _group_by_future_pr(market_rows).keys()
                ),
                "no_market_launch_authority_created_flag": True,
                "no_external_market_fact_created_flag": True,
                "no_runtime_live_order_profit_authority_created_flag": True,
            }
        )
    return {
        "market_index_id": "QTT_MARKET_SPECIFIC_MASTER_PLAN_SECTION_INDEX_V1_0",
        "authority_class": "STATIC_MARKET_SECTION_INDEX_NOT_MARKET_LAUNCH_AUTHORITY",
        "markets": markets,
    }


def _market_index_summary(index: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    markets = [item for item in index.get("markets", []) if isinstance(item, dict)]
    stage_counts = Counter(str(market.get("market_stage_class")) for market in markets)
    route_counts: Counter[str] = Counter()
    for market in markets:
        grouped = market.get("related_sections_grouped_by_route_class", {})
        if not isinstance(grouped, dict):
            continue
        for route_class, section_ids in grouped.items():
            route_counts[str(route_class)] += len(_list_value(section_ids))
    by_market = {
        str(market.get("market_id")): len(_list_value(market.get("related_section_ids")))
        for market in markets
    }
    return {
        "market_specific_index_count": len(markets),
        "market_entry_counts_by_market_stage_class": {
            value: int(stage_counts.get(value, 0)) for value in MARKET_STAGE_CLASSES
        },
        "market_entry_counts_by_route_class": {
            value: int(route_counts.get(value, 0))
            for value in config.get("route_class_enum", ROUTE_CLASSES)
        },
        "prediction_market_section_counts": {
            "KALSHI": by_market.get("KALSHI", 0),
            "POLYMARKET": by_market.get("POLYMARKET", 0),
            "FORECASTEX_IBKR": by_market.get("FORECASTEX_IBKR", 0),
            "PREDICTION_MARKETS_GENERAL": by_market.get(
                "PREDICTION_MARKETS_GENERAL", 0
            ),
        },
        "future_market_candidate_bucket_counts": {
            "MARKET_EXPANSION_GENERAL": by_market.get("MARKET_EXPANSION_GENERAL", 0)
        },
        "owner_review_required_market_candidate_counts": {
            "OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE": by_market.get(
                "OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE", 0
            )
        },
        "market_launch_authority_created": False,
        "stage2_launch_authority_created": False,
        "next_market_selected": False,
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
    roadmap_index = _load_json(root / DEFAULT_ROADMAP_INDEX)
    blueprint_index = _load_json(root / DEFAULT_BLUEPRINT_INDEX)
    controller = _load_json(root / DEFAULT_CONTROLLER)
    roster = _load_json(root / DEFAULT_ROSTER)
    crosswalk_rows = _build_crosswalk_rows(
        manifest=manifest,
        registry=registry,
        roadmap_index=roadmap_index,
        blueprint_index=blueprint_index,
        controller=controller,
    )
    command_matrix_rows = _build_command_matrix_rows(
        crosswalk_rows, registry["central_config"]
    )
    market_index = _market_section_index(crosswalk_rows, registry["central_config"])
    section_records = [
        _section_record(section, entries)
        for section in manifest["sections"]
    ]
    crosswalk_summary = _crosswalk_summary(
        rows=crosswalk_rows,
        manifest=manifest,
        config=registry["central_config"],
        roster=roster,
    )
    command_matrix_summary = _command_matrix_summary(
        command_rows=command_matrix_rows,
        crosswalk_rows=crosswalk_rows,
        manifest=manifest,
        config=registry["central_config"],
    )
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
        "central_config": registry["central_config"],
        "pr120_scope_summary": {
            "repo_canonical_pr_label": crosswalk_summary["repo_canonical_pr_label"],
            "roadmap_pr_label": crosswalk_summary["roadmap_pr_label"],
            "blueprint_pr_label": crosswalk_summary["blueprint_pr_label"],
            "semantic_task_id": crosswalk_summary["semantic_task_id"],
            "title": crosswalk_summary["title"],
            "materialized_capability": registry["central_config"][
                "roadmap_crosswalk_config"
            ].get("materialized_capability"),
            "state_transition": registry["central_config"][
                "roadmap_crosswalk_config"
            ].get("state_transition"),
            "pr119_github_audit_currentization_evidence": crosswalk_summary[
                "pr119_github_audit_currentization_evidence"
            ],
            "controller_decision_reference": crosswalk_summary[
                "controller_decision_reference"
            ],
            "artifact_family_decision": crosswalk_summary["artifact_family_decision"],
            "static_control_plane_only": True,
            "roadmap_pr104_command_matrix_implemented": False,
            "no_old_coverage_ledger_reintroduction": True,
            "no_master_plan_text_mutation": True,
            "no_runtime_live_source_connector_replay_paper_order_profit_latency_superiority_quantum_execution_authority": True,
            "no_market_launch_or_stage2_launch_authority": True,
            "no_next_market_selection": True,
        },
        "pr121_scope_summary": {
            "repo_canonical_pr_label": command_matrix_summary[
                "repo_canonical_pr_label"
            ],
            "roadmap_pr_label": command_matrix_summary["roadmap_pr_label"],
            "blueprint_pr_label": command_matrix_summary["blueprint_pr_label"],
            "semantic_task_id": command_matrix_summary["semantic_task_id"],
            "title": command_matrix_summary["title"],
            "materialized_capability": registry["central_config"][
                "command_matrix_config"
            ].get("materialized_capability"),
            "state_transition": registry["central_config"][
                "command_matrix_config"
            ].get("state_transition"),
            "pr120_github_audit_currentization_evidence": command_matrix_summary[
                "pr120_github_audit_currentization_evidence"
            ],
            "controller_decision_reference": command_matrix_summary[
                "controller_decision_reference"
            ],
            "blueprint_decision_reference": command_matrix_summary[
                "blueprint_decision_reference"
            ],
            "artifact_family_decision": command_matrix_summary[
                "artifact_family_decision"
            ],
            "compact_normalized_command_matrix_flag": command_matrix_summary[
                "compact_normalized_command_matrix_flag"
            ],
            "static_control_plane_only": True,
            "roadmap_pr105_source_retrieval_executor_implemented": False,
            "no_old_coverage_ledger_reintroduction": True,
            "no_master_plan_text_mutation": True,
            "no_runtime_live_source_connector_replay_paper_order_profit_latency_superiority_quantum_execution_authority": True,
            "no_market_launch_or_stage2_launch_authority": True,
            "no_next_market_selection": True,
        },
        "roadmap_crosswalk": {
            "crosswalk_id": registry["central_config"][
                "roadmap_crosswalk_config"
            ].get("crosswalk_id"),
            "authority_class": registry["central_config"][
                "roadmap_crosswalk_config"
            ].get("authority_class"),
            "rows": crosswalk_rows,
        },
        "roadmap_crosswalk_summary": crosswalk_summary,
        "command_matrix": {
            "command_matrix_id": registry["central_config"][
                "command_matrix_config"
            ].get("command_matrix_id"),
            "authority_class": registry["central_config"][
                "command_matrix_config"
            ].get("authority_class"),
            "repo_canonical_pr_label": command_matrix_summary[
                "repo_canonical_pr_label"
            ],
            "roadmap_pr_label": command_matrix_summary["roadmap_pr_label"],
            "blueprint_pr_label": command_matrix_summary["blueprint_pr_label"],
            "semantic_task_id": command_matrix_summary["semantic_task_id"],
            "materialized_capability": registry["central_config"][
                "command_matrix_config"
            ].get("materialized_capability"),
            "state_transition": registry["central_config"][
                "command_matrix_config"
            ].get("state_transition"),
            "source_crosswalk_reference": "docs/master_plan/generated/MasterPlanSectionCoverageReport.json#/roadmap_crosswalk/rows",
            "compact_normalized_command_matrix_flag": command_matrix_summary[
                "compact_normalized_command_matrix_flag"
            ],
            "rows": command_matrix_rows,
        },
        "command_matrix_summary": command_matrix_summary,
        "market_specific_section_index": market_index,
        "market_specific_section_index_summary": _market_index_summary(
            market_index, registry["central_config"]
        ),
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
