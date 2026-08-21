from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tools import ci_branch_context as context
from tools import validate_idempotence_runtime_containment as validator


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "idempotence_runtime_containment_inventory.json"
)
WORKFLOW_TEXT = (
    REPO_ROOT / ".github" / "workflows" / "qtt_validation.yml"
).read_text(encoding="utf-8")


def _inventory() -> dict[str, object]:
    return deepcopy(validator.load_inventory(INVENTORY_PATH))


def _codes(failures) -> set[str]:
    return {failure.code for failure in failures}


def _validate(
    inventory: dict[str, object],
    *,
    workflow_text: str = WORKFLOW_TEXT,
    changed_paths: tuple[str, ...] = (),
    tracked_paths: tuple[str, ...] = (),
    staged_paths: tuple[str, ...] = (),
    discovered_idempotence=None,
    pytest_membership=None,
    runner_shards=None,
):
    return validator.validate(
        REPO_ROOT,
        inventory=inventory,
        workflow_text=workflow_text,
        changed_paths=changed_paths,
        tracked_paths=tracked_paths,
        staged_paths=staged_paths,
        discovered_idempotence=discovered_idempotence,
        pytest_membership=pytest_membership,
        runner_shards=runner_shards,
    )


def _discovered_with(path: str, **updates):
    discovered = list(validator.discover_idempotence_tests(REPO_ROOT))
    for index, item in enumerate(discovered):
        if item.path == path:
            discovered[index] = validator.DiscoveredIdempotence(
                path=item.path,
                has_verify_idempotent=updates.get(
                    "has_verify_idempotent", item.has_verify_idempotent
                ),
                builder_twice=updates.get("builder_twice", item.builder_twice),
                bounded_contract=updates.get("bounded_contract", item.bounded_contract),
            )
            return tuple(discovered)
    raise AssertionError(f"missing discovered idempotence path: {path}")


def test_current_inventory_passes_and_classifies_runtime_containment():
    inventory = _inventory()
    failures = _validate(inventory)

    assert failures == ()
    assert {entry["phase"] for entry in inventory["pytest_shards"]} == {
        f"pytest-shard-{index}" for index in range(1, 9)
    }
    assert {entry["family"] for entry in inventory["known_heavy_families"]} >= {
        "PR166-SF-R2",
        "PR166-SM3",
        "PR166-SM2",
        "PR165-D3",
        "PR166-S2",
        "PR165-D2",
        "PR166-SF",
        "PR166-SM",
        "PR162E-Q",
    }
    assert all(
        entry["classification"].startswith("RUNTIME_ARTIFACT_")
        for entry in inventory["runtime_artifact_policy"]
    )
    assert {
        entry["classification"]
        for entry in inventory["checkout_fixture_requirements"]
    } == {"CHECKOUT_FIXTURE_CLASSIFIED_ONLY"}
    assert inventory["manual_nightly_exhaustive_paths"]


def test_missing_idempotence_test_classification_fails():
    inventory = _inventory()
    removed = inventory["idempotence_tests"].pop()

    failures = _validate(inventory)

    assert validator.Failure(
        "UNCLASSIFIED_IDEMPOTENCE_TEST", (("path", removed["path"]),)
    ) in failures


def test_default_ci_verify_idempotent_fails_unless_lightweight_and_budgeted():
    inventory = _inventory()
    path = inventory["idempotence_tests"][0]["path"]
    discovered = _discovered_with(path, has_verify_idempotent=True)
    pytest_membership = {path: inventory["idempotence_tests"][0]["pytest_shard"]}

    failures = _validate(
        inventory,
        discovered_idempotence=discovered,
        pytest_membership=pytest_membership,
    )

    assert "DEFAULT_CI_EXHAUSTIVE_VERIFY_IDEMPOTENT" in _codes(failures)


def test_builder_twice_default_ci_without_bounded_contract_fails():
    inventory = _inventory()
    path = (
        "tests/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/test_pr166_sm_idempotence.py"
    )
    discovered = _discovered_with(path, builder_twice=True, bounded_contract=False)
    pytest_membership = {path: "pytest-shard-4"}

    failures = _validate(
        inventory,
        discovered_idempotence=discovered,
        pytest_membership=pytest_membership,
    )

    assert "BUILDER_TWICE_UNBOUNDED_DEFAULT_CI" in _codes(failures)


def test_missing_shard_8_fails():
    inventory = _inventory()
    inventory["pytest_shards"] = [
        entry
        for entry in inventory["pytest_shards"]
        if entry["phase"] != "pytest-shard-8"
    ]

    failures = _validate(inventory)

    assert validator.Failure("MISSING_PYTEST_SHARD", (("shard", "pytest-shard-8"),)) in failures


def test_failed_or_cancelled_shard_not_aggregated_fails():
    inventory = _inventory()
    workflow_text = WORKFLOW_TEXT.replace("          - phase: pytest-shard-8\n", "")

    failures = _validate(inventory, workflow_text=workflow_text)

    assert "SHARD_NOT_AGGREGATED" in _codes(failures)


def test_non_success_result_guard_removed_fails():
    inventory = _inventory()
    workflow_text = WORKFLOW_TEXT.replace('result != "success"', 'result == "failure"')

    failures = _validate(inventory, workflow_text=workflow_text)

    assert "WORKFLOW_AGGREGATION_NOT_FAIL_CLOSED" in _codes(failures)


def test_tracked_router_runtime_artifact_fails():
    failures = _validate(
        _inventory(),
        tracked_paths=(".tmp/qtt-validation-router/fast-preflight.json",),
    )

    assert "RUNTIME_ARTIFACT_TRACKED" in _codes(failures)


def test_staged_timing_runtime_artifact_fails():
    failures = _validate(
        _inventory(),
        staged_paths=(".tmp/qtt-validation-timing/fast-preflight.json",),
    )

    assert "RUNTIME_ARTIFACT_TRACKED" in _codes(failures)


def test_real_source_test_and_generated_files_are_not_runtime_artifacts():
    inventory = _inventory()

    assert not validator.is_runtime_artifact_path("src/qtt/example.py", inventory)
    assert not validator.is_runtime_artifact_path(
        "tests/tools/test_example.py", inventory
    )
    assert not validator.is_runtime_artifact_path(
        "docs/master_plan/generated/PR999_NewReport.report.json", inventory
    )


def test_broad_tmp_runtime_policy_fails():
    inventory = _inventory()
    inventory["runtime_artifact_policy"].append(
        {
            "classification": "RUNTIME_ARTIFACT_IGNORED_IF_UNTRACKED",
            "path_pattern": ".tmp/**",
        }
    )

    failures = _validate(inventory)

    assert "BROAD_TMP_RUNTIME_ARTIFACT_ALLOWLIST" in _codes(failures)


def test_generated_report_payload_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=("docs/master_plan/generated/PR166_Q_New.report.json",),
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_exact_registered_repair_scope_allows_only_current_pr152_report():
    branch = context.ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_BRANCH
    pr152_report = (
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    )

    assert validator._allowed_explicit_roadmap_feature_touch(
        branch,
        pr152_report,
        auto_discovered_changed_paths=True,
    )
    assert validator._validate_changed_files(
        _inventory(),
        (pr152_report,),
        workflow_text=WORKFLOW_TEXT,
        current_branch=branch,
        auto_discovered_changed_paths=True,
    ) == []

    for denied_path in (
        "docs/master_plan/generated/Unrelated.report.json",
        "docs/master_plan/generated/PR208_FinalSummary.report.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/roadmap/generated/Unrelated.report.json",
    ):
        assert not validator._allowed_explicit_roadmap_feature_touch(
            branch,
            denied_path,
            auto_discovered_changed_paths=True,
        )

    for adversarial_branch in (
        branch.upper(),
        f"{branch}-suffix",
        f"{branch}/",
        branch.replace("receipt-closure", "receipts-closure"),
        "repair/st12-unregistered-repair",
    ):
        assert not validator._allowed_explicit_roadmap_feature_touch(
            adversarial_branch,
            pr152_report,
            auto_discovered_changed_paths=True,
        )


def test_master_plan_content_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=("docs/master_plan/QTT_MasterPlan_Current.md",),
    )

    assert "FORBIDDEN_MASTER_PLAN_CHANGE" in _codes(failures)


def test_pr166_q_business_file_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=(
            "src/qtt/stage1_prediction_markets/pr166_q_quantum_next/logic.py",
        ),
    )

    assert "FORBIDDEN_PR166_Q_BUSINESS_CHANGE" in _codes(failures)


def test_pr166_q_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
            "docs/master_plan/generated/pr166_q_shards/"
            "PR166_Q_QuantumStructuralReadiness.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/report_writer.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-q-quantum-classical-hybrid-comparator",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr166_q_github_pr_merge_ref_auto_discovered_changes_are_allowed(
    monkeypatch,
):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/222/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "222/merge")
    monkeypatch.setenv(
        "GITHUB_HEAD_REF",
        "pr166-q-quantum-classical-hybrid-comparator",
    )
    monkeypatch.setattr(
        validator,
        "_changed_paths",
        lambda _repo_root: (
            "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/validator.py",
            "tests/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/"
            "test_pr166_q_validator.py",
        ),
    )
    monkeypatch.setattr(validator, "_tracked_paths", lambda _repo_root: ())
    monkeypatch.setattr(validator, "_staged_paths", lambda _repo_root: ())

    failures = validator.validate(
        REPO_ROOT,
        inventory=_inventory(),
        workflow_text=WORKFLOW_TEXT,
    )

    assert "FORBIDDEN_PR166_Q_BUSINESS_CHANGE" not in _codes(failures)
    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" not in _codes(failures)


def test_pr166_q_branch_scoped_exception_does_not_allow_master_plan():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/QTT_MasterPlan_Current.md",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-q-quantum-classical-hybrid-comparator",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_MASTER_PLAN_CHANGE" in _codes(failures)


def test_pr168_rp5e_shared_receipt_currentization_is_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
            "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
            "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rp5e-stack-gen",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" not in _codes(failures)


def test_pr168_rp5f_pr152_currentization_is_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
            "tools/validate_pr168_rp5f_dynamic_targets.py",
            "tests/pr168_rp5f/test_validation.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rp5f-dynamic-target-order-grid",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" not in _codes(failures)


def test_pr166_qb_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR166_QB_FinalSummary.report.json",
            "docs/master_plan/generated/pr166_qb_shards/"
            "PR166_QB_RaceArb.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_qb_bounded_quantum_benchmark/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr166_qb_bounded_quantum_benchmark/test_pr166_qb_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qb-bounded-nonlive-quantum-optimizer-benchmark",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr166_qb_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_Q_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qb-bounded-nonlive-quantum-optimizer-benchmark",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr166_qc_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR166_QC_FinalSummary.report.json",
            "docs/master_plan/generated/pr166_qc_shards/"
            "PR166_QC_ReplayEvidence.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr166_qc_quantum_selected_replay_paper_retest/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qc-quantum-selected-replay-paper-retest",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr166_qc_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_QB_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr166-qc-quantum-selected-replay-paper-retest",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr162e_q_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR162E_Q_FinalSummary.report.json",
            "docs/master_plan/generated/pr162e_q_shards/"
            "PR162E_Q_MapEligibility.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr162e_q_quantum_automapper/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr162e_q_quantum_automapper/test_pr162e_q_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-q-quantum-automapper",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr162e_q_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_QC_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-q-quantum-automapper",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr162e_plugin_framework_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR162E_FinalSummary.report.json",
            "docs/master_plan/generated/PR162E_PluginRegistry.report.json",
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr162e_plugin_framework/report_writer.py",
            "src/qtt/plugins/contracts.py",
            "tests/pr162e/test_pr162e_plugin_abi.py",
            "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-plugin-framework",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr162e_plugin_framework_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR167_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr162e-plugin-framework",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr167_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/PR167_FinalSummary.report.json",
            "docs/master_plan/generated/pr167_shards/"
            "PR167_SimEligibility.part_0001_of_0001.report.json",
            "src/qtt/stage1_prediction_markets/"
            "pr167_open_trade_simulator_integration/report_writer.py",
            "tests/stage1_prediction_markets/"
            "pr167_open_trade_simulator_integration/test_pr167_artifacts.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr167-open-trade-simulator-integration",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr167_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR166_QC_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr167-open-trade-simulator-integration",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr168_rank_branch_scoped_auto_discovered_changes_are_allowed():
    failures = validator._validate_changed_files(
        _inventory(),
        (
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
            "docs/master_plan/generated/PR168_RANK_FinalSummary.report.json",
            "docs/master_plan/generated/pr168_rank_shards/"
            "PR168_RANK_EvidenceBackedRanking.part_0001_of_0001.report.json",
            "tools/pr168_rank_compute_kernel.py",
            "tools/validate_pr168_rank_input_consumption.py",
            "tests/pr168_rank/test_input_consumption.py",
        ),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rank-evidence-backed-ranking",
        auto_discovered_changed_paths=True,
    )

    assert failures == []


def test_pr168_rank_branch_scoped_exception_does_not_allow_other_reports():
    failures = validator._validate_changed_files(
        _inventory(),
        ("docs/master_plan/generated/PR168_RP_FinalSummary.report.json",),
        workflow_text=WORKFLOW_TEXT,
        current_branch="pr168-rank-evidence-backed-ranking",
        auto_discovered_changed_paths=True,
    )

    assert "FORBIDDEN_GENERATED_REPORT_PAYLOAD_CHANGE" in _codes(failures)


def test_pr165_d3_business_file_change_is_rejected_for_hardening_pr():
    failures = _validate(
        _inventory(),
        changed_paths=(
            "src/qtt/stage1_prediction_markets/"
            "pr165_d3_quantum_aware_scenario_selection_v3/report_writer.py",
        ),
    )

    assert "FORBIDDEN_PR165_D3_BUSINESS_CHANGE" in _codes(failures)


def test_sparse_checkout_profile_addition_is_rejected_when_main_checkout_green():
    failures = _validate(
        _inventory(),
        changed_paths=(".github/sparse-checkout/runtime-profile.txt",),
    )

    assert "SPARSE_CHECKOUT_EXPERIMENT_BLOCKED" in _codes(failures)


def test_removed_inventory_path_fails_unless_removed_with_reason():
    inventory = _inventory()
    inventory["manual_nightly_exhaustive_paths"].append(
        {
            "classification": "MANUAL_NIGHTLY_EXHAUSTIVE_IDEMPOTENCE",
            "path": "tools/build_removed_exhaustive.py",
        }
    )

    failures = _validate(inventory)

    assert "STALE_INVENTORY_ENTRY" in _codes(failures)

    inventory["manual_nightly_exhaustive_paths"][-1][
        "removed_with_reason"
    ] = "synthetic removed path for staleness test"
    failures = _validate(inventory)

    assert "STALE_INVENTORY_ENTRY" not in _codes(failures)


def test_newly_discovered_idempotence_file_missing_from_inventory_fails():
    inventory = _inventory()
    discovered = tuple(validator.discover_idempotence_tests(REPO_ROOT)) + (
        validator.DiscoveredIdempotence(
            path="tests/stage1_prediction_markets/pr999/test_new_idempotence.py",
            has_verify_idempotent=False,
            builder_twice=True,
            bounded_contract=False,
        ),
    )

    failures = _validate(inventory, discovered_idempotence=discovered)

    assert "UNCLASSIFIED_IDEMPOTENCE_TEST" in _codes(failures)


def test_renamed_pytest_shard_not_reflected_in_inventory_fails():
    inventory = _inventory()
    for entry in inventory["pytest_shards"]:
        if entry["phase"] == "pytest-shard-8":
            entry["phase"] = "pytest-shard-eight"

    failures = _validate(inventory)

    assert "MISSING_PYTEST_SHARD" in _codes(failures)


def test_unknown_workflow_job_missing_classification_fails():
    inventory = _inventory()
    workflow_text = WORKFLOW_TEXT + "\n  surprise_job:\n    name: Surprise Job\n"

    failures = _validate(inventory, workflow_text=workflow_text)

    assert validator.Failure(
        "UNCLASSIFIED_WORKFLOW_JOB", (("job", "surprise_job"),)
    ) in failures
