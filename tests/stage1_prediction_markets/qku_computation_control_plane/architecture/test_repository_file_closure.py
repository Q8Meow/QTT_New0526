from pathlib import Path


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


def test_production_package_is_exactly_the_collapsed_47_files_and_certified_data() -> None:
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
