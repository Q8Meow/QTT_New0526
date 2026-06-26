from __future__ import annotations

from tools.pr168_rp5c_config import ROW_SHARDS, manifest_path_for_shard, shard_path
from tools.pr168_rp5c_report_writer import read_json, read_jsonl

from ._helpers import load_report


def test_rp5c_generated_paths_are_cross_os_safe_and_manifests_match() -> None:
    audit = load_report("PR168_RP5C_CrossOSPathPortabilityAudit.report.json")

    assert audit["generated_path_case_collision_count"] == 0
    assert audit["absolute_local_path_leak_count"] == 0
    assert audit["backslash_only_path_leak_count"] == 0
    assert audit["cross_os_path_portability_status"] == "PASS"

    for key in ROW_SHARDS:
        rows = read_jsonl(shard_path(key))
        manifest = read_json(manifest_path_for_shard(shard_path(key)))
        assert manifest["row_count"] == len(rows)
