from tests.pr162e.helpers import records


def test_external_candidates_are_provisional_and_mapped():
    rows = records("PR162E_ExternalCandidateIntake.report.json")
    assert len(rows) == 12
    assert all(row["source_truth_accepted"] is False for row in rows)
    assert all(row["plugin_family_mapping"] for row in rows)
