from tools.pr168_data1_validator import run_validation


def test_pr168_data1_historical_full_book_availability_audit_exists() -> None:
    run_validation("historical_full_book_availability_audit_exists")
