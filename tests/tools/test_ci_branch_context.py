from pathlib import Path

import pytest

from tools import ci_branch_context as context


REPO_ROOT = Path(__file__).resolve().parents[2]
GITHUB_BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)
ST12_BRANCH_CASES = (
    (
        "agent/st12a-contract-envelope",
        (
            "agent/st12a-contract-envelop",
            "agent/st12a-contract-envelope-copy",
            "agent/st12a-contract-envelope/",
            "Agent/st12a-contract-envelope",
        ),
    ),
    (
        "agent/st12b-contextual-computability-v3",
        (
            "agent/st12b-contextual-computability",
            "agent/st12b-contextual-computability-v3-copy",
            "agent/st12b-contextual-computability-v3/",
            "Agent/st12b-contextual-computability-v3",
        ),
    ),
    (
        "agent/st12c-deterministic-receipts-accounting-v1",
        (
            "agent/st12c-deterministic-receipts-accounting",
            "agent/st12c-deterministic-receipts-accounting-v1-copy",
            "agent/st12c-deterministic-receipts-accounting-v1/",
            "Agent/st12c-deterministic-receipts-accounting-v1",
        ),
    ),
    (
        "agent/st12e-capability-guard",
        (
            "agent/st12e-capability",
            "agent/st12e-capability-guard-copy",
            "agent/st12e-capability-guard/",
            "Agent/st12e-capability-guard",
        ),
    ),
    (
        "agent/st12d-mode-snapshot-boundary",
        (
            "agent/st12d-mode-snapshot",
            "agent/st12d-mode-snapshot-boundary-copy",
            "agent/st12d-mode-snapshot-boundary/",
            "Agent/st12d-mode-snapshot-boundary",
        ),
    ),
    (
        "agent/st12f-evidence-model-risk-v1",
        (
            "agent/st12f-evidence-model-risk",
            "agent/st12f-evidence-model-risk-v1-copy",
            "agent/st12f-evidence-model-risk-v1/",
            "Agent/st12f-evidence-model-risk-v1",
        ),
    ),
    (
        "agent/st12h-validation-currentization-operations-publication",
        (
            "agent/st12h-validation-currentization-operations",
            "agent/st12h-validation-currentization-operations-publication-copy",
            "agent/st12h-validation-currentization-operations-publication/",
            "Agent/st12h-validation-currentization-operations-publication",
            "agent/*st12h-validation-currentization-operations-publication",
        ),
    ),
    (
        context.F12_EXACT_TIME_COMPOSITION_BRANCH,
        (
            context.F12_EXACT_TIME_COMPOSITION_BRANCH.upper(),
            "prefix-" + context.F12_EXACT_TIME_COMPOSITION_BRANCH,
            context.F12_EXACT_TIME_COMPOSITION_BRANCH + "-suffix",
            context.F12_EXACT_TIME_COMPOSITION_BRANCH + "/",
            "f12-exact-time-*",
        ),
    ),
)


F13_BRANCH_CASE = (
    context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH,
    (
        context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH.upper(),
        "prefix-" + context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH,
        context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH + "-suffix",
        context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH + "/",
        "f13-private-clock-*",
    ),
)


def _clear_github_branch_context_env(monkeypatch):
    for env_name in GITHUB_BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def test_repair_and_main_cumulative_branch_classification():
    _assert_f14_exact_scope_and_interfaces()
    repair_branch = context.NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_BRANCH

    assert context.is_repair_branch("repair/pr138-main-push-ci-context") is True
    assert context.is_repair_branch(repair_branch) is True
    assert context.is_validation_infrastructure_branch(repair_branch) is True
    assert context.is_owner_authorized_validation_branch(repair_branch) is False
    assert context.is_main_cumulative_branch(repair_branch) is True
    assert context.is_main_cumulative_branch("main") is True
    assert context.is_main_cumulative_branch("repair/main-cumulative-example") is True
    assert (
        context.is_main_cumulative_branch(
            "pr-ci-fastfail-validation-context-preflight"
        )
        is True
    )
    assert (
        context.is_main_cumulative_branch(
            context.CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH
        )
        is True
    )
    assert (
        context.is_main_cumulative_branch(
            context.PR208_CI_RUNTIME_RATIONALIZATION_BRANCH
        )
        is True
    )
    assert context.is_main_cumulative_branch("feature/unrelated") is False
    assert context.is_downstream_roadmap_branch(
        "feature/non-downstream-validation",
        after_pr=97,
    ) is False
    assert context.is_repair_branch("feature/non-downstream-validation") is False


def test_st12_architecture_oracle_prerequisite_repair_branch_is_exactly_classified():
    branch = context.ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH

    assert context.is_repair_branch(branch) is True
    assert context.is_owner_authorized_validation_branch(branch) is True
    assert context.is_validation_infrastructure_branch(branch) is False
    assert context.is_validation_execution_branch(branch) is False
    assert context.is_main_cumulative_branch(branch) is False
    assert context.roadmap_pr_number(branch) is None
    assert branch not in context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS

    for adversarial in (
        f"{branch}-copy",
        f"{branch}/",
        branch.upper(),
        branch.replace("oracle-closure", "oracles-closure"),
        "repair/st12-architecture-independent-oracle-unrelated",
    ):
        assert adversarial != branch
        assert not context.is_owner_authorized_validation_branch(adversarial)


def test_st12_inherited_math_receipt_repair_branch_is_exactly_classified():
    branch = context.ST12_INHERITED_MATH_ROW_RECEIPT_REPAIR_BRANCH

    assert context.is_repair_branch(branch) is True
    assert context.is_owner_authorized_validation_branch(branch) is True
    assert context.is_validation_infrastructure_branch(branch) is False
    assert context.is_validation_execution_branch(branch) is False
    assert context.is_main_cumulative_branch(branch) is False
    assert context.roadmap_pr_number(branch) is None
    assert branch not in context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS

    for adversarial in (
        f"{branch}-copy",
        f"{branch}/",
        branch.upper(),
        branch.replace("receipt-closure", "receipts-closure"),
        "repair/st12-inherited-math-row-receipt-*",
    ):
        assert adversarial != branch
        assert not context.is_owner_authorized_validation_branch(adversarial)


@pytest.mark.parametrize(
    ("branch", "adversarial_branches"),
    ST12_BRANCH_CASES,
    ids=("st12a", "st12b", "st12c", "st12e", "st12d", "st12f", "st12h", "f12"),
)
def test_st12_owner_authorized_branches_are_exactly_validation_only(
    branch: str,
    adversarial_branches: tuple[str, ...],
):
    def assert_selected_branch(branch, adversarial_branches):
        assert context.is_owner_authorized_validation_branch(branch)
        assert context.roadmap_pr_number(branch) is None
        for gate in ("PR159R", "PR160"):
            assert context.is_branch_allowed_for_upstream_pr_gate(branch, gate)
        for threshold in (94, 95, 96, 138):
            assert context.is_downstream_or_main_validation_branch(
                branch, after_pr=threshold, allow_repair=False,
            )
        assert not context.is_main_cumulative_branch(branch)
        assert not context.is_repair_branch(branch)
        assert not context.is_validation_infrastructure_branch(branch)
        assert not context.is_validation_execution_branch(branch)
        assert branch not in context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_PR_NUMBERS
        assert not context.is_downstream_roadmap_branch(
            branch, after_pr=1, allow_repair=False,
        )
        for minimum in (1, 99):
            assert context.is_pr_or_later_branch(
                branch, minimum_pr=minimum, allow_main=False, allow_repair=False,
            )
        for prefix in ("refs/heads/", "refs/remotes/origin/", "origin/"):
            assert context.normalize_branch_context(prefix + branch) == branch
            assert context.is_owner_authorized_validation_branch(prefix + branch)
        for adversarial in (*adversarial_branches, "agent/other"):
            assert not context.is_owner_authorized_validation_branch(adversarial)
            for gate in ("PR159R", "PR160"):
                assert not context.is_branch_allowed_for_upstream_pr_gate(adversarial, gate)
            for threshold in (94, 95, 96):
                assert not context.is_downstream_or_main_validation_branch(
                    adversarial, after_pr=threshold, allow_repair=False,
                )
            assert not context.is_pr_or_later_branch(
                adversarial, minimum_pr=99, allow_main=False, allow_repair=False,
            )

        if branch in {context.F12_EXACT_TIME_COMPOSITION_BRANCH, context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH}:
            from tools import run_validation_gates as runner

            builder = "build_pr168_rp5c_immutable_qku_formula_library.py"
            assert runner.OWNER_VALIDATION_READ_ONLY_UPSTREAM_BUILDER_SCRIPT_NAMES == (
                frozenset({builder})
            )
            commands = [
                ["python", "tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
                ["python", f"tools/{builder}", "--repo-root", "."],
                ["python", "-B", "-m", "pytest", "tests/pr168_rp5c", "-q"],
                ["python", "tools/independent_validate_qku_computation_control_plane_d.py"],
                ["python", "tools/build_other.py", "--output", "synthetic-output"],
                ["python", "tools/build_pr168_rp5c_immutable_qku_formula_library.py.copy"],
            ]
            original = [command.copy() for command in commands]
            expected = [command.copy() for index, command in enumerate(commands) if index != 1]
            filtered = runner._filter_foreign_branch_guarded_builders_for_owner_validation(
                commands, branch=branch,
            )
            assert filtered == expected
            assert commands == original
            for unknown in ("unregistered-validation-context", *adversarial_branches):
                retained = runner._filter_foreign_branch_guarded_builders_for_owner_validation(
                    commands, branch=unknown,
                )
                assert retained == original
                assert commands == original

        if branch == context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH:
            from tools import validation_scope_registry as registry
            from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import report as pr152

            expected_paths = frozenset({
                'src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py',
                'src/qtt/stage1_prediction_markets/qku_computation_control_plane/persistence.py',
                'src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py',
                'src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py',
                'src/qtt/stage1_prediction_markets/qku_computation_control_plane/sqlite_reference.py',
                'src/qtt/stage1_prediction_markets/qku_computation_control_plane/transaction.py',
                'tests/source_evidence/test_s1_pit_data_phase_a_01.py',
                'tests/stage1_prediction_markets/qku_computation_control_plane/accounting/test_contract_matrix.py',
                'tests/stage1_prediction_markets/qku_computation_control_plane/security/test_deserialization_safety.py',
                'tests/tools/test_ci_branch_context.py',
                'tools/ci_branch_context.py',
                'tools/independent_validate_qku_computation_control_plane_execution.py',
                'tools/validation_scope_registry.py',
            })
            assert type(registry.F13_ALLOWED_EXACT_PATHS) is frozenset
            assert registry.F13_ALLOWED_EXACT_PATHS == expected_paths
            assert len(expected_paths) == 13
            assert context.roadmap_pr_number(branch) is None
            for prefix in ("", "refs/heads/", "refs/remotes/origin/", "origin/"):
                supplied_branch = prefix + branch
                for path in sorted(expected_paths):
                    for supplied_path in (path, "./" + path, path.replace("/", "\\")):
                        decision = registry.explain_pr_scope_decision(
                            supplied_branch, supplied_path,
                        )
                        assert decision == {
                            "allowed": True,
                            "branch": branch,
                            "normalized_path": path,
                            "pr_id": "F13",
                            "matched_rule": "exact:" + path,
                            "reason": "registered_exact_path",
                        }
                        assert registry.is_pr_scoped_changed_path_allowed(
                            supplied_branch, supplied_path,
                        )
                        assert context.is_explicit_downstream_repair_changed_path(
                            supplied_branch, supplied_path,
                        )
                        assert pr152._is_allowed_pr152_changed_path_for_branch(
                            supplied_path, supplied_branch,
                        )
                for path in expected_paths:
                    for unapproved_path in (
                        path + ".near", "prefix/" + path, "../" + path,
                        "/" + path, "C:/" + path, path.upper(),
                    ):
                        assert not registry.is_pr_scoped_changed_path_allowed(
                            supplied_branch, unapproved_path,
                        )
            for adversarial in (*adversarial_branches, "feature/unrelated", "HEAD"):
                for path in expected_paths:
                    assert not registry.is_pr_scoped_changed_path_allowed(adversarial, path)
                    assert not context.is_explicit_downstream_repair_changed_path(adversarial, path)
                    assert not pr152._is_allowed_pr152_changed_path_for_branch(path, adversarial)

            denied_paths = (
                "src/qtt/stage1_prediction_markets/qku_computation_control_plane/unapproved.py",
                "tools/validation_reliability.py",
                "tools/changed_area_validation_router.py",
                pr152.c.MASTER_PLAN_PATH.as_posix(),
                pr152.c.ATOMICROWS_BUNDLE_PATH.as_posix(),
                pr152._forbidden_bundle_sidecar_path(),
            )
            for path in denied_paths:
                assert not registry.is_pr_scoped_changed_path_allowed(branch, path)
                assert not pr152._is_allowed_pr152_changed_path_for_branch(path, branch)
            # Existing legacy shared-path compatibility is not new F13 edit authority.
            assert not registry.is_pr_scoped_changed_path_allowed(
                branch, ".github/workflows/qtt_validation.yml",
            )
            original_changed_paths = pr152._changed_paths
            original_branch_context = pr152.current_branch_context
            with pytest.MonkeyPatch.context() as scope_patch:
                scope_patch.setattr(
                    pr152, "current_branch_context",
                    lambda _root: context.BranchContext(branch=branch, source="synthetic-test"),
                )
                scope_patch.setattr(pr152, "_changed_paths", lambda _root: sorted(expected_paths))
                assert pr152._validate_changed_paths(REPO_ROOT) == []
                for rejected_path in denied_paths:
                    scope_patch.setattr(
                        pr152, "_changed_paths",
                        lambda _root, rejected_path=rejected_path: sorted(expected_paths | {rejected_path}),
                    )
                    failures = pr152._validate_changed_paths(REPO_ROOT)
                    assert "PR152_CHANGED_PATH_OUT_OF_SCOPE: " + rejected_path in failures
                scope_patch.setattr(pr152, "_changed_paths", lambda _root: ["<git-status-unavailable>"])
                assert pr152._validate_changed_paths(REPO_ROOT) == ["PR152_GIT_STATUS_UNAVAILABLE"]
            assert pr152._changed_paths is original_changed_paths
            assert pr152.current_branch_context is original_branch_context

            import ast
            from contextlib import redirect_stderr, redirect_stdout
            from copy import deepcopy
            from io import StringIO

            from tools import independent_validate_qku_computation_control_plane_execution as execution_validator

            original_tree_loader = execution_validator._tree
            persistence_tree = original_tree_loader("persistence.py")
            original_tree_dump = ast.dump(persistence_tree, include_attributes=True)
            adapter = next(
                node for node in persistence_tree.body
                if isinstance(node, ast.ClassDef) and node.name == "PersistenceAdapterV1"
            )
            original_methods = {
                node.name for node in adapter.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not node.name.startswith("_")
            }
            get_record_node = next(
                node for node in adapter.body
                if isinstance(node, ast.FunctionDef) and node.name == "get_record"
            )
            for removed_method, added_method, expected_difference in (
                ("load_committed_private_clock_receipt_v1", None,
                 {"load_committed_private_clock_receipt_v1"}),
                ("get_record", None, {"get_record"}),
                (None, "unexpected_public_method", {"unexpected_public_method"}),
                ("get_record", "unexpected_public_method",
                 {"get_record", "unexpected_public_method"}),
            ):
                mutated_tree = deepcopy(persistence_tree)
                mutated_adapter = next(
                    node for node in mutated_tree.body
                    if isinstance(node, ast.ClassDef) and node.name == "PersistenceAdapterV1"
                )
                if removed_method is not None:
                    mutated_adapter.body = [
                        node for node in mutated_adapter.body
                        if not (
                            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and node.name == removed_method
                        )
                    ]
                if added_method is not None:
                    unexpected_method = deepcopy(get_record_node)
                    unexpected_method.name = added_method
                    mutated_adapter.body.append(unexpected_method)
                mutated_methods = {
                    node.name for node in mutated_adapter.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not node.name.startswith("_")
                }
                assert original_methods ^ mutated_methods == expected_difference
                if removed_method is not None and added_method is not None:
                    assert len(mutated_methods) == len(original_methods)

                def mutated_tree_loader(name, mutation=mutated_tree):
                    if name == "persistence.py":
                        return deepcopy(mutation)
                    return original_tree_loader(name)

                with StringIO() as stdout, StringIO() as stderr:
                    with pytest.MonkeyPatch.context() as tree_patch:
                        tree_patch.setattr(execution_validator, "_tree", mutated_tree_loader)
                        with redirect_stdout(stdout), redirect_stderr(stderr):
                            result = execution_validator.main()
                    assert execution_validator._tree is original_tree_loader
                    assert result == 1
                    assert stderr.getvalue() == (
                        f"typed persistence interface mismatch: {sorted(expected_difference)}\n"
                    )
                    assert execution_validator.SUCCESS not in stdout.getvalue()
                    assert execution_validator.SUCCESS not in stderr.getvalue()
                assert ast.dump(persistence_tree, include_attributes=True) == original_tree_dump

    assert_selected_branch(branch, adversarial_branches)
    if branch == context.F12_EXACT_TIME_COMPOSITION_BRANCH:
        assert_selected_branch(*F13_BRANCH_CASE)


def test_st12_pull_request_detached_context_uses_exact_github_head_ref(
    monkeypatch,
):
    _clear_github_branch_context_env(monkeypatch)
    for name in context.BRANCH_CONTEXT_ENV_CANDIDATES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/276/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "276/merge")
    for branch, adversarial_branches in (*ST12_BRANCH_CASES, F13_BRANCH_CASE):
        for prefix in ("", "refs/heads/", "refs/remotes/origin/", "origin/"):
            monkeypatch.setenv("GITHUB_HEAD_REF", prefix + branch)
            resolved = context.current_branch_context(
                REPO_ROOT,
                git_stdout=lambda *_args: (0, "HEAD", ""),
            )
            assert resolved.branch == branch
            assert resolved.source == "GITHUB_HEAD_REF"
            if branch == context.F13_PRIVATE_CLOCK_STORAGE_REPLAY_BRANCH:
                from tools import validation_scope_registry as registry
                from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import report as pr152

                with monkeypatch.context() as scope_patch:
                    scope_patch.setattr(pr152, "current_branch_context", lambda _root: resolved)
                    scope_patch.setattr(
                        pr152, "_changed_paths",
                        lambda _root: sorted(registry.F13_ALLOWED_EXACT_PATHS),
                    )
                    assert pr152._validate_changed_paths(REPO_ROOT) == []
            assert context.github_actions_pull_request_detached_context_active(
                branch_returncode=0, branch="HEAD",
            )
            for gate in ("PR159R", "PR160"):
                assert (
                    context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
                        context.github_actions_head_ref_branch_context(), gate,
                    )
                )
        for adversarial in adversarial_branches:
            monkeypatch.setenv("GITHUB_HEAD_REF", adversarial)
            resolved = context.current_branch_context(
                REPO_ROOT, git_stdout=lambda *_args: (0, "HEAD", ""),
            )
            assert not context.is_owner_authorized_validation_branch(resolved.branch)
            for gate in ("PR159R", "PR160"):
                assert not (
                    context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
                        context.github_actions_head_ref_branch_context(), gate,
                    )
                )
    monkeypatch.setenv(
        "GITHUB_HEAD_REF",
        "agent/st12c-deterministic-receipts-accounting-v1-suffix",
    )
    assert not (
        context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
            context.github_actions_head_ref_branch_context(), "PR160",
        )
    )
    monkeypatch.delenv("GITHUB_HEAD_REF")
    resolved = context.current_branch_context(
        REPO_ROOT, git_stdout=lambda *_args: (0, "HEAD", ""),
    )
    assert resolved.branch == ""
    assert resolved.source == ""
    assert context.github_actions_branch_context() == ""
    assert not context.is_owner_authorized_validation_branch(resolved.branch)
    for gate in ("PR159R", "PR160"):
        assert not context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
            context.github_actions_head_ref_branch_context(), gate,
        )


def test_roadmap_pr_number_parses_pr_branches():
    assert context.roadmap_pr_number("pr97-atomicrows-full-bundle-row-expansion-plan") == 97
    assert (
        context.roadmap_pr_number(
            "pr99-atomicrows-bundle-builder-deterministic-assembly-gate"
        )
        == 99
    )
    assert context.roadmap_pr_number(context.PR208_CI_RUNTIME_RATIONALIZATION_BRANCH) is None
    assert (
        context.roadmap_pr_number(
            f"{context.PR208_CI_RUNTIME_RATIONALIZATION_BRANCH}-copy"
        )
        is None
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


def test_pr161e_explicit_changed_path_allowance_is_narrow():
    branch = "pr161e-replay-paper-outcome-capture-scenario-learning-bridge"

    assert context.is_pr_or_later_branch(branch, minimum_pr=161) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161E_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr161e_replay_paper_outcome_capture_shards/PR161E_AgentOutcomeTaskQueue.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr161e_replay_paper_outcome_capture_scenario_learning.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


def test_pr161f_explicit_changed_path_allowance_is_narrow():
    branch = "pr161f-replay-paper-executor-input-run-artifact-generation"

    assert context.is_pr_or_later_branch(branch, minimum_pr=161) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161F_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr161f_replay_paper_executor_input_run_artifact_generation_shards/PR161F_AgentRunTaskQueue.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr161f_replay_paper_executor_input_run_artifact_generation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


def test_pr162_explicit_changed_path_allowance_is_narrow():
    branch = "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "nonlive_replay_paper_data_adapter_quantum_forward_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "pr162_safe_nonlive_replay_paper_quantum_forward_shards/"
        "PR162_QKUArtifactCoverageBridge.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


def test_pr162a_explicit_changed_path_allowance_is_narrow():
    branch = "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "safe_repo_local_nonlive_dataset_materialization_authority_gate/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162A_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "pr162a_safe_repo_local_nonlive_dataset_shards/"
        "PR162A_MarketScenarioQKUMappingMatrix.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "data/stage1_prediction_markets/nonlive_datasets/pr162a/"
        "normalized_candidates/kalshi_historical_market_trades_candlesticks_tiny_candidate.normalized.jsonl",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/currentize_pr152_after_generated_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
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
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/unrelated.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


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


def test_pr159s_explicit_changed_path_allowance_is_narrow():
    branch = "pr159s-open-source-intelligence-candidate-completion"
    repair_branch = "repair/pr159s-open-intake-branch-context-relaxation"

    assert context.is_pr_or_later_branch(branch, minimum_pr=159) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/source_intelligence/schemas/pr159s_source_taxonomy.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159S_TerminalCompletionSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/source_intelligence/test_pr159s_terminal_completion_counts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr159s_open_intake_completion.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake/report_builder.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159R_ExactSourceLocatorValueUnitCapture.report.json",
    )


def test_pr161b_explicit_changed_path_allowance_is_narrow():
    branch = "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"

    assert context.is_pr_or_later_branch(branch, minimum_pr=161) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161B_ResidualCoverageFinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr161b_master_plan_residual_candidate_coverage.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
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
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161A_FinalValueStateSummary.report.json",
    )


def test_pr161c_explicit_changed_path_allowance_is_narrow():
    branch = "pr161c-qku-residual-candidate-assimilation-fill-campaign"

    assert context.is_pr_or_later_branch(branch, minimum_pr=161) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/qku_residual_candidate_assimilation/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161C_QKUFinalAssimilationSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr161c_qku_report_shards/PR161C_QKU9360PrimaryMaterializationRegistry.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr161c_qku_residual_candidate_assimilation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161A_FinalValueStateSummary.report.json",
    )


def test_pr161d_explicit_changed_path_allowance_is_narrow():
    branch = "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization"

    assert context.is_pr_or_later_branch(branch, minimum_pr=161) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "qku_candidate_quality_replay_paper_prioritization/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "qku_candidate_quality_replay_paper_prioritization/"
        "test_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161D_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161D_QKUMarketBundleActivationPolicy.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161D_QKUAgentRoleBundleSlice.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr161d_qku_candidate_quality_shards/"
        "PR161D_QKUCategoryRankingRegistry.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR161C_QKUFinalAssimilationSummary.report.json",
    )


def test_pr162c_explicit_changed_path_allowance_is_narrow():
    branch = "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "multisource_safe_nonlive_dataset_expansion_strict_qku_coverage/"
        "test_pr162c_preflight_consumes_required_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162C_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR162C_EXECUTABLE_QKU_AND_DATASET_PREFLIGHT_RECEIPT.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr162c_multisource_safe_nonlive_dataset_shards/"
        "PR162C_StrictQKUCoverageProofMatrix.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


def test_pr162d_explicit_changed_path_allowance_is_narrow():
    branch = "pr162d-aggressive-qku-candidate-materialization-agent-routing"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "aggressive_qku_candidate_materialization_agent_routing/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "aggressive_qku_candidate_materialization_agent_routing/"
        "test_pr162d_no_acquisition_gate_regression.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "pr162d_aggressive_qku_candidate_materialization_agent_routing_shards/"
        "PR162D_QKUFieldFillExpansionMatrix.report.shard_0001.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162B_FinalSummary.report.json",
    )


def test_pr162d_r1_explicit_changed_path_allowance_is_narrow():
    branch = "pr162d-r1-external-formula-data-quantum-acquisition-expansion"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162d_r1_external_formula_data_quantum_acquisition_expansion/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162d_r1_external_formula_data_quantum_acquisition_expansion/"
        "schemas/PR162D_R1_FinalSummary.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr162d_r1_external_formula_data_quantum_acquisition_expansion/"
        "test_pr162d_r1_requires_external_acquisition.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_R1_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162d_r1_external_formula_data_quantum_acquisition_expansion.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162d_r1_external_formula_data_quantum_acquisition_expansion.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/test_ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/source_intelligence/"
        "test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_FinalSummary.report.json",
    )


def test_pr162r_a_explicit_changed_path_allowance_is_narrow():
    branch = "pr162r-a-replay-paper-executability-classification-audit"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162r_a_replay_paper_executability_classification_audit/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162r_a_replay_paper_executability_classification_audit/"
        "schemas/pr162r_a_finalsummary.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr162r_a_replay_paper_executability_classification_audit/"
        "test_pr162r_a_classifies_all_routed_candidates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_A_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162r_a_replay_paper_executability_classification_audit.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162r_a_replay_paper_executability_classification_audit.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/test_ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_R1_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "aggressive_qku_candidate_materialization_agent_routing/validator.py",
    )


def test_pr162d_r2a_explicit_changed_path_allowance_is_narrow():
    branch = "pr162d-r2a-real-computable-formulations-redo"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162d_r2a_real_formulations/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162d_r2a_real_formulations/schemas/FormulationRecordV1.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr162d_r2a_real_formulations/test_validation_wiring.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_R2A_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_R2A_HumanReviewTopFormulations.report.md",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162d_r2a_real_formulations.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162d_r2a_real_formulations.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_A_FinalSummary.report.json",
    )


def test_pr162r_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr162r-generic-replay-paper-adapter-rerun"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162r_generic_replay_paper_adapter_rerun/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162r_generic_replay_paper_adapter_rerun/schemas/ReplayPaperAdapterInputV1.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr162r_generic_replay_paper_adapter_rerun/test_validation_wiring.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_Old548CompatibilityTrace.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162r_generic_replay_paper_adapter_rerun.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162r_generic_replay_paper_adapter_rerun.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "source_intelligence/test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "source_intelligence/test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "atomicrows_pr154_value_state/test_pr161a_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/test_pr161b_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_A_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162D_R2A_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/constants.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/999/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr162r_b_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr162r-b-replay-paper-data-binding-completion"

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162r_b_replay_paper_data_binding_completion/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162r_b_replay_paper_data_binding_completion/schemas/BindingTaskV1.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr162r_b_replay_paper_data_binding_completion/test_validation_wiring.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fixtures/stage1_prediction_markets/"
        "pr162r_b_replay_paper_data_binding_completion/"
        "synthetic_paper_market_state.fixture.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_B_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162r_b_replay_paper_data_binding_completion.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162r_b_replay_paper_data_binding_completion.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/999/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr163_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr163-generic-paper-adapter-capture-framework"

    assert context.is_pr_or_later_branch(branch, minimum_pr=163) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_generic_paper_adapter_capture_framework/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_generic_paper_adapter_capture_framework/schemas/"
        "PaperAdapterInputV1.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr163_generic_paper_adapter_capture_framework/test_validation_wiring.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR163_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr163_generic_paper_adapter_capture_framework.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr163_generic_paper_adapter_capture_framework.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_B_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/999/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr163_b_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr163-b-paired-replay-paper-concurrent-executor"

    assert context.is_pr_or_later_branch(branch, minimum_pr=163) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_b_paired_replay_paper_concurrent_executor/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_b_paired_replay_paper_concurrent_executor/schemas/"
        "PairedReplayPaperRunInputV1.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr163_b_paired_replay_paper_concurrent_executor/test_validation_wiring.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR163_B_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr163_b_shards/"
        "PR163_B_ReplayLaneExecutionTraceRegistry.part_0001_of_0003.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr163_b_paired_replay_paper_concurrent_executor.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr163_b_paired_replay_paper_concurrent_executor.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR163_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/999/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr164_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr164-review-provenance-qku-canonical-coverage-audit"

    assert context.is_pr_or_later_branch(branch, minimum_pr=164) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr164_review_provenance_qku_canonical_coverage_audit/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr164_review_provenance_qku_canonical_coverage_audit/schemas/"
        "pr164_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr164_review_provenance_qku_canonical_coverage_audit/test_pr164_report_sharding_limits.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR164_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr164_shards/"
        "PR164_QKUComputabilityMaterializationRegistry.part_0001_of_0005.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr164_review_provenance_qku_canonical_coverage_audit.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr164_review_provenance_qku_canonical_coverage_audit.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
        "pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


def test_pr165_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr165-evidence-backed-scoring-ranking"

    assert context.is_pr_or_later_branch(branch, minimum_pr=165) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_evidence_backed_scoring_ranking/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_evidence_backed_scoring_ranking/schemas/"
        "pr165_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr165_evidence_backed_scoring_ranking/test_pr165_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr165_shards/"
        "PR165_GlobalCandidateRanking.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr165_evidence_backed_scoring_ranking.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr165_evidence_backed_scoring_ranking.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR164_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr164_review_provenance_qku_canonical_coverage_audit/validators.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1001/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr165_b_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr165-b-condition-scoped-negative-memory"

    assert context.is_pr_or_later_branch(branch, minimum_pr=165) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_b_condition_scoped_negative_memory/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_b_condition_scoped_negative_memory/schemas/"
        "pr165_b_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr165_b_condition_scoped_negative_memory/test_pr165_b_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_B_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr165_b_shards/"
        "PR165_B_CandidateVersionMemoryRegistry.part_0001_of_0007.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr165_b_condition_scoped_negative_memory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr165_b_condition_scoped_negative_memory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_evidence_backed_scoring_ranking/validators.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1002/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr165_c_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr165-c-replay-paper-memory-consumer-integration"

    assert context.is_pr_or_later_branch(branch, minimum_pr=165) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_c_replay_paper_memory_consumer_integration/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_c_replay_paper_memory_consumer_integration/schemas/"
        "pr165_c_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr165_c_replay_paper_memory_consumer_integration/test_pr165_c_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_C_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr165_c_shards/"
        "PR165_C_MemoryConsumerRouter.part_0001_of_0007.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr165_c_replay_paper_memory_consumer_integration.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr165_c_replay_paper_memory_consumer_integration.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_B_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_b_condition_scoped_negative_memory/validators.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1003/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr165_d_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr165-d-scenario-qku-combination-selection"

    assert context.is_pr_or_later_branch(branch, minimum_pr=165) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d_scenario_qku_combination_selection/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d_scenario_qku_combination_selection/schemas/"
        "pr165_d_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr165_d_scenario_qku_combination_selection/test_pr165_d_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_D_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr165_d_shards/"
        "PR165_D_RetestBatchSelectionQueue.part_0001_of_0007.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr165_d_scenario_qku_combination_selection.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr165_d_scenario_qku_combination_selection.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_C_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_c_replay_paper_memory_consumer_integration/validators.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1004/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_s_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-s-replay-paper-scenario-retest-execution"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s_replay_paper_scenario_retest_execution/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s_replay_paper_scenario_retest_execution/schemas/"
        "pr166_s_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_s_replay_paper_scenario_retest_execution/test_pr166_s_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_S_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_s_shards/"
        "PR166_S_OrderIntentRegistry.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_s_replay_paper_scenario_retest_execution.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_D_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d_scenario_qku_combination_selection/validators.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1005/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_sm_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-sm-score-memory-refresh-from-pr166-s-results"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/schemas/"
        "pr166_sm_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/test_pr166_sm_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_sm_shards/"
        "PR166_SM_RefreshedScoreRegistry.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_S_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s_replay_paper_scenario_retest_execution/validators.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1006/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_sf_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-sf-repair-materialization-before-retest"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/schemas/"
        "pr166_sf_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/"
        "test_pr166_sf_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SF_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_sf_shards/"
        "PR166_SF_TargetUniverseRegistry.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_sf_repair_materialization_before_retest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_sf_repair_materialization_before_retest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/changed_area_validation_router.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/"
        "test_pr165_d2_optional_pr166_sf_handling.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1007/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_s2_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-s2-replay-paper-retest-loop-v2"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/schemas/"
        "pr166_s2_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/"
        "test_pr166_s2_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_S2_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_s2_shards/"
        "PR166_S2_RetestUniverse.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_s2_replay_paper_retest_loop_v2.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_s2_replay_paper_retest_loop_v2.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/changed_area_validation_router.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SF_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1008/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_sm2_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-sm2-score-memory-refresh-v2"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/schemas/"
        "pr166_sm2_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/"
        "test_pr166_sm2_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM2_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_sm2_shards/"
        "PR166_SM2_ScoreRegistry.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_sm2_score_memory_refresh_v2.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_sm2_score_memory_refresh_v2.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/changed_area_validation_router.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_fail_closed_guards.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_S2_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1009/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_sf_r2_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-sf-r2-targeted-conversion-repair-retest"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/schemas/"
        "pr166_sf_r2_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/"
        "test_pr166_sf_r2_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SF_R2_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_sf_r2_shards/"
        "PR166_SF_R2_NetEdgeLedger.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_sf_r2_targeted_conversion_repair_retest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_sf_r2_targeted_conversion_repair_retest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/changed_area_validation_router.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM2_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1010/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_sm3_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr166-sm3-score-memory-refresh-v3"

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/schemas/"
        "pr166_sm3_score_registry.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/"
        "test_pr166_sm3_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM3_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_sm3_shards/"
        "PR166_SM3_ScoreRegistry.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_sm3_score_memory_refresh_v3.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_sm3_score_memory_refresh_v3.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/changed_area_validation_router.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SF_R2_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1011/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_q_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = context.PR166_Q_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_q_quantum_classical_hybrid_comparator/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_q_quantum_classical_hybrid_comparator/schemas/"
        "pr166_q_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_q_quantum_classical_hybrid_comparator/test_pr166_q_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_q_shards/"
        "PR166_Q_QuantumClassicalHybridRaceLedger.part_0001_of_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_q_quantum_classical_hybrid_comparator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_q_quantum_classical_hybrid_comparator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_idempotence_runtime_containment.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM3_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/166/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_qb_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = context.PR166_QB_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_qb_bounded_quantum_benchmark/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_qb_bounded_quantum_benchmark/schemas/"
        "pr166_qb_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_qb_bounded_quantum_benchmark/test_pr166_qb_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_QB_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_qb_shards/"
        "PR166_QB_RaceArb.part_0001_of_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_qb_bounded_quantum_benchmark.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_qb_bounded_quantum_benchmark.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_idempotence_runtime_containment.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/223/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr166_qc_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = context.PR166_QC_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=166) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_qc_quantum_selected_replay_paper_retest/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_qc_quantum_selected_replay_paper_retest/schemas/"
        "pr166_qc_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_QC_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr166_qc_shards/"
        "PR166_QC_ReplayEvidence.part_0001_of_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr166_qc_quantum_selected_replay_paper_retest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_idempotence_runtime_containment.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )


def test_pr162e_q_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = context.PR162E_Q_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162e_q_quantum_automapper/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr162e_q_quantum_automapper/schemas/"
        "pr162e_q_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr162e_q_quantum_automapper/test_pr162e_q_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162E_Q_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr162e_q_shards/"
        "PR162E_Q_MapEligibility.part_0001_of_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162e_q_quantum_automapper.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162e_q_quantum_automapper.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_idempotence_runtime_containment.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_qc_quantum_selected_replay_paper_retest/validator.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_QB_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/224/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr162e_plugin_framework_changed_path_allowance_is_narrow(monkeypatch):
    branch = context.PR162E_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr162e_plugin_framework/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr162e_plugin_framework/schemas/plugin_contract.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/plugins/contracts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/pr162e/test_pr162e_plugin_abi.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162E_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr162e_plugin_framework.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr162e_plugin_framework.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr167_open_trade_simulator_integration/io.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/connectors/live_connector.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR167_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/227/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr167_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = context.PR167_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=167) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr167_open_trade_simulator_integration/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr167_open_trade_simulator_integration/schemas/"
        "pr167_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr167_open_trade_simulator_integration/test_pr167_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR167_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr167_shards/"
        "PR167_SimEligibility.part_0001_of_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr167_open_trade_simulator_integration.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr167_open_trade_simulator_integration.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_idempotence_runtime_containment.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_field_coverage_enrichment_plan/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_qc_quantum_selected_replay_paper_retest/validator.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_QC_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/167/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr165_d2_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr165-d2-score-refreshed-scenario-selection-v2"
    repair_branch = context.PR165_D2_MAIN_PUSH_BRANCH_CONTEXT_REPAIR_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=165) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/schemas/"
        "pr165_d2_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/test_pr165_d2_validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_D2_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr165_d2_shards/"
        "PR165_D2_NetEdgeAdjustedCandidateRanking.part_0001_of_0004.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/changed_area_validation_router.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/test_validation_inventory.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/tools/test_changed_area_validation_router.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr166_sm_score_memory_refresh_from_pr166_s_results/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/test_pr165_d2_idempotence.py",
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
        "docs/master_plan/generated/PR165_D2_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/schemas/"
        "pr165_d2_report_manifest.schema.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/test_pr165_d2_validator.py",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", f"refs/heads/{branch}")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


def test_pr163_c_explicit_changed_path_allowance_is_narrow(monkeypatch):
    branch = "pr163-c-pretrade-infrastructure-rejection-remediation"
    repair_branch = context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH

    assert context.is_pr_or_later_branch(branch, minimum_pr=163) is True
    assert (
        context.is_explicit_downstream_repair_branch_context_allowed(
            repair_branch,
            upstream_pr=159,
        )
        is True
    )
    assert (
        context.is_explicit_downstream_repair_branch_context_allowed(
            repair_branch,
            upstream_pr=160,
        )
        is True
    )
    assert (
        context.is_explicit_downstream_repair_branch_context_allowed(
            repair_branch,
            upstream_pr=161,
        )
        is True
    )
    assert (
        context.is_explicit_downstream_repair_branch_context_allowed(
            repair_branch,
            upstream_pr=162,
        )
        is False
    )
    assert (
        context.is_explicit_downstream_repair_branch_context_allowed(
            repair_branch,
            upstream_pr=163,
        )
        is False
    )
    assert (
        context.is_explicit_downstream_repair_branch_context_allowed(
            "repair/pr163-c-unrelated-context",
            upstream_pr=160,
        )
        is False
    )
    assert (
        context.is_downstream_or_main_validation_branch(
            repair_branch,
            after_pr=160,
            allow_repair=False,
        )
        is True
    )
    assert (
        context.is_downstream_or_main_validation_branch(
            repair_branch,
            after_pr=163,
            allow_repair=False,
        )
        is False
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/validators.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/schemas/"
        "pr163_c_report_manifest.schema.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/test_pr163_c_report_sharding_limits.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr163_c_shards/"
        "PR163_C_ArtificialInfrastructureRejectionTaxonomy.part_0001_of_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/build_pr163_c_pretrade_infrastructure_rejection_remediation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/ci_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/run_validation_gates.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/"
        "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "source_intelligence/test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
        "pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/"
        "test_pr161a_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/"
        "test_pr161b_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "safe_repo_local_nonlive_dataset_materialization_authority_gate/"
        "validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "source_intelligence/pr159s_open_intake/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "source_intelligence/test_pr159s_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/"
        "test_pr160_branch_context_relaxation.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
        "pr161a_materialization_bridge/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/atomicrows_pr154_value_state/"
        "test_pr161a_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "master_plan_residual_candidate_coverage/"
        "test_pr161b_branch_context.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "safe_repo_local_nonlive_dataset_materialization_authority_gate/"
        "validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "src/qtt/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tests/stage1_prediction_markets/"
        "pr163_c_pretrade_infrastructure_rejection_remediation/"
        "test_pr163_c_repeat_run_determinism.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        repair_branch,
        "tools/ci_branch_context.py",
    )
    atomicrows_bundle_path = (
        "docs/master_plan/atomic_rows/" + "AtomicRows" + ".bundle" + ".jsonl"
    )
    atomicrows_sidecar_path = (
        "docs/master_plan/atomic_rows/"
        + "AtomicRows"
        + ".bundle"
        + "."
        + "sha256"
    )
    forbidden_repair_paths = (
        "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
        "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/generated/PR163_C_RuntimeCashAuthority.report.json",
        atomicrows_bundle_path,
        atomicrows_sidecar_path,
        "docs/master_plan/source_evidence/accepted_source_packet.json",
        "src/qtt/source_evidence/connector_binding.py",
        "src/qtt/stage1_prediction_markets/private_state/account_snapshot.py",
        "src/qtt/stage1_prediction_markets/runtime_cash/cash_state.py",
        "src/qtt/stage1_prediction_markets/order_live/live_order_router.py",
        "src/qtt/stage1_prediction_markets/quantum_backend/backend_runtime.py",
        "src/qtt/stage1_prediction_markets/llm_runtime/model_client.py",
        "src/qtt/stage1_prediction_markets/freeze_checksum/qku_digest.py",
        "src/qtt/stage1_prediction_markets/profit_claims/profit_summary.py",
    )
    for forbidden_path in forbidden_repair_paths:
        assert not context.is_explicit_downstream_repair_changed_path(
            repair_branch,
            forbidden_path,
        )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit/validators.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR163_B_FinalSummary.report.json",
    )

    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1000/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", branch)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == branch


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


def test_upstream_branch_gate_policy_exact_repairs_are_fail_closed():
    assert context.is_branch_allowed_for_upstream_pr_gate(
        context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        "PR160",
        ancestry_present=True,
    )
    assert not context.is_branch_allowed_for_upstream_pr_gate(
        context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        "PR160",
    )
    assert context.is_explicit_repair_branch_allowed_for_upstream_pr_gate(
        context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
        "PR160",
    )
    assert not context.is_explicit_repair_branch_allowed_for_upstream_pr_gate(
        "repair/pr163-c-unrelated-context",
        "PR160",
    )
    assert not context.is_branch_allowed_for_upstream_pr_gate(
        "repair/pr163-c-unrelated-context",
        "PR160",
        ancestry_present=True,
    )


def test_upstream_branch_gate_policy_allows_exact_validation_infrastructure_branch():
    for branch in context.VALIDATION_INFRASTRUCTURE_BRANCHES:
        for gate_id in context.BRANCH_CONTEXT_GATE_POLICIES:
            assert context.is_branch_allowed_for_upstream_pr_gate(branch, gate_id)
            assert context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
                branch,
                gate_id,
            )
            copycat_branch = f"{branch}-copy"
            assert not context.is_branch_allowed_for_upstream_pr_gate(
                copycat_branch,
                gate_id,
                ancestry_present=True,
            )
            assert not context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
                copycat_branch,
                gate_id,
            )


def test_changed_path_helper_requires_exact_repair_scope():
    assert context.changed_path_allowed_for_explicit_repair_branch(
        context.PR160_MAIN_ANCESTRY_REPAIR_BRANCH,
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert not context.changed_path_allowed_for_explicit_repair_branch(
        "repair/pr160-unlisted-context",
        "src/qtt/stage1_prediction_markets/"
        "pr160_split_reclassification_route_closure/validator.py",
    )
    assert not context.changed_path_allowed_for_explicit_repair_branch(
        context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    )

    branch = context.NO_RUNTIME_CUSTODY_AND_CI_DEPENDENCY_REPAIR_BRANCH
    expected_paths = frozenset(
        {
            "tools/validate_no_runtime_artifacts.py",
            "tests/fail_closed/test_no_runtime_artifacts_strict.py",
            "tools/validation_inventory.py",
            "tests/tools/test_changed_area_validation_router.py",
            "tools/ci_branch_context.py",
            "tests/tools/test_ci_branch_context.py",
            "tools/run_validation_gates.py",
            "tests/fail_closed/test_run_validation_gates.py",
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        }
    )
    assert context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS[branch] == (
        expected_paths
    )
    for path in expected_paths:
        assert context.changed_path_allowed_for_explicit_repair_branch(branch, path)

    for path in (
        "README.md",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "src/qtt/runtime/order_executor.py",
    ):
        assert not context.changed_path_allowed_for_explicit_repair_branch(branch, path)

    for lookalike_branch in (f"{branch}/nested", f"{branch}-suffix"):
        assert not context.changed_path_allowed_for_explicit_repair_branch(
            lookalike_branch,
            "tools/ci_branch_context.py",
        )


def test_idempotence_runtime_containment_hardening_scope_is_exact():
    branch = context.IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_BRANCH
    assert context.is_idempotence_runtime_containment_hardening_branch(branch)
    assert context.is_downstream_or_main_validation_branch(
        branch,
        after_pr=138,
        allow_repair=False,
    )
    assert context.is_pr_or_later_branch(branch, minimum_pr=99)
    assert not context.is_validation_infrastructure_branch(branch)
    assert context.is_branch_allowed_for_upstream_pr_gate(branch, "PR160")
    assert context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
        branch,
        "PR160",
    )

    for path in context.IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_CHANGED_PATHS:
        assert context.is_idempotence_runtime_containment_hardening_changed_path(
            branch,
            path,
        )
        assert context.is_explicit_downstream_repair_changed_path(branch, path)

    denied_paths = (
        ".github/workflows/unrelated.yml",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
        "src/qtt/stage1_prediction_markets/"
        "pr165_d3_quantum_aware_scenario_selection_v3/report.py",
        "src/qtt/stage1_prediction_markets/"
        "pr166_q_quantum_comparator_business_logic/validator.py",
        "tests/stage1_prediction_markets/"
        "pr165_d3_quantum_aware_scenario_selection_v3/test_pr165_d3_idempotence.py",
    )
    for path in denied_paths:
        assert not context.is_validation_infrastructure_changed_path(branch, path)
        assert not context.is_idempotence_runtime_containment_hardening_changed_path(
            branch,
            path,
        )
        assert not context.is_explicit_downstream_repair_changed_path(branch, path)


def test_pr166_sm2_bounded_idempotence_ci_repair_scope_is_exact():
    branch = context.PR166_SM2_BOUNDED_IDEMPOTENCE_CI_REPAIR_BRANCH
    assert context.is_downstream_or_main_validation_branch(
        branch,
        after_pr=138,
        allow_repair=False,
    )
    assert not context.is_downstream_or_main_validation_branch(
        branch,
        after_pr=166,
        allow_repair=False,
    )
    assert context.is_branch_allowed_for_upstream_pr_gate(branch, "PR160")
    assert context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
        branch,
        "PR160",
    )
    allowed_paths = (
        "src/qtt/stage1_prediction_markets/bounded_idempotence.py",
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/stage1_prediction_markets/"
        "pr165_d3_quantum_aware_scenario_selection_v3/test_pr165_d3_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr165_d2_score_refreshed_scenario_selection_v2/"
        "test_pr165_d2_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_s2_replay_paper_retest_loop_v2/test_pr166_s2_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_sf_repair_materialization_before_retest/test_pr166_sf_idempotence.py",
        "tests/stage1_prediction_markets/"
        "pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_idempotence.py",
        "tools/ci_branch_context.py",
        "tools/validate_repair_pr_changed_file_scope.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
    )

    for path in allowed_paths:
        assert context.changed_path_allowed_for_explicit_repair_branch(branch, path)

    denied_paths = (
        "docs/master_plan/generated/PR166_SM2_FinalSummary.report.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "src/qtt/stage1_prediction_markets/"
        "pr165_d3_quantum_aware_scenario_selection_v3/report_writer.py",
        "src/qtt/stage1_prediction_markets/quantum_backend/backend_runtime.py",
    )
    for path in denied_paths:
        assert not context.changed_path_allowed_for_explicit_repair_branch(branch, path)


def test_validation_infrastructure_changed_path_scope_is_exact():
    for branch in context.VALIDATION_INFRASTRUCTURE_BRANCHES:
        assert context.is_validation_infrastructure_branch(branch)
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_ci_branch_context_matrix.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/run_validation_gates.py",
        )
        for path in (
            ".gitattributes",
            "tools/validation_reliability.py",
            "tools/run_pytest_fresh_basetemp.py",
            "tests/fail_closed/test_pytest_fresh_basetemp_helper.py",
        ):
            assert context.is_validation_infrastructure_changed_path(branch, path)
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_no_runtime_artifacts.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/bounded_idempotence.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tests/tools/test_validate_repair_pr_changed_file_scope.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tests/atomicrows/test_atomicrows_sha_freeze_final_readiness_state_contract.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tests/atomicrows/test_atomicrows_bundle_materialization_manifest.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tests/atomicrows/test_atomicrows_bundle_boundary_state_contract.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/validator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr165_evidence_backed_scoring_ranking.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR165_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr165_shards/"
            "PR165_GlobalCandidateRanking.part_0001_of_0004.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr165_b_condition_scoped_negative_memory.py",
        )
        assert not context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/"
            "AtomicRowsShaFreezeFinalReadinessStateContract.report.json",
        )
        assert not context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_atomicrows_sha_freeze_authority_runtime.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR165_B_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr165_b_shards/"
            "PR165_B_ScenarioOutcomeMatrix.part_0001_of_0007.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr165_d_scenario_qku_combination_selection.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR165_D_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr165_d_shards/"
            "PR165_D_RetestBatchSelectionQueue.part_0001_of_0007.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr166_s_replay_paper_scenario_retest_execution.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR166_S_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr166_s_shards/"
            "PR166_S_OrderIntentRegistry.part_0001_of_0004.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr166_s_replay_paper_scenario_retest_execution/validators.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR166_SM_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr166_sm_shards/"
            "PR166_SM_RefreshedScoreRegistry.part_0001_of_0004.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr166_sm_score_memory_refresh_from_pr166_s_results/validator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr166_sf_repair_materialization_before_retest.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR166_SF_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr166_sf_shards/"
            "PR166_SF_TargetUniverseRegistry.part_0001_of_0004.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr166_sf_repair_materialization_before_retest/validator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr166_s2_replay_paper_retest_loop_v2.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR166_S2_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr166_s2_shards/"
            "PR166_S2_RetestUniverse.part_0001_of_0004.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr166_s2_replay_paper_retest_loop_v2/validator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr166_q_quantum_classical_hybrid_comparator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR166_Q_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr166_q_shards/"
            "PR166_Q_QuantumClassicalHybridRaceLedger.part_0001_of_0001.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr166_q_quantum_classical_hybrid_comparator/validator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr166_qb_bounded_quantum_benchmark.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR166_QB_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr166_qb_shards/"
            "PR166_QB_RaceArb.part_0001_of_0001.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr166_qb_bounded_quantum_benchmark/validator.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/PR165_D2_FinalSummary.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "docs/master_plan/generated/pr165_d2_shards/"
            "PR165_D2_NetEdgeAdjustedCandidateRanking.part_0001_of_0004.report.json",
        )
        assert context.is_validation_infrastructure_changed_path(
            branch,
            "src/qtt/stage1_prediction_markets/"
            "pr165_d2_score_refreshed_scenario_selection_v2/validator.py",
        )
        for path in context.IDEMPOTENCE_RUNTIME_CONTAINMENT_HARDENING_CHANGED_PATHS:
            assert context.is_validation_infrastructure_changed_path(branch, path)
    assert not context.is_validation_infrastructure_changed_path(
        "repair/pr163-c-main-branch-context-after-merge",
        "tools/validate_ci_branch_context_matrix.py",
    )
    assert not context.is_validation_infrastructure_changed_path(
        context.CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH,
        "docs/master_plan/generated/PR164ReviewProvenanceAudit.report.json",
    )
    assert not context.is_validation_infrastructure_changed_path(
        context.CI_RUNTIME_PARALLEL_CACHE_TIMEOUT_BRANCH,
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    )


def test_pull_request_detached_head_simulation_prefers_head_ref(monkeypatch):
    _clear_github_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/200/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "200/merge")
    monkeypatch.setenv(
        "GITHUB_HEAD_REF",
        context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
    )

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, "", ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, "HEAD", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    branch_context = context.current_branch_context(
        REPO_ROOT,
        git_stdout=fake_git_stdout,
    )
    assert branch_context.branch == context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH
    assert context.github_actions_pull_request_detached_context_active(
        branch_returncode=0,
        branch="",
    )
    assert not context.github_actions_main_push_context_active()
    assert context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
        branch_context.branch,
        "PR160",
    )

    s1_branch = context.S1_LAUNCH_GRAPH_IMPLEMENTATION_BRANCH
    assert s1_branch == "s1-launch-graph-materialization-01"
    assert s1_branch in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
    assert context.is_owner_authorized_validation_branch(s1_branch)
    assert not context.is_repair_branch(s1_branch)
    assert not context.is_main_cumulative_branch(s1_branch)
    assert context.roadmap_pr_number(s1_branch) is None
    for near_name in (
        s1_branch.upper(),
        f"{s1_branch}-copy",
        f"{s1_branch}/",
        s1_branch.replace("materialization", "*"),
        s1_branch.removesuffix("-01"),
    ):
        assert near_name not in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
        assert not context.is_owner_authorized_validation_branch(near_name)

    monkeypatch.setenv("GITHUB_HEAD_REF", s1_branch)
    s1_branch_context = context.current_branch_context(
        REPO_ROOT,
        git_stdout=fake_git_stdout,
    )
    assert s1_branch_context.branch == s1_branch
    assert s1_branch_context.source == "GITHUB_HEAD_REF"

    package_branch = context.S1_PLUGIN_PACKAGE_CURRENTIZATION_BRANCH
    assert package_branch == "s1-plugin-package-currentization-01"
    assert package_branch in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
    assert context.is_owner_authorized_validation_branch(package_branch)
    assert not context.is_repair_branch(package_branch)
    assert not context.is_main_cumulative_branch(package_branch)
    assert context.roadmap_pr_number(package_branch) is None
    for near_name in (
        package_branch.upper(),
        f"{package_branch}-copy",
        f"{package_branch}/",
        package_branch.replace("package", "*"),
        package_branch.removesuffix("-01"),
        package_branch.replace("currentization", "materialization"),
    ):
        assert near_name not in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
        assert not context.is_owner_authorized_validation_branch(near_name)

    monkeypatch.setenv("GITHUB_HEAD_REF", package_branch)
    package_branch_context = context.current_branch_context(
        REPO_ROOT,
        git_stdout=fake_git_stdout,
    )
    assert package_branch_context.branch == package_branch
    assert package_branch_context.source == "GITHUB_HEAD_REF"

    pit_branch = context.S1_PIT_DATA_PHASE_A_01_IMPLEMENTATION_BRANCH
    assert pit_branch == "s1-pit-data-phase-a-01"
    assert pit_branch in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
    assert context.is_owner_authorized_validation_branch(pit_branch)
    assert not context.is_repair_branch(pit_branch)
    assert not context.is_main_cumulative_branch(pit_branch)
    assert context.roadmap_pr_number(pit_branch) is None
    for near_name in (
        pit_branch.upper(),
        f"{pit_branch}-copy",
        f"{pit_branch}/",
        pit_branch.replace("phase-a-01", "phase-*-01"),
        pit_branch.removesuffix("-01"),
    ):
        assert near_name not in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
        assert not context.is_owner_authorized_validation_branch(near_name)

    monkeypatch.setenv("GITHUB_HEAD_REF", pit_branch)
    pit_branch_context = context.current_branch_context(
        REPO_ROOT,
        git_stdout=fake_git_stdout,
    )
    assert pit_branch_context.branch == pit_branch
    assert pit_branch_context.source == "GITHUB_HEAD_REF"


def test_pr152_helper_cli_repair_branch_allows_validation_execution_gates_only():
    branch = context.PR152_HELPER_CLI_TEMP_REPO_GIT_STATUS_REPAIR_BRANCH

    assert context.is_validation_execution_branch(branch)
    assert not context.is_validation_infrastructure_branch(branch)
    assert context.is_downstream_or_main_validation_branch(
        branch,
        after_pr=166,
        allow_repair=False,
    )
    for gate_id in context.BRANCH_CONTEXT_GATE_POLICIES:
        assert context.is_branch_allowed_for_upstream_pr_gate(branch, gate_id)
        assert context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
            branch,
            gate_id,
        )

    copycat = f"{branch}-copy"
    assert not context.is_validation_execution_branch(copycat)
    for gate_id in context.BRANCH_CONTEXT_GATE_POLICIES:
        assert not context.is_branch_allowed_for_upstream_pr_gate(
            copycat,
            gate_id,
            ancestry_present=True,
        )
        assert not context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
            copycat,
            gate_id,
        )


def test_pr165_d3_quantum_selection_branch_context_allowance_is_narrow():
    branch = context.PR165_D3_BRANCH
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR165_D3_FinalSummary.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr165_d3_shards/"
        "PR165_D3_SelectedCombos.shard_0001.report.json",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "pr165_d3_quantum_aware_scenario_selection_v3/validator.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_pr165_d3_quantum_aware_scenario_selection_v3.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_no_runtime_artifacts.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        ".github/workflows/qtt_validation.yml",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_sha_freeze_final_readiness_state_contract.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_bundle_materialization_manifest.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/atomicrows/test_atomicrows_bundle_boundary_state_contract.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2/report_writer.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr166_sf_repair_materialization_before_retest/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3/io.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sf_r2_targeted_conversion_repair_retest/"
        "test_pr166_sf_r2_idempotence.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "tests/stage1_prediction_markets/"
        "pr166_sm3_score_memory_refresh_v3/"
        "test_pr166_sm3_idempotence.py",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR166_SM3_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/AtomicRowsShaFreezeFinalReadinessStateContract.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "tools/validate_no_runtime_trade_execution.py",
    )


def test_st12g_owner_authorized_branch_match_is_exact() -> None:
    branch = "agent/st12g-existing-owner-projections-v2"
    assert branch in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
    assert context.is_owner_authorized_validation_branch(branch)
    for near_name in (
        f"{branch}-copy",
        branch.removesuffix("-v2"),
        branch.upper(),
    ):
        assert near_name not in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
        assert not context.is_owner_authorized_validation_branch(near_name)

    engvr_branch = context.ENGVR_IMPLEMENTATION_BRANCH
    conditional_report = (
        "docs/master_plan/generated/"
        "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    )
    assert engvr_branch in context.OWNER_AUTHORIZED_VALIDATION_BRANCHES
    assert context.is_owner_authorized_validation_branch(engvr_branch)
    assert len(context.ENGVR_NORMAL_CHANGED_PATHS) == 16
    assert context.ENGVR_TRIGGERED_CONDITIONAL_CHANGED_PATHS == frozenset(
        {conditional_report}
    )
    assert len(context.ENGVR_TRIGGERED_CONDITIONAL_CHANGED_PATHS) == 1
    assert len(context.ENGVR_CHANGED_PATHS) == 17
    assert context.ENGVR_CHANGED_PATHS == (
        context.ENGVR_NORMAL_CHANGED_PATHS
        | context.ENGVR_TRIGGERED_CONDITIONAL_CHANGED_PATHS
    )
    assert context.EXPLICIT_DOWNSTREAM_REPAIR_BRANCH_CHANGED_PATHS[engvr_branch] == (
        context.ENGVR_CHANGED_PATHS
    )
    assert context.is_explicit_downstream_repair_changed_path(
        engvr_branch,
        conditional_report,
    )
    for path in context.ENGVR_CHANGED_PATHS:
        assert context.is_explicit_downstream_repair_changed_path(engvr_branch, path)
        assert "*" not in path and "?" not in path and "[" not in path
        assert not context.is_explicit_downstream_repair_changed_path(
            engvr_branch,
            f"{path}.near",
        )
    for near_name in (
        engvr_branch.upper(),
        f"{engvr_branch}-copy",
        engvr_branch.removeprefix("hardening/"),
        f"{engvr_branch}/",
    ):
        assert not context.is_owner_authorized_validation_branch(near_name)
        assert not context.is_explicit_downstream_repair_changed_path(
            near_name,
            "tools/validation_reliability.py",
        )
    for protected in (
        ".github/workflows/qtt_validation.yml",
        "src/qtt/stage1_prediction_markets/example.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "tools/changed_area_validation_router.py",
    ):
        assert protected not in context.ENGVR_CHANGED_PATHS
        assert not context.is_explicit_downstream_repair_changed_path(
            engvr_branch,
            protected,
        )
    for near_conditional_report in (
        conditional_report.upper(),
        conditional_report.removesuffix(".json"),
        f"{conditional_report}.near",
        f"near/{conditional_report}",
        "docs/master_plan/generated/",
    ):
        assert near_conditional_report not in context.ENGVR_CHANGED_PATHS
        assert not context.is_explicit_downstream_repair_changed_path(
            engvr_branch,
            near_conditional_report,
        )


_F14_EXPECTED_PATHS = frozenset(('src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/persistence.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/sqlite_reference.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/transaction.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py', 'tests/source_evidence/test_s1_pit_data_phase_a_01.py', 'tests/stage1_prediction_markets/qku_computation_control_plane/accounting/test_contract_matrix.py', 'tests/stage1_prediction_markets/qku_computation_control_plane/security/test_deserialization_safety.py', 'tests/stage1_prediction_markets/qku_computation_control_plane/tranche_b/test_resolution_pipeline.py', 'tests/tools/test_ci_branch_context.py', 'tools/ci_branch_context.py', 'tools/validation_scope_registry.py', 'tools/independent_validate_qku_computation_control_plane_execution.py', 'src/qtt/stage1_prediction_markets/private_state_receipts/request.py', 'src/qtt/stage1_prediction_markets/private_state_receipts/receipt.py', 'src/qtt/stage1_prediction_markets/private_state_receipts/handoff.py', 'tools/validate_source_fact_binding_connector_semantic_readiness_static.py', 'tools/validate_no_runtime_artifacts.py', 'tests/source_evidence/test_source_fact_binding_connector_semantic_readiness_static.py', 'tests/fail_closed/test_no_runtime_artifacts_strict.py', '.github/workflows/qtt_validation.yml', '.gitignore', 'tools/validation_reliability.py', 'tools/run_validation_gates.py', 'src/qtt/core/testing/gate_result.py', 'tests/fail_closed/test_run_validation_gates.py', 'tests/fail_closed/test_pytest_fresh_basetemp_helper.py', 'tools/independent_validate_qku_computation_control_plane.py', 'src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py', 'tools/currentize_pr152_after_generated_artifacts.py', 'tests/tools/test_currentize_pr152_after_generated_artifacts.py', 'tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py', 'tests/atomicrows/test_atomicrows_semantic_value_materialization_owner_authorization_gate.py', 'tests/atomicrows/test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py'))


def _assert_f14_exact_scope_and_interfaces():
    from tools.validation_scope_registry import F14_ALLOWED_EXACT_PATHS, explain_pr_scope_decision
    from tools.independent_validate_qku_computation_control_plane_execution import _f14_execution_contract_failures_v1
    assert F14_ALLOWED_EXACT_PATHS == _F14_EXPECTED_PATHS and len(_F14_EXPECTED_PATHS) == 37
    branch = 'f14-private-evidence-join'
    assert context.F14_PRIVATE_EVIDENCE_JOIN_BRANCH == branch
    assert context.is_owner_authorized_validation_branch(branch)
    for bad in (branch.upper(), 'prefix-' + branch, branch + '-suffix', branch + '/', 'f14-private-*'):
        assert not context.is_owner_authorized_validation_branch(bad)
    for path in _F14_EXPECTED_PATHS:
        decision = explain_pr_scope_decision(branch,path)
        assert decision['allowed'] is True and decision['pr_id'] == 'F14'
    for path in ('src/qtt/stage1_prediction_markets/credential_readiness/validator.py',
            'src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py',
            '.gitattributes', 'tests/new_f14_test.py', 'docs/master_plan/MasterPlan.md'):
        assert explain_pr_scope_decision(branch,path)['allowed'] is False
    assert _f14_execution_contract_failures_v1(REPO_ROOT) == []
    original = Path.read_text
    for old,new in (('PRIVATE_EVIDENCE_WITNESS = "PRIVATE_EVIDENCE_WITNESS"',
            'PRIVATE_EVIDENCE_WITNESS = "SAME_COUNT_SUBSTITUTION"'),
            ('def load_committed_private_evidence_snapshot_v1(', 'def foreign_snapshot_reader(')):
        def changed(path,*args,**kwargs):
            text=original(path,*args,**kwargs)
            if path.name in ('receipts.py','persistence.py'): return text.replace(old,new)
            return text
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(Path,'read_text',changed)
            assert _f14_execution_contract_failures_v1(REPO_ROOT)

    from tools import validation_scope_registry as registry
    from src.qtt.stage1_prediction_markets.atomicrows_semantic_field_coverage_enrichment_plan import report as pr140_report
    from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_owner_authorization_gate import report as pr141_report
    from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate import report as pr142_report

    original_scope = registry.F14_ALLOWED_EXACT_PATHS
    removed_path = 'tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan.py'
    sibling = 'tests/atomicrows/test_atomicrows_semantic_field_coverage_enrichment_plan_extra.py'
    for changed_scope in (
        _F14_EXPECTED_PATHS - {removed_path},
        _F14_EXPECTED_PATHS | {sibling},
        (_F14_EXPECTED_PATHS - {removed_path}) | {sibling},
    ):
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(registry, 'F14_ALLOWED_EXACT_PATHS', changed_scope)
            with pytest.raises(AssertionError):
                _assert_f14_exact_scope_and_interfaces()
        assert registry.F14_ALLOWED_EXACT_PATHS is original_scope

    legacy_exclusions = (
        '.gitignore',
        'src/qtt/stage1_prediction_markets/private_state_receipts/handoff.py',
        'src/qtt/stage1_prediction_markets/private_state_receipts/receipt.py',
        'src/qtt/stage1_prediction_markets/private_state_receipts/request.py',
        'tests/tools/test_currentize_pr152_after_generated_artifacts.py',
    )
    protected_paths = (
        ('docs/master_plan/QTT_MasterPlan_Current.md', 'MASTER_PLAN_MUTATION_DETECTED'),
        ('docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl', 'ATOMICROWS_BUNDLE_MUTATION_DETECTED'),
        ('docs/master_plan/atomic_rows/pr98_row_family_sources/source_rows.jsonl', 'ROW_FAMILY_SOURCE_MUTATION_DETECTED'),
    )
    for label, report in (('PR140', pr140_report), ('PR141', pr141_report), ('PR142', pr142_report)):
        original_context = report.current_branch_context
        original_changed_paths = report._changed_paths
        with pytest.MonkeyPatch.context() as patch:
            f14_context = context.BranchContext(branch=branch, source='unit-test')
            patch.setattr(report, 'current_branch_context', lambda root: f14_context)
            patch.setattr(report, '_changed_paths', lambda root: sorted(_F14_EXPECTED_PATHS))
            assert report._validate_changed_paths(REPO_ROOT) == []
            for path, reason in protected_paths:
                patch.setattr(report, '_changed_paths', lambda root, path=path: [path])
                assert f'{label}_{reason}' in report._validate_changed_paths(REPO_ROOT)
            patch.setattr(report, '_changed_paths', lambda root: [sibling])
            assert report._validate_changed_paths(REPO_ROOT) == [f'{label}_CHANGED_PATH_OUT_OF_SCOPE: {sibling}']
            legacy_context = context.BranchContext(
                branch='pr-ci-fastfail-validation-context-preflight', source='unit-test'
            )
            patch.setattr(report, 'current_branch_context', lambda root: legacy_context)
            patch.setattr(report, '_changed_paths', lambda root: list(legacy_exclusions))
            assert report._validate_changed_paths(REPO_ROOT) == sorted(
                f'{label}_CHANGED_PATH_OUT_OF_SCOPE: {path}' for path in legacy_exclusions
            )
            lookalike_context = context.BranchContext(branch=branch + '-unregistered', source='unit-test')
            patch.setattr(report, 'current_branch_context', lambda root: lookalike_context)
            patch.setattr(report, '_changed_paths', lambda root: ['.gitignore'])
            assert report._validate_changed_paths(REPO_ROOT) == [f'{label}_CHANGED_PATH_OUT_OF_SCOPE: .gitignore']
        assert report.current_branch_context is original_context
        assert report._changed_paths is original_changed_paths
