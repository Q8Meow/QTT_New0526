#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import os
import pathlib
import re
import subprocess
from typing import Callable, Sequence

BRANCH_CONTEXT_ENV_CANDIDATES = (
    "GITHUB_HEAD_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF",
    "BRANCH_NAME",
    "CI_COMMIT_REF_NAME",
)

CI_DETACHED_HEAD_MODE_MARKER = "CI_DETACHED_HEAD_MODE_ACTIVE"
CI_SHALLOW_FETCH_ANCESTRY_SKIP_MARKER = "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER = (
    "DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_ACTIVE"
)
REPAIR_BRANCH_PREFIX = "repair/"
MAIN_CUMULATIVE_BRANCH_PREFIX = "repair/main-cumulative-"
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS = {
    "repair-pr153r-redo-report-determinism": 153,
    "repair/pr153s-source-value-capture-closure-classifier": 153,
    "pr154-atomicrows-parameter-default-value-materialization-gate": 154,
    "repair/pr154-post-merge-pytest-context-hygiene": 154,
}
EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS = {
    "repair-pr153r-redo-report-determinism": frozenset(
        {
            "tools/ci_branch_context.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        }
    ),
    "repair/pr153s-source-value-capture-closure-classifier": frozenset(
        {
            "docs/master_plan/generated/PR153S_SourceValueCaptureClosureClassifier.report.json",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/__init__.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/classifier.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/inputs.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/report.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/taxonomy.py",
            "src/qtt/stage1_prediction_markets/pr153s_source_value_capture_closure_classifier/validator.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/source_evidence/test_pr153s_source_value_capture_closure_classifier.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_pr153s_source_value_capture_closure_classifier.py",
        }
    ),
    "repair/pr154-post-merge-pytest-context-hygiene": frozenset(
        {
            "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
        }
    ),
    "pr154-atomicrows-parameter-default-value-materialization-gate": frozenset(
        {
            "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/__init__.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/inputs.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/materializer.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/report.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/taxonomy.py",
            "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/validator.py",
            "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tools/validate_atomicrows_parameter_default_value_materialization_gate.py",
        }
    ),
}

GitStdout = Callable[[pathlib.Path, Sequence[str]], tuple[int, str, str]]


@dataclass(frozen=True)
class BranchContext:
    branch: str
    source: str
    git_error: str = ""


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def github_actions_active() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def normalize_branch_context(value: str) -> str:
    branch = value.strip()
    if not branch or branch == "HEAD":
        return ""
    if branch.startswith("refs/pull/"):
        return ""
    if re.match(r"^[0-9]+/(head|merge)$", branch):
        return ""
    for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
        if branch.startswith(prefix):
            return branch[len(prefix) :]
    return branch


def current_branch_context(
    repo_root: pathlib.Path,
    env_candidates: Sequence[str] = BRANCH_CONTEXT_ENV_CANDIDATES,
    *,
    git_stdout: GitStdout | None = None,
) -> BranchContext:
    git_stdout = git_stdout or _git_stdout
    for env_name in env_candidates:
        branch = normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return BranchContext(branch=branch, source=env_name)

    git_errors: list[str] = []
    for args in (["branch", "--show-current"], ["rev-parse", "--abbrev-ref", "HEAD"]):
        branch_rc, branch_stdout, branch_err = git_stdout(repo_root, args)
        if branch_rc != 0:
            git_errors.append(branch_err or f"git {' '.join(args)} failed")
            continue
        branch = normalize_branch_context(branch_stdout)
        if branch:
            return BranchContext(branch=branch, source=f"git {' '.join(args)}")

    return BranchContext(branch="", source="", git_error="; ".join(git_errors))


def github_actions_branch_context() -> str:
    for env_name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME", "GITHUB_REF"):
        branch = normalize_branch_context(os.getenv(env_name, ""))
        if branch:
            return branch
    return ""


def github_actions_pull_request_detached_context_active(
    *,
    branch_returncode: int | None = None,
    branch: str = "",
) -> bool:
    if not github_actions_active():
        return False
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    github_ref = os.getenv("GITHUB_REF", "")
    github_ref_name = os.getenv("GITHUB_REF_NAME", "")
    pull_request_event = event_name in {"pull_request", "pull_request_target"}
    pull_request_ref = (
        github_ref.startswith("refs/pull/")
        or re.match(r"^[0-9]+/(head|merge)$", github_ref_name) is not None
    )
    if branch_returncode is None:
        return pull_request_event or pull_request_ref

    merge_ref = (
        re.match(r"^refs/(?:remotes/)?pull/[0-9]+/merge$", github_ref) is not None
        or re.match(r"^[0-9]+/merge$", github_ref_name) is not None
    )
    detached_branch = branch_returncode != 0 or branch.strip() in {"", "HEAD"}
    return merge_ref or (pull_request_event and detached_branch)


def github_actions_main_push_context_active() -> bool:
    if not github_actions_active():
        return False
    return (
        os.getenv("GITHUB_EVENT_NAME") == "push"
        and os.getenv("GITHUB_REF") == "refs/heads/main"
        and os.getenv("GITHUB_REF_NAME") == "main"
    )


def is_repair_branch(branch: str) -> bool:
    return branch.startswith(REPAIR_BRANCH_PREFIX)


def is_main_cumulative_branch(branch: str) -> bool:
    return branch == "main" or branch.startswith(MAIN_CUMULATIVE_BRANCH_PREFIX)


def roadmap_pr_number(branch: str) -> int | None:
    match = re.match(r"^pr(?P<number>[0-9]+)[a-z]*-", branch)
    if match is None:
        return None
    return int(match.group("number"))


def _explicit_downstream_repair_branch_pr_number(branch: str) -> int | None:
    return EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS.get(branch)


def is_explicit_downstream_repair_changed_path(branch: str, path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS.get(
        branch,
        frozenset(),
    )


def is_downstream_roadmap_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
    explicit_repair_pr = _explicit_downstream_repair_branch_pr_number(branch)
    if explicit_repair_pr is not None:
        return explicit_repair_pr > after_pr
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number > after_pr


def is_downstream_or_main_validation_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
    return is_main_cumulative_branch(branch) or is_downstream_roadmap_branch(
        branch,
        after_pr,
        allow_repair=allow_repair,
    )


def is_pr_or_later_branch(
    branch: str,
    minimum_pr: int,
    *,
    allow_main: bool = True,
    allow_repair: bool = True,
) -> bool:
    if allow_main and is_main_cumulative_branch(branch):
        return True
    explicit_repair_pr = _explicit_downstream_repair_branch_pr_number(branch)
    if explicit_repair_pr is not None:
        return explicit_repair_pr >= minimum_pr
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number >= minimum_pr
