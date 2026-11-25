"""Bounded data-only LP03 worker. Only the original parent owns effects/custody.

The fixed module entry accepts no path, executable, callback, key or store.
Native launch/termination and source admission belong to the existing owners.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .context import _native_ident, _native_require, _public_counter_v1
from .serialization import deterministic_json, _evidence_canonical_object_v1, _evidence_frozen_data_v1


WORKER_PROTOCOL_V1 = "QTT_LP03_WORKER_V1"
_PARENT_KINDS_V1 = frozenset({"START", "INPUT_SEGMENT", "CONTINUE", "CANCEL"})
_WORKER_KINDS_V1 = frozenset({"STARTED", "READ_REQUEST", "COMPUTATION_RESULT", "SEGMENT", "FAILED", "COMPLETE"})
_PAYLOAD_FIELDS_V1 = MappingProxyType({
    "START": frozenset({"signed_grant", "environment_identity", "package_identity_ref"}),
    "STARTED": frozenset({"environment_identity", "executable", "base_executable", "prefix", "base_prefix", "module_file", "process_id",
                          "clock_domain_id", "boot_identity_ref"}),
    "READ_REQUEST": frozenset({"record_refs"}),
    "INPUT_SEGMENT": frozenset({"segment_ordinal", "final_segment", "inputs", "original_record_refs", "event"}),
    "CONTINUE": frozenset({"command", "event_ordinal"}),
    "CANCEL": frozenset({"reason_ref"}),
    "COMPUTATION_RESULT": frozenset({"event_ordinal", "invocation_contract", "numeric_context_policy_ref", "raw_output_json", "original_record_refs", "invocation_measurement"}),
    "SEGMENT": frozenset({"segment_ordinal", "first_event_ordinal", "last_event_ordinal", "computations", "complete"}),
    "FAILED": frozenset({"reason_code", "exception_class", "event_ordinal", "measurement_or_absence"}),
    "COMPLETE": frozenset({"events", "computations", "segments"}),
})


def _worker_invocation_contract_v1(contract):
    from dataclasses import fields
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import EvidenceOriginV1
    _native_require(isinstance(contract, Mapping)
                    and set(contract) == {field.name for field in fields(EvidencePrivateInvocationContractV1)}
                    and all(type(value) is str for name, value in contract.items() if name != "owner_bindings")
                    and type(contract["owner_bindings"]) in (tuple, list)
                    and contract["origin_policy"] in EvidenceOriginV1._value2member_map_, "LP03_WORKER_INVOCATION_FIELDS")
    expected = resolve_evidence_invocation_v1(contract["math_id"], implementation_pin=contract["raw_implementation_id"],
        specification_pin=contract["mathematical_semantic_version"], resource_policy_ref=contract["resource_policy_ref"],
        origin=EvidenceOriginV1(contract["origin_policy"]))
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_WORKER_INVOCATION_CONTRACT_CHANGED")
    return expected


def _worker_cashflow_inputs_v1(payload, event):
    """Join the closed public invocation to every original cashflow source."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import decode_evidence_public_invocation_inputs_v1, _extract
    from .models import _evidence_cashflow_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id in ("MATH-06", "MATH-07")
                    and event["kind"] == "SYNTHETIC_SIGNED_TOTAL_CASHFLOW_CONTEXT"
                    and event["payload"]["math_id"] == contract.math_id, "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_cashflow_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_CASHFLOW_SOURCE_ROSTER_JOIN")
    native = {binding.input_name: _extract(part.reconstructed_canonical_events[0]["values"], binding.exact_field_path)
              for binding, part in zip(FORMULA_INPUT_AUTHORITY_BY_MATH_ID[contract.math_id], sources, strict=True)}
    raw = deterministic_json(payload["inputs"]).encode("utf-8")
    _native_require(raw == deterministic_json(native).encode("utf-8"), "LP03_WORKER_CASHFLOW_ORIGINAL_TEXT_JOIN")
    return decode_evidence_public_invocation_inputs_v1(contract.math_id, raw, maximum_bytes=65536, maximum_nodes=4096)


def _worker_market_inputs_v1(payload, event):
    """Join the closed public invocation to every original market source."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import decode_evidence_public_invocation_inputs_v1, _extract
    from .models import _evidence_market_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id in ("MATH-01", "MATH-04", "MATH-05")
                    and event["kind"] == "SYNTHETIC_MARKET_PRICE_CONTEXT"
                    and event["payload"]["math_id"] == contract.math_id, "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_market_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_MARKET_SOURCE_ROSTER_JOIN")
    native = {binding.input_name: _extract(part.reconstructed_canonical_events[0]["values"], binding.exact_field_path)
              for binding, part in zip(FORMULA_INPUT_AUTHORITY_BY_MATH_ID[contract.math_id], sources)}
    raw = deterministic_json(payload["inputs"]).encode("utf-8")
    _native_require(raw == deterministic_json(native).encode("utf-8"), "LP03_WORKER_MARKET_ORIGINAL_TEXT_JOIN")
    return decode_evidence_public_invocation_inputs_v1(contract.math_id, raw, maximum_bytes=65536, maximum_nodes=4096)


def _worker_kelly27_inputs_v1(payload, event):
    """Closed M27 values retain their two original source representations."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .input_resolver import decode_evidence_private_inputs_v1
    from .models import _evidence_kelly27_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-27" and event["kind"] == "SYNTHETIC_KELLY_PROBABILITY_PAYOFF_CONTEXT",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_kelly27_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_KELLY27_SOURCE_ROSTER_JOIN")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-27"].bindings
    native = {binding.input_name: part.reconstructed_canonical_events[0]["values"][binding.input_name]
              for binding, part in zip(bindings, sources)}
    # Original source text remains the wire value. Decode once for the exact
    # private type check, then compare canonical representations independently.
    # No Decimal normalization or rational equality can hide a changed scale.
    raw = deterministic_json(payload["inputs"]).encode("utf-8")
    _native_require(raw == deterministic_json(native).encode("utf-8"), "LP03_WORKER_KELLY27_ORIGINAL_TEXT_JOIN")
    decoded = decode_evidence_private_inputs_v1("MATH-27", raw, maximum_bytes=65536, maximum_nodes=4096)
    return decoded



def _worker_kelly28_inputs_v1(payload, event):
    """Closed M28 values retain their original publication and constraint sources."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .input_resolver import decode_evidence_private_inputs_v1
    from .models import _evidence_kelly28_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-28" and event["kind"] == "SYNTHETIC_FRACTIONAL_KELLY_CONTEXT",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_kelly28_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_KELLY28_SOURCE_ROSTER_JOIN")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-28"].bindings
    native = {binding.input_name: part.reconstructed_canonical_events[0]["values"][binding.input_name]
              for binding, part in zip(bindings, sources)}
    # Original source text remains the wire value. Decode once for the exact
    # private type check, then compare canonical representations independently.
    # No Decimal normalization or rational equality can hide a changed scale.
    raw = deterministic_json(payload["inputs"]).encode("utf-8")
    _native_require(raw == deterministic_json(native).encode("utf-8"), "LP03_WORKER_KELLY28_ORIGINAL_TEXT_JOIN")
    decoded = decode_evidence_private_inputs_v1("MATH-28", raw, maximum_bytes=65536, maximum_nodes=4096)
    return decoded


def _worker_research_inputs_v1(payload, event):
    """Closed M26 values retain their three original source representations."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .input_resolver import decode_evidence_private_inputs_v1
    from .models import _evidence_research_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-26" and event["kind"] == "SYNTHETIC_RESEARCH_DECISION",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_research_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_RESEARCH_SOURCE_ROSTER_JOIN")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-26"].bindings
    native = {binding.input_name: part.reconstructed_canonical_events[0]["values"][binding.input_name]
              for binding, part in zip(bindings, sources)}
    # Original source text remains the wire value. Decode once for the exact
    # private type check, then compare canonical representations independently.
    # No Decimal normalization or rational equality can hide a changed scale.
    raw = deterministic_json(payload["inputs"]).encode("utf-8")
    _native_require(raw == deterministic_json(native).encode("utf-8"), "LP03_WORKER_RESEARCH_ORIGINAL_TEXT_JOIN")
    decoded = decode_evidence_private_inputs_v1("MATH-26", raw, maximum_bytes=65536, maximum_nodes=4096)
    return decoded


def _worker_brier_inputs_v1(payload, event):
    """Typed MATH08 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_forecast_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-08" and event["kind"] == "SYNTHETIC_FORECAST_EVALUATION_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-08", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    rows, outcomes = decoded["probability_rows"], decoded["outcome_indices"]
    _native_require(type(rows) is tuple and bool(rows) and type(outcomes) is tuple and len(outcomes) == len(rows)
                    and type(rows[0]) is tuple and len(rows[0]) >= 2
                    and all(type(row) is tuple and len(row) == len(rows[0])
                            and all(type(value) is float and isfinite(value) and 0 <= value <= 1 for value in row) for row in rows)
                    and all(type(value) is int and 0 <= value < len(rows[0]) for value in outcomes),
                    "LP03_WORKER_BRIER_INPUT_TYPES")
    sources = _evidence_forecast_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_FORECAST_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-08"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_FORECAST_TYPED_VALUE_JOIN")
    return decoded

def _worker_log_loss_inputs_v1(payload, event):
    """Typed MATH09 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_log_loss_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-09" and event["kind"] == "SYNTHETIC_LOG_LOSS_EVALUATION_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-09", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    rows, outcomes = decoded["probability_rows"], decoded["outcome_indices"]
    _native_require(type(rows) is tuple and bool(rows) and type(outcomes) is tuple and len(outcomes) == len(rows)
                    and type(rows[0]) is tuple and len(rows[0]) >= 2
                    and all(type(row) is tuple and len(row) == len(rows[0])
                            and all(type(value) is float and isfinite(value) and 0 <= value <= 1 for value in row) for row in rows)
                    and all(type(value) is int and 0 <= value < len(rows[0]) for value in outcomes),
                    "LP03_WORKER_LOG_LOSS_INPUT_TYPES")
    epsilon = decoded["clip_epsilon"]
    _native_require(type(epsilon) is float and isfinite(epsilon) and 0.0 < epsilon < 0.5,
                    "LP03_WORKER_LOG_LOSS_EPSILON_DOMAIN")
    sources = _evidence_log_loss_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_LOG_LOSS_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-09"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_LOG_LOSS_TYPED_VALUE_JOIN")
    return decoded


def _worker_heldout_inputs_v1(payload, event):
    """Join the original topology fields and its separate scoring sources."""
    from .input_resolver import decode_evidence_public_invocation_inputs_v1
    from .models import _evidence_heldout_source_data_v1

    topology = _worker_invocation_contract_v1(payload["invocation_contract"])
    scorer = _worker_invocation_contract_v1(payload["scorer_invocation_contract"])
    parts, values, scored_trace = _evidence_heldout_source_data_v1(event["payload"])
    _native_require(event["kind"] == "SYNTHETIC_HELD_OUT_FOLD_SCORING"
        and event["payload"]["topology_math_id"] == topology.math_id
        and topology.origin_policy == scorer.origin_policy == "SOFTWARE_CONFORMANCE"
        and scored_trace["scorer_math_id"] == scorer.math_id,
        "LP03_WORKER_HELD_OUT_INPUT_PROFILE")
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id,
        record_id=part.original_record_refs[0].record_id) for part in parts)
    _native_require(all(sum(dict(ref) == original for ref in payload["original_record_refs"]) == 1
        for original in source_refs), "LP03_WORKER_HELD_OUT_SOURCE_ROSTER")
    original_inputs = deterministic_json(payload["inputs"]).encode("utf-8", "strict")
    decoded = decode_evidence_public_invocation_inputs_v1(topology.math_id, original_inputs,
        maximum_bytes=65536, maximum_nodes=4096)
    _native_require(deterministic_json(decoded) == deterministic_json(values),
        "LP03_WORKER_HELD_OUT_ORIGINAL_TOPOLOGY_VALUES")
    return decoded, scored_trace


def _heldout_computation_count_v1(topology_math_id, inputs):
    if topology_math_id == "MATH-20":
        return 1 + inputs["folds"]
    _native_require(topology_math_id == "MATH-21", "LP03_WORKER_HELD_OUT_INPUT_PROFILE")
    return 7 if inputs["k_test_groups"] == 2 else 1 + inputs["N_groups"]


def _worker_verify_original_source_permissions_v1(parts, field_rosters, signed_reads, *, selection_failure, scope_failure):
    """Verify record-specific signed source rights in the isolated worker."""
    from .models import EvidenceAbsenceV1, EvidenceExactSelectionV1

    for part, fields in zip(parts, field_rosters, strict=True):
        ref, = part.original_record_refs
        row, = part.reconstructed_canonical_events
        clocks, scope = row["native_clocks"], row["scope"]
        choices = tuple(selection for selection in signed_reads
            if selection.original_store_id == ref.store_id and type(selection.selection) is EvidenceExactSelectionV1
            and selection.selection.record_refs == (ref.record_id,))
        _native_require(len(choices) == 1, selection_failure)
        selected, = choices
        _native_require((selected.original_owner_id, selected.permitted_record_kinds,
            selected.required_original_rights_refs) == (row["owner_id"], (row["record_kind"],), part.rights_refs)
            and set(selected.allowed_fields) == set(fields)
            and type(selected.profile_scope) is type(selected.account_scope) is EvidenceAbsenceV1
            and type(selected.market_scope) is tuple and scope["market_scope_id"] in selected.market_scope
            and type(selected.instrument_scope) is tuple
            and scope["instrument_or_contract_scope_id"] in selected.instrument_scope
            and selected.effective_from_wall_ns <= clocks["effective_time"] < selected.effective_until_wall_ns
            and selected.known_from_wall_ns <= clocks["available_time"] < selected.known_until_wall_ns,
            scope_failure)


def _worker_math39_queue_inputs_v1(payload, event, *, signed_reads=None):
    """Re-derive the four public invocation arguments from the original records."""
    from .bindings import CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import decode_evidence_public_invocation_inputs_v1
    from .models import _evidence_math39_queue_source_data_v1

    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-39" and contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == "SYNTHETIC_ACKNOWLEDGED_QUEUE", "LP03_WORKER_QUEUE_PUBLIC_PROFILE")
    parts, resolved = _evidence_math39_queue_source_data_v1(event["payload"])
    originals = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in parts)
    _native_require(all(sum(dict(row) == ref for row in payload["original_record_refs"]) == 1 for ref in originals),
                    "LP03_WORKER_QUEUE_ORIGINAL_READS")
    wire = deterministic_json(payload["inputs"]).encode("utf-8", "strict")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-39", wire, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(dict(decoded) == dict(resolved.authoritative_values)
        and deterministic_json(payload["inputs"]) == deterministic_json({key:str(value)
            for key,value in resolved.authoritative_values.items()}), "LP03_WORKER_QUEUE_ORIGINAL_DERIVED_VALUES")
    if signed_reads is not None:
        _worker_verify_original_source_permissions_v1(parts,
            ((binding.exact_field_path,) for binding in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-39"]),
            signed_reads,
            selection_failure="LP03_WORKER_QUEUE_SIGNED_SOURCE_SELECTION",
            scope_failure="LP03_WORKER_QUEUE_SIGNED_SOURCE_SCOPE_AND_INTERVAL")
    return decoded


def _worker_original_private_inputs_v1(payload, event, *, signed_reads=None):
    """Verify the frame's private wire matches the original owner arguments."""
    from .input_resolver import decode_evidence_private_inputs_v1, decode_evidence_public_invocation_inputs_v1
    from .models import _evidence_original_private_input_profile_v1, _evidence_original_private_inputs_v1

    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    math_id = contract.math_id
    _, expected, _ = _evidence_original_private_input_profile_v1(math_id)
    _native_require(contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == expected, "LP03_WORKER_ANALYTIC_PRIVATE_INVOCATION_PROFILE")
    parts, original_inputs, _ = _evidence_original_private_inputs_v1(event["payload"], math_id=math_id)
    originals = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in parts)
    _native_require(all(sum(dict(row) == ref for row in payload["original_record_refs"]) == 1 for ref in originals),
        "LP03_WORKER_ANALYTIC_PRIVATE_ORIGINAL_READS")
    wire = deterministic_json(payload["inputs"]).encode("utf-8", "strict")
    if math_id == "MATH-36":
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID

        decoded = decode_evidence_public_invocation_inputs_v1(math_id, wire, maximum_bytes=65536, maximum_nodes=4096)
        if signed_reads is not None:
            _worker_verify_original_source_permissions_v1(parts,
                ((binding.exact_field_path,) for binding in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]),
                signed_reads,
                selection_failure="LP03_WORKER_BINARY_BOOK_SIGNED_SOURCE_SELECTION",
                scope_failure="LP03_WORKER_BINARY_BOOK_SIGNED_SOURCE_SCOPE_AND_INTERVAL")
    else:
        decoded = decode_evidence_private_inputs_v1(math_id, wire, maximum_bytes=65536, maximum_nodes=4096)
        if signed_reads is not None:
            from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
            from .models import _LP03_ORIGINAL_PRIVATE_BINARY64_EXECUTION_IDS_V1

            _native_require(math_id in _LP03_ORIGINAL_PRIVATE_BINARY64_EXECUTION_IDS_V1,
                "LP03_WORKER_BINARY64_EXECUTION_SIGNED_PROFILE")
            _worker_verify_original_source_permissions_v1(parts,
                ((binding.input_name, "original_execution_context")
                    for binding in EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1[math_id].bindings),
                signed_reads, selection_failure="LP03_WORKER_BINARY64_EXECUTION_SIGNED_SOURCE_SELECTION",
                scope_failure="LP03_WORKER_BINARY64_EXECUTION_SIGNED_SOURCE_SCOPE_AND_INTERVAL")
    _native_require(deterministic_json(decoded) == deterministic_json(original_inputs),
        "LP03_WORKER_ANALYTIC_PRIVATE_ORIGINAL_VALUES")
    return decoded


def _worker_original_quantum_inputs_v1(payload, event, *, grant=None):
    """Use only the exact retained source values and the current signed read roles."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .input_resolver import decode_evidence_private_inputs_v1
    from .models import (_evidence_original_quantum_sources_v1, _evidence_quantum_original_lock_pins_v1,
        _evidence_quantum_source_epochs_v1)

    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    math_id = contract.math_id
    _native_require(contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == "SYNTHETIC_ORIGINAL_QUANTUM_INPUT", "LP03_WORKER_QUANTUM_SOURCE_PROFILE")
    parts, values, scope = _evidence_original_quantum_sources_v1(event["payload"], math_id=math_id)
    originals = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in parts)
    _native_require(all(sum(dict(row) == ref for row in payload["original_record_refs"]) == 1 for ref in originals),
        "LP03_WORKER_QUANTUM_ORIGINAL_RECORD_REFS")
    if grant is not None:
        _native_require(grant.component_closure == (math_id,) and grant.callback_pins == ()
            and grant.input_lock_ref == scope["original_lock_id"], "LP03_WORKER_QUANTUM_SIGNED_LOCK")
        pins = _evidence_quantum_original_lock_pins_v1(grant.component_and_callback_pins["quantum_original_lock"],
            basis=scope["original_economic_basis"])
        _native_require(set(_evidence_quantum_source_epochs_v1(parts)) <= set(pins["source_epoch_pairs"]),
            "LP03_WORKER_QUANTUM_SIGNED_SOURCE_EPOCHS")
        bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1[math_id].bindings
        _worker_verify_original_source_permissions_v1(parts,
            ((binding.input_name, "original_quantum_context") for binding in bindings),
            grant.allowed_reads, selection_failure="LP03_WORKER_QUANTUM_SIGNED_SOURCE_SELECTION",
            scope_failure="LP03_WORKER_QUANTUM_SIGNED_SOURCE_SCOPE")
    wire = deterministic_json(payload["inputs"]).encode("utf-8", "strict")
    decoded = decode_evidence_private_inputs_v1(math_id, wire, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(deterministic_json(decoded) == deterministic_json(values), "LP03_WORKER_QUANTUM_ORIGINAL_ARGUMENTS")
    return decoded


def _worker_recorded_ope_point_inputs_v1(payload, event):
    from .input_resolver import decode_evidence_public_invocation_inputs_v1
    from .models import _evidence_recorded_ope_source_data_v1

    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    math_id = contract.math_id
    _native_require(math_id in ("MATH-23", "MATH-24", "MATH-25")
        and contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == "SYNTHETIC_RECORDED_OPE_POINT",
        "LP03_WORKER_OPE_POINT_ORIGINAL_INVOCATION_PROFILE")
    parts, inputs, _, _ = _evidence_recorded_ope_source_data_v1(event["payload"], math_id=math_id)
    originals = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in parts)
    _native_require(all(sum(dict(row) == ref for row in payload["original_record_refs"]) == 1 for ref in originals),
        "LP03_WORKER_OPE_POINT_ORIGINAL_READS")
    wire = deterministic_json(payload["inputs"]).encode("utf-8", "strict")
    decoded = decode_evidence_public_invocation_inputs_v1(math_id, wire, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(deterministic_json(decoded) == deterministic_json(inputs), "LP03_WORKER_OPE_POINT_ORIGINAL_VALUES")
    return decoded


def _worker_recorded_dr_inputs_v1(payload, event, *, attempt_ref):
    from .input_resolver import decode_evidence_public_invocation_inputs_v1
    from .models import _evidence_dr_original_source_data_v1

    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-22" and contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == "SYNTHETIC_RECORDED_DR_UNCERTAINTY",
        "LP03_WORKER_DR_ORIGINAL_INVOCATION_PROFILE")
    raw_ref = attempt_ref + "::DATA::RAW"
    _native_require(event["payload"]["estimator_original_raw_ref"] == raw_ref, "LP03_WORKER_DR_ORIGINAL_RAW_REF")
    parts, inputs, _, _, _ = _evidence_dr_original_source_data_v1(event["payload"], original_raw_ref=raw_ref)
    originals = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in parts)
    _native_require(all(sum(dict(row) == ref for row in payload["original_record_refs"]) == 1 for ref in originals),
        "LP03_WORKER_DR_ORIGINAL_READS")
    wire = deterministic_json(payload["inputs"]).encode("utf-8", "strict")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-22", wire, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(deterministic_json(decoded) == deterministic_json(inputs), "LP03_WORKER_DR_ORIGINAL_ROW_VALUES")
    return decoded


def _worker_cscv_inputs_v1(payload, event):
    """Join M17/M18 wire values to complete source data; never issue custody."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed
    from .models import _evidence_cscv_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-19"
        and contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == "SYNTHETIC_CSCV_MATRIX_AND_GROUP_POLICY", "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_cscv_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
        "LP03_WORKER_CSCV_SOURCE_ROSTER_JOIN")
    decoded = decode_evidence_public_invocation_inputs_v1(contract.math_id, deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    original = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID[contract.math_id], strict=True):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        original[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Preserve the exact integer group policy, float bits and declared
    # chronology, including every material strategy column.
    _native_require(deterministic_json(decoded) == deterministic_json(original), "LP03_WORKER_CSCV_TYPED_VALUE_JOIN")
    return decoded



def _worker_sharpe_inputs_v1(payload, event):
    """Join M17/M18 wire values to complete source data; never issue custody."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed
    from .models import _evidence_sharpe_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id in ("MATH-17", "MATH-18")
        and contract.origin_policy == "SOFTWARE_CONFORMANCE"
        and event["kind"] == "SYNTHETIC_SHARPE_LEDGER_AND_MOMENTS"
        and event["payload"]["math_id"] == contract.math_id, "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    sources = _evidence_sharpe_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
        "LP03_WORKER_SHARPE_SOURCE_ROSTER_JOIN")
    decoded = decode_evidence_public_invocation_inputs_v1(contract.math_id, deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    original = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID[contract.math_id], strict=True):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        original[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Exact canonical comparison keeps integer support, float types, signed
    # zeros, and every attempted/pruned trial in its original position.
    _native_require(deterministic_json(decoded) == deterministic_json(original), "LP03_WORKER_SHARPE_TYPED_VALUE_JOIN")
    return decoded


def _worker_spa_inputs_v1(payload, event):
    """Typed MATH16 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_spa_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-16" and event["kind"] == "SYNTHETIC_SPA_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-16", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    matrix, sign, seed, replicates, block, alpha, variant = (decoded[name] for name in (
        "loss_differentials", "sign_convention", "seed", "replicates", "expected_block_length", "alpha", "recenter_variant"))
    _native_require(type(matrix) is tuple and 3 <= len(matrix) <= 4
        and all(type(row) is tuple and 1 <= len(row) <= 2 for row in matrix)
        and all(len(row) == len(matrix[0]) for row in matrix)
        and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for row in matrix for value in row)
        and type(sign) is str and sign == "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"
        and type(seed) is int and seed.bit_length() <= 256 and type(replicates) is int
        and 1 <= replicates <= 4 and len(matrix) * replicates <= 16
        and type(block) is float and isfinite(block) and 1.0 <= block <= len(matrix)
        and type(alpha) is float and isfinite(alpha) and 0.0 < alpha < 1.0
        and type(variant) is str and variant == "HANSEN_CONSISTENT_LOG_LOG_THRESHOLD", "LP03_WORKER_SPA_INPUT_TYPES")
    sources = _evidence_spa_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_SPA_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-16"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_SPA_TYPED_VALUE_JOIN")
    return decoded


def _worker_reality_check_inputs_v1(payload, event):
    """Typed MATH15 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_reality_check_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-15" and event["kind"] == "SYNTHETIC_REALITY_CHECK_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-15", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    matrix, sign, seed, replicates, block, alpha = (decoded[name] for name in (
        "loss_differentials", "sign_convention", "seed", "replicates", "expected_block_length", "alpha"))
    _native_require(type(matrix) is tuple and 2 <= len(matrix) <= 4
        and all(type(row) is tuple and 1 <= len(row) <= 2 for row in matrix)
        and all(len(row) == len(matrix[0]) for row in matrix)
        and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for row in matrix for value in row)
        and type(sign) is str and sign == "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"
        and type(seed) is int and seed.bit_length() <= 256 and type(replicates) is int
        and 1 <= replicates <= 4 and len(matrix) * replicates <= 16
        and type(block) is float and isfinite(block) and 1.0 <= block <= len(matrix)
        and type(alpha) is float and isfinite(alpha) and 0.0 < alpha < 1.0, "LP03_WORKER_REALITY_INPUT_TYPES")
    sources = _evidence_reality_check_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_REALITY_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-15"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_REALITY_TYPED_VALUE_JOIN")
    return decoded


def _worker_bootstrap_inputs_v1(payload, event):
    """Typed MATH14 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_bootstrap_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-14" and event["kind"] == "SYNTHETIC_STATIONARY_BOOTSTRAP_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-14", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    values, block, seed, replicates, confidence, method = (decoded[name] for name in (
        "series", "expected_block_length", "seed", "replicates", "confidence", "interval_method"))
    _native_require(type(values) is tuple and 2 <= len(values) <= 8
        and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for value in values)
        and type(block) is float and isfinite(block) and 1.0 <= block <= len(values)
        and type(seed) is int and seed.bit_length() <= 256 and type(replicates) is int
        and 1 <= replicates <= 4 and len(values) * replicates <= 16
        and type(confidence) is float and isfinite(confidence) and 0.0 < confidence < 1.0
        and type(method) is str and method == "PERCENTILE_TYPE7", "LP03_WORKER_BOOTSTRAP_INPUT_TYPES")
    sources = _evidence_bootstrap_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_BOOTSTRAP_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-14"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_BOOTSTRAP_TYPED_VALUE_JOIN")
    return decoded


def _worker_wilson_inputs_v1(payload, event):
    """Typed MATH11 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_wilson_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-11" and event["kind"] == "SYNTHETIC_BERNOULLI_COUNT_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-11", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    successes, trials, confidence = decoded["successes"], decoded["trials"], decoded["confidence"]
    _native_require(type(successes) is int and type(trials) is int
                    and 0 <= successes <= trials <= 2**53 and trials > 0
                    and type(confidence) is float and isfinite(confidence) and 0.0 < confidence < 1.0,
                    "LP03_WORKER_WILSON_INPUT_TYPES")
    sources = _evidence_wilson_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_WILSON_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-11"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_WILSON_TYPED_VALUE_JOIN")
    return decoded


def _worker_calibration_inputs_v1(payload, event):
    """Typed MATH10 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_calibration_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    _native_require(contract.math_id == "MATH-10" and event["kind"] == "SYNTHETIC_CALIBRATION_EVALUATION_BATCH",
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1("MATH-10", deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    probabilities, outcomes = decoded["probabilities"], decoded["outcomes"]
    policy, count = decoded["bin_policy"], decoded["bin_count"]
    _native_require(type(probabilities) is tuple and 0 < len(probabilities) <= 4096
                    and type(outcomes) is tuple and len(outcomes) == len(probabilities)
                    and all(type(value) is float and isfinite(value) and 0 <= value <= 1 for value in probabilities)
                    and all(type(value) is int and value in (0, 1) for value in outcomes),
                    "LP03_WORKER_CALIBRATION_INPUT_TYPES")
    _native_require(type(policy) is str and policy in ("EQUAL_WIDTH", "EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES")
                    and type(count) is int and 0 < count <= 4096
                    and (policy == "EQUAL_WIDTH" or count <= len(probabilities)),
                    "LP03_WORKER_CALIBRATION_BIN_POLICY")
    sources = _evidence_calibration_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_CALIBRATION_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-10"]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_CALIBRATION_TYPED_VALUE_JOIN")
    return decoded


def _worker_multiple_testing_inputs_v1(payload, event):
    """Typed MATH12/MATH13 data and original-source-value joins, never source authority."""
    from math import isfinite
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import (decode_evidence_public_invocation_inputs_v1, _evidence_decode_source_values_v1, _parse_typed)
    from .models import _evidence_multiple_testing_source_slices_v1
    contract = _worker_invocation_contract_v1(payload["invocation_contract"])
    math_id = contract.math_id
    _native_require(math_id in ("MATH-12", "MATH-13") and event["kind"] == "SYNTHETIC_MULTIPLE_TESTING_BATCH"
                    and event["payload"]["math_id"] == math_id,
                    "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    decoded = decode_evidence_public_invocation_inputs_v1(math_id, deterministic_json(payload["inputs"]).encode("utf-8"),
        maximum_bytes=65536, maximum_nodes=4096)
    ps, q = decoded["p_values"], decoded["q"]
    _native_require(type(ps) is tuple and 0 < len(ps) <= 32
                    and all(type(p) is float and isfinite(p) and 0.0 <= p <= 1.0 for p in ps)
                    and type(q) is float and isfinite(q) and 0.0 < q < 1.0,
                    "LP03_WORKER_MULTIPLE_INPUT_TYPES")
    sources = _evidence_multiple_testing_source_slices_v1(event["payload"])
    source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                        for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in source_refs),
                    "LP03_WORKER_MULTIPLE_SOURCE_ROSTER_JOIN")
    typed = {}
    for part, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]):
        values = _evidence_decode_source_values_v1(part.reconstructed_canonical_events[0])
        typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
    # Canonical typed values retain float-vs-int and the sign of binary64 zero.
    # This applies the existing original input conversion; it is not coercion
    # of worker-provided values to make a loose equality assertion pass.
    _native_require(deterministic_json(decoded) == deterministic_json(typed), "LP03_WORKER_MULTIPLE_TYPED_VALUE_JOIN")
    return decoded


def _worker_probability_edge_clock_limits_v1(value):
    """Read exact execution restrictions; never create a grant or deadline."""
    names = ("valid_from_wall_ns", "exclusive_expiry_wall_ns", "admitted_monotonic_ns", "exclusive_deadline_monotonic_ns")
    _native_require(isinstance(value, Mapping) and set(value) == set(names)
        and all(type(value[name]) is int and 0 <= value[name] < 2**63 for name in names), "LP03_WORKER_EDGE_CLOCK_LIMIT_FIELDS")
    limits = tuple(value[name] for name in names)
    _native_require(limits[0] < limits[1] and limits[2] < limits[3], "LP03_WORKER_EDGE_CLOCK_LIMIT_ORDER")
    return limits


def _worker_probability_edge_aggregate_prefix_v1(value, measurement_or_absence):
    """Retain actual enclosing observations even when validation failed."""
    from .latency_policy import _evidence_clock_declarations_v1, _evidence_invocation_measurement_v1
    _native_require(isinstance(value, Mapping) and set(value) == {
        "clock_identity", "clock_declarations", "started", "completed", "call_outcome", "measurement_failure_class_or_none"},
        "LP03_WORKER_EDGE_AGGREGATE_PREFIX_FIELDS")
    identity = value["clock_identity"]
    _native_require(isinstance(identity, Mapping) and set(identity) == {"clock_domain_id", "boot_identity_ref", "process_identity_ref"},
                    "LP03_WORKER_EDGE_AGGREGATE_PREFIX_IDENTITY")
    for text in identity.values():
        _native_ident(text)
    _evidence_clock_declarations_v1(value["clock_declarations"])
    for name in ("started", "completed"):
        sample = value[name]
        _native_require(sample is None or type(sample) in (tuple,list) and len(sample) == 3
            and all(type(counter) is int and 0 <= counter < 2**63 for counter in sample),
            "LP03_WORKER_EDGE_AGGREGATE_PREFIX_SAMPLE")
    _native_require(type(value["call_outcome"]) is str and value["call_outcome"] in ("NOT_STARTED", "ENTERED", "SUCCESS", "FAILED")
        and ((value["started"] is None) == (value["call_outcome"] == "NOT_STARTED"))
        and (value["completed"] is None or value["started"] is not None), "LP03_WORKER_EDGE_AGGREGATE_PREFIX_PROGRESS")
    failure = value["measurement_failure_class_or_none"]
    if failure is not None:
        _native_ident(failure)
    _native_require(isinstance(measurement_or_absence, Mapping), "LP03_WORKER_EDGE_AGGREGATE_MEASUREMENT")
    if "state" in measurement_or_absence:
        _native_require(set(measurement_or_absence) == {"state", "reason"}
            and measurement_or_absence["state"] == "ABSENT_WITH_REASON"
            and measurement_or_absence["reason"] in ("INVOCATION_NOT_STARTED", "INVOCATION_CLOCK_UNAVAILABLE"),
            "LP03_WORKER_EDGE_AGGREGATE_MEASUREMENT_ABSENCE")
        if measurement_or_absence["reason"] == "INVOCATION_NOT_STARTED":
            _native_require(value["started"] is None and value["completed"] is None
                and value["call_outcome"] == "NOT_STARTED" and failure is None,
                "LP03_WORKER_EDGE_AGGREGATE_NOT_STARTED")
        else:
            _native_require(failure is not None, "LP03_WORKER_EDGE_AGGREGATE_UNAVAILABLE_REASON")
    else:
        measured = _evidence_invocation_measurement_v1(measurement_or_absence)
        _native_require(all(measured[name] == text for name,text in identity.items())
            and deterministic_json(measured["clock_declarations"]) == deterministic_json(value["clock_declarations"])
            and deterministic_json(measured["started"]) == deterministic_json(value["started"])
            and deterministic_json(measured["completed"]) == deterministic_json(value["completed"])
            and measured["outcome"] == value["call_outcome"] and failure is None,
            "LP03_WORKER_EDGE_AGGREGATE_ORIGINAL_SAMPLE_JOIN")
    # A failed sample ordering remains diagnostic. Only the existing native
    # measurement validator can mark the enclosing interval validated.
    return _evidence_frozen_data_v1(value)


def _worker_probability_edge_capacity_v1(*, clock, contracts, attempt_ref, fence_ref, original_record_refs,
                                         market_input_json, frame_byte_limit, remaining_output_bytes):
    """Reserve success plus a later diagnostic before either original call.

    The objects below are width templates only. They are never measurements,
    frames sent to the parent, or evidence records. Every ceiling comes from
    the original grant. A smaller residual chain limit is an admission bound.
    """
    from dataclasses import fields
    from .implementation_registry import EvidencePrivateInvocationContractV1, LP03_DECIMAL_CONTEXT_POLICY_REF_V1
    from .latency_policy import _EvidenceLocalClockV1
    from .serialization import _encode_evidence_projection_json_v1
    _native_require(type(clock) is _EvidenceLocalClockV1 and type(contracts) is tuple and len(contracts) == 2
        and all(type(row) is EvidencePrivateInvocationContractV1 for row in contracts)
        and tuple(row.math_id for row in contracts) == ("MATH-01", "MATH-02")
        and type(frame_byte_limit) is int and 0 < frame_byte_limit <= 65536
        and type(remaining_output_bytes) is int and 0 < remaining_output_bytes < 2**63
        and type(market_input_json) is bytes and 0 < len(market_input_json) <= frame_byte_limit,
        "LP03_WORKER_EDGE_CAPACITY_ARGUMENTS")
    _native_ident(attempt_ref);_native_ident(fence_ref)
    _native_require(len(attempt_ref + "::CONVERSION") <= 256, "LP03_WORKER_EDGE_CAPACITY_DERIVED_ID")
    # The original source decoder supplies this canonical wire; check that
    # width premise explicitly, without executing M01 or constructing money.
    _worker_edge_json_data_v1(market_input_json.decode("utf-8", "strict"), maximum_bytes=frame_byte_limit)
    _native_require(all(byte >= 32 for byte in market_input_json), "LP03_WORKER_EDGE_CAPACITY_CANONICAL_WIRE")
    contract_data = tuple({field.name:(list(getattr(row, field.name)) if field.name == "owner_bindings"
                                    else getattr(row, field.name)) for field in fields(EvidencePrivateInvocationContractV1)}
                          for row in contracts)
    for row in contract_data:
        _worker_invocation_contract_v1(row)
    _native_require(type(original_record_refs) in (tuple,list) and 0 < len(original_record_refs) <= 256,
                    "LP03_WORKER_EDGE_CAPACITY_READ_ROSTER")
    refs = []
    for row in original_record_refs:
        _native_require(isinstance(row, Mapping) and set(row) == {"store_id", "record_id"}, "LP03_WORKER_EDGE_CAPACITY_READ_REF")
        _native_ident(row["store_id"]);_native_ident(row["record_id"])
        refs.append(dict(store_id=row["store_id"], record_id=row["record_id"]))
    declarations = _EvidenceLocalClockV1.declaration_v1(clock)
    native_declarations = {name:dict(implementation=declarations[name]["implementation"],
        reported_resolution_ns=tuple(declarations[name]["reported_resolution_ns"]),
        uncertainty_ns_or_absence=dict(declarations[name]["uncertainty_ns_or_absence"]))
        for name in ("wall", "monotonic", "process_cpu")}
    identity = dict(clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref,
                    process_identity_ref=clock.process_identity_ref)
    maximum_counter = 2**63 - 1
    sizing_sample = (maximum_counter,) * 3
    sizing_measurement = dict(identity, clock_declarations=native_declarations, started=sizing_sample,
        completed=sizing_sample, duration_ns=maximum_counter, cpu_ns=maximum_counter, outcome="SUCCESS")
    # A permitted exception label has at most 256 characters. Four UTF-8 bytes
    # per character also cover the two-level quote/backslash expansion here.
    maximum_label = "\U0001f4a1" * 256
    def absent_capture():
        # Longer than either actual capture-state/value metadata or any of
        # this closed prefix's fixed absence reasons; payload bytes are added
        # separately. This template is never accepted as a real diagnostic.
        return dict(state="ABSENT_WITH_REASON", reason="X" * 64)
    returns = [dict(stage=name, return_status="X" * 32, captured_member_count=10,
        input_json_or_absence=absent_capture(), output_json_or_absence=absent_capture()) for name in ("MATH-01", "MATH-02")]
    descriptors = [dict(captured_member_count=4, fields=dict(type_name="Decimal", shape="scalar", unit="dimensionless",
        basis="winning payout-normalized probability")), dict(captured_member_count=4,
        fields=dict(type_name="float64", shape="scalar", unit="probability points", basis="unit interval"))]
    conversion = dict(return_status="X" * 32, captured_member_count=11, input_descriptor_captures=descriptors,
        receipt_json_or_absence=absent_capture(), converted_binary64_or_absence=absent_capture())
    stages = [dict(stage=name, status="X" * 64, started=sizing_sample, completed=sizing_sample, call_outcome="X" * 16,
        measurement_validation="NOT_VALIDATED", measurement_json_or_absence=absent_capture(),
        measurement_failure_class=maximum_label if index == 0 else None,
        call_failure_class=maximum_label if index == 0 else None, return_processing_failure_class=None)
        for index,name in enumerate(("MATH-01", "CONVERSION::DECIMAL_PROBABILITY_TO_FINITE_FLOAT64_V1", "MATH-02"))]
    # Only the active stage can have error labels: failed call + measurement,
    # or successful return processing + measurement. All nine keys remain;
    # seven nulls cover either placement of the two maximum-width labels.
    sizing_prefix = dict(profile="CAPTURED_ORIGINAL_STACK_PREFIX_DIAGNOSTIC_NO_RESULT_AUTHORITY_V1",
        stack_id="STACK::MATH-01::MATH-02::V3_4", edge_id="EDGE::MATH-01::MATH-02",
        conversion_receipt_id=attempt_ref + "::CONVERSION", phase="X" * 32, failure_phase="X" * 32,
        original_serialized_bytes=maximum_counter, clock_identity=identity, clock_declarations=native_declarations,
        execution_clock_limits={name:maximum_counter for name in (
            "valid_from_wall_ns", "exclusive_expiry_wall_ns", "admitted_monotonic_ns", "exclusive_deadline_monotonic_ns")},
        returns=returns, conversion=conversion, stages=stages)
    sizing_prefix_wire = _encode_evidence_projection_json_v1(sizing_prefix, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    def frame_width(kind, payload):
        # Include each real transport prefix in the total output reservation.
        return 4 + len(_encode_evidence_projection_json_v1(dict(protocol=WORKER_PROTOCOL_V1, kind=kind,
            attempt_ref=attempt_ref, fence_ref=fence_ref, ordinal=maximum_counter, payload=payload),
            maximum_bytes=frame_byte_limit, maximum_nodes=4096))
    success_base = frame_width("COMPUTATION_RESULT", dict(event_ordinal=0, invocation_contract=contract_data[1],
        producer_invocation_contract=contract_data[0], numeric_context_policy_ref=LP03_DECIMAL_CONTEXT_POLICY_REF_V1,
        raw_output_json="X" * 128, original_record_refs=refs, invocation_measurement=sizing_measurement, chain_artifact_json=""))
    failure_base = frame_width("FAILED", dict(reason_code=maximum_label, exception_class=maximum_label, event_ordinal=0,
        measurement_or_absence=sizing_measurement, invocation_contract=contract_data[1], producer_invocation_contract=contract_data[0],
        aggregate_observation_prefix=dict(clock_identity=identity, clock_declarations=native_declarations,
            started=sizing_sample, completed=sizing_sample, call_outcome="NOT_STARTED", measurement_failure_class_or_none=maximum_label),
        chain_prefix_or_absence=dict(state="CAPTURED_ORIGINAL_PREFIX_DIAGNOSTIC", prefix_json=sizing_prefix_wire.decode("utf-8"))))
    absence_failure_base = frame_width("FAILED", dict(reason_code=maximum_label, exception_class=maximum_label, event_ordinal=0,
        measurement_or_absence=sizing_measurement, invocation_contract=contract_data[1], producer_invocation_contract=contract_data[0],
        aggregate_observation_prefix=dict(clock_identity=identity, clock_declarations=native_declarations,
            started=sizing_sample, completed=sizing_sample, call_outcome="NOT_STARTED", measurement_failure_class_or_none=maximum_label),
        chain_prefix_or_absence=dict(state="ABSENT_WITH_REASON", reason="ORIGINAL_PREFIX_ENCODING_FAILED",
                                    capture_exception_class_or_none=maximum_label)))
    failure_base = max(failure_base, absence_failure_base)
    segment_bound = frame_width("SEGMENT", dict(segment_ordinal=0, first_event_ordinal=0, last_event_ordinal=0, computations=2, complete=True))
    complete_bound = frame_width("COMPLETE", dict(events=1, computations=2, segments=1))
    # Every canonical JSON byte is non-control ASCII or UTF-8. Two string
    # embeddings multiply only quotes/backslashes by four, other bytes by one.
    market_embedded_content = sum(4 if byte in (34,92) else 1 for byte in market_input_json)
    fixed_total = success_base + failure_base + segment_bound + complete_bound + market_embedded_content
    chain_limit = min(65536, (frame_byte_limit + 4 - success_base) // 2,
        (frame_byte_limit + 4 - failure_base - market_embedded_content) // 4,
        (remaining_output_bytes - fixed_total) // 6)
    _native_require(chain_limit > 0, "LP03_WORKER_EDGE_OUTPUT_RESERVATION_EXHAUSTED")
    success_bound = success_base + 2 * chain_limit
    failure_bound = failure_base + market_embedded_content + 4 * chain_limit
    total_bound = success_bound + segment_bound + complete_bound + failure_bound
    _native_require(success_bound <= frame_byte_limit + 4 and failure_bound <= frame_byte_limit + 4
        and total_bound <= remaining_output_bytes, "LP03_WORKER_EDGE_OUTPUT_RESERVATION_JOIN")
    # Binding the original measured chain additionally checks its minimum
    # measurement scope before its first call. No limit is enlarged here.
    return MappingProxyType(dict(chain_output_limit=chain_limit, success_frame_bound=success_bound,
        failure_frame_bound=failure_bound, segment_frame_bound=segment_bound, complete_frame_bound=complete_bound,
        total_remaining_output_reservation=total_bound, market_double_embedded_content_bytes=market_embedded_content))


def _worker_probability_edge_inputs_v1(payload, event, *, attempt_ref):
    """Decode this closed stack's external data; confer no source custody."""
    from datetime import UTC, datetime, timedelta
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .input_resolver import _extract, _evidence_decode_source_values_v1, _parse_typed
    from .models import (ComputationExecutionContextV1, ComputationScopeV1, ImplementationVersionPinV1,
                         _evidence_probability_edge_chain_sources_v1)
    from .serialization import _native_strict_json, _encode_evidence_projection_json_v1
    _native_ident(attempt_ref)
    contracts = (_worker_invocation_contract_v1(payload["producer_invocation_contract"]),
                 _worker_invocation_contract_v1(payload["invocation_contract"]))
    _native_require(tuple(row.math_id for row in contracts) == ("MATH-01", "MATH-02")
        and contracts[0].resource_policy_ref == contracts[1].resource_policy_ref
        and all(row.origin_policy == "SOFTWARE_CONFORMANCE" for row in contracts)
        and event["kind"] == "SYNTHETIC_SAME_SNAPSHOT_PROBABILITY_EDGE",
        "LP03_WORKER_EDGE_CHAIN_EXACT_CONTRACTS")
    inputs = payload["inputs"]
    _native_require(isinstance(inputs, Mapping) and set(inputs) == {
        "market_input_json", "model_input_json", "execution_context_json", "conversion_receipt_id"}
        and all(type(value) is str and 0 < len(value) <= 65536 for value in inputs.values())
        and inputs["conversion_receipt_id"] == attempt_ref + "::CONVERSION"
        and len(inputs["conversion_receipt_id"]) <= 256,
        "LP03_WORKER_EDGE_CHAIN_PENDING_INPUT_FIELDS")
    _native_ident(inputs["conversion_receipt_id"])
    input_bytes = 0
    for text in inputs.values():
        for char in text:
            point = ord(char)
            _native_require(not 0xD800 <= point <= 0xDFFF, "LP03_WORKER_EDGE_CHAIN_INPUT_UTF8")
            input_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
            _native_require(input_bytes <= 65536, "LP03_WORKER_EDGE_CHAIN_INPUT_BYTE_BOUND")
    sources = _evidence_probability_edge_chain_sources_v1(event["payload"])
    refs = tuple(dict(store_id=part.original_record_refs[0].store_id, record_id=part.original_record_refs[0].record_id)
                 for part in sources)
    _native_require(all(sum(dict(ref) == source_ref for ref in payload["original_record_refs"]) == 1 for source_ref in refs),
                    "LP03_WORKER_EDGE_CHAIN_SOURCE_ROSTER_JOIN")
    events = tuple(part.reconstructed_canonical_events[0] for part in sources)
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-01"]
    market = {binding.input_name:_extract(source["values"], binding.exact_field_path)
              for binding,source in zip(bindings,events[:2],strict=True)}
    edge_bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-02"]
    model = {binding.input_name:_parse_typed(_evidence_decode_source_values_v1(source)[binding.exact_field_path],binding)
             for binding,source in zip((edge_bindings[0],edge_bindings[2]),events[2:],strict=True)}
    market_wire, model_wire = (inputs[name].encode("utf-8", "strict") for name in ("market_input_json", "model_input_json"))
    _native_require(_encode_evidence_projection_json_v1(market, maximum_bytes=65536, maximum_nodes=4096) == market_wire
        and _encode_evidence_projection_json_v1(model, maximum_bytes=65536, maximum_nodes=4096) == model_wire,
        "LP03_WORKER_EDGE_CHAIN_ORIGINAL_SOURCE_VALUES")
    # Only original external source data exists here. The missing market
    # probability cannot be supplied through this pending input segment.
    for raw,names in ((market_wire,{"contract_price","payout_per_winning_contract"}),
                      (model_wire,{"calibrated_model_probability","calibration_state"})):
        value = _native_strict_json(raw, max_bytes=65536, max_nodes=4096, binary64_numbers=True)
        _native_require(type(value) is dict and set(value) == names, "LP03_WORKER_EDGE_CHAIN_PENDING_INPUT_FIELDS")
    first = events[0]
    decision_ns = first["native_clocks"]["as_of_time"]
    _native_require(all(source["native_clocks"]["as_of_time"] == decision_ns for source in events)
        and decision_ns < first["values"]["contract_context"]["horizon_end_wall_ns"],
        "LP03_WORKER_EDGE_CHAIN_SNAPSHOT_HORIZON")
    decision = datetime(1970,1,1,tzinfo=UTC) + timedelta(microseconds=decision_ns // 1000)
    scope_fields = ("market_scope_id","venue_scope_id","event_scope_id","instrument_or_contract_scope_id","mode_context_id","input_snapshot_id")
    _native_require(set(first["scope"]) == set(scope_fields), "LP03_WORKER_EDGE_CHAIN_CONTEXT_SCOPE")
    context = ComputationExecutionContextV1(context_id=first["context_id"], as_of=decision, observed_at=decision,
        source_epoch_id=first["source_epoch_id"], input_version=first["input_version"],
        maximum_age=timedelta(microseconds=min(source["ttl_ns"] for source in events)//1000),
        scope=ComputationScopeV1(**{name:first["scope"][name] for name in scope_fields}),
        binding_profile_version="3.4", parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1",
        implementation_versions=tuple(ImplementationVersionPinV1(row.math_id,row.raw_implementation_id) for row in contracts),
        dependency_graph_id="STACK::MATH-01::MATH-02::V3_4", dependency_graph_version="3.4")
    context_wire = inputs["execution_context_json"].encode("utf-8", "strict")
    _native_strict_json(context_wire, max_bytes=65536, max_nodes=4096, binary64_numbers=True)
    _native_require(deterministic_json(context).encode("utf-8") == context_wire,
                    "LP03_WORKER_EDGE_CHAIN_ORIGINAL_CONTEXT_RECONSTRUCTION")
    return contracts, context, market_wire, model_wire, inputs["conversion_receipt_id"]


def _worker_edge_text_bytes_v1(text, *, maximum_bytes, allow_empty=False):
    """Bound this stack's nested UTF-8 text before allocating its byte copy."""
    _native_require(type(maximum_bytes) is int and 0 < maximum_bytes <= 65536 and type(allow_empty) is bool
        and type(text) is str and (0 if allow_empty else 1) <= len(text) <= maximum_bytes, "LP03_WORKER_EDGE_JSON_BOUND")
    size = 0
    for char in text:
        point = ord(char)
        _native_require(not 0xD800 <= point <= 0xDFFF, "LP03_WORKER_EDGE_JSON_UTF8")
        size += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(size <= maximum_bytes, "LP03_WORKER_EDGE_JSON_BOUND")
    return text.encode("utf-8", "strict")


def _worker_edge_json_data_v1(text, *, maximum_bytes):
    """Read this stack's canonical data without any execution authority."""
    from .serialization import _native_strict_json, _encode_evidence_projection_json_v1
    raw = _worker_edge_text_bytes_v1(text, maximum_bytes=maximum_bytes)
    data = _native_strict_json(raw, max_bytes=maximum_bytes, max_nodes=4096, binary64_numbers=True)
    _native_require(_encode_evidence_projection_json_v1(data, maximum_bytes=maximum_bytes, maximum_nodes=4096) == raw,
                    "LP03_WORKER_EDGE_JSON_CANONICAL")
    return raw, data


def _worker_probability_edge_result_v1(payload, *, attempt_ref):
    """Validate completed stack data; never execute a formula or conversion."""
    import math
    import struct
    from dataclasses import fields
    from .context import parse_utc
    from .models import ComputationExecutionContextV1, ComputationScopeV1
    from .input_resolver import decode_evidence_public_invocation_inputs_v1
    from .specification import decode_evidence_raw_output_v1
    from .latency_policy import _evidence_invocation_measurement_v1
    contracts = (_worker_invocation_contract_v1(payload["producer_invocation_contract"]),
                 _worker_invocation_contract_v1(payload["invocation_contract"]))
    _native_require(tuple(row.math_id for row in contracts) == ("MATH-01", "MATH-02")
        and all(row.origin_policy == "SOFTWARE_CONFORMANCE" for row in contracts)
        and contracts[0].resource_policy_ref == contracts[1].resource_policy_ref,
        "LP03_WORKER_EDGE_RESULT_CONTRACTS")
    _raw, artifact = _worker_edge_json_data_v1(payload["chain_artifact_json"], maximum_bytes=65536)
    _native_require(type(artifact) is dict and set(artifact) == {
        "profile", "stack_id", "edge_id", "use_limit", "producer_input_json", "producer_output_json",
        "conversion_receipt_json", "consumer_input_json", "consumer_output_json", "measured_original_stages", "measurement_scope"} | ({"execution_clock_limits"} if "execution_clock_limits" in artifact else set())
        and artifact["profile"] == "ORIGINAL_REGISTERED_SAME_SNAPSHOT_MATH01_CONVERSION_MATH02_V1"
        and artifact["stack_id"] == "STACK::MATH-01::MATH-02::V3_4" and artifact["edge_id"] == "EDGE::MATH-01::MATH-02"
        and artifact["use_limit"] == "CONTRACT_AND_FIXTURE_ONLY_NO_MODE_ACTIVATION"
        and artifact["measurement_scope"] == "THREE_ORIGINAL_CALL_INTERVALS_EXCLUDING_INTERSTAGE_WORK",
        "LP03_WORKER_EDGE_RESULT_ARTIFACT")
    limits = (_worker_probability_edge_clock_limits_v1(artifact["execution_clock_limits"])
              if "execution_clock_limits" in artifact else None)
    producer_wire, producer_values = _worker_edge_json_data_v1(artifact["producer_input_json"], maximum_bytes=65536)
    consumer_wire, consumer_values = _worker_edge_json_data_v1(artifact["consumer_input_json"], maximum_bytes=65536)
    decode_evidence_public_invocation_inputs_v1("MATH-01", producer_wire, maximum_bytes=65536, maximum_nodes=4096)
    decode_evidence_public_invocation_inputs_v1("MATH-02", consumer_wire, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(type(producer_values) is dict and set(producer_values) == {"contract_price", "payout_per_winning_contract"}
        and all(type(value) is str and bool(value) for value in producer_values.values()), "LP03_WORKER_EDGE_RESULT_PRODUCER_TYPES")
    _native_require(type(consumer_values) is dict and set(consumer_values) == {
        "calibrated_model_probability", "market_implied_probability", "calibration_state"}
        and all(type(consumer_values[name]) is float and math.isfinite(consumer_values[name]) and 0.0 <= consumer_values[name] <= 1.0
                for name in ("calibrated_model_probability", "market_implied_probability"))
        and consumer_values["calibration_state"] == "CALIBRATED_FOR_DECLARED_CONTEXT", "LP03_WORKER_EDGE_RESULT_CONSUMER_TYPES")
    producer_raw, producer_text = _worker_edge_json_data_v1(artifact["producer_output_json"], maximum_bytes=65536)
    consumer_raw, _consumer_value = _worker_edge_json_data_v1(artifact["consumer_output_json"], maximum_bytes=65536)
    producer_result = decode_evidence_raw_output_v1("MATH-01", producer_raw, maximum_bytes=65536, maximum_nodes=4096)
    consumer_result = decode_evidence_raw_output_v1("MATH-02", consumer_raw, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(0 <= producer_result <= 1 and -1.0 <= consumer_result <= 1.0
        and artifact["consumer_output_json"] == payload["raw_output_json"], "LP03_WORKER_EDGE_RESULT_RAW_JOIN")
    _receipt_wire, receipt = _worker_edge_json_data_v1(artifact["conversion_receipt_json"], maximum_bytes=65536)
    _native_require(type(receipt) is dict and set(receipt) == {
        "receipt_id", "conversion_id", "conversion_version", "source", "target", "source_value", "converted_value",
        "rounding_and_precision", "execution_context", "failure_disposition", "no_authority_flag"}
        and receipt["receipt_id"] == attempt_ref + "::CONVERSION" and len(receipt["receipt_id"]) <= 256
        and receipt["conversion_id"] == "CONVERSION::DECIMAL_PROBABILITY_TO_FINITE_FLOAT64_V1"
        and receipt["conversion_version"] == "1.0.0"
        and receipt["source"] == dict(type_name="Decimal", shape="scalar", unit="dimensionless", basis="winning payout-normalized probability")
        and receipt["target"] == dict(type_name="float64", shape="scalar", unit="probability points", basis="unit interval")
        and receipt["source_value"] == producer_text and type(receipt["source_value"]) is str
        and type(receipt["converted_value"]) is float and math.isfinite(receipt["converted_value"])
        and 0.0 <= receipt["converted_value"] <= 1.0
        and receipt["rounding_and_precision"] == "EXACT_DECIMAL_TO_NEAREST_FINITE_IEEE754_BINARY64; NO_PRECONVERSION_ROUNDING"
        and receipt["failure_disposition"] == "DEPENDENCY_UNRESOLVED_BLOCK_CONTEXT_AND_STACK"
        and receipt["no_authority_flag"] is True,
        "LP03_WORKER_EDGE_RESULT_CONVERSION")
    _native_ident(receipt["receipt_id"])
    _native_require(type(consumer_values) is dict and set(consumer_values) == {
        "calibrated_model_probability", "market_implied_probability", "calibration_state"}
        and type(consumer_values["market_implied_probability"]) is float
        and struct.pack(">d", consumer_values["market_implied_probability"]) == struct.pack(">d", receipt["converted_value"]),
        "LP03_WORKER_EDGE_RESULT_CONVERTED_BITS")
    context = receipt["execution_context"]
    _native_require(type(context) is dict and set(context) == {field.name for field in fields(ComputationExecutionContextV1)}
        and context["dependency_graph_id"] == artifact["stack_id"] and context["dependency_graph_version"] == "3.4"
        and context["binding_profile_version"] == "3.4" and context["parameter_policy_version"] == "ST12F_PARAMETER_RESOURCE_ROW_V1"
        and context["implementation_versions"] == [dict(math_spec_id=row.math_id, implementation_id=row.raw_implementation_id) for row in contracts]
        and type(context["scope"]) is dict and set(context["scope"]) == {field.name for field in fields(ComputationScopeV1)}
        and type(context["maximum_age"]) is float and math.isfinite(context["maximum_age"]) and context["maximum_age"] > 0.0
        and type(context["as_of"]) is str and context["as_of"] == context["observed_at"],
        "LP03_WORKER_EDGE_RESULT_CONTEXT")
    _native_require(parse_utc(context["as_of"], field_name="edge execution as_of").isoformat() == context["as_of"],
                    "LP03_WORKER_EDGE_RESULT_CONTEXT_TIME")
    for name in ("context_id", "source_epoch_id", "input_version"):
        _native_ident(context[name])
    for value in context["scope"].values():
        _native_ident(value)
    aggregate = _evidence_invocation_measurement_v1(payload["invocation_measurement"])
    _native_require(aggregate["outcome"] == "SUCCESS", "LP03_WORKER_EDGE_RESULT_AGGREGATE")
    if limits is not None:
        _native_require(all(limits[0] <= sample[0] < limits[1] and limits[2] <= sample[1] < limits[3]
            for sample in (aggregate["started"], aggregate["completed"])), "LP03_WORKER_EDGE_RESULT_AGGREGATE_CLOCK_LIMIT")
    stages = artifact["measured_original_stages"]
    names = ("MATH-01", "CONVERSION::DECIMAL_PROBABILITY_TO_FINITE_FLOAT64_V1", "MATH-02")
    _native_require(type(stages) is list and len(stages) == 3, "LP03_WORKER_EDGE_RESULT_STAGE_ROSTER")
    previous = aggregate["started"]
    for name, row in zip(names, stages, strict=True):
        _native_require(type(row) is dict and set(row) == {"stage", "measurement", "scope"} and row["stage"] == name
            and row["scope"] == "ORIGINAL_CALL_WITH_CUSTODY_CHECKS_RETURN_CAPTURE_AND_ACCOUNTING_BEFORE_WITNESS_AND_SERIALIZATION",
            "LP03_WORKER_EDGE_RESULT_STAGE_SCOPE")
        measured = _evidence_invocation_measurement_v1(row["measurement"])
        _native_require(measured["outcome"] == "SUCCESS"
            and all(measured[field] == aggregate[field] for field in (
                "clock_domain_id", "boot_identity_ref", "process_identity_ref", "clock_declarations"))
            and all(a <= b <= c <= d for a,b,c,d in zip(previous, measured["started"], measured["completed"], aggregate["completed"], strict=True)),
            "LP03_WORKER_EDGE_RESULT_STAGE_NESTING")
        if limits is not None:
            _native_require(all(limits[0] <= sample[0] < limits[1] and limits[2] <= sample[1] < limits[3]
                for sample in (measured["started"], measured["completed"])), "LP03_WORKER_EDGE_RESULT_STAGE_CLOCK_LIMIT")
        previous = measured["completed"]
    # The original parent separately joins both input wires and this context
    # to its original pending source packet. This decoder confers no custody.
    return artifact


def _worker_probability_edge_failure_v1(payload, *, attempt_ref):
    """Read diagnostic captures without promoting them to successful output."""
    import struct
    from .latency_policy import _evidence_invocation_measurement_v1, _evidence_clock_declarations_v1
    contracts = (_worker_invocation_contract_v1(payload["producer_invocation_contract"]),
                 _worker_invocation_contract_v1(payload["invocation_contract"]))
    _native_require(tuple(row.math_id for row in contracts) == ("MATH-01", "MATH-02")
        and all(row.origin_policy == "SOFTWARE_CONFORMANCE" for row in contracts)
        and contracts[0].resource_policy_ref == contracts[1].resource_policy_ref,
        "LP03_WORKER_EDGE_FAILURE_CONTRACTS")
    outer_prefix = (_worker_probability_edge_aggregate_prefix_v1(payload["aggregate_observation_prefix"], payload["measurement_or_absence"])
                    if "aggregate_observation_prefix" in payload else None)
    envelope = payload["chain_prefix_or_absence"]
    _native_require(isinstance(envelope, Mapping), "LP03_WORKER_EDGE_FAILURE_PREFIX")
    if envelope.get("state") == "ABSENT_WITH_REASON":
        _native_require(set(envelope) == {"state", "reason", "capture_exception_class_or_none"}
            and envelope["reason"] in ("CHAIN_NOT_CREATED", "CHAIN_NOT_STARTED", "ORIGINAL_PREFIX_ENCODING_FAILED"),
            "LP03_WORKER_EDGE_FAILURE_PREFIX_ABSENCE")
        name = envelope["capture_exception_class_or_none"]
        _native_require((name is None and envelope["reason"] != "ORIGINAL_PREFIX_ENCODING_FAILED")
            or (type(name) is str and 0 < len(name) <= 256 and envelope["reason"] == "ORIGINAL_PREFIX_ENCODING_FAILED"),
            "LP03_WORKER_EDGE_FAILURE_PREFIX_EXCEPTION")
        if name is not None:
            _native_ident(name)
        return None
    _native_require(set(envelope) == {"state", "prefix_json"}
        and envelope["state"] == "CAPTURED_ORIGINAL_PREFIX_DIAGNOSTIC", "LP03_WORKER_EDGE_FAILURE_PREFIX")
    _wire, data = _worker_edge_json_data_v1(envelope["prefix_json"], maximum_bytes=65536)
    _native_require(type(data) is dict and set(data) == {
        "profile", "stack_id", "edge_id", "conversion_receipt_id", "phase", "failure_phase", "original_serialized_bytes",
        "clock_identity", "clock_declarations", "returns", "conversion", "stages"} | ({"execution_clock_limits"} if "execution_clock_limits" in data else set())
        and data["profile"] == "CAPTURED_ORIGINAL_STACK_PREFIX_DIAGNOSTIC_NO_RESULT_AUTHORITY_V1"
        and data["stack_id"] == "STACK::MATH-01::MATH-02::V3_4" and data["edge_id"] == "EDGE::MATH-01::MATH-02"
        and data["conversion_receipt_id"] == attempt_ref + "::CONVERSION" and len(data["conversion_receipt_id"]) <= 256
        and data["phase"] in ("FAILED", "COMPLETED"), "LP03_WORKER_EDGE_FAILURE_PREFIX_SCOPE")
    limits = (_worker_probability_edge_clock_limits_v1(data["execution_clock_limits"])
              if "execution_clock_limits" in data else None)
    phases = ("MATH01_RUNNING", "MATH01_RETURNED", "CONVERSION_RUNNING", "CONVERSION_RETURNED", "MATH02_RUNNING", "MATH02_RETURNED")
    _native_require((data["phase"] == "FAILED" and data["failure_phase"] in phases)
        or (data["phase"] == "COMPLETED" and data["failure_phase"] is None), "LP03_WORKER_EDGE_FAILURE_PHASE")
    _native_require(type(data["original_serialized_bytes"]) is int and 0 <= data["original_serialized_bytes"] <= 65536,
                    "LP03_WORKER_EDGE_FAILURE_ACCOUNTING")
    identities = data["clock_identity"]
    _native_require(type(identities) is dict and set(identities) == {"clock_domain_id", "boot_identity_ref", "process_identity_ref"},
                    "LP03_WORKER_EDGE_FAILURE_CLOCK_IDENTITY")
    for value in identities.values():
        _native_ident(value)
    _evidence_clock_declarations_v1(data["clock_declarations"])
    if outer_prefix is not None:
        _native_require(dict(outer_prefix["clock_identity"]) == identities
            and deterministic_json(outer_prefix["clock_declarations"]) == deterministic_json(data["clock_declarations"]),
            "LP03_WORKER_EDGE_FAILURE_OUTER_CLOCK_JOIN")
        _native_require(outer_prefix["started"] is not None
            and (outer_prefix["call_outcome"] == "FAILED" if data["phase"] == "FAILED"
                 else outer_prefix["call_outcome"] in ("SUCCESS", "FAILED")),
            "LP03_WORKER_EDGE_FAILURE_OUTER_PROGRESS_JOIN")
    aggregate = payload["measurement_or_absence"]
    if "state" not in aggregate:
        _evidence_invocation_measurement_v1(aggregate)
        _native_require(all(aggregate[name] == value for name,value in identities.items())
            and deterministic_json(aggregate["clock_declarations"]) == deterministic_json(data["clock_declarations"]),
                        "LP03_WORKER_EDGE_FAILURE_AGGREGATE_IDENTITY")
    def captured(value, absence_reason):
        _native_require(type(value) is dict, "LP03_WORKER_EDGE_FAILURE_CAPTURE_FIELDS")
        if value.get("state") == "ABSENT_WITH_REASON":
            _native_require(value == dict(state="ABSENT_WITH_REASON", reason=absence_reason),
                            "LP03_WORKER_EDGE_FAILURE_CAPTURE_ABSENCE")
            return None
        _native_require(set(value) == {"state", "value"} and value["state"] == "CAPTURED_ORIGINAL_BYTES",
                        "LP03_WORKER_EDGE_FAILURE_CAPTURE_FIELDS")
        _worker_edge_text_bytes_v1(value["value"], maximum_bytes=65536, allow_empty=True)
        return value["value"]
    returns = data["returns"]
    _native_require(type(returns) is list and len(returns) == 2, "LP03_WORKER_EDGE_FAILURE_RETURN_ROSTER")
    for name,row in zip(("MATH-01", "MATH-02"), returns, strict=True):
        _native_require(type(row) is dict and set(row) == {
            "stage", "return_status", "captured_member_count", "input_json_or_absence", "output_json_or_absence"}
            and row["stage"] == name and row["return_status"] in ("NOT_RETURNED", "RETURNED_UNWITNESSED", "WITNESSED")
            and type(row["captured_member_count"]) is int and 0 <= row["captured_member_count"] <= 10,
            "LP03_WORKER_EDGE_FAILURE_RETURN_FIELDS")
        count = row["captured_member_count"]
        captured(row["input_json_or_absence"], "CAPTURED_INPUT_MEMBER_NOT_BYTES" if count >= 2 else "ORIGINAL_INPUT_BYTES_NOT_CAPTURED")
        captured(row["output_json_or_absence"], "CAPTURED_OUTPUT_MEMBER_NOT_BYTES" if count >= 6 else "ORIGINAL_OUTPUT_BYTES_NOT_CAPTURED")
        _native_require((count >= 2 or row["input_json_or_absence"]["state"] == "ABSENT_WITH_REASON")
            and (count >= 6 or row["output_json_or_absence"]["state"] == "ABSENT_WITH_REASON")
            and (row["return_status"] != "NOT_RETURNED" or count == 0)
            and (row["return_status"] != "WITNESSED" or count == 10), "LP03_WORKER_EDGE_FAILURE_RETURN_CAPTURE_JOIN")
        if row["return_status"] == "WITNESSED":
            _native_require(all(row[field]["state"] == "CAPTURED_ORIGINAL_BYTES" and bool(row[field]["value"])
                for field in ("input_json_or_absence", "output_json_or_absence")), "LP03_WORKER_EDGE_FAILURE_WITNESSED_WIRE")
    conversion = data["conversion"]
    _native_require(type(conversion) is dict and set(conversion) == {
        "return_status", "captured_member_count", "input_descriptor_captures", "receipt_json_or_absence", "converted_binary64_or_absence"}
        and conversion["return_status"] in ("NOT_RETURNED", "RETURNED_UNWITNESSED", "WITNESSED")
        and type(conversion["captured_member_count"]) is int and 0 <= conversion["captured_member_count"] <= 11,
        "LP03_WORKER_EDGE_FAILURE_CONVERSION_FIELDS")
    count = conversion["captured_member_count"]
    descriptors = conversion["input_descriptor_captures"]
    _native_require(type(descriptors) is list and len(descriptors) == 2, "LP03_WORKER_EDGE_FAILURE_DESCRIPTOR_ROSTER")
    for descriptor in descriptors:
        _native_require(type(descriptor) is dict and set(descriptor) == {"captured_member_count", "fields"}
            and type(descriptor["captured_member_count"]) is int and 0 <= descriptor["captured_member_count"] <= 4
            and type(descriptor["fields"]) is dict
            and set(descriptor["fields"]) == set(("type_name", "shape", "unit", "basis")[:descriptor["captured_member_count"]])
            and all(type(value) is str and 0 < len(value) <= 256 for value in descriptor["fields"].values()),
            "LP03_WORKER_EDGE_FAILURE_DESCRIPTOR_CAPTURE")
    _native_require((conversion["return_status"] != "NOT_RETURNED" or count == 0)
        and (conversion["return_status"] != "WITNESSED" or count == 11), "LP03_WORKER_EDGE_FAILURE_CONVERSION_CAPTURE_JOIN")
    receipt = captured(conversion["receipt_json_or_absence"], "ORIGINAL_RECEIPT_BYTES_NOT_ENCODED")
    if receipt is not None:
        receipt = _worker_edge_json_data_v1(receipt, maximum_bytes=65536)[1]
    converted = conversion["converted_binary64_or_absence"]
    _native_require(type(converted) is dict, "LP03_WORKER_EDGE_FAILURE_CONVERTED_FIELDS")
    if converted.get("state") == "ABSENT_WITH_REASON":
        _native_require(converted == dict(state="ABSENT_WITH_REASON",
            reason="CAPTURED_CONVERTED_MEMBER_NOT_BINARY64" if count >= 7 else "ORIGINAL_CONVERTED_VALUE_NOT_CAPTURED"),
            "LP03_WORKER_EDGE_FAILURE_CONVERTED_ABSENCE")
    else:
        _native_require(set(converted) == {"state", "big_endian_hex"} and converted["state"] == "CAPTURED_ORIGINAL_BINARY64"
            and count >= 7 and type(converted["big_endian_hex"]) is str and len(converted["big_endian_hex"]) == 16
            and all(char in "0123456789abcdef" for char in converted["big_endian_hex"]),
            "LP03_WORKER_EDGE_FAILURE_CONVERTED_FIELDS")
        if receipt is not None:
            _native_require(type(receipt) is dict and type(receipt.get("converted_value")) is float
                and struct.pack(">d", receipt["converted_value"]).hex() == converted["big_endian_hex"],
                "LP03_WORKER_EDGE_FAILURE_CONVERTED_BITS")
    if conversion["return_status"] == "WITNESSED":
        _native_require(converted["state"] == "CAPTURED_ORIGINAL_BINARY64"
            and descriptors == [dict(captured_member_count=4, fields=dict(type_name="Decimal", shape="scalar",
                unit="dimensionless", basis="winning payout-normalized probability")),
                dict(captured_member_count=4, fields=dict(type_name="float64", shape="scalar", unit="probability points", basis="unit interval"))],
            "LP03_WORKER_EDGE_FAILURE_WITNESSED_CONVERSION")
    stages = data["stages"]
    names = ("MATH-01", "CONVERSION::DECIMAL_PROBABILITY_TO_FINITE_FLOAT64_V1", "MATH-02")
    _native_require(type(stages) is list and len(stages) == 3, "LP03_WORKER_EDGE_FAILURE_STAGE_ROSTER")
    statuses = ("NOT_ENTERED", "START_CLOCK_PENDING", "START_CLOCK_FAILED", "CALL_ENTERED", "RETURN_CAPTURE_PENDING",
        "END_CLOCK_PENDING", "END_CLOCK_OBSERVED", "END_CLOCK_OBSERVED_RETURN_CAPTURE_INCOMPLETE",
        "MEASUREMENT_ENCODED_UNVALIDATED", "RETURNED_UNWITNESSED", "CALL_FAILED", "MEASUREMENT_UNAVAILABLE_OR_UNENCODED", "VALIDATED")
    for name,row in zip(names,stages,strict=True):
        _native_require(type(row) is dict and set(row) == {"stage", "status", "started", "completed", "call_outcome",
            "measurement_validation", "measurement_json_or_absence", "measurement_failure_class", "call_failure_class",
            "return_processing_failure_class"} and row["stage"] == name and row["status"] in statuses
            and row["call_outcome"] in ("NOT_ENTERED", "ENTERED", "SUCCESS", "FAILED")
            and row["measurement_validation"] in ("VALIDATED", "NOT_VALIDATED"), "LP03_WORKER_EDGE_FAILURE_STAGE_FIELDS")
        for field in ("started", "completed"):
            sample = row[field]
            _native_require(sample is None or (type(sample) is list and len(sample) == 3
                and all(type(value) is int and 0 <= value < 2**63 for value in sample)), "LP03_WORKER_EDGE_FAILURE_RAW_OBSERVATION")
        for field in ("measurement_failure_class", "call_failure_class", "return_processing_failure_class"):
            value = row[field]
            _native_require(value is None or type(value) is str and 0 < len(value) <= 256,
                            "LP03_WORKER_EDGE_FAILURE_EXCEPTION_CLASS")
            if value is not None:
                _native_ident(value)
        measurement = captured(row["measurement_json_or_absence"], "ORIGINAL_MEASUREMENT_BYTES_NOT_ENCODED")
        if measurement is not None:
            measurement = _worker_edge_json_data_v1(measurement, maximum_bytes=65536)[1]
            _native_require(type(measurement) is dict and set(measurement) == {"stage", "measurement", "scope"}
                and measurement["stage"] == name
                and measurement["scope"] == "ORIGINAL_CALL_WITH_CUSTODY_CHECKS_RETURN_CAPTURE_AND_ACCOUNTING_BEFORE_WITNESS_AND_SERIALIZATION"
                and type(measurement["measurement"]) is dict, "LP03_WORKER_EDGE_FAILURE_MEASUREMENT_FIELDS")
            native = measurement["measurement"]
            _native_require(native.get("started") == row["started"] and native.get("completed") == row["completed"]
                and native.get("outcome") == row["call_outcome"] and all(native.get(key) == value for key,value in identities.items())
                and deterministic_json(native.get("clock_declarations")) == deterministic_json(data["clock_declarations"]),
                "LP03_WORKER_EDGE_FAILURE_MEASUREMENT_CAPTURE_JOIN")
            if row["measurement_validation"] == "VALIDATED":
                _evidence_invocation_measurement_v1(native)
        else:
            _native_require(row["measurement_validation"] == "NOT_VALIDATED", "LP03_WORKER_EDGE_FAILURE_MISSING_MEASUREMENT")
    # A diagnostic can describe an invalid observation or unwitnessed return,
    # but it must still describe a reachable ordered prefix of this operation.
    reached = 2 if data["phase"] == "COMPLETED" else phases.index(data["failure_phase"]) // 2
    returned = (returns[0], conversion, returns[1])
    for index,(stage,result) in enumerate(zip(stages,returned,strict=True)):
        entered = stage["call_outcome"] in ("ENTERED", "SUCCESS", "FAILED")
        successful_return = stage["call_outcome"] == "SUCCESS"
        _native_require(successful_return == (result["return_status"] != "NOT_RETURNED")
            and (not entered or stage["started"] is not None)
            and (stage["completed"] is None or stage["started"] is not None), "LP03_WORKER_EDGE_FAILURE_PROGRESS_JOIN")
        if stage["status"] == "NOT_ENTERED":
            _native_require(stage["call_outcome"] == "NOT_ENTERED" and stage["started"] is None and stage["completed"] is None
                and stage["measurement_validation"] == "NOT_VALIDATED"
                and stage["measurement_json_or_absence"]["state"] == "ABSENT_WITH_REASON"
                and all(stage[field] is None for field in (
                    "measurement_failure_class", "call_failure_class", "return_processing_failure_class")),
                "LP03_WORKER_EDGE_FAILURE_NOT_ENTERED")
        if stage["status"] == "START_CLOCK_FAILED":
            _native_require(stage["call_outcome"] == "NOT_ENTERED" and stage["completed"] is None
                and stage["measurement_failure_class"] is not None and stage["measurement_validation"] == "NOT_VALIDATED"
                and stage["measurement_json_or_absence"]["state"] == "ABSENT_WITH_REASON", "LP03_WORKER_EDGE_FAILURE_START_FAILURE")
        if stage["measurement_validation"] == "VALIDATED":
            _native_require(stage["status"] in ("RETURNED_UNWITNESSED", "CALL_FAILED", "VALIDATED")
                and stage["started"] is not None and stage["completed"] is not None,
                "LP03_WORKER_EDGE_FAILURE_VALIDATED_MEASUREMENT")
            if limits is not None:
                _native_require(all(limits[0] <= sample[0] < limits[1] and limits[2] <= sample[1] < limits[3]
                    for sample in (stage["started"], stage["completed"])), "LP03_WORKER_EDGE_FAILURE_VALIDATED_CLOCK_LIMIT")
        if stage["status"] in ("RETURNED_UNWITNESSED", "CALL_FAILED", "VALIDATED"):
            _native_require(stage["measurement_validation"] == "VALIDATED"
                and stage["call_outcome"] == ("FAILED" if stage["status"] == "CALL_FAILED" else "SUCCESS"),
                "LP03_WORKER_EDGE_FAILURE_MEASURED_STATUS")
        if stage["status"] == "VALIDATED":
            _native_require(result["return_status"] == "WITNESSED", "LP03_WORKER_EDGE_FAILURE_VALIDATED_RETURN")
        _native_require((stage["call_failure_class"] is not None) == (stage["call_outcome"] == "FAILED"),
                        "LP03_WORKER_EDGE_FAILURE_CALL_FAILURE_CLASS")
        _native_require(stage["return_processing_failure_class"] is None or stage["call_outcome"] == "SUCCESS",
                        "LP03_WORKER_EDGE_FAILURE_RETURN_PROCESSING_CAUSE")
        if index < reached or index > reached or data["phase"] == "COMPLETED":
            _native_require(all(stage[field] is None for field in (
                "measurement_failure_class", "call_failure_class", "return_processing_failure_class")),
                "LP03_WORKER_EDGE_FAILURE_INACTIVE_STAGE_LABELS")
        if index < reached or data["phase"] == "COMPLETED":
            _native_require(stage["status"] == "VALIDATED" and result["return_status"] == "WITNESSED",
                            "LP03_WORKER_EDGE_FAILURE_PREVIOUS_STAGE")
        if index > reached:
            _native_require(stage["status"] == "NOT_ENTERED" and result["captured_member_count"] == 0,
                            "LP03_WORKER_EDGE_FAILURE_LATER_STAGE")
        if index == reached and data["phase"] == "FAILED":
            _native_require(successful_return == data["failure_phase"].endswith("_RETURNED"),
                            "LP03_WORKER_EDGE_FAILURE_ACTIVE_RETURN_PHASE")
    if data["phase"] == "COMPLETED":
        _native_require(receipt is not None and all(row["input_json_or_absence"]["state"] == "CAPTURED_ORIGINAL_BYTES"
            and row["output_json_or_absence"]["state"] == "CAPTURED_ORIGINAL_BYTES" for row in returns)
            and all(stage[field] is None for stage in stages for field in (
                "measurement_failure_class", "call_failure_class", "return_processing_failure_class")),
            "LP03_WORKER_EDGE_FAILURE_COMPLETED_CAPTURES")
    # Data may expose the integrity/measurement failure that caused the stop.
    # Do not require a successful-result schema or invent missing observations.
    return data


def _worker_canonical_object_v1(raw, *, max_bytes):
    from .serialization import _native_strict_json
    body = _native_strict_json(raw, max_bytes=max_bytes, max_nodes=4096, binary64_numbers=True)
    _native_require(type(body) is dict and deterministic_json(body).encode("utf-8") == raw, "LP03_NONCANONICAL_JSON")
    # _worker_frame_v1 freezes all fields and permits native floats only in the
    # exact typed MATH08/MATH09/MATH10/MATH12/MATH13 input fields after its closed source/contract joins.
    return body


def _evidence_decode_heldout_worker_artifact_v1(raw, *, topology_math_id, topology_raw_json,
    scorer_contract, maximum_bytes, maximum_nodes):
    """Check every original fold scorer continuation in the closed worker frame."""
    from .implementation_registry import EvidencePrivateInvocationContractV1
    from .latency_policy import _evidence_invocation_measurement_v1
    from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1
    from .specification import decode_evidence_raw_output_v1

    _native_require(type(topology_math_id) is str and topology_math_id in ("MATH-20","MATH-21")
        and type(scorer_contract) is EvidencePrivateInvocationContractV1
        and scorer_contract.math_id in ("MATH-08","MATH-09")
        and scorer_contract.origin_policy=="SOFTWARE_CONFORMANCE","LP03_FOLD_WORKER_ORIGINAL_CONTRACT")
    _native_require(type(maximum_bytes) is int and 0<maximum_bytes<=65536
        and type(maximum_nodes) is int and 0<maximum_nodes<=4096
        and type(raw) is bytes and type(topology_raw_json) is bytes and
            0<len(raw)+len(topology_raw_json)<=maximum_bytes,
        "LP03_FOLD_WORKER_COMPLETE_FRAME_BUDGET")
    value=_evidence_canonical_object_v1(raw,max_bytes=maximum_bytes)
    _native_require(set(value)=={"profile","topology_math_id","scorer_math_id","folds"}
        and value["profile"]=="ORIGINAL_WORKER_HELD_OUT_SCORES_V1"
        and value["topology_math_id"]==topology_math_id and value["scorer_math_id"]==scorer_contract.math_id,
        "LP03_FOLD_WORKER_ARTIFACT_FIELDS")
    topology=decode_evidence_raw_output_v1(topology_math_id,topology_raw_json,
        maximum_bytes=maximum_bytes,maximum_nodes=maximum_nodes)
    splits=topology["folds" if topology_math_id=="MATH-20" else "splits"]
    folds=value["folds"]
    _native_require(type(folds) is list and 2<=len(folds)==len(splits)<=(4 if topology_math_id=="MATH-20" else 6),
        "LP03_FOLD_WORKER_COMPLETE_SCORE_ROSTER")
    prediction_refs,training_refs=set(),set()
    previous=None
    for ordinal,(record,split) in enumerate(zip(folds,splits,strict=True)):
        _native_require(type(record) is dict and set(record)=={"ordinal","training_receipt_ref","sample_receipts",
            "scorer_raw_json","invocation_measurement"} and type(record["ordinal"]) is int and record["ordinal"]==ordinal,
            "LP03_FOLD_WORKER_SCORE_FIELDS")
        train=record["training_receipt_ref"]
        _native_ident(train)
        _native_require(train not in training_refs,"LP03_FOLD_WORKER_TRAINING_RECEIPT_ROSTER")
        training_refs.add(train)
        receipts=record["sample_receipts"]
        names=split["test_sample_ids"]
        _native_require(type(receipts) is list and 0<len(receipts)==len(names)<=8,"LP03_FOLD_WORKER_SCORE_SAMPLE_ROSTER")
        for row,identifier in zip(receipts,names,strict=True):
            _native_require(type(row) is dict and set(row)=={"sample_id","label_receipt_ref","prediction_receipt_ref","prediction_available_wall_ns","outcome_available_wall_ns"}
                and row["sample_id"]==identifier,"LP03_FOLD_WORKER_SCORE_SAMPLE_ORDER")
            for key in ("sample_id","label_receipt_ref","prediction_receipt_ref"):
                _native_ident(row[key])
            _public_counter_v1(row["prediction_available_wall_ns"], allow_zero=False)
            _public_counter_v1(row["outcome_available_wall_ns"], allow_zero=False)
            _native_require(row["prediction_available_wall_ns"] < row["outcome_available_wall_ns"]
                and row["label_receipt_ref"]!=row["prediction_receipt_ref"]
                and row["prediction_receipt_ref"] not in prediction_refs,"LP03_FOLD_WORKER_SCORE_RECEIPT_JOIN")
            prediction_refs.add(row["prediction_receipt_ref"])
        text=record["scorer_raw_json"]
        _native_require(type(text) is str and 0<len(text)<=maximum_bytes,"LP03_FOLD_WORKER_SCORER_RAW_WIRE")
        raw_score=decode_evidence_raw_output_v1(scorer_contract.math_id,text.encode("utf-8","strict"),
            maximum_bytes=maximum_bytes,maximum_nodes=maximum_nodes)
        _native_require(len(raw_score["per_observation"])==len(names)
            and deterministic_json(raw_score)==text,"LP03_FOLD_WORKER_SCORER_RAW_SCORE_ROSTER")
        result=_evidence_invocation_measurement_v1(record["invocation_measurement"])
        _native_require(result["outcome"]=="SUCCESS","LP03_FOLD_WORKER_SCORER_NATIVE_SUCCESS")
        if previous is not None:
            _native_require((result["clock_domain_id"],result["process_identity_ref"],result["boot_identity_ref"])==(
                previous["clock_domain_id"],previous["process_identity_ref"],previous["boot_identity_ref"])
                and all(a<=b for a,b in zip(previous["completed"],result["started"],strict=True)),
                "LP03_FOLD_WORKER_SCORER_NATIVE_CHRONOLOGY")
        previous=result
    _native_require(prediction_refs.isdisjoint(training_refs),"LP03_FOLD_WORKER_SCORER_RECEIPT_IDENTITY")
    return _evidence_frozen_data_v1(value)


def _evidence_decode_recorded_dr_worker_artifact_v1(artifact_json, *, raw_output_json, attempt_ref,
                                                       topology_measurement, maximum_bytes):
    """Check a complete observed M22 continuation before lane publication."""
    from .latency_policy import _evidence_invocation_measurement_v1
    from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1, _native_strict_json

    _native_require(type(maximum_bytes) is int and 0 < maximum_bytes <= 65536 and type(artifact_json) is str
        and 0 < len(artifact_json) <= maximum_bytes and type(raw_output_json) is str,
        "LP03_DR_WORKER_CONTINUATION_WIRE")
    _native_ident(attempt_ref)
    artifact = _evidence_canonical_object_v1(artifact_json.encode("utf-8", "strict"), max_bytes=maximum_bytes)
    _native_require(set(artifact) == {"profile", "estimator_original_raw_ref", "certificate_json", "invocation_measurement"}
        and artifact["profile"] == "ORIGINAL_WORKER_RECORDED_DR_UNCERTAINTY_V1"
        and artifact["estimator_original_raw_ref"] == attempt_ref + "::DATA::RAW"
        and type(artifact["certificate_json"]) is str,
        "LP03_DR_WORKER_CONTINUATION_FIELDS")
    body = artifact["certificate_json"].encode("utf-8", "strict")
    certificate = _native_strict_json(body, max_bytes=maximum_bytes, max_nodes=4096, binary64_numbers=True)
    _native_require(type(certificate) is dict and set(certificate) == {
            "profile", "disposition", "target", "reasons", "original_raw", "original_policy", "original_input",
            "group_means", "arithmetic", "interval", "source_admission", "measurement_model_uncertainty"}
        and certificate["target"] == "MEAN_CONDITIONAL_RECORDED_DR_SCORE"
        and certificate["profile"] == "RECORDED_DR_UNCERTAINTY_DATA_V1"
        and certificate["disposition"] in ("CONDITIONAL_DATA_CALCULATION", "UNCERTAINTY_UNAVAILABLE")
        and certificate["original_policy"]["raw_receipt_ref"] == artifact["estimator_original_raw_ref"]
        and deterministic_json(certificate) == artifact["certificate_json"]
        and deterministic_json(certificate["original_raw"]) == raw_output_json,
        "LP03_DR_WORKER_CONTINUATION_ORIGINAL_RAW")
    current = _evidence_invocation_measurement_v1(artifact["invocation_measurement"])
    prior = _evidence_invocation_measurement_v1(topology_measurement)
    _native_require(current["outcome"] == prior["outcome"] == "SUCCESS"
        and all(current[name] == prior[name] for name in ("clock_domain_id", "boot_identity_ref", "process_identity_ref"))
        and all(a <= b for a,b in zip(prior["completed"], current["started"], strict=True)),
        "LP03_DR_WORKER_CONTINUATION_NATIVE_CLOCKS")
    return _evidence_frozen_data_v1(artifact), certificate


def _evidence_original_quantum_constructor_result_v1(
    math_id, raw_wire, constructor_wire, *, maximum_bytes, input_lock_ref=None, original_values=None,
):
    """Decode the retained worker pair, optionally joining the protected original inputs."""
    from decimal import localcontext
    from .context import decimal_context_v1
    from .quantum_benchmark import QuantumClassicalNoTradeComparisonV1, QuantumTraceValidationReceiptV1
    from .serialization import _evidence_canonical_object_v1, deterministic_json
    from .specification import decode_evidence_raw_output_v1

    _native_require(math_id in ("MATH-50", "MATH-51", "MATH-52")
        and type(maximum_bytes) is int and 0 < maximum_bytes <= 65536,
        "LP03_ORIGINAL_QUANTUM_RESULT_PROFILE")
    encoded = []
    for text in (raw_wire, constructor_wire):
        _native_require(type(text) is str and 0 < len(text) <= maximum_bytes,
            "LP03_ORIGINAL_QUANTUM_COMPLETE_WIRE_BOUND")
        wire = text.encode("utf-8", "strict")
        _native_require(len(wire) <= maximum_bytes, "LP03_ORIGINAL_QUANTUM_COMPLETE_WIRE_BOUND")
        encoded.append(wire)
    raw = decode_evidence_raw_output_v1(math_id, encoded[0], maximum_bytes=maximum_bytes, maximum_nodes=4096)
    data = _evidence_canonical_object_v1(encoded[1], max_bytes=maximum_bytes)
    with localcontext(decimal_context_v1()):
        if math_id == "MATH-52":
            receipt = QuantumClassicalNoTradeComparisonV1.from_canonical_mapping(data)
            _native_require(receipt.winner == raw["winner"] and receipt.quantum_advantage_claim_allowed is False
                and str(receipt.delta_quantum_vs_classical) == str(raw["delta_quantum_vs_classical"])
                and str(receipt.delta_quantum_vs_no_trade) == str(raw["delta_quantum_vs_no_trade"]),
                "LP03_ORIGINAL_QUANTUM_MATCHED_COMPARISON_RAW")
            if original_values is not None:
                quantum = original_values["quantum_receipt"]
                _native_require(receipt.comparison_id == original_values["comparison_id"]
                    and receipt.validated_quantum == quantum.as_comparator()
                    and receipt.strongest_classical == original_values["strongest_classical_receipt"]
                    and receipt.no_trade == original_values["no_trade_receipt"]
                    and receipt.comparison_basis == quantum.comparison_basis,
                    "LP03_ORIGINAL_QUANTUM_ORIGINAL_COMPETING_RECEIPTS")
        else:
            receipt = QuantumTraceValidationReceiptV1.from_canonical_mapping(data)
            qaoa = math_id == "MATH-50"
            objective = "trace_expected_locked_cost" if qaoa else "trace_expectation"
            variance = "EXPLICIT_ABSENCE" if qaoa else str(raw["variance"])
            _native_require(receipt.math_spec_id == math_id and receipt.terminal_state == "VALIDATED_TRACE_ONLY"
                and receipt.quantum_advantage_claim_allowed is False and raw["effect_call_count"] == 0
                and str(receipt.recomputed_objective) == str(raw[objective])
                and str(receipt.recomputed_variance_or_explicit_absence) == variance
                and str(receipt.original_economic_utility) == str(raw["original_economic_objective"])
                and receipt.selected_candidate_id == raw["selected_candidate_id"]
                and receipt.selected_original_model_feasible is raw["selected_original_model_feasible"] is True,
                "LP03_ORIGINAL_QUANTUM_TRACE_RAW_JOIN")
            if original_values is not None:
                trace = original_values["trace"]
                coordinate = "candidate_id" if qaoa else "parameter_point_id"
                selected_id = trace.selected_candidate_id if qaoa else trace.selected_point_id
                selected = next((point for point in trace.points if getattr(point, coordinate) == selected_id), None)
                _native_require(selected is not None and receipt.receipt_id == f"ST12F-QUANTUM-TRACE::{trace.trace_id}"
                    and (receipt.trace_id, receipt.formulation_id, receipt.selected_candidate_id)
                        == (trace.trace_id, trace.formulation_id, selected_id)
                    and receipt.input_lock_id == trace.input_lock_id and receipt.comparison_basis == trace.comparison_basis
                    and receipt.strongest_classical_receipt_ref == trace.strongest_classical_comparator.receipt_id
                    and receipt.no_trade_receipt_ref == trace.no_trade_comparator.receipt_id
                    and receipt.deterministic_tie_break == selected_id
                    and receipt.selected_original_model_feasible is selected.original_model_feasible
                    and str(receipt.original_economic_utility) == str(selected.original_economic_utility)
                    and str(receipt.resource_use) == str(selected.resource_use)
                    and str(receipt.latency) == str(selected.latency),
                    "LP03_ORIGINAL_QUANTUM_ORIGINAL_TRACE_AND_COMPARATORS")
        _native_require((input_lock_ref is None or receipt.input_lock_id == input_lock_ref)
            and deterministic_json(receipt) == constructor_wire,
            "LP03_ORIGINAL_QUANTUM_IMMUTABLE_LOCK_AND_WIRE")
    return raw, receipt


def _worker_frame_v1(value, *, direction, attempt_ref, fence_ref, ordinal):
    _native_require(isinstance(value, Mapping) and set(value) == {"protocol", "kind", "attempt_ref", "fence_ref", "ordinal", "payload"},
                    "LP03_WORKER_FRAME_FIELDS")
    _native_require(direction in ("PARENT_TO_WORKER", "WORKER_TO_PARENT"), "LP03_WORKER_DIRECTION")
    kinds = _PARENT_KINDS_V1 if direction == "PARENT_TO_WORKER" else _WORKER_KINDS_V1
    _native_require(type(value["kind"]) is str and value["kind"] in kinds, "LP03_WORKER_KIND_OR_DIRECTION")
    _native_require(value["protocol"] == WORKER_PROTOCOL_V1 and type(value["ordinal"]) is int
                    and value["ordinal"] == ordinal and value["attempt_ref"] == attempt_ref and value["fence_ref"] == fence_ref,
                    "LP03_WORKER_ATTEMPT_FENCE_OR_ORDINAL")
    _native_ident(attempt_ref)
    _native_ident(fence_ref)
    _public_counter_v1(ordinal, allow_zero=True)
    payload = value["payload"]
    _native_require(isinstance(payload, Mapping), "LP03_WORKER_PAYLOAD_FIELDS")
    if "profile" in payload:
        return MappingProxyType(dict(value, payload=_worker_timeline_payload_v1(value["kind"], payload)))
    routed_segment = value["kind"] == "INPUT_SEGMENT" and "invocation_contract" in payload
    edge_segment = routed_segment and "producer_invocation_contract" in payload
    edge_result = value["kind"] == "COMPUTATION_RESULT" and "producer_invocation_contract" in payload
    edge_failure = value["kind"] == "FAILED" and "chain_prefix_or_absence" in payload
    extra_fields = ({"producer_invocation_contract", "chain_artifact_json"} if edge_result else
                    {"producer_invocation_contract", "invocation_contract", "chain_prefix_or_absence"} if edge_failure else set())
    if edge_failure and "aggregate_observation_prefix" in payload:
        extra_fields |= {"aggregate_observation_prefix"}
    heldout_segment = routed_segment and "scorer_invocation_contract" in payload
    heldout_result = value["kind"] == "COMPUTATION_RESULT" and "scorer_invocation_contract" in payload
    if heldout_segment or heldout_result:
        extra_fields |= {"scorer_invocation_contract"}
    if heldout_result:
        extra_fields |= {"held_out_score_artifact_json"}
    dr_result = value["kind"] == "COMPUTATION_RESULT" and "dr_uncertainty_artifact_json" in payload
    if dr_result:
        extra_fields |= {"dr_uncertainty_artifact_json"}
    quantum_result = value["kind"] == "COMPUTATION_RESULT" and "quantum_constructor_receipt_json" in payload
    if quantum_result:
        extra_fields |= {"quantum_constructor_receipt_json"}
    expected_fields = (_PAYLOAD_FIELDS_V1[value["kind"]] | ({"invocation_contract"} if routed_segment else set())
                       | ({"producer_invocation_contract"} if edge_segment else set()) | extra_fields)
    _native_require(set(payload) == expected_fields, "LP03_WORKER_PAYLOAD_FIELDS")
    brier_inputs = None
    for name in ("event_ordinal", "segment_ordinal", "first_event_ordinal", "last_event_ordinal", "computations", "events", "segments", "process_id"):
        if name in payload:
            _public_counter_v1(payload[name], allow_zero=name != "process_id")
    for name in ("final_segment", "complete"):
        if name in payload:
            _native_require(type(payload[name]) is bool, "LP03_WORKER_BOOLEAN_FIELD")
    for name in ("record_refs", "original_record_refs"):
        if name in payload:
            refs = payload[name]
            _native_require(type(refs) in (list, tuple) and 0 < len(refs) <= 256, "LP03_WORKER_RECORD_REF_ROSTER")
            for ref in refs:
                _native_require(isinstance(ref, Mapping) and set(ref) == {"store_id", "record_id"}, "LP03_WORKER_RECORD_REF_FIELDS")
                _native_ident(ref["store_id"])
                _native_ident(ref["record_id"])
            _native_require(len({(ref["store_id"], ref["record_id"]) for ref in refs}) == len(refs), "LP03_WORKER_DUPLICATE_RECORD_REF")
    for name in ("reason_ref", "reason_code", "exception_class", "package_identity_ref", "clock_domain_id", "boot_identity_ref"):
        if name in payload:
            _native_ident(payload[name])
    if value["kind"] == "CONTINUE":
        _native_require(type(payload["command"]) is str and payload["command"] in ("COMPUTE", "FINISH"), "LP03_WORKER_COMMAND")
    if value["kind"] == "INPUT_SEGMENT":
        _native_require(isinstance(payload["inputs"], Mapping), "LP03_WORKER_INPUT_VALUES")
        from .models import _evidence_normalized_event_v1
        event = _evidence_normalized_event_v1(payload["event"])
        _native_require(event["local_ordinal"] == payload["segment_ordinal"]
                        and dict(event["source_record_ref"]) in tuple(dict(ref) for ref in payload["original_record_refs"]),
                        "LP03_WORKER_EVENT_SOURCE_JOIN")
        if routed_segment:
            edge_event = event["kind"] == "SYNTHETIC_SAME_SNAPSHOT_PROBABILITY_EDGE"
            _native_require(edge_segment == edge_event, "LP03_WORKER_EDGE_CHAIN_CLOSED_INPUT_VARIANT")
            heldout_event = event["kind"] == "SYNTHETIC_HELD_OUT_FOLD_SCORING"
            _native_require(heldout_segment == heldout_event, "LP03_WORKER_HELD_OUT_INPUT_VARIANT")
            if heldout_event:
                brier_inputs, _scored_trace = _worker_heldout_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_RECORDED_DR_UNCERTAINTY":
                brier_inputs = _worker_recorded_dr_inputs_v1(payload, event, attempt_ref=attempt_ref)
            elif event["kind"] == "SYNTHETIC_ACKNOWLEDGED_QUEUE":
                _worker_math39_queue_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_ORIGINAL_QUANTUM_INPUT":
                _worker_original_quantum_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_PRIVATE_BINARY64_EXECUTION_INPUT":
                brier_inputs = _worker_original_private_inputs_v1(payload, event)
            elif event["kind"] in ("SYNTHETIC_PRIVATE_ANALYTIC_INPUT", "SYNTHETIC_PRIVATE_DECIMAL_EXECUTION_INPUT"):
                _worker_original_private_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_RECORDED_OPE_POINT":
                brier_inputs = _worker_recorded_ope_point_inputs_v1(payload, event)
            elif edge_event:
                _worker_probability_edge_inputs_v1(payload, event, attempt_ref=attempt_ref)
            elif event["kind"] == "SYNTHETIC_SIGNED_TOTAL_CASHFLOW_CONTEXT":
                _worker_cashflow_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_MARKET_PRICE_CONTEXT":
                _worker_market_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_RESEARCH_DECISION":
                _worker_research_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_KELLY_PROBABILITY_PAYOFF_CONTEXT":
                _worker_kelly27_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_FRACTIONAL_KELLY_CONTEXT":
                _worker_kelly28_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_MULTIPLE_TESTING_BATCH":
                brier_inputs = _worker_multiple_testing_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_CALIBRATION_EVALUATION_BATCH":
                brier_inputs = _worker_calibration_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_CSCV_MATRIX_AND_GROUP_POLICY":
                brier_inputs = _worker_cscv_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_SHARPE_LEDGER_AND_MOMENTS":
                brier_inputs = _worker_sharpe_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_SPA_BATCH":
                brier_inputs = _worker_spa_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_REALITY_CHECK_BATCH":
                brier_inputs = _worker_reality_check_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_STATIONARY_BOOTSTRAP_BATCH":
                brier_inputs = _worker_bootstrap_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_BERNOULLI_COUNT_BATCH":
                brier_inputs = _worker_wilson_inputs_v1(payload, event)
            elif event["kind"] == "SYNTHETIC_LOG_LOSS_EVALUATION_BATCH":
                brier_inputs = _worker_log_loss_inputs_v1(payload, event)
            else:
                brier_inputs = _worker_brier_inputs_v1(payload, event)
        else:
            _native_require(event["kind"] == "SYNTHETIC_BOOK_SNAPSHOT", "LP03_WORKER_INPUT_PROFILE_UNAVAILABLE")
    if value["kind"] == "COMPUTATION_RESULT":
        _native_require(type(payload["raw_output_json"]) is str and 0 < len(payload["raw_output_json"]) <= 65536
                        and isinstance(payload["invocation_contract"], Mapping), "LP03_WORKER_RESULT_FIELDS")
        from .implementation_registry import LP03_DECIMAL_CONTEXT_POLICY_REF_V1
        from .specification import decode_evidence_raw_output_v1
        contract = payload["invocation_contract"]
        _worker_invocation_contract_v1(contract)
        _native_require(payload["numeric_context_policy_ref"] == LP03_DECIMAL_CONTEXT_POLICY_REF_V1, "LP03_WORKER_INVOCATION_FIELDS")
        # Closed schema validation of the exact original output bytes. The
        # nested JSON is never an authorization object or an egress exemption:
        # the original raw decoder retains the ordinary secret/path guards.
        decode_evidence_raw_output_v1(contract["math_id"], payload["raw_output_json"].encode("utf-8", "strict"),
            maximum_bytes=65536, maximum_nodes=4096)
        from .latency_policy import _evidence_invocation_measurement_v1
        measured = _evidence_invocation_measurement_v1(payload["invocation_measurement"])
        _native_require(measured["outcome"] == "SUCCESS", "LP03_WORKER_FAILED_INVOCATION_HAS_VALUE")
        if edge_result:
            _worker_probability_edge_result_v1(payload, attempt_ref=attempt_ref)
        math_id = contract["math_id"]
        _native_require(quantum_result == (math_id in ("MATH-50", "MATH-51", "MATH-52")), "LP03_WORKER_QUANTUM_RESULT_VARIANT")
        if quantum_result:
            _evidence_original_quantum_constructor_result_v1(math_id, payload["raw_output_json"],
                payload["quantum_constructor_receipt_json"], maximum_bytes=65536)
        _native_require(dr_result == (math_id == "MATH-22"), "LP03_WORKER_DR_RESULT_VARIANT")
        if dr_result:
            _evidence_decode_recorded_dr_worker_artifact_v1(payload["dr_uncertainty_artifact_json"],
                raw_output_json=payload["raw_output_json"], attempt_ref=attempt_ref,
                topology_measurement=measured, maximum_bytes=65536)
        _native_require(heldout_result == (math_id in ("MATH-20", "MATH-21")),
            "LP03_WORKER_HELD_OUT_RESULT_VARIANT")
        if heldout_result:
            scorer = _worker_invocation_contract_v1(payload["scorer_invocation_contract"])
            _native_require(type(payload["held_out_score_artifact_json"]) is str,
                "LP03_WORKER_HELD_OUT_RESULT_SCORER")
            artifact = _evidence_decode_heldout_worker_artifact_v1(
                payload["held_out_score_artifact_json"].encode("utf-8", "strict"),
                topology_math_id=math_id, topology_raw_json=payload["raw_output_json"].encode("utf-8", "strict"),
                scorer_contract=scorer, maximum_bytes=65536, maximum_nodes=4096)
            first = artifact["folds"][0]["invocation_measurement"]
            _native_require(all(first[name] == measured[name] for name in
                ("clock_domain_id", "boot_identity_ref", "process_identity_ref"))
                and all(a <= b for a, b in zip(measured["completed"], first["started"], strict=True)),
                "LP03_WORKER_HELD_OUT_AFTER_TOPOLOGY")
    if value["kind"] == "FAILED":
        from .latency_policy import _evidence_invocation_measurement_v1
        measured = payload["measurement_or_absence"]
        _native_require(isinstance(measured, Mapping), "LP03_WORKER_FAILURE_MEASUREMENT")
        if "state" in measured:
            _native_require(set(measured) == {"state", "reason"} and measured["state"] == "ABSENT_WITH_REASON"
                            and measured["reason"] in ("INVOCATION_NOT_STARTED", "INVOCATION_CLOCK_UNAVAILABLE"),
                            "LP03_WORKER_FAILURE_MEASUREMENT_ABSENCE")
        else:
            _evidence_invocation_measurement_v1(measured)
    if edge_failure:
        _worker_probability_edge_failure_v1(payload, attempt_ref=attempt_ref)
    if value["kind"] == "START":
        from .models import EvidenceSignedMessageV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1
        signed = EvidenceSignedMessageV1.from_canonical_mapping(
            _evidence_canonical_object_v1(deterministic_json(payload["signed_grant"]).encode("utf-8")))
        message = EvidenceAuthorizationMessageV1.from_canonical_mapping(
            _evidence_canonical_object_v1(signed.canonical_message.encode("utf-8")))
        _native_require(message.kind is EvidenceMessageKindV1.ATTEMPT_GRANT and message.subject == attempt_ref
                        and message.payload["fence_ref"] == fence_ref, "LP03_WORKER_START_GRANT_JOIN")
    if value["kind"] in ("START", "STARTED"):
        from .models import EvidenceEnvironmentIdentityV1
        EvidenceEnvironmentIdentityV1.from_canonical_mapping(
            _evidence_canonical_object_v1(deterministic_json(payload["environment_identity"]).encode("utf-8")))
    if value["kind"] == "STARTED":
        _native_require(all(type(payload[name]) is str and 0 < len(payload[name]) <= 4096
                            for name in ("executable", "base_executable", "prefix", "base_prefix", "module_file")),
                        "LP03_WORKER_RUNTIME_PATH_OBSERVATION")
    if brier_inputs is not None:
        frozen = _evidence_frozen_data_v1(dict(value, payload=dict(payload, inputs={})))
        return MappingProxyType(dict(frozen, payload=MappingProxyType(dict(frozen["payload"], inputs=brier_inputs))))
    return _evidence_frozen_data_v1(value)


def encode_evidence_worker_frame_v1(value, *, direction, attempt_ref, fence_ref, ordinal, frame_byte_limit):
    _native_require(type(frame_byte_limit) is int and 0 < frame_byte_limit <= 65536, "LP03_WORKER_FRAME_LIMIT")
    _native_require(type(value) is dict and len(value) == 6 and all(type(name) is str for name in value)
                    and type(value.get("kind")) is str
                    and type(value.get("payload")) is dict, "LP03_WORKER_NATIVE_FRAME_REQUIRED")
    _native_require(len(value["payload"]) <= 12 and all(type(name) is str for name in value["payload"]),
                    "LP03_WORKER_NATIVE_FRAME_REQUIRED")
    if ((value["kind"] == "INPUT_SEGMENT" and "invocation_contract" in value["payload"])
            or (value["kind"] in ("COMPUTATION_RESULT", "FAILED") and "producer_invocation_contract" in value["payload"])):
        from .serialization import _encode_evidence_projection_json_v1
        # This variant requires native JSON containers prepared from the
        # original bounded source bytes. Budget admission precedes formatting.
        raw = _encode_evidence_projection_json_v1(value, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    else:
        raw = deterministic_json(value).encode("utf-8", "strict")
    _native_require(0 < len(raw) <= frame_byte_limit, "LP03_WORKER_FRAME_TOO_LARGE")
    _worker_frame_v1(_worker_canonical_object_v1(raw, max_bytes=frame_byte_limit), direction=direction,
                     attempt_ref=attempt_ref, fence_ref=fence_ref, ordinal=ordinal)
    return len(raw).to_bytes(4, "big") + raw


def decode_evidence_worker_frame_v1(raw, *, direction, attempt_ref, fence_ref, ordinal, frame_byte_limit):
    _native_require(type(raw) is bytes and type(frame_byte_limit) is int and 0 < frame_byte_limit <= 65536,
                    "LP03_WORKER_FRAME_ENCODING")
    _native_require(4 <= len(raw) <= frame_byte_limit + 4, "LP03_WORKER_PARTIAL_OR_OVERSIZED_FRAME")
    length = int.from_bytes(raw[:4], "big")
    _native_require(0 < length <= frame_byte_limit and len(raw) == length + 4, "LP03_WORKER_PARTIAL_OR_TRAILING_FRAME")
    body = _worker_canonical_object_v1(raw[4:], max_bytes=frame_byte_limit)
    return _worker_frame_v1(body, direction=direction, attempt_ref=attempt_ref, fence_ref=fence_ref, ordinal=ordinal)


def _read_worker_frame_bytes_v1(stream, frame_byte_limit):
    """Read one bounded frame; clean EOF is distinct from any partial frame."""
    prefix = stream.read(4)
    if prefix == b"":
        return None
    _native_require(type(prefix) is bytes, "LP03_WORKER_BINARY_PIPE_REQUIRED")
    while len(prefix) < 4:
        part = stream.read(4 - len(prefix))
        _native_require(type(part) is bytes and bool(part), "LP03_WORKER_PARTIAL_EOF")
        prefix += part
    length = int.from_bytes(prefix, "big")
    _native_require(0 < length <= frame_byte_limit <= 65536, "LP03_WORKER_FRAME_TOO_LARGE")
    parts, remaining = [], length
    while remaining:
        part = stream.read(remaining)
        _native_require(type(part) is bytes and 0 < len(part) <= remaining, "LP03_WORKER_PARTIAL_EOF")
        parts.append(part)
        remaining -= len(part)
    return prefix + b"".join(parts)


def _write_worker_bytes_v1(stream, raw):
    remaining = memoryview(raw)
    while remaining:
        written = stream.write(remaining)
        _native_require(type(written) is int and 0 < written <= len(remaining), "LP03_WORKER_PIPE_WRITE_FAILED")
        remaining = remaining[written:]
    stream.flush()


def _worker_environment_v1():
    import platform
    import sys
    import sysconfig
    import cryptography
    from .models import EvidenceEnvironmentIdentityV1
    # CPython's Windows build platform is in-process data. platform.machine()
    # calls uname/win32_ver, whose fallback can launch a `ver` subprocess.
    architecture = {"win-amd64": "AMD64", "win-arm64": "ARM64", "win32": "x86"}.get(sysconfig.get_platform())
    _native_require(architecture is not None, "LP03_WORKER_PLATFORM_UNAVAILABLE")
    return EvidenceEnvironmentIdentityV1(implementation=sys.implementation.name, complete_version=sys.version,
        build=" ".join(platform.python_build()), architecture=architecture, package_versions=(("cryptography", cryptography.__version__),))


def sample_evidence_uniform53_v1(coordinates, *, expected_environment, work):
    """Pure fixed recipe; the original operation owns preregistration/budgets.

    This checks the actual local environment against supplied pinned data, but
    does not authenticate that data or admit an event/namespace/claim. The
    original owner must charge coordinates and retain the same numerical work.
    """
    from random import Random
    from .errors import ReasonCode
    from .models import EvidenceEnvironmentIdentityV1
    from .parameter_policy import _EvidenceNumericalWorkV1

    _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
    with work:
        work._require(type(coordinates) is tuple and len(coordinates) == 8, "LP03_RNG_COORDINATE_SHAPE")
        for coordinate in coordinates:
            work._require(type(coordinate) is int and 0 <= coordinate and coordinate.bit_length() <= 256,
                          "LP03_RNG_COORDINATE_DOMAIN")
            work._exact(coordinate)
        work._require(type(expected_environment) is EvidenceEnvironmentIdentityV1, "LP03_RNG_EXPECTED_ENVIRONMENT_TYPE")
        work._require(_worker_environment_v1() == expected_environment, "LP03_RNG_ENVIRONMENT_MISMATCH",
                      reason=ReasonCode.EVIDENCE_RNG_ENVIRONMENT_MISMATCH)
        prefix = b"QTT-LP03-SCENARIO-V1\0"
        widths = tuple(max(1, (coordinate.bit_length() + 7) // 8) for coordinate in coordinates)
        encoded_length = len(prefix) + sum(2 + width for width in widths)
        work._bits(encoded_length * 8)
        parts = [prefix]
        for coordinate, width in zip(coordinates, widths):
            work._consumed["integer_operations"] += 2
            parts.extend((width.to_bytes(2, "big"), coordinate.to_bytes(width, "big")))
        encoded = b"".join(parts)
        work._require(len(encoded) == encoded_length, "LP03_RNG_ENCODING_SIZE")
        work._consumed["integer_operations"] += 1
        seed = int.from_bytes(encoded, "big")
        generator = Random(seed)
        work._consumed["random_draws"] += 1
        bits = generator.getrandbits(53)
        work._require(type(bits) is int and 0 <= bits < 2**53, "LP03_RNG_U53_DOMAIN")
        uniform = work._fraction(bits, work._shift(1, 53))
        return work._emit(dict(profile="QTT_LP03_SCENARIO_MT19937_U53_V1", master_seed=coordinates[0],
            plan_revision=coordinates[1], scenario_ordinal=coordinates[2], dependence_group_ordinal=coordinates[3],
            event_ordinal=coordinates[4], variable_purpose_ordinal=coordinates[5], draw_ordinal=coordinates[6],
            namespace_ordinal=coordinates[7], encoded_coordinate=encoded.hex(), uniform53_bits=bits, uniform=uniform))


def measure_dr_score_uncertainty_v1(raw_json, *, input_json, policy_json, maximum_input_bytes,
                                  maximum_input_nodes, maximum_output_bytes, maximum_output_nodes, work,
                                  original_fit_after_first_label=False):
    """Bounded §9.3 conditional data calculation; not an admitted UNCERTAINTY.

    Original bytes and input row positions are retained. Neither these bytes
    nor policy proof-reference strings authenticate their producers. The native
    operation must join original inputs/raw/policy, measure physical resources,
    and publish its supplementary record before a metric may consume it.
    """
    from math import copysign
    from .input_resolver import decode_evidence_public_invocation_inputs_v1
    from .parameter_policy import (_EvidenceNumericalWorkV1, decode_evidence_dr_uncertainty_policy_v1,
                                   _measure_evidence_dr_group_arithmetic_v1)
    from .serialization import _encode_evidence_projection_json_v1
    from .specification import decode_evidence_raw_output_v1
    _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
    with work:
        work._require(type(maximum_output_bytes) is int and 0 < maximum_output_bytes <= 1048576
                      and type(maximum_output_nodes) is int and 0 < maximum_output_nodes <= 4096,
                      "LP03_DR_OUTPUT_BUDGET")
        work._require(type(maximum_input_bytes) is int and 0 < maximum_input_bytes <= 1048576
                      and type(maximum_input_nodes) is int and 0 < maximum_input_nodes <= 4096,
                      "LP03_DR_INPUT_BUDGET")
        # One aggregate input allowance precedes all three decoder allocations.
        work._require(all(type(value) is bytes for value in (raw_json, input_json, policy_json))
                      and sum(len(value) for value in (raw_json, input_json, policy_json)) <= maximum_input_bytes,
                      "LP03_DR_AGGREGATE_INPUT_BYTES")
        remaining_nodes = maximum_input_nodes
        def retain_nodes(value):
            nonlocal remaining_nodes
            remaining_nodes -= 1
            work._require(remaining_nodes >= 0, "LP03_DR_AGGREGATE_INPUT_NODES")
            if type(value) is MappingProxyType:
                for name, child in value.items():
                    retain_nodes(name)
                    retain_nodes(child)
            elif type(value) is tuple:
                for child in value:
                    retain_nodes(child)
        raw = decode_evidence_raw_output_v1("MATH-22", raw_json,
            maximum_bytes=maximum_input_bytes, maximum_nodes=remaining_nodes)
        retain_nodes(raw)
        work._require(remaining_nodes > 0, "LP03_DR_AGGREGATE_INPUT_NODES")
        inputs = decode_evidence_public_invocation_inputs_v1("MATH-22", input_json,
            maximum_bytes=maximum_input_bytes, maximum_nodes=remaining_nodes)
        retain_nodes(inputs)
        work._require(remaining_nodes > 0, "LP03_DR_AGGREGATE_INPUT_NODES")
        policy = decode_evidence_dr_uncertainty_policy_v1(policy_json,
            maximum_bytes=maximum_input_bytes, maximum_nodes=remaining_nodes)
        retain_nodes(policy)

        # Only the decoder-created graph is copied. Exact JSON scalar types,
        # including original negative zero, remain unchanged in the output.
        def data(value):
            if type(value) is MappingProxyType:
                return {name: data(child) for name, child in value.items()}
            if type(value) is tuple:
                return [data(child) for child in value]
            return value

        reasons = []
        def unavailable(reason):
            if reason not in reasons:
                reasons.append(reason)

        work._require(type(original_fit_after_first_label) is bool, "LP03_DR_ORIGINAL_FIT_CHRONOLOGY_TYPE")
        if original_fit_after_first_label:
            unavailable("OUTCOME_LEAKING_NUISANCE_FIT")

        rows = inputs["logged_rows"]
        work._require(type(rows) is tuple and all(type(row) is MappingProxyType for row in rows),
                      "LP03_DR_INPUT_ROW_TYPE")
        row_ids = tuple(row.get("row_id") for row in rows)
        work._require(all(type(value) is str for value in row_ids), "LP03_DR_INPUT_ROW_IDENTITY_TYPE")
        for value in row_ids:
            _native_ident(value)
        work._require(all(type(row.get("fold_id")) is int and 0 <= row["fold_id"] < 2**256 for row in rows),
                      "LP03_DR_INPUT_FOLD_ID_TYPE")
        work._require(len(set(row_ids)) == len(row_ids), "LP03_DR_DUPLICATE_INPUT_ROW_IDENTITY")
        if not row_ids or row_ids != policy["row_ids"] or len(raw["row_values"]) != len(row_ids) or len(raw["importance_weights"]) != len(row_ids):
            unavailable("RAW_INPUT_ROW_ROSTER_MISMATCH")
        groups = policy["groups"]
        if not groups or tuple(group["ordinal"] for group in groups) != tuple(range(1, len(groups) + 1)):
            unavailable("INCOMPLETE_ORDERED_GROUP_PREFIX")
        positions = {name: index for index, name in enumerate(row_ids)}
        members = tuple(name for group in groups for name in group["row_ids"])
        if len(members) != len(row_ids) or len(set(members)) != len(members) or set(members) != set(row_ids):
            unavailable("INCOMPLETE_GROUP_MEMBERSHIP")
        if any(tuple(sorted(group["row_ids"], key=lambda name: positions.get(name, -1))) != group["row_ids"] for group in groups):
            unavailable("GROUP_ROW_ORDER_CHANGED")
        if not groups or not groups[0]["row_ids"] or any(len(group["row_ids"]) != len(groups[0]["row_ids"]) for group in groups):
            unavailable("UNEQUAL_OR_EMPTY_GROUP_SIZES")
        required = ("logging_policy_ref", "support_receipt_ref", "reward_basis_ref", "crossfit_plan_ref",
                    "conditional_target_assumption_ref", "group_bound_proof_ref", "group_lower", "group_upper", "alpha")
        for name in required:
            if policy[name] is None:
                unavailable("MISSING_" + name.upper())
        if raw["clipping_applied"] is not False:
            unavailable("CLIPPED_RECORDED_SCORES_UNSUPPORTED")
        if any(value == 0 and copysign(1, value) < 0 for value in (*raw["row_values"], raw["doubly_robust_estimate"])):
            unavailable("NEGATIVE_ZERO_STATISTICAL_INPUT_UNSUPPORTED")

        evaluated = []
        fold_ids = []
        for record in policy["crossfit_records"]:
            fold_ids.append(record["fold_id"])
            evaluation = record["evaluation_row_ids"]
            evaluated.extend(evaluation)
            if set(evaluation).intersection(record["training_row_ids"]):
                unavailable("OUTCOME_LEAKING_NUISANCE_FIT")
            if record["prediction_receipt_ref"] is None or record["training_exclusion_ref"] is None:
                unavailable("MISSING_CROSSFIT_PRODUCER_RECORDS")
            if not evaluation or any(name not in positions or rows[positions[name]].get("fold_id") != record["fold_id"] for name in evaluation):
                unavailable("CROSSFIT_FOLD_MEMBERSHIP_MISMATCH")
        if len(set(fold_ids)) != len(fold_ids) or len(evaluated) != len(row_ids) or set(evaluated) != set(row_ids):
            unavailable("INCOMPLETE_CROSSFIT_COVERAGE")
        if any(row.get("cross_fitted_prediction") is not True for row in rows):
            unavailable("CROSSFIT_INPUT_STATE_UNAVAILABLE")

        parameters = {name: None if policy[name] is None else work._exact(work.parse_decimal_v1(policy[name]))
                      for name in ("group_lower", "group_upper", "alpha")}
        weights = tuple(work._exact(work.parse_decimal_v1(value)) for value in policy["group_weights"])
        zero = work._fraction(0)
        low, high, alpha = (parameters[name] for name in ("group_lower", "group_upper", "alpha"))
        if low is not None and high is not None:
            work._require(work._compare(low, high) < 0, "LP03_NUMERICAL_BOUND_OR_ALPHA_DOMAIN")
        if alpha is not None:
            work._require(work._compare(alpha, zero) > 0 and work._compare(alpha, work._fraction(1)) < 0,
                          "LP03_NUMERICAL_BOUND_OR_ALPHA_DOMAIN")
        if len(weights) != len(groups) or not weights or any(work._compare(value, zero) <= 0 or work._compare(value, weights[0]) != 0 for value in weights):
            unavailable("UNEQUAL_OR_NONPOSITIVE_GROUP_WEIGHTS")
        arithmetic, interval, group_means = None, None, []
        if not reasons:
            groups_result, arithmetic_result, interval_result = _measure_evidence_dr_group_arithmetic_v1(
                raw["row_values"], tuple(tuple(positions[name] for name in group["row_ids"]) for group in groups),
                estimator=raw["doubly_robust_estimate"], lower=low, upper=high, alpha=alpha,
                claim_ordinal=policy["claim_ordinal"], work=work)
            group_means, arithmetic, interval = data(groups_result), data(arithmetic_result), data(interval_result)
        result = dict(profile="RECORDED_DR_UNCERTAINTY_DATA_V1",
            disposition="UNCERTAINTY_UNAVAILABLE" if reasons else "CONDITIONAL_DATA_CALCULATION",
            target="MEAN_CONDITIONAL_RECORDED_DR_SCORE", reasons=reasons,
            original_raw=data(raw), original_policy=data(policy), original_input=data(inputs),
            group_means=group_means, arithmetic=arithmetic, interval=interval,
            source_admission="NOT_ESTABLISHED_BY_DATA_PROCEDURE",
            measurement_model_uncertainty="NOT_ESTABLISHED_BY_DATA_PROCEDURE")
        remaining = work.limits["max_serialized_bytes"] - work.consumed["serialized_bytes"]
        work._require(remaining > 0, "LP03_NUMERICAL_SERIALIZATION_EXHAUSTED")
        output = _encode_evidence_projection_json_v1(result,
            maximum_bytes=min(maximum_output_bytes, remaining), maximum_nodes=maximum_output_nodes)
        work._consumed["serialized_bytes"] += len(output)
        return output


def _prepare_evidence_heldout_scorer_inputs_v1(*, topology_math_id, topology_raw_json, scored_trace,
                                                scorer_contract, maximum_input_bytes, maximum_nodes):
    """Validate complete held-out coverage before the first original scorer call."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .serialization import _encode_evidence_projection_json_v1
    from .specification import decode_evidence_raw_output_v1

    _native_require(scored_trace is not None, "LP03_MISSING_PREDICTION_PRODUCER")
    _native_require(type(scored_trace) is dict and set(scored_trace)=={
        "profile","prediction_owner","prediction_model_id","prediction_model_version",
        "evaluation_cutoff_wall_ns","outcome_labels","split_traces","scorer_math_id","clip_epsilon_or_absence"},
        "LP03_FOLD_TRACE_FIELDS")
    scorer=scorer_contract.math_id
    _native_require(scorer in ("MATH-08","MATH-09") and scored_trace["scorer_math_id"]==scorer
        and scored_trace["profile"]=="SOFTWARE_CONFORMANCE_ORIGINAL_HELD_OUT_PREDICTION_TRACE_V1"
        and scored_trace["prediction_owner"]==FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-02"][0].accepted_upstream_owner_id
        and scorer_contract.origin_policy=="SOFTWARE_CONFORMANCE","LP03_FOLD_SCORER_ORIGIN_AND_PIN")
    for key in ("prediction_model_id","prediction_model_version"):
        _native_ident(scored_trace[key])
    cutoff=scored_trace["evaluation_cutoff_wall_ns"]
    _public_counter_v1(cutoff,allow_zero=False)
    topology=decode_evidence_raw_output_v1(topology_math_id,topology_raw_json,
        maximum_bytes=maximum_input_bytes,maximum_nodes=maximum_nodes)
    prescribed=topology["folds" if topology_math_id=="MATH-20" else "splits"]
    traces, labels=scored_trace["split_traces"],scored_trace["outcome_labels"]
    _native_require(type(traces) is list and 2 <= len(traces)==len(prescribed) <= 6
        and type(labels) is list and 2 <= len(labels) <= 8,"LP03_FOLD_SCORER_ROSTER")
    complete_samples={identifier for split in prescribed for identifier in split["test_sample_ids"]}
    by_sample={}
    label_refs=set()
    for label in labels:
        _native_require(type(label) is dict and set(label)=={"sample_id","available_wall_ns","label_receipt_ref","outcome_index"},
            "LP03_FOLD_OUTCOME_LABEL_FIELDS")
        identifier,ref=label["sample_id"],label["label_receipt_ref"]
        _native_ident(identifier)
        _native_ident(ref)
        _public_counter_v1(label["available_wall_ns"],allow_zero=False)
        _native_require(identifier not in by_sample and ref not in label_refs and identifier in complete_samples
            and label["available_wall_ns"]<=cutoff
            and type(label["outcome_index"]) is int and 0 <= label["outcome_index"] < 4,
            "LP03_FOLD_OUTCOME_LABEL_AVAILABILITY")
        by_sample[identifier]=label
        label_refs.add(ref)
    _native_require(set(by_sample)==complete_samples,"LP03_FOLD_OUTCOME_LABEL_ROSTER")
    seen_prediction,seen_training=set(),set()
    prepared=[]
    # Validate coverage, original model lineage, and chronology of every
    # prescribed fold before invoking any scorer. No partial topology-only
    # collection can be returned as a complete score distribution.
    for ordinal,(split,trace) in enumerate(zip(prescribed,traces,strict=True)):
        _native_require(type(trace) is dict and set(trace)=={"ordinal","training_sample_ids","training_receipt_ref",
            "training_maximum_known_wall_ns","prediction_rows"} and type(trace["ordinal"]) is int
            and trace["ordinal"]==ordinal,"LP03_FOLD_TRACE_SPLIT_FIELDS")
        training,train_ref=trace["training_sample_ids"],trace["training_receipt_ref"]
        training_cut=trace["training_maximum_known_wall_ns"]
        _native_ident(train_ref)
        _public_counter_v1(training_cut,allow_zero=True)
        _native_require(type(training) is list and len(training)<=8 and all(type(item) is str for item in training)
            and tuple(training)==split["train_sample_ids"] and not set(training).intersection(split["test_sample_ids"])
            and train_ref not in seen_training and train_ref not in label_refs,"LP03_FOLD_ORIGINAL_TRAINING_EXCLUSION")
        seen_training.add(train_ref)
        predictions=trace["prediction_rows"]
        expected=split["test_sample_ids"]
        _native_require(type(predictions) is list and 0 < len(predictions)==len(expected)<=8,
            "LP03_FOLD_PREDICTION_ROSTER")
        rows,outcomes,refs=[],[],[]
        for identifier,prediction in zip(expected,predictions,strict=True):
            _native_require(type(prediction) is dict and set(prediction)=={"sample_id","issued_wall_ns","prediction_receipt_ref",
                "training_receipt_ref","model_id","model_version","probabilities"},"LP03_FOLD_PREDICTION_FIELDS")
            receipt,issued=prediction["prediction_receipt_ref"],prediction["issued_wall_ns"]
            _native_ident(receipt)
            _public_counter_v1(issued,allow_zero=False)
            label=by_sample[identifier]
            _native_require(prediction["sample_id"]==identifier and receipt not in seen_prediction and receipt not in label_refs
                and receipt not in seen_training and prediction["training_receipt_ref"]==train_ref
                and prediction["model_id"]==scored_trace["prediction_model_id"]
                and prediction["model_version"]==scored_trace["prediction_model_version"]
                and training_cut<=issued<label["available_wall_ns"]<=cutoff,"LP03_FOLD_PREDICTION_PREOUTCOME_JOIN")
            probabilities=prediction["probabilities"]
            _native_require(type(probabilities) is list and 2 <= len(probabilities) <=4
                and all(type(value) is float and 0.0 <= value <=1.0 for value in probabilities)
                and label["outcome_index"] < len(probabilities),"LP03_FOLD_PREDICTION_PROBABILITY_DOMAIN")
            seen_prediction.add(receipt)
            rows.append(probabilities)
            outcomes.append(label["outcome_index"])
            refs.append(dict(sample_id=identifier, prediction_receipt_ref=receipt,
                label_receipt_ref=label["label_receipt_ref"], prediction_available_wall_ns=issued,
                outcome_available_wall_ns=label["available_wall_ns"]))
        inputs=dict(probability_rows=rows,outcome_indices=outcomes)
        clip=scored_trace["clip_epsilon_or_absence"]
        if scorer=="MATH-09":
            _native_require(type(clip) is float and 0.0 < clip < 0.5,"LP03_FOLD_SCORER_CLIP_POLICY")
            inputs["clip_epsilon"]=clip
        else:
            _native_require(clip==dict(state="ABSENT_WITH_REASON",reason="BRIER_NO_CLIP"),"LP03_FOLD_SCORER_CLIP_POLICY")
        raw_input=_encode_evidence_projection_json_v1(inputs,maximum_bytes=maximum_input_bytes,maximum_nodes=maximum_nodes)
        prepared.append((ordinal,train_ref,tuple(refs),raw_input))
    _native_require(seen_prediction.isdisjoint(seen_training)
        and sum(len(row[3]) for row in prepared)<=maximum_input_bytes,"LP03_FOLD_SCORER_COMPLETE_INPUT_BUDGET")
    return tuple(prepared)


def measure_evidence_fold_scores_v1(*, topology_math_id, topology_raw_json, scored_trace, scorer_contract, clock, grant, message,
                                    maximum_input_bytes, maximum_output_bytes, maximum_nodes):
    """Run the pinned scorer once per prescribed fold in the original worker.

    The caller must already have validated the signed grant, actual topology
    execution, and exact original source/view associations. This adapter only
    consumes the bounded supported software trace and emits actual scorer
    invocations. It cannot authorize any model fit or provider request.
    """
    from .context import _native_require
    from .implementation_registry import EvidencePrivateInvocationContractV1, invoke_evidence_public_wire_v1
    from .latency_policy import _EvidenceLocalClockV1, _evidence_invocation_measurement_v1
    from .models import EvidenceAttemptGrantPayloadV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1

    _native_require(type(topology_math_id) is str and topology_math_id in ("MATH-20","MATH-21")
        and type(scorer_contract) is EvidencePrivateInvocationContractV1
        and type(clock) is _EvidenceLocalClockV1 and type(grant) is EvidenceAttemptGrantPayloadV1
        and type(message) is EvidenceAuthorizationMessageV1 and message.kind is EvidenceMessageKindV1.ATTEMPT_GRANT
        and grant.component_closure == (topology_math_id,), "LP03_FOLD_SCORER_ORIGINAL_CONTRACT")
    _native_require(type(maximum_input_bytes) is int and 0 < maximum_input_bytes <= 65536
        and type(maximum_output_bytes) is int and 0 < maximum_output_bytes <= 65536
        and type(maximum_nodes) is int and 0 < maximum_nodes <= 4096,
        "LP03_FOLD_SCORER_FINITE_ALLOWANCE")
    deadline = grant.deadline
    _native_require((deadline.clock_domain_id, deadline.boot_identity_ref) == (
        clock.clock_domain_id, clock.boot_identity_ref),
        "LP03_FOLD_SCORER_NATIVE_CLOCK_JOIN")
    _native_require(grant.component_and_callback_pins.get("supplementary_scorers") == ((
            scorer_contract.math_id, scorer_contract.raw_implementation_id,
            scorer_contract.mathematical_semantic_version, scorer_contract.resource_policy_ref),),
        "LP03_FOLD_SCORER_SIGNED_PIN_JOIN")

    def observe_current():
        sample = _EvidenceLocalClockV1.observe_v1(clock)
        _native_require(message.valid_from_wall_ns <= sample[0] < message.exclusive_expiry_wall_ns
            and deadline.admitted_monotonic_ns <= sample[1] < deadline.exclusive_deadline_monotonic_ns,
            "LP03_FOLD_SCORER_ORIGINAL_DEADLINE")
        return sample

    prepared = _prepare_evidence_heldout_scorer_inputs_v1(topology_math_id=topology_math_id,
        topology_raw_json=topology_raw_json, scored_trace=scored_trace, scorer_contract=scorer_contract,
        maximum_input_bytes=maximum_input_bytes, maximum_nodes=maximum_nodes)
    # Reserve framed evidence and every sample lineage before the first
    # scorer call. The enclosing worker charges its exact final transport.
    # Actual source IDs and native clock declarations determine the fixed
    # metadata. Public counters and binary64 number spellings have finite maxima.
    largest_counter = (1 << 256) - 1
    largest_reading = (largest_counter,) * 3
    declarations = _EvidenceLocalClockV1.declaration_v1(clock)
    measurement_shell = dict(clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref,
        process_identity_ref=clock.process_identity_ref, clock_declarations=declarations,
        started=largest_reading, completed=largest_reading, duration_ns=largest_counter,
        cpu_ns=largest_counter, outcome="SUCCESS")
    shell = dict(profile="ORIGINAL_WORKER_HELD_OUT_SCORES_V1", topology_math_id=topology_math_id,
        scorer_math_id=scorer_contract.math_id, folds=tuple(dict(ordinal=ordinal,
            training_receipt_ref=train_ref, sample_receipts=refs, scorer_raw_json="",
            invocation_measurement=measurement_shell) for ordinal,train_ref,refs,_ in prepared))
    framing_reserve = len(deterministic_json(shell).encode("utf-8"))
    # The two frozen scorer schemas both contain one mean and one scalar for
    # each observation. Reserve each token and JSON-string escaping in advance.
    fold_limits = tuple(128 + 32 * (1 + len(refs)) for _,_,refs,_ in prepared)
    _native_require(framing_reserve + sum(fold_limits) <= maximum_output_bytes,
        "LP03_FOLD_SCORER_COMPLETE_OUTPUT_BUDGET")
    measured=[]
    for (ordinal,train_ref,refs,raw_input), output_limit in zip(prepared,fold_limits,strict=True):
        started = observe_current()
        original=invoke_evidence_public_wire_v1(scorer_contract,raw_input,
            maximum_input_bytes=maximum_input_bytes,maximum_nodes=maximum_nodes,maximum_output_bytes=output_limit,
            maximum_output_nodes=maximum_nodes)
        finished = observe_current()
        _native_require(original.contract is scorer_contract,
            "LP03_FOLD_SCORER_ORIGINAL_RESULT_JOIN")
        measurement=_evidence_invocation_measurement_v1(dict(clock_domain_id=clock.clock_domain_id,
            boot_identity_ref=clock.boot_identity_ref,process_identity_ref=clock.process_identity_ref,
            clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock),started=started,completed=finished,
            duration_ns=finished[1]-started[1],cpu_ns=finished[2]-started[2],outcome="SUCCESS"))
        _native_require(len(deterministic_json(original.output_json.decode("utf-8", "strict")).encode("utf-8")) - 2 <= output_limit,
            "LP03_FOLD_SCORER_COMPLETE_OUTPUT_BUDGET")
        measured.append((ordinal,train_ref,refs,original,measurement))
    return tuple(measured)


def _measure_original_recorded_dr_continuation_v1(*, envelope, grant, clock, original, source_payload,
                                                 maximum_input_bytes, maximum_output_bytes, work):
    """Measure the bounded uncertainty continuation of an actual MATH-22 call."""
    from .implementation_registry import EvidencePrivateWireInvocationResultV1
    from .latency_policy import _EvidenceLocalClockV1, _evidence_invocation_measurement_v1
    from .models import (
        EvidenceAttemptGrantPayloadV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1,
        _evidence_dr_original_source_data_v1,
    )
    from .parameter_policy import _EvidenceNumericalWorkV1
    from .serialization import _native_strict_json

    _native_require(type(envelope) is EvidenceAuthorizationMessageV1 and envelope.kind is EvidenceMessageKindV1.ATTEMPT_GRANT
        and type(grant) is EvidenceAttemptGrantPayloadV1 and grant.component_closure == ("MATH-22",)
        and type(original) is EvidencePrivateWireInvocationResultV1 and original.contract.math_id == "MATH-22"
        and type(clock) is _EvidenceLocalClockV1 and type(work) is _EvidenceNumericalWorkV1,
        "LP03_DR_NATIVE_ORIGINAL_MEASUREMENT_REQUIRED")
    deadline = grant.deadline
    _native_require((clock.clock_domain_id, clock.boot_identity_ref) == (deadline.clock_domain_id, deadline.boot_identity_ref)
        and type(maximum_input_bytes) is type(maximum_output_bytes) is int
        and 0 < maximum_input_bytes <= min(grant.budgets.max_input_bytes, grant.budgets.frame_byte_limit)
        and 0 < maximum_output_bytes <= min(grant.budgets.max_output_bytes, grant.budgets.frame_byte_limit)
        and grant.budgets.max_computations >= 2, "LP03_DR_NATIVE_CONTINUATION_GRANT_SCOPE")

    def check_current(sample):
        _native_require(envelope.valid_from_wall_ns <= sample[0] < envelope.exclusive_expiry_wall_ns
            and deadline.admitted_monotonic_ns <= sample[1] < deadline.exclusive_deadline_monotonic_ns,
            "LP03_DR_NATIVE_CONTINUATION_EXPIRED")

    started = _EvidenceLocalClockV1.observe_v1(clock)
    check_current(started)
    raw_ref = grant.grant_ref + "::DATA::RAW"
    parts, inputs, policy, policy_wire, original_fit_after_first_label = _evidence_dr_original_source_data_v1(source_payload, original_raw_ref=raw_ref)
    input_wire = deterministic_json(inputs).encode("utf-8", "strict")
    _native_require(input_wire == original.input_json and original.contract.resource_policy_ref == grant.protocol_ref,
        "LP03_DR_NATIVE_ORIGINAL_ESTIMATOR_JOIN")
    certificate = measure_dr_score_uncertainty_v1(original.output_json, input_json=input_wire, policy_json=policy_wire,
        maximum_input_bytes=maximum_input_bytes, maximum_input_nodes=4096,
        maximum_output_bytes=maximum_output_bytes, maximum_output_nodes=4096, work=work,
        original_fit_after_first_label=original_fit_after_first_label)
    completed = _EvidenceLocalClockV1.observe_v1(clock)
    check_current(completed)
    measured = _evidence_invocation_measurement_v1(dict(clock_domain_id=clock.clock_domain_id,
        boot_identity_ref=clock.boot_identity_ref, process_identity_ref=clock.process_identity_ref,
        clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock), started=started, completed=completed,
        duration_ns=completed[1]-started[1], cpu_ns=completed[2]-started[2], outcome="SUCCESS"))
    structured = _native_strict_json(certificate, max_bytes=maximum_output_bytes, max_nodes=4096, binary64_numbers=True)
    _native_require(structured["original_policy"]["raw_receipt_ref"] == raw_ref
        and structured["original_policy"]["input_receipt_ref"] == policy["input_receipt_ref"]
        and len(parts) >= 2, "LP03_DR_NATIVE_ORIGINAL_SOURCE_AND_RESULT")
    return certificate, measured


class _EvidenceTimelineBufferV1:
    """Retain a bounded sequence of original admitted events for one attempt."""

    __slots__ = ("_limits", "_origin", "_allowed_refs", "_events", "_event_ids", "_revisions",
                 "_segment_ordinal", "_input_bytes", "_final", "_selected", "_last_decision")

    def __init__(self, *, limits, origin, allowed_refs):
        from .models import EvidenceExecutionLimitsV1, EvidenceOriginV1, EvidenceRecordRefV1

        _native_require(type(limits) is EvidenceExecutionLimitsV1 and type(origin) is EvidenceOriginV1,
                        "LP03_TIMELINE_LIMIT_OWNER")
        _native_require(type(allowed_refs) is tuple and 0 < len(allowed_refs) <= 256
                        and all(type(ref) is EvidenceRecordRefV1 for ref in allowed_refs)
                        and len(set(allowed_refs)) == len(allowed_refs), "LP03_TIMELINE_ALLOWED_SOURCE_ROSTER")
        self._limits = limits
        self._origin = origin
        self._allowed_refs = frozenset(allowed_refs)
        self._events = []
        self._event_ids = set()
        self._revisions = {}
        self._segment_ordinal = 0
        self._input_bytes = 0
        self._final = False
        self._selected = set()
        self._last_decision = None

    def admit_segment_v1(self, *, segment_ordinal, events, final, original_wire_bytes):
        from .models import EvidenceTimelineEventV1

        limits = self._limits
        _public_counter_v1(segment_ordinal, allow_zero=True)
        _public_counter_v1(original_wire_bytes)
        _native_require(not self._final and not self._selected and segment_ordinal == self._segment_ordinal
                        and type(final) is bool, "LP03_TIMELINE_SEGMENT_ORDER")
        _native_require(type(events) is tuple and 0 < len(events) <= limits.segment_max_events
                        and original_wire_bytes <= min(limits.segment_max_bytes, limits.frame_byte_limit)
                        and len(self._events) + len(events) <= limits.max_events
                        and len(self._events) + len(events) <= limits.max_input_reads
                        and self._input_bytes + original_wire_bytes <= limits.max_input_bytes,
                        "LP03_TIMELINE_SEGMENT_RESOURCE_EXHAUSTED")
        identities = set()
        revisions = dict(self._revisions)
        for ordinal, event in enumerate(events, len(self._events)):
            _native_require(type(event) is EvidenceTimelineEventV1 and event.origin is self._origin
                            and event.source_record_ref in self._allowed_refs and event.local_ordinal == ordinal
                            and event.event_id not in self._event_ids and event.event_id not in identities,
                            "LP03_TIMELINE_EVENT_ORDER_OR_SOURCE")
            prior_revision = revisions.get(event.source_record_ref)
            _native_require(prior_revision is None or prior_revision < event.source_revision,
                            "LP03_TIMELINE_NONMONOTONE_REVISION")
            identities.add(event.event_id)
            revisions[event.source_record_ref] = event.source_revision
        self._events.extend(events)
        self._event_ids.update(identities)
        self._revisions = revisions
        self._input_bytes += original_wire_bytes
        self._segment_ordinal += 1
        self._final = final

    def available_v1(self, *, decision_wall_ns):
        """Expose only the next causally available events in deterministic order."""
        _public_counter_v1(decision_wall_ns, allow_zero=True)
        _native_require(self._final and (self._last_decision is None or self._last_decision <= decision_wall_ns),
                        "LP03_TIMELINE_INCOMPLETE_OR_BACKDATED_DECISION")
        selected = tuple(event for event in self._events if event.event_id not in self._selected
                         and event.availability_wall_ns <= decision_wall_ns)
        ordered = tuple(sorted(selected, key=_evidence_timeline_event_key_v1))
        self._selected.update(event.event_id for event in ordered)
        self._last_decision = decision_wall_ns
        return ordered

    def available_refs_v1(self, decision_wall_ns):
        return frozenset(event.source_record_ref for event in self._events
                         if event.availability_wall_ns <= decision_wall_ns)

def _evidence_timeline_event_key_v1(event):
    provider = event.provider_order_or_absence
    ordered = type(provider) is tuple
    return event.availability_wall_ns, not ordered, provider if ordered else (), event.local_ordinal


_CAUSAL_TIMELINE_WORKER_PROFILE_V1 = "CAUSAL_TIMELINE_V1"
_CAUSAL_TIMELINE_CONTINUE_FIELDS_V1 = {
    "STEP": {"decision_ordinal", "decision_wall_ns"},
    "APPLY_CALLBACK_RESULT": {"event_ordinal", "role", "outcome"},
    "INVOKE_COMPONENT": {"event_ordinal", "request_ordinal", "request", "inputs"},
    "FINISH": {"decision_count"},
}
_CAUSAL_TIMELINE_FRAME_FIELDS_V1 = {
    "INPUT_SEGMENT": {"segment_ordinal", "final_segment", "events"},
    "READ_REQUEST": {"record_refs", "event_ordinal_or_none", "role_or_none", "scenario_values"},
    "SEGMENT": {"segment_ordinal", "decision_ordinal", "event_ids", "outcomes", "lane_state_ref",
                "callbacks_started", "coordinates_sampled", "domain_state"},
    "COMPLETE": {"events", "segments", "callbacks_started", "coordinates_sampled", "computations", "lane_state_ref"},
    "FAILED": {"reason_code", "exception_class", "event_ordinal_or_none", "events", "callbacks_started",
               "coordinates_sampled", "computations", "lane_state_ref", "measurement_or_absence", "outcomes", "domain_state"},
}


def _worker_timeline_payload_v1(kind, payload):
    """Validate a closed timeline profile carried by the existing worker framing."""
    from .context import _public_refs_v1
    from .models import (EvidenceCallbackRoleV1, EvidenceRecordRefV1, EvidenceStepComputationRequestV1,
                         EvidenceStepOutcomeV1, EvidenceTimelineEventV1)

    if kind == "CONTINUE":
        command = payload.get("command")
        _native_require(type(command) is str and command in _CAUSAL_TIMELINE_CONTINUE_FIELDS_V1,
                        "LP03_TIMELINE_WORKER_COMMAND")
        fields = _CAUSAL_TIMELINE_CONTINUE_FIELDS_V1[command] | {"command"}
    else:
        fields = _CAUSAL_TIMELINE_FRAME_FIELDS_V1.get(kind)
    _native_require(fields is not None and set(payload) == fields | {"profile"}
                    and payload["profile"] == _CAUSAL_TIMELINE_WORKER_PROFILE_V1,
                    "LP03_TIMELINE_WORKER_PAYLOAD_FIELDS")
    for name in ("event_ordinal", "event_ordinal_or_none", "decision_ordinal", "decision_wall_ns", "decision_count",
                 "segment_ordinal", "callbacks_started", "coordinates_sampled", "segments",
                 "computations", "request_ordinal"):
        if name in payload and (name != "event_ordinal_or_none" or payload[name] is not None):
            _public_counter_v1(payload[name], allow_zero=True)
    if kind in ("COMPLETE", "FAILED"):
        _public_counter_v1(payload["events"], allow_zero=True)
    for name in ("reason_code", "exception_class", "lane_state_ref"):
        if name in payload:
            _native_ident(payload[name])
    for name in ("role", "role_or_none"):
        if name in payload and (name != "role_or_none" or payload[name] is not None):
            _native_require(type(payload[name]) is str and payload[name] in EvidenceCallbackRoleV1,
                            "LP03_TIMELINE_WORKER_ROLE")
    if kind == "INPUT_SEGMENT":
        rows = payload["events"]
        _native_require(type(payload["final_segment"]) is bool and type(rows) in (list, tuple) and 0 < len(rows) <= 128,
                        "LP03_TIMELINE_WORKER_SEGMENT_ROSTER")
        for row in rows:
            EvidenceTimelineEventV1.from_canonical_mapping(row)
    elif kind == "READ_REQUEST":
        rows = payload["record_refs"]
        _native_require(type(rows) in (list, tuple) and 0 < len(rows) <= 256, "LP03_TIMELINE_WORKER_READ_REFS")
        refs = tuple(EvidenceRecordRefV1.from_canonical_mapping(row) for row in rows)
        _native_require(len(refs) == len(set(refs)), "LP03_TIMELINE_WORKER_DUPLICATE_READ_REF")
        initial = payload["event_ordinal_or_none"] is None
        values = payload["scenario_values"]
        _native_require(initial == (payload["role_or_none"] is None)
                        and type(values) in (list, tuple) and len(values) <= 256
                        and (not initial or not values), "LP03_TIMELINE_WORKER_READ_PROFILE")
        for receipt in values:
            _evidence_timeline_coordinate_receipt_v1(receipt)
    elif kind == "CONTINUE" and payload["command"] == "APPLY_CALLBACK_RESULT":
        EvidenceStepOutcomeV1.from_canonical_mapping(payload["outcome"])
    elif kind == "CONTINUE" and payload["command"] == "INVOKE_COMPONENT":
        EvidenceStepComputationRequestV1.from_canonical_mapping(payload["request"])
        _native_require(isinstance(payload["inputs"], Mapping), "LP03_TIMELINE_COMPONENT_INPUTS")
    elif kind in ("SEGMENT", "FAILED"):
        _native_require(isinstance(payload["domain_state"], Mapping) and set(payload["domain_state"]) == {
            "books", "reconnect_pending", "legs", "rate_budget", "cash_reserve"}, "LP03_TIMELINE_WORKER_DOMAIN_STATE")
        if kind == "SEGMENT":
            event_ids = payload["event_ids"]
            _native_require(type(event_ids) in (list, tuple) and bool(event_ids), "LP03_TIMELINE_WORKER_SEGMENT_EVENT_IDS")
            _public_refs_v1(tuple(event_ids))
        outcomes = payload["outcomes"]
        _native_require(type(outcomes) in (list, tuple) and len(outcomes) <= 256, "LP03_TIMELINE_STEP_OUTCOME_ROSTER")
        for outcome in outcomes:
            EvidenceStepOutcomeV1.from_canonical_mapping(outcome)
    return _evidence_frozen_data_v1(dict(payload))


def _evidence_timeline_coordinate_receipt_v1(receipt):
    """Check the exact reported coordinates and rational without drawing again."""
    from math import gcd

    fields = ("master_seed", "plan_revision", "scenario_ordinal", "dependence_group_ordinal", "event_ordinal",
              "variable_purpose_ordinal", "draw_ordinal", "namespace_ordinal")
    _native_require(isinstance(receipt, Mapping) and set(receipt) == {
        "profile", *fields, "encoded_coordinate", "uniform53_bits", "uniform"}
        and receipt["profile"] == "QTT_LP03_SCENARIO_MT19937_U53_V1", "LP03_TIMELINE_COORDINATE_RECEIPT")
    coordinate = tuple(receipt[field] for field in fields)
    _native_require(all(type(value) is int and 0 <= value < 2**256 for value in coordinate),
                    "LP03_TIMELINE_COORDINATE_RECEIPT_DOMAIN")
    encoded = bytearray(b"QTT-LP03-SCENARIO-V1\0")
    for value in coordinate:
        width = max(1, (value.bit_length() + 7) // 8)
        encoded.extend(width.to_bytes(2, "big"))
        encoded.extend(value.to_bytes(width, "big"))
    bits = receipt["uniform53_bits"]
    _native_require(type(bits) is int and 0 <= bits < 2**53, "LP03_TIMELINE_COORDINATE_RECEIPT_BITS")
    common = gcd(bits, 2**53)
    _native_require(receipt["encoded_coordinate"] == encoded.hex()
                    and receipt["uniform"] == {"numerator": str(bits // common), "denominator": str(2**53 // common)},
                    "LP03_TIMELINE_COORDINATE_RECEIPT_VALUE")
    return coordinate


def _evidence_timeline_public_candidate_v1(event):
    """Reconstruct the approved LP02 typed candidate from a bounded original row."""
    from dataclasses import fields
    from ..market_data_ingest import adapter as pit
    from .context import _native_utc_nanoseconds, exact_decimal, parse_utc
    from .errors import ContractValidationError, ReasonCode
    from .point_in_time import PITTransportStateV1
    from .serialization import deterministic_json

    body = event.payload
    _native_require(set(body) == {"candidate", "transport_state", "lifecycle_state"}
                    and isinstance(body["candidate"], Mapping), "LP03_TIMELINE_PUBLIC_CANDIDATE_FIELDS")
    candidate = dict(body["candidate"])
    _native_require(set(candidate) == {member.name for member in fields(pit.PITCanonicalEventCandidateV2)}
                    and candidate["event_kind"] == event.kind and candidate["connection_epoch"] == event.connection_epoch
                    and candidate["event_record_id"] == event.event_id
                    and deterministic_json(candidate["no_effect_flags"]) == deterministic_json(pit.NO_EFFECTS_V1),
                    "LP03_TIMELINE_ORIGINAL_PUBLIC_CANDIDATE")
    native_order = candidate["provider_sequence_start_or_none"], candidate["provider_sequence_end_or_none"]
    _native_require(native_order == (event.provider_order_or_absence if type(event.provider_order_or_absence) is tuple
                                     else (None, None)), "LP03_TIMELINE_ORIGINAL_PUBLIC_SEQUENCE")
    kind = pit.PITEventKindV2(event.kind)
    candidate["event_kind"] = kind
    candidate["profile_id"] = pit.Stage1VenueProfileIdV1(candidate["profile_id"])
    if (candidate["profile_id"] is pit.Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
            and (kind in (pit.PITEventKindV2.BOOK_SNAPSHOT, pit.PITEventKindV2.BOOK_DELTA)
                 or candidate["wire_dialect"] == "KALSHI_TRADE_API_WS_V2_FIXED_POINT"
                 or candidate["provider_subscription_id_or_none"] is not None)):
        # LP02 requires the privately issued original stream witness. A
        # sequence or receipt string on this data-only wire cannot replace it.
        raise ContractValidationError(ReasonCode.EVIDENCE_INPUT_UNAVAILABLE, "LP03_TIMELINE_ORIGINAL_STREAM_WITNESS_REQUIRED")
    candidate["depth_class"] = pit.PITDepthClassV2(candidate["depth_class"])
    candidate["no_effect_flags"] = pit.NO_EFFECTS_V1
    for field in ("provider_event_time_utc_or_none", "provider_publication_time_utc_or_none",
                  "qtt_received_at_utc", "qtt_parse_completed_at_utc"):
        if candidate[field] is not None:
            candidate[field] = parse_utc(candidate[field], field_name=field)
    source_payload = candidate["payload"]
    _native_require(isinstance(source_payload, Mapping), "LP03_TIMELINE_ORIGINAL_PUBLIC_PAYLOAD")
    allowed = tuple(owner for owner in pit._pit_payload_types_for_event_kind_v2(kind)
                    if set(source_payload) == {member.name for member in fields(owner)})
    _native_require(len(allowed) == 1, "LP03_TIMELINE_PUBLIC_PAYLOAD_DISCRIMINATOR")
    owner = allowed[0]
    payload = dict(source_payload)
    if "fields" in payload:
        _native_require(payload["event_kind"] == kind.value, "LP03_TIMELINE_PUBLIC_SCALAR_KIND")
        payload["event_kind"] = kind
    else:
        level_field, level_owner, quantity = (
            ("updates", pit._PITAbsoluteLevelUpdateV2, "absolute_quantity") if "updates" in payload else
            ("deltas", pit._PITDeltaLevelV2, "quantity_delta") if "deltas" in payload else
            ("levels", pit._PITBookLevelV2, "quantity")
        )
        decimals = ("price", quantity, "price_increment", "price_origin", "quantity_increment_or_none")
        levels = []
        for value in payload[level_field]:
            typed = dict(value)
            _native_require(set(typed) == {member.name for member in fields(level_owner)},
                            "LP03_TIMELINE_PUBLIC_LEVEL_FIELDS")
            for key in decimals:
                if typed[key] is not None:
                    typed[key] = exact_decimal(typed[key], field_name=key)
            levels.append(level_owner(**typed))
        payload[level_field] = tuple(levels)
    candidate["payload"] = owner(**payload)
    original = pit.PITCanonicalEventCandidateV2(**candidate)
    availability = _native_utc_nanoseconds(original.qtt_parse_completed_at_utc.isoformat())
    _native_require(availability <= event.availability_wall_ns, "LP03_TIMELINE_PUBLIC_PARSE_AVAILABILITY")
    _native_ident(body["lifecycle_state"])
    return original, PITTransportStateV1(body["transport_state"]), body["lifecycle_state"]


class _EvidenceTimelineLaneStateV1:
    """One lane's original book, leg and reality-input state."""

    __slots__ = ("_grant", "_cash_basis", "_books", "_book_prefix", "_reconnect", "_legs", "_observations", "_budget", "_reserve")

    def __init__(self, grant, scope):
        self._grant = grant
        self._cash_basis = scope.accepted_cash_basis_or_none
        self._books = {}
        self._book_prefix = {}
        self._reconnect = {}
        self._legs = {}
        self._observations = {}
        self._budget = None
        self._reserve = None

    def begin_v1(self, event, *, decision_wall_ns):
        from .models import _LP03_PUBLIC_TIMELINE_KINDS_V1

        if event.kind in _LP03_PUBLIC_TIMELINE_KINDS_V1:
            self._public_v1(event)
        else:
            self._synthetic_v1(event.kind, event.payload, event, decision_wall_ns=decision_wall_ns, generated=False)

    def apply_v1(self, event, outcome, *, decision_wall_ns):
        for intent in outcome.proposed_intents:
            self._add_intent_v1(intent, decision_wall_ns)
        for observation in outcome.generated_observations:
            prior = self._observations.get(observation.observation_id)
            canonical = deterministic_json(observation)
            _native_require(prior is None or prior == canonical, "LP03_TIMELINE_CONFLICTING_OBSERVATION")
            if prior is None:
                self._synthetic_v1(observation.kind, observation.payload, event, decision_wall_ns=decision_wall_ns, generated=True)
                self._observations[observation.observation_id] = canonical

    def require_component_v1(self, event):
        from .models import _LP03_PUBLIC_TIMELINE_KINDS_V1
        from .point_in_time import PITAnchorStateV1, PITAvailabilityStateV2

        _native_require(not self._reconnect and not any(row.recovery_required for row in self._book_prefix.values()),
                        "LP03_TIMELINE_PUBLIC_COMPONENT_REQUIRES_ANCHOR")
        if event.kind in _LP03_PUBLIC_TIMELINE_KINDS_V1:
            candidate = event.payload["candidate"]
            key = tuple(candidate[name] for name in ("profile_id", "market_id", "instrument_id", "channel"))
            transition = self._book_prefix.get(key)
            _native_require(transition is not None and not transition.recovery_required and key not in self._reconnect
                            and transition.post_state.state_vector.anchor_state is PITAnchorStateV1.ANCHOR_ACCEPTED
                            and transition.post_state.state_vector.availability_state in (
                                PITAvailabilityStateV2.AVAILABLE_CURRENT_STATE, PITAvailabilityStateV2.AVAILABLE_CHANGE_LEVEL),
                            "LP03_TIMELINE_PUBLIC_COMPONENT_REQUIRES_ANCHOR")

    def _public_v1(self, event):
        from ..orderbook_event_state_snapshot.builder import apply_pit_event_v2
        from .point_in_time import PITAnchorStateV1, PITEventDispositionV1, PITEventKindV2, PITTransportStateV1

        candidate, transport, lifecycle = _evidence_timeline_public_candidate_v1(event)
        key = candidate.profile_id.value, candidate.market_id, candidate.instrument_id, candidate.channel
        expected_epoch = self._reconnect.get(key)
        prior = self._books.get(key)
        last = self._book_prefix.get(key)
        anchor = candidate.event_kind in (PITEventKindV2.BOOK_SNAPSHOT, PITEventKindV2.BOOK_REPLACEMENT)
        if expected_epoch is not None:
            _native_require(candidate.connection_epoch == expected_epoch, "LP03_TIMELINE_STALE_RECONNECT_EPOCH")
            if prior is not None and prior.post_state.capture_session_id != candidate.capture_session_id:
                prior = None
        elif last is not None and last.recovery_required and not anchor:
            prior = last
        previous = None if prior is None else prior.post_state
        ordinal = 1 if previous is None else previous.last_completed_event_ordinal + 1
        transition = apply_pit_event_v2(previous, candidate, candidate_event_ordinal=ordinal,
                                       transport_state=transport, lifecycle_state=lifecycle)
        self._book_prefix[key] = transition
        if transition.event_disposition is PITEventDispositionV1.COMMITTED:
            if expected_epoch is None:
                self._books[key] = transition
            elif (anchor and not transition.recovery_required and transport is PITTransportStateV1.CONNECTED_HEALTHY
                  and transition.post_state.state_vector.anchor_state is PITAnchorStateV1.ANCHOR_ACCEPTED):
                self._books[key] = transition
                del self._reconnect[key]

    def _add_intent_v1(self, intent, decision_wall_ns):
        from .context import _native_utc_nanoseconds
        from .lifecycle import FillAccumulatorV1

        ref = intent.economic_intent_id
        _native_require(ref not in self._legs and intent.owner_envelope_ref == self._grant.original_owner_envelope_ref
                        and intent.mode_ref in (self._grant.lane.value, "SOFTWARE_CONFORMANCE")
                        and decision_wall_ns < _native_utc_nanoseconds(intent.expires_at.isoformat()),
                        "LP03_TIMELINE_ORIGINAL_INTENT")
        # This state is an explicit simulation of a proposed intent. The typed
        # custody and fill inputs must supply subsequent observations.
        self._legs[ref] = (intent, "PROVIDER_PENDING", FillAccumulatorV1(intent.quantity_text))

    def _synthetic_v1(self, kind, data, event, *, decision_wall_ns, generated):
        from dataclasses import fields, replace
        from .accounting import AccountingAmountV1, AccountingAndTCAServiceV1
        from .context import _native_obj, _native_utc_nanoseconds
        from .lifecycle import ExecutionCustodyReceiptV1, FillAccumulatorV1, RateLimitBudgetV1
        from .models import _evidence_timeline_intent_v1

        if kind == "SYNTHETIC_TIMER":
            row = _native_obj(dict(data), ("timer_ref", "due_wall_ns"))
            _native_ident(row["timer_ref"])
            _public_counter_v1(row["due_wall_ns"], allow_zero=True)
            _native_require(row["due_wall_ns"] <= event.availability_wall_ns, "LP03_TIMELINE_TIMER_AVAILABILITY")
            return
        if kind == "SYNTHETIC_RECONNECT":
            row = _native_obj(dict(data), ("profile_id", "market_id", "instrument_id", "channel", "next_connection_epoch"))
            key = tuple(row[name] for name in ("profile_id", "market_id", "instrument_id", "channel"))
            for value in (*key, row["next_connection_epoch"]):
                _native_ident(value)
            before = self._books.get(key)
            _native_require(before is not None and key not in self._reconnect
                            and before.post_state.connection_epoch == event.connection_epoch
                            and before.post_state.connection_epoch != row["next_connection_epoch"],
                            "LP03_TIMELINE_ORIGINAL_RECONNECT")
            self._reconnect[key] = row["next_connection_epoch"]
            return
        if kind in ("SYNTHETIC_ORDER_INTENT", "SYNTHETIC_AMEND"):
            payload = _native_obj(dict(data), ("intent",))
            intent = _evidence_timeline_intent_v1(payload["intent"])
            if kind == "SYNTHETIC_ORDER_INTENT":
                self._add_intent_v1(intent, decision_wall_ns)
            else:
                prior, state, fills = self._leg_v1(intent.economic_intent_id)
                _native_require(state in ("ACKNOWLEDGED", "PARTIALLY_FILLED")
                                and replace(prior, quantity_text=intent.quantity_text, limit_price_text=intent.limit_price_text) == intent,
                                "LP03_TIMELINE_ORIGINAL_AMENDMENT")
                updated = FillAccumulatorV1(intent.quantity_text, fills.accepted_fills)
                _native_require(updated.remaining_quantity > 0, "LP03_TIMELINE_AMENDMENT_REMAINING_QUANTITY")
                self._legs[intent.economic_intent_id] = (intent, state, updated)
            return
        if kind == "SYNTHETIC_RATE_BUDGET":
            row = _native_obj(dict(data), ("budget",))
            supplied = dict(row["budget"])
            members = tuple(member.name for member in fields(RateLimitBudgetV1) if member.init)
            budget = RateLimitBudgetV1(**_native_obj(supplied, members))
            _native_require(_native_utc_nanoseconds(budget.evaluated_at.isoformat()) <= decision_wall_ns
                            and budget.source_binding_ref == event.source_record_ref.record_id,
                            "LP03_TIMELINE_ORIGINAL_RATE_BUDGET_AVAILABILITY")
            self._budget = (budget.budget_ref, budget.admission_decision)
            return
        if kind == "SYNTHETIC_MULTILEG_OUTCOME":
            row = _native_obj(dict(data), ("candidate_ref", "legs"))
            _native_ident(row["candidate_ref"])
            expected = tuple(self._leg_view_v1(ref, state, fills)
                             for ref, (intent, state, fills) in sorted(self._legs.items())
                             if intent.trade_plan_candidate_ref == row["candidate_ref"])
            _native_require(len(expected) > 1 and deterministic_json(row["legs"]) == deterministic_json(expected),
                            "LP03_TIMELINE_MULTILEG_OUTCOME_MISMATCH")
            return
        if kind == "SYNTHETIC_VOID":
            row = _native_obj(dict(data), ("intent_ref", "void_reason_ref", "reserve"))
            _native_ident(row["void_reason_ref"])
            intent, status, fills = self._leg_v1(row["intent_ref"])
            _native_require(status in ("ACKNOWLEDGED", "PARTIALLY_FILLED", "FILLED", "CANCELLED"),
                            "LP03_TIMELINE_VOID_TERMINAL_STATE")
            self._reserve = self._check_reserve_v1(row["reserve"], AccountingAmountV1, AccountingAndTCAServiceV1)
            self._legs[intent.economic_intent_id] = (intent, "VOIDED", fills)
            return
        event_class = {
            "SYNTHETIC_ORDER_ACK": "ACK", "SYNTHETIC_CANCEL": "CANCEL",
            "SYNTHETIC_FILL": "FILL", "SYNTHETIC_SETTLEMENT": "SETTLEMENT",
        }.get(kind)
        _native_require(event_class is not None, "LP03_TIMELINE_SYNTHETIC_EVENT_KIND")
        extra = ("fill",) if event_class == "FILL" else ("reserve",) if event_class == "SETTLEMENT" else ()
        row = _native_obj(dict(data), ("custody", *extra))
        receipt = ExecutionCustodyReceiptV1(**_native_obj(dict(row["custody"]),
            tuple(member.name for member in fields(ExecutionCustodyReceiptV1))))
        ref = receipt.economic_intent_ref
        intent, state, fills = self._leg_v1(ref)
        declared_attempt = self._grant.grant_ref if generated else self._grant.scenario_plan_ref.record_id
        _native_require(receipt.event_class == event_class and receipt.attempt_ref == declared_attempt
                        and receipt.source_payload_custody_ref == event.source_record_ref.record_id
                        and _native_utc_nanoseconds(receipt.effective_at.isoformat())
                            <= _native_utc_nanoseconds(receipt.recorded_at.isoformat()) <= decision_wall_ns
                        and receipt.prior_state == ("CANCEL_PENDING" if event_class == "CANCEL" else state),
                        "LP03_TIMELINE_ORIGINAL_CUSTODY")
        if event_class == "CANCEL":
            from .lifecycle import FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1

            FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1.validate(state, receipt.prior_state)
        if event_class == "FILL":
            fill = _native_obj(dict(row["fill"]), ("fill_id", "sequence", "quantity_text", "payload_json"))
            _native_ident(fill["fill_id"])
            fills = FillAccumulatorV1(intent.quantity_text, (*fills.accepted_fills, (fill["fill_id"], fill["sequence"],
                receipt.effective_at, fill["quantity_text"], fill["payload_json"])))
            inferred = "FILLED" if fills.remaining_quantity == 0 else "PARTIALLY_FILLED"
            _native_require(receipt.candidate_state == inferred, "LP03_TIMELINE_FILL_STATE_MISMATCH")
        if event_class == "SETTLEMENT":
            self._reserve = self._check_reserve_v1(row["reserve"], AccountingAmountV1, AccountingAndTCAServiceV1)
        self._legs[ref] = (intent, receipt.candidate_state, fills)

    def _check_reserve_v1(self, value, amount_type, service):
        from .context import _native_obj

        names = ("available_cash", "reserved_cash", "pending_cash", "owner_protected_cash",
                 "quarantined_cash", "accepted_cash_basis")
        roster = _native_obj(dict(value), names)
        _native_require(self._cash_basis is not None and roster["accepted_cash_basis"] == self._cash_basis.amount,
                        "LP03_TIMELINE_ORIGINAL_CASH_BASIS_CHANGED")
        balances = {name: amount_type(**dict(roster[name])) for name in names}
        service.validate_reserve_conservation(**balances)
        return balances

    def _leg_v1(self, ref):
        _native_ident(ref)
        _native_require(ref in self._legs, "LP03_TIMELINE_INTENT_NOT_PREVIOUSLY_ADMITTED")
        return self._legs[ref]

    @staticmethod
    def _leg_view_v1(ref, state, fills):
        return dict(intent_ref=ref, state=state, filled_quantity_text=str(fills.filled_quantity),
                    remaining_quantity_text=str(fills.remaining_quantity))

    def view_v1(self):
        books = tuple(dict(scope=key, state_ref=result.post_state.state_id,
                           continuity=result.continuity_result.value,
                           disposition=result.event_disposition.value, recovery_required=result.recovery_required,
                           failure_reason_or_none=None if result.failure_reason_or_none is None else result.failure_reason_or_none.value,
                           connection_epoch=result.post_state.connection_epoch)
                      for key, result in sorted(self._book_prefix.items()))
        view = dict(books=books, reconnect_pending=tuple(sorted(self._reconnect.items())),
                    legs=tuple(self._leg_view_v1(ref, state, fills) for ref, (_, state, fills) in sorted(self._legs.items())),
                    rate_budget=self._budget, cash_reserve=self._reserve)
        from .serialization import _evidence_canonical_object_v1

        return _evidence_frozen_data_v1(_evidence_canonical_object_v1(deterministic_json(view).encode("utf-8")))


def _run_causal_timeline_worker_v1(*, grant, scope, clock, current, send, receive, input_stream):
    """Execute only the original decision schedule under the scoped signed attempt."""
    import hashlib
    import sys
    import traceback
    from .errors import ComputationControlPlaneError
    from .implementation_registry import (LP03_DECIMAL_CONTEXT_POLICY_REF_V1, _LP03_PUBLIC_EVIDENCE_INVOCATION_IDS_V1,
        invoke_evidence_private_wire_v1, invoke_evidence_public_wire_v1, resolve_evidence_invocation_v1)
    from .latency_policy import _EvidenceLocalClockV1, _evidence_invocation_measurement_v1
    from .models import EvidenceStepOutcomeV1, EvidenceTimelineEventV1
    from .parameter_policy import _EvidenceNumericalWorkV1

    limits = grant.budgets
    refs = tuple(dict.fromkeys(pin.source_record_ref for pin in scope.event_pins))
    buffer = _EvidenceTimelineBufferV1(limits=limits, origin=scope.scenario_plan.origin, allowed_refs=refs)
    domain = _EvidenceTimelineLaneStateV1(grant, scope)
    work = _EvidenceNumericalWorkV1(scope.numerical_work_limits, retained_input_capacity=limits.max_input_reads)
    component_pins = {row[0]: row[1:] for row in grant.component_and_callback_pins["components"]}
    profile = _CAUSAL_TIMELINE_WORKER_PROFILE_V1
    draws = {}
    admitted = events = callbacks = computations = segments = 0
    state_ref = grant.grant_ref
    active_event = None
    pending_outcomes = []
    measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_NOT_STARTED")

    def emit(kind, **payload):
        send(kind, dict(profile=profile, **payload))

    def expect(command, **expected):
        payload = receive("CONTINUE")
        _native_require(payload.get("profile") == profile and payload.get("command") == command
                        and all(payload[name] == original for name, original in expected.items()),
                        "LP03_TIMELINE_CAUSAL_COMMAND")
        return payload

    try:
        emit("READ_REQUEST", record_refs=refs, event_ordinal_or_none=None, role_or_none=None, scenario_values=())
        while admitted < len(scope.event_pins):
            payload, wire_size = receive("INPUT_SEGMENT", with_size=True)
            _native_require(payload.get("profile") == profile, "LP03_TIMELINE_INPUT_PROFILE")
            batch = tuple(EvidenceTimelineEventV1.from_canonical_mapping(row) for row in payload["events"])
            pins = scope.event_pins[admitted:admitted + len(batch)]
            _native_require(len(batch) == len(pins), "LP03_TIMELINE_INPUT_PIN_COUNT")
            for event, pin in zip(batch, pins, strict=True):
                digest = hashlib.sha256(deterministic_json(event).encode("utf-8")).hexdigest()
                _native_require((event.event_id, event.source_record_ref, event.local_ordinal, digest) ==
                                (pin.event_id, pin.source_record_ref, pin.local_ordinal, pin.canonical_event_sha256),
                                "LP03_TIMELINE_ORIGINAL_EVENT_PIN")
            admitted += len(batch)
            _native_require(payload["final_segment"] == (admitted == len(scope.event_pins)),
                            "LP03_TIMELINE_EARLY_OR_LATE_INPUT_END")
            buffer.admit_segment_v1(segment_ordinal=payload["segment_ordinal"], events=batch,
                                    final=payload["final_segment"], original_wire_bytes=wire_size)

        for decision, instant in enumerate(scope.decision_wall_ns):
            expect("STEP", decision_ordinal=decision, decision_wall_ns=instant)
            available = buffer.available_v1(decision_wall_ns=instant)
            source_refs = buffer.available_refs_v1(instant) | frozenset(pin.source_record_ref
                for pin in scope.component_input_pins if pin.availability_wall_ns <= instant)
            for event in available:
                active_event = event.local_ordinal
                current()
                domain.begin_v1(event, decision_wall_ns=instant)
                for pin in scope.callbacks:
                    _native_require(callbacks < limits.max_callbacks, "LP03_TIMELINE_CALLBACK_RESOURCE_EXHAUSTED")
                    coordinates = tuple(row for row in scope.coordinates if row[4] == active_event
                                        and row[7] in (0, pin.namespace_ordinal))
                    for coordinate in coordinates:
                        if coordinate not in draws:
                            _native_require(len(draws) < limits.max_coordinates, "LP03_TIMELINE_COORDINATE_RESOURCE_EXHAUSTED")
                            draws[coordinate] = sample_evidence_uniform53_v1(coordinate,
                                expected_environment=scope.scenario_plan.exact_environment_identity, work=work)
                    emit("READ_REQUEST", record_refs=(event.source_record_ref,), event_ordinal_or_none=active_event,
                         role_or_none=pin.role.value, scenario_values=tuple(draws[row] for row in coordinates))
                    payload = expect("APPLY_CALLBACK_RESULT", event_ordinal=active_event, role=pin.role.value)
                    callbacks += 1
                    outcome = EvidenceStepOutcomeV1.from_canonical_mapping(payload["outcome"])
                    _require_evidence_timeline_outcome_v1(outcome, grant=grant, event=event, pin=pin,
                        source_refs=source_refs, final_event=events + 1 == len(scope.event_pins))
                    _native_require(outcome.next_lane_state_ref != state_ref, "LP03_TIMELINE_REUSED_LANE_STATE")
                    pending_outcomes.append(outcome)
                    _native_require(outcome.disposition != "REJECTED", "LP03_TIMELINE_CALLBACK_REJECTED")
                    domain.apply_v1(event, outcome, decision_wall_ns=instant)
                    for ordinal, request in enumerate(outcome.component_requests):
                        domain.require_component_v1(event)
                        _native_require(computations < limits.max_computations, "LP03_TIMELINE_COMPUTATION_RESOURCE_EXHAUSTED")
                        component = expect("INVOKE_COMPONENT", event_ordinal=active_event, request_ordinal=ordinal)
                        _native_require(deterministic_json(component["request"]) == deterministic_json(request),
                                        "LP03_TIMELINE_ORIGINAL_COMPONENT_REQUEST")
                        math_id = request.math_id
                        implementation, specification = component_pins[math_id]
                        contract = resolve_evidence_invocation_v1(math_id, implementation_pin=implementation,
                            specification_pin=specification, resource_policy_ref=grant.protocol_ref, origin=event.origin)
                        invocation = (invoke_evidence_public_wire_v1 if math_id in _LP03_PUBLIC_EVIDENCE_INVOCATION_IDS_V1
                                      else invoke_evidence_private_wire_v1)
                        current()
                        began = _EvidenceLocalClockV1.observe_v1(clock)
                        computations += 1
                        status = "FAILED"
                        measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_CLOCK_UNAVAILABLE")
                        try:
                            result = invocation(contract, deterministic_json(component["inputs"]).encode("utf-8"),
                                maximum_input_bytes=min(limits.max_input_bytes, limits.segment_max_bytes),
                                maximum_nodes=4096, maximum_output_bytes=min(limits.frame_byte_limit, limits.max_output_bytes),
                                maximum_output_nodes=4096)
                            _native_require(result.contract is contract, "LP03_TIMELINE_ORIGINAL_COMPUTATION_RESULT")
                            status = "SUCCESS"
                        finally:
                            ended = _EvidenceLocalClockV1.observe_v1(clock)
                            measurement = _evidence_invocation_measurement_v1(dict(clock_domain_id=clock.clock_domain_id,
                                boot_identity_ref=clock.boot_identity_ref, process_identity_ref=clock.process_identity_ref,
                                clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock), started=began, completed=ended,
                                duration_ns=ended[1] - began[1], cpu_ns=ended[2] - began[2], outcome=status))
                        current()
                        send("COMPUTATION_RESULT", dict(event_ordinal=active_event, invocation_contract=contract,
                            numeric_context_policy_ref=LP03_DECIMAL_CONTEXT_POLICY_REF_V1,
                            raw_output_json=result.output_json.decode("utf-8", "strict"),
                            original_record_refs=request.original_input_refs, invocation_measurement=measurement))
                    state_ref = outcome.next_lane_state_ref
                events += 1
                emit("SEGMENT", segment_ordinal=segments, decision_ordinal=decision, event_ids=(event.event_id,),
                     outcomes=tuple(pending_outcomes), lane_state_ref=state_ref, callbacks_started=callbacks,
                     coordinates_sampled=len(draws), domain_state=domain.view_v1())
                segments += 1
                pending_outcomes.clear()
        _native_require(events == len(scope.event_pins), "LP03_TIMELINE_UNDISPATCHED_ORIGINAL_EVENT")
        expect("FINISH", decision_count=len(scope.decision_wall_ns))
        _native_require(_read_worker_frame_bytes_v1(input_stream, limits.frame_byte_limit) is None,
                        "LP03_TIMELINE_TRAILING_PARENT_FRAME")
        current()
        emit("COMPLETE", events=events, segments=segments, callbacks_started=callbacks, coordinates_sampled=len(draws),
             computations=computations, lane_state_ref=state_ref)
        return 0
    except BaseException as exc:
        traceback.print_exc(limit=8, file=sys.stderr)
        emit("FAILED", reason_code=(exc.reason_code.value if isinstance(exc, ComputationControlPlaneError)
                                    else "WORKER_PROTOCOL_OR_COMPUTATION_FAILED"),
             exception_class=type(exc).__module__ + "." + type(exc).__qualname__, event_ordinal_or_none=active_event,
             events=events, callbacks_started=callbacks, coordinates_sampled=len(draws), computations=computations,
             lane_state_ref=state_ref, measurement_or_absence=measurement, outcomes=tuple(pending_outcomes),
             domain_state=domain.view_v1())
        return 1


def _require_evidence_timeline_outcome_v1(outcome, *, grant, event, pin, source_refs, final_event):
    from .models import EvidenceCallbackRoleV1

    _native_require(outcome.next_lane_state_ref.startswith(grant.grant_ref + "::"),
                    "LP03_TIMELINE_LANE_STATE_SCOPE")
    _native_require(all(row.math_id in grant.component_closure and set(row.original_input_refs) <= source_refs
                        for row in outcome.component_requests), "LP03_TIMELINE_COMPONENT_SCOPE")
    _native_require(all(row.parent_event_id == event.event_id and row.origin is event.origin
                        for row in outcome.generated_observations), "LP03_TIMELINE_OBSERVATION_SCOPE")
    _native_require(all(row.owner_envelope_ref == grant.original_owner_envelope_ref and row.mode_ref == grant.lane.value
                        for row in outcome.proposed_intents), "LP03_TIMELINE_INTENT_SCOPE")
    _native_require(outcome.disposition != "COMPLETE" or (final_event and pin.role is EvidenceCallbackRoleV1.VENUE_REALITY),
                    "LP03_TIMELINE_EARLY_CALLBACK_COMPLETION")
    if pin.role is EvidenceCallbackRoleV1.STRATEGY:
        _native_require(not outcome.generated_observations, "LP03_TIMELINE_STRATEGY_REALITY_BOUNDARY")
    else:
        _native_require(not outcome.proposed_intents, "LP03_TIMELINE_REALITY_INTENT_BOUNDARY")


def _evidence_lane_completion_v1(grant, complete, expected_calls):
    """Check completion against the bounded profile that the grant selected."""
    scope = grant.causal_timeline_v1()
    if scope is None:
        return complete == dict(events=1, computations=expected_calls, segments=1)
    return (complete.get("profile") == _CAUSAL_TIMELINE_WORKER_PROFILE_V1
            and complete["events"] == len(scope.event_pins)
            and complete["segments"] == len(scope.event_pins)
            and complete["callbacks_started"] == len(scope.callbacks) * len(scope.event_pins)
            and complete["coordinates_sampled"] == len(scope.coordinates)
            and complete["computations"] == expected_calls
            and complete["lane_state_ref"].startswith(grant.grant_ref + "::"))


def _run_worker_v1(input_stream, output_stream):
    """Closed deterministic single or registered pair profiles; no owner/store access."""
    import os
    import sys
    from pathlib import Path
    from .models import (EvidenceSignedMessageV1, EvidenceAuthorizationMessageV1, EvidenceMessageKindV1,
                         EvidenceAttemptGrantPayloadV1, EvidenceEnvironmentIdentityV1, _evidence_decode_authorization_payload_v1)
    from .implementation_registry import (resolve_evidence_invocation_v1, invoke_evidence_public_wire_v1,
        invoke_evidence_private_wire_v1, LP03_DECIMAL_CONTEXT_POLICY_REF_V1)
    from .serialization import safe_json_loads
    from .latency_policy import _EvidenceLocalClockV1, _evidence_invocation_measurement_v1
    raw = _read_worker_frame_bytes_v1(input_stream, 65536)
    _native_require(raw is not None, "LP03_WORKER_START_REQUIRED")
    start_body = _evidence_canonical_object_v1(raw[4:])
    _native_require(isinstance(start_body, Mapping) and start_body.get("kind") == "START", "LP03_WORKER_START_REQUIRED")
    attempt_ref, fence_ref = start_body.get("attempt_ref"), start_body.get("fence_ref")
    start = decode_evidence_worker_frame_v1(raw, direction="PARENT_TO_WORKER", attempt_ref=attempt_ref,
        fence_ref=fence_ref, ordinal=0, frame_byte_limit=65536)
    # Structural data verification is not a grant handle or source authority.
    # The parent verifies the actual enrolled signature and original ledger.
    signed = EvidenceSignedMessageV1.from_canonical_mapping(dict(start["payload"]["signed_grant"]))
    message = EvidenceAuthorizationMessageV1.from_canonical_mapping(
        _evidence_canonical_object_v1(signed.canonical_message.encode("utf-8")))
    grant = _evidence_decode_authorization_payload_v1(message)
    scope = grant.causal_timeline_v1() if type(grant) is EvidenceAttemptGrantPayloadV1 else None
    _native_require(message.kind is EvidenceMessageKindV1.ATTEMPT_GRANT and type(grant) is EvidenceAttemptGrantPayloadV1
                    and grant.grant_ref == attempt_ref and grant.fence_ref == fence_ref
                    and grant.component_closure in (("MATH-06",), ("MATH-07",), ("MATH-01",), ("MATH-03",), ("MATH-04",), ("MATH-05",), ("MATH-08",), ("MATH-09",), ("MATH-10",), ("MATH-11",), ("MATH-14",), ("MATH-15",), ("MATH-16",), ("MATH-17",), ("MATH-18",), ("MATH-19",), ("MATH-20",), ("MATH-21",), ("MATH-22",), ("MATH-23",), ("MATH-24",), ("MATH-25",), ("MATH-12",), ("MATH-13",), ("MATH-26",), ("MATH-27",), ("MATH-28",), ("MATH-29",), ("MATH-30",), ("MATH-31",), ("MATH-37",), ("MATH-32",), ("MATH-33",), ("MATH-35",), ("MATH-36",), ("MATH-38",), ("MATH-39",), ("MATH-40",), ("MATH-41",), ("MATH-42",), ("MATH-43",), ("MATH-44",), ("MATH-45",), ("MATH-50",), ("MATH-51",), ("MATH-52",), ("MATH-01", "MATH-02"))
                    and (grant.callback_pins == () if scope is None else scope.scenario_plan.origin is message.origin),
                    "LP03_WORKER_PROFILE_UNAVAILABLE")
    edge = grant.component_closure == ("MATH-01", "MATH-02")
    computations = 2 if edge else 1
    math_id = grant.component_closure[-1] if edge else grant.component_closure[0]
    heldout = math_id in ("MATH-20", "MATH-21")
    quantum = math_id in ("MATH-50", "MATH-51", "MATH-52")
    recorded_dr = math_id == "MATH-22"
    if recorded_dr:
        dr_limits = grant.component_and_callback_pins["supplementary_uncertainty_policy"]
        computations = 2
    if heldout:
        pins = grant.component_and_callback_pins.get("supplementary_scorers")
        _native_require(type(pins) is tuple and len(pins) == 1, "LP03_WORKER_HELD_OUT_SIGNED_SCORER_REQUIRED")
        scorer_pin = pins[0]
        scorer_contract = resolve_evidence_invocation_v1(scorer_pin[0], implementation_pin=scorer_pin[1],
            specification_pin=scorer_pin[2], resource_policy_ref=scorer_pin[3], origin=message.origin)
    edge_clock_guard = None
    if edge:
        edge_contracts = tuple(resolve_evidence_invocation_v1(row[0], implementation_pin=row[1],
            specification_pin=row[2], resource_policy_ref=grant.protocol_ref, origin=message.origin)
            for row in grant.component_and_callback_pins["components"])
        _native_require(tuple(row.math_id for row in edge_contracts) == grant.component_closure
            and all(row.origin_policy == "SOFTWARE_CONFORMANCE" for row in edge_contracts),
            "LP03_WORKER_EDGE_GRANT_CONTRACTS")
    limits = grant.budgets
    _native_require(len(raw) - 4 <= limits.frame_byte_limit and limits.max_events >= 1
                    and (scope is not None or limits.max_computations >= computations)
                    and limits.segment_max_events >= 1, "LP03_WORKER_RESOURCE_EXHAUSTED")
    expected_environment = EvidenceEnvironmentIdentityV1.from_canonical_mapping(
        _evidence_canonical_object_v1(deterministic_json(start["payload"]["environment_identity"]).encode("utf-8")))
    _native_require(_worker_environment_v1() == expected_environment, "LP03_WORKER_ENVIRONMENT_MISMATCH")
    _native_ident(start["payload"]["package_identity_ref"])
    clock = _EvidenceLocalClockV1()
    _native_require((clock.clock_domain_id, clock.boot_identity_ref)
                    == (grant.deadline.clock_domain_id, grant.deadline.boot_identity_ref), "LP03_WORKER_CLOCK_DOMAIN_MISMATCH")

    def current():
        if edge_clock_guard is not None:
            edge_clock_guard()
        wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(clock)
        if edge_clock_guard is not None:
            edge_clock_guard()
        monotonic_current = grant.deadline.admitted_monotonic_ns <= mono < grant.deadline.exclusive_deadline_monotonic_ns
        wall_current = message.valid_from_wall_ns <= wall < message.exclusive_expiry_wall_ns
        if not (monotonic_current and wall_current):
            clocks = dict(observed_wall_ns=wall, valid_from_wall_ns=message.valid_from_wall_ns,
                exclusive_expiry_wall_ns=message.exclusive_expiry_wall_ns, observed_monotonic_ns=mono,
                admitted_monotonic_ns=grant.deadline.admitted_monotonic_ns,
                exclusive_deadline_monotonic_ns=grant.deadline.exclusive_deadline_monotonic_ns,
                wall_current=wall_current, monotonic_current=monotonic_current)
            _native_require(False, "LP03_WORKER_EXPIRED " + deterministic_json(clocks))
        return wall, mono, _cpu

    current()
    outgoing, incoming, emitted = 0, 1, 0

    def send(kind, payload):
        nonlocal outgoing, emitted
        frame = dict(protocol=WORKER_PROTOCOL_V1, kind=kind, attempt_ref=attempt_ref, fence_ref=fence_ref,
                     ordinal=outgoing, payload=payload)
        raw_frame = encode_evidence_worker_frame_v1(frame, direction="WORKER_TO_PARENT", attempt_ref=attempt_ref,
            fence_ref=fence_ref, ordinal=outgoing, frame_byte_limit=limits.frame_byte_limit)
        if scope is not None and kind == "SEGMENT":
            _native_require(len(raw_frame) <= limits.segment_max_bytes, "LP03_TIMELINE_OUTPUT_SEGMENT_BYTE_LIMIT")
        _native_require(emitted + len(raw_frame) <= limits.max_output_bytes, "LP03_WORKER_RESOURCE_EXHAUSTED")
        emitted += len(raw_frame)
        _write_worker_bytes_v1(output_stream, raw_frame)
        outgoing += 1

    def receive(expected_kind, *, with_size=False):
        nonlocal incoming
        incoming_raw = _read_worker_frame_bytes_v1(input_stream, limits.frame_byte_limit)
        _native_require(incoming_raw is not None, "LP03_WORKER_UNEXPECTED_EOF")
        frame = decode_evidence_worker_frame_v1(incoming_raw, direction="PARENT_TO_WORKER", attempt_ref=attempt_ref,
            fence_ref=fence_ref, ordinal=incoming, frame_byte_limit=limits.frame_byte_limit)
        incoming += 1
        _native_require(frame["kind"] != "CANCEL", "LP03_WORKER_CANCELLED")
        _native_require(frame["kind"] == expected_kind, "LP03_WORKER_CAUSAL_FRAME_ORDER")
        current()
        return (frame["payload"], len(incoming_raw)) if with_size else frame["payload"]

    edge_chain = edge_export = edge_export_code = None
    edge_entered = False
    if edge:
        from dataclasses import fields
        from types import FunctionType, BuiltinFunctionType
        from . import latency_policy as edge_clock_owner
        from .implementation_registry import (_EvidenceProbabilityEdgeChainV1,
            EvidencePrivateInvocationContractV1)
        from .serialization import _encode_evidence_projection_json_v1
        edge_clock_type = _EvidenceLocalClockV1
        edge_clock_namespace = tuple(edge_clock_type.__dict__.items())
        edge_clock_functions = tuple((member, member.__code__) for _name, member in edge_clock_namespace
                                     if type(member) is FunctionType)
        edge_observe, edge_declare = edge_clock_type.observe_v1, edge_clock_type.declaration_v1
        edge_measure = _evidence_invocation_measurement_v1
        edge_measure_code = edge_measure.__code__
        edge_native_clocks = (edge_clock_owner.time.time_ns, edge_clock_owner.time.monotonic_ns,
                              edge_clock_owner.time.process_time_ns)
        edge_clock_fields = ("_kernel", "_ntdll", "_process", "_identity", "clock_domain_id", "process_identity_ref",
                             "boot_identity_ref", "_EvidenceLocalClockV1__functions", "_EvidenceLocalClockV1__declarations")
        edge_clock_facts = tuple(object.__getattribute__(clock, name) for name in edge_clock_fields)
        edge_declarations_original = edge_declare(clock)
        edge_declarations = {name:dict(implementation=edge_declarations_original[name]["implementation"],
            reported_resolution_ns=tuple(edge_declarations_original[name]["reported_resolution_ns"]),
            uncertainty_ns_or_absence=dict(edge_declarations_original[name]["uncertainty_ns_or_absence"]))
            for name in ("wall", "monotonic", "process_cpu")}
        edge_identity = dict(clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref,
                             process_identity_ref=clock.process_identity_ref)
        edge_aggregate = dict(clock_identity=edge_identity, clock_declarations=edge_declarations,
            started=None, completed=None, call_outcome="NOT_STARTED", measurement_failure_class_or_none=None)
        edge_contract_data = tuple({field.name:(list(getattr(row, field.name)) if field.name == "owner_bindings"
                                               else getattr(row, field.name))
                                   for field in fields(EvidencePrivateInvocationContractV1)} for row in edge_contracts)

        def edge_exception_label(exc):
            # Explicit absence labels are not claims about a different class.
            kind = type(exc)
            if type(kind) is not type:
                return "UNAVAILABLE::EXCEPTION_CLASS_METADATA_TYPE"
            module = type.__getattribute__(kind, "__module__")
            name = type.__getattribute__(kind, "__qualname__")
            if type(module) is not str or type(name) is not str or not 0 < len(module) + 1 + len(name) <= 256:
                return "UNAVAILABLE::EXCEPTION_CLASS_METADATA_LENGTH"
            label = module + "." + name
            try:
                _native_ident(label)
            except Exception:
                return "UNAVAILABLE::EXCEPTION_CLASS_METADATA_CHARACTERS"
            return label

        def edge_check_clock():
            _native_require(edge_clock_owner._EvidenceLocalClockV1 is edge_clock_type
                and tuple(edge_clock_type.__dict__) == tuple(name for name, _ in edge_clock_namespace)
                and all(edge_clock_type.__dict__[name] is member for name, member in edge_clock_namespace)
                and all(function.__code__ is code for function, code in edge_clock_functions)
                and edge_clock_owner._evidence_invocation_measurement_v1 is edge_measure
                and edge_measure.__code__ is edge_measure_code
                and all(type(function) is BuiltinFunctionType for function in edge_native_clocks)
                and all(actual is original for actual,original in zip(
                    (edge_clock_owner.time.time_ns, edge_clock_owner.time.monotonic_ns,
                     edge_clock_owner.time.process_time_ns), edge_native_clocks, strict=True))
                and all(object.__getattribute__(clock, name) is original
                        for name,original in zip(edge_clock_fields, edge_clock_facts, strict=True))
                and edge_declare(clock) is edge_declarations_original,
                "LP03_WORKER_EDGE_ORIGINAL_AGGREGATE_CLOCK_CHANGED")

        def edge_finish_aggregate():
            nonlocal measurement
            # Capture the actual sample before validation or formatting. A
            # primary call error and a secondary clock error remain distinct.
            edge_check_clock()
            edge_aggregate["completed"] = edge_observe(clock)
            edge_check_clock()
            began, ended = edge_aggregate["started"], edge_aggregate["completed"]
            candidate = dict(edge_identity, clock_declarations=edge_declarations, started=began, completed=ended,
                duration_ns=ended[1] - began[1], cpu_ns=ended[2] - began[2], outcome=edge_aggregate["call_outcome"])
            edge_measure(candidate)
            edge_check_clock()
            measurement = candidate

        def edge_failed_payload(exc):
            payload = dict(reason_code=(exc.reason_code.value if isinstance(exc, ComputationControlPlaneError)
                                        else "WORKER_PROTOCOL_OR_COMPUTATION_FAILED"),
                exception_class=edge_exception_label(exc), event_ordinal=0, measurement_or_absence=measurement,
                producer_invocation_contract=edge_contract_data[0], invocation_contract=edge_contract_data[1],
                aggregate_observation_prefix=edge_aggregate,
                chain_prefix_or_absence=dict(state="ABSENT_WITH_REASON",
                    reason="CHAIN_NOT_CREATED" if edge_chain is None else "CHAIN_NOT_STARTED",
                    capture_exception_class_or_none=None))
            if edge_chain is not None and edge_entered:
                try:
                    _native_require(edge_export is not None and edge_export.__code__ is edge_export_code,
                                    "LP03_WORKER_EDGE_ORIGINAL_PREFIX_ACCESSOR_CHANGED")
                    # A sizing shell only: an empty prefix is never sent or
                    # passed through the successful frame validator.
                    payload["chain_prefix_or_absence"] = dict(state="CAPTURED_ORIGINAL_PREFIX_DIAGNOSTIC", prefix_json="")
                    shell = dict(protocol=WORKER_PROTOCOL_V1, kind="FAILED", attempt_ref=attempt_ref,
                                 fence_ref=fence_ref, ordinal=outgoing, payload=payload)
                    shell_bytes = 4 + len(_encode_evidence_projection_json_v1(shell,
                        maximum_bytes=limits.frame_byte_limit, maximum_nodes=4096))
                    embedded_limit = min(65536, min(limits.frame_byte_limit + 4,
                        limits.max_output_bytes - emitted) - shell_bytes + 2)
                    _native_require(embedded_limit > 2, "LP03_WORKER_EDGE_FAILURE_OUTPUT_EXHAUSTED")
                    captured = edge_export(edge_chain, maximum_bytes=min(65536, embedded_limit),
                                           maximum_embedded_bytes=embedded_limit)
                    _native_require(edge_export.__code__ is edge_export_code and type(captured) is bytes,
                                    "LP03_WORKER_EDGE_ORIGINAL_PREFIX_ACCESSOR_CHANGED")
                    payload["chain_prefix_or_absence"] = dict(state="CAPTURED_ORIGINAL_PREFIX_DIAGNOSTIC",
                                                               prefix_json=captured.decode("utf-8", "strict"))
                except BaseException as capture_error:
                    payload["chain_prefix_or_absence"] = dict(state="ABSENT_WITH_REASON",
                        reason="ORIGINAL_PREFIX_ENCODING_FAILED",
                        capture_exception_class_or_none=edge_exception_label(capture_error))
            return payload

        edge_clock_guard = edge_check_clock

    send("STARTED", dict(environment_identity=_worker_environment_v1(), executable=str(Path(sys.executable).resolve()),
        base_executable=str(Path(sys._base_executable).resolve()), prefix=str(Path(sys.prefix).resolve()),
        base_prefix=str(Path(sys.base_prefix).resolve()), module_file=str(Path(__file__).resolve()), process_id=os.getpid(),
        clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref))
    if scope is not None:
        _native_require(scope.scenario_plan.exact_environment_identity == expected_environment,
                        "LP03_TIMELINE_SCENARIO_RUNTIME_JOIN")
        return _run_causal_timeline_worker_v1(grant=grant, scope=scope, clock=clock, current=current, send=send,
                                             receive=receive, input_stream=input_stream)
    measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_NOT_STARTED")
    try:
        refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                     for selection in grant.allowed_reads for ref in selection.selection.record_refs)
        send("READ_REQUEST", dict(record_refs=refs))
        inputs = receive("INPUT_SEGMENT")
        _native_require(type(inputs["segment_ordinal"]) is int and inputs["segment_ordinal"] == 0
                        and inputs["final_segment"] is True and tuple(inputs["original_record_refs"]) == tuple(_evidence_frozen_data_v1(refs)),
                        "LP03_WORKER_INPUT_SEGMENT_SCOPE")
        _native_require(len(deterministic_json(inputs).encode("utf-8")) <= limits.segment_max_bytes, "LP03_WORKER_SEGMENT_TOO_LARGE")
        if math_id == "MATH-39":
            _worker_math39_queue_inputs_v1(inputs, inputs["event"], signed_reads=grant.allowed_reads)
        elif math_id in ("MATH-36", "MATH-41", "MATH-42", "MATH-43", "MATH-44"):
            _native_require(inputs["invocation_contract"]["math_id"] == math_id,
                "LP03_WORKER_INPUT_GRANT_CONTRACT_JOIN")
            _worker_original_private_inputs_v1(inputs, inputs["event"], signed_reads=grant.allowed_reads)
        if quantum:
            quantum_inputs = _worker_original_quantum_inputs_v1(inputs, inputs["event"], grant=grant)
        if math_id in ("MATH-06","MATH-07"):
            _native_require(inputs["event"]["kind"] == "SYNTHETIC_SIGNED_TOTAL_CASHFLOW_CONTEXT"
                and inputs["event"]["payload"]["math_id"] == math_id,
                "LP03_WORKER_CASHFLOW_GRANT_EVENT_JOIN")
            metadata=inputs["event"]["payload"]["source_slices"][0]["reconstructed_canonical_events"][0]["values"]["cashflow_context"]
            _native_require(message.exclusive_expiry_wall_ns <= metadata["horizon_end_wall_ns"],
                "LP03_WORKER_CASHFLOW_ORIGINAL_HORIZON_LIMIT")

        decision = current()
        event = inputs["event"]
        _native_require(event["availability_wall_ns"] <= decision[0] and event["local_ordinal"] == 0,
                        "LP03_WORKER_EVENT_NOT_AVAILABLE")
        continuation = receive("CONTINUE")
        _native_require(dict(continuation) == dict(command="COMPUTE", event_ordinal=0), "LP03_WORKER_CAUSAL_FRAME_ORDER")
        if edge:
            decoded_contracts, edge_context, market_wire, model_wire, conversion_id = _worker_probability_edge_inputs_v1(
                inputs, event, attempt_ref=attempt_ref)
            _native_require(decoded_contracts == edge_contracts
                and all(deterministic_json(inputs[name]) == deterministic_json(row)
                        for name,row in zip(("producer_invocation_contract","invocation_contract"), edge_contracts, strict=True)),
                "LP03_WORKER_EDGE_INPUT_GRANT_CONTRACT_JOIN")
            from .models import _evidence_probability_edge_chain_sources_v1
            edge_sources = _evidence_probability_edge_chain_sources_v1(event["payload"])
            horizon = edge_sources[0].reconstructed_canonical_events[0]["values"]["contract_context"]["horizon_end_wall_ns"]
            _native_require(message.exclusive_expiry_wall_ns <= horizon,
                            "LP03_WORKER_EDGE_GRANT_EXCEEDS_SOURCE_HORIZON")
            edge_limits = (message.valid_from_wall_ns, min(message.exclusive_expiry_wall_ns, horizon),
                grant.deadline.admitted_monotonic_ns, grant.deadline.exclusive_deadline_monotonic_ns)
            edge_check_clock()
            capacity = _worker_probability_edge_capacity_v1(clock=clock, contracts=edge_contracts,
                attempt_ref=attempt_ref, fence_ref=fence_ref, original_record_refs=refs, market_input_json=market_wire,
                frame_byte_limit=limits.frame_byte_limit, remaining_output_bytes=limits.max_output_bytes - emitted)
            edge_chain = _EvidenceProbabilityEdgeChainV1(contracts=edge_contracts, market_input_json=market_wire,
                model_input_json=model_wire, context=edge_context, conversion_receipt_id=conversion_id,
                maximum_input_bytes=min(65536, limits.max_input_bytes, limits.segment_max_bytes), maximum_nodes=4096,
                maximum_output_bytes=capacity["chain_output_limit"], measurement_clock=clock, execution_clock_limits=edge_limits)
            edge_export = _EvidenceProbabilityEdgeChainV1.failure_prefix_v1
            edge_export_code = edge_export.__code__
            edge_original = edge_chain.original
            _native_require(edge_original[0] is edge_contracts and edge_original[1] is market_wire
                and edge_original[2] is model_wire and edge_original[3] is edge_context and edge_original[4] == conversion_id
                and edge_original[7] == capacity["chain_output_limit"] and edge_chain.execution_clock_limits is edge_limits,
                "LP03_WORKER_EDGE_ORIGINAL_CAPACITY_BINDING")
            current()
            try:
                edge_check_clock()
                edge_aggregate["started"] = edge_observe(clock)
                edge_aggregate["call_outcome"] = "ENTERED"
                edge_check_clock()
            except BaseException as clock_error:
                edge_aggregate["measurement_failure_class_or_none"] = edge_exception_label(clock_error)
                measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_CLOCK_UNAVAILABLE")
                raise
            measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_CLOCK_UNAVAILABLE")
            try:
                _native_require(edge_limits[0] <= edge_aggregate["started"][0] < edge_limits[1]
                    and edge_limits[2] <= edge_aggregate["started"][1] < edge_limits[3],
                    "LP03_WORKER_EDGE_AGGREGATE_START_EXPIRED")
                edge_entered = True
                completed_chain = _EvidenceProbabilityEdgeChainV1.run_v1(edge_chain)
                edge_aggregate["call_outcome"] = "SUCCESS"
                _native_require(completed_chain is edge_chain, "LP03_WORKER_EDGE_ORIGINAL_COMPLETION")
                state = edge_chain.inspect_v1()
                _native_require(state["phase"] == "COMPLETED" and state["consumer"].contract is edge_contracts[1]
                    and state["producer"].contract is edge_contracts[0] and type(state["artifact_json"]) is bytes,
                    "LP03_WORKER_EDGE_ORIGINAL_COMPLETION")
                raw_output_json = state["consumer"].output_json.decode("utf-8", "strict")
                artifact_json = state["artifact_json"].decode("utf-8", "strict")
            except BaseException:
                if edge_aggregate["call_outcome"] != "SUCCESS":
                    edge_aggregate["call_outcome"] = "FAILED"
                try:
                    edge_finish_aggregate()
                except BaseException as clock_error:
                    edge_aggregate["measurement_failure_class_or_none"] = edge_exception_label(clock_error)
                    measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_CLOCK_UNAVAILABLE")
                raise
            edge_aggregate["call_outcome"] = "SUCCESS"
            # This is deliberately outside the primary-call exception block:
            # a failed end observation never rewrites successful call status
            # or attempts the same end observation a second time.
            try:
                edge_finish_aggregate()
            except BaseException as clock_error:
                edge_aggregate["measurement_failure_class_or_none"] = edge_exception_label(clock_error)
                measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_CLOCK_UNAVAILABLE")
                raise
            _native_require(edge_limits[0] <= edge_aggregate["completed"][0] < edge_limits[1]
                and edge_limits[2] <= edge_aggregate["completed"][1] < edge_limits[3],
                "LP03_WORKER_EDGE_AGGREGATE_END_EXPIRED")
            current()
            send("COMPUTATION_RESULT", dict(event_ordinal=0, invocation_contract=edge_contract_data[1],
                producer_invocation_contract=edge_contract_data[0], numeric_context_policy_ref=LP03_DECIMAL_CONTEXT_POLICY_REF_V1,
                raw_output_json=raw_output_json, original_record_refs=refs, invocation_measurement=measurement,
                chain_artifact_json=artifact_json))
        else:
            pin = grant.component_and_callback_pins["components"][0]
            _native_require(pin[0] == math_id, "LP03_WORKER_COMPONENT_PIN_JOIN")
            contract = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
                resource_policy_ref=grant.protocol_ref, origin=message.origin)
            _native_require((math_id == "MATH-03" and "invocation_contract" not in inputs)
                            or (math_id in ("MATH-06", "MATH-07", "MATH-01", "MATH-04", "MATH-05", "MATH-08", "MATH-09", "MATH-10", "MATH-11", "MATH-14", "MATH-15", "MATH-16", "MATH-17", "MATH-18", "MATH-19", "MATH-20", "MATH-21", "MATH-22", "MATH-23", "MATH-24", "MATH-25", "MATH-12", "MATH-13", "MATH-26", "MATH-27", "MATH-28", "MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52") and "invocation_contract" in inputs
                                and deterministic_json(inputs["invocation_contract"]) == deterministic_json(contract)),
                            "LP03_WORKER_INPUT_GRANT_CONTRACT_JOIN")
            if heldout:
                _native_require(deterministic_json(inputs["scorer_invocation_contract"]) == deterministic_json(scorer_contract),
                    "LP03_WORKER_HELD_OUT_SIGNED_SCORER_JOIN")
                _, scored_trace = _worker_heldout_inputs_v1(inputs, inputs["event"])
                computations = _heldout_computation_count_v1(math_id, inputs["inputs"])
                _native_require(computations <= limits.max_computations, "LP03_WORKER_HELD_OUT_COMPUTATION_BUDGET")
            current()
            began = _EvidenceLocalClockV1.observe_v1(clock)
            measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_CLOCK_UNAVAILABLE")
            outcome = "FAILED"
            try:
                # The input graph is this worker's own previously bounded frame
                # reconstruction. Include its wire conversion and the complete
                # original dispatch/output boundary in success/failure measurement.
                input_json = deterministic_json(inputs["inputs"]).encode("utf-8")
                invocation = invoke_evidence_private_wire_v1 if math_id in ("MATH-26", "MATH-27", "MATH-28", "MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-38", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52") else invoke_evidence_public_wire_v1
                original_result = invocation(contract, input_json,
                    maximum_input_bytes=min(limits.max_input_bytes, limits.segment_max_bytes), maximum_nodes=4096,
                    maximum_output_bytes=min(limits.frame_byte_limit, limits.max_output_bytes - emitted), maximum_output_nodes=4096)
                raw_output_json = original_result.output_json.decode("utf-8", "strict")
                _native_require(original_result.contract is contract
                                and (math_id != "MATH-03" or type(safe_json_loads(raw_output_json)) is str),
                                "LP03_WORKER_ORIGINAL_RAW_OUTPUT_JOIN")
                if quantum:
                    constructor = original_result.constructor_receipt_or_none
                    constructor_wire = deterministic_json(constructor)
                    _evidence_original_quantum_constructor_result_v1(math_id, raw_output_json, constructor_wire,
                        maximum_bytes=min(65536, limits.frame_byte_limit, limits.max_output_bytes - emitted),
                        input_lock_ref=grant.input_lock_ref, original_values=quantum_inputs)
                outcome = "SUCCESS"
            finally:
                ended = _EvidenceLocalClockV1.observe_v1(clock)
                measurement = _evidence_invocation_measurement_v1(dict(clock_domain_id=clock.clock_domain_id,
                    boot_identity_ref=clock.boot_identity_ref, process_identity_ref=clock.process_identity_ref,
                    clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock),
                    started=began, completed=ended, duration_ns=ended[1] - began[1], cpu_ns=ended[2] - began[2], outcome=outcome))
            current()
            result = dict(event_ordinal=0, invocation_contract=contract,
                numeric_context_policy_ref=LP03_DECIMAL_CONTEXT_POLICY_REF_V1, raw_output_json=raw_output_json,
                original_record_refs=refs, invocation_measurement=measurement)
            if quantum:
                result["quantum_constructor_receipt_json"] = constructor_wire
            if heldout:
                topology_raw = original_result.output_json
                allowance = min(limits.frame_byte_limit, limits.max_output_bytes - emitted)
                # The topology and scorer receipts are nested JSON strings.
                # Check the complete encoded outer frame before sending.
                topology_cost = len(deterministic_json(raw_output_json).encode("utf-8"))
                envelope_cost = 4096 + topology_cost + len(deterministic_json(refs).encode("utf-8"))
                artifact_allowance = (allowance - envelope_cost) // 2
                _native_require(artifact_allowance > 0, "LP03_WORKER_HELD_OUT_COMPLETE_WIRE_CAPACITY")
                measured = measure_evidence_fold_scores_v1(topology_math_id=math_id, topology_raw_json=topology_raw,
                    scored_trace=scored_trace, scorer_contract=scorer_contract, clock=clock, grant=grant, message=message,
                    maximum_input_bytes=min(limits.max_input_bytes, limits.segment_max_bytes),
                    maximum_output_bytes=artifact_allowance, maximum_nodes=4096)
                _native_require(len(measured) + 1 == computations, "LP03_WORKER_HELD_OUT_COMPLETE_CALL_COUNT")
                artifact = dict(profile="ORIGINAL_WORKER_HELD_OUT_SCORES_V1", topology_math_id=math_id,
                    scorer_math_id=scorer_contract.math_id, folds=tuple(dict(ordinal=ordinal,
                        training_receipt_ref=train_ref, sample_receipts=sample_refs,
                        scorer_raw_json=scored.output_json.decode("utf-8", "strict"),
                        invocation_measurement=sample_measurement)
                        for ordinal, train_ref, sample_refs, scored, sample_measurement in measured))
                artifact_json = deterministic_json(artifact)
                raw_artifact = artifact_json.encode("utf-8", "strict")
                _native_require(len(raw_artifact) <= artifact_allowance
                    and len(deterministic_json(artifact_json).encode("utf-8")) + envelope_cost <= allowance,
                    "LP03_WORKER_HELD_OUT_COMPLETE_WIRE_CAPACITY")
                _evidence_decode_heldout_worker_artifact_v1(raw_artifact, topology_math_id=math_id,
                    topology_raw_json=topology_raw, scorer_contract=scorer_contract,
                    maximum_bytes=allowance, maximum_nodes=4096)
                result.update(scorer_invocation_contract=scorer_contract, held_out_score_artifact_json=artifact_json)
            if recorded_dr:
                from .parameter_policy import _EvidenceNumericalWorkV1
                from .models import _evidence_dr_original_source_data_v1
                source = inputs["event"]["payload"]
                source_parts, _, policy, _, _ = _evidence_dr_original_source_data_v1(
                    source, original_raw_ref=attempt_ref+"::DATA::RAW")
                _native_require(policy["protocol_ref"] == dr_limits["parameter_protocol_ref"]
                    and source_parts[1].original_record_refs[0].record_id == dr_limits["uncertainty_source_ref"],
                    "LP03_WORKER_DR_ORIGINAL_SIGNED_PARAMETER_POLICY")
                work = _EvidenceNumericalWorkV1(dr_limits["numerical_work_limits"],
                    retained_input_capacity=3+len(policy["group_weights"]))
                allowance = min(limits.frame_byte_limit, limits.max_output_bytes-emitted)
                envelope_bytes = 4096 + len(deterministic_json(result).encode("utf-8"))
                certificate, measured = _measure_original_recorded_dr_continuation_v1(envelope=message,
                    grant=grant, clock=clock, original=original_result, source_payload=source,
                    maximum_input_bytes=min(limits.segment_max_bytes, limits.max_input_bytes, limits.frame_byte_limit),
                    maximum_output_bytes=(allowance-envelope_bytes)//4, work=work)
                artifact_json = deterministic_json(dict(profile="ORIGINAL_WORKER_RECORDED_DR_UNCERTAINTY_V1",
                    estimator_original_raw_ref=attempt_ref+"::DATA::RAW", certificate_json=certificate.decode("utf-8"),
                    invocation_measurement=measured))
                _native_require(len(deterministic_json(artifact_json).encode("utf-8")) + envelope_bytes <= allowance,
                    "LP03_WORKER_DR_CONTINUATION_WIRE_CAPACITY")
                _evidence_decode_recorded_dr_worker_artifact_v1(artifact_json, raw_output_json=raw_output_json,
                    attempt_ref=attempt_ref, topology_measurement=measurement, maximum_bytes=allowance)
                result["dr_uncertainty_artifact_json"] = artifact_json
            current()
            send("COMPUTATION_RESULT", result)
        send("SEGMENT", dict(segment_ordinal=0, first_event_ordinal=0, last_event_ordinal=0, computations=computations, complete=True))
        finish = receive("CONTINUE")
        _native_require(dict(finish) == dict(command="FINISH", event_ordinal=1), "LP03_WORKER_CAUSAL_FRAME_ORDER")
        _native_require(input_stream.read(1) == b"", "LP03_WORKER_TRAILING_INPUT")
        if edge:
            current()
        send("COMPLETE", dict(events=1, computations=computations, segments=1))
        return 0
    except BaseException as exc:
        if not edge and not isinstance(exc, Exception):
            raise
        import traceback
        from .errors import ComputationControlPlaneError
        if edge:
            # Reporting/transport failure cannot replace the captured primary.
            try:
                traceback.print_exc(limit=8, file=sys.stderr)
            except BaseException:
                pass
            try:
                send("FAILED", edge_failed_payload(exc))
            except BaseException:
                raise exc
            return 1
        traceback.print_exc(limit=8, file=sys.stderr)
        reason = exc.reason_code.value if isinstance(exc, ComputationControlPlaneError) else "WORKER_PROTOCOL_OR_COMPUTATION_FAILED"
        send("FAILED", dict(reason_code=reason, exception_class=type(exc).__module__ + "." + type(exc).__qualname__,
                            event_ordinal=0, measurement_or_absence=measurement))
        return 1


class EvidencePlatformV1:
    """Explicit original lane composition; worker execution still belongs to SVC."""

    __slots__ = ("_host", "_store", "_supervisor", "_lane", "_original")

    def __init__(self):
        raise TypeError("use the original explicit lane binding")

    def __copy__(self):
        raise TypeError("LP03 lane composition cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 lane composition cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 lane composition cannot be serialized")

    @classmethod
    def bind_evidence_lane_v1(cls, *, host_binding, store, supervisor):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from .models import EvidenceLaneV1, EvidenceStoreRoleV1, EvidenceKeyPurposeV1
        from .persistence import _EvidenceBoundStoreV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        _native_require(cls is EvidencePlatformV1 and type(host_binding) is EvidenceHostBindingV1
                        and type(store) is SQLiteReferenceAdapterV1 and type(supervisor) is EvidenceProcessSupervisorV1,
                        "LP03_ORIGINAL_LANE_COMPOSITION")
        EvidenceProcessSupervisorV1._assert_original_v1(supervisor)
        retained = store._evidence_store_binding_v1
        config, issuer_config = host_binding.public_configuration, supervisor._issuer.host.public_configuration
        _native_require(type(retained) is _EvidenceBoundStoreV1
                        and retained.binding.role in (EvidenceStoreRoleV1.REPLAY, EvidenceStoreRoleV1.PAPER)
                        and host_binding.signing_purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER
                        and config.service_owner == "QKU_COMPUTATION_CONTROL_PLANE"
                        and config.service_principal == retained.binding.allowed_writer_principal
                        and config.store_bindings == issuer_config.store_bindings
                        and config.deployment_id == issuer_config.deployment_id
                        and config.environment_identity == issuer_config.environment_identity
                        and config.package_identity_ref == issuer_config.package_identity_ref
                        and config.generation == issuer_config.generation
                        and config.verification_keys == issuer_config.verification_keys
                        and "VERIFY_OWN_COMMITTED_BATCH" in retained.binding.allowed_reader_purposes,
                        "LP03_LANE_ORIGINAL_ROLE_CONFIGURATION")
        _EvidenceBoundStoreV1._require_original_objects_v1(retained, host_binding, store)
        lane = EvidenceLaneV1(retained.binding.role.value)
        with supervisor._issuer.lock:
            _native_require(supervisor._issuer.operation is None and all(entry._lane is not lane for entry in supervisor._lane_platforms),
                            "LP03_LANE_ALREADY_BOUND_OR_BUSY")
            result = object.__new__(cls)
            result._host, result._store, result._supervisor, result._lane = host_binding, store, supervisor, lane
            result._original = (host_binding, store, supervisor, lane, retained)
            supervisor._lane_platforms = (*supervisor._lane_platforms, result)
            return result

    def _assert_original_v1(self):
        _native_require(type(self) is EvidencePlatformV1 and all(left is right for left, right in zip(
            (self._host, self._store, self._supervisor, self._lane, self._store._evidence_store_binding_v1), self._original))
            and any(entry is self for entry in self._supervisor._lane_platforms), "LP03_ORIGINAL_LANE_BINDING_CHANGED")

    def run_lane_v1(self, attempt_grant):
        from ...service.pr169_svc1_resolvers import DashboardReadModelService, EvidenceProcessSupervisorV1
        from .persistence import _EvidenceLaneOperationV1, _EvidenceRegistrationOperationV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        from .transaction import TrancheCUnitOfWorkV1, TransactionRetryPolicyV1
        EvidencePlatformV1._assert_original_v1(self)
        attempt = attempt_grant._attempt
        _native_require(attempt.supervisor is self._supervisor and attempt.request.lane is self._lane
                        and attempt.lane_operation is None, "LP03_LANE_ORIGINAL_ATTEMPT")
        DashboardReadModelService.dispatch_evidence_attempt_v1(self._supervisor._service, attempt_grant)
        try:
            operation = _EvidenceLaneOperationV1(self, attempt)
        except BaseException as original_error:
            native = self._supervisor._active
            if native is not None and native.original[1] is attempt:
                trigger_original = EvidenceProcessSupervisorV1._retain_failure_trigger_v1(self._supervisor, native, original_error)
                EvidenceProcessSupervisorV1._audit_failure_v1(self._supervisor, native,
                    reason="INTEGRITY_FAILURE", original_error=original_error, trigger_original=trigger_original)
            raise
        registration = attempt.registration
        with registration.issuer.lock:
            _native_require(registration.active_lane_operation is None, "LP03_LANE_OPERATION_REENTRY")
            registration.active_lane_operation = operation
            try:
                with EvidenceProcessSupervisorV1._operation_v1(self._supervisor, attempt):
                    unit = TrancheCUnitOfWorkV1(self._store, TransactionRetryPolicyV1(max_transaction_attempts=1))
                    TrancheCUnitOfWorkV1.execute_evidence_v1(unit, operation=operation)
                    SQLiteReferenceAdapterV1._evidence_append_lane_publication_v1(self._store, operation)
                    SQLiteReferenceAdapterV1.resolve_evidence_availability_v1(self._store, operation.publication_ref,
                        record_refs=operation.required_record_refs, purpose="EVIDENCE_LANE_REGISTRATION_V1",
                        current_grant=attempt_grant, clock=registration.issuer.clock)
                    from ...agents.pr169_agent_orch1_resolvers import AgentOrchService
                    AgentOrchService._finalize_evidence_lane_v1(registration.issuer.service, operation)
                    return operation
            except BaseException as original_error:
                trigger_original = EvidenceProcessSupervisorV1._retain_failure_trigger_v1(self._supervisor, operation.native, original_error)
                registration.active_lane_operation = None
                EvidenceProcessSupervisorV1._audit_failure_v1(self._supervisor, operation.native,
                    reason="INTEGRITY_FAILURE", original_error=original_error, trigger_original=trigger_original)
                raise
            finally:
                registration.active_lane_operation = None


def _main_v1():
    import sys
    _native_require(sys.argv[1:] == ["--worker-v1"], "LP03_WORKER_FIXED_ENTRY_ONLY")
    return _run_worker_v1(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(_main_v1())
