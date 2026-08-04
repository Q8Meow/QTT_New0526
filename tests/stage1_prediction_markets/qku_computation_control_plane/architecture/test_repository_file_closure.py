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
}


def test_production_package_is_exactly_the_collapsed_39_files() -> None:
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
    assert not tuple(
        path
        for path in package.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    )
