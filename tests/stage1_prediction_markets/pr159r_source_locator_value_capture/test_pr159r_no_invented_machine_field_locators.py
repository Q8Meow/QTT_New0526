def test_pr159r_no_invented_machine_field_locators(pr159r_artifacts):
    for record in pr159r_artifacts["locator_matrix"]["records"]:
        locator = record["quote_span_or_machine_field_locator_or_null"]
        if locator:
            assert locator.get("machine_field_locator") in (None, "")

