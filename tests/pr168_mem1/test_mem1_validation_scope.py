from pathlib import Path

from tools.changed_area_validation_router import RouterInput, build_router_result
from tools import validation_scope_registry as registry


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_mem1_branch_scope_allows_owned_paths() -> None:
    for path in (
        "docs/master_plan/generated/pr168_mem1/winning_recipe.jsonl",
        "src/qtt/memory/pr168_mem1/builder.py",
        "tools/build_pr168_mem1_condition_scoped_memory.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_mem1_condition_scoped_memory.py",
        "tools/query_pr168_mem1_memory.py",
        "tests/pr168_mem1/test_mem1_builder.py",
    ):
        assert registry.is_pr_scoped_changed_path_allowed(registry.PR168_MEM1_BRANCH, path)


def test_changed_area_router_maps_mem1_generated_output_to_mem1_validators() -> None:
    result = build_router_result(
        RouterInput(
            repo_root=REPO_ROOT,
            changed_files=("docs/master_plan/generated/pr168_mem1/winning_recipe.jsonl",),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch=registry.PR168_MEM1_BRANCH,
        )
    )
    assert "build_pr168_mem1_condition_scoped_memory" in result.required_validators
    assert "validate_pr168_mem1_condition_scoped_memory" in result.required_validators
    assert result.fail_closed_reasons == ()
