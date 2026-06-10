import json
from pathlib import Path

import pytest

from tools.changed_area_validation_router import RouterInput, build_router_result
from tools.cross_platform_path_invariant import (
    path_invariant_failures,
    pr208_generated_reports,
)
from tools.repo_path_refs import normalize_repo_ref, resolve_repo_ref, to_repo_posix
from tools import validation_inventory


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_ref_helper_serializes_posix_and_accepts_legacy_backslashes():
    legacy = r"docs\master_plan\generated\PR165_C_FinalSummary.report.json"
    normalized = "docs/master_plan/generated/PR165_C_FinalSummary.report.json"

    assert normalize_repo_ref(legacy) == normalized
    assert to_repo_posix(REPO_ROOT / normalized, REPO_ROOT) == normalized
    assert resolve_repo_ref(REPO_ROOT, legacy).relative_to(REPO_ROOT).as_posix() == normalized


def test_repo_ref_helper_rejects_unsafe_refs():
    for bad_ref in (
        "",
        "../docs/master_plan/generated/report.json",
        "docs/master_plan/../generated/report.json",
        "/docs/master_plan/generated/report.json",
        r"C:\repo\docs\master_plan\generated\report.json",
    ):
        with pytest.raises(ValueError):
            resolve_repo_ref(REPO_ROOT, bad_ref)


def test_generated_json_path_backslash_refs_fail(tmp_path):
    report = tmp_path / "docs" / "master_plan" / "generated" / "Bad.report.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps({"shard_path": r"docs\master_plan\generated\shard.json"}),
        encoding="utf-8",
    )

    failures = path_invariant_failures(
        tmp_path,
        ("docs/master_plan/generated/Bad.report.json",),
    )

    assert len(failures) == 1
    assert "backslash in serialized path ref" in failures[0].reason


def test_generated_json_root_marker_dot_is_not_treated_as_file_ref(tmp_path):
    report = tmp_path / "docs" / "master_plan" / "generated" / "Root.report.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"field_path": "."}), encoding="utf-8")

    assert (
        path_invariant_failures(
            tmp_path,
            ("docs/master_plan/generated/Root.report.json",),
        )
        == ()
    )


def test_router_normalizes_windows_style_changed_paths_for_linux_ci():
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=(
                r"docs\master_plan\generated\PR165_C_FinalSummary.report.json",
            ),
            workflow_event_name="pull_request",
            is_pull_request=True,
        )
    )

    assert result.changed_files == (
        "docs/master_plan/generated/PR165_C_FinalSummary.report.json",
    )
    assert (
        "validate_pr165_c_replay_paper_memory_consumer_integration"
        in result.required_validators
    )


def test_pr208_generated_reports_do_not_contain_backslash_path_refs_if_present():
    reports = pr208_generated_reports(REPO_ROOT)

    assert path_invariant_failures(REPO_ROOT, reports) == ()


def test_validator_inventory_globs_are_posix_for_cross_platform_ci():
    for entry in validation_inventory.validation_inventory():
        for glob in entry.required_when_files_match:
            assert "\\" not in glob
