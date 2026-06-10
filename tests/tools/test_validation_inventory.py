from pathlib import Path

from tools import run_validation_gates as runner
from tools import validation_inventory as inventory


def test_inventory_represents_every_run_validation_gate_command():
    rows = inventory.validation_inventory()
    ids = {entry.validator_id for entry in rows}
    expected_ids = set()
    validation_dir = Path(".tmp/test_inventory")
    pytest_basetemp = validation_dir / "pytest"
    for phase_record in runner.build_phase_manifest(validation_dir, pytest_basetemp):
        phase = phase_record["phase"]
        for command in phase_record["commands"]:
            expected_ids.add(inventory.validator_id_for_command(command, phase))

    assert ids == expected_ids
    assert inventory.validate_inventory(rows) == ()


def test_inventory_classifies_reduced_pr_and_full_validation_behavior():
    rows = inventory.validation_inventory()
    counts = inventory.inventory_counts(rows)

    assert counts["current_validator_count"] == len(rows)
    assert counts["classified_validator_count"] == len(rows)
    assert counts["fast_universal_preflight_count"] >= 7
    assert counts["validators_moved_out_of_default_pr_path_count"] > 0
    assert counts["validators_still_running_on_main_count"] == len(rows)
    assert counts["validators_deleted_count"] == 0
    assert counts["tests_deleted_count"] == 0


def test_inventory_has_pr208_validation_infrastructure_entries():
    by_id = inventory.inventory_by_id()

    for validator_id in (
        "validate_validation_inventory",
        "changed_area_validation_router",
        "cross_platform_path_invariant",
    ):
        entry = by_id[validator_id]
        assert inventory.FAST_UNIVERSAL_PREFLIGHT in entry.validator_class
        assert entry.runs_on_pull_request_default is True
        assert entry.full_validation_required_when_changed is True
        assert entry.cross_platform_sensitive is True


def test_inventory_path_globs_are_posix():
    for entry in inventory.validation_inventory():
        for field_name in (
            "input_globs",
            "output_globs",
            "generated_report_globs",
            "schema_globs",
            "tool_globs",
            "test_globs",
            "workflow_globs",
            "required_when_files_match",
        ):
            for glob in getattr(entry, field_name):
                assert "\\" not in glob, (entry.validator_id, field_name, glob)
