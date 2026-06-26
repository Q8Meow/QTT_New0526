from __future__ import annotations

from ._helpers import load_report, load_rows


def test_rp5c_no_global_ban_and_no_orphan_proofs_pass() -> None:
    no_global = load_report("PR168_RP5C_NoGlobalBanProof.report.json")
    no_orphan_identity = load_report("PR168_RP5C_NoOrphanIdentityProof.report.json")
    no_orphan_source = load_report("PR168_RP5C_NoOrphanSourceArtifactProof.report.json")
    no_orphan_generated = load_report("PR168_RP5C_NoOrphanGeneratedSurfaceProof.report.json")

    assert no_global["global_formula_ban_count"] == 0
    assert no_global["global_qku_ban_count"] == 0
    assert no_orphan_identity["orphan_identity_count"] == 0
    assert no_orphan_source["orphan_source_artifact_count"] == 0
    assert no_orphan_source["orphan_input_report_count"] == 0
    assert no_orphan_generated["orphan_generated_shard_count"] == 0
    assert len(load_rows("no_global_ban_rows")) == len(load_rows("immutable_qku_formula_library"))
