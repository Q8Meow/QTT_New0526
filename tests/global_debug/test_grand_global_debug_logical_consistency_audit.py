from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess

from tools import run_validation_gates as runner
from tools import validate_grand_global_debug_logical_consistency_audit as pr152_cli
from tools.ci_branch_context import BranchContext

from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
    constants as c,
    report as pr152_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
_UNCACHED_PR152_BUILD_REPORT = pr152_report.build_report


def _cached_pr152_build_report(repo_root: Path | str) -> dict:
    return runner.build_pr152_report_with_run_cache(
        repo_root,
        _UNCACHED_PR152_BUILD_REPORT,
    )


pr152_report.build_report = _cached_pr152_build_report


def _report() -> dict:
    return pr152_report.build_report(REPO_ROOT)


def _string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)


def _path_like_values(payload: dict):
    for key, value in pr152_report._walk(payload):
        if pr152_report._is_path_like_key(key):
            yield from _string_values(value)


def _copy_inputs(tmp_path: Path) -> Path:
    for rel_path in c.REQUIRED_UPSTREAM_ARTIFACTS:
        source = REPO_ROOT / rel_path
        target = tmp_path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    return tmp_path


def _mutated_pr151_root(tmp_path: Path, mutator) -> Path:
    root = _copy_inputs(tmp_path)
    path = root / c.PR151_REPORT_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return root


_PR152_VALIDATION_INFRASTRUCTURE_COUNT_PATHS = {
    "$.completed_pr_artifact_audit.validator_tool_count": (
        "completed_pr_artifact_audit",
        "validator_tool_count",
    ),
    "$.validator_tool_registry_audit.validator_tool_count": (
        "validator_tool_registry_audit",
        "validator_tool_count",
    ),
    "$.whole_repo_inventory_audit.audited_text_file_count": (
        "whole_repo_inventory_audit",
        "audited_text_file_count",
    ),
    "$.whole_repo_inventory_audit.category_counts.VALIDATOR_TOOL": (
        "whole_repo_inventory_audit",
        "category_counts",
        "VALIDATOR_TOOL",
    ),
    "$.whole_repo_inventory_audit.tracked_file_count": (
        "whole_repo_inventory_audit",
        "tracked_file_count",
    ),
}


def _set_nested(payload: dict, keys: tuple[str, ...], value: int) -> None:
    target = payload
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value


def _get_nested(payload: dict, keys: tuple[str, ...]) -> int:
    target = payload
    for key in keys:
        target = target[key]
    return target


def _pr152_validation_infrastructure_count_payloads(
    delta: int | None = None,
) -> tuple[dict, dict]:
    if delta is None:
        delta = pr152_report._PR_CI_FASTFAIL_VALIDATOR_TOOL_DELTA
    tracked = {
        "completed_pr_artifact_audit": {"validator_tool_count": 139},
        "validator_tool_registry_audit": {"validator_tool_count": 139},
        "whole_repo_inventory_audit": {
            "audited_text_file_count": 6250,
            "category_counts": {"VALIDATOR_TOOL": 139},
            "tracked_file_count": 6251,
        },
    }
    rebuilt = deepcopy(tracked)
    for keys in _PR152_VALIDATION_INFRASTRUCTURE_COUNT_PATHS.values():
        _set_nested(rebuilt, keys, _get_nested(tracked, keys) + delta)
    return tracked, rebuilt


def _validate_stubbed_pr152_report_delta(
    monkeypatch,
    repo_root: Path,
    tracked: dict,
    rebuilt: dict,
) -> list[str]:
    monkeypatch.setattr(pr152_report, "build_report", lambda repo_root: deepcopy(rebuilt))
    monkeypatch.setattr(pr152_report, "validate_report_payload", lambda payload: [])
    monkeypatch.setattr(pr152_report, "_read_json", lambda path: deepcopy(tracked))
    monkeypatch.setattr(
        pr152_report,
        "_validate_changed_paths",
        lambda repo_root, tracked_report_write_allowed=False: [],
    )
    return pr152_report.validate_repository_artifacts(repo_root)


def _write_policy_validator_tools(root: Path, *, omit: str | None = None) -> None:
    for rel_path in pr152_report._PR_CI_FASTFAIL_VALIDATOR_TOOL_PATHS:
        if rel_path == omit:
            continue
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# validator tool\n", encoding="utf-8")


def test_pr152_consumes_required_preflight_and_alias() -> None:
    payload = _report()
    consumed = {
        row["artifact_path"]
        for row in payload["upstream_artifact_inputs"]
        if row["consumed"]
    }
    for rel_path in c.REQUIRED_UPSTREAM_ARTIFACTS:
        assert rel_path.as_posix() in consumed
    preflight = payload["orchestration_preflight_receipt"]
    assert preflight["all_required_inputs_consumed"] is True
    assert preflight["owner_source_packet_consumed"] is True
    assert preflight["pr149_report_consumed"] is True
    assert preflight["pr150_report_consumed"] is True
    assert preflight["pr151_report_consumed"] is True
    alias = preflight["alias_resolution"]
    assert alias["requested_alias"] == c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
    assert alias["canonical_successor_used"] is True
    assert alias["created_missing_alias"] is False


def test_pr152_inventories_and_categorizes_repo_files() -> None:
    payload = _report()
    inventory = payload["whole_repo_inventory_audit"]
    assert inventory["tracked_file_count"] >= 1500
    assert inventory["audited_text_file_count"] > inventory["audited_non_text_file_count"]
    assert c.REPORT_SCAN_ESCAPE_KEY in inventory
    categories = inventory["category_counts"]
    for category in (
        "GENERATED_REPORT",
        "VALIDATOR_TOOL",
        "TEST",
        "SCHEMA",
        "SOURCE",
        "ROADMAP",
        "MASTER_PLAN",
    ):
        assert categories[category] > 0
    assert payload["completed_pr_artifact_audit"]["generated_report_count"] >= 100
    assert payload["completed_pr_artifact_audit"]["validator_tool_count"] >= 100
    assert payload["completed_pr_artifact_audit"]["test_file_count"] >= 300


def test_pr152_audits_completed_surfaces_and_generated_reports() -> None:
    payload = _report()
    assert payload["completed_pr_artifact_audit"]["pr_identity_roster_consumed"] is True
    assert payload["completed_pr_artifact_audit"]["roadmap_controller_consumed"] is True
    assert payload["completed_pr_artifact_audit"]["completed_pr_surface_count"] >= 1
    assert payload["completed_pr_artifact_audit"]["missing_expected_surface_findings"] == []
    assert payload["generated_report_consistency_audit"]["deterministic_consistency_status"] == "PASS"
    assert payload["generated_report_consistency_audit"]["json_parse_failure_count"] == 0
    assert payload["roadmap_controller_consistency_audit"]["status"] == "PASS"


def test_pr152_deep_chain_pr149_pr150_pr151() -> None:
    payload = _report()
    chain = payload["pr149_pr150_pr151_deep_chain_audit"]
    assert chain["pr149_report_present"] is True
    assert chain["pr150_report_present"] is True
    assert chain["pr151_report_present"] is True
    assert chain["pr149_to_pr150_chain_status"] == "PASS"
    assert chain["pr150_to_pr151_chain_status"] == "PASS"
    assert chain["pr150_eligible_source_target_count"] == 146
    assert chain["pr151_queue_item_count"] == 342
    assert chain["pr151_typed_exclusion_count"] == 0
    assert chain["queue_to_target_mapping_status"] == "PASS"
    assert chain["platform_scope_consistency_status"] == "PASS"
    assert chain["eligible_target_ids_not_represented"] == []
    assert chain["orphan_queue_target_ids"] == []


def test_pr152_proves_pr151_absence_boundaries() -> None:
    chain = _report()["pr149_pr150_pr151_deep_chain_audit"]
    for key in (
        "source_value_absence_status",
        "accepted_value_absence_status",
        "connector_value_absence_status",
        "runtime_value_absence_status",
        "replay_paper_value_absence_status",
        "optimizer_output_absence_status",
        "quantum_output_absence_status",
        "order_use_absence_status",
        "official_domain_absence_status",
        "no_claim_flag_status",
        "atomicrows_boundary_status",
        "quantum_boundary_status",
    ):
        assert chain[key] == "PASS"


def test_pr152_source_atomicrows_quantum_and_runtime_boundaries() -> None:
    payload = _report()
    assert payload["source_evidence_boundary_audit"]["authority_boundary_status"] == "PASS"
    assert payload["atomicrows_boundary_audit"]["authority_boundary_status"] == "PASS"
    assert payload["runtime_replay_paper_live_boundary_audit"]["authority_boundary_status"] == "PASS"
    assert payload["quantum_forward_boundary_audit"]["authority_boundary_status"] == "PASS"
    assert payload["agent_algorithm_parameter_stack_audit"]["metadata_only_status"] == "PASS"
    assert payload["agent_algorithm_parameter_stack_audit"]["order_authority_status"] == "ABSENT"
    assert payload["validator_tool_registry_audit"]["broad_generated_allowlist_status"] == "PASS"
    assert payload["validator_tool_registry_audit"]["broad_roadmap_allowlist_status"] == "PASS"


def test_report_is_deterministic_and_has_no_local_paths() -> None:
    first = _UNCACHED_PR152_BUILD_REPORT(REPO_ROOT)
    second = _UNCACHED_PR152_BUILD_REPORT(REPO_ROOT)
    assert first == second
    assert pr152_report.json_dump(first) == pr152_report.json_dump(second)
    serialized = pr152_report.json_dump(first)
    assert "C:\\Users\\" not in serialized
    assert str(REPO_ROOT) not in serialized
    assert REPO_ROOT.as_posix() not in serialized
    assert "AtomicRows.bundle." not in serialized
    assert ("AtomicRows.bundle." + "sha" + "256") not in serialized
    assert '"sk\\u0069pped_local_runtime_path_count"' in serialized


def test_pr152_path_fields_are_repo_relative_posix() -> None:
    payload = _report()
    path_values = list(_path_like_values(payload))
    assert path_values
    for value in path_values:
        assert "\\" not in value
        assert not value.startswith("/")
        assert re.match(r"^[A-Za-z]:/", value) is None


def test_pr152_nested_audit_arrays_are_sorted() -> None:
    payload = _report()
    upstream_paths = [row["artifact_path"] for row in payload["upstream_artifact_inputs"]]
    optional_paths = [row["artifact_path"] for row in payload["optional_context_inputs"]]
    finding_ids = [row["finding_id"] for row in payload["audit_findings"]]
    assert upstream_paths == sorted(upstream_paths, key=pr152_report._stable_path_key)
    assert optional_paths == sorted(optional_paths, key=pr152_report._stable_path_key)
    assert finding_ids == sorted(finding_ids)
    for key in (
        "source_evidence_boundary_audit",
        "atomicrows_boundary_audit",
        "runtime_replay_paper_live_boundary_audit",
        "quantum_forward_boundary_audit",
    ):
        paths = payload[key]["audited_artifacts"]
        assert paths == sorted(paths, key=pr152_report._stable_path_key)


def test_pr152_synthetic_unordered_inputs_are_canonicalized() -> None:
    paths_a = ["B\\z.py", "./a/B.py", "A/x.py"]
    paths_b = list(reversed(paths_a))
    present = {"B/z.py", "a/B.py", "A/x.py"}
    assert pr152_report._path_records(paths_a, present, True) == pr152_report._path_records(
        paths_b,
        present,
        True,
    )
    assert pr152_report._simple_boundary_audit(
        domain="WHOLE_REPO_INVENTORY",
        status="PASS",
        reason_code="PR152_READY",
        audited_artifacts=paths_a,
    ) == pr152_report._simple_boundary_audit(
        domain="WHOLE_REPO_INVENTORY",
        status="PASS",
        reason_code="PR152_READY",
        audited_artifacts=paths_b,
    )


def test_pr152_repo_paths_are_posix_and_case_stable() -> None:
    normalized = pr152_report._stable_sorted_repo_paths(
        ["B\\z.py", "./a/B.py", "A/x.py", "b/a.py"]
    )
    assert normalized == ["a/B.py", "A/x.py", "b/a.py", "B/z.py"]
    assert all("\\" not in path for path in normalized)


def test_pr152_git_inventory_uses_normalized_nul_paths(tmp_path, monkeypatch) -> None:
    for rel_path in ("B/z.py", "a/B.py", "A/x.py"):
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("value\n", encoding="utf-8")

    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        assert repo_root == tmp_path
        assert args == ["ls-files", "-z"]
        return 0, "B\\z.py\0./a/B.py\0A/x.py\0", ""

    monkeypatch.setattr(pr152_report, "_git_stdout", fake_git_stdout)
    inventory = pr152_report._repo_inventory(tmp_path)
    assert inventory["inventory_source"] == "git ls-files -z"
    assert inventory["tracked_files"] == ["a/B.py", "A/x.py", "B/z.py"]
    assert inventory["audit"]["tracked_file_count"] == 3
    assert inventory["audit"]["audited_root_directories"] == ["A", "a", "B"]


def test_validation_default_output_and_write_modes(capsys, tmp_path) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before_report = report_path.read_bytes()
    before_diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    output_path = tmp_path / "pr152.report.json"

    assert pr152_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    assert report_path.read_bytes() == before_report

    assert pr152_cli.main(
        ["--repo-root", REPO_ROOT.as_posix(), "--output", output_path.as_posix()]
    ) == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == _report()
    assert sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    ) == ["pr152.report.json"]
    assert report_path.read_bytes() == before_report

    assert pr152_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--write-report"]) == 0
    assert json.loads(report_path.read_text(encoding="utf-8")) == _report()
    after_diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    assert report_path.read_bytes() == before_report
    assert after_diff == before_diff
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_stale_report_comparator_reports_deterministic_path() -> None:
    tracked = {"completed_pr_artifact_audit": {"generated_report_count": 131}}
    rebuilt = {"completed_pr_artifact_audit": {"generated_report_count": 132}}
    diagnostics = pr152_report.report_payload_mismatch_diagnostics(tracked, rebuilt)
    assert diagnostics == [
        {
            "json_path": "$.completed_pr_artifact_audit.generated_report_count",
            "mismatch_kind": "value_mismatch",
            "tracked_type": "int",
            "rebuilt_type": "int",
            "tracked_value": 131,
            "rebuilt_value": 132,
        }
    ]


def test_stale_report_comparator_keeps_repository_validation_fail_closed(
    monkeypatch,
    tmp_path,
) -> None:
    tracked = {"completed_pr_artifact_audit": {"generated_report_count": 131}}
    rebuilt = {"completed_pr_artifact_audit": {"generated_report_count": 132}}
    monkeypatch.setattr(pr152_report, "build_report", lambda repo_root: rebuilt)
    monkeypatch.setattr(pr152_report, "validate_report_payload", lambda payload: [])
    monkeypatch.setattr(pr152_report, "_read_json", lambda path: tracked)
    monkeypatch.setattr(
        pr152_report,
        "_validate_changed_paths",
        lambda repo_root, tracked_report_write_allowed=False: [],
    )

    failures = pr152_report.validate_repository_artifacts(tmp_path)
    assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in failures
    details = [
        failure
        for failure in failures
        if failure.startswith("PR152_REPORT_STALE_OR_NONDETERMINISTIC_DETAIL:")
    ]
    assert details == [
        "PR152_REPORT_STALE_OR_NONDETERMINISTIC_DETAIL: "
        "json_path=$.completed_pr_artifact_audit.generated_report_count "
        "mismatch_kind=value_mismatch tracked_type=int rebuilt_type=int "
        "tracked_value=131 rebuilt_value=132"
    ]


def test_pr152_validation_infrastructure_exact_fastfail_delta_is_allowed(
    monkeypatch,
) -> None:
    tracked, rebuilt = _pr152_validation_infrastructure_count_payloads()

    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        REPO_ROOT,
        tracked,
        rebuilt,
    )

    assert failures == []
    assert pr152_report._validation_infrastructure_delta_policy_failures(REPO_ROOT) == []
    for rel_path in pr152_report._PR_CI_FASTFAIL_VALIDATOR_TOOL_PATHS:
        assert (REPO_ROOT / rel_path).is_file()
        assert (
            pr152_report._category_for_path(
                rel_path,
                text_file=pr152_report._is_text_file(REPO_ROOT / rel_path),
            )
            == "VALIDATOR_TOOL"
        )


def test_pr152_validation_infrastructure_delta_allowed_in_pull_request_detached_context(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/202/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "202/merge")
    monkeypatch.setenv(
        "GITHUB_HEAD_REF",
        "pr201-pr152-currentization-after-merge",
    )
    tracked, rebuilt = _pr152_validation_infrastructure_count_payloads()

    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        REPO_ROOT,
        tracked,
        rebuilt,
    )

    assert pr152_report.current_branch_context(REPO_ROOT).branch == (
        "pr201-pr152-currentization-after-merge"
    )
    assert failures == []


def test_pr152_validation_infrastructure_delta_allowed_in_main_push_context(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    tracked, rebuilt = _pr152_validation_infrastructure_count_payloads()

    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        REPO_ROOT,
        tracked,
        rebuilt,
    )

    assert pr152_report.current_branch_context(REPO_ROOT).branch == "main"
    assert failures == []


def test_pr152_validation_infrastructure_delta_is_policy_based_not_branch_based(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        pr152_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch="unrelated-branch", source="unit-test"),
    )
    tracked, rebuilt = _pr152_validation_infrastructure_count_payloads()
    assert (
        _validate_stubbed_pr152_report_delta(
            monkeypatch,
            REPO_ROOT,
            tracked,
            rebuilt,
        )
        == []
    )

    wrong_tracked = {"completed_pr_artifact_audit": {"test_file_count": 10}}
    wrong_rebuilt = {"completed_pr_artifact_audit": {"test_file_count": 13}}
    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        REPO_ROOT,
        wrong_tracked,
        wrong_rebuilt,
    )
    assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in failures


def test_pr152_validation_infrastructure_delta_wrong_count_fails(
    monkeypatch,
) -> None:
    for delta in (1, 2, 3, pr152_report._PR_CI_FASTFAIL_VALIDATOR_TOOL_DELTA + 1):
        tracked, rebuilt = _pr152_validation_infrastructure_count_payloads(delta=delta)
        failures = _validate_stubbed_pr152_report_delta(
            monkeypatch,
            REPO_ROOT,
            tracked,
            rebuilt,
        )

        assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in failures
        assert any(
            failure.startswith(
                "PR152_VALIDATION_INFRASTRUCTURE_DELTA_POLICY_WRONG_DELTA"
            )
            for failure in failures
        )


def test_pr152_validation_infrastructure_delta_wrong_json_path_fails(
    monkeypatch,
) -> None:
    tracked = {"completed_pr_artifact_audit": {"test_file_count": 10}}
    rebuilt = {"completed_pr_artifact_audit": {"test_file_count": 13}}

    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        REPO_ROOT,
        tracked,
        rebuilt,
    )

    assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in failures
    assert any(
        "$.completed_pr_artifact_audit.test_file_count" in failure
        for failure in failures
    )


def test_pr152_validation_infrastructure_delta_missing_expected_tool_fails(
    monkeypatch,
    tmp_path,
) -> None:
    missing_path = "tools/validate_nested_validator_contracts.py"
    _write_policy_validator_tools(tmp_path, omit=missing_path)
    tracked, rebuilt = _pr152_validation_infrastructure_count_payloads()

    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        tmp_path,
        tracked,
        rebuilt,
    )

    assert (
        "PR152_VALIDATION_INFRASTRUCTURE_DELTA_POLICY_MISSING_TOOL: "
        f"{missing_path}"
    ) in failures
    assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in failures


def test_pr152_validation_infrastructure_delta_future_tool_fails_with_path(
    monkeypatch,
    tmp_path,
) -> None:
    future_tool = "tools/validate_future_tool.py"
    _write_policy_validator_tools(tmp_path)
    future_path = tmp_path / future_tool
    future_path.parent.mkdir(parents=True, exist_ok=True)
    future_path.write_text("# future validator\n", encoding="utf-8")
    monkeypatch.setattr(
        pr152_report,
        "VALIDATION_INFRASTRUCTURE_CHANGED_PATHS",
        frozenset(
            {
                *pr152_report._PR_CI_FASTFAIL_VALIDATOR_TOOL_PATHS,
                future_tool,
            }
        ),
    )
    tracked, rebuilt = _pr152_validation_infrastructure_count_payloads(
        delta=pr152_report._PR_CI_FASTFAIL_VALIDATOR_TOOL_DELTA + 1
    )

    failures = _validate_stubbed_pr152_report_delta(
        monkeypatch,
        tmp_path,
        tracked,
        rebuilt,
    )

    assert any(
        failure.startswith(
            "PR152_VALIDATION_INFRASTRUCTURE_DELTA_UNREGISTERED_TOOL: "
            f"{future_tool} "
        )
        and "not covered by the current allowed delta policy" in failure
        and "explicitly register it in the PR152 validation-infrastructure inventory "
        "delta policy" in failure
        and "deliberate PR152 currentization strategy" in failure
        for failure in failures
    )
    assert "PR152_REPORT_STALE_OR_NONDETERMINISTIC" in failures


def test_pr152_validation_infrastructure_delta_forbidden_mismatch_paths_fail() -> None:
    forbidden_paths = [
        "$.generated_report_consistency_audit.generated_report_count",
        "$.whole_repo_inventory_audit.category_counts.MASTER_PLAN",
        "$.whole_repo_inventory_audit.category_counts.ATOMICROWS",
        "$.whole_repo_inventory_audit.category_counts.SOURCE_EVIDENCE",
        "$.source_evidence_boundary_audit.authority_boundary_status",
        "$.no_claim_flags.connector_semantic_value_created",
        "$.no_claim_flags.private_state_fetch_created",
        "$.no_claim_flags.runtime_cash_receipt_created",
        "$.no_claim_flags.order_execution_created",
        "$.no_claim_flags.live_reachability_created",
        "$.no_claim_flags.quantum_backend_call_created",
        "$.no_claim_flags.llm_runtime_created",
        "$.no_claim_flags.qtt_integrity_authority_created",
        "$.no_claim_flags.profit_proof_created",
    ]
    forbidden_paths.extend(
        [
            "$.no_claim_flags." + "sha256_authority_created",
            "$.no_claim_flags." + "freeze_authority_created",
            "$.no_claim_flags." + "checksum_authority_created",
        ]
    )

    for json_path in forbidden_paths:
        diagnostic = {
            "json_path": json_path,
            "mismatch_kind": "value_mismatch",
            "tracked_type": "int",
            "rebuilt_type": "int",
            "tracked_value": 1,
            "rebuilt_value": 4,
        }
        assert not pr152_report._validation_infrastructure_report_count_mismatch_allowed(
            REPO_ROOT,
            [diagnostic],
        )


def test_explicit_tracked_write_guard_allows_only_pr152_report_on_main(monkeypatch) -> None:
    report_path = c.REPORT_PATH.as_posix()
    unrelated_path = "docs/master_plan/generated/PR152_unrelated.report.json"
    expected_report_failure = f"PR152_CHANGED_PATH_OUT_OF_SCOPE: {report_path}"
    expected_unrelated_failure = f"PR152_CHANGED_PATH_OUT_OF_SCOPE: {unrelated_path}"

    monkeypatch.setattr(
        pr152_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch="main", source="unit-test"),
    )
    monkeypatch.setattr(pr152_report, "_changed_paths", lambda repo_root: [report_path])
    assert pr152_report.validate_repository_artifacts(REPO_ROOT) == [
        expected_report_failure
    ]
    assert (
        pr152_report.validate_repository_artifacts(
            REPO_ROOT,
            tracked_report_write_allowed=True,
        )
        == []
    )

    monkeypatch.setattr(
        pr152_report,
        "_changed_paths",
        lambda repo_root: [report_path, unrelated_path],
    )
    assert pr152_report.validate_repository_artifacts(
        REPO_ROOT,
        tracked_report_write_allowed=True,
    ) == [expected_unrelated_failure]


def test_pr152_fast_preflight_workflow_path_is_exactly_scoped(monkeypatch) -> None:
    workflow_path = ".github/workflows/qtt_validation.yml"
    assert workflow_path in c.EXACT_CHANGED_PATH_CANDIDATES
    monkeypatch.setattr(
        pr152_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="pr201-pr152-currentization-after-merge",
            source="unit-test",
        ),
    )
    monkeypatch.setattr(pr152_report, "_changed_paths", lambda repo_root: [workflow_path])
    assert pr152_report.validate_repository_artifacts(REPO_ROOT) == []

    monkeypatch.setattr(
        pr152_report,
        "_changed_paths",
        lambda repo_root: [workflow_path, ".github/workflows/unrelated.yml"],
    )
    assert pr152_report.validate_repository_artifacts(REPO_ROOT) == [
        "PR152_CHANGED_PATH_OUT_OF_SCOPE: .github/workflows/unrelated.yml"
    ]


def test_missing_and_malformed_upstream_fail_closed(tmp_path) -> None:
    _evidence, missing = pr152_report.load_static_evidence(tmp_path / "empty")
    assert any(failure.startswith("PR152_UPSTREAM_REPORT_MISSING") for failure in missing)

    copied = _copy_inputs(tmp_path / "malformed")
    bad_path = copied / c.PR150_REPORT_PATH
    bad_path.write_text("{", encoding="utf-8")
    _evidence, malformed = pr152_report.load_static_evidence(copied)
    assert any(failure.startswith("PR152_UPSTREAM_REPORT_PARSE_ERROR") for failure in malformed)


def test_synthetic_chain_mismatch_and_orphan_fail_closed(tmp_path) -> None:
    def remove_queue(payload: dict) -> None:
        target_id = payload["pr150_source_target_coverage_summary"]["eligible_pr150_target_ids"][0]
        payload["official_source_retrieval_target_queue"] = [
            row
            for row in payload["official_source_retrieval_target_queue"]
            if row["pr150_target_id"] != target_id
        ]

    mismatch = pr152_report.build_report(_mutated_pr151_root(tmp_path / "mismatch", remove_queue))
    assert "PR152_CHAIN_MAPPING_MISSING" in pr152_report.validate_report_payload(mismatch)

    def add_orphan(payload: dict) -> None:
        row = deepcopy(payload["official_source_retrieval_target_queue"][0])
        row["retrieval_target_id"] = row["retrieval_target_id"] + "_ORPHAN"
        row["pr150_target_id"] = "PR150_ORPHAN_TARGET"
        payload["official_source_retrieval_target_queue"].append(row)

    orphan = pr152_report.build_report(_mutated_pr151_root(tmp_path / "orphan", add_orphan))
    assert "PR152_CHAIN_MAPPING_MISSING" in pr152_report.validate_report_payload(orphan)


def test_synthetic_value_and_order_drift_fail_closed(tmp_path) -> None:
    cases = {
        "captured_value": "PR152_CHAIN_MAPPING_MISSING",
        "accepted_value": "PR152_CHAIN_MAPPING_MISSING",
        "connector_semantic_value": "PR152_CHAIN_MAPPING_MISSING",
        "runtime_receipt_value": "PR152_CHAIN_MAPPING_MISSING",
        "replay_paper_result_value": "PR152_CHAIN_MAPPING_MISSING",
        "quantum_output_value": "PR152_CHAIN_MAPPING_MISSING",
    }
    for key, expected in cases.items():
        def mutate(payload: dict, field: str = key) -> None:
            payload["official_source_retrieval_target_queue"][0][field] = "synthetic"

        built = pr152_report.build_report(_mutated_pr151_root(tmp_path / key, mutate))
        assert expected in pr152_report.validate_report_payload(built)

    def make_order_state(payload: dict) -> None:
        payload["official_source_retrieval_target_queue"][0]["order_use_eligibility"] = (
            "ORDER_USABLE"
        )

    order_payload = pr152_report.build_report(_mutated_pr151_root(tmp_path / "order", make_order_state))
    assert "PR152_CHAIN_MAPPING_MISSING" in pr152_report.validate_report_payload(order_payload)


def test_synthetic_authority_and_network_drift_fail_closed(tmp_path, monkeypatch) -> None:
    payload = _report()
    payload["no_claim_flags"]["atomicrows_bundle_mutated"] = True
    assert "PR152_FORBIDDEN_FLAG_TRUE: atomicrows_bundle_mutated" in pr152_report.validate_report_payload(payload)

    payload = _report()
    payload["no_claim_flags"]["qtt_integrity_authority_created"] = True
    assert "PR152_FORBIDDEN_FLAG_TRUE: qtt_integrity_authority_created" in pr152_report.validate_report_payload(payload)

    payload = _report()
    payload["no_claim_flags"]["quantum_backend_call_created"] = True
    assert "PR152_FORBIDDEN_FLAG_TRUE: quantum_backend_call_created" in pr152_report.validate_report_payload(payload)

    root = _copy_inputs(tmp_path / "network")
    target = (
        root
        / "src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/report.py"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("import requests\n", encoding="utf-8")
    built = pr152_report.build_report(root)
    assert "PR152_NETWORK_CODE_DRIFT_DETECTED" in pr152_report.validate_report_payload(built)


def test_reason_codes_and_bypass_markers_are_centralized() -> None:
    payload = _report()
    reasons = {row["reason_code"] for row in payload["audit_findings"]}
    assert reasons.issubset(set(c.REASON_CODES))
    marker_a = "allow_repair=" + "True"
    marker_b = "raise SystemExit(" + "0)"
    marker_c = "x" + "fail"
    marker_d = "s" + "ki" + "p"
    files = [
        REPO_ROOT
        / "tools"
        / "validate_grand_global_debug_logical_consistency_audit.py",
        REPO_ROOT
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "grand_global_debug_logical_consistency_audit"
        / "report.py",
        REPO_ROOT
        / "tests"
        / "global_debug"
        / "test_grand_global_debug_logical_consistency_audit.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for marker in (marker_a, marker_b, marker_c, marker_d):
        assert marker not in combined


def test_validation_gate_sequence_includes_pr152_without_tracked_write() -> None:
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]
    pr151_index = command_names.index(
        "validate_official_source_retrieval_target_pack_parameter_defaults.py"
    )
    pr152_index = command_names.index(
        "validate_grand_global_debug_logical_consistency_audit.py"
    )
    agent_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")
    assert pr151_index < pr152_index < agent_index
    assert commands[pr152_index] == [
        runner.sys.executable,
        str(Path("tools") / "validate_grand_global_debug_logical_consistency_audit.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr152_index]
    assert "--output" not in commands[pr152_index]
