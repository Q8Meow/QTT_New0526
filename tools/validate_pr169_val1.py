#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tokenize
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import run_validation_gates as runner  # noqa: E402
from tools.validation_inventory import canonical_command  # noqa: E402

SUCCESS_MARKER = "QTT_PR169_VAL1_OK"
REPORT_DIR = Path("docs/master_plan/generated/pr169_val1")
REQUIRED_REPORT_NAMES = (
    "manifest.json",
    "shards.report.json",
    "timing.report.json",
    "parity.report.json",
    "readability.report.json",
    "acceptance.report.json",
)
OLD_SLOW_PHASE = runner.DETERMINISTIC_VALIDATORS_PHASE
BASELINE_WORKFLOW_REF = (
    "PR270 pull_request run 29013998571 and post-merge main run 29016781546"
)
BASELINE_SLOWEST_PHASE_MINUTES = 45.00866666666667
BASELINE_WORKFLOW_WALL_CLOCK_MINUTES = 50.75
BASELINE_JOB_DURATION_MINUTES = 47.833333333333336
BASELINE_VALIDATION_COMMAND_MINUTES = 45.00866666666667
BASELINE_TIMING_SOURCE = (
    "GitHub Actions job logs for QTT Validation PR270 pull_request "
    "Validation Shard (tools-generated-artifacts)"
)
TRACKED_AGENT_ORCH1_PREFIX = "docs/master_plan/generated/pr169_agent_orch1"
BIDI_CODEPOINTS = frozenset((*range(0x202A, 0x202F), *range(0x2066, 0x206A)))
HIDDEN_CODEPOINTS = frozenset({0x200B, 0x200C, 0x200D, 0xFEFF})
ALLOWED_CONTROL_CODEPOINTS = frozenset({9, 10, 13})
CRITICAL_WORKFLOW_FILES = (Path(".github/workflows/qtt_validation.yml"),)
CRITICAL_PYTHON_FILES = (
    Path("tools/run_validation_gates.py"),
    Path("tools/build_pr169_val1.py"),
    Path("tools/validate_pr169_val1.py"),
    Path("tools/build_pr169_agent_orch1.py"),
    Path("tools/validate_pr169_agent_orch1.py"),
    Path("src/qtt/agents/pr169_agent_orch1_resolvers.py"),
)


@dataclass(frozen=True)
class ReadabilityRecord:
    path: str
    line_count: int
    max_line_length: int
    hidden_bidi_control_chars: tuple[str, ...]
    many_defs_or_classes_on_one_line: bool
    semicolon_statement_lines: int
    minified: bool

    @property
    def pass_(self) -> bool:
        return (
            not self.hidden_bidi_control_chars
            and not self.many_defs_or_classes_on_one_line
            and self.semicolon_statement_lines == 0
            and not self.minified
        )


def _normal_path(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _read_text(repo_root: Path, relative: Path) -> str:
    return (repo_root / relative).read_text(encoding="utf-8")


def _job_block(workflow_text: str, job_id: str) -> str:
    marker = f"  {job_id}:\n"
    start = workflow_text.find(marker)
    if start == -1:
        return ""
    next_job = workflow_text.find("\n  ", start + len(marker))
    while next_job != -1 and workflow_text[next_job + 3 : next_job + 5] == "  ":
        next_job = workflow_text.find("\n  ", next_job + 1)
    if next_job == -1:
        return workflow_text[start:]
    return workflow_text[start:next_job]


def workflow_matrix_phases(repo_root: Path) -> tuple[str, ...]:
    workflow = _read_text(repo_root, CRITICAL_WORKFLOW_FILES[0])
    shard_block = _job_block(workflow, "validation_shards")
    return tuple(
        re.findall(r"^\s+- phase: ([A-Za-z0-9_-]+)\s*$", shard_block, re.MULTILINE)
    )


def _workflow_checks(repo_root: Path) -> list[str]:
    workflow = _read_text(repo_root, CRITICAL_WORKFLOW_FILES[0])
    shard_block = _job_block(workflow, "validation_shards")
    validation_block = _job_block(workflow, "validation")
    failures: list[str] = []
    phases = workflow_matrix_phases(repo_root)
    if tuple(runner.ORDERED_PHASES) != phases:
        failures.append(
            "WORKFLOW_MATRIX_PHASE_MISMATCH: "
            f"workflow={phases!r} runner={tuple(runner.ORDERED_PHASES)!r}"
        )
    if OLD_SLOW_PHASE in phases:
        failures.append("WORKFLOW_STILL_RUNS_OLD_DETERMINISTIC_ALIAS")
    if "      fail-fast: false\n" not in shard_block:
        failures.append("WORKFLOW_MATRIX_FAIL_FAST_NOT_FALSE")
    if "continue-on-error: true" in shard_block or "continue-on-error: true" in validation_block:
        failures.append("WORKFLOW_REQUIRED_JOB_CONTINUE_ON_ERROR")
    for phase in runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES:
        if f"validation-timing-${{{{ matrix.phase }}}}" not in shard_block:
            failures.append(f"WORKFLOW_TIMING_ARTIFACT_NAME_MISSING: {phase}")
            break
        if f"validation-router-${{{{ matrix.phase }}}}" not in shard_block:
            failures.append(f"WORKFLOW_ROUTER_ARTIFACT_NAME_MISSING: {phase}")
            break
    if shard_block.count("if: ${{ always() }}") < 2:
        failures.append("WORKFLOW_ARTIFACT_UPLOAD_NOT_ALWAYS")
    if "actions/upload-artifact@v4" not in shard_block:
        failures.append("WORKFLOW_UPLOAD_ARTIFACT_MISSING")
    if "actions/download-artifact@v4" not in validation_block:
        failures.append("WORKFLOW_DOWNLOAD_ARTIFACT_MISSING")
    if "pattern: validation-*" not in validation_block:
        failures.append("WORKFLOW_DOWNLOAD_PATTERN_MISSING")
    if "tools/validate_pr169_val1.py" not in validation_block:
        failures.append("WORKFLOW_VAL1_ARTIFACT_AGGREGATOR_MISSING")
    if "      - validation_shards\n" not in validation_block:
        failures.append("WORKFLOW_VALIDATION_GATES_DOES_NOT_NEED_SHARDS")
    if "    if: ${{ always() }}\n" not in validation_block:
        failures.append("WORKFLOW_VALIDATION_GATES_NOT_ALWAYS")
    if 'result != "success"' not in validation_block or "raise SystemExit(1)" not in validation_block:
        failures.append("WORKFLOW_VALIDATION_GATES_NOT_FAIL_CLOSED")
    return failures


def _command_digest(commands: Sequence[Sequence[str]]) -> str:
    canonical = [list(canonical_command(command)) for command in commands]
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def deterministic_shard_parity(repo_root: Path) -> dict[str, object]:
    validation_dir = repo_root / ".tmp" / "pr169_val1_validation_dir"
    pytest_basetemp = validation_dir / "pytest"
    old_commands = runner.build_phase_commands(
        OLD_SLOW_PHASE,
        validation_dir,
        pytest_basetemp,
    )
    subphase_commands: dict[str, list[list[str]]] = {
        phase: runner.build_phase_commands(phase, validation_dir, pytest_basetemp)
        for phase in runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES
    }
    flattened = [
        command
        for phase in runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES
        for command in subphase_commands[phase]
    ]
    old_canonical = [canonical_command(command) for command in old_commands]
    new_canonical = [canonical_command(command) for command in flattened]
    duplicate_new = sorted(
        {
            command
            for command in new_canonical
            if new_canonical.count(command) > 1
        }
    )
    dropped = [command for command in old_canonical if command not in new_canonical]
    added = [command for command in new_canonical if command not in old_canonical]
    ranges = {
        phase: {
            "start_command_index": start,
            "end_command_index": end,
            "command_count": len(subphase_commands[phase]),
        }
        for phase, (start, end) in runner.DETERMINISTIC_VALIDATOR_SHARD_COMMAND_RANGES.items()
    }
    return {
        "old_phase": OLD_SLOW_PHASE,
        "new_shard_phases": list(runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES),
        "new_shard_count": len(runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES),
        "old_command_count": len(old_commands),
        "new_command_count": len(flattened),
        "old_phase_to_new_phase_map": {
            OLD_SLOW_PHASE: list(runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES),
        },
        "new_shard_command_ranges": ranges,
        "coverage_parity_state": "pass"
        if old_canonical == new_canonical and not duplicate_new
        else "fail",
        "dropped_selector_count": len(dropped),
        "duplicate_selector_count": len(duplicate_new),
        "added_selector_count": len(added),
        "old_command_digest": _command_digest(old_commands),
        "new_command_digest": _command_digest(flattened),
        "deterministic_compatibility_alias": OLD_SLOW_PHASE in runner.VALIDATION_PHASES
        and OLD_SLOW_PHASE not in runner.ORDERED_PHASES,
    }


def _bad_codepoints(text: str) -> tuple[str, ...]:
    bad: set[int] = set()
    for char in text:
        codepoint = ord(char)
        if codepoint in ALLOWED_CONTROL_CODEPOINTS:
            continue
        if (
            codepoint < 32
            or 0x7F <= codepoint <= 0x9F
            or codepoint in BIDI_CODEPOINTS
            or codepoint in HIDDEN_CODEPOINTS
        ):
            bad.add(codepoint)
    return tuple(f"U+{codepoint:04X}" for codepoint in sorted(bad))


def scan_readability_file(repo_root: Path, relative: Path) -> ReadabilityRecord:
    text = _read_text(repo_root, relative)
    lines = text.splitlines()
    line_count = len(lines)
    max_line_length = max((len(line) for line in lines), default=0)
    many_defs = any(
        len(re.findall(r"\b(def|class)\s+[A-Za-z_]", line)) > 1 for line in lines
    )
    semicolon_statement_lines = _semicolon_statement_line_count(text)
    if relative.suffix == ".yml":
        minified = line_count < 80 or any(line.count(":") > 12 for line in lines)
    elif relative.name == "__init__.py":
        minified = False
    else:
        minified = line_count < 10 or any(len(line) > 400 for line in lines)
    return ReadabilityRecord(
        path=_normal_path(relative),
        line_count=line_count,
        max_line_length=max_line_length,
        hidden_bidi_control_chars=_bad_codepoints(text),
        many_defs_or_classes_on_one_line=many_defs,
        semicolon_statement_lines=semicolon_statement_lines,
        minified=minified,
    )


def _semicolon_statement_line_count(text: str) -> int:
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    except tokenize.TokenError:
        return sum(1 for line in text.splitlines() if ";" in line)
    lines: set[int] = set()
    for token in tokens:
        if token.type == tokenize.OP and token.string == ";":
            lines.add(token.start[0])
    return len(lines)


def readability_records(repo_root: Path) -> tuple[ReadabilityRecord, ...]:
    paths: list[Path] = [*CRITICAL_WORKFLOW_FILES]
    paths.extend(path for path in CRITICAL_PYTHON_FILES if (repo_root / path).exists())
    agent_tests = sorted(Path("tests/pr169_agent_orch1").glob("*.py"))
    paths.extend(agent_tests)
    return tuple(scan_readability_file(repo_root, path) for path in paths)


def _agent_orch_generated_diff_paths(repo_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", TRACKED_AGENT_ORCH1_PREFIX],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ("<git diff failed>",)
    return tuple(path for path in completed.stdout.splitlines() if path.strip())


def _json_artifact_exists(artifact_root: Path, artifact_name: str, phase: str) -> bool:
    artifact_dir = artifact_root / artifact_name
    if not artifact_dir.exists():
        return False
    candidates = sorted(artifact_dir.rglob("*.json"))
    return any(candidate.name == f"{phase}.json" for candidate in candidates)


def validate_artifacts(artifact_root: Path, expected_phases: Sequence[str]) -> list[str]:
    failures: list[str] = []
    if not artifact_root.exists():
        return [f"VAL1_ARTIFACT_ROOT_MISSING: {_normal_path(artifact_root)}"]
    for phase in expected_phases:
        timing_name = f"validation-timing-{phase}"
        router_name = f"validation-router-{phase}"
        if not _json_artifact_exists(artifact_root, timing_name, phase):
            failures.append(f"VAL1_TIMING_ARTIFACT_MISSING: {phase}")
        if not _json_artifact_exists(artifact_root, router_name, phase):
            failures.append(f"VAL1_ROUTER_ARTIFACT_MISSING: {phase}")
    return failures


def common_report_fields(repo_root: Path) -> dict[str, object]:
    parity = deterministic_shard_parity(repo_root)
    workflow_failures = _workflow_checks(repo_root)
    readability = readability_records(repo_root)
    readability_failures = [
        record.path for record in readability if not record.pass_
    ]
    agent_diff_paths = _agent_orch_generated_diff_paths(repo_root)
    failed = bool(
        workflow_failures
        or readability_failures
        or agent_diff_paths
        or parity["coverage_parity_state"] != "pass"
    )
    return {
        "producer": "tools/build_pr169_val1.py",
        "validator": "tools/validate_pr169_val1.py",
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "baseline_workflow_ref": BASELINE_WORKFLOW_REF,
        "baseline_slowest_phase": OLD_SLOW_PHASE,
        "baseline_slowest_phase_minutes_or_unknown": BASELINE_SLOWEST_PHASE_MINUTES,
        "baseline_timing_source": BASELINE_TIMING_SOURCE,
        "workflow_wall_clock_minutes_or_unknown": BASELINE_WORKFLOW_WALL_CLOCK_MINUTES,
        "job_duration_minutes_or_unknown": BASELINE_JOB_DURATION_MINUTES,
        "setup_dependency_minutes_or_unknown": 2.35,
        "validation_command_minutes_or_unknown": BASELINE_VALIDATION_COMMAND_MINUTES,
        "queue_wait_minutes_or_unknown": None,
        "artifact_upload_download_minutes_or_unknown": None,
        "new_shard_phases": parity["new_shard_phases"],
        "new_shard_count": parity["new_shard_count"],
        "old_phase_to_new_phase_map": parity["old_phase_to_new_phase_map"],
        "new_shard_command_ranges": parity["new_shard_command_ranges"],
        "coverage_parity_state": parity["coverage_parity_state"],
        "dropped_selector_count": parity["dropped_selector_count"],
        "duplicate_selector_count": parity["duplicate_selector_count"],
        "timing_artifact_upload_enabled": not any(
            failure.startswith("WORKFLOW_TIMING_ARTIFACT")
            or failure.startswith("WORKFLOW_ROUTER_ARTIFACT")
            or failure == "WORKFLOW_ARTIFACT_UPLOAD_NOT_ALWAYS"
            for failure in workflow_failures
        ),
        "timing_artifact_aggregation_enabled": not any(
            failure.startswith("WORKFLOW_DOWNLOAD")
            or failure == "WORKFLOW_VAL1_ARTIFACT_AGGREGATOR_MISSING"
            for failure in workflow_failures
        ),
        "workflow_yaml_readability_fixed": False,
        "python_readability_fixed": False,
        "readability_guard_enabled": True,
        "hidden_bidi_control_guard_enabled": True,
        "validation_weakened": False,
        "trading_semantic_change": False,
        "qku_formula_semantic_change": False,
        "agent_orch_generated_semantic_change": bool(agent_diff_paths),
        "runtime_authority_change": False,
        "paper_live_execution_change": False,
        "agent_orch_generated_semantic_diff_count": len(agent_diff_paths),
        "hidden_test_deselection_created": False,
        "source_truth_change": False,
        "qtt_sha_authority_change": False,
        "pass": not failed,
        "fail_closed_reasons": [
            *workflow_failures,
            *[f"READABILITY_GUARD_FAIL: {path}" for path in readability_failures],
            *[
                f"AGENT_ORCH1_GENERATED_DIFF: {path}"
                for path in agent_diff_paths
            ],
            *(
                []
                if parity["coverage_parity_state"] == "pass"
                else ["DETERMINISTIC_SHARD_PARITY_FAIL"]
            ),
        ],
    }


def build_report_payloads(repo_root: Path) -> dict[str, dict[str, object]]:
    common = common_report_fields(repo_root)
    parity = deterministic_shard_parity(repo_root)
    readability = readability_records(repo_root)
    report_names = list(REQUIRED_REPORT_NAMES)
    payloads: dict[str, dict[str, object]] = {}
    payloads["manifest.json"] = {
        **common,
        "report_id": "pr169_val1_manifest",
        "reports": report_names,
        "owned_generated_prefix": _normal_path(REPORT_DIR),
    }
    payloads["shards.report.json"] = {
        **common,
        "report_id": "pr169_val1_shards",
        "old_slow_phase": OLD_SLOW_PHASE,
        "deterministic_compatibility_alias": parity[
            "deterministic_compatibility_alias"
        ],
        "old_command_count": parity["old_command_count"],
        "new_command_count": parity["new_command_count"],
        "old_command_digest": parity["old_command_digest"],
        "new_command_digest": parity["new_command_digest"],
    }
    payloads["timing.report.json"] = {
        **common,
        "report_id": "pr169_val1_timing",
        "timing_inconclusive": True,
        "speedup_unproven_until_pr_ci": True,
        "baseline_pull_request_run_id": 29013998571,
        "baseline_main_run_id": 29016781546,
        "baseline_slowest_job": "Validation Shard (tools-generated-artifacts)",
    }
    payloads["parity.report.json"] = {
        **common,
        "report_id": "pr169_val1_parity",
        "old_command_digest": parity["old_command_digest"],
        "new_command_digest": parity["new_command_digest"],
        "added_selector_count": parity["added_selector_count"],
    }
    payloads["readability.report.json"] = {
        **common,
        "report_id": "pr169_val1_readability",
        "critical_files": [
            {
                "path": record.path,
                "line_count": record.line_count,
                "max_line_length": record.max_line_length,
                "hidden_bidi_control_chars": list(record.hidden_bidi_control_chars),
                "many_defs_or_classes_on_one_line": record.many_defs_or_classes_on_one_line,
                "semicolon_statement_lines": record.semicolon_statement_lines,
                "minified": record.minified,
                "pass": record.pass_,
            }
            for record in readability
        ],
    }
    payloads["acceptance.report.json"] = {
        **common,
        "report_id": "pr169_val1_acceptance",
        "acceptance_state": "pass" if common["pass"] else "fail",
        "do_not_start_paper_loop": True,
    }
    return payloads


def _validate_reports(repo_root: Path) -> list[str]:
    failures: list[str] = []
    report_dir = repo_root / REPORT_DIR
    payloads = build_report_payloads(repo_root)
    for name in REQUIRED_REPORT_NAMES:
        path = report_dir / name
        if not path.exists():
            failures.append(f"VAL1_REPORT_MISSING: {_normal_path(path.relative_to(repo_root))}")
            continue
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"VAL1_REPORT_INVALID_JSON: {name}: {exc}")
            continue
        if current.get("report_id") != payloads[name]["report_id"]:
            failures.append(f"VAL1_REPORT_ID_MISMATCH: {name}")
        if current.get("pass") is not True:
            failures.append(f"VAL1_REPORT_NOT_PASSING: {name}")
    unexpected = sorted(
        path.name
        for path in report_dir.glob("*")
        if path.is_file() and path.name not in REQUIRED_REPORT_NAMES
    )
    for name in unexpected:
        failures.append(f"VAL1_UNEXPECTED_REPORT: {name}")
    return failures


def validate(repo_root: Path, artifact_root: Path | None = None) -> list[str]:
    failures: list[str] = []
    common = common_report_fields(repo_root)
    failures.extend(str(reason) for reason in common["fail_closed_reasons"])
    failures.extend(_validate_reports(repo_root))
    if artifact_root is not None:
        failures.extend(validate_artifacts(artifact_root, runner.ORDERED_PHASES))
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    artifact_root = args.artifact_root
    if artifact_root is not None and not artifact_root.is_absolute():
        artifact_root = repo_root / artifact_root
    failures = validate(repo_root, artifact_root)
    if failures:
        for failure in failures:
            print(f"QTT_PR169_VAL1_FAIL {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
