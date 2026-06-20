from tools.pr168_rp_validator import run_validation


def test_validation_scope_registry_integration() -> None:
    run_validation("validation_scope_registry_integration")
