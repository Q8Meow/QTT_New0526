import functools
import json
from pathlib import Path

from tools import generate_atomicrows_exact_row_agent_family_eligibility_matrix as generator
from tools import run_validation_gates as runner
from tools import validate_atomicrows_exact_row_agent_family_eligibility_matrix as gate


REPO_ROOT = Path(__file__).resolve().parents[2]
EXACT_DIR = REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_write_manifest_is_byte_stable_with_newline(tmp_path, monkeypatch, newline: bytes) -> None:
    payload = {
        "manifest_id": "TEST_D2_E0_NEWLINE_STABILITY",
        "row_coverage_records": [
            {"exact_row_id": "ROW_001", "scoring_readiness_decision": "STATIC_ONLY"}
        ],
    }
    manifest_path = Path("generated") / "manifest.json"
    output_path = tmp_path / manifest_path
    output_path.parent.mkdir(parents=True)
    existing = generator.render_manifest(payload).encode("utf-8").replace(b"\n", newline)
    output_path.write_bytes(existing)

    monkeypatch.setattr(generator, "build_manifest", lambda repo_root=generator.REPO_ROOT: payload)

    assert generator.write_manifest(tmp_path, manifest_path) == output_path
    assert output_path.read_bytes() == existing


@functools.lru_cache(maxsize=1)
def _manifest() -> dict:
    return gate.load_manifest(REPO_ROOT / gate.DEFAULT_MANIFEST)


@functools.lru_cache(maxsize=1)
def _records() -> tuple[dict, ...]:
    return tuple(_manifest()["row_coverage_records"])


@functools.lru_cache(maxsize=1)
def _validated_report() -> dict:
    result = gate.validate(repo_root=REPO_ROOT)
    assert result.ok, result.failures
    assert result.report is not None
    return result.report


def _family_records(family_id: str) -> list[dict]:
    return [record for record in _records() if record["family_id"] == family_id]


def test_d2_e0_manifest_schema_validates_and_validator_emits_marker(capsys):
    manifest = _manifest()
    schema = _load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)
    record_schema = _load_json(REPO_ROOT / gate.DEFAULT_RECORD_SCHEMA)

    assert gate.validate_manifest_payload(manifest, schema, record_schema) == []
    assert gate.main(["--repo-root", str(REPO_ROOT)]) == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_d2_e0_report_exists_and_is_deterministic():
    report = _validated_report()
    path = REPO_ROOT / gate.DEFAULT_REPORT

    assert path.exists()
    assert gate.serialize_report(report) == gate.serialize_report(json.loads(gate.serialize_report(report)))
    assert report["result_marker"] == gate.SUCCESS_MARKER
    assert report["scoring_ranking_readiness_overlay_status"] == gate.OVERLAY_SUCCESS_STATE


def test_d2_e0_exact_row_source_counts_and_distribution():
    report = _validated_report()

    assert EXACT_DIR.is_dir()
    assert len(list(EXACT_DIR.glob("*.exact_rows.jsonl"))) == 15
    assert sum(1 for path in EXACT_DIR.glob("*.exact_rows.jsonl") for _ in path.read_text(encoding="utf-8").splitlines()) == 4183
    assert report["source_family_file_count"] == 15
    assert report["source_exact_row_record_count"] == 4183
    assert report["family_distribution_match"] is True


def test_d2_e0_all_rows_have_exactly_one_eligibility_and_scoring_record():
    records = _records()
    report = _validated_report()
    row_ids = [record["exact_row_id"] for record in records]

    assert len(records) == 4183
    assert len(row_ids) == len(set(row_ids))
    assert report["matrix_coverage_count"] == 4183
    assert report["scoring_readiness_coverage_count"] == 4183
    assert report["missing_row_count"] == 0
    assert report["duplicate_row_count"] == 0
    assert report["unexpected_row_count"] == 0
    assert all(record["agent_family_eligibility_decision"] for record in records)
    assert all(record["scoring_readiness_decision"] for record in records)


def test_d2_e0_records_are_ordered_by_family_and_row_index():
    records = _records()
    assert [(record["family_id"], record["row_index"]) for record in records] == sorted(
        (record["family_id"], record["row_index"]) for record in records
    )


def test_d2_e0_fail_closed_forbidden_authorities_are_false_for_every_row():
    for record in _records():
        for field in generator.FORBIDDEN_AUTHORITY_BOOL_FIELDS:
            assert record[field] is False
        assert record["blocked_authority_classes"] == list(generator.BLOCKED_AUTHORITY_CLASSES)
        assert set(record["allowed_agent_family_classes"]).issubset(
            set(generator.ALLOWED_AGENT_FAMILY_CLASSES)
        )


def test_d2_e0_report_forbidden_authority_counts_are_zero():
    report = _validated_report()
    zero_fields = [
        "live_order_authority_count",
        "final_order_submission_authority_count",
        "live_trade_intent_authority_count",
        "scoring_execution_allowed_count",
        "ranking_execution_allowed_count",
        "selection_execution_allowed_count",
        "candidate_stack_generation_allowed_count",
        "optimizer_execution_allowed_count",
        "replay_execution_allowed_count",
        "paper_execution_allowed_count",
        "quantum_backend_authority_count",
        "quantum_simulator_authority_count",
        "quantum_provider_authority_count",
        "source_fact_authority_count",
        "connector_authority_count",
        "runtime_cash_authority_count",
        "bundle_authority_count",
        "sha_freeze_authority_count",
        "final_readiness_authority_count",
    ]

    assert all(report[field] == 0 for field in zero_fields)


def test_d2_e0_no_computed_score_rank_selection_optimizer_replay_profit_or_superiority_outputs():
    report = _validated_report()
    forbidden_keys = gate.FORBIDDEN_COMPUTED_ROW_FIELDS

    assert all(not (set(record) & forbidden_keys) for record in _records())
    assert report["computed_score_field_count"] == 0
    assert report["numeric_ranking_output_count"] == 0
    assert report["selected_stack_output_count"] == 0
    assert report["optimizer_output_count"] == 0
    assert report["replay_paper_result_count"] == 0
    assert report["profit_evidence_count"] == 0
    assert report["expected_profit_proof_count"] == 0
    assert report["latency_superiority_evidence_count"] == 0
    assert report["execution_superiority_evidence_count"] == 0
    assert report["quantum_advantage_evidence_count"] == 0


def test_d2_e0_future_score_component_labels_are_metadata_only():
    overlay = _manifest()["scoring_ranking_readiness_overlay"]
    required = set(generator.FUTURE_SCORE_COMPONENT_INPUT_LABELS)

    assert set(overlay["future_score_component_input_labels"]) == required
    assert all(definition["computed_value_created_by_d2_e0"] is False for definition in overlay["scoring_feature_definitions"])
    assert all(set(record["eligible_future_score_components"]) <= required for record in _records())
    assert all(record["ranking_contract_input_eligible_future_only"] is True for record in _records())
    assert all(record["selection_contract_input_eligible_future_only"] is True for record in _records())


def test_d2_e0_future_stack_role_labels_are_present_with_block_reasons():
    required = set(generator.FUTURE_STACK_ROLE_LABELS)

    for record in _records():
        eligible = set(record["eligible_future_stack_roles"])
        blocked = {item["role_label"] for item in record["blocked_future_stack_roles"]}
        assert eligible
        assert eligible | blocked == required
        assert eligible.isdisjoint(blocked)
        assert all(item["block_reason_code"] for item in record["blocked_future_stack_roles"])


def test_d2_e0_family_role_and_score_label_mapping():
    expected = {
        "001_signal_features": ("SIGNAL_ROLE", "PLATFORM_APPLICABILITY_SCORE_INPUT"),
        "002_scoring_ranking": ("SCORING_ROLE", "FINAL_SELECTION_SCORE_INPUT"),
        "003_normalization_calibration": ("NORMALIZATION_ROLE", "COMPLEXITY_PENALTY_INPUT"),
        "004_risk_control": ("RISK_ROLE", "DRAWDOWN_PENALTY_INPUT"),
        "005_execution_connector_boundary": ("EXECUTION_BOUNDARY_ROLE", "EXECUTION_COST_PENALTY_INPUT"),
        "006_capital_sizing_cash": ("CAPITAL_SIZING_ROLE", "RUNTIME_READINESS_SCORE_INPUT"),
        "007_latency_routing": ("LATENCY_ROUTING_ROLE", "LATENCY_FIT_SCORE_INPUT"),
        "008_error_guard_fail_closed": ("ERROR_GUARD_ROLE", "RISK_FIT_SCORE_INPUT"),
        "009_lifecycle_agent_binding": ("AGENT_LIFECYCLE_BINDING_ROLE", "AGENT_BINDING_SCORE_INPUT"),
        "010_source_evidence_connector_semantic": ("SOURCE_EVIDENCE_ROLE", "SOURCE_CURRENTNESS_PENALTY_INPUT"),
        "011_replay_paper_validation": ("REPLAY_PAPER_VALIDATION_ROLE", "REPLAY_PAPER_SCORE_INPUT"),
        "012_quantum_advisory_optimization": ("QUANTUM_ADVISORY_ROLE", "QUANTUM_APPLICABILITY_SCORE_INPUT"),
        "013_quantum_qubo_ising_metadata": ("QUBO_ISING_METADATA_ROLE", "OPTIMIZER_SCORE_INPUT"),
        "014_quantum_qaoa_vqe_annealing_metadata": ("QAOA_VQE_ANNEALING_METADATA_ROLE", "QUANTUM_BOOST_INPUT"),
        "015_quantum_portfolio_hybrid_comparator": ("QUANTUM_PORTFOLIO_COMPARATOR_ROLE", "EXPECTED_NET_PROFIT_SCORE_INPUT"),
    }

    for family_id, (role, score_label) in expected.items():
        records = _family_records(family_id)
        assert records
        assert all(record["eligible_future_stack_roles"] == [role] for record in records)
        assert all(score_label in record["eligible_future_score_components"] for record in records)


def test_d2_e0_family_specific_execution_blocks():
    assert all(record["scoring_execution_allowed"] is False and record["ranking_execution_allowed"] is False for record in _family_records("002_scoring_ranking"))
    assert all(record["connector_authority_allowed"] is False and record["live_order_authority_allowed"] is False for record in _family_records("005_execution_connector_boundary"))
    assert all(record["runtime_cash_authority_allowed"] is False for record in _family_records("006_capital_sizing_cash"))
    assert all(record["latency_superiority_evidence_allowed"] is False for record in _family_records("007_latency_routing"))
    assert all(record["source_fact_authority_allowed"] is False and record["connector_authority_allowed"] is False for record in _family_records("010_source_evidence_connector_semantic"))
    assert all(record["replay_execution_allowed"] is False and record["paper_execution_allowed"] is False for record in _family_records("011_replay_paper_validation"))


def test_d2_e0_quantum_families_are_metadata_only():
    report = _validated_report()
    quantum_records = [
        record for record in _records() if record["family_id"] in generator.source_generator.QUANTUM_FORWARD_FAMILY_IDS
    ]

    assert len(quantum_records) == 1103
    assert report["quantum_family_metadata_only_result"]["metadata_only"] is True
    assert all(record["quantum_backend_authority_allowed"] is False for record in quantum_records)
    assert all(record["quantum_simulator_authority_allowed"] is False for record in quantum_records)
    assert all(record["quantum_provider_authority_allowed"] is False for record in quantum_records)
    assert all(record["quantum_advantage_evidence_allowed"] is False for record in quantum_records)


def test_d2_e0_governance_family_009_is_non_live():
    report = _validated_report()

    assert len(_family_records("009_lifecycle_agent_binding")) == 270
    assert report["agent_governance_family_non_live_result"]["non_live"] is True


def test_d2_e0_trade_context_and_low_latency_policies_are_static_only():
    overlay = _manifest()["scoring_ranking_readiness_overlay"]
    trade_policy = overlay["trade_context_selection_readiness_policy"]
    latency_policy = overlay["low_latency_readiness_policy"]

    assert trade_policy["single_row_trade_stack_blocked"] is True
    assert trade_policy["single_parameter_trade_stack_blocked"] is True
    assert trade_policy["single_algorithm_trade_stack_blocked"] is True
    assert trade_policy["role_complete_multi_row_stack_preparation_allowed_future_metadata_only"] is True
    assert latency_policy["static_precomputed_metadata_only"] is True
    assert latency_policy["live_path_source_retrieval_allowed"] is False
    assert latency_policy["live_path_quantum_backend_call_allowed"] is False
    assert latency_policy["live_path_llm_call_allowed"] is False


def test_d2_e0_future_pr_handoffs_are_ready_without_execution():
    report = _validated_report()
    handoff = _manifest()["future_pr_handoff"]

    assert handoff["future_bundle_materialization_executed_by_d2_e0"] is False
    assert handoff["future_sha_freeze_executed_by_d2_e0"] is False
    assert handoff["future_final_readiness_executed_by_d2_e0"] is False
    assert report["future_pr84_handoff_ready"] is True
    assert report["future_pr85_handoff_ready"] is True
    assert report["future_pr86_handoff_ready"] is True
    assert report["future_pr87_handoff_ready"] is True
    assert report["future_pr88_handoff_ready"] is True
    assert report["future_pr89_handoff_ready"] is True
    assert report["future_pr90_plus_handoff_ready"] is True


def test_d2_e0_repair_pr_e_handoff_does_not_create_bundle_or_sha():
    report = _validated_report()

    assert report["future_repair_pr_e_handoff_state"] == "REPAIR_PR_E_BUNDLE_MATERIALIZATION_REQUIRED_FUTURE_ONLY_NOT_EXECUTED"
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
    assert report["forbidden_artifact_checks"]["AtomicRows.bundle.jsonl"] is True
    assert report["forbidden_artifact_checks"]["AtomicRows.bundle.sha256"] is True


def test_d2_e0_master_plan_is_unchanged():
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []
    assert _validated_report()["master_plan_diff_check"]["unchanged"] is True


def test_d2_e0_run_validation_gates_includes_validator_in_correct_order():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py" in command_names
    assert command_names.index("validate_atomicrows_exact_row_source_materialization_manifest.py") < command_names.index(
        "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
    ) < command_names.index("validate_generated_derivative_bootstrap_gate_static.py")


def test_d2_e0_generator_write_manifest_is_byte_stable_with_crlf_existing_file(tmp_path, monkeypatch):
    _assert_write_manifest_is_byte_stable_with_newline(tmp_path, monkeypatch, b"\r\n")


def test_d2_e0_generator_write_manifest_is_byte_stable_with_lf_existing_file(tmp_path, monkeypatch):
    _assert_write_manifest_is_byte_stable_with_newline(tmp_path, monkeypatch, b"\n")


def test_d2_e0_generator_is_deterministic():
    manifest_path = REPO_ROOT / generator.DEFAULT_MANIFEST
    report_path = REPO_ROOT / gate.DEFAULT_REPORT
    before = {
        manifest_path: manifest_path.read_bytes(),
        report_path: report_path.read_bytes(),
    }
    assert generator.main([]) == 0
    after = {
        manifest_path: manifest_path.read_bytes(),
        report_path: report_path.read_bytes(),
    }

    assert before == after
