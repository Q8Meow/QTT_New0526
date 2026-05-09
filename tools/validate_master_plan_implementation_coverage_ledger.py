#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import subprocess
import sys
from typing import Any, Sequence

try:
    import build_master_plan_implementation_coverage_ledger as builder
except ModuleNotFoundError:
    from tools import build_master_plan_implementation_coverage_ledger as builder

SUCCESS_MARKER = "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_OK"
FAILURE_MARKER = "MASTER_PLAN_IMPLEMENTATION_COVERAGE_LEDGER_FAILED"

EXPECTED_ROOT_FIELDS = {
    "ledger_type",
    "ledger_schema_version",
    "generated_at_policy",
    "generated_by_tool",
    "source_repository_path",
    "source_master_plan_path",
    "authority",
    "coverage_summary",
    "pr_records",
    "master_plan_section_records",
    "validation_marker_records",
    "review_required_records",
    "future_pr_tracking_policy",
}

EXPECTED_AUTHORITY = copy.deepcopy(builder.AUTHORITY)

EXPECTED_STRONG_PR_MARKERS = {
    pr_number: spec["validation_markers"][0]
    for pr_number, spec in builder.STRONG_PR_RECORDS.items()
}

EXPECTED_STRONG_PR_VALIDATORS = {
    pr_number: spec["validator_tools"][0]
    for pr_number, spec in builder.STRONG_PR_RECORDS.items()
}

EXPECTED_STRONG_PR_SECTIONS = {
    pr_number: set(spec["master_plan_section_ids"])
    for pr_number, spec in builder.STRONG_PR_RECORDS.items()
}

EXPECTED_PR47_MARKERS = set(builder.PR47_VALIDATION_MARKERS)
EXPECTED_PR47_VALIDATORS = set(builder.PR47_VALIDATOR_TOOLS)

FORBIDDEN_TRUE_FIELDS = {
    "ledger_is_master_plan_authority",
    "ledger_is_source_fact_authority",
    "ledger_is_connector_semantic_authority",
    "ledger_is_runtime_authority",
    "ledger_is_order_authority",
    "ledger_is_atomicrows_authority",
    "ledger_is_profit_evidence",
    "ledger_may_select_next_pr_without_master_plan_crosscheck",
    "runtime_authority_created_flag",
    "order_authority_created_flag",
    "profit_claim_created_flag",
    "atomicrows_bundle_created_flag",
    "atomicrows_sha_created_flag",
    "source_fact_acceptance_created_flag",
    "connector_semantics_populated_flag",
    "live_reachability_created_flag",
    "runtime_resolver_snapshot_created_flag",
    "replay_or_paper_execution_created_flag",
    "replay_paper_result_packets_created_flag",
    "result_merge_created_flag",
    "dual_result_review_decision_created_flag",
    "owner_live_promotion_approval_created_flag",
    "live_eligibility_created_flag",
    "canary_eligibility_created_flag",
    "canary_execution_created_flag",
    "runtime_cash_receipt_created_flag",
    "blocker_reduction_created_flag",
    "network_io_created_flag",
    "source_retrieval_created_flag",
    "retrieves_source_evidence",
    "creates_source_fact_acceptance",
    "creates_real_accepted_source_evidence_packets",
    "populates_production_connector_semantics",
    "creates_runtime_resolver_snapshot",
    "executes_replay_or_paper",
    "creates_replay_or_paper_result_packets",
    "merges_replay_paper_results",
    "creates_dual_result_review_decision",
    "creates_owner_live_promotion_approval",
    "creates_live_eligibility",
    "creates_canary_eligibility",
    "executes_canary",
    "creates_live_reachability",
    "creates_order_authority",
    "creates_runtime_cash_receipt",
    "creates_atomicrows_bundle",
    "creates_atomicrows_hash",
    "reduces_blockers",
    "creates_profit_evidence",
    "creates_network_io",
    "atomicrows_bundle_present",
    "atomicrows_sha_present",
    "creates_authority_flag",
}


class SchemaValidationError(ValueError):
    pass


def _load_json_object(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        raise SchemaValidationError(f"JSON file is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"JSON file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SchemaValidationError(f"JSON file must contain an object: {path}")
    return value


def _resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaValidationError(f"only local schema refs are supported: {ref}")
    current: Any = schema
    for part in ref[2:].split("/"):
        current = current[part]
    if not isinstance(current, dict):
        raise SchemaValidationError(f"schema ref does not resolve to object: {ref}")
    return current


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaValidationError(f"unsupported schema type: {expected}")


def _validate_value_against_schema(
    value: Any,
    node: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[str]:
    if "$ref" in node:
        return _validate_value_against_schema(
            value,
            _resolve_ref(root_schema, node["$ref"]),
            root_schema,
            path,
        )

    failures: list[str] = []
    expected_type = node.get("type")
    if isinstance(expected_type, list):
        if not any(_type_matches(value, item) for item in expected_type):
            failures.append(f"{path} has wrong type")
            return failures
    elif isinstance(expected_type, str):
        if not _type_matches(value, expected_type):
            failures.append(f"{path} has wrong type")
            return failures

    if "const" in node and value != node["const"]:
        failures.append(f"{path} must be {node['const']!r}")
    if "enum" in node and value not in node["enum"]:
        failures.append(f"{path} must be one of {node['enum']!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            failures.append(f"{path} must be >= {node['minimum']}")
        if "maximum" in node and value > node["maximum"]:
            failures.append(f"{path} must be <= {node['maximum']}")

    if isinstance(value, dict):
        properties = node.get("properties", {})
        required = set(node.get("required", []))
        missing = sorted(required - set(value))
        failures.extend(f"{path}.{field} is required" for field in missing)
        if node.get("additionalProperties") is False:
            unexpected = sorted(set(value) - set(properties))
            failures.extend(f"{path}.{field} is not allowed" for field in unexpected)
        for key, child in value.items():
            if key in properties:
                failures.extend(
                    _validate_value_against_schema(
                        child,
                        properties[key],
                        root_schema,
                        f"{path}.{key}",
                    )
                )

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            failures.append(f"{path} must contain at least {node['minItems']} items")
        if "maxItems" in node and len(value) > node["maxItems"]:
            failures.append(f"{path} must contain at most {node['maxItems']} items")
        if "items" in node:
            for index, item in enumerate(value):
                failures.extend(
                    _validate_value_against_schema(
                        item,
                        node["items"],
                        root_schema,
                        f"{path}[{index}]",
                    )
                )

    return failures


def validate_against_schema(
    ledger: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    return _validate_value_against_schema(ledger, schema, schema, "ledger")


def _walk(value: Any, path: str = "ledger"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _stable_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _root_shape_failures(ledger: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    missing = sorted(EXPECTED_ROOT_FIELDS - set(ledger))
    unexpected = sorted(set(ledger) - EXPECTED_ROOT_FIELDS)
    if missing:
        failures.append("ledger missing required fields: " + ", ".join(missing))
    if unexpected:
        failures.append("ledger has unexpected fields: " + ", ".join(unexpected))
    if ledger.get("ledger_type") != builder.LEDGER_TYPE:
        failures.append(f"ledger_type must be {builder.LEDGER_TYPE}")
    if ledger.get("ledger_schema_version") != builder.LEDGER_SCHEMA_VERSION:
        failures.append(f"ledger_schema_version must be {builder.LEDGER_SCHEMA_VERSION}")
    if ledger.get("generated_at_policy") != builder.GENERATED_AT_POLICY:
        failures.append(f"generated_at_policy must be {builder.GENERATED_AT_POLICY}")
    if ledger.get("generated_by_tool") != builder.GENERATED_BY_TOOL:
        failures.append(f"generated_by_tool must be {builder.GENERATED_BY_TOOL}")
    if ledger.get("source_repository_path") != ".":
        failures.append("source_repository_path must be repository-relative '.'")
    if ledger.get("source_master_plan_path") != builder.SOURCE_MASTER_PLAN_PATH:
        failures.append(
            f"source_master_plan_path must be {builder.SOURCE_MASTER_PLAN_PATH}"
        )
    if ledger.get("authority") != EXPECTED_AUTHORITY:
        failures.append("authority block must match PR47 non-authoritative ledger contract")
    return failures


def _forbidden_claim_failures(ledger: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for path, key, value in _walk(ledger):
        if key in FORBIDDEN_TRUE_FIELDS and value is True:
            failures.append(f"{path} must remain false")
    return failures


def _pr_record_failures(ledger: dict[str, Any]) -> list[str]:
    records = ledger.get("pr_records")
    if not isinstance(records, list):
        return ["pr_records must be a list"]
    by_pr = {
        record.get("pr_number"): record
        for record in records
        if isinstance(record, dict)
    }
    failures: list[str] = []

    expected_pr_numbers = list(range(builder.TRACKED_PR_MIN, builder.TRACKED_PR_MAX + 1))
    if sorted(by_pr) != expected_pr_numbers:
        failures.append("pr_records must contain exactly PR #1 through PR #47")

    for pr_number in range(
        builder.TRACKED_PR_MIN,
        builder.HISTORICAL_REVIEW_REQUIRED_PR_MAX + 1,
    ):
        record = by_pr.get(pr_number)
        if not record:
            continue
        if record.get("review_status") == "VERIFIED":
            failures.append(
                f"PR #{pr_number} must not be VERIFIED without explicit section evidence"
            )
        if record.get("review_status") != "SECTION_MAPPING_REQUIRES_OWNER_REVIEW":
            failures.append(
                f"PR #{pr_number} must be marked SECTION_MAPPING_REQUIRES_OWNER_REVIEW"
            )

    for pr_number, marker in EXPECTED_STRONG_PR_MARKERS.items():
        record = by_pr.get(pr_number)
        if not isinstance(record, dict):
            failures.append(f"PR #{pr_number} strong record is missing")
            continue
        if record.get("review_status") != "VERIFIED":
            failures.append(f"PR #{pr_number} strong record must be VERIFIED")
        if marker not in record.get("validation_markers", []):
            failures.append(f"PR #{pr_number} missing validation marker {marker}")
        validator = EXPECTED_STRONG_PR_VALIDATORS[pr_number]
        if validator not in record.get("validator_tools", []):
            failures.append(f"PR #{pr_number} missing validator tool {validator}")
        sections = set(record.get("master_plan_section_ids", []))
        if not EXPECTED_STRONG_PR_SECTIONS[pr_number].issubset(sections):
            failures.append(f"PR #{pr_number} missing expected master-plan section IDs")
        if record.get("implementation_status") not in {
            "STATIC_CONTRACT_IMPLEMENTED",
            "STATIC_GATE_IMPLEMENTED",
        }:
            failures.append(f"PR #{pr_number} must be a static implemented record")

    pr47 = by_pr.get(47)
    if not isinstance(pr47, dict):
        failures.append("PR #47 tracking record is missing")
    else:
        if pr47.get("implementation_status") != "TRACKING_ONLY":
            failures.append("PR #47 must remain TRACKING_ONLY")
        if pr47.get("review_status") != "SECTION_MAPPING_REQUIRES_OWNER_REVIEW":
            failures.append("PR #47 must require owner section-mapping review")
        if pr47.get("branch_name_if_known") is not None:
            failures.append("PR #47 must not require branch-name metadata")
        if pr47.get("local_commit_if_known") is not None:
            failures.append("PR #47 must not require local branch-tip metadata")
        if pr47.get("merge_commit_if_known") is not None:
            failures.append("PR #47 must not require merge-commit metadata")
        if pr47.get("master_plan_section_ids") != []:
            failures.append("PR #47 must not claim a verified master-plan section mapping")
        missing_markers = EXPECTED_PR47_MARKERS - set(pr47.get("validation_markers", []))
        if missing_markers:
            failures.append(
                "PR #47 missing validation markers: " + ", ".join(sorted(missing_markers))
            )
        missing_validators = EXPECTED_PR47_VALIDATORS - set(pr47.get("validator_tools", []))
        if missing_validators:
            failures.append(
                "PR #47 missing validator tools: " + ", ".join(sorted(missing_validators))
            )

    return failures


def _section_record_failures(ledger: dict[str, Any]) -> list[str]:
    records = ledger.get("master_plan_section_records")
    if not isinstance(records, list):
        return ["master_plan_section_records must be a list"]
    section_ids = {
        section_id
        for spec in builder.STRONG_PR_RECORDS.values()
        for section_id in spec["master_plan_section_ids"]
    }
    actual = {
        record.get("section_id")
        for record in records
        if isinstance(record, dict)
    }
    missing = sorted(section_ids - actual)
    if missing:
        return ["master_plan_section_records missing strong sections: " + ", ".join(missing)]
    return []


def _marker_record_failures(ledger: dict[str, Any]) -> list[str]:
    records = ledger.get("validation_marker_records")
    if not isinstance(records, list):
        return ["validation_marker_records must be a list"]
    actual = {
        record.get("validation_marker")
        for record in records
        if isinstance(record, dict)
    }
    missing = sorted(set(EXPECTED_STRONG_PR_MARKERS.values()) - actual)
    if missing:
        return ["validation_marker_records missing strong markers: " + ", ".join(missing)]
    return []


def _policy_failures(ledger: dict[str, Any]) -> list[str]:
    policy = ledger.get("future_pr_tracking_policy")
    if not isinstance(policy, dict):
        return ["future_pr_tracking_policy must be an object"]
    failures: list[str] = []
    if policy.get("future_pr_must_add_or_regenerate_ledger_coverage") is not True:
        failures.append("future PRs must add or regenerate ledger coverage")
    if policy.get("ledger_does_not_replace_master_plan_crosscheck") is not True:
        failures.append("future policy must preserve master-plan crosscheck")
    if policy.get("ledger_may_not_select_next_pr_without_master_plan_crosscheck") is not True:
        failures.append("future policy must block ledger-only next-PR selection")
    required = {
        "PR number",
        "section IDs",
        "validator marker",
        "generated report",
        "authority boundary",
        "next allowed consumer",
        "review required flag",
    }
    if not required.issubset(set(policy.get("required_future_pr_fields", []))):
        failures.append("future policy missing required tracking fields")
    return failures


def _filesystem_failures(repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    for rel_path in [builder.CANONICAL_ATOMICROWS_BUNDLE, builder.CANONICAL_ATOMICROWS_SHA]:
        if (repo_root / pathlib.Path(rel_path)).exists():
            failures.append(f"protected AtomicRows path must remain absent: {rel_path}")
    return failures


def _determinism_failures(
    ledger: dict[str, Any],
    repo_root: pathlib.Path,
    ledger_path: pathlib.Path,
) -> list[str]:
    rebuilt = builder.build_ledger(repo_root)
    failures: list[str] = []
    if ledger != rebuilt:
        failures.append("ledger content is not deterministic against local builder output")
    if ledger_path.exists() and ledger_path.read_text(encoding="utf-8") != _stable_json(ledger):
        failures.append("ledger file does not use deterministic sorted JSON formatting")
    return failures


def validate_ledger(
    ledger: dict[str, Any],
    schema: dict[str, Any],
    *,
    repo_root: pathlib.Path,
    ledger_path: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    failures.extend(validate_against_schema(ledger, schema))
    failures.extend(_root_shape_failures(ledger))
    failures.extend(_forbidden_claim_failures(ledger))
    failures.extend(_pr_record_failures(ledger))
    failures.extend(_section_record_failures(ledger))
    failures.extend(_marker_record_failures(ledger))
    failures.extend(_policy_failures(ledger))
    failures.extend(_filesystem_failures(repo_root))
    failures.extend(_determinism_failures(ledger, repo_root, ledger_path))
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root).resolve()
    ledger_path = repo_root / pathlib.Path(args.ledger)
    schema_path = repo_root / pathlib.Path(args.schema)

    try:
        ledger = _load_json_object(ledger_path)
        schema = _load_json_object(schema_path)
        failures = validate_ledger(
            ledger,
            schema,
            repo_root=repo_root,
            ledger_path=ledger_path,
        )
    except (OSError, SchemaValidationError, KeyError, subprocess.CalledProcessError) as exc:
        failures = [str(exc)]

    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
