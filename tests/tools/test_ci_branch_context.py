from pathlib import Path

from tools import ci_branch_context as context


REPO_ROOT = Path(__file__).resolve().parents[2]
GITHUB_BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)


def _clear_github_branch_context_env(monkeypatch):
    for env_name in GITHUB_BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def test_repair_and_main_cumulative_branch_classification():
    assert context.is_repair_branch("repair/pr138-main-push-ci-context") is True
    assert context.is_main_cumulative_branch("main") is True
    assert context.is_main_cumulative_branch("repair/main-cumulative-example") is True
    assert context.is_downstream_roadmap_branch(
        "feature/non-downstream-validation",
        after_pr=97,
    ) is False
    assert context.is_repair_branch("feature/non-downstream-validation") is False


def test_roadmap_pr_number_parses_pr_branches():
    assert context.roadmap_pr_number("pr97-atomicrows-full-bundle-row-expansion-plan") == 97
    assert (
        context.roadmap_pr_number(
            "pr99-atomicrows-bundle-builder-deterministic-assembly-gate"
        )
        == 99
    )


def test_downstream_or_main_validation_branch_respects_same_pr_boundary():
    assert (
        context.is_downstream_or_main_validation_branch(
            "repair/pr138-main-push-ci-context",
            after_pr=97,
        )
        is True
    )
    assert context.is_downstream_or_main_validation_branch("pr98-anything", after_pr=97) is True
    assert context.is_downstream_or_main_validation_branch("pr97-anything", after_pr=97) is False
    assert (
        context.is_downstream_or_main_validation_branch(
            "repair/pr160-main-push-branch-context-relaxation",
            after_pr=138,
            allow_repair=False,
        )
        is True
    )


def test_pr_or_later_branch_respects_repair_opt_in():
    assert (
        context.is_pr_or_later_branch(
            "repair/pr138-main-push-ci-context",
            minimum_pr=99,
            allow_repair=True,
        )
        is True
    )
    assert (
        context.is_pr_or_later_branch(
            "repair/pr138-main-push-ci-context",
            minimum_pr=99,
            allow_repair=False,
        )
        is False
    )
    assert context.is_pr_or_later_branch("pr98-anything", minimum_pr=99) is False
    assert context.is_pr_or_later_branch("pr99-anything", minimum_pr=99) is True


def test_same_pr_repair_branch_requires_matching_pr_number():
    assert context.is_same_pr_repair_branch(
        "repair/pr160-main-push-branch-context-relaxation",
        160,
    )
    assert not context.is_same_pr_repair_branch(
        "repair/pr159-official-source-bridge",
        160,
    )
    assert not context.is_same_pr_repair_branch(
        "pr160-pr154-split-reclassification-route-closure-bridge",
        160,
    )


def test_pr_branch_ancestry_checks_exact_and_remote_refs():
    calls: list[tuple[str, ...]] = []

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        calls.append(command)
        if command == (
            "merge-base",
            "--is-ancestor",
            "origin/pr160-pr154-split-reclassification-route-closure-bridge",
            "HEAD",
        ):
            return 0, "", ""
        return 1, "", "not ancestor"

    assert context.pr_branch_ancestry_present(
        REPO_ROOT,
        "pr160-pr154-split-reclassification-route-closure-bridge",
        git_stdout=fake_git_stdout,
    )
    assert calls == [
        (
            "merge-base",
            "--is-ancestor",
            "pr160-pr154-split-reclassification-route-closure-bridge",
            "HEAD",
        ),
        (
            "merge-base",
            "--is-ancestor",
            "refs/heads/pr160-pr154-split-reclassification-route-closure-bridge",
            "HEAD",
        ),
        (
            "merge-base",
            "--is-ancestor",
            "origin/pr160-pr154-split-reclassification-route-closure-bridge",
            "HEAD",
        ),
    ]


def test_pr_branch_merged_ancestry_accepts_exact_github_merge_subject():
    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command[:2] == ("merge-base", "--is-ancestor"):
            return 1, "", "not ancestor"
        if command == (
            "log",
            "--format=%s",
            "--fixed-strings",
            "--grep=/pr160-pr154-split-reclassification-route-closure-bridge",
            "HEAD",
        ):
            return (
                0,
                "Merge pull request #172 from Q8Meow/"
                "pr160-pr154-split-reclassification-route-closure-bridge\n",
                "",
            )
        raise AssertionError(f"unexpected git command: {command!r}")

    assert context.pr_branch_merged_ancestry_present(
        REPO_ROOT,
        "pr160-pr154-split-reclassification-route-closure-bridge",
        git_stdout=fake_git_stdout,
    )
    assert not context.github_merge_commit_subject_mentions_branch(
        "Merge pull request #172 from Q8Meow/"
        "pr160-pr154-split-reclassification-route-closure-bridge-extra",
        "pr160-pr154-split-reclassification-route-closure-bridge",
    )


def test_pr_branch_merged_ancestry_refreshes_shallow_history_before_retry():
    calls: list[tuple[str, ...]] = []
    refreshed = False

    def fake_git_stdout(repo_root, args):
        nonlocal refreshed
        command = tuple(args)
        calls.append(command)
        if command[:2] == ("merge-base", "--is-ancestor"):
            return 1, "", "not ancestor"
        if command == (
            "log",
            "--format=%s",
            "--fixed-strings",
            "--grep=/pr160-pr154-split-reclassification-route-closure-bridge",
            "HEAD",
        ):
            if refreshed:
                return (
                    0,
                    "Merge pull request #172 from Q8Meow/"
                    "pr160-pr154-split-reclassification-route-closure-bridge\n",
                    "",
                )
            return 0, "", ""
        if command == ("rev-parse", "--is-shallow-repository"):
            return 0, "true", ""
        if command == ("fetch", "--no-tags", "--prune", "--unshallow", "origin"):
            refreshed = True
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    assert context.pr_branch_merged_ancestry_present_with_shallow_refresh(
        REPO_ROOT,
        "pr160-pr154-split-reclassification-route-closure-bridge",
        git_stdout=fake_git_stdout,
    )
    assert (
        "fetch",
        "--no-tags",
        "--prune",
        "--unshallow",
        "origin",
    ) in calls


def test_pr154_explicit_changed_path_allowance_is_narrow():
    branch = "pr154-atomicrows-parameter-default-value-materialization-gate"
    repair_branch = "repair/pr154-post-merge-pytest-context-hygiene"

    assert context.is_pr_or_later_branch(branch, minimum_pr=154) is True
    assert (
        context.is_downstream_or_main_validation_branch(
            repair_branch,
            after_pr=153,
            allow_repair=False,
        )
        is True
    )
    assert (
        context.is_downstream_or_main_validation_branch(
            repair_branch,
            after_pr=154,
            allow_repair=False,
        )
        is False
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/atomicrows_parameter_default_value_materialization_gate/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR154_AtomicRowsParameterDefaultValueMaterializationGate.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/atomicrows/test_atomicrows_parameter_default_value_materialization_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/tools/test_ci_branch_context.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json",
    )


def test_pr155_explicit_changed_path_allowance_is_narrow():
    branch = "pr155-agent-consumable-parameter-default-registry"

    assert context.is_pr_or_later_branch(branch, minimum_pr=155) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/agent_consumable_parameter_default_registry/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR155_AgentConsumableParameterDefaultRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_agent_consumable_parameter_default_registry.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )


def test_pr156_explicit_changed_path_allowance_is_narrow():
    branch = "pr156-agent-default-binding-universal-intake-gate"

    assert context.is_pr_or_later_branch(branch, minimum_pr=156) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/agent_default_binding_universal_intake_gate/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR156_AgentDefaultBindingUniversalIntakeGate.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_agent_default_binding_universal_intake_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/test_ci_branch_context.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )


def test_pr157_explicit_changed_path_allowance_is_narrow():
    branch = "pr157-pr154-atomicrows-fillpath-owner-agent-bridge"

    assert context.is_pr_or_later_branch(branch, minimum_pr=157) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr157_completion_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr157_atomicrows_completion_shards/PR157_AtomicRows4183CompletionMaterialization.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )


def test_pr158_explicit_changed_path_allowance_is_narrow():
    branch = "pr158-owner-response-atomicrows-selection-readiness-bridge"

    assert context.is_pr_or_later_branch(branch, minimum_pr=158) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR158_AtomicRowsSelectionReadinessOverlay.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/owner_inputs/PR157_OwnerCompletionInputResponse.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr158_owner_response_selection_readiness_bridge.py",
    )

    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/pr158_test_support.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge/test_pr158_no_execution_authority.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/pr157_completion_materialization_bridge/test_pr157_owner_response_absent_does_not_fabricate_values.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/governance/test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )


def test_pr160_explicit_changed_path_allowance_is_narrow():
    branch = "pr160-pr154-split-reclassification-route-closure-bridge"
    repair_branch = "repair/pr160-main-push-branch-context-relaxation"
    current_repair_branch = "repair/pr160-main-ancestry-after-pr176"

    assert context.is_pr_or_later_branch(branch, minimum_pr=160) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR160_PR154SplitReclassificationRouteClosure.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_split_reclassification_count_33.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr160_split_reclassification_route_closure.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_downstream_or_main_validation_branch(
        current_repair_branch,
        after_pr=138,
        allow_repair=False,
    )
    assert context.is_explicit_downstream_repair_changed_path(
        current_repair_branch,
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        current_repair_branch,
        "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure/test_pr160_branch_context_relaxation.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )


def test_pr159_explicit_changed_path_allowance_is_narrow():
    branch = "pr159-official-source-retry-atomicrows-source-completion-bridge"

    assert context.is_pr_or_later_branch(branch, minimum_pr=159) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr159_official_source_completion_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159_OfficialSourceCompletionBridge.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159_HumanReadableSourceCompletionSummary.md",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr159_official_source_completion_bridge.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/pr159_official_source_completion_bridge/test_pr159_total_source_target_count_879.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )


def test_pr159r_explicit_changed_path_allowance_is_narrow():
    branch = "pr159r-exact-source-locator-value-unit-capture"
    repair_branch = "repair/pr159r-branch-context-relaxation"

    assert context.is_pr_or_later_branch(branch, minimum_pr=159) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159R_ExactSourceLocatorValueUnitCapture.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/test_pr159r_target_universe_count_869.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr159r_source_locator_value_capture.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/report.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159_OfficialSourceCompletionBridge.report.json",
    )


def test_pull_request_detached_context_can_preserve_merge_ref_semantics(monkeypatch):
    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/feature")
    monkeypatch.setenv("GITHUB_REF_NAME", "feature")

    assert (
        context.github_actions_pull_request_detached_context_active(
            branch_returncode=0,
            branch="feature",
        )
        is False
    )
    assert (
        context.github_actions_pull_request_detached_context_active(
            branch_returncode=0,
            branch="HEAD",
        )
        is True
    )

    monkeypatch.setenv("GITHUB_REF", "refs/pull/138/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "138/merge")
    assert (
        context.github_actions_pull_request_detached_context_active(
            branch_returncode=0,
            branch="feature",
        )
        is True
    )


def test_main_push_context_requires_exact_github_main_push_env(monkeypatch):
    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

    assert context.github_actions_main_push_context_active() is True

    monkeypatch.setenv("GITHUB_REF", "main")
    assert context.github_actions_main_push_context_active() is False

    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    assert context.github_actions_main_push_context_active() is False
