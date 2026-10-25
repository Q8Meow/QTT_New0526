#!/usr/bin/env python3
"""Independent source-registry validation without importing production."""

from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_POLICY = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
    / "source_policy.py"
)
BINDINGS = SOURCE_POLICY.with_name("bindings.py")
SUCCESS_MARKER = "QKU_SOURCE_INDEPENDENTLY_VALIDATED"
ATOMIC_TERMINALS = {
    "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE",
}
CLAIM_BINDING_TERMINALS = {
    "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
}
PRIMARY_SOURCE_TERMINALS = {
    "COMPLETE_PRIMARY_SOURCE",
}


def _literal(tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"missing literal {name}")


def _tuple_literal(tree: ast.Module, name: str) -> tuple[object, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, tuple):
                return value
    raise ValueError(f"missing tuple {name}")


def _source_use_admission_failures_v1(root):
    """Independent structural joins; synthetic behavior is exercised separately."""
    failures = []
    paths = {
        "policy": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
        "service": "src/qtt/service/owner_source_use.py",
        "pretrade": "src/qtt/pretrade/pr169_pretrade1_resolvers.py",
        "native": "src/qtt/service/owner_source_use_windows.py",
    }
    trees = {name: ast.parse((root / path).read_text(encoding="utf-8")) for name, path in paths.items()}

    def method(which, owner, name):
        classes = [n for n in trees[which].body if isinstance(n, ast.ClassDef) and n.name == owner] if owner else [trees[which]]
        found = [n for cls in classes for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name]
        if len(found) != 1:
            raise ValueError("source-use method association missing: " + name)
        return found[0]

    def calls(node):
        return [n for n in ast.walk(node) if isinstance(n, ast.Call)]

    def require_calls(node, expected):
        if not expected <= {ast.unparse(n.func) for n in calls(node)}:
            failures.append("source-use producer/consumer calls incomplete: " + getattr(node, "name", type(node).__name__))

    try:
        complete = method("policy", "SourceUseAuthorityV1", "complete_action_v1")
        require_calls(complete, {"_require_completed_operation_v1", "_verify_source_use_response_v1",
                                "self._commit_verified_action_v1"})
        consumed = [n.lineno for n in ast.walk(complete) if isinstance(n, ast.Assign)
                    and any(ast.unparse(t) == "self._pending" for t in n.targets)
                    and isinstance(n.value, ast.Constant) and n.value.value is None]
        verified = [n.lineno for n in calls(complete) if ast.unparse(n.func) == "_verify_source_use_response_v1"]
        if not consumed or len(verified) != 1 or min(consumed) >= verified[0]:
            failures.append("pending authority is not consumed before real verification")
        commit = method("policy", "SourceUseAuthorityV1", "_commit_verified_action_v1")
        require_calls(commit, {"self._heads_v1", "self._uow.commit_source_use_action_v1",
                              "self._issue_binding_v1", "self.stop_v1"})
        expressions = {ast.unparse(n) for n in ast.walk(commit)}
        if not {"self._valid_completion is pending", "self._counter = proof.counter",
                "originals_before == pending.original_heads"} <= expressions:
            failures.append("verified action lacks cancellation/counter/original association")
        binding = method("policy", "SourceUseAuthorityV1", "_issue_binding_v1")
        require_calls(binding, {"PITSourceCurrentizationReceiptV1", "PITRightsAdmissionReceiptV1",
                               "validate_pit_source_rights_admission_v1"})
        constructors = {ast.unparse(n.func): n for n in calls(binding)}
        if "facts.factual_checked_at_utc" not in ast.unparse(constructors["PITSourceCurrentizationReceiptV1"]):
            failures.append("original factual time is not the PIT source time")
        current = method("policy", "SourceUseAuthorityV1", "_check_binding_v1")
        require_calls(current, {"self._live_v1", "self._heads_v1", "validate_pit_source_rights_admission_v1"})
        required_current = {"binding._root is self._root", "self._bindings.get(id(binding)) is binding",
                            "self._review.record_id == binding._review_event_ref",
                            "self._use.record_id == binding._use_event_ref",
                            "permit._owner is owner"}
        if not required_current <= {ast.unparse(n) for n in ast.walk(current)}:
            failures.append("binding identity/parent currentness checks missing")
        for name in ("_prepare_read_v1", "_recheck_and_charge_v1", "_check_inputs_v1"):
            require_calls(method("policy", "KalshiFeeObservationOwnerV1", name), {"self._authority_guard_v1"})
        pending = method("policy", "KalshiFeeObservationOwnerV1", "_require_pending_v1")
        if "prepared.originating_thread is current_thread()" not in {ast.unparse(n) for n in ast.walk(pending)}:
            failures.append("request start lacks original thread association")
        direct = method("pretrade", None, "compose_kalshi_observed_fee_scenario_cashflows_v1")
        require_calls(direct, {"source_owner._check_inputs_v1", "source_owner._publication_fence_v1",
                              "compose_kalshi_quadratic_taker_buy_yes_cashflows_v1"})
        session = method("pretrade", "KalshiFeeScenarioSessionV1", "evaluate")
        fences = [n for n in ast.walk(session) if isinstance(n, ast.With) and any(
            isinstance(item.context_expr, ast.Call) and ast.unparse(item.context_expr.func) == "owner._publication_fence_v1"
            for item in n.items)]
        if len(fences) != 1:
            failures.append("outer session publication fence missing")
        else:
            require_calls(fences[0], {"owner.revoke"})
            if not any(isinstance(n, ast.Return) for n in ast.walk(fences[0])) or not any(
                    isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and n.value.value == "CONSUMED"
                    for n in ast.walk(fences[0])):
                failures.append("successful cleanup/CONSUMED/return are not in the same fence")
        require_calls(method("service", "OwnerSourceUseControllerV1", "complete_action_v1"),
            {"self._authority.complete_action_v1", "KalshiFeeScenarioSessionV1", "session.evaluate", "authority._check_binding_v1"})
        window = method("native", None, "_run_local_window_v1")
        if any(isinstance(node, ast.With)
               and any(ast.unparse(item.context_expr) == "controller._authority._lock" for item in node.items)
               and "set_text" in {ast.unparse(n.func) for n in calls(node)} for node in ast.walk(window)):
            failures.append("native window I/O holds the authority lock")
        display = method("service", "OwnerSourceUseControllerV1", "_display_result_v1")
        exposure = [node for node in ast.walk(display) if isinstance(node, ast.With)
                    and any(ast.unparse(item.context_expr) == "self._authority._lock" for item in node.items)
                    and any(isinstance(n, ast.Assign) and any(ast.unparse(t) == "self._display_model" for t in n.targets)
                            for n in ast.walk(node))]
        if len(exposure) != 1:
            failures.append("closed local display model assignment lacks authority fence")
        prepare = method("policy", "SourceUseAuthorityV1", "prepare_action_v1")
        reservation = {ast.unparse(ast.parse(value, mode="eval").body) for value in (
            "len(rows) + 2 <= 256",
            "sum(len(deterministic_json(row).encode('utf-8')) for row in rows.values()) + 2 * 65536 <= 16 * 1024 * 1024")}
        if not reservation <= {ast.unparse(n) for n in ast.walk(prepare)}:
            failures.append("positive confirmation lacks the fixed count/byte reservation")
    except (KeyError, ValueError) as error:
        failures.append(str(error))
    return failures


def _kalshi_scheduled_scenario_failures_v1(root):
    """AST-only delegation/effect boundary; behavior and review remain separate."""
    failures = []
    source = ast.parse((root / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py").read_text(encoding="utf-8"))
    pretrade = ast.parse((root / "src/qtt/pretrade/pr169_pretrade1_resolvers.py").read_text(encoding="utf-8"))
    selected = {}
    for tree, names in ((source, {
        "KalshiScheduledFeeStateV1", "_kalshi_scheduled_utc_v1", "_kalshi_scheduled_clocks_v1",
        "_kalshi_scheduled_context_v1", "_kalshi_scheduled_state_snapshot_v1",
        "resolve_kalshi_scheduled_fee_scenario_v1",
    }), (pretrade, {"KalshiScheduledTakerBuyYesFillV1", "compose_kalshi_scheduled_fee_scenario_cashflows_v1"})):
        for name in names:
            found = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name]
            if len(found) != 1:
                failures.append("scheduled scenario symbol missing/duplicated: " + name)
            else:
                selected[name] = found[0]
    allowed = set(selected) | {
        "dataclass", "type", "len", "getattr", "tuple", "sorted", "zip", "enumerate", "timedelta",
        "_native_ident", "_native_require", "PointInTimeClocksV1", "ComputationContextKeyV1",
        "KalshiQuadraticSeriesFeeCandidateV1", "KalshiQuadraticTakerBuyYesFillV1",
        "ContractValidationError", "PointInTimeError", "SourcePolicyError", "NumericDomainError",
        "PointInTimePolicyV1.validate", "local.assert_fresh", "object.__setattr__", "values.items",
        "selected.append", "covering.append", "local_fills.append", "Fraction", "_kalshi_bounded_fraction",
        "kalshi_quadratic_taker_buy_yes_input_v1", "compose_kalshi_conditional_cashflows_v1",
    }
    for name, node in selected.items():
        for child in ast.walk(node):
            if isinstance(child, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.AsyncFunctionDef)):
                failures.append("scheduled scenario effect/import boundary: " + name)
            if isinstance(child, ast.Call) and ast.unparse(child.func) not in allowed:
                failures.append("scheduled scenario unapproved call: " + ast.unparse(child.func))
            if isinstance(child, ast.Attribute) and isinstance(child.ctx, (ast.Store, ast.Del)):
                failures.append("scheduled scenario external mutation: " + name)
            if isinstance(child, ast.Call) and ast.unparse(child.func) == "object.__setattr__":
                if not (isinstance(node, ast.ClassDef) and len(child.args) == 3
                        and ast.unparse(child.args[0]) == "self"
                        and isinstance(child.args[1], ast.Constant) and child.args[1].value in {"fill", "clocks"}):
                    failures.append("scheduled scenario unexpected attribute mutation: " + name)
    for name, required in (
        ("_kalshi_scheduled_context_v1", {"ComputationContextKeyV1", "local.assert_fresh"}),
        ("resolve_kalshi_scheduled_fee_scenario_v1", {"PointInTimePolicyV1.validate"}),
        ("compose_kalshi_scheduled_fee_scenario_cashflows_v1", {
            "resolve_kalshi_scheduled_fee_scenario_v1", "kalshi_quadratic_taker_buy_yes_input_v1",
            "compose_kalshi_conditional_cashflows_v1",
        }),
    ):
        calls = [n for n in ast.walk(selected[name]) if isinstance(n, ast.Call)] if name in selected else []
        for target in required:
            found = [n for n in calls if ast.unparse(n.func) == target]
            if len(found) != 1:
                failures.append("scheduled scenario delegation missing/duplicated: " + target)
            elif target == "PointInTimePolicyV1.validate":
                keywords = {k.arg: ast.unparse(k.value) for k in found[0].keywords}
                if keywords != {"receipt_id": "row.state_ref", "field_class": "PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT",
                                "clocks": "row.clocks", "context": "local_context"}:
                    failures.append("scheduled scenario central clock policy association changed")
    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(_source_use_admission_failures_v1(REPO_ROOT))
    failures.extend(_kalshi_scheduled_scenario_failures_v1(REPO_ROOT))
    tree = ast.parse(
        SOURCE_POLICY.read_text(encoding="utf-8"),
        filename=str(SOURCE_POLICY),
    )
    try:
        source_rows = json.loads(_literal(tree, "_CERTIFIED_SOURCE_ROWS_JSON"))
        overlays = json.loads(
            _literal(tree, "_CURRENTIZATION_OVERLAY_ROWS_JSON")
        )
        st12f_overlays = _tuple_literal(tree, "_ST12F_SOURCE_OVERLAY_ROWS_V1")
        st12f_conflicts = _tuple_literal(tree, "_ST12F_SOURCE_CONFLICT_ROWS_V1")
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if len(source_rows) + len(st12f_overlays) != 35 or len(st12f_conflicts) != 7:
        failures.append("ST12-F terminal source closure is not exact 35 decisions and seven conflicts")
    if len(source_rows) != 29:
        failures.append(f"certified source denominator={len(source_rows)}, expected=29")
    if len(overlays) != 7:
        failures.append(f"overlay denominator={len(overlays)}, expected=7")
    if len({row["source_state_id"] for row in source_rows}) != 29:
        failures.append("certified source ids are not unique")
    if len({row["currentization_id"] for row in overlays}) != 7:
        failures.append("overlay ids are not unique")
    for row in source_rows:
        certified = row.get("certified_step11_row", {})
        specification = row.get("step12_implementation_specification", {})
        atomic_facts = certified.get("atomic_fact_results", ())
        if (
            not isinstance(row.get("source_state_id"), str)
            or not row["source_state_id"]
            or not isinstance(row.get("stable_source_identity"), str)
            or not row["stable_source_identity"]
            or row.get("provider_connection_or_effect_authorized") is not False
            or row.get("runtime_online_research_allowed") is not False
            or row.get("codex_online_research_allowed") is not False
            or row.get("research_completeness_state")
            not in CLAIM_BINDING_TERMINALS
            or not isinstance(certified, dict)
            or certified.get("research_completeness_state")
            not in PRIMARY_SOURCE_TERMINALS
            or certified.get("active_runtime_authority") is not False
            or certified.get("all_atomic_facts_pass") is not True
            or certified.get("conflict_resolution_state")
            != "TERMINAL_OWNER_SIDE_SOURCE_CONFLICT_RESOLUTION_COMPLETE"
            or not isinstance(atomic_facts, list)
            or not atomic_facts
            or any(
                not isinstance(fact, dict)
                or not isinstance(fact.get("atomic_fact_id"), str)
                or not fact["atomic_fact_id"]
                or fact.get("result") not in ATOMIC_TERMINALS
                for fact in atomic_facts
            )
            or not isinstance(specification, dict)
            or not specification.get("implementation_binding")
            or not specification.get("failure_reason_code")
        ):
            failures.append(
                f"certified source row is not terminal and effect-free: "
                f"{row.get('source_state_id')!r}"
            )
    if len({row["stable_source_identity"] for row in source_rows}) != 29:
        failures.append("certified stable source identities are not unique")
    adversarial_atomic = (
        "BYPASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE",
        "NOT_PASS",
        "PASSIVE",
        "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE_SUFFIX",
    )
    adversarial_complete = (
        "COMPLETE_",
        "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING_SUFFIX",
        "COMPLETE_PRIMARY_SOURCE_SUFFIX",
    )
    if any(value in ATOMIC_TERMINALS for value in adversarial_atomic) or any(
        value in CLAIM_BINDING_TERMINALS or value in PRIMARY_SOURCE_TERMINALS
        for value in adversarial_complete
    ):
        failures.append("source terminal allowlists accept lookalike values")
    source_text = SOURCE_POLICY.read_text(encoding="utf-8")
    for class_name, exact_value in (
        (
            "AtomicFactTerminalStateV1",
            "PASS_RECONFIRMED_DIRECT_PRIMARY_OR_PRIMARY_METHOD_SOURCE",
        ),
        (
            "ClaimBindingTerminalStateV1",
            "COMPLETE_TERMINAL_EXACT_CLAIM_BINDING",
        ),
        ("PrimarySourceCompletenessV1", "COMPLETE_PRIMARY_SOURCE"),
    ):
        if class_name not in source_text or exact_value not in source_text:
            failures.append(f"typed source terminal enum missing: {class_name}")
    if any(
        row.get("runtime_effect_authorized") is not False
        or not isinstance(row.get("exact_facts"), dict)
        or not row["exact_facts"]
        or not isinstance(row.get("implementation_rule"), str)
        or not row["implementation_rule"]
        for row in overlays
    ):
        failures.append("source overlays are not exact effect-free contracts")
    by_id = {row["currentization_id"]: row for row in overlays}
    endpoint_facts = by_id["ST12A-CURR-SOURCE-001"]["exact_facts"]
    if (
        len(endpoint_facts) != 6
        or endpoint_facts["DELETE /orders"]["burst"]
        != "2000 requests/10 seconds"
        or endpoint_facts["DELETE /orders"]["sustained"]
        != "15000 requests/10 minutes"
    ):
        failures.append("endpoint/window currentization is not exact")
    signer_facts = by_id["ST12A-CURR-SOURCE-002"]["exact_facts"]
    if (
        signer_facts["standard_order_burst_tokens"] != 60
        or signer_facts["standard_order_rate_tokens_per_second"] != 40
        or signer_facts["standard_cancel_burst_tokens"] != 120
        or signer_facts["standard_cancel_rate_tokens_per_second"] != 80
        or signer_facts["warning_mode_duration"]
        != "two weeks; live enforcement date to be announced"
    ):
        failures.append("signer token-bucket currentization is not exact")
    response_facts = by_id["ST12A-CURR-SOURCE-003"]["exact_facts"]
    if (
        response_facts["successful_FAK_FOK_response_uses"] != "tradeIDs"
        or response_facts["custom_REST_followup"]
        != (
            "poll existing trades by tradeID until hash is available "
            "or status is FAILED"
        )
        or response_facts["accepted_order_resubmission_allowed"] is not False
        or response_facts["inline_transactionHashes_expected"] is not False
    ):
        failures.append("FAK/FOK success response is not bound to tradeIDs")
    lifecycle_facts = by_id["ST12A-CURR-SOURCE-004"]["exact_facts"]
    if lifecycle_facts["trade_pending_statuses"] != [
        "MATCHED",
        "MINED",
        "RETRYING",
    ]:
        failures.append("RETRYING is not a nonterminal pending state")
    subjects = {row["subject"] for row in overlays}
    for subject in (
        "Python Decimal arithmetic baseline",
        "Qiskit Optimization compatibility observation",
        "D-Wave Ocean SDK compatibility observation",
    ):
        if subject not in subjects:
            failures.append(f"dependency currentization missing: {subject}")
    bindings_text = BINDINGS.read_text(encoding="utf-8")
    if bindings_text.count("ST12-SOURCE-RULE::011") != 1:
        failures.append("source-claim binding rule 011 is not uniquely materialized")
    if "broad_regex_or_alias_matching_allowed: bool = False" not in bindings_text:
        failures.append("broad source matching is not default-denied")
    try:
        bindings_tree = ast.parse(bindings_text, filename=str(BINDINGS))
        primary_sources = json.loads(
            _literal(bindings_tree, "_ST12B_PRIMARY_SOURCE_REGISTRY_JSON")
        )
        source_conflicts = json.loads(
            _literal(bindings_tree, "_ST12B_SOURCE_CONFLICT_RESOLUTION_JSON")
        )
        source_currentizations = json.loads(
            _literal(bindings_tree, "_ST12B_SOURCE_CURRENTIZATION_JSON")
        )
        numeric_authorities = json.loads(
            _literal(bindings_tree, "_ST12B_NUMERIC_VALUE_AUTHORITY_JSON")
        )
        input_authorities = json.loads(
            _literal(bindings_tree, "_ST12B_FORMULA_INPUT_AUTHORITY_JSON")
        )
        online_currentizations = json.loads(
            _literal(bindings_tree, "_ST12B_ONLINE_CURRENTIZATION_JSON")
        )
    except (SyntaxError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"v3.4 source/value literals could not be reconstructed: {exc}")
        primary_sources = []
        source_conflicts = []
        source_currentizations = []
        numeric_authorities = []
        input_authorities = []
        online_currentizations = []
    if (
        len(primary_sources) != 55
        or Counter(
            str(row.get("normalized_source_class"))
            for row in primary_sources
            if isinstance(row, dict)
        )
        != {
            "EXTERNAL_PRIMARY_OR_OFFICIAL_SOURCE": 24,
            "OWNER_FORMAL_DERIVATION": 30,
            "OWNER_ARCHITECTURE_OR_POLICY": 1,
        }
        or len(
            {
                row.get("source_id")
                for row in primary_sources
                if isinstance(row, dict)
            }
        )
        != 55
    ):
        failures.append("v3.4 primary-source population is not exact 24+30+1=55")
    if (
        len(source_conflicts) != 1
        or not isinstance(source_conflicts[0], dict)
        or len(source_conflicts[0].get("source_ids", ())) != 3
        or source_conflicts[0].get("terminal_state")
        != "RESOLVED_TO_RUNTIME_BINDING_REQUIRED"
        or "builder fees remain separate and additive"
        not in str(source_conflicts[0].get("resolution"))
    ):
        failures.append("v3.4 source conflict is not exact and fail-closed")
    if (
        len(source_currentizations) != 7
        or len(online_currentizations) != 5
        or any(
            not isinstance(row, dict)
            or row.get("live_refetch_state") != "SUCCEEDED_2026-07-29"
            or row.get("retrieved_date") != "2026-07-29"
            for row in online_currentizations
        )
    ):
        failures.append("v3.4 currentization populations are not exact 7+5")
    if (
        len(input_authorities) != 142
        or len(numeric_authorities) != 621
        or Counter(
            str(row.get("subject_kind"))
            for row in numeric_authorities
            if isinstance(row, dict)
        )
        != {"PARAMETER": 479, "FORMULA_INPUT": 142}
        or any(
            not isinstance(row, dict)
            or row.get("source_semantics_do_not_authenticate_runtime_number")
            is not True
            for row in numeric_authorities
        )
    ):
        failures.append("v3.4 numeric-value/source authority separation is not exact")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} source_rows={len(source_rows)} "
        f"overlays={len(overlays)} binding_rules=1 "
        f"v34_primary_sources={len(primary_sources)} "
        f"v34_numeric_authorities={len(numeric_authorities)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
