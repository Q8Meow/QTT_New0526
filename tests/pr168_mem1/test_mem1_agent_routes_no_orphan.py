from .test_support import read_json, read_jsonl


def test_agent_routes_and_no_orphan_proof_exist() -> None:
    assert read_jsonl("agent_alias_map.jsonl")
    assert read_jsonl("agent_route.jsonl")
    assert read_json("agent_route.report.json")["pr165_d2_consumed_flag"] is True
    assert read_json("no_orphan.report.json")["no_orphan_pass_flag"] is True
    assert read_jsonl("orph_art.jsonl")[0]["orphan_artifact_count"] == 0
    assert read_jsonl("orph_qku.jsonl")[0]["orphan_qku_count"] == 0
