from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import ROOT


def test_pr159_no_scattered_hardcoded_blocker_no_authority_vocabulary():
    src_dir = ROOT / "src/qtt/stage1_prediction_markets/pr159_official_source_completion_bridge"
    constants_text = (src_dir / "constants.py").read_text(encoding="utf-8")
    assert "class SourceTargetState" in constants_text
    assert "class AuthorityProfile" in constants_text
    for path in src_dir.glob("*.py"):
        if path.name == "constants.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert '"ACCEPTED_COMPLETED"' not in text
        assert '"PR159_NO_RUNTIME_NO_LIVE_NO_CONNECTOR_BINDING"' not in text

