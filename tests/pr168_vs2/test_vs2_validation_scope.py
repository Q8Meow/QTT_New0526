from pathlib import Path

from tools.changed_area_validation_router import RouterInput, build_router_result
from tools import validation_scope_registry as registry


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_vs2_branch_scope_allows_owned_paths() -> None:
    for path in (
        "docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl",
        "docs/master_plan/generated/pr168_vs2/no_private_state.jsonl",
        "docs/master_plan/generated/pr168_vs2/no_private_state.manifest.json",
        "src/qtt/paper/pr168_vs2/builder.py",
        "tools/build_pr168_vs2_paper_intent_candidates.py",
        "tools/validate_pr168_vs2_paper_intent_candidates.py",
        "tests/pr168_vs2/test_vs2_builder.py",
    ):
        assert registry.is_pr_scoped_changed_path_allowed(registry.PR168_VS2_BRANCH, path)


def test_changed_area_router_maps_vs2_generated_output_to_vs2_validators() -> None:
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=("docs/master_plan/generated/pr168_vs2/vs2_packet_registry.jsonl",),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch=registry.PR168_VS2_BRANCH,
        )
    )
    assert "build_pr168_vs2_paper_intent_candidates" in result.required_validators
    assert "validate_pr168_vs2_paper_intent_candidates" in result.required_validators
    assert result.fail_closed_reasons == ()
