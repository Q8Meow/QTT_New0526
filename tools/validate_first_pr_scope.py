#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Sequence

SUCCESS_MARKER = "FIRST_PR_SCOPE_GATE_OK"

BLOCK_FLAG_TO_SCOPE_BLOCK = {
    "block_runtime": "runtime",
    "block_live": "live",
    "block_sha": "sha",
    "block_companion_package": "companion_package",
    "block_profit_claims": "profit_claims",
    "block_source_retrieval": "source_retrieval",
    "block_source_acceptance": "source_acceptance",
    "block_connector_binding": "connector_binding",
    "block_private_state_fetch": "private_state_fetch",
    "block_order_execution": "order_execution",
    "block_neural_training": "neural_training",
    "block_neural_inference": "neural_inference",
    "block_external_repo_clone": "external_repo_clone",
    "block_package_install_scripts": "package_install_scripts",
}


def _load_scope_report(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"scope report is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"scope report is not valid JSON: {exc}"]
    if not isinstance(value, dict):
        return None, ["scope report must contain an object"]
    return value, []


def validate_first_pr_scope(
    *,
    repo_root: pathlib.Path,
    scope_report_path: pathlib.Path,
    requested_blocks: set[str],
) -> list[str]:
    failures: list[str] = []
    if not repo_root.exists() or not repo_root.is_dir():
        failures.append(f"repo root is missing or not a directory: {repo_root}")

    scope, scope_failures = _load_scope_report(scope_report_path)
    failures.extend(scope_failures)
    if scope is None:
        return failures

    if scope.get("first_pr_scope") != "schema_only_scaffold":
        failures.append("first_pr_scope must be schema_only_scaffold")

    blocks = scope.get("blocks")
    if not isinstance(blocks, list) or not all(isinstance(item, str) for item in blocks):
        failures.append("scope report blocks must be a list of strings")
        return failures

    missing_blocks = sorted(requested_blocks - set(blocks))
    if missing_blocks:
        failures.append(f"scope report missing requested blocks: {', '.join(missing_blocks)}")
    return failures


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--scope-report", required=True)
    for flag_name in sorted(BLOCK_FLAG_TO_SCOPE_BLOCK):
        parser.add_argument(f"--{flag_name.replace('_', '-')}", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    requested_blocks = {
        block
        for flag_name, block in BLOCK_FLAG_TO_SCOPE_BLOCK.items()
        if getattr(args, flag_name)
    }

    failures = validate_first_pr_scope(
        repo_root=pathlib.Path(args.repo_root),
        scope_report_path=pathlib.Path(args.scope_report),
        requested_blocks=requested_blocks,
    )
    if failures:
        raise SystemExit("FIRST_PR_SCOPE_GATE_FAILED\n- " + "\n- ".join(failures))
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
