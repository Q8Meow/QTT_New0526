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


def github_actions_pull_request_detached_context_active() -> bool:
    if not github_actions_active():
        return False
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    github_ref = os.getenv("GITHUB_REF", "")
    github_ref_name = os.getenv("GITHUB_REF_NAME", "")
    return (
        event_name in {"pull_request", "pull_request_target"}
        or github_ref.startswith("refs/pull/")
        or re.match(r"^[0-9]+/(head|merge)$", github_ref_name) is not None
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


def is_downstream_roadmap_branch(
    branch: str,
    after_pr: int,
    *,
    allow_repair: bool = True,
) -> bool:
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
    if allow_repair and is_repair_branch(branch):
        return True
    pr_number = roadmap_pr_number(branch)
    return pr_number is not None and pr_number >= minimum_pr
