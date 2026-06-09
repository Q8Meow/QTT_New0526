"""Agent task queue projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_agent_task_queue_rows(repo_root):
    return build_core_tables(repo_root)["AgentTaskQueueCoreTable"]
