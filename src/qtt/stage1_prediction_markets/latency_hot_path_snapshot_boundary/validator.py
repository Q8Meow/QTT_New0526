"""Fail-closed validator for PR137L latency hot-path snapshot boundary artifacts."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import constants as c
from .model import ValidationOutcome
from .report import build_index, build_report


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, str(key), item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _string_values(value: Any) -> list[str]:
    values: list[str] = []
    for _path, _key, item in _walk(value):
        if isinstance(item, str):
            values.append(item)
    return values


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def _github_actions_pull_request_merge_ref_active(
    *,
    branch_returncode: int,
    branch: str,
) -> bool:
    if not _github_actions_active():
        return False
    github_ref = os.getenv("GITHUB_REF", "")
    github_ref_name = os.getenv("GITHUB_REF_NAME", "")
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    merge_ref = (
        re.match(r"^refs/(?:remotes/)?pull/[0-9]+/merge$", github_ref) is not None
        or re.match(r"^[0-9]+/merge$", github_ref_name) is not None
    )
    detached_branch = branch_returncode != 0 or branch.strip() in {"", "HEAD"}
    return merge_ref or (
        event_name in {"pull_request", "pull_request_target"} and detached_branch
    )


def _validate_environment(repo_root: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    receipts: list[str] = []
    branch_rc, branch, _branch_err = _git_stdout(repo_root, ["branch", "--show-current"])
    head_rc, head, _head_err = _git_stdout(repo_root, ["log", "-1", "--oneline"])

    if _github_actions_pull_request_merge_ref_active(
        branch_returncode=branch_rc,
        branch=branch,
    ):
        receipts.extend(
            [
                c.RECEIPT_CI_DETACHED_HEAD_MODE,
                c.RECEIPT_CI_SHALLOW_FETCH_ANCESTRY_SKIPPED,
                c.RECEIPT_CI_MERGE_REF_BASELINE_ACCEPTED,
            ]
        )
        return failures, receipts

    if branch_rc != 0 or branch != c.BRANCH:
        failures.append(c.REASON_BASELINE_BRANCH_MISMATCH)

    if head_rc == 0 and head.startswith(c.BASE_HEAD_PREFIX):
        return failures, receipts

    base_rc, _base_out, _base_err = _git_stdout(
        repo_root,
        ["rev-parse", "--verify", f"{c.BASE_HEAD_PREFIX}^{{commit}}"],
    )
    ancestor_rc, _ancestor_out, _ancestor_err = _git_stdout(
        repo_root,
        ["merge-base", "--is-ancestor", c.BASE_HEAD_PREFIX, "HEAD"],
    )
    if base_rc == 0 and ancestor_rc == 0:
        receipts.append(c.RECEIPT_LOCAL_BRANCH_DESCENDANT_BASELINE_ACCEPTED)
    else:
        failures.append(c.REASON_BASELINE_HEAD_MISMATCH)
    return failures, receipts


def _validate_required_context(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("pr136_selector_artifacts_missing"):
        failures.append(c.REASON_PR136_SELECTOR_REQUIRED)
    if report.get("pr137_dependency_controller_artifacts_missing"):
        failures.append(c.REASON_PR137_DEPENDENCY_CONTROLLER_REQUIRED)
    if report.get("crosswalk_context_artifacts_missing"):
        failures.append(c.REASON_CROSSWALK_CONTEXT_REQUIRED)
    return failures


def _validate_identity(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "report_type": c.REPORT_TYPE,
        "schema_version": 1,
        "generated_at_utc": c.STATIC_TIME,
        "pr_id": c.PR_ID,
        "title": c.TITLE,
        "branch": c.BRANCH,
        "authority_class": c.AUTHORITY_CLASS,
        "scope_class": c.SCOPE_CLASS,
        "readiness_state": c.READINESS_STATE,
        "latency_scope": c.LATENCY_SCOPE,
        "selector_authority_preserved": "PR136",
        "dependency_controller_authority_preserved": "PR137",
        "validation_state": c.READINESS_STATE,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
    if report.get("required_upstream_prs") != ["PR137"]:
        failures.append(c.REASON_UPSTREAM_PR137_REQUIRED)
    if report.get("static_evidence_dependencies") != ["PR137R"]:
        failures.append(c.REASON_PR137R_STATIC_EVIDENCE_REQUIRED)
    if report.get("downstream_dependencies") != ["PR138"]:
        failures.append(c.REASON_DOWNSTREAM_PR138_REQUIRED)
    if report.get("pr137r_evidence_consumed") is not True:
        failures.append(c.REASON_PR137R_STATIC_EVIDENCE_REQUIRED)
    if report.get("implements_pr138") is not False:
        failures.append(c.REASON_PR138_SCOPE_FORBIDDEN)
    if report.get("structural_evidence_only") is not True:
        failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
    return failures


def _validate_dependency_chain(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    chain = report.get("dependency_chain")
    if not isinstance(chain, Mapping):
        return [c.REASON_ACTIVE_SEQUENCE_MISSING]
    if chain.get("pr137l_occurrence_count") != 1:
        failures.append(c.REASON_DUPLICATE_ENTRY_FORBIDDEN)
    if chain.get("pr137_to_pr137l") is not True:
        failures.append(c.REASON_UPSTREAM_PR137_REQUIRED)
    if chain.get("pr137l_to_pr138") is not True:
        failures.append(c.REASON_DOWNSTREAM_PR138_REQUIRED)
    if chain.get("pr138_requires_pr137l") is not True:
        failures.append(c.REASON_DOWNSTREAM_PR138_REQUIRED)
    if chain.get("pr137r_active_sequence_node") is not False:
        failures.append(c.REASON_DISCONNECTED_ROADMAP_FORBIDDEN)
    if chain.get("disconnected_roadmap_created") is not False:
        failures.append(c.REASON_DISCONNECTED_ROADMAP_FORBIDDEN)
    if chain.get("controller_mutation_required") is not False:
        failures.append(c.REASON_DISCONNECTED_ROADMAP_FORBIDDEN)
    prefix = chain.get("active_sequence_observed_prefix")
    if not isinstance(prefix, list) or prefix[:3] != ["PR137", c.PR_ID, "PR138"]:
        failures.append(c.REASON_ACTIVE_SEQUENCE_MISSING)
    return failures


def _validate_pr137r_snapshot(
    report: Mapping[str, Any],
    repo_root: Path | None,
) -> list[str]:
    failures: list[str] = []
    snapshot = report.get("pr137r_static_evidence_snapshot")
    if not isinstance(snapshot, Mapping):
        return [c.REASON_PR137R_STATIC_EVIDENCE_REQUIRED]
    expected = {
        "source_report": c.PR137R_REPORT_PATH.as_posix(),
        "atomicrows_bundle_artifact_found": True,
        "atomicrows_functional_bundle_status": "PRESENT_AND_STATICALLY_VALIDATED",
        "expected_atomicrows_row_count": 4183,
        "atomicrows_row_count_proven": True,
        "atomicrows_row_count_value": 4183,
        "atomicrows_schema_validated": True,
        "atomicrows_validation_error_count": 0,
        "atomicrows_row_family_source_files_found": True,
        "atomicrows_row_family_source_file_count": 15,
        "atomicrows_bundle_builder_found": True,
        "atomicrows_bundle_validator_found": True,
        "atomicrows_agent_read_only_consumer_found": True,
        "atomicrows_agent_consumption_boundary": (
            "READ_ONLY_STATIC_CONSUMER_ONLY_NOT_RUNTIME_NOT_LIVE"
        ),
        "atomicrows_final_readiness_gate_found": False,
        "atomicrows_day1_live_trading_ready": False,
        "atomicrows_profit_evidence_created": False,
        "atomicrows_quantum_advantage_evidence_created": False,
        "atomicrows_semantic_row_contract_complete": False,
        "atomicrows_pr137l_usage": "READ_ONLY_PRECOMPUTED_STATIC_EVIDENCE_SNAPSHOT_ONLY",
    }
    for key, value in expected.items():
        if snapshot.get(key) != value:
            failures.append(c.REASON_PR137R_STATIC_EVIDENCE_CONTRADICTION)
    if snapshot.get("atomicrows_final_readiness_gate_found") is not False:
        failures.append(c.REASON_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN)
    if snapshot.get("atomicrows_day1_live_trading_ready") is not False:
        failures.append(c.REASON_ATOMICROWS_DAY1_LIVE_READY_CLAIM_FORBIDDEN)
    if snapshot.get("atomicrows_profit_evidence_created") is not False:
        failures.append(c.REASON_ATOMICROWS_BUNDLE_AS_PROFIT_EVIDENCE_FORBIDDEN)
    if snapshot.get("atomicrows_quantum_advantage_evidence_created") is not False:
        failures.append(c.REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN)
    if repo_root is not None:
        source = repo_root / str(snapshot.get("source_report", ""))
        if not source.exists():
            failures.append(c.REASON_PR137R_REPORT_REQUIRED)
    return failures


def _validate_market_and_roadmap(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("global_roadmap_model") != c.GLOBAL_ROADMAP_MODEL:
        failures.append(c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN)
    if report.get("one_global_roadmap_preserved") is not True:
        failures.append(c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN)
    if report.get("market_scoped_overlays_only") is not True:
        failures.append(c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN)
    if report.get("market_specific_roadmap_forks_created") is not False:
        failures.append(c.REASON_MARKET_ROADMAP_FORK_FORBIDDEN)
    if report.get("market_scopes") != list(c.CANONICAL_MARKET_SCOPES):
        failures.append(c.REASON_FORECASTEX_ALIAS_FORBIDDEN)
    forbidden = set(c.FORBIDDEN_THIRD_VENUE_ALIASES)
    if any(value in forbidden for value in _string_values(report)):
        failures.append(c.REASON_FORECASTEX_ALIAS_FORBIDDEN)
    return failures


def _validate_boundary_surfaces(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("precomputed_snapshot_boundary_types") != list(
        c.PRECOMPUTED_SNAPSHOT_BOUNDARY_TYPES
    ):
        failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
    if report.get("control_plane_producer_lanes") != list(c.CONTROL_PLANE_PRODUCER_LANES):
        failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
    if report.get("future_live_consumer_lanes") != list(c.FUTURE_LIVE_CONSUMER_LANES):
        failures.append(c.REASON_STATIC_BOUNDARY_ONLY)

    constraints = report.get("live_path_boundary_constraints")
    if not isinstance(constraints, Mapping):
        failures.append(c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN)
    else:
        for field in c.LIVE_PATH_REQUIRED_TRUE_CONSTRAINTS:
            if constraints.get(field) is not True:
                failures.append(c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN)

    live_path = report.get("live_path_boundary")
    if not isinstance(live_path, Mapping):
        failures.append(c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN)
    else:
        if live_path.get("complexity_target") != c.LATENCY_COMPLEXITY_TARGET:
            failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
        for field in c.LIVE_PATH_REQUIRED_FALSE_FIELDS:
            if live_path.get(field) is not False:
                failures.append(c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN)

    latency = report.get("latency_discipline")
    if not isinstance(latency, Mapping):
        failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
    else:
        if (
            latency.get("live_pretrade_snapshot_boundary_complexity_target")
            != c.LATENCY_COMPLEXITY_TARGET
        ):
            failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
        for field in c.LATENCY_DISCIPLINE_TRUE_FIELDS:
            if latency.get(field) is not True:
                failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
        for field in c.LATENCY_DISCIPLINE_FALSE_FIELDS:
            if latency.get(field) is not True:
                failures.append(c.REASON_LIVE_PATH_CONTROL_PLANE_DEPENDENCY_FORBIDDEN)
    return failures


def _validate_quantum_and_atomicrows_metadata(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    quantum = report.get("quantum_future_ref_metadata")
    if not isinstance(quantum, Mapping):
        failures.append(c.REASON_QUANTUM_EXECUTION_FORBIDDEN)
    else:
        for field in c.QUANTUM_ALLOWED_TRUE_FIELDS:
            if quantum.get(field) is not True:
                failures.append(c.REASON_QUANTUM_EXECUTION_FORBIDDEN)
        for field in c.QUANTUM_REQUIRED_FALSE_FIELDS:
            if quantum.get(field) is not False:
                if "optimizer_input" in field:
                    failures.append(c.REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN)
                elif "advantage" in field:
                    failures.append(c.REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN)
                else:
                    failures.append(c.REASON_QUANTUM_EXECUTION_FORBIDDEN)

    atomicrows = report.get("atomicrows_future_ref_metadata")
    if not isinstance(atomicrows, Mapping):
        failures.append(c.REASON_ATOMICROWS_MUTATION_FORBIDDEN)
    else:
        for field in c.ATOMICROWS_ALLOWED_TRUE_FIELDS:
            if atomicrows.get(field) is not True:
                failures.append(c.REASON_ATOMICROWS_MUTATION_FORBIDDEN)
        for field in c.ATOMICROWS_REQUIRED_FALSE_FIELDS:
            if atomicrows.get(field) is not False:
                if "materialization" in field:
                    failures.append(c.REASON_ATOMICROWS_MATERIALIZATION_FORBIDDEN)
                elif "final_readiness" in field:
                    failures.append(c.REASON_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN)
                elif "qtt_sha" in field:
                    failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
                else:
                    failures.append(c.REASON_ATOMICROWS_MUTATION_FORBIDDEN)
    return failures


def _reason_for_created_flag(flag: str) -> str:
    if "latency_superiority" in flag:
        return c.REASON_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN
    if "execution_superiority" in flag:
        return c.REASON_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN
    if "alpha" in flag:
        return c.REASON_ALPHA_EVIDENCE_FORBIDDEN
    if "profit" in flag:
        return c.REASON_PROFIT_EVIDENCE_FORBIDDEN
    if "source_retrieval" in flag:
        return c.REASON_SOURCE_RETRIEVAL_FORBIDDEN
    if "source_acceptance" in flag or "accepted_source" in flag:
        return c.REASON_SOURCE_ACCEPTANCE_FORBIDDEN
    if "connector" in flag:
        return c.REASON_CONNECTOR_BINDING_FORBIDDEN
    if "replay" in flag or "paper" in flag:
        return c.REASON_REPLAY_PAPER_EXECUTION_FORBIDDEN
    if "ranking" in flag or "scoring" in flag or "arbitration" in flag:
        return c.REASON_ORDER_AUTHORITY_FORBIDDEN
    if "order" in flag or "fill" in flag or "trading_signal" in flag:
        return c.REASON_ORDER_AUTHORITY_FORBIDDEN
    if "quantum_optimizer_input" in flag:
        return c.REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN
    if "quantum_advantage" in flag:
        return c.REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN
    if "quantum" in flag:
        return c.REASON_QUANTUM_EXECUTION_FORBIDDEN
    if "qtt_sha" in flag or "digest" in flag:
        return c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN
    if "atomicrows_final_readiness" in flag:
        return c.REASON_ATOMICROWS_FINAL_READINESS_CLAIM_FORBIDDEN
    if "atomicrows_materialization" in flag:
        return c.REASON_ATOMICROWS_MATERIALIZATION_FORBIDDEN
    if "atomicrows" in flag:
        return c.REASON_ATOMICROWS_MUTATION_FORBIDDEN
    if "sha" in flag:
        return c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN
    if "runtime" in flag:
        return c.REASON_RUNTIME_AUTHORITY_FORBIDDEN
    if "live" in flag or "day1" in flag:
        return c.REASON_LIVE_AUTHORITY_FORBIDDEN
    return c.REASON_STATIC_BOUNDARY_ONLY


def _validate_not_created_flags(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    flags = report.get("not_created_flags")
    if not isinstance(flags, Mapping):
        return [c.REASON_STATIC_BOUNDARY_ONLY]
    for field in c.NOT_CREATED_FLAGS:
        if field not in flags:
            failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
        elif flags.get(field) is not False:
            failures.append(_reason_for_created_flag(field))
    for field, value in flags.items():
        if value is not False:
            failures.append(_reason_for_created_flag(str(field)))
    diff_checks = report.get("forbidden_diff_checks")
    if not isinstance(diff_checks, Mapping):
        failures.append(c.REASON_STATIC_BOUNDARY_ONLY)
    else:
        for field, value in diff_checks.items():
            if value is not False:
                failures.append(_reason_for_created_flag(str(field)))
    return failures


def _validate_no_forbidden_integrity_surface(
    report: Mapping[str, Any],
    repo_root: Path | None,
) -> list[str]:
    failures: list[str] = []
    forbidden_key = c.FORBIDDEN_GENERATED_INTEGRITY_KEY
    for _path, key, item in _walk(report):
        if key == forbidden_key:
            failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
        if "sidecar" in key.lower() and item is not False:
            failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
    text = _json_text(report)
    if re.search(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:", text):
        failures.append(c.REASON_IDEMPOTENCY_FAILURE)
    forbidden_library_name = "hash" + "lib"
    if forbidden_library_name in text:
        failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
    disabled_integrity_ref = "AtomicRows.bundle." + forbidden_key
    if disabled_integrity_ref in text:
        failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
    if repo_root is not None:
        for rel_path in c.PR137L_CREATED_PATHS:
            path = repo_root / rel_path
            if not path.exists() or path.is_dir():
                continue
            artifact_text = path.read_text(encoding="utf-8", errors="ignore")
            if f'"{forbidden_key}"' in artifact_text:
                failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
            if forbidden_library_name in artifact_text or disabled_integrity_ref in artifact_text:
                failures.append(c.REASON_QTT_SHA_DIGEST_AUTHORITY_FORBIDDEN)
    return failures


def _validate_idempotency(report: Mapping[str, Any], repo_root: Path | None) -> list[str]:
    if repo_root is None:
        return []
    failures: list[str] = []
    expected_report = build_report(repo_root)
    if dict(report) != expected_report:
        failures.append(c.REASON_IDEMPOTENCY_FAILURE)
    index_path = repo_root / c.INDEX_PATH
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append(c.REASON_IDEMPOTENCY_FAILURE)
        else:
            if index != build_index(expected_report):
                failures.append(c.REASON_IDEMPOTENCY_FAILURE)
    return failures


def _protected_diff_failures(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in c.PROTECTED_UNTOUCHED_PATHS:
        completed = subprocess.run(
            ["git", "diff", "--", rel_path],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            failures.append(c.REASON_ALLOWLIST_EXPANSION_REQUIRED)
        elif completed.stdout.strip():
            failures.append(c.REASON_ATOMICROWS_MUTATION_FORBIDDEN)
    return failures


def success_receipts_for_report(report: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(c.SUCCESS_RECEIPTS)


def validate_report_payload(
    report: Mapping[str, Any],
    *,
    repo_root: Path | str | None = None,
    enforce_environment: bool = False,
    enforce_protected_diff: bool = False,
) -> ValidationOutcome:
    root = Path(repo_root).resolve() if repo_root is not None else None
    failures: list[str] = []
    environment_receipts: list[str] = []
    if enforce_environment and root is not None:
        environment_failures, environment_receipts = _validate_environment(root)
        failures.extend(environment_failures)
    failures.extend(_validate_identity(report))
    failures.extend(_validate_required_context(report))
    failures.extend(_validate_dependency_chain(report))
    failures.extend(_validate_pr137r_snapshot(report, root))
    failures.extend(_validate_market_and_roadmap(report))
    failures.extend(_validate_boundary_surfaces(report))
    failures.extend(_validate_quantum_and_atomicrows_metadata(report))
    failures.extend(_validate_not_created_flags(report))
    failures.extend(_validate_no_forbidden_integrity_surface(report, root))
    failures.extend(_validate_idempotency(report, root))
    if enforce_protected_diff and root is not None:
        failures.extend(_protected_diff_failures(root))
    unique_failures = tuple(sorted(set(failures)))
    return ValidationOutcome(
        ok=not unique_failures,
        failures=unique_failures,
        receipts=(
            success_receipts_for_report(report) + tuple(environment_receipts)
            if not unique_failures
            else ()
        ),
    )
