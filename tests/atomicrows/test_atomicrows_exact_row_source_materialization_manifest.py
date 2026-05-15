import functools
import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_exact_row_generator_dry_run_manifest as c_gate
from tools import validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest as c1_gate
from tools import generate_atomicrows_exact_row_source_files as generator
from tools import validate_atomicrows_exact_row_source_materialization_manifest as gate


REPO_ROOT = Path(__file__).resolve().parents[2]
EXACT_DIR = REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def _validated_report() -> dict:
    result = gate.validate(repo_root=REPO_ROOT)
    assert result.ok, result.failures
    assert result.report is not None
    return result.report


@functools.lru_cache(maxsize=1)
def _rows() -> tuple[dict, ...]:
    rows = []
    for path in sorted(EXACT_DIR.glob("*.exact_rows.jsonl")):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    return tuple(rows)


def _family_files() -> list[Path]:
    return sorted(EXACT_DIR.glob("*.exact_rows.jsonl"))


def test_d_manifest_schema_validates(capsys):
    config = gate.load_yaml(REPO_ROOT / gate.DEFAULT_MANIFEST)
    schema = _load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)

    assert gate.validate_manifest_payload(config, schema) == []
    assert gate.main(["--repo-root", str(REPO_ROOT)]) == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_d_source_record_schema_validates_sample_rows():
    schema = _load_json(REPO_ROOT / gate.DEFAULT_RECORD_SCHEMA)
    rows = _rows()

    for index in (0, 389, 4182):
        assert gate.validate_source_record_schema(
            rows[index], schema, location=f"sample:{index}"
        ) == []


def test_d_exact_row_sources_directory_exists():
    assert EXACT_DIR.is_dir()


def test_d_exactly_15_family_files_exist():
    assert [path.name for path in _family_files()] == list(generator.expected_file_names())


def test_d_total_row_count_4183():
    assert len(_rows()) == 4183
    assert _validated_report()["exact_row_source_record_count"] == 4183


def test_d_family_counts_match_c0_exactly():
    report = _validated_report()
    assert [entry["row_count"] for entry in report["family_materialization"]] == [
        count for _, _, count in generator.FAMILY_DISTRIBUTION
    ]
    assert report["aggregate_checks"]["c0_distribution_matches_source_files"] is True


def test_d_row_ranges_match_c0_exactly():
    ranges = [
        (entry["start_row_index"], entry["end_row_index"])
        for entry in _validated_report()["family_materialization"]
    ]
    assert ranges == [
        (1, 390),
        (391, 720),
        (721, 940),
        (941, 1255),
        (1256, 1535),
        (1536, 1755),
        (1756, 2005),
        (2006, 2225),
        (2226, 2495),
        (2496, 2810),
        (2811, 3080),
        (3081, 3370),
        (3371, 3635),
        (3636, 3900),
        (3901, 4183),
    ]


def test_d_row_indexes_contiguous_no_gaps_no_overlaps():
    assert [row["row_index"] for row in _rows()] == list(range(1, 4184))
    aggregate = _validated_report()["aggregate_checks"]
    assert aggregate["row_ranges_contiguous"] is True
    assert aggregate["row_ranges_non_overlapping"] is True
    assert aggregate["row_ranges_no_gaps"] is True


def test_d_row_ids_deterministic_unique_and_match_dry_run():
    rows = _rows()
    row_ids = [row["row_id"] for row in rows]
    assert len(row_ids) == len(set(row_ids))
    assert row_ids[0] == "AR_EXACT_001_SIGNAL_FEATURES_000001"
    assert row_ids[389] == "AR_EXACT_001_SIGNAL_FEATURES_000390"
    assert row_ids[-1] == "AR_EXACT_015_QUANTUM_PORTFOLIO_HYBRID_COMPARATOR_000283"
    assert _validated_report()["aggregate_checks"]["dry_run_matches_source_files"] is True


def test_d_every_row_has_required_authority_fields():
    assert all(row["authority_class"] == generator.AUTHORITY_CLASS for row in _rows())
    assert all(row["authority_field_policy"]["row_is_exact_source_record"] is True for row in _rows())


def test_d_every_row_has_source_pointer_policy():
    assert all(row["source_pointer_policy"] == generator.source_pointer_policy() for row in _rows())


def test_d_every_row_has_block_code_policy():
    assert all(row["block_code_policy"] == generator.block_code_policy() for row in _rows())
    assert all(set(row["block_codes"]) >= set(generator.BASE_BLOCK_CODES) for row in _rows())


def test_d_every_row_has_agent_eligibility_deny_by_default():
    assert all(row["agent_eligibility"] == generator.agent_eligibility() for row in _rows())


def test_d_every_row_has_subfamily_and_row_class():
    assert all(row["subfamily_id"] and row["row_class"] for row in _rows())


def test_d_every_row_has_execution_boundary():
    assert all(row["execution_boundary"] == generator.execution_boundary() for row in _rows())


def test_d_every_row_has_external_fact_boundary():
    assert all(row["external_fact_boundary"] == generator.external_fact_boundary() for row in _rows())


def test_d_every_row_has_selection_and_scoring_boundary():
    assert all(
        row["selection_and_scoring_boundary"] == generator.selection_and_scoring_boundary()
        for row in _rows()
    )


def test_d_every_row_has_latency_boundary():
    assert all(row["latency_boundary"] == generator.latency_boundary() for row in _rows())


def test_d_every_row_has_risk_boundary():
    assert all(row["risk_boundary"] == generator.risk_boundary() for row in _rows())


def test_d_every_row_has_future_extension_policy():
    assert all(row["future_extension_policy"] == generator.future_extension_policy() for row in _rows())


def test_d_quantum_forward_families_metadata_only():
    quantum_rows = [row for row in _rows() if row["family_id"] in generator.QUANTUM_FORWARD_FAMILY_IDS]
    assert len(quantum_rows) == 1103
    assert all(row["quantum_metadata"]["quantum_forward_family_flag"] is True for row in quantum_rows)
    assert all(row["quantum_metadata"]["quantum_backend_execution_created"] is False for row in quantum_rows)
    assert all(row["quantum_metadata"]["quantum_advantage_claim_created"] is False for row in quantum_rows)


def test_d_non_quantum_families_not_marked_quantum_forward():
    non_quantum_rows = [
        row for row in _rows() if row["family_id"] not in generator.QUANTUM_FORWARD_FAMILY_IDS
    ]
    assert all(row["quantum_metadata"]["quantum_forward_family_flag"] is False for row in non_quantum_rows)


def test_d_quantum_rows_have_future_quantum_extension_slots():
    quantum_rows = [row for row in _rows() if row["family_id"] in generator.QUANTUM_FORWARD_FAMILY_IDS]
    assert all(row["future_extension_policy"]["extension_slots"]["quantum_extension_refs"] == [] for row in quantum_rows)
    assert all(row["quantum_metadata"]["future_quantum_extension_supported"] is True for row in quantum_rows)


def test_d_agent_governance_family_009_count_270():
    assert sum(1 for row in _rows() if row["family_id"] == "009_lifecycle_agent_binding") == 270
    assert _validated_report()["agent_eligibility_audit"]["deny_by_default_pending_d2_e0"] is True


def test_d_no_bundle_no_sha_no_freeze_no_final_readiness():
    report = _validated_report()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
    assert report["forbidden_artifact_absence"]["atomicrows_bundle_absent"] is True
    assert report["forbidden_artifact_absence"]["atomicrows_bundle_sha_absent"] is True
    assert report["forbidden_artifact_absence"]["freeze_absent"] is True
    assert report["forbidden_artifact_absence"]["final_readiness_absent"] is True


def test_d_no_runtime_live_order_source_connector_profit_authority():
    for row in _rows():
        policy = row["authority_field_policy"]
        assert policy["row_is_runtime_authority"] is False
        assert policy["row_is_live_authority"] is False
        assert policy["row_is_order_authority"] is False
        assert policy["row_is_source_fact_authority"] is False
        assert policy["row_is_connector_semantic_authority"] is False
        assert policy["row_is_profit_authority"] is False


def test_d_no_replay_paper_optimizer_quantum_backend_execution():
    assert all(
        row["execution_boundary"] == generator.execution_boundary()
        for row in _rows()
    )


def test_d_no_profit_latency_execution_quantum_advantage_evidence():
    assert all(row["quantum_metadata"]["quantum_profit_evidence_created"] is False for row in _rows())
    assert all(row["latency_boundary"]["latency_superiority_evidence_created"] is False for row in _rows())
    assert _validated_report()["authority_boundary_audit"]["no_execution_superiority_evidence_created"] is True
    assert _validated_report()["authority_boundary_audit"]["no_quantum_advantage_evidence_created"] is True


def test_d_no_fabricated_institutional_ranges_or_quantum_defaults():
    assert all(not gate.contains_forbidden_literal(row) for row in _rows())
    assert all(
        "NO_NUMERIC_DEFAULTS" in row["quantum_metadata"]["quantum_parameter_surface"]
        for row in _rows()
        if row["family_id"] in generator.QUANTUM_FORWARD_FAMILY_IDS
    )


def test_d_report_does_not_embed_all_rows():
    report = _validated_report()
    assert "rows" not in report
    assert "source_rows" not in report
    assert "exact_rows" not in report
    assert len(report["family_materialization"]) == 15


def test_d_generator_is_deterministic():
    before = {path.name: path.read_bytes() for path in _family_files()}
    assert generator.main([]) == 0
    after = {path.name: path.read_bytes() for path in _family_files()}
    assert before == after


def test_d_generator_preserves_existing_crlf_bytes_when_rows_match(tmp_path):
    plan = generator.build_family_plans()[2]
    path = tmp_path / Path(plan.exact_rows_file_path)
    path.parent.mkdir(parents=True)
    canonical = generator.render_family_file_bytes(plan)
    crlf = canonical.replace(b"\n", b"\r\n")
    path.write_bytes(crlf)

    generator.write_family_file(tmp_path, plan)

    assert path.read_bytes() == crlf


def test_d_generator_rewrites_existing_crlf_file_when_content_changes(tmp_path):
    plan = generator.build_family_plans()[2]
    path = tmp_path / Path(plan.exact_rows_file_path)
    path.parent.mkdir(parents=True)
    canonical = generator.render_family_file_bytes(plan)
    tampered = canonical.replace(b"\n", b"\r\n").replace(
        b'"family_row_ordinal":1',
        b'"family_row_ordinal":999',
        1,
    )
    assert tampered != canonical
    path.write_bytes(tampered)

    generator.write_family_file(tmp_path, plan)

    assert path.read_bytes() == canonical


def test_d_generator_is_rerunnable_without_extra_files():
    names_before = [path.name for path in _family_files()]
    assert generator.main([]) == 0
    assert [path.name for path in _family_files()] == names_before
    assert len(_family_files()) == 15


def test_d_validator_writes_only_materialization_report():
    upstream_reports = [
        REPO_ROOT / "docs/master_plan/generated/AtomicRowsExactRowAuthorityClassifierBridge.report.json",
        REPO_ROOT / "docs/master_plan/generated/AtomicRowsExactRowExpansionManifest.report.json",
        REPO_ROOT / "docs/master_plan/generated/AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json",
        REPO_ROOT / "docs/master_plan/generated/AtomicRowsExactRowGeneratorDryRun.report.json",
        REPO_ROOT / "docs/master_plan/generated/AtomicRowsRepairChainGrandDebugLogicAudit.report.json",
    ]
    before = {path: path.read_bytes() for path in upstream_reports}
    assert gate.main(["--repo-root", str(REPO_ROOT)]) == 0
    assert {path: path.read_bytes() for path in upstream_reports} == before
    assert (REPO_ROOT / gate.DEFAULT_REPORT).exists()


def test_d_run_validation_gates_includes_d_validator():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert "validate_atomicrows_exact_row_source_materialization_manifest.py" in command_names


def test_d_validation_gate_order_is_coherent():
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert command_names.index("validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py") < command_names.index(
        "validate_atomicrows_exact_row_source_materialization_manifest.py"
    ) < command_names.index("validate_generated_derivative_bootstrap_gate_static.py")


def test_d_c_and_c1_validators_accept_post_d_only_with_valid_d_materialization():
    c_result = c_gate.validate(repo_root=REPO_ROOT)
    c1_result = c1_gate.validate(repo_root=REPO_ROOT)
    assert c_result.ok, c_result.failures
    assert c1_result.ok, c1_result.failures
    assert c_result.report["post_d_transition_audit"]["current_exact_row_sources_presence_allowed_by_repair_pr_d"] is True
    assert c1_result.report["post_d_transition_audit"]["current_exact_row_sources_presence_allowed_by_repair_pr_d"] is True


def test_d_bundle_builder_remains_future_required():
    assert _validated_report()["blocked_future_work"]["repair_pr_e_bundle_materialization_required"] is True


def test_d_sha_freeze_remains_future_required():
    assert _validated_report()["blocked_future_work"]["repair_pr_f_sha_freeze_required"] is True


def test_d_final_readiness_remains_future_required():
    assert _validated_report()["blocked_future_work"]["roadmap_pr_101_final_readiness_delayed"] is True


def test_d_master_plan_not_modified():
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []


def test_d_no_extra_exact_row_source_files():
    assert [path.name for path in _family_files()] == list(generator.expected_file_names())


def test_d_all_jsonl_files_end_with_newline_and_have_no_blank_lines():
    for path in _family_files():
        raw = path.read_bytes()
        assert raw.endswith(b"\n")
        assert all(line.strip() for line in raw.decode("utf-8").splitlines())


def test_d_row_file_paths_match_family_ids():
    for row in _rows():
        assert row["source_file_family_id"] == row["family_id"]
        assert row["source_file_path"].endswith(f"{row['family_id']}.exact_rows.jsonl")


def test_d_future_extension_slots_are_empty_and_non_authoritative():
    for row in _rows():
        slots = row["future_extension_policy"]["extension_slots"]
        assert all(value == [] for value in slots.values())
        assert row["future_extension_policy"]["extension_may_not_create_live_authority_by_default"] is True


def test_d_low_latency_boundary_static_only_no_hot_path_dependency():
    assert all(row["latency_boundary"] == generator.latency_boundary() for row in _rows())
    assert all(row["execution_boundary"]["live_hot_path_dependency_created"] is False for row in _rows())
