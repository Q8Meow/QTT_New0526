from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.artifact_names import (
    build_artifact_name_entries,
)
from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.models import (
    all_artifact_filenames,
)
from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.path_safety import (
    path_safety_failures,
)

from ._helpers import read_json


def test_short_generated_artifact_names_are_windows_safe() -> None:
    filenames = all_artifact_filenames()
    assert path_safety_failures(filenames) == []
    assert all(len(name) <= 64 for name in filenames)


def test_artifact_registry_maps_short_names_to_logical_names() -> None:
    registry = read_json("art_reg.json")
    entries = registry["artifacts"]
    assert entries == build_artifact_name_entries()
    assert {entry["short_file"] for entry in entries} == set(all_artifact_filenames())
