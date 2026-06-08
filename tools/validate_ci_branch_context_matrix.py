#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import sys
from typing import Iterator, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import ci_branch_context as context  # noqa: E402


SUCCESS_MARKER = "CI_BRANCH_CONTEXT_MATRIX_OK"
BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)


@contextmanager
def patched_env(values: Mapping[str, str]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in BRANCH_CONTEXT_ENV}
    try:
        for name in BRANCH_CONTEXT_ENV:
            os.environ.pop(name, None)
        os.environ.update(values)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def _check_exact_repair_branch_matrix(failures: list[str]) -> None:
    ancestry_required_repairs = (
        ("PR159R", context.PR159R_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR159R", context.PR159R_DETACHED_HEAD_REPAIR_BRANCH),
        ("PR159S", context.PR159S_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR160", context.PR160_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR160", context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH),
    )
    for gate_id, branch in ancestry_required_repairs:
        _expect(
            context.is_branch_allowed_for_upstream_pr_gate(
                branch,
                gate_id,
                ancestry_present=True,
            ),
            failures,
            f"{gate_id} exact repair branch should pass with ancestry: {branch}",
        )
        _expect(
            not context.is_branch_allowed_for_upstream_pr_gate(branch, gate_id),
            failures,
            f"{gate_id} ancestry-bound repair branch passed without ancestry: {branch}",
        )

    exact_repairs = (
        ("PR161A", context.PR161A_REPAIR_BRANCH),
        ("PR161B", context.PR161B_REPAIR_BRANCH),
        ("PR159R", context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR159S", context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR160", context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR161A", context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH),
        ("PR161B", context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH),
    )
    for gate_id, branch in exact_repairs:
        _expect(
            context.is_explicit_repair_branch_allowed_for_upstream_pr_gate(
                branch,
                gate_id,
            ),
            failures,
            f"{gate_id} exact repair branch should be explicit: {branch}",
        )
        _expect(
            context.is_branch_allowed_for_upstream_pr_gate(branch, gate_id),
            failures,
            f"{gate_id} exact repair branch should pass: {branch}",
        )


def _check_unrelated_repairs_fail(failures: list[str]) -> None:
    unrelated_repairs = (
        "repair/pr163-c-unrelated-context",
        "repair/pr160-unlisted-context",
        "repair/pr999-anything",
    )
    for gate_id in ("PR159R", "PR159S", "PR160", "PR161A", "PR161B", "PR162A"):
        for branch in unrelated_repairs:
            _expect(
                not context.is_explicit_repair_branch_allowed_for_upstream_pr_gate(
                    branch,
                    gate_id,
                ),
                failures,
                f"{gate_id} unrelated repair branch should not be explicit: {branch}",
            )
            _expect(
                not context.is_branch_allowed_for_upstream_pr_gate(
                    branch,
                    gate_id,
                    ancestry_present=True,
                ),
                failures,
                f"{gate_id} unrelated repair branch passed branch gate: {branch}",
            )


def _check_local_named_branches(failures: list[str]) -> None:
    cases = (
        ("PR159R", context.PR159R_BRANCH),
        ("PR159R", context.PR162C_BRANCH),
        ("PR159S", context.PR162C_BRANCH),
        ("PR160", context.PR159R_BRANCH),
        ("PR160", context.PR163_B_BRANCH),
        ("PR161A", context.PR161B_BRANCH),
        ("PR161B", context.PR162A_BRANCH),
        ("PR162A", context.PR163_C_BRANCH),
        ("PR163-C", context.PR163_C_BRANCH),
    )
    for gate_id, branch in cases:
        _expect(
            context.is_branch_allowed_for_upstream_pr_gate(branch, gate_id),
            failures,
            f"{gate_id} local named branch should pass: {branch}",
        )

    wrong_cases = (
        ("PR159S", context.PR160_BRANCH),
        ("PR161B", context.PR161A_BRANCH),
        ("PR163-C", context.PR164_BRANCH),
        ("PR160", "feature/unrelated"),
    )
    for gate_id, branch in wrong_cases:
        _expect(
            not context.is_branch_allowed_for_upstream_pr_gate(branch, gate_id),
            failures,
            f"{gate_id} wrong branch should fail closed: {branch}",
        )


def _check_main_push_and_pull_request_are_separate(failures: list[str]) -> None:
    with patched_env(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_REF_NAME": "main",
        }
    ):
        _expect(
            context.github_actions_main_push_context_active(),
            failures,
            "main push context was not detected",
        )
        _expect(
            not context.github_actions_pull_request_detached_context_active(
                branch_returncode=0,
                branch="main",
            ),
            failures,
            "main push was misclassified as pull_request detached-head",
        )
        _expect(
            context.is_main_push_context_allowed_for_upstream_pr_gate(
                "main",
                "PR160",
                ancestry_present=True,
            ),
            failures,
            "main push with ancestry should be allowed separately",
        )
        _expect(
            not context.is_main_push_context_allowed_for_upstream_pr_gate(
                "main",
                "PR160",
                ancestry_present=False,
            ),
            failures,
            "main push without ancestry should fail closed",
        )

    with patched_env(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/200/merge",
            "GITHUB_REF_NAME": "200/merge",
            "GITHUB_HEAD_REF": context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        }
    ):
        _expect(
            not context.github_actions_main_push_context_active(),
            failures,
            "pull_request merge ref was misclassified as main push",
        )
        _expect(
            context.github_actions_pull_request_detached_context_active(
                branch_returncode=0,
                branch="",
            ),
            failures,
            "pull_request merge ref was not detected as detached-head context",
        )


def _fake_detached_git_stdout(
    repo_root: Path,
    args: Sequence[str],
) -> tuple[int, str, str]:
    command = tuple(args)
    if command == ("branch", "--show-current"):
        return 0, "", ""
    if command == ("rev-parse", "--abbrev-ref", "HEAD"):
        return 0, "HEAD", ""
    return 1, "", "unexpected git call"


def _check_pull_request_detached_simulation(repo_root: Path, failures: list[str]) -> None:
    with patched_env(
        {
            "GITHUB_ACTIONS": "true",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/200/merge",
            "GITHUB_REF_NAME": "200/merge",
            "GITHUB_HEAD_REF": context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
        }
    ):
        branch_context = context.current_branch_context(
            repo_root,
            git_stdout=_fake_detached_git_stdout,
        )
        _expect(
            branch_context.branch
            == context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            failures,
            "simulated pull_request did not prefer GITHUB_HEAD_REF",
        )
        _expect(
            context.github_actions_pull_request_detached_context_active(
                branch_returncode=0,
                branch="",
            ),
            failures,
            "simulated pull_request did not model detached git branch output",
        )
        _expect(
            context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
                branch_context.branch,
                "PR160",
            ),
            failures,
            "PR160 should allow exact PR163-C repair head ref in detached PR",
        )
        _expect(
            not context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
                "repair/pr163-c-unrelated-context",
                "PR160",
            ),
            failures,
            "unrelated repair head ref passed detached PR context",
        )


def validate(repo_root: Path) -> tuple[str, ...]:
    failures: list[str] = []
    _check_exact_repair_branch_matrix(failures)
    _check_unrelated_repairs_fail(failures)
    _check_local_named_branches(failures)
    _check_main_push_and_pull_request_are_separate(failures)
    _check_pull_request_detached_simulation(repo_root, failures)
    return tuple(failures)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--simulate-github-pr",
        action="store_true",
        help="Run only the GitHub pull_request detached-head simulation case.",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    if args.simulate_github_pr:
        failures: list[str] = []
        _check_pull_request_detached_simulation(repo_root, failures)
    else:
        failures = list(validate(repo_root))

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
