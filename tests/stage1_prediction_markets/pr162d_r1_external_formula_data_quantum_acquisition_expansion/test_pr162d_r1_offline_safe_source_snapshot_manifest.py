from __future__ import annotations


def test_pr162d_r1_offline_safe_source_snapshot_manifest(records):
    snapshots = records("PR162D_R1_OfflineSafeSourceSnapshotManifest.report.json")
    assert snapshots
    assert all(record["stored_private_state_flag"] is False for record in snapshots)
    assert all(record["stored_secret_flag"] is False for record in snapshots)
    assert all(record["ci_network_required_flag"] is False for record in snapshots)
