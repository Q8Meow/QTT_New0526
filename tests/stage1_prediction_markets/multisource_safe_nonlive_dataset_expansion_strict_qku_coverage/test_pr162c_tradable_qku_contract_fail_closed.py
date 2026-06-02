from .test_support import records


def test_pr162c_tradable_qku_contract_fail_closed():
    audits = records("PR162C_TradableQKUCandidateContractAudit.report.json")

    assert len(audits) == 9360
    assert not any(record["pr162r_ready_flag"] for record in audits)
    assert all(
        record["tradable_qku_candidate_contract_status"]
        == "FAIL_CLOSED_PENDING_STRICT_DATA_AND_OWNER_GATES"
        for record in audits
    )
