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


def test_inventory_has_pr165_d3_quantum_selection_entry():
    entry = inventory.inventory_by_id()[
        "validate_pr165_d3_quantum_aware_scenario_selection_v3"
    ]
    assert "docs/master_plan/generated/PR165_D3_*.report.json" in entry.output_globs
    assert "src/qtt/stage1_prediction_markets/pr165_d3*/schemas/**" in entry.schema_globs
    assert "tools/validate_pr165_d3_quantum_aware_scenario_selection_v3.py" in entry.tool_globs
    assert "tests/stage1_prediction_markets/pr165_d3*/**" in entry.required_when_files_match


def test_inventory_keeps_pr166_qb_and_qc_scopes_distinct():
    by_id = inventory.inventory_by_id()

    qb = by_id["validate_pr166_qb_bounded_quantum_benchmark"]
    assert "docs/master_plan/generated/PR166_QB_*.report.json" in qb.output_globs
    assert "src/qtt/stage1_prediction_markets/pr166_qb*/schemas/**" in qb.schema_globs

    qc = by_id["validate_pr166_qc_quantum_selected_replay_paper_retest"]
    assert "docs/master_plan/generated/PR166_QC_*.report.json" in qc.output_globs
    assert "src/qtt/stage1_prediction_markets/pr166_qc*/schemas/**" in qc.schema_globs
    assert (
        "tests/stage1_prediction_markets/"
        "pr166_qc*/**"
        in qc.required_when_files_match
    )


def test_inventory_has_pr162e_q_quantum_automapper_entry():
    entry = inventory.inventory_by_id()["validate_pr162e_q_quantum_automapper"]

    assert "docs/master_plan/generated/PR162E_Q_*.report.json" in entry.output_globs
    assert "src/qtt/stage1_prediction_markets/pr162e_q*/schemas/**" in entry.schema_globs
    assert "tools/validate_pr162e_q_quantum_automapper.py" in entry.tool_globs
    assert (
        "tests/stage1_prediction_markets/pr162e_q*/**"
        in entry.required_when_files_match
    )


def test_inventory_knows_every_pytest_shard_phase_job():
    for phase in runner.PYTEST_SHARD_PHASES:
        assert inventory.phase_job_id(phase) == phase.replace("-", "_")

    phase_jobs = {
        inventory.phase_job_id(phase)
        for phase in (
            runner.FAST_PREFLIGHT_PHASE,
            runner.DETERMINISTIC_VALIDATORS_PHASE,
            *runner.PYTEST_SHARD_PHASES,
            runner.POST_VALIDATION_PHASE,
        )
    }
    assert {
        "pytest_shard_1",
        "pytest_shard_2",
        "pytest_shard_3",
        "pytest_shard_4",
        "pytest_shard_5",
        "pytest_shard_6",
        "pytest_shard_7",
        "pytest_shard_8",
    }.issubset(phase_jobs)


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
