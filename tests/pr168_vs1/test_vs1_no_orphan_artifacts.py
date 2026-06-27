from __future__ import annotations

from ._helpers import rows


def test_vs1_artifact_and_qku_formula_no_orphan_proofs_pass():
    artifact_ledger = rows("vs1_no_orphan_artifact_ledger.jsonl")
    qku_formula = rows("no_orphan_qku_formula_proof.jsonl")

    assert artifact_ledger
    assert qku_formula
    assert all(row["orphan_artifact_flag"] is False for row in artifact_ledger)
    assert all(row["proof_status"] == "NO_ORPHAN_SELECTED_IDENTITY_ROUTED" for row in qku_formula)
