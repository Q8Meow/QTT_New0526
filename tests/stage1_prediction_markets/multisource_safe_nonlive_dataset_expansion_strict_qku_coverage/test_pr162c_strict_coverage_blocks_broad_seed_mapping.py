from .test_support import records, report


def test_pr162c_strict_coverage_blocks_broad_seed_mapping():
    summary = report("PR162C_FinalSummary.report.json")
    proofs = records("PR162C_StrictQKUCoverageProofMatrix.report.json")

    assert summary["pr162a_repaired_qkus_mapped_to_run_capable_datasets"] == 0
    assert summary["pr162a_repaired_pr162_adapter_rerun_ready_count"] == 0
    assert summary["strict_run_capable_qku_count"] == 0
    assert not any(record["pr162r_ready_flag"] for record in proofs)
    assert {record["blocker_code"] for record in proofs} == {"BLOCKED_REQUIRED_FIELDS_MISSING"}
