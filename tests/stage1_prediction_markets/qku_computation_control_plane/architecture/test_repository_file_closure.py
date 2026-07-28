from pathlib import Path


EXPECTED_TRANCHE_A_PRODUCTION_FILES = {
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
}
EXPECTED_TRANCHE_B_PRODUCTION_FILES = {
    "contextual_computability.py",
    "fallback.py",
    "freshness.py",
    "input_resolver.py",
    "point_in_time.py",
    "service.py",
    "stack_resolver.py",
    "unit_conversion.py",
}


def test_production_package_preserves_a_and_adds_exactly_eight_b_files() -> None:
    root = Path(__file__).resolve().parents[4]
    package = (
        root
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
    )
    actual = {path.name for path in package.glob("*.py")}
    assert len(EXPECTED_TRANCHE_A_PRODUCTION_FILES) == 19
    assert len(EXPECTED_TRANCHE_B_PRODUCTION_FILES) == 8
    assert not (
        EXPECTED_TRANCHE_A_PRODUCTION_FILES
        & EXPECTED_TRANCHE_B_PRODUCTION_FILES
    )
    assert actual == (
        EXPECTED_TRANCHE_A_PRODUCTION_FILES
        | EXPECTED_TRANCHE_B_PRODUCTION_FILES
    )
    assert not tuple(
        path
        for path in package.iterdir()
        if path.is_dir() and path.name != "__pycache__"
    )
