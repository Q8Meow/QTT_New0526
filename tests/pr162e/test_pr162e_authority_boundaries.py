from tests.pr162e.helpers import forbidden_count_fields, load_report, plugin_rows


def test_authority_boundaries_have_zero_forbidden_counts_and_flags():
    audit = load_report("PR162E_AuthorityBoundaryAudit.report.json")["records"][0]
    assert audit["forbidden_authority_total"] == 0
    assert all(audit[field] == 0 for field in forbidden_count_fields())
    assert all(row["live_order_authority_flag"] is False for row in plugin_rows())
