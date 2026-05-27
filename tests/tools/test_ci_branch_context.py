from tools import ci_branch_context as context


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
