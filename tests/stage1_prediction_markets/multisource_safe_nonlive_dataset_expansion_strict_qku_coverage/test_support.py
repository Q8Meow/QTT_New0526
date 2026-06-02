from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.json_io import (
    read_json,
    records_from_payload,
)
from src.qtt.stage1_prediction_markets.multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.paths import (
    resolve_repo_relative,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def report(filename: str) -> dict[str, Any]:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


def records(filename: str) -> list[dict[str, Any]]:
    payload = report(filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest = report(c.SHARD_MANIFEST_REPORT_FILENAME)
    by_report = {
        record["report_filename"]: record
        for record in records_from_payload(manifest)
    }
    output: list[dict[str, Any]] = []
    for shard_ref in by_report[filename]["shard_files"]:
        output.extend(records_from_payload(read_json(resolve_repo_relative(REPO_ROOT, shard_ref))))
    return output
