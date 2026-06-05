from src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun.authority_policy import (
    COMPUTABILITY_ROUTES,
)


def test_qku_computability_invariant(summary, records):
    rows = records("PR162R_QKUComputabilityClassificationMatrix.report.json")
    assert len(rows) >= summary["candidate_packet_v1_ingested_count"]
    for row in rows:
        assert row["qku_id"]
        assert row["candidate_packet_ref"]
        assert row["computability_route"] in COMPUTABILITY_ROUTES
        assert row["upstream_route_refs"]
        assert row["downstream_route_refs"]
