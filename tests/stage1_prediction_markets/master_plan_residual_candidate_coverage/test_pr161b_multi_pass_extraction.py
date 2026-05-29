from .pr161b_test_support import candidate_records, records


def test_pr161b_multi_pass_extraction_records_pass_ids():
    pass_ids = {pass_id for record in candidate_records() for pass_id in record["extraction_pass_ids"]}
    assert "PASS_1_SECTION_AWARE_EXTRACTION" in pass_ids
    assert "PASS_6_QUANTUM_EXTRACTION" in pass_ids
    assert all(record["extraction_pass_ids_applied"] for record in records("section_search_coverage"))
