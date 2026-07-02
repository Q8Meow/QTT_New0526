from tests.pr169_dash1.conftest import BASE


def test_no_required_dash1_artifact_uses_weak_hint_filename() -> None:
    assert not list(BASE.rglob("*_hint.jsonl"))
