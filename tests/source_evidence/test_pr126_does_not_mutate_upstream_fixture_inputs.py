from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    FIXTURE_DIR,
    artifacts,
)


def test_pr126_does_not_mutate_upstream_fixture_inputs():
    input_paths = [
        FIXTURE_DIR / "accepted_source_evidence_records.v1.fixture.json",
        FIXTURE_DIR / "connector_semantic_binding_records.v1.fixture.json",
        FIXTURE_DIR / "source_change_snapshot.v1.fixture.json",
    ]
    before = {path: path.read_bytes() for path in input_paths}

    artifacts()

    after = {path: path.read_bytes() for path in input_paths}
    assert after == before
