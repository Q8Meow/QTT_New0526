from pathlib import Path

from tools import run_validation_gates as runner
from tools import validation_inventory as inventory
from tools import changed_area_validation_router as router
from tools.changed_area_validation_router import (
    RouterInput,
    build_router_result,
    build_routing_policy_report,
)


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


def test_pr168_gfp2r_generated_report_maps_to_owner_validator():
    result = _pull_request_result(
        "docs/master_plan/generated/PR168_GFP2R_FinalSummary.report.json"
    )

    assert (
        "validate_pr168_gfp2r_data1a_gated_candidate_recompute"
        in result.required_validators
    )
    assert result.touched_generated_reports == (
        "docs/master_plan/generated/PR168_GFP2R_FinalSummary.report.json",
    )
    assert result.cross_platform_path_scan_required is True
    assert result.fail_closed_reasons == ()


def test_pr168_rp2_generated_report_maps_to_owner_validator():
    result = _pull_request_result(
        "docs/master_plan/generated/PR168_RP2_Final.report.json"
    )

    assert "validate_pr168_rp2_map2" in result.required_validators
    assert result.touched_generated_reports == (
        "docs/master_plan/generated/PR168_RP2_Final.report.json",
    )
    assert result.cross_platform_path_scan_required is True
    assert result.fail_closed_reasons == ()


def test_pr168_map3_generated_report_maps_to_owner_validator():
    result = _pull_request_result(
        "docs/master_plan/generated/PR168_MAP3_FinalSummary.report.json"
    )

    assert "validate_pr168_map3" in result.required_validators
    assert result.touched_generated_reports == (
        "docs/master_plan/generated/PR168_MAP3_FinalSummary.report.json",
    )
    assert result.cross_platform_path_scan_required is True
    assert result.fail_closed_reasons == ()


def test_pr168_map3_validator_tool_maps_to_owner_validator():
    result = _pull_request_result("tools/validate_pr168_map3.py")

    assert "validate_pr168_map3" in result.required_validators
    assert result.fail_closed_reasons == ()
    assert "tools/validate_pr168_map3.py" not in result.unknown_files


def test_pr168_rp3_generated_report_maps_to_owner_validator():
    result = _pull_request_result(
        "docs/master_plan/generated/PR168_RP3_FinalSummary.report.json"
    )

    assert "validate_pr168_rp3" in result.required_validators
    assert result.touched_generated_reports == (
        "docs/master_plan/generated/PR168_RP3_FinalSummary.report.json",
    )
    assert result.cross_platform_path_scan_required is True
    assert result.fail_closed_reasons == ()


def test_pr168_rp3_validator_tool_maps_to_owner_validator():
    result = _pull_request_result("tools/validate_pr168_rp3.py")

    assert "validate_pr168_rp3" in result.required_validators
    assert result.fail_closed_reasons == ()
    assert "tools/validate_pr168_rp3.py" not in result.unknown_files


def test_pr169_svc1_shared_ci_repair_paths_map_to_svc1_validators():
    paths = (
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "tools/pr168_rp5c_config.py",
    )
    result = _pull_request_result(*paths)

    assert "build_pr169_svc1" in result.required_validators
    assert "validate_pr169_svc1" in result.required_validators
    assert result.fail_closed_reasons == ()
    for path in paths:
        assert path not in result.unknown_files


def test_pr168_rp5d_r1_generated_output_routes_only_to_rp5d_r1_owner():
    result = _pull_request_result(
        "docs/master_plan/generated/pr168_rp5d_r1/agent_consume.jsonl"
    )

    assert result.full_validation_required is False
    assert result.fail_closed_reasons == ()
    assert "build_pr168_rp5d_r1_exec_now_unlock" in result.required_validators
    assert "validate_pr168_rp5d_r1_exec_now_unlock" in result.required_validators
    assert "validate_pr168_rp_validation_scope_registry_integration" not in (
        result.required_validators
    )
    assert "build_pr168_rp_formula_based_replay_paper_recompute" not in (
        result.required_validators
    )


def test_pr168_rp5f_generated_output_routes_only_to_rp5f_owner():
    result = _pull_request_result(
        "docs/master_plan/generated/pr168_rp5f/targets.jsonl"
    )

    assert result.full_validation_required is False
    assert result.fail_closed_reasons == ()
    assert "build_pr168_rp5f_dynamic_targets" in result.required_validators
    assert "validate_pr168_rp5f_dynamic_targets" in result.required_validators
    assert "validate_pr168_rp_validation_scope_registry_integration" not in (
        result.required_validators
    )
    assert "build_pr168_rp_formula_based_replay_paper_recompute" not in (
        result.required_validators
    )
    assert "validate_pr168_rp5e_stack_gen" not in result.required_validators


def test_generated_report_without_owner_fails_closed():
    result = _pull_request_result(
        "docs/master_plan/generated/UnownedGeneratedReport.report.json"
    )

    assert result.fail_closed_reasons == (
        "GENERATED_REPORT_OWNER_MISSING: "
        "docs/master_plan/generated/UnownedGeneratedReport.report.json",
    )


def test_validation_infrastructure_change_forces_full_validation():
    validation_infrastructure_paths = (
        "tools/changed_area_validation_router.py",
        "tools/validate_no_runtime_artifacts.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
    )

    for path in validation_infrastructure_paths:
        result = _pull_request_result(path)

        assert result.full_validation_required is True
        assert result.full_validation_reason == (
            f"validation infrastructure changed: {path}"
        )
        assert result.skipped_validators == ()
        assert result.fail_closed_reasons == ()
        assert result.unknown_files == ()
        assert len(result.required_validators) == len(inventory.validation_inventory())


def test_qku_control_plane_change_routes_all_central_validators():
    path = (
        "src/qtt/stage1_prediction_markets/"
        "qku_computation_control_plane/accounting.py"
    )
    result = _pull_request_result(path)

    assert router.QKU_VALIDATOR_IDS <= set(result.required_validators)
    assert inventory.ST12C_QKU_VALIDATOR_IDS <= set(result.required_validators)
    assert path not in result.unknown_files
    assert result.fail_closed_reasons == ()
    assert "QKU computation control plane" in result.touched_domains
    assert result.full_validation_required is True


def test_qku_shared_integration_paths_use_the_exact_allowlists() -> None:
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=tuple(sorted(inventory.QKU_ALLOWED_EXACT_PATHS)),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch="feature/small-pr",
        )
    )
    assert router.QKU_ALLOWED_EXACT_PATHS == inventory.QKU_ALLOWED_EXACT_PATHS
    assert inventory.QKU_ALLOWED_EXACT_PATHS == frozenset(
        (
            *inventory.ST12A_ALLOWED_EXACT_PATHS,
            *inventory.ST12B_ALLOWED_EXACT_PATHS,
                *inventory.ST12C_ALLOWED_EXACT_PATHS,
                *inventory.ST12D_ALLOWED_EXACT_PATHS,
                *inventory.ST12E_ALLOWED_EXACT_PATHS,
                *inventory.ST12F_ALLOWED_EXACT_PATHS,
                *inventory.ST12G_ALLOWED_EXACT_PATHS,
                *inventory.ST12H_ALLOWED_EXACT_PATHS,
            )
        )
    for path in inventory.QKU_ALLOWED_EXACT_PATHS:
        assert router.QKU_VALIDATOR_IDS <= set(result.classified_files[path])
    assert result.unknown_files == ()
    assert result.fail_closed_reasons == ()


def test_local_git_change_collection_unions_all_four_surfaces(monkeypatch):
    outputs = {
        (
            "diff",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            "origin/main...HEAD",
        ): "committed.py\nshared.py\n",
        (
            "diff",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            "HEAD",
        ): "unstaged.py\nshared.py\n",
        (
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRTUXB",
        ): "staged.py\n",
        ("ls-files", "--others", "--exclude-standard"): "untracked.py\n",
    }

    monkeypatch.setattr(
        router,
        "_git_stdout",
        lambda _root, args: (0, outputs[tuple(args)], ""),
    )

    assert router.changed_files_from_git(REPO_ROOT) == (
        "committed.py",
        "shared.py",
        "staged.py",
        "unstaged.py",
        "untracked.py",
    )


def test_st12e_paths_route_all_six_e_validators() -> None:
    path = (
        "docs/master_plan/generated/qku_control_plane/"
        "agent_capability/manifest.json"
    )
    result = _pull_request_result(path)

    assert inventory.ST12E_QKU_VALIDATOR_IDS <= set(
        result.required_validators
    )
    assert path not in result.unknown_files
    assert result.fail_closed_reasons == ()

    unallowlisted = (
        "src/qtt/stage1_prediction_markets/"
        "qku_computation_control_plane/runtime.py"
    )
    unallowlisted_result = _pull_request_result(unallowlisted)
    assert unallowlisted_result.unknown_files == (unallowlisted,)
    assert unallowlisted_result.full_validation_required is True
    assert unallowlisted_result.full_validation_reason == (
        "unknown changed files force full validation"
    )


def test_st12d_paths_route_every_d_validator_without_skips() -> None:
    path = (
        "docs/master_plan/generated/qku_control_plane/"
        "mode_snapshot/manifest.json"
    )
    result = _pull_request_result(path)

    assert inventory.ST12D_QKU_VALIDATOR_IDS <= set(result.required_validators)
    assert path not in result.unknown_files
    assert result.skipped_validators == ()
    assert result.fail_closed_reasons == ()


def test_qtt_authority_registry_change_routes_to_owner_validator():
    result = _pull_request_result("tools/qtt_authority_reason_code_registry.py")

    assert result.full_validation_required is True
    assert "validate_qtt_authority_reason_code_registry" in result.required_validators
    assert result.fail_closed_reasons == ()
    assert "tools/qtt_authority_reason_code_registry.py" not in result.unknown_files


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


def test_pr152_decision_is_clean_after_currentization_counts_match(monkeypatch):
    monkeypatch.setattr(
        router,
        "_pr152_currentization_report_matches_filesystem",
        lambda _repo_root: True,
    )
    result = _pull_request_result(
        "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json"
    )

    assert result.pr152_currentization_required is False
    assert "matches filesystem counts" in result.pr152_currentization_reason


def test_pr152_inventory_counts_include_current_tracked_surfaces(tmp_path):
    paths = (
        tmp_path / "docs/master_plan/generated/Current.report.json",
        tmp_path
        / "tests/stage1_prediction_markets/qku_computation_control_plane"
        / "architecture/test_current_surface.py",
        tmp_path / "tools/validate_qku_computation_control_plane.py",
    )
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n" if path.suffix == ".json" else "# tracked\n", encoding="utf-8")

    assert router._current_pr152_inventory_counts(tmp_path) == {
        "generated_report_count": 1,
        "test_file_count": 1,
        "validator_tool_count": 1,
    }


def test_pr152_decision_triggers_when_currentization_report_is_stale(monkeypatch):
    monkeypatch.setattr(
        router,
        "_pr152_currentization_report_matches_filesystem",
        lambda _repo_root: False,
    )
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
        inventory.validator_id_for_command(command, "pytest-shard-5")
        for command in runner.build_pytest_shard_commands(
            "pytest-shard-5",
            Path(".tmp") / "pytest",
        )
        if any(part.startswith(f"{runner.PR166_SM2_TEST_ROOT}/") for part in command)
    }

    assert len(expected_ids) == len(runner.PR166_SM2_PYTEST_FILE_GROUPS)
    assert expected_ids.issubset(set(result.required_validators))
    assert inventory.VALIDATION_MATRIX_JOB_ID in result.required_jobs
    assert result.fail_closed_reasons == ()


def test_pr166_sf_r2_split_pytest_groups_preserve_directory_routing():
    result = _pull_request_result(
        f"{runner.PR166_SF_R2_TEST_ROOT}/test_pr166_sf_r2_validator.py"
    )
    expected_ids = {
        inventory.validator_id_for_command(command, phase)
        for phase in ("pytest-shard-4", "pytest-shard-6")
        for command in runner.build_pytest_shard_commands(
            phase,
            Path(".tmp") / "pytest",
        )
        if any(part.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/") for part in command)
    }

    assert len(expected_ids) == len(runner.PR166_SF_R2_PYTEST_FILE_GROUPS)
    assert expected_ids.issubset(set(result.required_validators))
    assert inventory.VALIDATION_MATRIX_JOB_ID in result.required_jobs
    assert result.fail_closed_reasons == ()


def test_router_policy_report_knows_all_eight_pytest_shard_jobs():
    report = build_routing_policy_report()
    expected_jobs = [inventory.VALIDATION_MATRIX_JOB_ID]

    assert report["required_jobs_for_reduced_pr_mode"] == expected_jobs
    assert report["required_jobs_for_full_mode"] == expected_jobs


def test_st12f_current_main_path_routes_all_focused_validators() -> None:
    result = _pull_request_result(
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py"
    )
    assert inventory.ST12F_QKU_VALIDATOR_IDS <= set(result.required_validators)
    assert result.fail_closed_reasons == ()


def test_every_st12g_path_routes_all_g_and_existing_owner_validators() -> None:
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=tuple(sorted(inventory.ST12G_ALLOWED_EXACT_PATHS)),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch="agent/st12g-existing-owner-projections-v2",
        )
    )
    assert len(inventory.ST12G_ALLOWED_EXACT_PATHS) == 65
    for path in inventory.ST12G_ALLOWED_EXACT_PATHS:
        assert inventory.ST12G_REQUIRED_VALIDATOR_IDS <= set(
            result.classified_files[path]
        )
    assert result.unknown_files == ()
    assert result.fail_closed_reasons == ()


def test_st12h_exact_paths_route_required_validators_and_protect_predecessors() -> None:
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=tuple(sorted(inventory.ST12H_ACTIVE_PATHS)),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch="agent/st12h-validation-currentization-operations-publication",
        )
    )
    assert len(inventory.ST12H_ACTIVE_PATHS) == 25
    assert result.unknown_files == ()
    assert result.fail_closed_reasons == ()
    for path in inventory.ST12H_ACTIVE_PATHS:
        assert inventory.ST12H_REQUIRED_VALIDATOR_IDS <= set(
            result.classified_files[path]
        )
    for path in (
        ".github/workflows/qtt_validation.yml",
        "tools/changed_area_validation_router.py",
        "tests/tools/test_validation_inventory.py",
    ):
        focused = _pull_request_result(path)
        assert focused.full_validation_required is True

    protected_path = sorted(router.ST12H_READ_ONLY_PREDECESSOR_PATHS)[0]
    protected = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=(protected_path,),
            current_branch="agent/st12h-validation-currentization-operations-publication",
        )
    )
    assert protected.fail_closed_reasons == (
        f"ST12H_READ_ONLY_PREDECESSOR_CHANGED: {protected_path}",
    )
