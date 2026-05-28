def test_pr159r_pr157_pr158_pr159_pr160_artifacts_consumed(pr159r_artifacts):
    paths = {item["path"] for item in pr159r_artifacts["master"]["input_consumption_receipt"]}
    assert any("PR157_" in path for path in paths)
    assert any("PR158_" in path for path in paths)
    assert any("PR159_" in path for path in paths)
    assert any("PR160_" in path for path in paths)

