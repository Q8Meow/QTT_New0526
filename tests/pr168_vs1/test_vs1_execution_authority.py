from __future__ import annotations

from ._helpers import report


def test_vs1_execution_authority_is_preview_only_and_denies_forbidden_actions():
    authority = report("vs1_execution_authority_receipt.report.json")

    assert authority["execution_mode"] == "VS1_PREVIEW_ONLY"
    assert authority["pr_id"] == "PR168-VS1"
    assert all(value is False for key, value in authority.items() if key.endswith("_authorized"))
