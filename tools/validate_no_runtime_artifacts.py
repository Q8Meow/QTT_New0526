#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import os
import pathlib
import re
import sys
import time
from typing import Callable

FORBIDDEN_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
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
    "dual_result_review",
    "live_connectors",
    "owner_live_promotion_review",
    "runtime_resolver",
    "runtime_resolver_snapshot",
    "runtime_services",
    "telegram_runtime",
    "three_venue_canary_eligibility",
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
STATIC_RUNTIME_RESOLVER_ALLOWED_PATHS = {
    pathlib.PurePosixPath("schemas/runtime_resolver"),
    pathlib.PurePosixPath("schemas/runtime_resolver/runtime_resolver.schema.json"),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_snapshot_input_lock.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_snapshot_manifest.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_consumer_contract.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver/"
        "stage1_runtime_resolver_snapshot_gate_report.schema.json"
    ),
    pathlib.PurePosixPath("tests/fixtures/runtime_resolver"),
    pathlib.PurePosixPath(
        "tests/fixtures/runtime_resolver/"
        "synthetic_runtime_resolver_source_required_disabled.v1.fixture.json"
    ),
    pathlib.PurePosixPath("tests/fixtures/source_evidence/runtime_resolver"),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/runtime_resolver/"
        "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
    ),
    pathlib.PurePosixPath("tests/runtime_resolver"),
    pathlib.PurePosixPath("tests/runtime_resolver/__init__.py"),
    pathlib.PurePosixPath(
        "tests/runtime_resolver/test_runtime_resolver_schema_surface.py"
    ),
    pathlib.PurePosixPath(
        "tests/runtime_resolver/test_runtime_resolver_source_required_fixture.py"
    ),
}
STATIC_RUNTIME_RESOLVER_SNAPSHOT_ALLOWED_PATHS = {
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
        "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
        "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
        "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
    ),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/runtime_resolver_snapshot"
    ),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/runtime_resolver_snapshot/"
        "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
    ),
}
STATIC_DUAL_RESULT_REVIEW_ALLOWED_PATHS = {
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/dual_result_review"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/dual_result_review/"
        "stage1_dual_result_review_input_contract.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/dual_result_review/"
        "stage1_replay_paper_comparison_matrix.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/dual_result_review/"
        "stage1_dual_result_review_gate_report.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/dual_result_review/"
        "stage1_owner_live_promotion_handoff_block.schema.json"
    ),
    pathlib.PurePosixPath("tests/fixtures/source_evidence/dual_result_review"),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/dual_result_review/"
        "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
    ),
}
STATIC_OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PATHS = {
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/owner_live_promotion_review"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
        "stage1_owner_live_promotion_review_input_contract.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
        "stage1_owner_approval_receipt_boundary.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
        "stage1_owner_live_promotion_review_gate_report.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
        "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
    ),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/owner_live_promotion_review"
    ),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/owner_live_promotion_review/"
        "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
    ),
}
STATIC_THREE_VENUE_CANARY_ELIGIBILITY_ALLOWED_PATHS = {
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
        "stage1_three_venue_canary_eligibility_input_contract.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
        "stage1_three_venue_platform_readiness_matrix.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
        "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
        "stage1_three_venue_canary_eligibility_gate_report.schema.json"
    ),
    pathlib.PurePosixPath(
        "src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/"
        "stage1_limited_live_canary_execution_block.schema.json"
    ),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/three_venue_canary_eligibility"
    ),
    pathlib.PurePosixPath(
        "tests/fixtures/source_evidence/three_venue_canary_eligibility/"
        "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
    ),
}
LOCAL_VISUAL_QA_BROWSER_AUTOMATION_ALLOWED_PATHS = {
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r1_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r1_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r2_visual_smoke.py"),
}
FORBIDDEN_RUNTIME_RESOLVER_ARTIFACT_NAMES = {
    "dual_result_review.packet.json",
    "dual_result_review_runtime.py",
    "live_snapshot.py",
    "live_promotion.py",
    "live_reachability.json",
    "merged_replay_paper_result.json",
    "order_execution.py",
    "owner_approval_receipt.json",
    "owner_live_promotion_review.packet.json",
    "owner_live_promotion_review_runtime.py",
    "profit_claim.json",
    "live_handoff.py",
    "limited_live_canary_execution.py",
    "paper_execution.py",
    "paper_result_packet.json",
    "replay_input_snapshot.json",
    "replay_execution.py",
    "replay_result_packet.json",
    "resolver_runtime.py",
    "runtime_resolver_snapshot.input_lock.json",
    "runtime_resolver_snapshot.packet.json",
    "runtime_snapshot.py",
    "runtime_cash_receipt.json",
    "runtime_resolver_to_replay_paper_runtime.py",
    "stage1runtimeresolversnapshot.input_lock.json",
    "stage1runtimeresolversnapshot.packet.json",
    "three_venue_canary_eligibility.packet.json",
    "three_venue_canary_eligibility_runtime.py",
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
PACKAGE_INSTALL_TEXT_SUFFIXES = TEXT_SUFFIXES | {".md", ".rst", ".txt"}
NO_RUNTIME_PROGRESS_INTERVAL_SECONDS = 30.0
SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    ".coverage",
    ".hypothesis",
    ".mypy_cache",
    ".nox",
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
SKIP_FILE_NAMES = {
    ".coverage",
    "coverage.xml",
    "junit.xml",
}
SKIP_CONTENT_PATHS = {
    pathlib.PurePosixPath("tools/validate_no_runtime_artifacts.py"),
}
SKIP_CONTENT_TOP_LEVEL_DIRS = {"docs"}
PACKAGE_INSTALL_SCAN_CONTENT_SKIP_DIR_SUFFIXES = ("_shards",)
PACKAGE_INSTALL_LINE_HINTS = (
    "pip",
    "uv ",
    "npm ",
    "pnpm ",
    "yarn ",
    "poetry ",
    "conda ",
)

# CI_TEST_DEPENDENCY_ALLOWLIST is the only package-install exception: CI may
# install pytest before running the repository's canonical validation gates.
CI_TEST_DEPENDENCY_ALLOWLIST = {
    pathlib.PurePosixPath(".github/workflows/qtt_validation.yml"): (
        "python -m pip install pytest"
    ),
}

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


@dataclass
class ScanStats:
    visited_paths: int = 0
    skipped_paths: int = 0
    content_files_scanned: int = 0
    package_text_files_scanned: int = 0
    package_text_files_skipped: int = 0
    violations: int = 0


def _part_key(part: str) -> str:
    return re.sub(r"[-\s]+", "_", part.lower())


def _rel_path(path: pathlib.Path, root: pathlib.Path) -> pathlib.PurePosixPath:
    return pathlib.PurePosixPath(path.relative_to(root).as_posix())


def _is_allowed_static_connector_binding_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_CONNECTOR_BINDING_ALLOWED_PATHS


def _is_allowed_static_runtime_resolver_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_RUNTIME_RESOLVER_ALLOWED_PATHS


def _is_allowed_static_runtime_resolver_snapshot_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_RUNTIME_RESOLVER_SNAPSHOT_ALLOWED_PATHS


def _is_allowed_static_dual_result_review_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_DUAL_RESULT_REVIEW_ALLOWED_PATHS


def _is_allowed_static_owner_live_promotion_review_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_OWNER_LIVE_PROMOTION_REVIEW_ALLOWED_PATHS


def _is_allowed_static_three_venue_canary_eligibility_contract_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in STATIC_THREE_VENUE_CANARY_ELIGIBILITY_ALLOWED_PATHS


def _is_allowed_local_visual_qa_browser_automation_path(
    rel: pathlib.PurePosixPath,
) -> bool:
    return rel in LOCAL_VISUAL_QA_BROWSER_AUTOMATION_ALLOWED_PATHS


def _content_label_allowed_for_path(
    rel: pathlib.PurePosixPath,
    label: str,
) -> bool:
    return (
        label == "browser retrieval automation"
        and _is_allowed_local_visual_qa_browser_automation_path(rel)
    )


def _is_allowed_always_forbidden_path(
    rel: pathlib.PurePosixPath,
    part_keys: set[str],
) -> bool:
    forbidden_parts = ALWAYS_FORBIDDEN_PATH_PARTS.intersection(part_keys)
    if forbidden_parts == {"dual_result_review"}:
        return _is_allowed_static_dual_result_review_contract_path(rel)
    if forbidden_parts == {"owner_live_promotion_review"}:
        return _is_allowed_static_owner_live_promotion_review_contract_path(rel)
    if forbidden_parts == {"runtime_resolver"}:
        return _is_allowed_static_runtime_resolver_contract_path(rel)
    if forbidden_parts == {"runtime_resolver_snapshot"}:
        return _is_allowed_static_runtime_resolver_snapshot_contract_path(rel)
    if forbidden_parts == {"three_venue_canary_eligibility"}:
        return _is_allowed_static_three_venue_canary_eligibility_contract_path(rel)
    return False


def _iter_paths(root: pathlib.Path) -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_PARTS]
        current_dir = pathlib.Path(dirpath)
        paths.extend(current_dir / name for name in dirnames)
        paths.extend(current_dir / name for name in filenames if name not in SKIP_FILE_NAMES)
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


def _is_generated_report_shard_payload_path(rel: pathlib.PurePosixPath) -> bool:
    return (
        len(rel.parts) >= 4
        and rel.parts[:3] == ("docs", "master_plan", "generated")
        and any(
            part.endswith(PACKAGE_INSTALL_SCAN_CONTENT_SKIP_DIR_SUFFIXES)
            for part in rel.parts[3:-1]
        )
    )


def _should_scan_package_install_text(path: pathlib.Path, root: pathlib.Path) -> bool:
    rel = _rel_path(path, root)
    if rel in SKIP_CONTENT_PATHS:
        return False
    if _is_generated_report_shard_payload_path(rel):
        return False
    return (
        rel.parts
        and rel.parts[0] in {"docs", "tests"}
        and path.is_file()
        and path.suffix.lower() in PACKAGE_INSTALL_TEXT_SUFFIXES
    )


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
        if not _content_label_allowed_for_path(path, label)
    ]


def _matched_line(text: str, match: re.Match[str]) -> str:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()


def _is_ci_test_dependency_allowlisted_pip_install(
    path: pathlib.PurePosixPath,
    text: str,
    match: re.Match[str],
    allowlist_hits: dict[pathlib.PurePosixPath, int],
) -> bool:
    allowed_command = CI_TEST_DEPENDENCY_ALLOWLIST.get(path)
    if allowed_command is None:
        return False
    if _matched_line(text, match) != allowed_command:
        return False

    allowlist_hits[path] = allowlist_hits.get(path, 0) + 1
    return allowlist_hits[path] == 1


def _scan_text_content(
    path: pathlib.PurePosixPath, text: str, enabled_flags: list[str]
) -> list[str]:
    violations: list[str] = []
    ci_test_dependency_allowlist_hits: dict[pathlib.PurePosixPath, int] = {}
    for flag in enabled_flags:
        for label, pattern in CONTENT_PATTERNS.get(flag, []):
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
            if not matches:
                continue
            if flag == "forbid_package_install_scripts" and label == "pip install command":
                forbidden_matches = [
                    match
                    for match in matches
                    if not _is_ci_test_dependency_allowlisted_pip_install(
                        path,
                        text,
                        match,
                        ci_test_dependency_allowlist_hits,
                    )
                ]
                if forbidden_matches:
                    violations.append(f"forbidden {label} in {path}")
                continue

            if matches and not _content_label_allowed_for_path(path, label):
                violations.append(f"forbidden {label} in {path}")
    return violations


def _line_might_contain_package_install(line: str) -> bool:
    lower = line.lower()
    return any(hint in lower for hint in PACKAGE_INSTALL_LINE_HINTS)


def _scan_package_install_text_file(
    path: pathlib.PurePosixPath,
    source_path: pathlib.Path,
) -> list[str]:
    violations: list[str] = []
    ci_test_dependency_allowlist_hits: dict[pathlib.PurePosixPath, int] = {}
    try:
        lines = source_path.open(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"unable to scan package install text in {path}: {exc.__class__.__name__}"]
    with lines:
        for line in lines:
            if not _line_might_contain_package_install(line):
                continue
            for label, pattern in CONTENT_PATTERNS["forbid_package_install_scripts"]:
                match = re.search(pattern, line, flags=re.IGNORECASE | re.MULTILINE)
                if not match:
                    continue
                if label == "pip install command" and _is_ci_test_dependency_allowlisted_pip_install(
                    path,
                    line,
                    match,
                    ci_test_dependency_allowlist_hits,
                ):
                    continue
                violations.append(f"forbidden {label} in {path}")
                return violations
    return violations


def _progress_receipt(
    progress: Callable[[str], None] | None,
    message: str,
) -> None:
    if progress is not None:
        progress(message)


def scan_repository(
    root: pathlib.Path,
    options: ScanOptions,
    *,
    progress: Callable[[str], None] | None = None,
    progress_interval_seconds: float = NO_RUNTIME_PROGRESS_INTERVAL_SECONDS,
) -> list[str]:
    root = root.resolve()
    violations: list[str] = []
    enabled_flags = _enabled_flags(options)
    stats = ScanStats()
    started = time.perf_counter()
    last_progress = started

    _progress_receipt(
        progress,
        f"NO_RUNTIME_ARTIFACT_SCAN_START root={root}",
    )
    paths = _iter_paths(root)
    _progress_receipt(
        progress,
        "NO_RUNTIME_ARTIFACT_SCAN_SCOPE "
        f"path_count={len(paths)} "
        f"elapsed_seconds={time.perf_counter() - started:.3f}",
    )

    def maybe_progress(force: bool = False) -> None:
        nonlocal last_progress
        if progress is None:
            return
        now = time.perf_counter()
        if not force and now - last_progress < progress_interval_seconds:
            return
        last_progress = now
        _progress_receipt(
            progress,
            "NO_RUNTIME_ARTIFACT_SCAN_PROGRESS "
            f"visited_paths={stats.visited_paths} "
            f"skipped_paths={stats.skipped_paths} "
            f"content_files_scanned={stats.content_files_scanned} "
            f"package_text_files_scanned={stats.package_text_files_scanned} "
            f"package_text_files_skipped={stats.package_text_files_skipped} "
            f"violations={len(violations)} "
            f"elapsed_seconds={now - started:.3f}",
        )

    for path in paths:
        stats.visited_paths += 1
        rel = _rel_path(path, root)
        name = path.name
        lower_name = name.lower()
        part_keys = {_part_key(part) for part in rel.parts}

        if name in FORBIDDEN_NAMES or lower_name in {item.lower() for item in FORBIDDEN_NAMES}:
            violations.append(f"forbidden runtime/secret artifact present: {rel}")
        if lower_name in FORBIDDEN_RUNTIME_RESOLVER_ARTIFACT_NAMES:
            violations.append(f"forbidden runtime resolver artifact present: {rel}")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append(f"forbidden secret-like file present: {rel}")
        if ALWAYS_FORBIDDEN_PATH_PARTS.intersection(part_keys) and not (
            _is_allowed_always_forbidden_path(rel, part_keys)
        ):
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
            if options.forbid_package_install_scripts and _should_scan_package_install_text(
                path,
                root,
            ):
                stats.package_text_files_scanned += 1
                violations.extend(_scan_package_install_text_file(rel, path))
            else:
                stats.skipped_paths += 1
                if (
                    options.forbid_package_install_scripts
                    and path.is_file()
                    and path.suffix.lower() in PACKAGE_INSTALL_TEXT_SUFFIXES
                    and _is_generated_report_shard_payload_path(rel)
                ):
                    stats.package_text_files_skipped += 1
            maybe_progress()
            continue

        stats.content_files_scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".py":
            violations.extend(_scan_python_content(rel, text, enabled_flags))
        else:
            violations.extend(_scan_text_content(rel, text, enabled_flags))
        maybe_progress()

    stats.violations = len(violations)
    _progress_receipt(
        progress,
        "NO_RUNTIME_ARTIFACT_SCAN_DONE "
        f"visited_paths={stats.visited_paths} "
        f"skipped_paths={stats.skipped_paths} "
        f"content_files_scanned={stats.content_files_scanned} "
        f"package_text_files_scanned={stats.package_text_files_scanned} "
        f"package_text_files_skipped={stats.package_text_files_skipped} "
        f"violations={stats.violations} "
        f"elapsed_seconds={time.perf_counter() - started:.3f}",
    )
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
    parser.add_argument(
        "--progress-interval-seconds",
        type=float,
        default=NO_RUNTIME_PROGRESS_INTERVAL_SECONDS,
    )
    args = parser.parse_args()

    violations = scan_repository(
        pathlib.Path(args.repo_root),
        options_from_args(args),
        progress=lambda message: print(message, file=sys.stderr, flush=True),
        progress_interval_seconds=args.progress_interval_seconds,
    )
    if violations:
        raise SystemExit("NO_RUNTIME_ARTIFACT_GATE_FAILED\n- " + "\n- ".join(violations))
    print("NO_RUNTIME_ARTIFACT_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
