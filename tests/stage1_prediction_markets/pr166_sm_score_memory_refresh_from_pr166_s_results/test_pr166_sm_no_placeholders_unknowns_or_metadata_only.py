from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.enums import (
    FORBIDDEN_STATUS_VALUES,
)


def _string_values(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(_string_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_string_values(item))
        return values
    return []


def test_pr166_sm_has_no_placeholder_unknown_or_metadata_only_rows(pr166_sm_summary):
    assert pr166_sm_summary["metadata_only_rows"] == 0
    assert pr166_sm_summary["placeholder_rows"] == 0
    assert pr166_sm_summary["unknown_status_rows"] == 0
    assert pr166_sm_summary["generic_blocker_rows"] == 0


def test_pr166_sm_rows_do_not_emit_forbidden_status_values(pr166_sm_records):
    allowed_audit_fields = {
        "forbidden_status_values_scanned_in_explicit_audit_field",
    }
    for filename, rows in pr166_sm_records.items():
        for row in rows[:250]:
            checked = {k: v for k, v in row.items() if k not in allowed_audit_fields}
            assert not (set(_string_values(checked)) & FORBIDDEN_STATUS_VALUES), filename
