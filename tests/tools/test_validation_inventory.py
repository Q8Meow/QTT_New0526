from fnmatch import fnmatchcase
from pathlib import Path

from tools import changed_area_validation_router as router
from tools import run_validation_gates as runner
from tools import validation_inventory as inventory


EXPECTED_ST12C_QKU_VALIDATOR_IDS = frozenset(
    {
        "validate_qku_computation_control_plane_accounting",
        "validate_qku_computation_control_plane_execution",
        "independent_validate_qku_computation_control_plane_accounting",
        "independent_validate_qku_computation_control_plane_execution",
    }
)
EXPECTED_ST12E_QKU_VALIDATOR_IDS = frozenset(
    {
        "independent_validate_qku_computation_control_plane_agent",
        "independent_validate_qku_computation_control_plane_llm",
        "independent_validate_qku_computation_control_plane_security",
        "validate_qku_computation_control_plane_agent",
        "validate_qku_computation_control_plane_llm",
        "validate_qku_computation_control_plane_security",
    }
)
EXPECTED_ST12D_QKU_VALIDATOR_IDS = frozenset(
    {
        "independent_validate_qku_computation_control_plane_d",
        "independent_validate_qku_computation_control_plane_execution",
        "independent_validate_qku_computation_control_plane_latency",
        "independent_validate_qku_computation_control_plane_security",
        "validate_qku_computation_control_plane_d",
        "validate_qku_computation_control_plane_execution",
        "validate_qku_computation_control_plane_latency",
        "validate_qku_computation_control_plane_security",
    }
)
EXPECTED_ST12F_QKU_VALIDATOR_IDS = frozenset(
    {
        "independent_validate_qku_computation_control_plane",
        "independent_validate_qku_computation_control_plane_architecture",
        "independent_validate_qku_computation_control_plane_d",
        "independent_validate_qku_computation_control_plane_execution",
        "independent_validate_qku_computation_control_plane_llm",
        "independent_validate_qku_computation_control_plane_model_risk",
        "independent_validate_qku_computation_control_plane_operations",
        "independent_validate_qku_computation_control_plane_quantum",
        "independent_validate_qku_computation_control_plane_source",
        "validate_qku_computation_control_plane_llm",
        "validate_qku_computation_control_plane_model_risk",
        "validate_qku_computation_control_plane_quantum",
    }
)
EXPECTED_ST12G_QKU_VALIDATOR_IDS = frozenset(
    {
        "validate_qku_computation_control_plane_g",
        "independent_validate_qku_computation_control_plane_g",
    }
)
EXPECTED_ST12G_OWNER_VALIDATOR_IDS = frozenset(
    {
        "validate_pr169_readiness1",
        "validate_pr169_pretrade1",
        "validate_pr169_agent_orch1",
        "validate_pr169_svc1",
        "validate_pr169_dash1_owner_dashboard",
        "validate_pr169_dash1_owner_dashboard_ui",
    }
)


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


def test_inventory_has_centralized_qku_validation_entries():
    entries = inventory.inventory_by_id()
    expected = {
        "independent_validate_qku_computation_control_plane",
        "independent_validate_qku_computation_control_plane_latency",
        "independent_validate_qku_computation_control_plane_model_risk",
        "validate_qku_computation_control_plane_architecture",
        "validate_qku_computation_control_plane_operations",
        "validate_qku_computation_control_plane_quantum",
        "validate_qku_computation_control_plane_security",
        "validate_qku_computation_control_plane_source",
        *EXPECTED_ST12C_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12D_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12E_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12F_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12G_QKU_VALIDATOR_IDS,
    }
    assert inventory.ST12C_QKU_VALIDATOR_IDS == EXPECTED_ST12C_QKU_VALIDATOR_IDS
    assert inventory.ST12E_QKU_VALIDATOR_IDS == EXPECTED_ST12E_QKU_VALIDATOR_IDS
    assert inventory.ST12D_QKU_VALIDATOR_IDS == EXPECTED_ST12D_QKU_VALIDATOR_IDS
    assert inventory.ST12F_QKU_VALIDATOR_IDS == EXPECTED_ST12F_QKU_VALIDATOR_IDS
    assert inventory.ST12G_QKU_VALIDATOR_IDS == EXPECTED_ST12G_QKU_VALIDATOR_IDS
    assert inventory.ST12D_EXCLUSIVE_QKU_VALIDATOR_IDS == {
        "independent_validate_qku_computation_control_plane_d",
        "validate_qku_computation_control_plane_d",
        "validate_qku_computation_control_plane_latency",
    }
    assert inventory.ST12E_EXCLUSIVE_QKU_VALIDATOR_IDS == (
        EXPECTED_ST12E_QKU_VALIDATOR_IDS
        - {
            "independent_validate_qku_computation_control_plane_security",
            "validate_qku_computation_control_plane_security",
        }
    )
    assert inventory.QKU_ALLOWED_EXACT_PATHS == frozenset(
        (
            *inventory.ST12A_ALLOWED_EXACT_PATHS,
            *inventory.ST12B_ALLOWED_EXACT_PATHS,
            *inventory.ST12C_ALLOWED_EXACT_PATHS,
            *inventory.ST12D_ALLOWED_EXACT_PATHS,
            *inventory.ST12E_ALLOWED_EXACT_PATHS,
            *inventory.ST12F_ALLOWED_EXACT_PATHS,
            *inventory.ST12G_ALLOWED_EXACT_PATHS,
        )
    )
    assert expected <= set(entries)
    for validator_id in expected:
        entry = entries[validator_id]
        if validator_id in EXPECTED_ST12G_QKU_VALIDATOR_IDS:
            expected_owner = "ST12-TRANCHE-G"
        elif validator_id in EXPECTED_ST12F_QKU_VALIDATOR_IDS:
            expected_owner = "ST12-TRANCHE-F"
        elif validator_id in inventory.ST12D_EXCLUSIVE_QKU_VALIDATOR_IDS:
            expected_owner = "ST12-TRANCHE-D"
        elif validator_id in inventory.ST12E_EXCLUSIVE_QKU_VALIDATOR_IDS:
            expected_owner = "ST12-TRANCHE-E"
        elif validator_id in EXPECTED_ST12C_QKU_VALIDATOR_IDS:
            expected_owner = "ST12-TRANCHE-C"
        elif validator_id.endswith(("_latency", "_model_risk")):
            expected_owner = "ST12-TRANCHE-B"
        else:
            expected_owner = "ST12-TRANCHE-A"
        assert entry.owner_pr_or_feature == expected_owner
        assert entry.owner_domain == "QKU computation control plane"
        assert inventory.QKU_ALLOWED_EXACT_PATHS <= set(
            entry.required_when_files_match
        )
        assert not any(
            "*" in path for path in entry.required_when_files_match
        )


def test_shared_validator_support_tool_ownership_is_exact_and_routes():
    shared_path = "tools/qku_independent_math_row_receipt.py"
    expected_owners = frozenset(
        {
            "independent_validate_qku_computation_control_plane",
            "independent_validate_qku_computation_control_plane_accounting",
            "independent_validate_qku_computation_control_plane_execution",
            "independent_validate_qku_computation_control_plane_d",
            "independent_validate_qku_computation_control_plane_model_risk",
            "independent_validate_qku_computation_control_plane_quantum",
            "pytest_shard_1_tools_fail_closed",
        }
    )
    entries = inventory.validation_inventory()
    entries_by_id = {entry.validator_id: entry for entry in entries}
    assert inventory.SHARED_VALIDATOR_SUPPORT_TOOL_OWNERS == {
        shared_path: expected_owners
    }
    assert expected_owners <= entries_by_id.keys()

    pytest_phase = next(
        phase_record
        for phase_record in runner.build_phase_manifest(
            Path(".tmp/test-shared-support-inventory"),
            Path(".tmp/test-shared-support-inventory/pytest"),
        )
        if phase_record["phase"] == "pytest-shard-1"
    )
    tools_fail_closed_command = next(
        command
        for command in pytest_phase["commands"]
        if "tests/tools" in command and "tests/fail_closed" in command
    )
    assert inventory.validator_id_for_command(
        tools_fail_closed_command,
        "pytest-shard-1",
    ) == "pytest_shard_1_tools_fail_closed"

    matching_ids = frozenset(
        entry.validator_id for entry in inventory.entries_matching_path(shared_path)
    )
    assert matching_ids == expected_owners
    for validator_id, entry in entries_by_id.items():
        if validator_id in expected_owners:
            assert shared_path in entry.tool_globs
        else:
            assert shared_path not in entry.tool_globs
        assert all(
            tool_glob == shared_path
            for tool_glob in entry.tool_globs
            if fnmatchcase(shared_path, tool_glob)
        )
    assert shared_path not in inventory.QKU_ALLOWED_EXACT_PATHS
    assert not any(
        fnmatchcase(shared_path, glob)
        for glob in inventory.VALIDATION_INFRASTRUCTURE_GLOBS
    )

    result = router.build_router_result(
        router.RouterInput(
            repo_root=Path(__file__).resolve().parents[2],
            changed_files=(shared_path,),
            workflow_event_name="pull_request",
            is_pull_request=True,
            current_branch="repair/st12-inherited-math-row-receipt-closure",
        )
    )
    assert result.unknown_files == ()
    assert result.fail_closed_reasons == ()
    assert result.classified_files[shared_path] == tuple(sorted(expected_owners))
    assert expected_owners <= set(result.required_validators)

    registered_commands = {
        (phase_record["phase"], inventory.canonical_command(command))
        for phase_record in runner.build_phase_manifest(
            Path(".tmp/qtt_validation_inventory"),
            Path(".tmp/qtt_validation_inventory/pytest"),
        )
        for command in phase_record["commands"]
    }
    assert len(entries) == 449
    assert {(entry.phase, entry.command) for entry in entries} == registered_commands
    assert {entry.phase for entry in entries} == set(runner.ORDERED_PHASES)


def test_qku_paths_route_to_primary_and_independent_validation():
    matching_ids = {
        entry.validator_id
        for entry in inventory.entries_matching_path(
            "src/qtt/stage1_prediction_markets/"
            "qku_computation_control_plane/implementation_registry.py"
        )
    }
    assert {
        "independent_validate_qku_computation_control_plane",
        "independent_validate_qku_computation_control_plane_latency",
        "independent_validate_qku_computation_control_plane_model_risk",
        "validate_qku_computation_control_plane_architecture",
        "validate_qku_computation_control_plane_operations",
        "validate_qku_computation_control_plane_quantum",
        "validate_qku_computation_control_plane_security",
        "validate_qku_computation_control_plane_source",
        *EXPECTED_ST12C_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12D_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12E_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12F_QKU_VALIDATOR_IDS,
        *EXPECTED_ST12G_QKU_VALIDATOR_IDS,
    } <= matching_ids


def test_st12g_exact_commands_and_owner_validators_are_registered() -> None:
    expected_commands = (
        "python tools/validate_qku_computation_control_plane.py --domain g",
        "python tools/independent_validate_qku_computation_control_plane_g.py",
        "python tools/validate_validation_inventory.py",
        "python -m pytest tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_contract_matrix.py -q",
        "python -m pytest tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_consumer_integration_matrix.py -q",
        "python tools/run_validation_gates.py --phase all --validation-mode full",
    )
    assert inventory.ST12G_EXACT_VALIDATION_COMMANDS == expected_commands
    assert inventory.ST12G_OWNER_VALIDATOR_IDS == EXPECTED_ST12G_OWNER_VALIDATOR_IDS
    assert inventory.ST12G_REQUIRED_VALIDATOR_IDS == frozenset(
        (*EXPECTED_ST12G_QKU_VALIDATOR_IDS, *EXPECTED_ST12G_OWNER_VALIDATOR_IDS)
    )
    assert inventory.ST12G_REQUIRED_VALIDATOR_IDS <= inventory.inventory_by_id().keys()


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


def test_inventory_has_pr169_dash1_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr169_dash1_owner_dashboard"]
    validate_entry = entries["validate_pr169_dash1_owner_dashboard"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR169_DASH1"
        assert "docs/master_plan/generated/pr169_dash1*/**" in entry.output_globs
        assert "src/qtt/dashboard/**" in entry.required_when_files_match
        assert "tests/pr169_dash1/**" in entry.required_when_files_match

    assert "tools/build_pr169_dash1_owner_dashboard.py" in build_entry.tool_globs
    assert "tools/validate_pr169_dash1_owner_dashboard.py" in validate_entry.tool_globs


def test_pr169_dash1_paths_match_only_dash1_validators():
    paths = (
        "docs/master_plan/generated/pr169_dash1/owner_dashboard_surface_registry.jsonl",
        "src/qtt/dashboard/owner_surface_resolver.py",
        "tests/pr169_dash1/test_dash1_chart_contracts.py",
        "tools/validate_pr169_dash1_owner_dashboard.py",
    )

    for path in paths:
        matching_ids = {entry.validator_id for entry in inventory.entries_matching_path(path)}
        assert "build_pr169_dash1_owner_dashboard" in matching_ids
        assert "validate_pr169_dash1_owner_dashboard" in matching_ids
        assert "validate_pr168_mem1_condition_scoped_memory" not in matching_ids
        assert "validate_pr168_vs2_paper_intent_candidates" not in matching_ids


def test_inventory_has_pr169_readiness1_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr169_readiness1"]
    validate_entry = entries["validate_pr169_readiness1"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR169_READINESS1"
        assert "docs/master_plan/generated/pr169_readiness1/**" in entry.output_globs
        assert "src/qtt/readiness/**" in entry.required_when_files_match
        assert "tests/pr169_readiness1/**" in entry.required_when_files_match

    assert "tools/build_pr169_readiness1.py" in build_entry.tool_globs
    assert "tools/validate_pr169_readiness1.py" in validate_entry.tool_globs


def test_pr169_readiness1_paths_match_only_readiness1_validators():
    paths = (
        "docs/master_plan/generated/pr169_readiness1/agent_readiness_registry.jsonl",
        "src/qtt/readiness/pr169_readiness1_resolvers.py",
        "tests/pr169_readiness1/test_pr169_readiness1.py",
        "tools/validate_pr169_readiness1.py",
    )

    for path in paths:
        matching_ids = {entry.validator_id for entry in inventory.entries_matching_path(path)}
        assert "build_pr169_readiness1" in matching_ids
        assert "validate_pr169_readiness1" in matching_ids
        assert "build_pr169_dash1_owner_dashboard" not in matching_ids
        assert "validate_pr169_dash1_owner_dashboard" not in matching_ids
        assert "validate_pr168_mem1_condition_scoped_memory" not in matching_ids


def test_inventory_has_pr169_svc1_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr169_svc1"]
    validate_entry = entries["validate_pr169_svc1"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR169_SVC1"
        assert "docs/master_plan/generated/pr169_svc1/**" in entry.output_globs
        assert "src/qtt/service/**" in entry.required_when_files_match
        assert "tests/pr169_svc1/**" in entry.required_when_files_match
        assert (
            "src/qtt/stage1_prediction_markets/"
            "pr168_vs1_trading_intelligence/runner.py"
        ) in entry.required_when_files_match
        assert "tools/pr168_rp5c_config.py" in entry.required_when_files_match

    assert "tools/build_pr169_svc1.py" in build_entry.tool_globs
    assert "tools/validate_pr169_svc1.py" in validate_entry.tool_globs


def test_pr169_svc1_paths_match_svc1_validators():
    paths = (
        "docs/master_plan/generated/pr169_svc1/service_registry.jsonl",
        "src/qtt/service/pr169_svc1_resolvers.py",
        "tests/pr169_svc1/test_pr169_svc1.py",
        "tools/validate_pr169_svc1.py",
        "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/runner.py",
        "tools/pr168_rp5c_config.py",
    )

    for path in paths:
        matching_ids = {entry.validator_id for entry in inventory.entries_matching_path(path)}
        assert "build_pr169_svc1" in matching_ids
        assert "validate_pr169_svc1" in matching_ids


def test_inventory_has_pr169_agent_orch1_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr169_agent_orch1"]
    validate_entry = entries["validate_pr169_agent_orch1"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR169_AGENT_ORCH1"
        assert "docs/master_plan/generated/pr169_agent_orch1/**" in entry.output_globs
        assert "src/qtt/agents/**" in entry.required_when_files_match
        assert "tests/pr169_agent_orch1/**" in entry.required_when_files_match

    assert "tools/build_pr169_agent_orch1.py" in build_entry.tool_globs
    assert "tools/validate_pr169_agent_orch1.py" in validate_entry.tool_globs


def test_pr169_agent_orch1_paths_match_agent_orch1_validators():
    paths = (
        "docs/master_plan/generated/pr169_agent_orch1/registry.jsonl",
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "tests/pr169_agent_orch1/test_registry_projection_integrity.py",
        "tools/validate_pr169_agent_orch1.py",
    )

    for path in paths:
        matching_ids = {entry.validator_id for entry in inventory.entries_matching_path(path)}
        assert "build_pr169_agent_orch1" in matching_ids
        assert "validate_pr169_agent_orch1" in matching_ids


def test_inventory_has_pr169_val1_entry():
    entry = inventory.inventory_by_id()["validate_pr169_val1"]

    assert entry.phase == "deterministic-validators-c"
    assert entry.owner_pr_or_feature == "PR169_VAL1"
    assert "docs/master_plan/generated/pr169_val1/**" in entry.output_globs
    assert ".github/workflows/qtt_validation.yml" in entry.required_when_files_match
    assert "tools/build_pr169_val1.py" in entry.required_when_files_match
    assert "tools/validate_pr169_val1.py" in entry.tool_globs
    assert "tests/tools/test_validation_shard_partition.py" in entry.required_when_files_match


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


def test_inventory_has_pr168_rp5d_r1_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5d_r1_exec_now_unlock"]
    validate_entry = entries["validate_pr168_rp5d_r1_exec_now_unlock"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5D_R1"
        assert "docs/master_plan/generated/PR168_RP5D_R1_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/pr168_rp5d_r1/**" in entry.output_globs
        assert "tests/pr168_rp5d_r1/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp5d_r1_exec_now_unlock.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp5d_r1_exec_now_unlock.py" in validate_entry.tool_globs


def test_pr168_rp5d_r1_paths_do_not_match_broad_pr168_rp_validators():
    paths = (
        "docs/master_plan/generated/pr168_rp5d_r1/agent_consume.jsonl",
        "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/runner.py",
        "tools/validate_pr168_rp5d_r1_exec_now_unlock.py",
    )

    for path in paths:
        matching_ids = {
            entry.validator_id for entry in inventory.entries_matching_path(path)
        }
        assert "build_pr168_rp5d_r1_exec_now_unlock" in matching_ids
        assert "validate_pr168_rp5d_r1_exec_now_unlock" in matching_ids
        assert (
            "validate_pr168_rp_validation_scope_registry_integration"
            not in matching_ids
        )
        assert "build_pr168_rp_formula_based_replay_paper_recompute" not in matching_ids
        assert (
            "validate_pr168_rp5d_replay_paper_executability_tiers"
            not in matching_ids
        )


def test_inventory_has_pr168_rp5f_entries():
    entries = inventory.inventory_by_id()
    build_entry = entries["build_pr168_rp5f_dynamic_targets"]
    validate_entry = entries["validate_pr168_rp5f_dynamic_targets"]

    for entry in (build_entry, validate_entry):
        assert entry.owner_pr_or_feature == "PR168_RP5F"
        assert "docs/master_plan/generated/PR168_RP5F_*.report.json" in entry.output_globs
        assert "docs/master_plan/generated/pr168_rp5f/**" in entry.output_globs
        assert "tests/pr168_rp5f/**" in entry.required_when_files_match

    assert "tools/build_pr168_rp5f_dynamic_targets.py" in build_entry.tool_globs
    assert "tools/validate_pr168_rp5f_dynamic_targets.py" in validate_entry.tool_globs


def test_pr168_rp5f_paths_do_not_match_broad_pr168_rp_validators():
    paths = (
        "docs/master_plan/generated/pr168_rp5f/targets.jsonl",
        "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
        "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/runner.py",
        "tools/validate_pr168_rp5f_dynamic_targets.py",
    )

    for path in paths:
        matching_ids = {
            entry.validator_id for entry in inventory.entries_matching_path(path)
        }
        assert "build_pr168_rp5f_dynamic_targets" in matching_ids
        assert "validate_pr168_rp5f_dynamic_targets" in matching_ids
        assert (
            "validate_pr168_rp_validation_scope_registry_integration"
            not in matching_ids
        )
        assert "build_pr168_rp_formula_based_replay_paper_recompute" not in matching_ids
        assert (
            "validate_pr168_rp5d_replay_paper_executability_tiers"
            not in matching_ids
        )
        assert "validate_pr168_rp5e_stack_gen" not in matching_ids


def test_inventory_knows_every_pytest_shard_phase_job():
    for phase in runner.ORDERED_PHASES:
        assert inventory.phase_job_id(phase) == inventory.VALIDATION_MATRIX_JOB_ID

    phase_jobs = {
        inventory.phase_job_id(phase)
        for phase in (
            runner.FAST_PREFLIGHT_PHASE,
            *runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES,
            *runner.PYTEST_SHARD_PHASES,
            runner.POST_VALIDATION_PHASE,
        )
    }
    assert phase_jobs == {inventory.VALIDATION_MATRIX_JOB_ID}
    assert runner.DETERMINISTIC_VALIDATORS_PHASE not in inventory.PHASE_JOB_IDS


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
