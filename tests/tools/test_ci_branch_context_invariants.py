"""Invariant checks for centralized CI branch-context handling."""

from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
CENTRAL_HELPER = TOOLS_DIR / "ci_branch_context.py"

FORBIDDEN_LOCAL_DEFINITIONS = {
    "MAIN_CUMULATIVE_BRANCH_PREFIX",
    "REPAIR_BRANCH_PREFIX",
}

WRAPPER_DELEGATES = {
    "_current_branch_context": ("current_branch_context",),
    "_downstream_validation_branch_allowed": (
        "is_downstream_roadmap_branch",
        "is_downstream_or_main_validation_branch",
    ),
    "_main_cumulative_branch_allowed": ("is_main_cumulative_branch",),
    "_downstream_or_main_validation_branch_allowed": (
        "is_downstream_or_main_validation_branch",
    ),
    "_pr99_static_builder_branch_allowed": ("is_pr_or_later_branch",),
}

ROADMAP_BRANCH_REGEX = re.compile(
    r"""(?:fr|rf|r)?["']\^?pr\(\?P<number>""",
    flags=re.IGNORECASE,
)


def _tool_files() -> tuple[Path, ...]:
    return tuple(sorted(TOOLS_DIR.glob("*.py")))


def _validator_files() -> tuple[Path, ...]:
    return tuple(path for path in _tool_files() if path != CENTRAL_HELPER)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _target_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.List, ast.Tuple)):
        names: set[str] = set()
        for element in target.elts:
            names.update(_target_names(element))
        return names
    return set()


def _assignment_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Assign):
        names: set[str] = set()
        for target in node.targets:
            names.update(_target_names(target))
        return names
    if isinstance(node, ast.AnnAssign):
        return _target_names(node.target)
    return set()


def _assignment_value(node: ast.AST) -> ast.expr | None:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        return node.value
    return None


def _ci_branch_context_attr(node: ast.AST | None, attr: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == attr
        and isinstance(node.value, ast.Name)
        and node.value.id == "ci_branch_context"
    )


def _calls_ci_branch_context_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    allowed_names: tuple[str, ...],
) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and any(
            _ci_branch_context_attr(node.func, name) for name in allowed_names
        ):
            return True
    return False


def test_branch_context_env_candidates_come_from_central_helper() -> None:
    offenders: list[str] = []

    for path in _validator_files():
        for node in ast.walk(_parse(path)):
            if "BRANCH_CONTEXT_ENV_CANDIDATES" not in _assignment_names(node):
                continue
            value = _assignment_value(node)
            if not _ci_branch_context_attr(value, "BRANCH_CONTEXT_ENV_CANDIDATES"):
                offenders.append(
                    f"{_relative(path)}:{getattr(node, 'lineno', '?')}: "
                    "forbidden pattern BRANCH_CONTEXT_ENV_CANDIDATES with local "
                    "value; must be assigned from "
                    "ci_branch_context.BRANCH_CONTEXT_ENV_CANDIDATES"
                )

    assert not offenders, (
        "Validator files must not define local branch-context environment "
        "candidate lists:\n" + "\n".join(offenders)
    )


def test_branch_context_compatibility_wrappers_delegate_to_central_helper() -> None:
    offenders: list[str] = []

    for path in _validator_files():
        for node in ast.walk(_parse(path)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            allowed_names = WRAPPER_DELEGATES.get(node.name)
            if not allowed_names:
                continue
            if _calls_ci_branch_context_function(node, allowed_names):
                continue
            expected = " or ".join(
                f"ci_branch_context.{name}" for name in allowed_names
            )
            offenders.append(
                f"{_relative(path)}:{node.lineno}: forbidden pattern def "
                f"{node.name} without central delegation; must delegate to "
                f"{expected}"
            )

    assert not offenders, (
        "Compatibility wrappers must delegate to tools.ci_branch_context:\n"
        + "\n".join(offenders)
    )


def test_branch_context_prefix_constants_are_not_redefined_locally() -> None:
    offenders: list[str] = []

    for path in _validator_files():
        for node in ast.walk(_parse(path)):
            local_names = _assignment_names(node) & FORBIDDEN_LOCAL_DEFINITIONS
            value = _assignment_value(node)
            for name in sorted(local_names):
                if _ci_branch_context_attr(value, name):
                    continue
                offenders.append(
                    f"{_relative(path)}:{getattr(node, 'lineno', '?')}: "
                    f"forbidden pattern local branch-context definition {name}; "
                    "use tools.ci_branch_context"
                )

    assert not offenders, (
        "Validator files must not redefine centralized branch-context constants:\n"
        + "\n".join(offenders)
    )


def test_roadmap_branch_regex_is_not_reimplemented_locally() -> None:
    offenders: list[str] = []

    for path in _validator_files():
        source = path.read_text(encoding="utf-8")
        for match in ROADMAP_BRANCH_REGEX.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            offenders.append(
                f"{_relative(path)}:{line}: forbidden local roadmap branch regex "
                f"pattern {match.group(0)!r}; use tools.ci_branch_context"
            )

    assert not offenders, (
        "Validator files must not reimplement roadmap branch regex parsing:\n"
        + "\n".join(offenders)
    )
