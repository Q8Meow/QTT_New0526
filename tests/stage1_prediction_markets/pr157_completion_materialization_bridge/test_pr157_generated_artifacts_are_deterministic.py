from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge.validator import validate_existing_artifacts
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import ROOT


def test_pr157_generated_artifacts_are_deterministic(tmp_path, monkeypatch):
    assert validate_existing_artifacts(ROOT).ok

    # Byte currentness is stricter than text/JSON equivalence.
    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import validator as native

    shard = {"shard_path": "currentness-shard.json", "shard_id": "finite", "row_count": 0,
             "first_row_id": None, "last_row_id": None, "records": []}
    expected = SimpleNamespace(pr154_report={"probe": 1}, pr154_registry={"probe": 2},
        atomicrows_report={"probe": 3}, atomicrows_registry={"probe": 4},
        owner_request_packet={"probe": 5}, atomicrows_shards=[shard])
    outputs = [(native.c.PR154_REPORT_PATH, expected.pr154_report),
               (native.c.PR154_REGISTRY_PATH, expected.pr154_registry),
               (native.c.ATOMICROWS_REPORT_PATH, expected.atomicrows_report),
               (native.c.ATOMICROWS_REGISTRY_PATH, expected.atomicrows_registry),
               (native.c.OWNER_REQUEST_PATH, expected.owner_request_packet),
               (shard["shard_path"], {
                   "registry_type": "PR157_ATOMICROWS_4183_COMPLETION_MATERIALIZATION_SHARD",
                   "pr_id": native.c.PR_ID, "semantic_task_id": native.c.SEMANTIC_TASK_ID,
                   "authority_class": native.c.AUTHORITY_CLASS, "shard_id": "finite", "row_count": 0,
                   "first_row_id": None, "last_row_id": None, "records": [],
                   "no_authority_confirmation": dict(native.c.NO_AUTHORITY_CONFIRMATION)})]
    serialized = [(rel, native.json_dump(value)) for rel, value in outputs]
    with monkeypatch.context() as patch:
        patch.setattr(native, "build_artifacts", lambda root: expected)
        for rel, value in serialized:
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value.encode("utf-8"))
        failures = []
        native._validate_currentness(tmp_path, failures)
        assert failures == []
        for rel, value in serialized:
            path = tmp_path / rel
            canonical = value.encode("utf-8")
            for replacement in (b"\r\n", b"\r"):
                changed = canonical.replace(b"\n", replacement)
                assert changed != canonical
                path.write_bytes(changed)
                failures = []
                native._validate_currentness(tmp_path, failures)
                assert len(failures) == 1
                assert "NOT_DETERMINISTIC_CURRENT" in failures[0]
                assert path.read_bytes() == changed
            path.write_bytes(b"\xff")
            with pytest.raises(UnicodeDecodeError):
                native._validate_currentness(tmp_path, [])
            assert path.read_bytes() == b"\xff"
            path.write_bytes(canonical)
        failures = []
        native._validate_currentness(tmp_path, failures)
        assert failures == []
