"""Report and generated artifact helpers for PR157."""

from __future__ import annotations

from pathlib import Path

from . import constants as c
from .completion_registry import build_artifacts
from .io import json_dump, write_json_file
from .models import BuildArtifacts


def write_artifacts(repo_root: Path | str) -> tuple[Path, Path, Path, Path, Path]:
    root = Path(repo_root).resolve()
    artifacts = build_artifacts(root)
    paths = (
        root / c.PR154_REPORT_PATH,
        root / c.PR154_REGISTRY_PATH,
        root / c.ATOMICROWS_REPORT_PATH,
        root / c.ATOMICROWS_REGISTRY_PATH,
        root / c.OWNER_REQUEST_PATH,
    )
    payloads = (
        artifacts.pr154_report,
        artifacts.pr154_registry,
        artifacts.atomicrows_report,
        artifacts.atomicrows_registry,
        artifacts.owner_request_packet,
    )
    for path, payload in zip(paths, payloads):
        write_json_file(path, payload)
    for shard in artifacts.atomicrows_shards:
        shard_path = root / Path(str(shard["shard_path"]))
        write_json_file(
            shard_path,
            {
                "registry_type": "PR157_ATOMICROWS_4183_COMPLETION_MATERIALIZATION_SHARD",
                "pr_id": c.PR_ID,
                "semantic_task_id": c.SEMANTIC_TASK_ID,
                "authority_class": c.AUTHORITY_CLASS,
                "shard_id": shard["shard_id"],
                "row_count": shard["row_count"],
                "first_row_id": shard["first_row_id"],
                "last_row_id": shard["last_row_id"],
                "records": shard["records"],
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            },
        )
    return paths


__all__ = ["BuildArtifacts", "build_artifacts", "json_dump", "write_artifacts"]
