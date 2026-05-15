import copy
import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_exact_row_expansion_manifest as gate


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_CONFIG)


def _load_schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)


def _load_pr97_plan() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.PR97_PLAN)


def _load_pr97_report() -> dict:
    return gate.load_json(REPO_ROOT / gate.PR97_REPORT)


def _load_pr97_schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.PR97_SCHEMA)


def _validated_report() -> dict:
    result = gate.validate(repo_root=REPO_ROOT)
    assert result.ok, result.failures
    assert result.report is not None
    return result.report


def test_static_yaml_validates_against_schema_and_validator_emits_marker(capsys):
    config = _load_config()
    schema = _load_schema()
    derivation = gate.derive_pr97_explicit_distribution(
        _load_pr97_plan(), _load_pr97_report(), _load_pr97_schema()
    )

    assert gate.validate_config_payload(config, schema, derivation) == []

    exit_code = gate.main(["--repo-root", str(REPO_ROOT)])

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_report_is_deterministic_and_blocked_pending_owner_distribution():
    report = _validated_report()
    first = gate.serialize_report(report)
    second = gate.serialize_report(json.loads(first))

    assert first == second
    assert report["generated_at_utc"] == "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
    assert report["report_type"] == "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_REPORT"
    assert report["artifact_id"] == "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST"
    assert report["validation_result"] == "PASS_BLOCKED_EXPECTED"
    assert report["validator_stdout_marker"] == gate.SUCCESS_MARKER
    assert report["manifest_created"] is True
    assert report["exact_distribution_ready"] is False
    assert report["owner_distribution_required"] is True
    assert report["distribution_authority"] == "OWNER_APPROVAL_REQUIRED"
    assert report["owner_required_decision"] == "EXACT_15_FAMILY_ROW_COUNT_DISTRIBUTION"
    assert report["family_counts_sum"] is None
    assert report["row_ranges_contiguous"] is None
    assert report["final_row_index"] is None


def test_target_family_order_future_files_and_forbidden_artifacts_remain_absent():
    config = _load_config()
    report = _validated_report()

    assert config["target_total_row_count"] == 4183
    assert report["target_total_row_count"] == 4183
    assert config["family_count_total"] == 15
    assert report["family_count_total"] == 15
    assert [family["family_slug"] for family in config["families"]] == list(
        gate.REQUIRED_FAMILY_SLUGS
    )
    assert [family["family_slug"] for family in report["families"]] == list(
        gate.REQUIRED_FAMILY_SLUGS
    )
    assert [family["future_exact_row_source_file"] for family in config["families"]] == list(
        gate.REQUIRED_EXACT_ROW_SOURCE_FILES
    )
    assert [family["future_source_blueprint_file"] for family in config["families"]] == list(
        gate.REQUIRED_SOURCE_BLUEPRINT_FILES
    )
    for future_file in gate.REQUIRED_EXACT_ROW_SOURCE_FILES:
        assert not (REPO_ROOT / future_file).exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
    assert report["forbidden_artifacts_absent"] == {
        "AtomicRows.bundle.jsonl": True,
        "AtomicRows.bundle.sha256": True,
        "exact_row_sources": True,
    }


def test_owner_process_approval_is_limited_and_no_guesswork_is_allowed():
    config = _load_config()
    report = _validated_report()
    owner_process = config["owner_process_approval"]
    distribution = config["distribution_authority"]

    assert owner_process["repair_pr_b_process_approved"] is True
    assert owner_process["owner_approves_exact_counts_now"] is False
    assert owner_process["codex_may_use_pr97_explicit_counts_only"] is True
    for field in (
        "codex_may_invent_counts",
        "codex_may_estimate_counts",
        "codex_may_balance_counts",
        "codex_may_optimize_counts",
        "codex_may_infer_counts_from_family_names",
    ):
        assert owner_process[field] is False
        assert distribution[field] is False
        assert report[field] is False
    assert distribution["source"] == "OWNER_APPROVAL_REQUIRED"
    assert distribution["source_pointer"] is None
    assert distribution["owner_required_decision"] == (
        "EXACT_15_FAMILY_ROW_COUNT_DISTRIBUTION"
    )
    assert distribution["no_guesswork"] is True
    assert all(
        family["count_authority"]
        in {"DERIVED_FROM_PR97_EXPLICIT_DISTRIBUTION", "OWNER_APPROVAL_REQUIRED"}
        for family in config["families"]
    )
    assert all(
        family["target_row_count"] is None
        and family["row_index_start"] is None
        and family["row_index_end"] is None
        for family in config["families"]
    )


def test_pr97_current_distribution_is_absent_but_synthetic_explicit_counts_derive_ranges():
    current = gate.derive_pr97_explicit_distribution(
        _load_pr97_plan(), _load_pr97_report(), _load_pr97_schema()
    )
    assert current.validation_result == "PASS_BLOCKED_EXPECTED"
    assert current.explicit_distribution_found is False
    assert current.counts is None

    plan = copy.deepcopy(_load_pr97_plan())
    counts = [1] * 14 + [4169]
    plan["exact_15_family_row_count_distribution"] = [
        {"family_slug": slug, "target_row_count": count}
        for slug, count in zip(gate.REQUIRED_FAMILY_SLUGS, counts)
    ]
    derived = gate.derive_pr97_explicit_distribution(
        plan, _load_pr97_report(), _load_pr97_schema()
    )

    assert derived.validation_result == "PASS_EXACT_DISTRIBUTION_READY"
    assert derived.source == "DERIVED_FROM_PR97_EXPLICIT_DISTRIBUTION"
    assert derived.family_counts_sum == 4183
    assert derived.row_ranges_contiguous is True
    assert derived.final_row_index == 4183
    assert derived.ranges[gate.REQUIRED_FAMILY_SLUGS[0]] == (1, 1)
    assert derived.ranges[gate.REQUIRED_FAMILY_SLUGS[-1]] == (15, 4183)

    bad_plan = copy.deepcopy(plan)
    bad_plan["exact_15_family_row_count_distribution"][-1]["target_row_count"] = 4168
    failed = gate.derive_pr97_explicit_distribution(
        bad_plan, _load_pr97_report(), _load_pr97_schema()
    )
    assert failed.validation_result == "FAIL"
    assert any("count sum must be 4183" in failure for failure in failed.failures)


def test_subfamily_row_class_doctrine_is_required_and_flat_family_buckets_are_rejected():
    config = _load_config()
    schema = _load_schema()

    assert config["families_are_top_level_buckets_not_parameters"] is True
    assert config["subfamily_row_class_doctrine_required"] is True
    assert config["allowed_subfamily_classes"] == list(gate.ALLOWED_SUBFAMILY_CLASSES)
    assert config["future_exact_row_required_fields"] == list(
        gate.FUTURE_EXACT_ROW_REQUIRED_FIELDS
    )
    assert all(family["subfamily_classes"] for family in config["families"])

    mutated = copy.deepcopy(config)
    mutated["families"][0]["subfamily_classes"] = []
    failures = gate.validate_config_payload(mutated, schema)
    assert any("subfamily_classes" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["families"][1]["count_authority"] = "INVENTED_BY_CODEX"
    failures = gate.validate_config_payload(mutated, schema)
    assert any("count_authority" in failure or "enum" in failure for failure in failures)


def test_upstream_repair_chain_is_preserved():
    report = _validated_report()

    assert report["pr97_expansion_plan_present"] is True
    assert report["pr98_blueprints_are_not_exact_rows"] is True
    assert report["pr99_path_b_remains_current_blocked_state"] is True
    assert report["pr100_sha_freeze_gate_remains_blocked"] is True
    assert report["repair_pr_a_bridge_present"] is True
    assert report["repair_pr_a_bridge_preserved"] is True
    assert report["repair_pr_a_authority_classifier_preserved"] is True
    assert report["repair_pr_a_agent_eligibility_governance_preserved"] is True


def test_quantum_forward_families_are_preserved_without_execution_or_advantage_claims():
    config = _load_config()
    report = _validated_report()
    families = {family["family_slug"]: family for family in config["families"]}

    assert report["quantum_forward_families_preserved"] is True
    for slug, relevance in gate.QUANTUM_RELEVANCE_BY_FAMILY.items():
        family = families[slug]
        assert family["quantum_relevance_class"] == relevance
        assert "QUANTUM_METADATA" in family["subfamily_classes"]
        for field in gate.QUANTUM_FALSE_FIELDS:
            assert family[field] is False
    for slug in (
        "013_quantum_qubo_ising_metadata",
        "014_quantum_qaoa_vqe_annealing_metadata",
        "015_quantum_portfolio_hybrid_comparator",
    ):
        assert "QUANTUM_BACKEND_REQUIREMENT" in families[slug]["subfamily_classes"]
    assert report["quantum_backend_authority_created"] is False
    assert report["quantum_advantage_evidence_created"] is False


def test_family_009_agent_governance_is_primary_and_deny_by_default():
    config = _load_config()
    report = _validated_report()
    family = config["families"][8]

    assert family["family_slug"] == "009_lifecycle_agent_binding"
    assert (
        family["agent_governance_relevance_class"]
        == "PRIMARY_AGENT_ROW_ACCESS_GOVERNANCE_FAMILY"
    )
    assert family["future_policy_row_kinds_allowed"] == list(gate.REQUIRED_POLICY_ROW_KINDS)
    assert "AGENT_ACCESS_POLICY" in family["subfamily_classes"]
    assert "FAMILY_ACCESS_POLICY" in family["subfamily_classes"]
    assert family["access_decision_default"] == "DENY"
    for field in gate.AGENT_DENY_FALSE_FIELDS:
        assert family[field] is False
    assert all(
        item["agent_eligibility_governance_required_for_future_rows"] is True
        and item["deny_by_default_agent_access_required"] is True
        for item in config["families"]
    )
    assert report["agent_governance_family_preserved"] is True
    assert report["deny_by_default_agent_access_preserved"] is True


def test_no_authority_or_evidence_is_created_and_master_plan_is_unchanged():
    config = _load_config()
    report = _validated_report()

    for field in gate.NO_AUTHORITY_FALSE_FIELDS:
        assert config["no_authority_created"][field] is False
        assert report[field] is False
    assert report["exact_rows_created"] is False
    assert report["exact_row_source_directory_created"] is False
    assert report["atomicrows_bundle_jsonl_created"] is False
    assert report["atomicrows_bundle_sha256_created"] is False
    assert report["sha_computed"] is False
    assert report["freeze_authority_created"] is False
    assert report["final_readiness_created"] is False
    assert report["master_plan_unchanged"] is True


def test_run_validation_gates_includes_manifest_after_repair_a_and_before_generated_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr97_index = command_names.index(
        "validate_atomicrows_full_bundle_row_expansion_plan.py"
    )
    pr98_index = command_names.index(
        "validate_atomicrows_bundle_row_family_source_files.py"
    )
    pr99_index = command_names.index(
        "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )
    bridge_index = command_names.index(
        "validate_atomicrows_exact_row_authority_classifier_bridge.py"
    )
    manifest_index = command_names.index(
        "validate_atomicrows_exact_row_expansion_manifest.py"
    )
    generated_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert pr97_index < pr98_index < pr99_index < pr100_index < bridge_index
    assert bridge_index < manifest_index < generated_index
    assert commands[manifest_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_exact_row_expansion_manifest.py"),
    ]
