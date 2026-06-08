#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import sys
from typing import Iterable, Sequence


SUCCESS_MARKER = "NESTED_VALIDATOR_CONTRACTS_OK"
SAFE_NESTED_VALIDATOR_RERUN_MARKER = (
    "NESTED_VALIDATOR_RERUN_ALLOWED_SAFE_FAST_INTENTIONAL"
)
ORCHESTRATOR_ALLOWLIST = {
    "tools/run_validation_gates.py",
    "tools/run_pytest_fresh_basetemp.py",
    "tools/validate_nested_validator_contracts.py",
}
FORBIDDEN_COMMAND_PATTERNS = (
    re.compile(r"(?:^|[\\/])tools[\\/]run_validation_gates\.py$"),
    re.compile(r"(?:^|[\\/])tools[\\/]run_pytest_fresh_basetemp\.py$"),
    re.compile(r"(?:^|[\\/])tools[\\/]validate_pr[0-9][A-Za-z0-9_-]*\.py$"),
    re.compile(r"^pytest(?:\.exe)?$"),
)


def _repo_relative(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _candidate_files(repo_root: Path) -> tuple[Path, ...]:
    roots = (repo_root / "tools", repo_root / "src" / "qtt" / "stage1_prediction_markets")
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*.py") if path.is_file())
    return tuple(sorted(files))


def _is_subprocess_run(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    )


def _literal_strings(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node.value
        return
    if isinstance(node, ast.JoinedStr):
        for value in node.values:
            yield from _literal_strings(value)
        return
    for child in ast.iter_child_nodes(node):
        yield from _literal_strings(child)


def _normal_command_token(value: str) -> str:
    return value.strip().replace("\\", "/")


def _forbidden_token(value: str) -> str | None:
    token = _normal_command_token(value)
    for pattern in FORBIDDEN_COMMAND_PATTERNS:
        if pattern.search(token):
            return token
    return None


def nested_validator_contract_failures_for_paths(
    repo_root: Path,
    paths: Sequence[Path],
) -> tuple[str, ...]:
    failures: list[str] = []
    for path in paths:
        relative = _repo_relative(path, repo_root)
        if relative in ORCHESTRATOR_ALLOWLIST:
            continue
        source = path.read_text(encoding="utf-8")
        if SAFE_NESTED_VALIDATOR_RERUN_MARKER in source:
            continue
        try:
            module = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{relative}:{exc.lineno}: unable to parse Python source")
            continue
        for node in ast.walk(module):
            if not isinstance(node, ast.Call) or not _is_subprocess_run(node):
                continue
            strings = tuple(_literal_strings(node))
            for value in strings:
                forbidden = _forbidden_token(value)
                if forbidden is None:
                    continue
                failures.append(
                    f"{relative}:{node.lineno}: nested full validator rerun "
                    f"forbidden: {forbidden}; validate recorded receipts/contracts "
                    f"or add {SAFE_NESTED_VALIDATOR_RERUN_MARKER}"
                )
    return tuple(failures)


def validate(repo_root: Path) -> tuple[str, ...]:
    return nested_validator_contract_failures_for_paths(
        repo_root,
        _candidate_files(repo_root),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    failures = validate(repo_root)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
