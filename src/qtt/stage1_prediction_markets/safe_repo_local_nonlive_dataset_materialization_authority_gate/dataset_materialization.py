"""Repo-local PR162A dataset materialization and manifest construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .dataset_normalization import normalize_kalshi_raw
from .json_io import read_json, write_json, write_jsonl
from .paths import repo_relative_posix


def materialize_repo_local_datasets(repo_root: Path) -> dict[str, Any]:
    raw_path = repo_root / c.KALSHI_TINY_RAW_PATH
    if not raw_path.exists():
        raise FileNotFoundError(f"missing PR162A raw candidate: {c.KALSHI_TINY_RAW_PATH.as_posix()}")
    raw_payload = read_json(raw_path)
    normalized_rows = normalize_kalshi_raw(raw_payload)
    normalized_path = repo_root / c.KALSHI_TINY_NORMALIZED_PATH
    write_jsonl(normalized_path, normalized_rows)
    manifest = {
        "dataset_id": c.KALSHI_RUN_CAPABLE_DATASET_ID,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "dataset_authority_class": "REPO_LOCAL_OFFICIAL_PUBLIC_HISTORICAL_DATASET_CANDIDATE",
        "source_class": "OFFICIAL_PUBLIC_HISTORICAL_DATA_CANDIDATE",
        "venue_scope": "KALSHI",
        "access_rights_status": "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK",
        "candidate_only_flag": True,
        "adapter_mechanics_fixture_flag": True,
        "dataset_seed_candidate_flag": True,
        "dataset_coverage_state": c.VENUE_SCOPED_RUN_CAPABLE_READY,
        "raw_relative_posix_path": repo_relative_posix(repo_root, raw_path),
        "normalized_relative_posix_path": repo_relative_posix(repo_root, normalized_path),
        "row_count_candidate": len(normalized_rows),
        "time_window_start": normalized_rows[0]["timestamp"],
        "time_window_end": normalized_rows[-1]["timestamp"],
        "strict_run_capable_min_row_count": c.MIN_STRICT_RUN_CAPABLE_ROW_COUNT,
        "strict_run_capable_min_time_window_seconds": (
            c.MIN_STRICT_RUN_CAPABLE_TIME_WINDOW_SECONDS
        ),
        "ci_requires_network": False,
        "network_materialization_in_default_build_flag": False,
        "materialization_mode": "NORMALIZE_EXISTING_REPO_LOCAL_DATA",
    }
    write_json(repo_root / c.KALSHI_TINY_MANIFEST_PATH, manifest)
    return {
        "raw_payload": raw_payload,
        "normalized_rows": normalized_rows,
        "manifest": manifest,
        "raw_path": raw_path,
        "normalized_path": normalized_path,
        "manifest_path": repo_root / c.KALSHI_TINY_MANIFEST_PATH,
    }


def file_size_class(size: int) -> str:
    if size < 1_000_000:
        return "SMALL"
    if size < 25_000_000:
        return "MEDIUM"
    return "LARGE_STREAMING_METADATA_ONLY"
