import json
import subprocess
import sys
from pathlib import Path

from src.qtt.core.testing import qtt_active_non_sha_day1_gate_state_registry as gate_registry
from tools import validate_qtt_roadmap_execution_state_controller as controller_gate


CONTROLLER_PATH = Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json")
SCHEMA_PATH = Path("schemas/roadmap/qtt_roadmap_execution_state_controller.schema.json")
ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
ACTIVE_REGISTRY_PATH = Path(
    "docs/master_plan/launch/QttActiveNonShaDay1GateStateRegistryContract.yaml"
)
FINAL_READINESS_POLICY_PATH = Path(
    "docs/master_plan/launch/QttFinalReadinessDependencyPolicyContract.yaml"
)
ROADMAP_DOCS = [
    Path("docs/roadmap/README.md"),
    Path(
        "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md"
    ),
    Path("docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json"),
    Path("docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md"),
    Path("docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"),
]


def _controller() -> dict:
    return json.loads(CONTROLLER_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _roster() -> dict:
    return json.loads(ROSTER_PATH.read_text(encoding="utf-8"))


def _roster_entry(entry_id: str) -> dict:
    return next(
        entry for entry in _roster()["entries"] if entry["roster_entry_id"] == entry_id
    )


def _mapping(label: str) -> dict:
    return next(
        entry
        for entry in _controller()["roadmap_range_currentization"]
        if entry["roadmap_pr_label"] == label
    )


def _iter_lists(value):
    if isinstance(value, list):
        yield value
        for item in value:
            yield from _iter_lists(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_lists(item)


def test_controller_json_validates():
    result = controller_gate.validate()

    assert result.ok, result.failures
    assert _controller()["controller_id"] == "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_V1_0"


def test_controller_schema_validates_expected_surface():
    schema = _schema()

    assert schema["title"] == "QTT Roadmap Execution-State Controller v1.0"
    assert "identity_translation_authority" in schema["required"]
    assert "roadmap_range_currentization" in schema["required"]
    assert schema["properties"]["roadmap_range_currentization"]["minItems"] == 26
    assert schema["properties"]["roadmap_range_currentization"]["maxItems"] == 26


def test_upstream_authority_paths_and_roster_reference_exist():
    controller = _controller()
    upstream_paths = {
        entry["authority_path"] for entry in controller["upstream_authorities"]
    }

    assert ACTIVE_REGISTRY_PATH.exists()
    assert FINAL_READINESS_POLICY_PATH.exists()
    assert ROSTER_PATH.exists()
    assert ACTIVE_REGISTRY_PATH.as_posix() in upstream_paths
    assert FINAL_READINESS_POLICY_PATH.as_posix() in upstream_paths
    assert ROSTER_PATH.as_posix() in upstream_paths
    assert (
        controller["identity_translation_authority"]["translator_path"]
        == ROSTER_PATH.as_posix()
    )


def test_pr117_roster_entry_is_currentized_and_keeps_planning_labels_null():
    pr117 = _roster_entry("PR117_REPO_CANONICAL_SELF_ENTRY")

    assert pr117["github_pr_number"] == 117
    assert pr117["github_audit_url"] == "https://github.com/Q8Meow/QTT_New0526/pull/117"
    assert pr117["roadmap_pr_label"] is None
    assert pr117["blueprint_pr_label"] is None


def test_pr118_self_entry_is_currentized_without_implying_roadmap_or_blueprint_118():
    pr118 = _roster_entry("PR118_REPO_CANONICAL_SELF_ENTRY")

    assert pr118["repo_canonical_pr_label"] == "PR118"
    assert pr118["github_pr_number"] == 118
    assert pr118["github_audit_url"] == "https://github.com/Q8Meow/QTT_New0526/pull/118"
    assert pr118["roadmap_pr_label"] is None
    assert pr118["blueprint_pr_label"] is None
    assert _mapping("PR #118")["title"] == "Replay engine executor"
    assert _mapping("PR #118")["roster_entry_id"] == "ROADMAP_PR_118_PLANNED"


def test_pr119_self_entry_is_currentized_without_implying_roadmap_or_blueprint_119():
    pr119 = _roster_entry("PR119_REPO_CANONICAL_SELF_ENTRY")

    assert pr119["repo_canonical_pr_label"] == "PR119"
    assert pr119["github_pr_number"] == 119
    assert pr119["github_audit_url"] == "https://github.com/Q8Meow/QTT_New0526/pull/119"
    assert pr119["roadmap_pr_label"] is None
    assert pr119["blueprint_pr_label"] is None
    assert _mapping("PR #119")["title"] == "Paper trading engine executor"
    assert _mapping("PR #119")["roster_entry_id"] == "ROADMAP_PR_119_PLANNED"


def test_roadmap_blueprint_labels_are_metadata_and_same_number_is_not_identity():
    controller = _controller()
    identity = controller["identity_translation_authority"]

    assert identity["same_number_identity_inference_forbidden"] is True
    assert identity["github_numbers_are_audit_only"] is True
    assert identity["roster_wins_on_identity_conflict"] is True
    assert all(
        entry["repo_delivery_status"] == "ROADMAP_BLUEPRINT_PLANNED_METADATA_ONLY"
        for entry in controller["roadmap_range_currentization"]
    )
    assert all(
        entry["identity_source"] == "QTT_PR_IDENTITY_ROSTER_V1_0"
        for entry in controller["roadmap_range_currentization"]
    )


def test_required_controller_state_classifications():
    taxonomy = _controller()["controlled_state_taxonomy"]

    assert taxonomy.count("FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES") == 1
    assert (
        _mapping("PR #101")["controller_state"]
        == "FINAL_READINESS_CONTROLLED_BY_ACTIVE_NON_SHA_GATES"
    )
    assert (
        _mapping("PR #125")["controller_state"]
        == "QUANTUM_BACKEND_STATE_CONTROLLED_BY_ACTIVE_NON_SHA_GATE"
    )
    assert (
        _mapping("PR #126")["controller_state"]
        == "QUANTUM_FORWARD_OPTIMIZATION_STATE_REFERENCED_BY_CONTROLLER"
    )
    for number in range(105, 127):
        entry = _mapping(f"PR #{number}")
        assert entry["controller_state"]
        assert entry["state_source"] == "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_V1_0"
        assert entry["identity_source"] == "QTT_PR_IDENTITY_ROSTER_V1_0"
        assert entry["next_allowed_action_class"]


def test_controller_does_not_duplicate_full_active_non_sha_gate_list():
    active_gate_ids = set(gate_registry.get_active_non_sha_day1_gate_ids())

    for value in _iter_lists(_controller()):
        string_items = {item for item in value if isinstance(item, str)}
        assert not active_gate_ids.issubset(string_items)

    fixture = json.loads(
        Path(
            "tests/fixtures/roadmap/synthetic_qtt_roadmap_execution_state_controller.v1.fixture.json"
        ).read_text(encoding="utf-8")
    )
    assert fixture["duplicates_full_active_non_sha_gate_list"] is False
    assert "remains the active non-SHA Day-1 gate source of truth" in fixture[
        "source_of_truth_note"
    ]


def test_capability_envelope_and_state_transition_are_single_pr118_flip():
    controller = _controller()
    envelope = controller["capability_envelope"]
    discipline = controller["state_transition_discipline"]

    assert envelope["materialized_capability_this_pr"] == (
        "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_V1_0"
    )
    assert envelope["state_transition_this_pr"] == (
        "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED"
    )
    assert envelope["downstream_functional_implementation_allowed_this_pr"] is False
    assert discipline["one_state_flip_per_repo_pr"] is True
    assert discipline["one_artifact_or_capability_per_repo_pr"] is True
    assert discipline["current_pr_state_flip"] == (
        "ROADMAP_EXECUTION_STATE_CONTROLLER_ESTABLISHED"
    )
    assert discipline["current_pr_materialized_capability"] == (
        "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_V1_0"
    )


def test_roadmap_blueprint_docs_reference_controller_and_do_not_copy_vectors():
    controller_path = CONTROLLER_PATH.as_posix()
    roster_path = ROSTER_PATH.as_posix()
    taxonomy = _controller()["controlled_state_taxonomy"]
    vector = _controller()["non_materialized_capability_vector"]

    for path in ROADMAP_DOCS:
        text = path.read_text(encoding="utf-8")
        assert controller_path in text
        assert roster_path in text
        assert not all(state in text for state in taxonomy)
        assert not all(capability in text for capability in vector)


def test_quantum_forward_state_routes_through_controller():
    controller = _controller()
    bindings = controller["active_state_bindings"]
    invariants = controller["controller_invariants"]

    assert bindings["quantum_backend_state"] == (
        "QUANTUM_BACKEND_STATE_CONTROLLED_BY_ACTIVE_NON_SHA_GATE"
    )
    assert bindings["quantum_backend_upstream_gate_reference"] == (
        "QUANTUM_BACKEND_AUTHORITY_GATE"
    )
    assert bindings["quantum_forward_optimization_state"] == (
        "QUANTUM_FORWARD_OPTIMIZATION_STATE_REFERENCED_BY_CONTROLLER"
    )
    assert invariants["future_quantum_optimization_support_must_route_through_controller"] is True
    assert invariants[
        "future_qaoa_vqe_qubo_ising_annealing_support_is_controller_referenced"
    ] is True
    assert invariants[
        "deterministic_selection_ranking_arbitration_future_compatibility_required"
    ] is True


def test_validator_success_marker_is_exact():
    completed = subprocess.run(
        [sys.executable, "tools/validate_qtt_roadmap_execution_state_controller.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_OK"
