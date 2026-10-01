from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import REPO_ROOT, assert_manifest_is_synchronized, final_summary
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import constants as c


def test_pr165_d3_build_outputs(tmp_path):
    summary = final_summary()
    assert summary["generated_root_report_count"] == 136
    assert summary["generated_schema_count"] == 137
    assert summary["generated_shard_count"] > 0
    assert summary["selected_combination_rows"] > 0
    assert summary["quantum_comparator_rows"] == 559
    for report in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / report).exists()
    assert_manifest_is_synchronized()

    import json
    from copy import deepcopy
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import validator as d3_validator
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_schema_templates_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import SerializationSafetyError, ReasonCode

    root = tmp_path / "d3-count-input"
    target = root / c.GENERATED_DIR / c.REPORT_FILENAMES[0]
    target.parent.mkdir(parents=True)
    name = c.REPORT_FILENAMES[0]
    base = {"roadmap_pr_id":c.PR_ID, "created_by_pr":c.PR_ID, "report_name":name,
            "schema_ref":c.REPORT_SCHEMA_REFS[name], "validator_ref":c.VALIDATOR_REF, "record_count":0, "records":[]}
    original_expect = d3_validator._expect
    original_read_json = d3_validator.read_json
    _schema_refs, schema_bank = _report_schema_templates_v1(c, profile="D3")
    schema_paths = {root / c.SCHEMA_DIR / key: value for key, value in schema_bank.items()}
    schema_reads = []
    report_reads = []
    observed = []

    def read_count_fixture(path):
        # Only schema storage is in memory. Parsing of the owned root, schema
        # comparison/compilation, and validation of its payload remain real.
        if path in schema_paths:
            schema_reads.append(path)
            return deepcopy(schema_paths[path])
        report_reads.append(path)
        return original_read_json(path)

    class CountBoundaryReached(Exception):
        pass

    def observe_count(condition, errors, message):
        original_expect(condition, errors, message)
        if message == f"{name}: record_count mismatch":
            observed.append((condition, tuple(errors)))
            raise CountBoundaryReached

    # Current ordering is schema admission, then the original count expression.
    # Valid-but-wrong integers reach _expect; malformed counts stop earlier.
    for count in (0, 1, False, 0.0, "0", 0.9, None, -1):
        changed = deepcopy(base)
        changed["record_count"] = count
        target.write_text(json.dumps(changed) + "\n", encoding="utf-8")
        observed.clear()
        schema_reads.clear()
        report_reads.clear()
        schema_failure = None
        with patch.object(d3_validator, "_expect", observe_count), patch.object(d3_validator, "read_json", read_count_fixture):
            try:
                d3_validator.validate_repo(root)
            except CountBoundaryReached:
                pass
            except SerializationSafetyError as exc:
                schema_failure = (exc.reason_code, str(exc))
            else:
                raise AssertionError("D3 count boundary was not reached")
        if type(count) is int and count >= 0:
            expected = [(True, ())] if count == 0 else [(False, (f"{name}: record_count mismatch",))]
            expected_failure = None
        else:
            expected = []
            expected_failure = (ReasonCode.SERIALIZATION_UNSAFE,
                                f"{ReasonCode.SERIALIZATION_UNSAFE}: schema report count must be an observed integer")
        assert observed == expected
        assert schema_failure == expected_failure
        assert schema_reads == list(schema_paths) and report_reads == [target]
    missing = deepcopy(base)
    del missing["record_count"]
    target.write_text(json.dumps(missing) + "\n", encoding="utf-8")
    observed.clear()
    schema_reads.clear()
    report_reads.clear()
    schema_failure = None
    with patch.object(d3_validator, "_expect", observe_count), patch.object(d3_validator, "read_json", read_count_fixture):
        try:
            d3_validator.validate_repo(root)
        except SerializationSafetyError as exc:
            schema_failure = (exc.reason_code, str(exc))
        else:
            raise AssertionError("D3 missing-count admission was not rejected")
    assert observed == [] and schema_failure == (ReasonCode.SERIALIZATION_UNSAFE, f"{ReasonCode.SERIALIZATION_UNSAFE}: schema report count must be an observed integer")
    assert schema_reads == list(schema_paths) and report_reads == [target]

    counts = {"generated_root_report_count":len(c.REPORT_FILENAMES), "selected_combination_rows":0,
              "champion_rows":0, "challenger_rows":0, "watch_rows":0, "no_trade_decision_rows":0,
              "paper_candidate_rows":0, "replay_retest_queue_rows":0, "repair_route_rows":0,
              "quantum_comparator_rows":0, "non_live_order_candidate_rows":0, "timeout_ms":3600000}
    summary_base = {**counts, "selected_rows_are_not_live_or_profit_evidence":True}
    failures = []
    d3_validator._validate_summary(summary_base, {}, failures)
    assert failures == []
    for field, expected in counts.items():
        for invalid in (float(expected), str(expected), True, False, None, -1):
            changed = deepcopy(summary_base)
            changed[field] = invalid
            failures = []
            d3_validator._validate_summary(changed, {}, failures)
            message = "final summary timeout_ms must be 3600000" if field == "timeout_ms" else f"final summary {field} mismatch: {invalid} != {expected}"
            assert failures == [message]
