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


def test_inventory_has_qtt_authority_reason_code_registry_entry():
    entry = inventory.inventory_by_id()["validate_qtt_authority_reason_code_registry"]

    assert entry.owner_pr_or_feature == "PR168-RP"
    assert entry.owner_domain == "QTT authority reason code registry"
    assert entry.full_validation_required_when_changed is True
    assert "tools/qtt_authority_reason_code_registry.py" in entry.required_when_files_match
    assert "tools/validate_qtt_authority_reason_code_registry.py" in entry.tool_globs
    assert (
        "tests/tools/test_qtt_authority_reason_code_registry.py"
        in entry.required_when_files_match
    )


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


def test_inventory_has_pr162e_plugin_framework_entries():
    entries = inventory.inventory_by_id()
    entry = entries["validate_pr162e_plugin_framework"]

    assert "docs/master_plan/generated/PR162E_*.report.json" in entry.output_globs
    assert "src/qtt/stage1_prediction_markets/pr162e*/schemas/**" in entry.schema_globs
    assert "src/qtt/plugins/**" in entry.required_when_files_match
    assert "tests/pr162e/**" in entry.required_when_files_match
    assert "tools/validate_pr162e_plugin_framework.py" in entry.tool_globs

    assert entries["validate_pr162e_negative_repair_factory"].owner_pr_or_feature == "PR162E"
    assert entries["validate_pr162e_no_orphan_lineage"].owner_pr_or_feature == "PR162E"


def test_inventory_has_pr167_open_trade_simulator_entry():
    entry = inventory.inventory_by_id()["validate_pr167_open_trade_simulator_integration"]

    assert "docs/master_plan/generated/PR167_*.report.json" in entry.output_globs
    assert "src/qtt/stage1_prediction_markets/pr167*/schemas/**" in entry.schema_globs
    assert "tools/validate_pr167_open_trade_simulator_integration.py" in entry.tool_globs
    assert (
        "tests/stage1_prediction_markets/pr167*/**"
        in entry.required_when_files_match
    )


def test_inventory_has_pr168_rank_entry():
    entry = inventory.inventory_by_id()["validate_pr168_rank_input_consumption"]

    assert "docs/master_plan/generated/PR168_RANK_*.report.json" in entry.output_globs
    assert "docs/master_plan/generated/pr168_rank*/**" in entry.output_globs
    assert "tools/validate_pr168_rank_input_consumption.py" in entry.tool_globs
    assert "tests/pr168_rank/**" in entry.required_when_files_match


def test_inventory_has_pr168_data1_entry():
    entry = inventory.inventory_by_id()["validate_pr168_data1_public_market_data_snapshots"]

    assert entry.owner_pr_or_feature == "PR168_DATA1"
    assert "docs/master_plan/generated/PR168_DATA1_*.report.json" in entry.output_globs
    assert "docs/master_plan/generated/pr168_data1*/**" in entry.output_globs
    assert "tools/validate_pr168_data1_public_market_data_snapshots.py" in entry.tool_globs
    assert "tests/pr168_data1/**" in entry.required_when_files_match


def test_inventory_has_pr168_data1a_entry():
    entry = inventory.inventory_by_id()["validate_pr168_data1a_focused_audit"]

    assert entry.owner_pr_or_feature == "PR168_DATA1A"
    assert "docs/master_plan/generated/PR168_DATA1A_*.report.json" in entry.output_globs
    assert "docs/master_plan/generated/pr168_data1a*/**" in entry.output_globs
    assert "tools/validate_pr168_data1a_focused_audit.py" in entry.tool_globs
    assert "tests/pr168_data1a/**" in entry.required_when_files_match


def test_inventory_has_pr168_gfp2r_entry():
    entry = inventory.inventory_by_id()[
        "validate_pr168_gfp2r_data1a_gated_candidate_recompute"
    ]

    assert entry.owner_pr_or_feature == "PR168_GFP2R"
    assert "docs/master_plan/generated/PR168_GFP2R_*.report.json" in entry.output_globs
    assert "docs/master_plan/generated/pr168_gfp2r*/**" in entry.output_globs
    assert (
        "tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py"
        in entry.tool_globs
    )
    assert "tests/pr168_gfp2r/**" in entry.required_when_files_match


def test_inventory_has_pr168_rp2_entry():
    entry = inventory.inventory_by_id()["validate_pr168_rp2_map2"]

    assert entry.owner_pr_or_feature == "PR168_RP2"
    assert "docs/master_plan/generated/PR168_RP2_*.report.json" in entry.output_globs
    assert "docs/master_plan/generated/rp2p/**" in entry.output_globs
    assert "tools/validate_pr168_rp2_map2.py" in entry.tool_globs
    assert "tests/pr168_rp2/**" in entry.required_when_files_match


def test_inventory_has_pr168_map3_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_map3"]
    validate_entry = entries["validate_pr168_map3"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_MAP3"
        assert "docs/master_plan/generated/PR168_MAP3_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/map3/**" in entry.output_globs
        assert "tests/pr168_map3/**" in entry.required_when_files_match

    assert "tools/build_pr168_map3.py" in build_entry.tool_globs
    assert "tools/validate_pr168_map3.py" in validate_entry.tool_globs


def test_inventory_has_pr168_rp3_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp3"]
    validate_entry = entries["validate_pr168_rp3"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP3"
        assert "docs/master_plan/generated/PR168_RP3_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/rp3/**" in entry.output_globs
        assert "tests/pr168_rp3/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp3.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp3.py" in validate_entry.tool_globs


def test_inventory_has_pr168_rank3_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rank3"]
    validate_entry = entries["validate_pr168_rank3"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RANK3"
        assert "docs/master_plan/generated/PR168_RANK3_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/rank3/**" in entry.output_globs
        assert "tests/pr168_rank3/**" in entry.required_when_files_match

    assert "tools/build_pr168_rank3.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rank3.py" in validate_entry.tool_globs


def test_inventory_has_pr168_rp5a_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5a_legacy_semantic_audit"]
    validate_entry = entries["validate_pr168_rp5a_legacy_semantic_audit"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5A"
        assert "docs/master_plan/generated/PR168_RP5A_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/rp5a/**" in entry.output_globs
        assert "tests/pr168_rp5a/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp5a_legacy_semantic_audit.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp5a_legacy_semantic_audit.py" in validate_entry.tool_globs


def test_inventory_has_pr168_rp5b_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5b_active_registry_safe_cleanup"]
    validate_entry = entries["validate_pr168_rp5b_active_registry_safe_cleanup"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5B"
        assert "docs/master_plan/generated/PR168_RP5B_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/rp5b/**" in entry.output_globs
        assert "tests/pr168_rp5b/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp5b_active_registry_safe_cleanup.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py" in validate_entry.tool_globs


def test_inventory_has_pr168_rp5c_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5c_immutable_qku_formula_library"]
    validate_entry = entries["validate_pr168_rp5c_immutable_qku_formula_library"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5C"
        assert "docs/master_plan/generated/PR168_RP5C_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/rp5c/**" in entry.output_globs
        assert "tests/pr168_rp5c/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp5c_immutable_qku_formula_library.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp5c_immutable_qku_formula_library.py" in validate_entry.tool_globs


def test_inventory_has_pr168_vs1_entries():
    entries = inventory.inventory_by_id()
    run_entry = entries["run_pr168_vs1_trading_intelligence_slice"]
    validate_entry = entries["validate_pr168_vs1_trading_intelligence_slice"]

    for entry in (run_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_VS1"
        assert "docs/master_plan/generated/PR168_VS1_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/pr168_vs1/**" in entry.output_globs
        assert "tests/pr168_vs1/**" in entry.required_when_files_match

    assert "tools/run_pr168_vs1_trading_intelligence_slice.py" in run_entry.tool_globs
    assert (
        "tools/validate_pr168_vs1_trading_intelligence_slice.py"
        in validate_entry.tool_globs
    )


def test_inventory_has_pr168_rp5d_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5d_replay_paper_executability_tiers"]
    validate_entry = entries["validate_pr168_rp5d_replay_paper_executability_tiers"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5D"
        assert "docs/master_plan/generated/PR168_RP5D_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/pr168_rp5d/**" in entry.output_globs
        assert "tests/pr168_rp5d/**" in entry.required_when_files_match

    assert (
        "tools/build_pr168_rp5d_replay_paper_executability_tiers.py"
        in build_entry.tool_globs
    )
    assert (
        "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py"
        in validate_entry.tool_globs
    )


def test_inventory_has_pr168_rp5e_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5e_stack_gen"]
    validate_entry = entries["validate_pr168_rp5e_stack_gen"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5E"
        assert "docs/master_plan/generated/PR168_RP5E_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/pr168_rp5e/**" in entry.output_globs
        assert "tests/pr168_rp5e/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp5e_stack_gen.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp5e_stack_gen.py" in validate_entry.tool_globs


def test_inventory_knows_every_pytest_shard_phase_job():
    for phase in runner.ORDERED_PHASES:
        assert inventory.phase_job_id(phase) == inventory.VALIDATION_MATRIX_JOB_ID

    phase_jobs = {
        inventory.phase_job_id(phase)
        for phase in (
            runner.FAST_PREFLIGHT_PHASE,
            runner.DETERMINISTIC_VALIDATORS_PHASE,
            *runner.PYTEST_SHARD_PHASES,
            runner.POST_VALIDATION_PHASE,
        )
    }
    assert phase_jobs == {inventory.VALIDATION_MATRIX_JOB_ID}


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
