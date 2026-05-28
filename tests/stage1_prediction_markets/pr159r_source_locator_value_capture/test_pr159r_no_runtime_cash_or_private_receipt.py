def test_pr159r_no_runtime_cash_or_private_receipt(pr159r_artifacts):
    no_authority = pr159r_artifacts["master"]["no_authority_confirmation"]
    assert no_authority["runtime_cash_receipt_created"] is False
    assert no_authority["private_state_fetch_created"] is False

