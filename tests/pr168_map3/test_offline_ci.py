from __future__ import annotations

from pathlib import Path

from tests.pr168_map3._helpers import new_map3_workspace, run_map3_tool


def test_offline_builder_and_validator_do_not_require_network() -> None:
    with new_map3_workspace() as workspace_name:
        workspace = Path(workspace_name)
        run_map3_tool(workspace, "build_pr168_map3.py", "--offline")
        run_map3_tool(workspace, "validate_pr168_map3.py")
