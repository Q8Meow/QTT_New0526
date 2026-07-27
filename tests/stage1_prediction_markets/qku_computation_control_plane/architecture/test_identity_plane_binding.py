from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    OwnerAdapterError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.identity_adapter import (
    IdentityViewV1,
    RP5CIdentityAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    CertifiedMathIdentityRefV1,
    RP5CCanonicalIdentityBindingV1,
)


def test_identity_resolution_binds_to_rp5c_lineage() -> None:
    root = Path(__file__).resolve().parents[4]
    view = RP5CIdentityAdapterV1(root).get_formula("FORMULA_QKU")
    assert view.identity_row_id == "RP5C_IDENTITY_00000001"
    assert view.formula_id == "FORMULA_QKU"
    assert view.source_owner == "RP5C_IDENTITY_LIBRARY"
    assert view.library_version == "ImmutableQKUFormulaLibraryV1"
    binding = RP5CCanonicalIdentityBindingV1((view,))
    assert binding.canonical_formula_ids == ("FORMULA_QKU",)
    assert binding.canonical_qku_ids == ()


def test_math_registry_references_are_not_synthetic_qkus() -> None:
    identity = CertifiedMathIdentityRefV1("MATH-01")
    assert identity.math_id == "MATH-01"
    assert identity.registry_owner == "QKUComputationControlPlaneV1"
    assert not hasattr(identity, "qku_id")
    with pytest.raises(ContractValidationError):
        CertifiedMathIdentityRefV1("QKU-FAKE")


def test_rp5c_identity_owner_and_lineage_fail_closed() -> None:
    with pytest.raises(OwnerAdapterError):
        IdentityViewV1(
            identity_row_id="fake",
            qku_id="QKU-FAKE",
            formula_id="",
            qku_family="fake",
            formula_family="",
            ontology_category="fake",
            library_version="fake",
            source_owner="SECOND_IDENTITY_PLANE",
        )
