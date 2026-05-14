import copy
import json
from pathlib import Path

from tools import validate_owner_dashboard_approval_menu_schema as gate


REPO_ROOT = Path(".")
PR96_BRANCH = "pr96-owner-dashboard-approval-static-screen-contract"
FEATURE_BRANCH = "feature/non-downstream-validation"
_REPORT_CACHE: dict | None = None


def _clear_branch_context_env(monkeypatch) -> None:
    for env_name in ("GITHUB_ACTIONS", *gate.BRANCH_CONTEXT_ENV_CANDIDATES):
        monkeypatch.delenv(env_name, raising=False)


def _mock_git_branch(monkeypatch, branch: str, *, detached: bool = False) -> None:
    original_git_stdout = gate._git_stdout

    def fake_git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, "" if detached else branch, ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, "HEAD" if detached else branch, ""
        return original_git_stdout(repo_root, args)

    monkeypatch.setattr(gate, "_git_stdout", fake_git_stdout)


def _write_file(root: Path, relative_path: Path) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("static artifact\n", encoding="utf-8")


def _forbidden_artifact_failure(relative_path: Path) -> str:
    return f"PR95 must not create forbidden later/runtime artifact: {relative_path.as_posix()}"


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert gate.main([]) == 0
        _REPORT_CACHE = json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _packet() -> dict:
    return _report()["owner_dashboard_approval_menu_schema_packet"]


def _options() -> list[dict]:
    return _packet()["menu_options"]


def _option(option_id: str) -> dict:
    for item in _options():
        if item["option_id"] == option_id:
            return item
    raise AssertionError(f"missing option: {option_id}")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _write_registry(tmp_path: Path, registry: dict) -> Path:
    path = tmp_path / "mutated_owner_dashboard_approval_menu_schema.json"
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _validate_mutated_registry(tmp_path: Path, registry: dict) -> gate.ValidationResult:
    return gate.validate(
        repo_root=REPO_ROOT,
        registry_path=_write_registry(tmp_path, registry),
        output_path=tmp_path / "OwnerDashboardApprovalMenuSchema.report.json",
    )


def test_pr95_metadata_and_owner_prompt_semantic_task_id_are_verified():
    report = _report()

    assert report["roadmap_pr_label"] == "PR #95"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == "owner prompt semantic task controls"
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert report["upstream_pr94_report_marker"] == "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"


def test_owner_dashboard_approval_menu_schema_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["menu_option_count"] == second_report["menu_option_count"]
    assert first_report["owner_dashboard_approval_menu_schema_packet"]["canonical_option_order"] == (
        second_report["owner_dashboard_approval_menu_schema_packet"]["canonical_option_order"]
    )


def test_all_required_owner_prompt_menu_concepts_exist_with_explicit_canonical_mapping():
    packet = _packet()

    assert packet["required_prompt_concept_order"] == list(gate.REQUIRED_PROMPT_CONCEPT_ORDER)
    assert packet["canonical_option_order"] == list(gate.CANONICAL_OPTION_ORDER)
    assert packet["prompt_concept_to_option_id_map"] == _registry()["prompt_concept_to_option_id_map"]
    assert packet["canonical_scope_substitution_policy"]["APPLY_TO_ROW"]["option_id"] == (
        "APPLY_TO_ONE_ROW"
    )
    assert packet["canonical_scope_substitution_policy"]["APPLY_TO_FAMILY"]["option_id"] == (
        "APPLY_TO_PARAMETER_FAMILY"
    )
    assert packet["silent_alias_count"] == 0
    assert packet["unknown_option_id_count"] == 0
    assert packet["duplicate_option_id_count"] == 0


def test_menu_options_have_expected_option_class_mapping():
    report_mapping = _packet()["option_class_mapping"]

    for option_id, expected_class in gate.OPTION_CLASS_BY_ID.items():
        assert report_mapping[option_id] == expected_class
    assert {
        option["option_class"]
        for option in _options()
    } == set(gate.OPTION_CLASS_ORDER)


def test_every_option_is_static_metadata_only_with_explicit_blocked_effects():
    for option in _options():
        assert option["handoff_only_flag"] is True
        assert option["requires_owner_identity_flag"] is True
        assert option["blocked_effects"] == list(gate.BLOCKED_EFFECTS)
        for field in gate.FALSE_OPTION_FIELDS:
            assert option[field] is False

    for field in gate.NO_AUTHORITY_FLAG_FIELDS:
        assert _packet()[field] is False
        assert _report()[field] is False
    for field in gate.ZERO_COUNT_FIELDS:
        assert _packet()[field] == 0
        assert _report()[field] == 0


def test_approve_with_override_is_internal_policy_metadata_only():
    option = _option("APPROVE_WITH_OVERRIDE")

    assert option["authority_class"] == (
        "OWNER_MENU_OVERRIDE_METADATA_ONLY_INTERNAL_QTT_WORKFLOW_NOT_EXTERNAL_FACT"
    )
    assert option["requires_owner_rationale_flag"] is True
    assert option["creates_source_fact_flag"] is False
    assert option["creates_runtime_cash_flag"] is False
    assert option["creates_receipt_flag"] is False


def test_waive_requirement_and_set_owner_value_are_internal_policy_metadata_only():
    for option_id in ["WAIVE_REQUIREMENT", "SET_OWNER_APPROVED_VALUE"]:
        option = _option(option_id)
        assert option["authority_class"] == (
            "OWNER_MENU_REQUIREMENT_VALUE_METADATA_ONLY_INTERNAL_POLICY_NOT_RECEIPT"
        )
        assert option["creates_receipt_flag"] is False
        assert option["creates_source_fact_flag"] is False

    assert _option("SET_OWNER_APPROVED_VALUE")["requires_owner_approved_value_flag"] is True


def test_approve_live_use_creates_no_live_canary_order_or_routing_authority():
    option = _option("APPROVE_LIVE_USE")

    assert option["creates_live_authority_flag"] is False
    assert option["creates_order_authority_flag"] is False
    for blocked in [
        "LIVE_AUTHORITY_CREATION",
        "CANARY_ELIGIBILITY_CREATION",
        "ORDER_SUBMISSION",
        "ORDER_CANCELLATION",
        "ORDER_REDUCTION",
        "ORDER_CLOSE",
        "LIVE_ROUTING",
    ]:
        assert blocked in option["blocked_effects"]
    assert _report()["creates_canary_eligibility"] is False
    assert _report()["order_submission_count"] == 0


def test_approve_quantum_backend_is_static_metadata_only():
    option = _option("APPROVE_QUANTUM_BACKEND")

    assert option["creates_optimizer_execution_flag"] is False
    assert option["creates_quantum_backend_execution_flag"] is False
    for blocked in [
        "QUANTUM_OPTIMIZER_EXECUTION",
        "QUANTUM_BACKEND_EXECUTION",
        "QUANTUM_SIMULATOR_EXECUTION",
        "QUANTUM_PROVIDER_CALL",
        "QUANTUM_ADVANTAGE_EVIDENCE_CREATION",
        "ORDER_SUBMISSION",
    ]:
        assert blocked in option["blocked_effects"]
    assert _report()["quantum_backend_execution_count"] == 0
    assert _report()["quantum_simulator_execution_count"] == 0
    assert _report()["quantum_provider_call_count"] == 0
    assert _report()["creates_quantum_advantage_evidence"] is False


def test_scope_options_have_explicit_allowed_target_scope_classes_and_no_mutation():
    expected = {
        "APPLY_TO_ONE_ROW": ["ROW"],
        "APPLY_TO_PARAMETER_FAMILY": ["PARAMETER_FAMILY"],
        "APPLY_TO_AGENT": ["AGENT"],
        "APPLY_GLOBALLY": ["GLOBAL"],
    }

    for option_id, scopes in expected.items():
        option = _option(option_id)
        assert option["option_class"] == "TARGET_SCOPE_OPTIONS"
        assert option["allowed_target_scope_classes"] == scopes
        assert option["creates_global_mutation_flag"] is False
    assert "GLOBAL_MUTATION" in _option("APPLY_GLOBALLY")["blocked_effects"]


def test_pr95_does_not_create_pr96_screen_runtime_receipts_or_atomicrows_authority():
    report = _report()

    branch_context = gate._current_branch_context(REPO_ROOT)
    downstream_pr96_or_later = gate._downstream_or_main_validation_branch_allowed(
        branch_context.branch
    )
    runtime_or_forbidden_paths = [
        *gate.FORBIDDEN_RUNTIME_PATHS,
        gate.CANONICAL_BUNDLE_JSONL,
        gate.CANONICAL_BUNDLE_SHA256,
    ]
    for path in runtime_or_forbidden_paths:
        assert not (REPO_ROOT / path).exists(), path
    if not downstream_pr96_or_later:
        for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
            assert not (REPO_ROOT / path).exists(), path

    assert report["creates_pr96_static_screen_contract"] is False
    assert report["creates_runtime_dashboard_service"] is False
    assert report["creates_dashboard_runtime_ui"] is False
    assert report["creates_telegram_runtime"] is False
    assert report["executes_owner_decision"] is False
    assert report["creates_owner_approval_receipt"] is False
    assert report["creates_owner_override_receipt"] is False
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False


def test_pr96_static_files_allowed_on_local_pr96_downstream_branch(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR96_BRANCH)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert failures == []


def test_pr96_static_files_allowed_on_main_cumulative_context(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, "main")
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert failures == []


def test_pr96_static_files_allowed_in_github_push_main_ref_name_context(
    tmp_path,
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    _mock_git_branch(monkeypatch, "ignored", detached=True)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert failures == []


def test_pr96_static_files_allowed_in_github_push_main_ref_context(
    tmp_path,
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    _mock_git_branch(monkeypatch, "ignored", detached=True)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert failures == []


def test_pr96_static_files_allowed_in_github_actions_detached_head_context(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", PR96_BRANCH)
    monkeypatch.setenv("GITHUB_REF_NAME", "97/merge")
    _mock_git_branch(monkeypatch, PR96_BRANCH, detached=True)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert failures == []


def test_pr96_static_files_blocked_on_non_downstream_branch(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, FEATURE_BRANCH)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        assert _forbidden_artifact_failure(path) in failures


def test_pr96_static_files_blocked_on_pr95_same_pr_branch(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, gate.TARGET_BRANCH)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        assert _forbidden_artifact_failure(path) in failures


def test_runtime_paths_remain_blocked_on_pr96_downstream_branch(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR96_BRANCH)
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)
    for path in gate.FORBIDDEN_RUNTIME_PATHS:
        (tmp_path / path).mkdir(parents=True, exist_ok=True)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    for path in gate.FORBIDDEN_RUNTIME_PATHS:
        assert _forbidden_artifact_failure(path) in failures
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        assert _forbidden_artifact_failure(path) not in failures


def test_runtime_paths_remain_blocked_on_main_cumulative_context(tmp_path, monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, "main")
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        _write_file(tmp_path, path)
    for path in gate.FORBIDDEN_RUNTIME_PATHS:
        (tmp_path / path).mkdir(parents=True, exist_ok=True)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    for path in gate.FORBIDDEN_RUNTIME_PATHS:
        assert _forbidden_artifact_failure(path) in failures
    for path in gate.PR96_STATIC_SCREEN_CONTRACT_PATHS:
        assert _forbidden_artifact_failure(path) not in failures


def test_atomicrows_bundle_and_hash_remain_blocked_on_pr96_downstream_branch(
    tmp_path,
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, PR96_BRANCH)
    _write_file(tmp_path, gate.CANONICAL_BUNDLE_JSONL)
    _write_file(tmp_path, gate.CANONICAL_BUNDLE_SHA256)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert (
        "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_ATOMICROWS_BUNDLE: "
        f"{gate.CANONICAL_BUNDLE_JSONL.as_posix()} must be absent"
    ) in failures
    assert (
        "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_ATOMICROWS_SHA: "
        f"{gate.CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
    ) in failures


def test_atomicrows_bundle_and_hash_remain_blocked_on_main_cumulative_context(
    tmp_path,
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    _mock_git_branch(monkeypatch, "main")
    _write_file(tmp_path, gate.CANONICAL_BUNDLE_JSONL)
    _write_file(tmp_path, gate.CANONICAL_BUNDLE_SHA256)

    failures = gate.validate_filesystem_boundaries(tmp_path)

    assert (
        "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_ATOMICROWS_BUNDLE: "
        f"{gate.CANONICAL_BUNDLE_JSONL.as_posix()} must be absent"
    ) in failures
    assert (
        "OWNER_DASHBOARD_APPROVAL_MENU_BLOCKED_ATOMICROWS_SHA: "
        f"{gate.CANONICAL_BUNDLE_SHA256.as_posix()} must be absent"
    ) in failures


def test_main_context_stdout_has_only_success_marker(tmp_path, monkeypatch, capsys):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    _mock_git_branch(monkeypatch, "ignored", detached=True)

    assert gate.main(["--out", str(tmp_path / "report.json")]) == 0

    output_lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert output_lines == [gate.SUCCESS_MARKER]


def test_pr95_creates_no_source_connector_runtime_cash_replay_paper_optimizer_profit_or_claims():
    report = _report()

    assert report["retrieves_source"] is False
    assert report["accepts_source"] is False
    assert report["creates_accepted_source_packet"] is False
    assert report["creates_connector_semantic_binding"] is False
    assert report["fetches_private_state"] is False
    assert report["creates_runtime_cash_receipt"] is False
    assert report["executes_replay"] is False
    assert report["executes_paper"] is False
    assert report["creates_replay_paper_result"] is False
    assert report["executes_optimizer"] is False
    assert report["executes_classical_optimizer"] is False
    assert report["executes_quantum_optimizer"] is False
    assert report["creates_profit_evidence"] is False
    assert report["claims_latency_superiority"] is False
    assert report["claims_execution_superiority"] is False


def test_missing_required_option_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["menu_options"] = [
        option for option in registry["menu_options"] if option["option_id"] != "APPROVE"
    ]

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("missing required option_id values: APPROVE" in failure for failure in result.failures)


def test_duplicate_option_id_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    duplicate = copy.deepcopy(registry["menu_options"][0])
    duplicate["canonical_sort_index"] = 999
    registry["menu_options"].append(duplicate)

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("duplicate option_id values: APPROVE" in failure for failure in result.failures)


def test_unknown_option_id_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["menu_options"][0]["option_id"] = "UNKNOWN_OWNER_MENU_OPTION"

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("unknown option_id values: UNKNOWN_OWNER_MENU_OPTION" in failure for failure in result.failures)


def test_runtime_effect_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["menu_options"][0]["creates_runtime_effect_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_runtime_effect_flag" in failure for failure in result.failures)


def test_receipt_creation_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["menu_options"][1]["creates_receipt_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_receipt_flag" in failure for failure in result.failures)


def test_source_connector_runtime_cash_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["menu_options"][0]["creates_source_fact_flag"] = True
    registry["menu_options"][0]["creates_connector_semantic_flag"] = True
    registry["menu_options"][0]["creates_runtime_cash_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_source_fact_flag" in failure for failure in result.failures)
    assert any("creates_connector_semantic_flag" in failure for failure in result.failures)
    assert any("creates_runtime_cash_flag" in failure for failure in result.failures)


def test_live_order_authority_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    live = next(item for item in registry["menu_options"] if item["option_id"] == "APPROVE_LIVE_USE")
    live["creates_live_authority_flag"] = True
    live["creates_order_authority_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_live_authority_flag" in failure for failure in result.failures)
    assert any("creates_order_authority_flag" in failure for failure in result.failures)


def test_quantum_backend_execution_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    quantum = next(
        item for item in registry["menu_options"] if item["option_id"] == "APPROVE_QUANTUM_BACKEND"
    )
    quantum["creates_quantum_backend_execution_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_quantum_backend_execution_flag" in failure for failure in result.failures)


def test_apply_globally_mutation_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    global_option = next(
        item for item in registry["menu_options"] if item["option_id"] == "APPLY_GLOBALLY"
    )
    global_option["creates_global_mutation_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_global_mutation_flag" in failure for failure in result.failures)


def test_atomicrows_bundle_or_hash_claim_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["no_authority_flags"]["creates_atomicrows_bundle"] = True
    registry["no_authority_flags"]["creates_atomicrows_bundle_sha256"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_atomicrows_bundle" in failure for failure in result.failures)
    assert any("creates_atomicrows_bundle_sha256" in failure for failure in result.failures)
