"""Report sharding helpers.

PR162R-B keeps row-level reports monolithic because the generated payloads are
within the size already used by nearby PR162R artifacts. This module records the
decision so validators and tests have a canonical place to inspect it.
"""

from __future__ import annotations

from typing import Any


def shard_manifest_for(filename: str, row_count: int) -> dict[str, Any]:
    return {
        "report_filename": filename,
        "row_count": row_count,
        "sharded_flag": False,
        "shard_paths": [],
        "shard_count": 0,
    }
