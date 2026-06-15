from pathlib import Path

from tools import run_validation_gates as runner
from tools import validation_inventory as inventory
from tools.changed_area_validation_router import RouterInput, build_router_result


REPO_ROOT = Path(__file__).resolve().parents[2]


def _pull_request_result(*changed_files: str):
    return build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=tuple(changed_files),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch="feature/small-pr",
        )
    )


def test_pull_request_routes_only_fast_and_touched_pr165_c_area():
    result = _pull_request_result(
        "src/qtt/stage1_prediction_markets/"
        "pr165_c_replay_paper_memory_consumer_integration/paths.py"
    )

    assert result.full_validation_required is False
    assert "validate_validation_inventory" in result.required_validators
    assert (
        "validate_pr165_c_replay_paper_memory_consumer_integration"
        in result.required_validators
    )
    assert (
        "validate_pr165_b_condition_scoped_negative_memory"
        in result.skipped_validators
    )
    assert result.fail_closed_reasons == ()


def test_touched_generated_report_maps_to_owner_validator_and_path_scan():
    result = _pull_request_result(
        "docs/master_plan/generated/PR165_C_FinalSummary.report.json"
    )

    assert (
        "validate_pr165_c_replay_paper_memory_consumer_integration"
        in result.required_validators
    )
    assert result.touched_generated_reports == (
        "docs/master_plan/generated/PR165_C_FinalSummary.report.json",
    )
    assert result.cross_platform_path_scan_required is True
    assert result.fail_closed_reasons == ()


def test_generated_report_without_owner_fails_closed():
    result = _pull_request_result(
        "docs/master_plan/generated/UnownedGeneratedReport.report.json"
    )

    assert result.fail_closed_reasons == (
        "GENERATED_REPORT_OWNER_MISSING: "
        "docs/master_plan/generated/UnownedGeneratedReport.report.json",
    )


def test_validation_infrastructure_change_forces_full_validation():
    result = _pull_request_result("tools/changed_area_validation_router.py")

    assert result.full_validation_required is True
    assert result.full_validation_reason == (
        "validation infrastructure changed: tools/changed_area_validation_router.py"
    )
    assert len(result.required_validators) > 100


def test_main_push_runs_full_validation():
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=("README.md",),
            workflow_event_name="push",
            github_ref="refs/heads/main",
            is_main_push=True,
            current_branch="main",
        )
    )

    assert result.full_validation_required is True
    assert result.full_validation_reason == "main push runs full validation"
    assert result.skipped_validators == ()


def test_router_output_is_deterministic():
    first = _pull_request_result(
        "tests/tools/test_changed_area_validation_router.py",
        "tools/validation_inventory.py",
    )
    second = _pull_request_result(
        "tools/validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
    )

    assert first.to_json_dict() == second.to_json_dict()


def test_pr152_decision_triggers_for_generated_report_count_changes():
    result = _pull_request_result(
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json"
    )

    assert result.pr152_currentization_required is True
    assert "PR152-tracked" in result.pr152_currentization_reason


def test_pr166_sm2_split_pytest_groups_preserve_directory_routing():
    result = _pull_request_result(
        f"{runner.PR166_SM2_TEST_ROOT}/test_pr166_sm2_validator.py"
    )
    expected_ids = {
        inventory.validator_id_for_command(command, "pytest-shard-2")
        for command in runner.build_pytest_shard_commands(
            "pytest-shard-2",
            Path(".tmp") / "pytest",
        )
        if any(part.startswith(f"{runner.PR166_SM2_TEST_ROOT}/") for part in command)
    }

    assert len(expected_ids) == len(runner.PR166_SM2_PYTEST_FILE_GROUPS)
    assert expected_ids.issubset(set(result.required_validators))
    assert result.fail_closed_reasons == ()
