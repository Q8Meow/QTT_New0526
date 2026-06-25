from __future__ import annotations

from tools.pr168_rp5c_config import CENTRAL_SURFACE_SHARDS, generated_ref, shard_path

from ._helpers import load_report


def test_rp5c_central_surface_manifest_lists_required_surfaces() -> None:
    report = load_report("PR168_RP5C_CentralSurfaceManifest.report.json")
    listed = set(report["canonical_active_surfaces"])
    required = {generated_ref(shard_path(key)) for key in CENTRAL_SURFACE_SHARDS}

    assert required.issubset(listed)
    assert report["central_surface_count"] == len(report["records"])
    assert all(row["raw_legacy_direct_consumer_allowed_flag"] is False for row in report["records"])
