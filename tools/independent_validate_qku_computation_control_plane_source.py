#!/usr/bin/env python3
"""Independent source-registry validation without importing production."""

from __future__ import annotations

import ast
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


def _assignment(tree: ast.Module, name: str) -> ast.expr | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    return None


def _source_rule_011(tree: ast.Module) -> dict[str, object] | None:
    value = _assignment(tree, "SOURCE_RULE_011")
    if (
        not isinstance(value, ast.Call)
        or not isinstance(value.func, ast.Name)
        or value.func.id != "SourceClaimBindingRuleV1"
    ):
        return None
    result: dict[str, object] = {}
    for keyword in value.keywords:
        if keyword.arg is None:
            return None
        try:
            result[keyword.arg] = ast.literal_eval(keyword.value)
        except (TypeError, ValueError):
            return None
    return result


def main() -> int:
    failures: list[str] = []
    tree = ast.parse(
        SOURCE_POLICY.read_text(encoding="utf-8"),
        filename=str(SOURCE_POLICY),
    )
    try:
        source_rows = json.loads(_literal(tree, "_CERTIFIED_SOURCE_ROWS_JSON"))
        overlays = json.loads(
            _literal(tree, "_CURRENTIZATION_OVERLAY_ROWS_JSON")
        )
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
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
    bindings_tree = ast.parse(bindings_text, filename=str(BINDINGS))
    try:
        tranche_b_rules = json.loads(
            _literal(
                bindings_tree,
                "_TRANCHE_B_SOURCE_CLAIM_BINDING_RULES_JSON",
            )
        )
    except (ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Tranche-B source rules are unreadable: {exc}")
        tranche_b_rules = []
    rule_ids = tuple(
        str(row.get("binding_rule_id"))
        for row in tranche_b_rules
        if isinstance(row, dict)
    )
    if (
        not isinstance(tranche_b_rules, list)
        or len(tranche_b_rules) != 10
        or len(rule_ids) != 10
        or len(set(rule_ids)) != 10
        or rule_ids.count("ST12-SOURCE-RULE::011") != 1
    ):
        failures.append("the exact ten Tranche-B source rules differ")
    for row in tranche_b_rules:
        if (
            not isinstance(row, dict)
            or row.get("research_completeness_state")
            != "COMPLETE_TERMINAL_EXACT_RULE"
            or row.get("source_pack_as_primary_allowed") is not False
            or row.get("broad_regex_or_alias_matching_allowed") is not False
            or row.get("codex_source_selection_allowed") is not False
            or not row.get("exact_claims")
            or not row.get("permitted_consumers")
        ):
            failures.append(
                "a Tranche-B source rule is nonterminal or permits source selection"
            )
    a_rule = _source_rule_011(bindings_tree)
    b_rule = next(
        (
            row
            for row in tranche_b_rules
            if isinstance(row, dict)
            and row.get("binding_rule_id") == "ST12-SOURCE-RULE::011"
        ),
        None,
    )
    exact_fields = (
        "binding_rule_id",
        "rule_class",
        "claim_selector",
        "source_identity_ref",
        "source_state_ref",
        "exact_claims",
        "permitted_consumers",
    )
    if (
        a_rule is None
        or b_rule is None
        or any(
            a_rule.get(name)
            != (
                tuple(b_rule[name])
                if name in {"exact_claims", "permitted_consumers"}
                else b_rule[name]
            )
            for name in exact_fields
        )
    ):
        failures.append(
            "preserved Tranche-A rule 011 differs from the certified B reuse row"
        )
    if "broad_regex_or_alias_matching_allowed: bool = False" not in bindings_text:
        failures.append("broad source matching is not default-denied")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} source_rows={len(source_rows)} "
        f"overlays={len(overlays)} tranche_a_binding_rules=1 "
        f"tranche_b_binding_rules={len(tranche_b_rules)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
