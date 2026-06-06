from pathlib import Path

from tools import ci_branch_context as context


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_ci_branch_context_pr163_pull_request_merge_ref(monkeypatch):
    for env_name in ("GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_REF_NAME", "GITHUB_HEAD_REF", "GITHUB_BASE_REF"):
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/999/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", "pr163-generic-paper-adapter-capture-framework")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    assert context.current_branch_context(REPO_ROOT).branch == "pr163-generic-paper-adapter-capture-framework"
    assert context.is_explicit_downstream_repair_changed_path(
        "pr163-generic-paper-adapter-capture-framework",
        "docs/master_plan/generated/PR163_FinalSummary.report.json",
    )
