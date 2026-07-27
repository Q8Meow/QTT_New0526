from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    validate_production_core_paths,
)


def test_current_owner_interfaces_and_production_paths_exist() -> None:
    root = Path(__file__).resolve().parents[4]
    report = validate_production_core_paths(root)
    assert report.passed
    owner_paths = (
        "tools/pr168_rp5c_library_reader.py",
        "docs/master_plan/generated/PR162E_PluginFamilyRegistry.report.json",
        "src/qtt/stage1_prediction_markets/pr162e_q_quantum_automapper/io.py",
        "src/qtt/readiness/pr169_readiness1_resolvers.py",
        "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
        "src/qtt/service/pr169_svc1_resolvers.py",
        "src/qtt/agents/pr169_agent_orch1_resolvers.py",
        "src/qtt/source_evidence/revalidation/scheduler.py",
        "src/qtt/stage1_prediction_markets/latency_hot_path_snapshot_boundary/constants.py",
        "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py",
    )
    assert len(owner_paths) == 10
    assert all((root / path).is_file() for path in owner_paths)
