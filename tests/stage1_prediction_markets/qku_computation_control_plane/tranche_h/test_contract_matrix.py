from __future__ import annotations

from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import tempfile

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
    SourcePolicyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    ST12HControlCaseV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    serialize_st12h_contract_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    ST12H_SOURCE_BINDINGS,
    ST12HSourceBindingV1,
    _observe_st12h_source_binding_v1,
    _validate_st12h_source_currentness_receipt_v1,
    validate_st12h_source_binding_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12H_CONTROL_CASES,
    ST12H_SEMANTIC_TEST_IDENTITIES,
    validate_st12h_control_case_v1,
    validate_st12h_serialized_contracts_v1,
)
from tools.independent_validate_qku_computation_control_plane import (
    _exercise_st12h_grouped_defect_injections_v1,
)


def _domain_cases(domain: str) -> tuple[ST12HControlCaseV1, ...]:
    return tuple(case for case in ST12H_CONTROL_CASES if case.domain == domain)


def _write_st12h_detached_source_fixture(root: Path) -> None:
    sources = {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/validation.py": """
ST12H_CONTROL_CASES = ()
ST12H_EXECUTABLE_CONTROL_ADAPTERS = {}
def validate_st12h_control_case_v1(case):
    return case
def validate_st12h_parameter_consumption_v1():
    return None
""".strip(),
        "tools/run_validation_gates.py": """
from tools.validation_scope_registry import build_st12h_validation_commands
def _execution_command_with_qku_root_importlib(command):
    return list(command)
""".strip(),
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/errors.py": """
class ReasonCode:
    KILL_OR_SUBMIT_DISABLED = "ST12D_KILL_OR_SUBMIT_DISABLED"
    CONTEXT_SCOPE_MISMATCH = "ST12E_CONTEXT_SCOPE_MISMATCH"
""".strip(),
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/models.py": """
class NoEffectFlagsV1:
    provider_connection_allowed: bool = False
    private_state_read_allowed: bool = False
    replay_or_paper_execution_allowed: bool = False
    llm_inference_allowed: bool = False
    qpu_execution_allowed: bool = False
    mode_or_allow_activation_allowed: bool = False
    order_release_allowed: bool = False
    capital_mutation_allowed: bool = False
""".strip(),
    }
    for relative_path, content in sources.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + "\n", encoding="utf-8")
    phase_lines = "\n".join(
        f"          - phase: residual-phase-{index:02d}" for index in range(1, 14)
    )
    workflow = f"""
jobs:
  validation_shards:
    strategy:
      matrix:
        include:
{phase_lines}
    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14.6'
      - run: |
          python -m pip install pytest==9.1.1
  validation:
    needs:
      - validation_shards
    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14.6'
""".strip()
    workflow_path = root / ".github/workflows/qtt_validation.yml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(workflow + "\n", encoding="utf-8")


def _assert_st12h_source_portability_and_dispositions() -> None:
    assert tuple(field.name for field in fields(ST12HSourceBindingV1)) == (
        "source_id",
        "source_name",
        "source_class",
        "authority_class",
        "source_locator",
        "publication_or_version",
        "observed_at",
        "currentness_state",
        "rights_state",
        "recheck_trigger",
        "codex_research_required",
    )
    evaluation_date = datetime.now(UTC).date()
    receipts = []
    for binding in ST12H_SOURCE_BINDINGS:
        assert validate_st12h_source_binding_v1(
            binding,
            evaluated_at=evaluation_date,
        ) is None
        receipts.append(
            _observe_st12h_source_binding_v1(
                binding,
                evaluated_at=evaluation_date,
            )
        )
    assert tuple(receipt.terminal_state for receipt in receipts) == (
        "CURRENT_BY_STABLE_VERSION",
        "CURRENT_BY_STABLE_VERSION",
        "PROVENANCE_ONLY_PINNED",
        "SUPERSEDED_BY_CURRENT_REPOSITORY_CUSTODY",
        "CURRENT_BY_TRACKED_REPOSITORY_RECHECK",
        "CURRENT_BY_TRACKED_REPOSITORY_RECHECK",
        "CURRENT_BY_STABLE_VERSION",
        "CURRENT_BY_STABLE_VERSION",
        "CURRENT_BY_TRACKED_REPOSITORY_RECHECK",
    )
    mutable = receipts[4]
    with pytest.raises(SourcePolicyError) as stale:
        _validate_st12h_source_currentness_receipt_v1(
            replace(
                mutable,
                valid_until=evaluation_date - timedelta(days=1),
            ),
            evaluated_at=evaluation_date,
        )
    assert stale.value.reason_code is ReasonCode.SOURCE_EPOCH_STALE
    with pytest.raises(SourcePolicyError) as conflict:
        validate_st12h_source_binding_v1(
            replace(
                ST12H_SOURCE_BINDINGS[2],
                authority_class="CURRENT_REPOSITORY_IMPLEMENTATION_AUTHORITY",
            ),
            evaluated_at=evaluation_date,
        )
    assert conflict.value.reason_code is ReasonCode.SOURCE_CONFLICT
    with tempfile.TemporaryDirectory(prefix="st12h-source-detached-") as root_text:
        root = Path(root_text)
        _write_st12h_detached_source_fixture(root)
        selected = tuple(
            ST12H_SOURCE_BINDINGS[index] for index in (3, 4, 5, 8)
        )
        detached = tuple(
            _observe_st12h_source_binding_v1(
                binding,
                evaluated_at=evaluation_date,
                repo_root=root,
            )
            for binding in selected
        )
        metadata = root / ".git"
        metadata.mkdir()
        (metadata / "HEAD").write_text(
            "ref: refs/heads/unrelated-symbolic-context\n",
            encoding="utf-8",
        )
        symbolic = tuple(
            _observe_st12h_source_binding_v1(
                binding,
                evaluated_at=evaluation_date,
                repo_root=root,
            )
            for binding in selected
        )
        assert detached == symbolic
    source_text = Path(
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py"
    ).read_text(encoding="utf-8")
    assert '".' + 'git"' not in source_text
    assert '".' + 'codex_inputs' not in source_text
    assert "ci_branch_context" not in source_text


def _assert_certified_control(case: ST12HControlCaseV1) -> None:
    receipt = validate_st12h_control_case_v1(case)
    assert receipt.case_id == case.case_id
    assert receipt.terminal_state == case.expected_terminal_state
    assert receipt.reason_code_or_none is case.expected_reason_code
    assert receipt.no_effect_flags is NO_EFFECTS_V1
    assert tuple(case.required_receipt_fields)
    payload_names = next(
        field
        for field in receipt.control_payload.fields
        if field.name == "required_receipt_fields"
    )
    assert payload_names.value == ",".join(case.required_receipt_fields)
    assertion_values = {
        field.name: field.value for field in receipt.assertion_results.fields
    }
    assert assertion_values["observed_valid_terminal_state"] == (
        case.expected_terminal_state
    )
    assert assertion_values["observed_mutation_reason_code"] == (
        case.expected_reason_code.value
        if case.expected_reason_code is not None
        else "EXPLICIT_ABSENCE_UNREGISTERED_EXCEPTION"
    )
    assert assertion_values["owner_valid_call_count"] == 1
    assert assertion_values["owner_mutation_call_count"] == 1
    assert assertion_values["required_fields_extracted"] is True
    assert assertion_values["no_effect_assertion_passed"] is True
    assert "expected_terminal_state" not in assertion_values
    assert "expected_reason_code" not in assertion_values

    serialized = serialize_st12h_contract_v1(
        receipt,
        binding_id="ST12H-SERIALIZED-CONTRACT::03",
    )
    payload = json.loads(serialized)
    assert validate_st12h_serialized_contracts_v1(
        binding_id="ST12H-SERIALIZED-CONTRACT::03",
        payload=payload,
    ) == ()

    mutated = replace(case, expected_terminal_state="FORGED_EXPECTED_RESULT")
    with pytest.raises(ContractValidationError) as captured:
        validate_st12h_control_case_v1(mutated)
    assert captured.value.reason_code is ReasonCode.VALIDATION_FAILED
    assert len(ST12H_SEMANTIC_TEST_IDENTITIES) == 42
    assert len(set(ST12H_SEMANTIC_TEST_IDENTITIES)) == 42
    if case.case_id == ST12H_CONTROL_CASES[0].case_id:
        defect_injections = _exercise_st12h_grouped_defect_injections_v1()
        assert len(defect_injections) == 19
        assert all(defect_injections.values())


@pytest.mark.parametrize("case", _domain_cases("accounting"))
def test_st12h_accounting_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("execution"))
def test_st12h_execution_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("llm"))
def test_st12h_llm_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("operations"))
def test_st12h_operations_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("security"))
def test_st12h_security_control_matrix(case: ST12HControlCaseV1) -> None:
    _assert_certified_control(case)


@pytest.mark.parametrize("case", _domain_cases("source"))
def test_st12h_source_control_matrix(case: ST12HControlCaseV1) -> None:
    if case.case_id == _domain_cases("source")[0].case_id:
        _assert_st12h_source_portability_and_dispositions()
    _assert_certified_control(case)
