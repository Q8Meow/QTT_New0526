from tools.pr168_gfp2r_config import VALID_MAPPING_CLASSES
from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_qku_formula_mapping_repair_classes_are_valid() -> None:
    mapping_rows = rows("mapping_repair")
    assert mapping_rows
    assert all(row["mapping_class"] in VALID_MAPPING_CLASSES for row in mapping_rows)
