def test_pr159r_target_field_ledger_for_accepted_packets(pr159r_artifacts):
    ledger_ids = {record["accepted_packet_id"] for record in pr159r_artifacts["ledger"]["records"]}
    assert all(record["accepted_packet_id"] in ledger_ids for record in pr159r_artifacts["accepted"]["records"])

