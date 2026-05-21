#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.launch_readiness import (  # noqa: E402
    day1_launch_readiness_roadmap_policy as policy,
)


REPORT_PATH = Path(policy.POLICY_LITERAL_DRIFT_REPORT_PATH)
APPROVED_DEFINITION_PATHS = {
    Path(policy.POLICY_MODULE_PATH).as_posix(),
    Path(policy.POLICY_SCHEMA_DEFS_PATH).as_posix(),
    Path(policy.POLICY_MANIFEST_PATH).as_posix(),
}
INSTANCE_PREFIXES = (
    "docs/master_plan/generated/PR136",
    "docs/roadmap/generated/CODEX_PR136",
    "docs/roadmap/generated/CODEX_REPO_PR135_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap",
)


def _write_report(repo_root: Path, failures: Sequence[str]) -> None:
    payload = {
        "receipt_type": "PR136_POLICY_LITERAL_DRIFT_REPORT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "approved_definition_locations": sorted(APPROVED_DEFINITION_PATHS),
        "instance_prefixes": list(INSTANCE_PREFIXES),
        "policy_literal_drift_detected": bool(failures),
        "failures": list(failures),
    }
    path = repo_root / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _policy_lists() -> dict[str, list[Any]]:
    return {
        "sequence_authority_classes": list(policy.SEQUENCE_AUTHORITY_CLASSES),
        "classification_labels": list(policy.CLASSIFICATION_LABELS),
        "evidence_classes": list(policy.EVIDENCE_CLASSES),
        "readiness_state_classes": list(policy.READINESS_STATE_CLASSES),
        "readiness_domain_taxonomy_rules": list(policy.READINESS_DOMAIN_TAXONOMY_RULES),
        "canonical_venues": list(policy.CANONICAL_VENUES),
        "future_pr_scope_classes": list(policy.FUTURE_PR_SCOPE_CLASSES),
        "future_pr_number_status": list(policy.FUTURE_PR_NUMBER_STATUS),
        "domain_types": list(policy.DOMAIN_TYPES),
        "block_code_refs": list(policy.BLOCK_CODE_REFS),
    }


def _policy_terms() -> set[str]:
    terms: set[str] = {policy.VALIDATOR_MARKER}
    for values in _policy_lists().values():
        terms.update(value for value in values if isinstance(value, str))
    terms.update(policy.NO_AUTHORITY_FLAGS)
    return terms


def _is_approved(rel_path: str) -> bool:
    return rel_path in APPROVED_DEFINITION_PATHS


def _is_instance(rel_path: str) -> bool:
    return rel_path.startswith(INSTANCE_PREFIXES)


def _pr136_owned_paths(repo_root: Path, extra_paths: Iterable[Path]) -> list[Path]:
    candidates = [
        Path(policy.POLICY_MODULE_PATH),
        Path(policy.ROADMAP_MODULE_PATH),
        Path("tools/validate_pr136_roadmap_policy_literal_drift.py"),
        Path("tools/validate_pr136_day1_launch_readiness_roadmap.py"),
        Path("tests/roadmap/test_pr136_day1_launch_readiness_roadmap.py"),
        Path("tests/fail_closed/test_run_validation_gates.py"),
        Path("tools/run_validation_gates.py"),
        Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
        Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json"),
    ]
    candidates.extend(Path(path) for path in policy.PR136_SCHEMA_PATHS)
    candidates.extend(Path(path) for path in policy.PR136_REPORT_PATHS)
    candidates.extend(Path(path) for path in policy.PR136_ROADMAP_RECEIPT_PATHS)
    candidates.extend(extra_paths)
    return [repo_root / path for path in candidates if (repo_root / path).exists()]


def _literal_collection_duplicates(path: Path, terms: set[str]) -> bool:
    if path.suffix != ".py":
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            node = statement.value
        elif isinstance(statement, ast.AnnAssign):
            node = statement.value
        else:
            continue
        if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            continue
        values = [
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        ]
        if len({value for value in values if value in terms}) >= 2:
            return True
    return False


def _schema_defines_policy_enum(path: Path, terms: set[str]) -> bool:
    if path.suffix != ".json":
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    def walk(value: Any) -> bool:
        if isinstance(value, dict):
            if "enum" in value and isinstance(value["enum"], list):
                hits = {item for item in value["enum"] if isinstance(item, str) and item in terms}
                if len(hits) >= 2:
                    return True
            return any(walk(item) for item in value.values())
        if isinstance(value, list):
            return any(walk(item) for item in value)
        return False

    return walk(payload)


def _forced_domain_count_13(text: str) -> bool:
    patterns = (
        r'"readiness_domain_count"\s*:\s*13\b',
        r"\breadiness_domain_count\s*=\s*13\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def validate_policy_literal_drift(
    *,
    repo_root: Path = _REPO_ROOT,
    extra_paths: Sequence[Path] = (),
    write_report: bool = True,
) -> list[str]:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    terms = _policy_terms()
    schema_path = repo_root / policy.POLICY_SCHEMA_DEFS_PATH
    manifest_path = repo_root / policy.POLICY_MANIFEST_PATH
    if not schema_path.exists():
        failures.append(f"missing policy schema defs: {policy.POLICY_SCHEMA_DEFS_PATH}")
    if not manifest_path.exists():
        failures.append(f"missing policy manifest: {policy.POLICY_MANIFEST_PATH}")

    if schema_path.exists() and manifest_path.exists():
        schema_defs = json.loads(schema_path.read_text(encoding="utf-8")).get("$defs", {})
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = _policy_lists()
        comparisons = {
            "sequence_authority_classes": schema_defs.get("sequence_authority_class", {}).get("enum"),
            "classification_labels": schema_defs.get("classification_label", {}).get("enum"),
            "evidence_classes": schema_defs.get("evidence_class", {}).get("enum"),
            "readiness_state_classes": schema_defs.get("readiness_state_class", {}).get("enum"),
            "readiness_domain_taxonomy_rules": schema_defs.get("taxonomy_rule", {}).get("enum"),
            "canonical_venues": schema_defs.get("canonical_venue_id", {}).get("enum"),
            "future_pr_scope_classes": schema_defs.get("future_pr_scope_class", {}).get("enum"),
            "future_pr_number_status": schema_defs.get("future_pr_number_status", {}).get("enum"),
            "domain_types": schema_defs.get("domain_type", {}).get("enum"),
            "block_code_refs": schema_defs.get("block_code_ref", {}).get("enum"),
        }
        for key, expected_values in expected.items():
            if comparisons.get(key) != expected_values:
                failures.append(f"policy schema defs drift at {key}")
            if manifest.get(key) != expected_values:
                failures.append(f"policy manifest drift at {key}")
        if schema_defs.get("validator_marker", {}).get("const") != policy.VALIDATOR_MARKER:
            failures.append("policy schema defs validator marker drift")
        if manifest.get("validator_marker") != policy.VALIDATOR_MARKER:
            failures.append("policy manifest validator marker drift")
        if manifest.get("no_authority_flags") != policy.NO_AUTHORITY_FLAGS:
            failures.append("policy manifest no-authority flag drift")

    for path in _pr136_owned_paths(repo_root, extra_paths):
        try:
            rel_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel_path = path.as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if _forced_domain_count_13(text):
            failures.append(f"readiness_domain_count forced to 13: {rel_path}")
        if re.search(r'"fixed_13_domain_model_used"\s*:\s*true', text, re.IGNORECASE):
            failures.append(f"fixed_13_domain_model_used true: {rel_path}")
        if _is_approved(rel_path) or _is_instance(rel_path):
            continue
        if _literal_collection_duplicates(path, terms):
            failures.append(f"policy literal list duplicated outside approved locations: {rel_path}")
        if _schema_defines_policy_enum(path, terms):
            failures.append(f"schema duplicates policy enum outside defs: {rel_path}")
    if write_report:
        _write_report(repo_root, failures)
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--extra-file", action="append", default=[], type=Path)
    args = parser.parse_args(argv)
    failures = validate_policy_literal_drift(
        repo_root=args.repo_root,
        extra_paths=tuple(args.extra_file),
    )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
