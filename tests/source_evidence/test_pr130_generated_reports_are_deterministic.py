from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_generated_reports_are_deterministic():
    generated = support.generated_report_payloads()
    built = support.artifacts()

    for key, payload in generated.items():
        assert payload == built[key]
