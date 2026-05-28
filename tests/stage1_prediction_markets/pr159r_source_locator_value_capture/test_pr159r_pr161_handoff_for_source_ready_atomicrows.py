def test_pr159r_pr161_handoff_for_source_ready_atomicrows(pr159r_artifacts):
    ready = [record for record in pr159r_artifacts["atomic_completion"]["records"] if record["source_ready_flag"]]
    assert pr159r_artifacts["pr161_handoff"]["record_count"] == len(ready)

