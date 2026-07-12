from __future__ import annotations

import pytest

from tools import build_pr168_rp5c_immutable_qku_formula_library as builder
from tools.pr168_rp5c_config import (
    ALLOWED_BUILD_BRANCH_NAMES,
    BRANCH_NAME,
    PR169_QKU_FORMULA_EXP1_ROLLBACK_VALIDATION_BRANCH_NAME,
)

from ._helpers import assert_hard_zero_report, load_report, load_rows


def test_rp5c_input_discovery_consumes_required_surfaces() -> None:
    report = load_report("PR168_RP5C_Input.report.json")
    rows = load_rows("source_artifact_consumption_ledger")
    paths = {row["source_file_path"] for row in rows}

    assert report["branch_name"] == "pr168-rp5c-immutable-qku-formula-library"
    assert "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json" in paths
    assert "docs/master_plan/generated/PR168_RP5B_LegacyKeepReasonLedger.report.json" in paths
    assert "docs/master_plan/generated/PR168_RP5A_QKUFormulaIdentityDependency.report.json" in paths
    assert "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json" in paths
    assert "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json" in paths
    assert all(row["consumption_status"] for row in rows)
    assert_hard_zero_report(report)


def _preflight(branch: str) -> dict[str, object]:
    return {
        "effective_branch_name": branch,
        "current_branch": branch,
        "ci_head_ref": None,
        "ci_ref_name": None,
    }


@pytest.mark.parametrize("branch", ALLOWED_BUILD_BRANCH_NAMES)
def test_rp5c_builder_accepts_expected_post_merge_branch_contexts(branch: str) -> None:
    builder._ensure_allowed_build_branch(_preflight(branch))


def test_rp5c_builder_accepts_exact_pr169_rollback_pull_request_context() -> None:
    branch = PR169_QKU_FORMULA_EXP1_ROLLBACK_VALIDATION_BRANCH_NAME
    effective = builder._effective_branch_name(
        "",
        branch,
        "274/merge",
        github_actions=True,
    )

    assert effective == branch
    builder._ensure_allowed_build_branch(_preflight(effective))


@pytest.mark.parametrize(
    "branch",
    [
        "PR169-QKU-FORMULA-EXP1-ROLLBACK",
        "xpr169-qku-formula-exp1-rollback",
        "pr169-qku-formula-exp1-rollback-repair",
        "pr169-qku-formula-exp1",
    ],
)
def test_rp5c_builder_rejects_pr169_rollback_branch_variants(branch: str) -> None:
    with pytest.raises(RuntimeError, match=BRANCH_NAME):
        builder._ensure_allowed_build_branch(_preflight(branch))


def test_rp5c_builder_accepts_github_actions_main_detached_head_context() -> None:
    effective = builder._effective_branch_name(
        "",
        None,
        "main",
        github_actions=True,
    )

    assert effective == "main"
    builder._ensure_allowed_build_branch(_preflight(effective))


def test_rp5c_builder_accepts_rp5f_pull_request_merge_context() -> None:
    effective = builder._effective_branch_name(
        "",
        "pr168-rp5f-dynamic-target-order-grid",
        "250/merge",
        github_actions=True,
    )

    assert effective == "pr168-rp5f-dynamic-target-order-grid"
    builder._ensure_allowed_build_branch(_preflight(effective))


def test_rp5c_builder_accepts_dash1_ui1_r2_r5_pull_request_merge_context() -> None:
    branch = "pr169-dash1-ui1-r2-r5-owner-visual-qa-truth-repair"
    effective = builder._effective_branch_name(
        "",
        branch,
        "265/merge",
        github_actions=True,
    )

    assert effective == branch
    builder._ensure_allowed_build_branch(_preflight(effective))


def test_rp5c_builder_accepts_dash1_ui1_r2_r6_pull_request_merge_context() -> None:
    branch = "pr169-ui1-r2r6"
    effective = builder._effective_branch_name(
        "",
        branch,
        "266/merge",
        github_actions=True,
    )

    assert effective == branch
    builder._ensure_allowed_build_branch(_preflight(effective))


def test_rp5c_builder_rejects_arbitrary_branch_context() -> None:
    with pytest.raises(RuntimeError, match=BRANCH_NAME):
        builder._ensure_allowed_build_branch(_preflight("feature/not-rp5c"))


def test_rp5c_builder_ignores_ci_branch_env_outside_github_actions() -> None:
    effective = builder._effective_branch_name(
        "",
        BRANCH_NAME,
        "main",
        github_actions=False,
    )

    assert effective == ""
    with pytest.raises(RuntimeError, match=BRANCH_NAME):
        builder._ensure_allowed_build_branch(_preflight(effective))
