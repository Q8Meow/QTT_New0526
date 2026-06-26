from __future__ import annotations

from ._helpers import load_rows


def test_rp5c_immutable_qku_formula_libraries_exist_and_link_sources() -> None:
    identities = load_rows("immutable_qku_formula_library")
    qkus = load_rows("immutable_qku_library")
    formulas = load_rows("immutable_formula_library")
    source_ids = {row["source_artifact_row_id"] for row in load_rows("source_artifact_consumption_ledger")}

    assert identities
    assert qkus
    assert formulas
    for row in identities[:1000]:
        assert row["source_artifact_row_id"] in source_ids
        assert row["immutable_original_preserved_flag"] is True
        assert row["global_ban_flag"] is False
        assert row["mutation_allowed_flag"] is False
        assert row["identity_authority_class"] != "SOURCE_TRUTH"
    assert all(row["source_artifact_row_id"] in source_ids for row in identities)
