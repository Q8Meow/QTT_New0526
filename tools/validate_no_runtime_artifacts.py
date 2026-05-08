#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import pathlib
import re

FORBIDDEN_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "AtomicRows.bundle.jsonl",
    "AtomicRows.bundle.sha256",
    "credentials.json",
    "id_rsa",
    "id_rsa.pub",
    "secrets.json",
}
FORBIDDEN_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
}
ALWAYS_FORBIDDEN_PATH_PARTS = {
    "dashboard_runtime",
    "live_connectors",
    "runtime_services",
    "telegram_runtime",
}
FLAG_FORBIDDEN_PATH_PARTS = {
    "forbid_source_retrieval": {
        "official_source_retriever",
        "source_fetch",
        "source_retrieval",
        "source_scraper",
    },
    "forbid_source_acceptance": {
        "accepted_source_evidence",
        "acceptance_executor",
        "source_acceptance",
    },
    "forbid_connector_binding": {
        "connector_binding",
        "connector_semantic_binding",
        "semantic_binding",
    },
    "forbid_private_state_fetch": {
        "account_state_fetch",
        "balance_fetcher",
        "private_state",
        "private_state_fetch",
    },
    "forbid_order_execution": {
        "live_order",
        "order_execution",
        "order_router",
        "trade_executor",
    },
    "forbid_neural_training": {
        "model_training",
        "neural_training",
        "train_model",
    },
    "forbid_neural_inference": {
        "inference_service",
        "neural_inference",
        "serve_model",
    },
    "forbid_external_repo_clone": {
        "external_repo_clone",
        "third_party_clones",
        "vendor_external_repo",
    },
}
PACKAGE_INSTALL_SCRIPT_NAMES = {
    "bootstrap.sh",
    "install.bat",
    "install.cmd",
    "install.ps1",
    "install.sh",
    "postinstall.js",
    "setup.sh",
}

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".cmd",
    ".ini",
    ".js",
    ".json",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".yaml",
    ".yml",
}
SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".tox",
    ".uv-cache",
    "__pycache__",
    "env",
    "node_modules",
    "venv",
}
SKIP_CONTENT_PATHS = {
    pathlib.PurePosixPath("tools/validate_no_runtime_artifacts.py"),
}
SKIP_CONTENT_TOP_LEVEL_DIRS = {"docs", "tests"}

CONTENT_PATTERNS = {
    "forbid_source_retrieval": [
        ("HTTP retrieval client", r"\b(?:requests|httpx)\.(?:get|post|request)\s*\("),
        ("urllib retrieval client", r"\burllib\.request\.urlopen\s*\("),
        ("aiohttp client", r"\baiohttp\.ClientSession\b"),
        ("browser retrieval automation", r"\b(?:playwright|selenium)\b"),
    ],
    "forbid_source_acceptance": [
        (
            "source acceptance call",
            r"\baccept(?:ed)?_source_(?:fact|evidence|packet)\s*\(",
        ),
        (
            "accepted source status assignment",
            r"\bsource_acceptance_status\s*=\s*[\"']ACCEPTED[\"']",
        ),
        (
            "accepted source evidence creation",
            r"\bcreate_accepted_source_evidence\s*\(",
        ),
    ],
    "forbid_connector_binding": [
        (
            "connector semantic binding call",
            r"\bbind_connector_semantic(?:s)?\s*\(",
        ),
        (
            "connector semantic value assignment",
            r"\bconnector_semantic_value\s*=",
        ),
        ("connector bound state", r"\bCONNECTOR_SEMANTIC_BOUND\b"),
    ],
    "forbid_private_state_fetch": [
        ("private state fetch call", r"\bfetch_private_state\s*\("),
        ("private state client", r"\bprivate_state_client\b"),
        ("account balance fetch call", r"\bget_account_balance\s*\("),
    ],
    "forbid_order_execution": [
        (
            "order execution call",
            r"\b(?:place|submit|send|cancel|reduce|close)_order\s*\(",
        ),
        ("order execution endpoint", r"[\"']/orders?/(?:submit|cancel|reduce|close)[\"']"),
        ("live order execution toggle", r"\bLIVE_ORDER_EXECUTION_ENABLED\s*=\s*True\b"),
    ],
    "forbid_neural_training": [
        ("model training call", r"\b(?:train|fit)_model\s*\("),
        ("torch optimizer import/use", r"\btorch\.optim\b"),
        ("tensorflow import/use", r"\b(?:tensorflow|keras)\b"),
    ],
    "forbid_neural_inference": [
        ("model predict call", r"\b(?:model|estimator)\.predict\s*\("),
        ("inference call", r"\brun_inference\s*\("),
        ("torch model load", r"\btorch\.load\s*\("),
        ("onnx runtime import/use", r"\bonnxruntime\b"),
    ],
    "forbid_external_repo_clone": [
        ("git clone command", r"\bgit\s+clone\b"),
        ("GitPython clone call", r"\bRepo\.clone_from\s*\("),
        (
            "subprocess git clone",
            r"\bsubprocess\.(?:run|check_call|check_output)\([^)]*\bgit\b[^)]*\bclone\b",
        ),
    ],
    "forbid_package_install_scripts": [
        ("pip install command", r"\b(?:python\s+-m\s+)?pip\s+install\b"),
        ("uv pip install command", r"\buv\s+pip\s+install\b"),
        ("npm install command", r"\bnpm\s+install\b"),
        ("pnpm install command", r"\bpnpm\s+install\b"),
        ("yarn install command", r"\byarn\s+(?:add|install)\b"),
        ("poetry install command", r"\bpoetry\s+install\b"),
        ("conda install command", r"\bconda\s+install\b"),
    ],
}


@dataclass(frozen=True)
class ScanOptions:
    forbid_source_retrieval: bool = False
    forbid_source_acceptance: bool = False
    forbid_connector_binding: bool = False
    forbid_private_state_fetch: bool = False
    forbid_order_execution: bool = False
    forbid_neural_training: bool = False
    forbid_neural_inference: bool = False
    forbid_external_repo_clone: bool = False
    forbid_package_install_scripts: bool = False


def _part_key(part: str) -> str:
    return re.sub(r"[-\s]+", "_", part.lower())


def _rel_path(path: pathlib.Path, root: pathlib.Path) -> pathlib.PurePosixPath:
    return pathlib.PurePosixPath(path.relative_to(root).as_posix())


def _iter_paths(root: pathlib.Path) -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_PARTS]
        current_dir = pathlib.Path(dirpath)
        paths.extend(current_dir / name for name in dirnames)
        paths.extend(current_dir / name for name in filenames)
    return sorted(paths, key=lambda item: item.as_posix().lower())


def _enabled_flags(options: ScanOptions) -> list[str]:
    return [
        field
        for field in ScanOptions.__dataclass_fields__
        if getattr(options, field)
    ]


def _should_scan_content(path: pathlib.Path, root: pathlib.Path) -> bool:
    rel = _rel_path(path, root)
    if rel in SKIP_CONTENT_PATHS:
        return False
    if rel.parts and rel.parts[0] in SKIP_CONTENT_TOP_LEVEL_DIRS:
        return False
    return path.is_file() and path.suffix.lower() in TEXT_SUFFIXES


def scan_repository(root: pathlib.Path, options: ScanOptions) -> list[str]:
    root = root.resolve()
    violations: list[str] = []
    enabled_flags = _enabled_flags(options)

    for path in _iter_paths(root):
        rel = _rel_path(path, root)
        name = path.name
        lower_name = name.lower()
        part_keys = {_part_key(part) for part in rel.parts}

        if name in FORBIDDEN_NAMES or lower_name in {item.lower() for item in FORBIDDEN_NAMES}:
            violations.append(f"forbidden runtime/secret artifact present: {rel}")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append(f"forbidden secret-like file present: {rel}")
        if ALWAYS_FORBIDDEN_PATH_PARTS.intersection(part_keys):
            violations.append(f"forbidden runtime path present: {rel}")

        for flag in enabled_flags:
            forbidden_parts = FLAG_FORBIDDEN_PATH_PARTS.get(flag, set())
            if forbidden_parts.intersection(part_keys):
                violations.append(f"forbidden {flag.replace('_', '-')} path present: {rel}")

        if (
            options.forbid_package_install_scripts
            and path.is_file()
            and lower_name in PACKAGE_INSTALL_SCRIPT_NAMES
        ):
            violations.append(f"forbidden package install script present: {rel}")

        if not _should_scan_content(path, root):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for flag in enabled_flags:
            for label, pattern in CONTENT_PATTERNS.get(flag, []):
                if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                    violations.append(f"forbidden {label} in {rel}")

    return violations


def options_from_args(args: argparse.Namespace) -> ScanOptions:
    return ScanOptions(
        forbid_source_retrieval=args.forbid_source_retrieval,
        forbid_source_acceptance=args.forbid_source_acceptance,
        forbid_connector_binding=args.forbid_connector_binding,
        forbid_private_state_fetch=args.forbid_private_state_fetch,
        forbid_order_execution=args.forbid_order_execution,
        forbid_neural_training=args.forbid_neural_training,
        forbid_neural_inference=args.forbid_neural_inference,
        forbid_external_repo_clone=args.forbid_external_repo_clone,
        forbid_package_install_scripts=args.forbid_package_install_scripts,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--forbid-source-retrieval", action="store_true")
    parser.add_argument("--forbid-source-acceptance", action="store_true")
    parser.add_argument("--forbid-connector-binding", action="store_true")
    parser.add_argument("--forbid-private-state-fetch", action="store_true")
    parser.add_argument("--forbid-order-execution", action="store_true")
    parser.add_argument("--forbid-neural-training", action="store_true")
    parser.add_argument("--forbid-neural-inference", action="store_true")
    parser.add_argument("--forbid-external-repo-clone", action="store_true")
    parser.add_argument("--forbid-package-install-scripts", action="store_true")
    args = parser.parse_args()

    violations = scan_repository(pathlib.Path(args.repo_root), options_from_args(args))
    if violations:
        raise SystemExit("NO_RUNTIME_ARTIFACT_GATE_FAILED\n- " + "\n- ".join(violations))
    print("NO_RUNTIME_ARTIFACT_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
