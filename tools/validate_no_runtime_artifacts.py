#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Callable

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

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
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r3_visual_smoke.py"),
    pathlib.PurePosixPath("tools/playwright_pr169_dash1_ui1_r2_r4_visual_smoke.py"),
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
LOCAL_CUSTODY_GIT_TIMEOUT_SECONDS = 10.0
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
TOP_LEVEL_LOCAL_CUSTODY_DIR_NAMES = frozenset({".codex_inputs", ".qtt"})
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
# install one exact approved pytest dependency before running the repository's
# canonical validation gates.
CI_TEST_DEPENDENCY_ALLOWLIST = {
    pathlib.PurePosixPath(".github/workflows/qtt_validation.yml"): frozenset(
        {
            "python -m pip install pytest",
            "python -m pip install pytest==9.1.1",
        }
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


def _validate_top_level_codex_custody_boundary(
    root: pathlib.Path,
) -> tuple[list[str], frozenset[str]]:
    root = root.resolve()
    custody_name = ".codex_inputs"
    custody_root = root / custody_name
    if not custody_root.exists():
        return [], frozenset()

    # Isolated synthetic roots are not repositories and must not cause Git to
    # search a parent checkout. Only an immediate Git marker authorizes the
    # bounded repository-local custody queries below.
    if not (root / ".git").exists():
        return [], frozenset()

    def run_git(
        operation: str,
        argv: list[str],
    ) -> tuple[subprocess.CompletedProcess[bytes] | None, str | None]:
        try:
            completed = subprocess.run(
                ["git", *argv],
                cwd=root,
                check=False,
                capture_output=True,
                text=False,
                shell=False,
                timeout=LOCAL_CUSTODY_GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None, f"LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: {operation}"
        return completed, None

    worktree, error = run_git("worktree-detection", ["rev-parse", "--show-toplevel"])
    if error is not None or worktree is None:
        return [error or "LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: worktree-detection"], frozenset()
    if worktree.returncode != 0:
        return ["LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: worktree-detection"], frozenset()
    try:
        worktree_root = pathlib.Path(
            worktree.stdout.decode("utf-8", errors="replace").strip()
        ).resolve()
    except (OSError, ValueError):
        return ["LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: worktree-detection"], frozenset()
    if worktree_root != root:
        return ["LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: worktree-detection"], frozenset()

    tracked, error = run_git(
        "tracked-path-query",
        ["ls-files", "-z", "--", custody_name],
    )
    if error is not None or tracked is None:
        return [error or "LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: tracked-path-query"], frozenset()
    if tracked.returncode != 0:
        return ["LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: tracked-path-query"], frozenset()
    tracked_paths = sorted(
        {
            pathlib.PurePosixPath(
                entry.decode("utf-8", errors="replace").replace("\\", "/")
            ).as_posix()
            for entry in tracked.stdout.split(b"\0")
            if entry
        },
        key=lambda path: (path.casefold(), path),
    )
    if tracked_paths:
        return [
            f"TRACKED_PATH_INSIDE_LOCAL_CUSTODY: {path}"
            for path in tracked_paths
        ], frozenset()

    ignored, error = run_git(
        "ignore-check",
        ["check-ignore", "--quiet", "--", custody_name],
    )
    if error is not None or ignored is None:
        return [error or "LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: ignore-check"], frozenset()
    if ignored.returncode == 0:
        return [], frozenset({custody_name})
    if ignored.returncode == 1:
        return [f"TOP_LEVEL_LOCAL_CUSTODY_NOT_IGNORED: {custody_name}"], frozenset()
    return ["LOCAL_CUSTODY_GIT_STATUS_UNAVAILABLE: ignore-check"], frozenset()


def _validate_top_level_local_custody_boundary(
    root: pathlib.Path,
) -> tuple[list[str], frozenset[str]]:
    failures, admitted = _validate_top_level_codex_custody_boundary(root)
    local = root / ".qtt"
    if os.path.lexists(local):
        from tools.validation_reliability import _require_local_layout
        try:
            _require_local_layout(root.resolve())
        except (OSError, ValueError, RuntimeError) as exc:
            return [*failures, f"REPOSITORY_LOCAL_LAYOUT_REJECTED: {exc}"], admitted
        admitted = admitted | frozenset({".qtt"})
    return failures, admitted


def _should_exclude_directory_from_scan(
    *,
    root: pathlib.Path,
    current_dir: pathlib.Path,
    directory_name: str,
    excluded_top_level_local_custody_dir_names: frozenset[str],
) -> bool:
    if directory_name in SKIP_DIR_PARTS:
        return True
    return (
        current_dir == root
        and directory_name in TOP_LEVEL_LOCAL_CUSTODY_DIR_NAMES
        and directory_name in excluded_top_level_local_custody_dir_names
    )


def _iter_paths(
    root: pathlib.Path,
    *,
    excluded_top_level_local_custody_dir_names: frozenset[str] = frozenset(),
) -> list[pathlib.Path]:
    root = root.resolve()
    paths: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = pathlib.Path(dirpath)
        dirnames[:] = [
            name
            for name in dirnames
            if not _should_exclude_directory_from_scan(
                root=root,
                current_dir=current_dir,
                directory_name=name,
                excluded_top_level_local_custody_dir_names=(
                    excluded_top_level_local_custody_dir_names
                ),
            )
        ]
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
    if name == "websockets.sync.client.connect":
        labels.append("websocket client")
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


_F14_NATIVE_OWNER = 'src/qtt/stage1_prediction_markets/private_state_receipts/request.py'
_F14_NATIVE_TRANSPORT_TEMPLATE = 'class RetailPrivateIngressV1:\n    def read_rest_once(self, request):\n        prepared = self._prepare_rest_v1(request)\n        import http.client\n        connection = http.client.HTTPSConnection("api.polymarket.us", 443, timeout=prepared.timeout_seconds, context=prepared.tls_context)\n        try:\n            self._recheck_and_charge_v1(prepared)\n            connection.request("GET", prepared.target, body=None, headers=prepared.headers)\n            response = connection.getresponse()\n            self._validate_response_headers_v1(prepared, response)\n            raw = response.read(prepared.maximum_raw_bytes + 1)\n            received = self._observe_clock_v1()\n            self._validate_response_body_v1(prepared, response, raw)\n            return self._retain_received_v1(prepared, raw, received, 200)\n        finally:\n            connection.close()\n\n    def read_private_message_once(self, request):\n        prepared = self._prepare_ws_v1(request)\n        import websockets.sync.client\n        with websockets.sync.client.connect("wss://api.polymarket.us/v1/ws/private", ssl=prepared.tls_context, additional_headers=prepared.headers, proxy=None, compression=None, open_timeout=prepared.timeout_seconds, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=prepared.maximum_raw_bytes, max_queue=16, logger=prepared.quiet_logger) as connection:\n            self._verify_handshake_v1(prepared, connection.response)\n            self._recheck_subscription_v1(prepared)\n            connection.send(prepared.subscription_json)\n            state = self._initial_ws_state_v1()\n            for unused in range(prepared.maximum_application_messages):\n                message = connection.recv(timeout=self._remaining_seconds_v1(prepared))\n                received = self._observe_clock_v1()\n                state, disposition, raw = self._classify_ws_message_v1(prepared, state, message)\n                if disposition == "SELECTED_UPDATE":\n                    return self._retain_received_v1(prepared, raw, received, 101)\n            self._raise_message_budget_v1()\n'

def f14_native_admission_v1(relpath: str, tree: ast.Module) -> tuple[frozenset[tuple], tuple[str, ...]]:
    """One exact AST template, not a file/module-wide network exemption.

    Return positions of just the two admitted imports and two construction calls.
    The callers must still scan every other node for all original restrictions.
    """
    if relpath != _F14_NATIVE_OWNER:
        return (frozenset(), ())
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'RetailPrivateIngressV1']
    if len(classes) != 1:
        return (frozenset(), ('F14_NATIVE_OWNER_CLASS_ROSTER',))
    template = ast.parse(_F14_NATIVE_TRANSPORT_TEMPLATE).body[0]
    allowed = set()
    errors = []
    for method in template.body:
        found = [n for n in classes[0].body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method.name]
        if len(found) != 1 or ast.dump(found[0], include_attributes=False) != ast.dump(method, include_attributes=False):
            errors.append('F14_NATIVE_METHOD_TEMPLATE:' + method.name)
            continue
        for node in ast.walk(found[0]):
            match = isinstance(node, ast.Import) and len(node.names) == 1 and (node.names[0].name in {'http.client', 'websockets.sync.client'})
            if isinstance(node, ast.Call):
                match = ast.unparse(node.func) in {'http.client.HTTPSConnection', 'websockets.sync.client.connect'}
            if match:
                allowed.add((type(node).__name__, node.lineno, node.col_offset, node.end_lineno, node.end_col_offset))
    if errors:
        return (frozenset(), tuple(errors))
    return (frozenset(allowed), ())

_KALSHI_FEE_NATIVE_OWNER = 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py'
_KALSHI_FEE_NATIVE_TRANSPORT_TEMPLATE = "class KalshiFeeObservationOwnerV1:\n    def _read_rest_once_v1(self, role, ticker):\n        prepared = self._prepare_read_v1(role, ticker)\n        import http.client\n        connection = http.client.HTTPSConnection(\"external-api.kalshi.com\", 443, timeout=prepared.timeout_seconds, context=prepared.tls_context)\n        try:\n            self._recheck_and_charge_v1(prepared)\n            connection.request(\"GET\", prepared.target, body=None, headers=prepared.headers)\n            response = connection.getresponse()\n            self._validate_response_headers_v1(prepared, response)\n            raw = response.read(prepared.maximum_raw_bytes + 1)\n            received = self._observe_clock_v1()\n            self._validate_response_body_v1(prepared, response, raw)\n            return self._retain_received_v1(prepared, raw, received)\n        except (OSError, http.client.HTTPException) as error:\n            self._raise_transport_v1(error)\n        finally:\n            try:\n                connection.close()\n            except OSError as error:\n                self._raise_transport_v1(error)\n"


def kalshi_fee_native_admission_v1(relpath: str, tree: ast.Module) -> tuple[frozenset[tuple], tuple[str, ...]]:
    """Admit only the two network nodes in the independently frozen method."""
    if relpath != _KALSHI_FEE_NATIVE_OWNER:
        return (frozenset(), ())
    classes = [node for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef) and node.name == 'KalshiFeeObservationOwnerV1']
    if not classes:
        return (frozenset(), ())
    if len(classes) != 1 or classes[0] not in tree.body:
        return (frozenset(), ('KALSHI_FEE_NATIVE_OWNER_CLASS_ROSTER',))
    template = ast.parse(_KALSHI_FEE_NATIVE_TRANSPORT_TEMPLATE).body[0].body[0]
    found = [node for node in classes[0].body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == template.name]
    if len(found) != 1 or ast.dump(found[0], include_attributes=False) != ast.dump(template, include_attributes=False):
        return (frozenset(), ('KALSHI_FEE_NATIVE_METHOD_TEMPLATE',))
    admitted = set()
    for node in ast.walk(found[0]):
        match = isinstance(node, ast.Import) and len(node.names) == 1 and node.names[0].name == 'http.client'
        if isinstance(node, ast.Call):
            match = ast.unparse(node.func) == 'http.client.HTTPSConnection'
        if match:
            admitted.add((type(node).__name__, node.lineno, node.col_offset, node.end_lineno, node.end_col_offset))
    return (frozenset(admitted), ())


# Reviewed, literal native entry/function boundaries. These are narrow AST
# templates and call sites, never a module-wide permission for native effects.
_SOURCE_USE_NATIVE_PATH = "src/qtt/service/owner_source_use_windows.py"
_SOURCE_USE_NATIVE_TEMPLATES = {
    "run_owner_source_use_local_v1": "def run_owner_source_use_local_v1() -> int:\n    root = None\n    controller = None\n    outcome = 1\n    try:\n        root = _bootstrap_owner_source_use_v1()\n        from .owner_source_use import _create_owner_source_use_controller_v1\n        controller = _create_owner_source_use_controller_v1(root)\n        outcome = _run_local_window_v1(root, controller)\n    except BaseException:\n        outcome = 1\n    finally:\n        if controller is not None:\n            try:\n                controller.stop_v1()\n            except BaseException:\n                outcome = 1\n        if root is not None:\n            try:\n                _close_native_root_v1(root)\n            except BaseException:\n                outcome = 1\n    return outcome",
    "_native_system_v1": "def _native_system_v1():\n    \"\"\"Fixed System32 libraries and explicit prototypes; no generic native caller.\"\"\"\n    _require(sys.platform == 'win32' and ctypes.sizeof(ctypes.c_void_p) == 8)\n    k = ctypes.WinDLL('kernel32.dll', use_last_error=True, winmode=2048)\n    a = ctypes.WinDLL('advapi32.dll', use_last_error=True, winmode=2048)\n    s = ctypes.WinDLL('shell32.dll', use_last_error=True, winmode=2048)\n    o = ctypes.WinDLL('ole32.dll', use_last_error=True, winmode=2048)\n    h, p, d, b = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32)\n    k.GetCurrentProcess.argtypes, k.GetCurrentProcess.restype = ([], h)\n    k.GetCurrentThread.argtypes, k.GetCurrentThread.restype = ([], h)\n    k.GetCurrentProcessId.argtypes, k.GetCurrentProcessId.restype = ([], d)\n    k.CloseHandle.argtypes, k.CloseHandle.restype = ([h], b)\n    k.LocalFree.argtypes, k.LocalFree.restype = ([h], h)\n    k.CreateFileW.argtypes = [ctypes.c_wchar_p, d, d, p, d, d, h]\n    k.CreateFileW.restype = h\n    k.GetFileType.argtypes, k.GetFileType.restype = ([h], d)\n    k.GetFileInformationByHandleEx.argtypes, k.GetFileInformationByHandleEx.restype = ([h, ctypes.c_int32, p, d], b)\n    k.GetFinalPathNameByHandleW.argtypes, k.GetFinalPathNameByHandleW.restype = ([h, ctypes.c_wchar_p, d, d], d)\n    k.GetDriveTypeW.argtypes, k.GetDriveTypeW.restype = ([ctypes.c_wchar_p], d)\n    k.GetVolumeInformationW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, d, p, p, p, ctypes.c_wchar_p, d]\n    k.GetVolumeInformationW.restype = b\n    k.ReadFile.argtypes, k.ReadFile.restype = ([h, p, d, ctypes.POINTER(d), p], b)\n    a.OpenProcessToken.argtypes, a.OpenProcessToken.restype = ([h, d, ctypes.POINTER(h)], b)\n    a.OpenThreadToken.argtypes, a.OpenThreadToken.restype = ([h, d, b, ctypes.POINTER(h)], b)\n    a.GetTokenInformation.argtypes, a.GetTokenInformation.restype = ([h, ctypes.c_int32, p, d, ctypes.POINTER(d)], b)\n    a.IsValidSid.argtypes, a.IsValidSid.restype = ([p], b)\n    a.GetLengthSid.argtypes, a.GetLengthSid.restype = ([p], d)\n    a.ConvertSidToStringSidW.argtypes, a.ConvertSidToStringSidW.restype = ([p, ctypes.POINTER(p)], b)\n    a.GetSecurityInfo.argtypes = [h, ctypes.c_int32, d, ctypes.POINTER(p), p, ctypes.POINTER(p), p, ctypes.POINTER(p)]\n    a.GetSecurityInfo.restype = d\n    a.GetSecurityDescriptorControl.argtypes, a.GetSecurityDescriptorControl.restype = ([p, ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(d)], b)\n    a.GetSecurityDescriptorLength.argtypes, a.GetSecurityDescriptorLength.restype = ([p], d)\n    a.GetSecurityDescriptorDacl.argtypes = [p, ctypes.POINTER(b), ctypes.POINTER(p), ctypes.POINTER(b)]\n    a.GetSecurityDescriptorDacl.restype = b\n    a.GetAce.argtypes, a.GetAce.restype = ([p, d, ctypes.POINTER(p)], b)\n    s.SHGetKnownFolderPath.argtypes, s.SHGetKnownFolderPath.restype = ([p, d, h, ctypes.POINTER(p)], ctypes.c_int32)\n    o.CoTaskMemFree.argtypes, o.CoTaskMemFree.restype = ([p], None)\n    return SimpleNamespace(kernel=k, security=a, shell=s, ole=o)",
    "_known_folders_v1": "def _known_folders_v1(api):\n    from uuid import UUID\n    paths = []\n    for fixed in ('905e63b6-c1bf-494e-b29c-65b732d3d21a', '62ab5d82-fdc1-4dc3-a9dd-070d1d495d97'):\n        guid = (ctypes.c_ubyte * 16).from_buffer_copy(UUID(fixed).bytes_le)\n        pointer = ctypes.c_void_p()\n        _require(api.shell.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(pointer)) == 0 and pointer.value)\n        try:\n            value = _native_utf16_v1(pointer.value, 32768)[0]\n        finally:\n            api.ole.CoTaskMemFree(pointer)\n        _require(len(value) >= 3 and value[1:3] == ':\\\\' and value[0].isascii() and value[0].isalpha() and (not value.startswith('\\\\')) and (':' not in value[2:]))\n        volume = value[:3]\n        filesystem = ctypes.create_unicode_buffer(32)\n        _require(api.kernel.GetDriveTypeW(volume) == 3 and api.kernel.GetVolumeInformationW(volume, None, 0, None, None, None, filesystem, len(filesystem)) and (filesystem.value == 'NTFS'))\n        paths.append(Path(value))\n    return tuple(paths)",
    "_open_control_object_v1": "def _open_control_object_v1(api, path, directory, sid, retained):\n    text = str(path)\n    _require(path.is_absolute() and len(text) < 32760 and (':' not in text[2:]) and (not text.startswith('\\\\')))\n    handle = api.kernel.CreateFileW(text, 131072 | 128 | 1, 1, None, 3, 2097152 | (33554432 if directory else 0), None)\n    _require(handle not in (None, ctypes.c_void_p(-1).value))\n    retained.append(handle)\n    state = _object_state_v1(api, handle, path, directory)\n    _check_acl_v1(_observe_acl_v1(api, handle), sid, directory)\n    _require(_object_state_v1(api, handle, path, directory) == state)\n    return (handle, state)",
    "_check_interpreter_v1": "def _check_interpreter_v1(installation):\n    runtime = installation / 'runtime'\n    expected = (runtime / 'python314.zip', runtime, installation / 'app', installation / 'deps')\n    _require(sys.version_info[:3] == (3, 14, 6) and sys.platform == 'win32' and (os.name == 'nt') and (ctypes.sizeof(ctypes.c_void_p) == 8) and (getattr(sys.implementation, '_multiarch', None) == 'win-amd64') and all((getattr(sys.flags, name) == 1 for name in ('isolated', 'no_site', 'ignore_environment', 'safe_path', 'dont_write_bytecode'))) and (sys.prefix == sys.base_prefix) and (sys.exec_prefix == sys.base_exec_prefix) and (os.path.normcase(sys.executable) == os.path.normcase(str(runtime / 'pythonw.exe'))) and (tuple((os.path.normcase(str(Path(value))) for value in sys.path)) == tuple((os.path.normcase(str(value)) for value in expected))) and (os.path.normcase(os.getcwd()) == os.path.normcase(str(runtime))) and (not {'site', 'sitecustomize', 'usercustomize'}.intersection(sys.modules)) and (len(sys.argv) == 1) and (os.path.normcase(sys.argv[0]) == os.path.normcase(str(installation / 'app' / 'qtt' / 'service' / 'owner_source_use_windows.py'))) and (os.path.normcase(__file__) == os.path.normcase(sys.argv[0])))",
    "_bootstrap_owner_source_use_v1": "def _bootstrap_owner_source_use_v1():\n    api = _native_system_v1()\n    retained = []\n    try:\n        sid = _check_principal_v1(_observe_principal_v1(api))\n        program_files, program_data = _known_folders_v1(api)\n        installation = program_files / 'QTT' / 'OwnerControl'\n        _check_interpreter_v1(installation)\n        for anchor in (program_files, program_data):\n            _open_control_object_v1(api, anchor / 'QTT', True, sid, retained)\n            _open_control_object_v1(api, anchor / 'QTT' / 'OwnerControl', True, sid, retained)\n        opened = {}\n        seen_ids = set()\n        stack = [installation]\n        while stack:\n            directory = stack.pop()\n            with os.scandir(directory) as entries:\n                for entry in entries:\n                    _require(len(opened) < 65536 and entry.name not in {'.', '..'} and (':' not in entry.name))\n                    path = directory / entry.name\n                    is_directory = entry.is_dir(follow_symlinks=False)\n                    handle, state = _open_control_object_v1(api, path, is_directory, sid, retained)\n                    _require(state[:2] not in seen_ids)\n                    seen_ids.add(state[:2])\n                    opened[os.path.normcase(str(path))] = (handle, state)\n                    if is_directory:\n                        stack.append(path)\n        for relative, directory in (('runtime', True), ('app', True), ('deps', True), ('runtime/pythonw.exe', False), ('runtime/python314.zip', False), ('runtime/python314._pth', False), ('app/qtt/service/owner_source_use_windows.py', False)):\n            required = opened.get(os.path.normcase(str(installation / relative)))\n            _require(required is not None and required[1][5] is directory)\n        pth = installation / 'runtime' / 'python314._pth'\n        handle, state = opened[os.path.normcase(str(pth))]\n        pth_raw = _read_control_bytes_v1(api, handle, state[3], 256)\n        _require(pth_raw in (b'python314.zip\\n.\\n../app\\n../deps\\n', b'python314.zip\\r\\n.\\r\\n../app\\r\\n../deps\\r\\n') and _object_state_v1(api, handle, pth, False) == state)\n        config = program_data / 'QTT' / 'OwnerControl' / 'enrollment.json'\n        handle, state = _open_control_object_v1(api, config, False, sid, retained)\n        raw = _read_control_bytes_v1(api, handle, state[3], 65536)\n        _require(_object_state_v1(api, handle, config, False) == state)\n        _bind_native_module_identity_v1()\n        from .owner_source_use import _read_public_enrollment_v1\n        enrollment = _read_public_enrollment_v1(raw)\n        _require(enrollment.approval_sid == sid and enrollment.root_state != 'DISABLED')\n        root = object.__new__(_SourceUseNativeRootV1)\n        root.api, root.handles, root.enrollment, root.sid = (api, retained, enrollment, sid)\n        root.closed, root.operation = (False, None)\n        from threading import RLock\n        root.operation_lock = RLock()\n        root.window = None\n        root.completion_worker = None\n        root.completed = {}\n        _ROOTS[id(root)] = root\n        return root\n    except BaseException:\n        for handle in reversed(retained):\n            api.kernel.CloseHandle(handle)\n        raise",
    "_webauthn_table_v1": "def _webauthn_table_v1(root):\n    _require_native_root_v1(root)\n    w = ctypes.WinDLL('webauthn.dll', use_last_error=True, winmode=2048)\n    w.WebAuthNGetApiVersionNumber.argtypes, w.WebAuthNGetApiVersionNumber.restype = ([], ctypes.c_uint32)\n    version = w.WebAuthNGetApiVersionNumber()\n    _require(type(version) is int and 1 <= version <= 9)\n    from fido2.client import win_api\n    _require(win_api.WEBAUTHN_API_VERSION == version)\n    _check_output_layouts_v1(win_api)\n    h, p, hr = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32)\n    w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable.argtypes = [ctypes.POINTER(ctypes.c_int32)]\n    w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable.restype = hr\n    w.WebAuthNGetCancellationId.argtypes, w.WebAuthNGetCancellationId.restype = ([ctypes.POINTER(win_api.GUID)], hr)\n    w.WebAuthNCancelCurrentOperation.argtypes, w.WebAuthNCancelCurrentOperation.restype = ([ctypes.POINTER(win_api.GUID)], hr)\n    w.WebAuthNAuthenticatorMakeCredential.argtypes = [h, ctypes.POINTER(win_api.WebAuthNRpEntityInformation), ctypes.POINTER(win_api.WebAuthNUserEntityInformation), ctypes.POINTER(win_api.WebAuthNCoseCredentialParameters), ctypes.POINTER(win_api.WebAuthNClientData), ctypes.POINTER(win_api.WebAuthNMakeCredentialOptions), ctypes.POINTER(p)]\n    w.WebAuthNAuthenticatorMakeCredential.restype = hr\n    w.WebAuthNAuthenticatorGetAssertion.argtypes = [h, ctypes.c_wchar_p, ctypes.POINTER(win_api.WebAuthNClientData), ctypes.POINTER(win_api.WebAuthNGetAssertionOptions), ctypes.POINTER(p)]\n    w.WebAuthNAuthenticatorGetAssertion.restype = hr\n    w.WebAuthNFreeCredentialAttestation.argtypes, w.WebAuthNFreeCredentialAttestation.restype = ([p], None)\n    w.WebAuthNFreeAssertion.argtypes, w.WebAuthNFreeAssertion.restype = ([p], None)\n    available = ctypes.c_int32()\n    _require(w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable(ctypes.byref(available)) == 0 and available.value == 1)\n    return (w, win_api)",
    "_acquire_native_response_v1": "def _acquire_native_response_v1(root, operation):\n    import time\n    from .owner_source_use import _source_use_b64_v1\n    _require_native_root_v1(root)\n    window = _check_owned_window_v1(root)\n    before = _check_principal_v1(_observe_principal_v1(root.api))\n    _require(before == root.sid)\n    library, table = (operation.library, operation.table)\n    authentication = operation.authentication\n    remaining_ms = (operation.deadline - time.monotonic_ns()) // 1000000\n    _require(1 <= remaining_ms <= 120000)\n    client = library.WebAuthNClientData(authentication.client_data)\n    pointer = ctypes.c_void_p()\n    operation.keepalive = [window, operation.guid, client]\n    try:\n        if authentication.operation == 'GET':\n            options = library.WebAuthNGetAssertionOptions(timeout=remaining_ms, attachment=library.WebAuthNAuthenticatorAttachment.PLATFORM, uv_requirement=library.WebAuthNUserVerificationRequirement.REQUIRED, credentials=[{'id': _source_use_b64_v1(authentication.enrollment.key_id_b64, maximum=1024), 'type': 'public-key', 'transport': 'INTERNAL'}], cancellationId=operation.guid, extensions=[], flags=0, cred_large_blob_operation=library.WebAuthNLargeBlobOperation.NONE)\n            operation.keepalive.append(options)\n            result = table.WebAuthNAuthenticatorGetAssertion(window.hwnd, 'localhost', ctypes.byref(client), ctypes.byref(options), ctypes.byref(pointer))\n        else:\n            options = library.WebAuthNMakeCredentialOptions(timeout=remaining_ms, require_resident_key=False, prefer_resident_key=False, attachment=library.WebAuthNAuthenticatorAttachment.PLATFORM, uv_requirement=library.WebAuthNUserVerificationRequirement.REQUIRED, attestation_convoyence=library.WebAuthNAttestationConveyancePreference.NONE, credentials=[], cancellationId=operation.guid, extensions=[], enterprise_attestation=library.WebAuthNEnterpriseAttestation.NONE, large_blob_support=library.WebAuthNLargeBlobSupport.NONE, enable_prf=False)\n            rp = library.WebAuthNRpEntityInformation({'id': 'localhost', 'name': 'QTT Owner Source Use'})\n            user = library.WebAuthNUserEntityInformation({'id': _source_use_b64_v1(authentication.enrollment.user_handle_b64, minimum=32, maximum=32), 'name': authentication.enrollment.owner_ref, 'displayName': authentication.enrollment.owner_ref})\n            algorithms = library.WebAuthNCoseCredentialParameters([{'type': 'public-key', 'alg': -7}])\n            operation.keepalive.extend((options, rp, user, algorithms))\n            result = table.WebAuthNAuthenticatorMakeCredential(window.hwnd, ctypes.byref(rp), ctypes.byref(user), ctypes.byref(algorithms), ctypes.byref(client), ctypes.byref(options), ctypes.byref(pointer))\n        _require(result == 0 and pointer.value)\n        after = _check_principal_v1(_observe_principal_v1(root.api))\n        _require(after == before == root.sid)\n        raw = _copy_native_response_v1(pointer.value, authentication.operation, authentication.client_data)\n        return (raw, before, after)\n    finally:\n        if pointer.value:\n            if authentication.operation == 'GET':\n                table.WebAuthNFreeAssertion(pointer)\n            else:\n                table.WebAuthNFreeCredentialAttestation(pointer)",
    "_user_table_v1": "def _user_table_v1():\n    user = ctypes.WinDLL('user32.dll', use_last_error=True, winmode=2048)\n    h, p, b, d, word = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32, ctypes.c_uint32, ctypes.c_size_t)\n    result = ctypes.c_ssize_t\n    user.IsWindow.argtypes, user.IsWindow.restype = ([h], b)\n    user.GetWindowThreadProcessId.argtypes, user.GetWindowThreadProcessId.restype = ([h, ctypes.POINTER(d)], d)\n    user.RegisterClassExW.argtypes, user.RegisterClassExW.restype = ([p], ctypes.c_uint16)\n    user.UnregisterClassW.argtypes, user.UnregisterClassW.restype = ([ctypes.c_wchar_p, h], b)\n    user.CreateWindowExW.argtypes = [d, ctypes.c_wchar_p, ctypes.c_wchar_p, d, b, b, b, b, h, h, h, p]\n    user.CreateWindowExW.restype = h\n    user.DefWindowProcW.argtypes, user.DefWindowProcW.restype = ([h, d, word, result], result)\n    user.DestroyWindow.argtypes, user.DestroyWindow.restype = ([h], b)\n    user.ShowWindow.argtypes, user.ShowWindow.restype = ([h, b], b)\n    user.UpdateWindow.argtypes, user.UpdateWindow.restype = ([h], b)\n    user.GetMessageW.argtypes, user.GetMessageW.restype = ([p, h, d, d], b)\n    user.TranslateMessage.argtypes, user.TranslateMessage.restype = ([p], b)\n    user.DispatchMessageW.argtypes, user.DispatchMessageW.restype = ([p], result)\n    user.PostQuitMessage.argtypes, user.PostQuitMessage.restype = ([b], None)\n    user.SetWindowTextW.argtypes, user.SetWindowTextW.restype = ([h, ctypes.c_wchar_p], b)\n    user.GetWindowTextLengthW.argtypes, user.GetWindowTextLengthW.restype = ([h], b)\n    user.GetWindowTextW.argtypes, user.GetWindowTextW.restype = ([h, ctypes.c_wchar_p, b], b)\n    user.EnableWindow.argtypes, user.EnableWindow.restype = ([h, b], b)\n    user.SendMessageW.argtypes, user.SendMessageW.restype = ([h, d, word, result], result)\n    user.SetTimer.argtypes, user.SetTimer.restype = ([h, word, d, p], word)\n    user.KillTimer.argtypes, user.KillTimer.restype = ([h, word], b)\n    user.MessageBoxW.argtypes, user.MessageBoxW.restype = ([h, ctypes.c_wchar_p, ctypes.c_wchar_p, d], b)\n    user.SetWindowLongPtrW.argtypes, user.SetWindowLongPtrW.restype = ([h, b, result], result)\n    user.CallWindowProcW.argtypes, user.CallWindowProcW.restype = ([p, h, d, word, result], result)\n    return user",
}
_SOURCE_USE_NATIVE_CALLS = (
    ("_sid_string_v1", "api.security.IsValidSid(pointer)"),
    ("_sid_string_v1", "api.security.GetLengthSid(pointer)"),
    ("_sid_string_v1", "api.security.ConvertSidToStringSidW(pointer, ctypes.byref(text))"),
    ("_sid_string_v1", "api.kernel.LocalFree(text)"),
    ("_observe_principal_v1", "api.security.OpenThreadToken(api.kernel.GetCurrentThread(), 8, True, ctypes.byref(thread))"),
    ("_observe_principal_v1", "api.kernel.GetCurrentThread()"),
    ("_observe_principal_v1", "api.kernel.CloseHandle(thread)"),
    ("_observe_principal_v1", "api.security.OpenProcessToken(api.kernel.GetCurrentProcess(), 8, ctypes.byref(handle))"),
    ("_observe_principal_v1", "api.kernel.GetCurrentProcess()"),
    ("_observe_principal_v1", "api.security.GetTokenInformation(handle, information, None, 0, ctypes.byref(length))"),
    ("_observe_principal_v1", "api.security.GetTokenInformation(handle, information, data, capacity, ctypes.byref(length))"),
    ("_observe_principal_v1", "api.kernel.CloseHandle(handle)"),
    ("_known_folders_v1", "api.shell.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(pointer))"),
    ("_known_folders_v1", "api.ole.CoTaskMemFree(pointer)"),
    ("_known_folders_v1", "api.kernel.GetDriveTypeW(volume)"),
    ("_known_folders_v1", "api.kernel.GetVolumeInformationW(volume, None, 0, None, None, None, filesystem, len(filesystem))"),
    ("_observe_acl_v1", "api.security.GetSecurityInfo(handle, 1, 5, ctypes.byref(owner), None, ctypes.byref(dacl), None, ctypes.byref(descriptor))"),
    ("_observe_acl_v1", "api.security.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision))"),
    ("_observe_acl_v1", "api.security.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(verified_dacl), ctypes.byref(defaulted))"),
    ("_observe_acl_v1", "api.security.GetSecurityDescriptorLength(descriptor)"),
    ("_observe_acl_v1", "api.security.GetAce(dacl, index, ctypes.byref(pointer))"),
    ("_observe_acl_v1", "api.security.IsValidSid(pointer.value + 8)"),
    ("_observe_acl_v1", "api.security.GetLengthSid(pointer.value + 8)"),
    ("_observe_acl_v1", "api.kernel.LocalFree(descriptor)"),
    ("_object_state_v1", "api.kernel.GetFileType(handle)"),
    ("_object_state_v1", "api.kernel.GetFileInformationByHandleEx(handle, kind, ctypes.byref(value), ctypes.sizeof(value))"),
    ("_object_state_v1", "api.kernel.GetFinalPathNameByHandleW(handle, text, len(text), 0)"),
    ("_open_control_object_v1", "api.kernel.CreateFileW(text, 131072 | 128 | 1, 1, None, 3, 2097152 | (33554432 if directory else 0), None)"),
    ("_read_control_bytes_v1", "api.kernel.ReadFile(handle, buffer, size + 1, ctypes.byref(count), None)"),
    ("_bootstrap_owner_source_use_v1", "api.kernel.CloseHandle(handle)"),
    ("_close_native_root_v1", "root.api.kernel.CloseHandle(handle)"),
    ("_check_owned_window_v1", "window.user.IsWindow(window.hwnd)"),
    ("_check_owned_window_v1", "window.user.GetWindowThreadProcessId(window.hwnd, ctypes.byref(process))"),
    ("_check_owned_window_v1", "root.api.kernel.GetCurrentProcessId()"),
    ("_acquire_native_response_v1", "table.WebAuthNAuthenticatorGetAssertion(window.hwnd, 'localhost', ctypes.byref(client), ctypes.byref(options), ctypes.byref(pointer))"),
    ("_acquire_native_response_v1", "table.WebAuthNAuthenticatorMakeCredential(window.hwnd, ctypes.byref(rp), ctypes.byref(user), ctypes.byref(algorithms), ctypes.byref(client), ctypes.byref(options), ctypes.byref(pointer))"),
    ("_acquire_native_response_v1", "table.WebAuthNFreeAssertion(pointer)"),
    ("_acquire_native_response_v1", "table.WebAuthNFreeCredentialAttestation(pointer)"),
    ("_start_native_operation_v1", "table.WebAuthNGetCancellationId(ctypes.byref(guid))"),
    ("_cancel_native_operation_v1", "operation.table.WebAuthNCancelCurrentOperation(ctypes.byref(operation.guid))"),
    ("_run_local_window_v1.set_text", "user.SetWindowTextW(window.controls[control], _display_text_v1(text))"),
    ("_run_local_window_v1.enable_inputs", "user.EnableWindow(window.controls[control], enabled)"),
    ("_run_local_window_v1.enable_inputs", "user.EnableWindow(window.controls[12], enabled and controller._pending_ref is not None)"),
    ("_run_local_window_v1.enable_inputs", "user.EnableWindow(window.controls[16], enabled and controller._authority is None and (controller._enrollment_stage is None))"),
    ("_run_local_window_v1.stop", "user.DestroyWindow(window.hwnd)"),
    ("_run_local_window_v1.timer", "user.DestroyWindow(window.hwnd)"),
    ("_run_local_window_v1.command", "user.GetWindowTextLengthW(window.controls[10])"),
    ("_run_local_window_v1.command", "user.GetWindowTextW(window.controls[10], buffer, len(buffer))"),
    ("_run_local_window_v1.command", "user.MessageBoxW(window.hwnd, 'Confirm the complete displayed action and its explicit effects?', 'QTT Owner Source Use', 36)"),
    ("_run_local_window_v1.command", "user.MessageBoxW(window.hwnd, 'Create a platform public key with user verification, then prove possession. This only produces a public enrollment candidate; it grants no source use.', 'QTT Owner Source Use', 36)"),
    ("_run_local_window_v1.procedure", "user.KillTimer(hwnd, 1)"),
    ("_run_local_window_v1.procedure", "user.PostQuitMessage(0)"),
    ("_run_local_window_v1.procedure", "user.DefWindowProcW(hwnd, message, wparam, lparam)"),
    ("_run_local_window_v1", "user.RegisterClassExW(ctypes.byref(specification))"),
    ("_run_local_window_v1", "user.CreateWindowExW(0, specification.name, 'QTT Owner Source Use', 13238272, 80, 60, 1000, 840, None, None, None, None)"),
    ("_run_local_window_v1", "user.CreateWindowExW(0, kind, title, 1342177280 | extra, x, y, width, height, window.hwnd, control, None, None)"),
    ("_run_local_window_v1", "user.SendMessageW(window.controls[10], 197, 262144, 0)"),
    ("_run_local_window_v1", "user.SendMessageW(window.controls[control], 197, 2147483646, 0)"),
    ("_run_local_window_v1.result_procedure", "user.CallWindowProcW(window.result_procedure, hwnd, message, wparam, lparam)"),
    ("_run_local_window_v1", "user.SetWindowLongPtrW(window.controls[14], -4, ctypes.cast(result_procedure, ctypes.c_void_p).value)"),
    ("_run_local_window_v1", "user.SetTimer(window.hwnd, 1, 100, None)"),
    ("_run_local_window_v1", "user.ShowWindow(window.hwnd, 5)"),
    ("_run_local_window_v1", "user.UpdateWindow(window.hwnd)"),
    ("_run_local_window_v1", "user.GetMessageW(ctypes.byref(message), None, 0, 0)"),
    ("_run_local_window_v1", "user.TranslateMessage(ctypes.byref(message))"),
    ("_run_local_window_v1", "user.DispatchMessageW(ctypes.byref(message))"),
    ("_run_local_window_v1", "user.IsWindow(window.hwnd)"),
    ("_run_local_window_v1", "user.DestroyWindow(window.hwnd)"),
    ("_run_local_window_v1", "user.UnregisterClassW(specification.name, None)"),
)


def source_use_native_contract_v1(relpath: str, tree: ast.Module) -> tuple[str, ...]:
    """Check explicit native entry and consequential source-use call sites."""
    failures = []
    native = relpath == _SOURCE_USE_NATIVE_PATH
    controller = relpath == "src/qtt/service/owner_source_use.py"
    policy = relpath == "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py"
    calls = []
    located = []
    parents = {}

    def visit(node, owner=()):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = (*owner, node.name)
        located.append((node, ".".join(owner)))
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
            visit(child, owner)
    visit(tree)
    if native:
        functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name, template in _SOURCE_USE_NATIVE_TEMPLATES.items():
            candidates = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
            if len(candidates) != 1 or ast.dump(candidates[0], include_attributes=False) != ast.dump(ast.parse(template).body[0], include_attributes=False):
                failures.append("SOURCE_USE_NATIVE_TEMPLATE:" + name)
        entry = [n for n in tree.body if isinstance(n, ast.If)]
        expected_entry = ast.parse('if __name__ == "__main__":\n    raise SystemExit(run_owner_source_use_local_v1())').body[0]
        if len(entry) != 1 or ast.dump(entry[0], include_attributes=False) != ast.dump(expected_entry, include_attributes=False):
            failures.append("SOURCE_USE_NATIVE_EXPLICIT_ENTRY")

    allowed_loaders = {
        "_native_system_v1": {"kernel32.dll", "advapi32.dll", "shell32.dll", "ole32.dll"},
        "_webauthn_table_v1": {"webauthn.dll"}, "_user_table_v1": {"user32.dll"},
    }
    helper_callers = {
        "_native_system_v1": {(True, "_bootstrap_owner_source_use_v1")},
        "_bootstrap_owner_source_use_v1": {(True, "run_owner_source_use_local_v1")},
        "_webauthn_table_v1": {(True, "_start_native_operation_v1")},
        "_user_table_v1": {(True, "_run_local_window_v1")},
        "_acquire_native_response_v1": {(True, "_start_native_operation_v1.worker")},
    }
    loader_count = 0
    entry_calls = []
    for node, owner in located:
        if relpath.startswith("src/"):
            protected_callable = (node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None)
            if protected_callable in {*helper_callers, "run_owner_source_use_local_v1", "_start_native_operation_v1"}:
                parent = parents.get(id(node))
                if not (isinstance(parent, ast.Call) and parent.func is node):
                    failures.append("SOURCE_USE_NATIVE_CALLABLE_REFERENCE:" + protected_callable)
            if isinstance(node, ast.Import) and any(a.name == "ctypes" and a.asname not in (None, "ctypes") for a in node.names):
                failures.append("SOURCE_USE_NATIVE_MODULE_ALIAS")
            if isinstance(node, ast.Name) and node.id == "ctypes" and isinstance(node.ctx, ast.Load):
                parent = parents.get(id(node))
                if not (isinstance(parent, ast.Attribute) and parent.value is node):
                    failures.append("SOURCE_USE_NATIVE_MODULE_INDIRECTION")
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "ctypes" and node.attr in {
                    "WinDLL", "CDLL", "OleDLL", "PyDLL", "windll", "cdll"}:
                parent = parents.get(id(node))
                if not (isinstance(parent, ast.Call) and parent.func is node):
                    failures.append("SOURCE_USE_NATIVE_LOADER_INDIRECTION")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if relpath.startswith("src/") and isinstance(node, ast.ImportFrom) and node.module == "ctypes" and any(
                    alias.name in {"WinDLL", "CDLL", "OleDLL", "PyDLL", "windll", "cdll"} for alias in node.names):
                failures.append("SOURCE_USE_NATIVE_LOADER_ALIAS")
            modules = _imported_module_names(node)
            for module in modules:
                if module == "fido2.client.windows" or (
                    module == "fido2.client.win_api" or module == "fido2.client"
                    and any(alias.name == "win_api" for alias in node.names)):
                    if not (native and owner == "_webauthn_table_v1" and isinstance(node, ast.ImportFrom)
                            and node.module == "fido2.client" and [a.name for a in node.names] == ["win_api"]):
                        failures.append("SOURCE_USE_NATIVE_IMPORT_BOUNDARY")
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        if native and name in {"globals", "locals", "vars", "eval", "exec", "__import__"}:
            failures.append("SOURCE_USE_NATIVE_DYNAMIC_NAMESPACE")
        if relpath.startswith("src/") and name.rsplit(".", 1)[-1] == "run_owner_source_use_local_v1":
            entry_calls.append(node)
            guarded = native and any(node is child for branch in tree.body if isinstance(branch, ast.If)
                and ast.dump(branch, include_attributes=False) == ast.dump(expected_entry, include_attributes=False)
                for child in ast.walk(branch))
            if not guarded:
                failures.append("SOURCE_USE_NATIVE_OPERATIONAL_ENTRY_CALLER")
        loader = name in {"ctypes.WinDLL", "ctypes.CDLL", "ctypes.OleDLL", "ctypes.PyDLL"} or name.startswith(("ctypes.windll.", "ctypes.cdll."))
        if loader and (native or relpath.startswith("src/")):
            valid = native and name == "ctypes.WinDLL" and len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
            valid = valid and node.args[0].value in allowed_loaders.get(owner, set())
            valid = valid and ast.dump(node, include_attributes=False) == ast.dump(ast.parse(
                "ctypes.WinDLL(" + repr(node.args[0].value) + ", use_last_error=True, winmode=0x800)").body[0].value, include_attributes=False)
            if not valid:
                failures.append("SOURCE_USE_NATIVE_DLL_BOUNDARY")
            loader_count += 1
        if native and name.startswith(("api.kernel.", "api.security.", "api.shell.", "api.ole.", "root.api.kernel.",
                                      "table.WebAuthN", "operation.table.WebAuthN", "user.", "window.user.")):
            calls.append((owner, ast.unparse(node)))
        if relpath.startswith("src/"):
            leaf = name.rsplit(".", 1)[-1]
            if leaf in helper_callers and (native, owner) not in helper_callers[leaf]:
                failures.append("SOURCE_USE_NATIVE_CALLER:" + leaf)
            if leaf == "_start_native_operation_v1" and not (controller and owner in {
                    "OwnerSourceUseControllerV1._confirm_prepared_v1",
                    "OwnerSourceUseControllerV1._begin_enrollment_v1",
                    "OwnerSourceUseControllerV1._complete_enrollment_v1"}):
                failures.append("SOURCE_USE_NATIVE_CALLER:" + leaf)
    if native and (loader_count != 6 or sorted(calls) != sorted(_SOURCE_USE_NATIVE_CALLS)):
        failures.append("SOURCE_USE_NATIVE_EXACT_CALL_SITES")
    if native and len(entry_calls) != 1:
        failures.append("SOURCE_USE_NATIVE_OPERATIONAL_ENTRY_COUNT")
    if policy and any(isinstance(n, ast.ClassDef) and n.name == "SourceUseAuthorityV1" for n in tree.body):
        methods = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        required = {
            "_authority_guard_v1": {"binding._authority._check_binding_v1"},
            "_recheck_and_charge_v1": {"self._authority_guard_v1", "self._require_pending_v1"},
            "_prepare_read_v1": {"self._authority_guard_v1"},
            "_publication_fence_v1": {"authority._check_binding_v1"},
            "complete_action_v1": {"_verify_source_use_response_v1", "self._commit_verified_action_v1"},
            "_commit_verified_action_v1": {"self._uow.commit_source_use_action_v1"},
        }
        for name, expected in required.items():
            observed = {ast.unparse(n.func) for n in ast.walk(methods.get(name, ast.Module(body=[], type_ignores=[])))
                        if isinstance(n, ast.Call)}
            if not expected <= observed:
                failures.append("SOURCE_USE_AUTHORITY_BOUNDARY:" + name)
    return tuple(failures)


def _scan_python_content(path: pathlib.Path, text: str, enabled_flags: list[str]) -> list[str]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return _scan_text_content(path, text, enabled_flags)

    admitted, admission_failures = f14_native_admission_v1(path.as_posix(), tree)
    kalshi_admitted, kalshi_failures = kalshi_fee_native_admission_v1(path.as_posix(), tree)
    admitted = admitted | kalshi_admitted
    admission_failures = admission_failures + kalshi_failures
    admission_failures += source_use_native_contract_v1(path.as_posix(), tree)
    found_by_flag = {flag: set[str]() for flag in enabled_flags}
    source_retrieval_imports = {
        "http.client": "http.client import/use",
        "websockets": "websocket client",
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
        admitted_network_position = (type(node).__name__, getattr(node, 'lineno', None),
            getattr(node, 'col_offset', None), getattr(node, 'end_lineno', None),
            getattr(node, 'end_col_offset', None)) in admitted
        for module_name in _imported_module_names(node):
            root_name = module_name.split(".", 1)[0]
            if "forbid_source_retrieval" in found_by_flag and not admitted_network_position:
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
                    "websocket client",
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
                if flag in found_by_flag and not (flag == "forbid_source_retrieval" and admitted_network_position):
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

    return list(admission_failures) + [
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


_F14_NATIVE_INSTALL = 'python -m pip install --only-binary=:all: --no-deps --index-url https://pypi.org/simple websockets==17.0.1 cryptography==50.0.1 cffi==2.1.1 pycparser==3.0 fido2==2.2.1'


def _is_ci_test_dependency_allowlisted_pip_install(
    path: pathlib.PurePosixPath,
    text: str,
    match: re.Match[str],
    allowlist_hits: dict[tuple[pathlib.PurePosixPath, str], int],
) -> bool:
    allowed_commands = CI_TEST_DEPENDENCY_ALLOWLIST.get(path)
    if allowed_commands is None:
        return False
    line = _matched_line(text, match)
    slot = "pytest" if line in allowed_commands else "native" if line == _F14_NATIVE_INSTALL else None
    if slot is None:
        return False
    key = (path, slot)
    allowlist_hits[key] = allowlist_hits.get(key, 0) + 1
    return allowlist_hits[key] == 1


def _scan_text_content(
    path: pathlib.PurePosixPath, text: str, enabled_flags: list[str]
) -> list[str]:
    violations: list[str] = []
    ci_test_dependency_allowlist_hits: dict[tuple[pathlib.PurePosixPath, str], int] = {}
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
    ci_test_dependency_allowlist_hits: dict[tuple[pathlib.PurePosixPath, str], int] = {}
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
    custody_violations, excluded_top_level_local_custody_dir_names = (
        _validate_top_level_local_custody_boundary(root)
    )
    violations.extend(custody_violations)
    paths = _iter_paths(
        root,
        excluded_top_level_local_custody_dir_names=(
            excluded_top_level_local_custody_dir_names
        ),
    )
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
