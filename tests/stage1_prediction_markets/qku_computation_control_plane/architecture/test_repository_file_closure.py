from pathlib import Path

from tools.validation_scope_registry import ST12G_ALLOWED_EXACT_PATHS


EXPECTED_PRODUCTION_FILES = {
    "__init__.py",
    "models.py",
    "errors.py",
    "context.py",
    "specification.py",
    "implementation_registry.py",
    "identity_adapter.py",
    "plugin_adapter.py",
    "quantum_adapter.py",
    "source_policy.py",
    "parameter_policy.py",
    "bindings.py",
    "dependency_graph.py",
    "oracle_contracts.py",
    "authority.py",
    "protocols.py",
    "serialization.py",
    "validation.py",
    "source_rights.py",
    "contextual_computability.py",
    "fallback.py",
    "freshness.py",
    "input_resolver.py",
    "point_in_time.py",
    "service.py",
    "stack_resolver.py",
    "unit_conversion.py",
    "economic_math.py",
    "receipts.py",
    "persistence.py",
    "migrations.py",
    "outbox.py",
    "transaction.py",
    "idempotency.py",
    "rollback.py",
    "accounting.py",
    "agent_policy.py",
    "lifecycle.py",
    "sqlite_reference.py",
    "latency_policy.py",
    "mode_snapshot_policy.py",
    "cohort_compiler.py",
    "input_lock.py",
    "evidence.py",
    "model_risk.py",
    "quantum_benchmark.py",
    "llm_gateway.py",
    "existing_owner_projection.py",
}
EXPECTED_DATA_FILES = {
    "st12f_parameter_resources_manifest.json",
    "st12f_parameter_rows_0001_0320.jsonl",
    "st12f_parameter_rows_0321_0640.jsonl",
    "st12f_parameter_rows_0641_0960.jsonl",
    "st12f_parameter_rows_0961_1280.jsonl",
    "st12f_parameter_rows_1281_1600.jsonl",
    "st12f_parameter_rows_1601_1920.jsonl",
    "st12f_parameter_rows_1921_2240.jsonl",
    "st12f_parameter_rows_2241_2560.jsonl",
    "st12f_parameter_rows_2561_2880.jsonl",
    "st12f_parameter_rows_2881_3200.jsonl",
    "st12f_parameter_rows_3201_3520.jsonl",
    "st12f_parameter_rows_3521_3840.jsonl",
}


def test_production_package_is_exactly_the_collapsed_48_files_and_certified_data() -> None:
    root = Path(__file__).resolve().parents[4]
    package = (
        root
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
    )
    actual = {path.name for path in package.glob("*.py")}
    assert actual == EXPECTED_PRODUCTION_FILES
    directories = {path.name for path in package.iterdir() if path.is_dir() and path.name != "__pycache__"}
    assert directories == {"data"}
    data = package / "data"
    assert {path.name for path in data.iterdir() if path.is_file()} == EXPECTED_DATA_FILES
    assert not (data / "__init__.py").exists()


ST12G_CREATE_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/existing_owner_projection.py",
        "tools/independent_validate_qku_computation_control_plane_g.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_contract_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_consumer_integration_matrix.py",
    }
)
ST12G_GENERATED_PATHS = frozenset(
    {
        "docs/master_plan/generated/qku_control_plane/existing_owner_projection/st12g_projection_contract_manifest.json",
        "docs/master_plan/generated/pr169_readiness1/st12g_evidence_projection_contract.generated.jsonl",
        "docs/master_plan/generated/pr169_pretrade1/st12g_evidence_projection_contract.generated.jsonl",
        "docs/master_plan/generated/pr169_agent_orch1/st12g_evidence_handoff_contract.generated.jsonl",
        "docs/master_plan/generated/pr169_svc1/st12g_evidence_view_contract.generated.jsonl",
        "docs/master_plan/generated/pr169_dash1/st12g_evidence_owner_view_contract.generated.jsonl",
        "docs/master_plan/generated/pr169_readiness1/readiness_manifest.json",
        "docs/master_plan/generated/pr169_readiness1/no_orphan.report.json",
        "docs/master_plan/generated/pr169_pretrade1/pretrade_manifest.json",
        "docs/master_plan/generated/pr169_pretrade1/no_orphan.report.json",
        "docs/master_plan/generated/pr169_agent_orch1/manifest.json",
        "docs/master_plan/generated/pr169_agent_orch1/no_orphan.report.json",
        "docs/master_plan/generated/pr169_svc1/service_manifest.json",
        "docs/master_plan/generated/pr169_svc1/no_orphan.report.json",
        "docs/master_plan/generated/pr169_dash1/owner_dashboard_registry_manifest.json",
        "docs/master_plan/generated/pr169_dash1/owner_dashboard_no_orphan.report.json",
        "docs/master_plan/generated/pr169_dash1/owner_data_value_route_map.generated.jsonl",
        "docs/master_plan/generated/pr169_dash1/owner_surface_projection_manifest.generated.jsonl",
        "docs/master_plan/generated/pr169_dash1/validation_summary.report.json",
        "docs/master_plan/generated/pr169_dash1/owner_dashboard_ui_manifest.json",
        "docs/master_plan/generated/pr169_dash1/ui/owner_dashboard_review_data.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui/owner_dashboard_review_bootstrap.generated.js",
        "docs/master_plan/generated/pr169_dash1/ui1_r2r6/truth.generated.json",
        "docs/master_plan/generated/pr169_dash1/ui1_r2r6/centralization_manifest.json",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
ST12G_READ_ONLY_PREDECESSOR_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/parameter_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/oracle_contracts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/service.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py",
        "src/qtt/core/testing/gate_result.py",
        "tests/core/test_qtt_cumulative_gate.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_operation_contract_closure.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/architecture/test_mode_evidence_orthogonality.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/context.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_lock.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/serialization.py",
    }
)
ST12G_FORBIDDEN_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/readiness_projection.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/pretrade_projection.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/svc_projection.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_orch_projection.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dashboard_projection.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/projection_manifest.py",
        "tests/qku_computation_control_plane/test_projection_integrity.py",
    }
)


def test_st12g_repository_frontier_has_exact_dispositions() -> None:
    root = Path(__file__).resolve().parents[4]
    modified = ST12G_ALLOWED_EXACT_PATHS - ST12G_CREATE_PATHS - ST12G_GENERATED_PATHS
    assert len(ST12G_CREATE_PATHS) == 4
    assert len(modified) == 36
    assert len(ST12G_GENERATED_PATHS) == 25
    assert len(ST12G_READ_ONLY_PREDECESSOR_PATHS) == 16
    assert len(ST12G_FORBIDDEN_PATHS) == 7
    assert len(
        ST12G_ALLOWED_EXACT_PATHS
        | ST12G_READ_ONLY_PREDECESSOR_PATHS
        | ST12G_FORBIDDEN_PATHS
    ) == 88
    assert not (
        ST12G_ALLOWED_EXACT_PATHS
        & (ST12G_READ_ONLY_PREDECESSOR_PATHS | ST12G_FORBIDDEN_PATHS)
    )
    for path in ST12G_ALLOWED_EXACT_PATHS | ST12G_READ_ONLY_PREDECESSOR_PATHS:
        assert (root / path).is_file(), path
    for path in ST12G_FORBIDDEN_PATHS:
        assert not (root / path).exists(), path
