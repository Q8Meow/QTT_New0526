#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
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
STATIC_CONNECTOR_BINDING_ALLOWED_PATHS = {
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/connector_semantic_binding"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
        "stage1_connector_semantic_binding_ledger_record.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
        "stage1_connector_semantic_value_canonicalization.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
        "stage1_connector_semantic_binding_consumer_contract.schema.json"
    ),
    pathlib.PurePosixPath("tests/fixtures/source_evidence/connector_semantic_binding"),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/connector_semantic_binding/"
        "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
    ),
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
SKIP_CONTENT_TOP_LEVEL_DIRS = {"docs"}

CONTENT_PATTERNS = {
    "forbid_source_retrieval": [
        ("HTTP retrieval client", r"\b(?:requests|httpx)\.(?:get|post|request)\s*\("),
        (
            "HTTP retrieval session client",
            r"\brequests\.Session\s*\(\s*\)\s*\.\s*(?:get|post|request)\s*\(",
        ),
        ("urllib retrieval client", r"\burllib\.request\.urlopen\s*\("),
        ("http.client import/use", r"\bhttp\.client\b"),
        ("socket client", r"\bsocket\.socket\s*\("),
        ("urllib3 client", r"\burllib3\b"),
        ("aiohttp client", r"\baiohttp\.ClientSession\b"),
        ("browser retrieval automation", r"\b(?:playwright|selenium)\b"),
        (
            "curl command",
            r"\bsubprocess\.(?:run|check_call|check_output)\([^)]*[\"']curl[\"']",
        ),
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
        (
            "subprocess pip install command",
            r"\bsubprocess\.(?:run|check_call|check_output)\([^)]*[\"'](?:pip|pip3)[\"'][^)]*[\"']install[\"']",
        ),
        (
            "pip install command",
            r"\b(?:(?:python|python3|py)\s+-m\s+)?pip3?\s+install\b",
        ),
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


def _is_allowed_static_connector_binding_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_CONNECTOR_BINDING_ALLOWED_PATHS


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
    if rel.parts and rel.parts[0] == "tests" and path.suffix.lower() != ".py":
        return False
    return path.is_file() and path.suffix.lower() in TEXT_SUFFIXES


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        base = _dotted_name(node.func)
        return f"{base}()" if base else None
    return None


def _imported_module_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module]
    return []


def _literal_command_tokens(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple)):
        tokens: list[str] = []
        for item in node.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                return []
            tokens.append(item.value.lower())
        return tokens
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.lower().split()
    return []


def _tokens_are_pip_install(tokens: list[str]) -> bool:
    if len(tokens) >= 2 and tokens[0] in {"pip", "pip3"} and tokens[1] == "install":
        return True
    return (
        len(tokens) >= 4
        and tokens[0] in {"python", "python3", "py"}
        and tokens[1:4] == ["-m", "pip", "install"]
    )


def _call_labels(node: ast.Call) -> list[str]:
    labels: list[str] = []
    name = _dotted_name(node.func)
    if name is None:
        return labels

    if name in {
        "requests.get",
        "requests.post",
        "requests.request",
        "httpx.get",
        "httpx.post",
        "httpx.request",
    }:
        labels.append("HTTP retrieval client")
    if name in {
        "requests.Session().get",
        "requests.Session().post",
        "requests.Session().request",
    }:
        labels.append("HTTP retrieval session client")
    if name == "urllib.request.urlopen":
        labels.append("urllib retrieval client")
    if name == "http.client.HTTPConnection" or name == "http.client.HTTPSConnection":
        labels.append("http.client import/use")
    if name == "socket.socket":
        labels.append("socket client")
    if name == "aiohttp.ClientSession":
        labels.append("aiohttp client")
    if name in {"Repo.clone_from", "git.Repo.clone_from"}:
        labels.append("GitPython clone call")

    call_name = name.rsplit(".", 1)[-1]
    if call_name in {
        "accept_source_fact",
        "accept_source_evidence",
        "accept_source_packet",
        "accepted_source_fact",
        "accepted_source_evidence",
        "accepted_source_packet",
    }:
        labels.append("source acceptance call")
    if call_name == "create_accepted_source_evidence":
        labels.append("accepted source evidence creation")
    if call_name in {"bind_connector_semantic", "bind_connector_semantics"}:
        labels.append("connector semantic binding call")
    if call_name == "fetch_private_state":
        labels.append("private state fetch call")
    if call_name == "get_account_balance":
        labels.append("account balance fetch call")
    if call_name in {
        "place_order",
        "submit_order",
        "send_order",
        "cancel_order",
        "reduce_order",
        "close_order",
    }:
        labels.append("order execution call")
    if call_name in {"train_model", "fit_model"}:
        labels.append("model training call")
    if name.endswith(".predict"):
        labels.append("model predict call")
    if call_name == "run_inference":
        labels.append("inference call")
    if name == "torch.load":
        labels.append("torch model load")

    if name in {"subprocess.run", "subprocess.check_call", "subprocess.check_output"} and node.args:
        tokens = _literal_command_tokens(node.args[0])
        if tokens:
            if tokens[0] == "git" and "clone" in tokens:
                labels.append("subprocess git clone")
            if tokens[0] == "curl":
                labels.append("curl command")
            if _tokens_are_pip_install(tokens):
                labels.append("subprocess pip install command")
    return labels


def _assignment_labels(node: ast.Assign | ast.AnnAssign) -> list[str]:
    labels: list[str] = []
    targets: list[ast.AST]
    value: ast.AST | None
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
        value = node.value
    else:
        targets = [node.target]
        value = node.value

    target_names = {
        name
        for target in targets
        if (name := _dotted_name(target)) is not None
    }
    if "connector_semantic_value" in target_names:
        labels.append("connector semantic value assignment")
    if "source_acceptance_status" in target_names and isinstance(value, ast.Constant):
        if value.value == "ACCEPTED":
            labels.append("accepted source status assignment")
    if "LIVE_ORDER_EXECUTION_ENABLED" in target_names and isinstance(value, ast.Constant):
        if value.value is True:
            labels.append("live order execution toggle")
    return labels


def _scan_python_content(path: pathlib.Path, text: str, enabled_flags: list[str]) -> list[str]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return _scan_text_content(path, text, enabled_flags)

    found_by_flag = {flag: set[str]() for flag in enabled_flags}
    source_retrieval_imports = {
        "http.client": "http.client import/use",
        "urllib3": "urllib3 client",
        "playwright": "browser retrieval automation",
        "selenium": "browser retrieval automation",
    }
    neural_training_imports = {
        "tensorflow": "tensorflow import/use",
        "keras": "tensorflow import/use",
    }
    neural_inference_imports = {
        "onnxruntime": "onnx runtime import/use",
    }

    for node in ast.walk(tree):
        for module_name in _imported_module_names(node):
            root_name = module_name.split(".", 1)[0]
            if "forbid_source_retrieval" in found_by_flag:
                if module_name in source_retrieval_imports:
                    found_by_flag["forbid_source_retrieval"].add(source_retrieval_imports[module_name])
                if root_name in source_retrieval_imports:
                    found_by_flag["forbid_source_retrieval"].add(source_retrieval_imports[root_name])
            if "forbid_neural_training" in found_by_flag and root_name in neural_training_imports:
                found_by_flag["forbid_neural_training"].add(neural_training_imports[root_name])
            if "forbid_neural_inference" in found_by_flag and root_name in neural_inference_imports:
                found_by_flag["forbid_neural_inference"].add(neural_inference_imports[root_name])

        if isinstance(node, ast.Call):
            labels = set(_call_labels(node))
            flag_to_labels = {
                "forbid_source_retrieval": {
                    "HTTP retrieval client",
                    "HTTP retrieval session client",
                    "urllib retrieval client",
                    "http.client import/use",
                    "socket client",
                    "urllib3 client",
                    "aiohttp client",
                    "browser retrieval automation",
                    "curl command",
                },
                "forbid_source_acceptance": {
                    "source acceptance call",
                    "accepted source evidence creation",
                },
                "forbid_connector_binding": {
                    "connector semantic binding call",
                },
                "forbid_private_state_fetch": {
                    "private state fetch call",
                    "account balance fetch call",
                },
                "forbid_order_execution": {
                    "order execution call",
                },
                "forbid_neural_training": {
                    "model training call",
                },
                "forbid_neural_inference": {
                    "model predict call",
                    "inference call",
                    "torch model load",
                },
                "forbid_external_repo_clone": {
                    "GitPython clone call",
                    "subprocess git clone",
                },
                "forbid_package_install_scripts": {
                    "subprocess pip install command",
                },
            }
            for flag, flag_labels in flag_to_labels.items():
                if flag in found_by_flag:
                    found_by_flag[flag].update(labels & flag_labels)

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            labels = set(_assignment_labels(node))
            if "forbid_source_acceptance" in found_by_flag:
                found_by_flag["forbid_source_acceptance"].update(
                    labels & {"accepted source status assignment"}
                )
            if "forbid_connector_binding" in found_by_flag:
                found_by_flag["forbid_connector_binding"].update(
                    labels & {"connector semantic value assignment"}
                )
            if "forbid_order_execution" in found_by_flag:
                found_by_flag["forbid_order_execution"].update(
                    labels & {"live order execution toggle"}
                )

        if isinstance(node, ast.Attribute):
            name = _dotted_name(node)
            if "forbid_neural_training" in found_by_flag and name == "torch.optim":
                found_by_flag["forbid_neural_training"].add("torch optimizer import/use")
            if "forbid_neural_inference" in found_by_flag and name == "onnxruntime":
                found_by_flag["forbid_neural_inference"].add("onnx runtime import/use")

        if isinstance(node, ast.Name):
            if "forbid_private_state_fetch" in found_by_flag and node.id == "private_state_client":
                found_by_flag["forbid_private_state_fetch"].add("private state client")
            if "forbid_connector_binding" in found_by_flag and node.id == "CONNECTOR_SEMANTIC_BOUND":
                found_by_flag["forbid_connector_binding"].add("connector bound state")

    return [
        f"forbidden {label} in {path}"
        for flag in enabled_flags
        for label in sorted(found_by_flag.get(flag, set()))
    ]


def _scan_text_content(path: pathlib.Path, text: str, enabled_flags: list[str]) -> list[str]:
    violations: list[str] = []
    for flag in enabled_flags:
        for label, pattern in CONTENT_PATTERNS.get(flag, []):
            if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                violations.append(f"forbidden {label} in {path}")
    return violations


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
            if (
                forbidden_parts.intersection(part_keys)
                and not (
                    flag == "forbid_connector_binding"
                    and _is_allowed_static_connector_binding_contract_path(rel)
                )
            ):
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
        if path.suffix.lower() == ".py":
            violations.extend(_scan_python_content(rel, text, enabled_flags))
        else:
            violations.extend(_scan_text_content(rel, text, enabled_flags))

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
