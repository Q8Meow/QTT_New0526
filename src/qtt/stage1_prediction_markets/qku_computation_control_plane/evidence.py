"""Canonical ST12-F lane, divergence, review, and evidence-bundle owner."""

from __future__ import annotations


def _require_evidence_probability_edge_lane_v1(lane):
    """Join all five original DATA spines to one retained native exchange."""
    from datetime import UTC, datetime, timedelta
    from .context import _native_require
    from .models import EvidenceDependencyExecutionRecordV1
    from .receipts import DurableComputationExecutionReceiptRecordV1
    from .input_resolver import EvidenceInvocationInputsV1, _require_evidence_probability_edge_result_v1
    from .implementation_registry import resolve_evidence_invocation_v1
    from .serialization import deterministic_json
    _native_require(lane.attempt.payload.component_closure == ("MATH-01","MATH-02")
        and len(lane.records.receipt_records) == 5 and lane.exchange[4] == dict(events=1,computations=2,segments=1),
        "LP03_EDGE_LANE_COMPLETE_ATOMIC_ROSTER")
    consumer, projection, segment, producer, dependency = (
        lane.records.receipt_records[0].typed_payload,lane.records.receipt_records[1].typed_payload.record,
        lane.records.receipt_records[2].typed_payload.record,lane.records.receipt_records[3].typed_payload,
        lane.records.receipt_records[4].typed_payload.record)
    _native_require(type(producer) is type(consumer) is DurableComputationExecutionReceiptRecordV1
        and type(dependency) is EvidenceDependencyExecutionRecordV1 and consumer is lane.raw
        and dependency.consumer_raw_receipt_ref == consumer.record_id
        and dependency.producer_raw_receipt_ref == producer.record_id
        and dependency.record_id == lane.attempt.grant_record.record_id + "::CONVERSION"
        and dependency.attempt_ref == lane.attempt.grant_record.record_id
        and dependency.lane is lane.attempt.request.lane
        and dependency.publication_ref is projection.publication_ref is lane.publication_ref
        and dependency.chain_artifact_json == lane.exchange[2]["chain_artifact_json"]
        and dependency.invocation_measurement == lane.exchange[2]["invocation_measurement"]
        and segment.aggregate_refs[-2:] == (producer.record_id,dependency.record_id),
        "LP03_EDGE_LANE_ORIGINAL_DEPENDENCY_JOIN")
    EvidenceDependencyExecutionRecordV1.__post_init__(dependency)
    attempt = lane.attempt
    contracts = tuple(resolve_evidence_invocation_v1(row[0],implementation_pin=row[1],specification_pin=row[2],
        resource_policy_ref=attempt.payload.protocol_ref,origin=attempt.grant_record.origin)
        for row in attempt.payload.component_and_callback_pins["components"])
    packets = attempt.invocations
    _native_require(lane.exchange[0] is packets[1] and lane.exchange[1] == contracts[1],
                    "LP03_EDGE_LANE_ORIGINAL_PENDING_PACKET")
    artifact = _require_evidence_probability_edge_result_v1(packets,attempt,contracts,lane.exchange[2],
        original_record_refs=lane.exchange[2]["original_record_refs"],frame_byte_limit=attempt.payload.budgets.frame_byte_limit)
    resolutions = tuple(EvidenceInvocationInputsV1._require_original_v1(packet,attempt) for packet in packets)
    terminal_ref = attempt.observation_appends[-1].body["observation_ref"]
    _native_require(producer.input_value_lineage_refs == resolutions[0].receipt_refs
        and consumer.input_value_lineage_refs == (*resolutions[1].receipt_refs,producer.record_id)
        and producer.dependency_receipt_refs == (attempt.grant_record.record_id,terminal_ref)
        and consumer.dependency_receipt_refs == (attempt.grant_record.record_id,terminal_ref,producer.record_id)
        and producer.execution_context_ref == consumer.execution_context_ref == dependency.execution_context_ref == resolutions[0].context_id
        and producer.input_snapshot_ref == consumer.input_snapshot_ref == attempt.registration.preparation.input_assembly_members[3].record_id,
        "LP03_EDGE_LANE_ORIGINAL_COMPONENT_LINEAGE")
    projected = lambda ns:datetime(1970,1,1,tzinfo=UTC)+timedelta(microseconds=ns//1000)
    for raw,contract,index,key,unit,basis in (
        (producer,contracts[0],0,"producer_output_json","probability","PAYOUT_NORMALIZED_CONTRACT_PRICE"),
        (consumer,contracts[1],2,"consumer_output_json","probability points","MODEL_MINUS_MARKET_SAME_SNAPSHOT")):
        measured = artifact["measured_original_stages"][index]["measurement"]
        _native_require(raw.existing_receipt.specification_id == contract.math_id
            and raw.existing_receipt.implementation_id == contract.raw_implementation_id
            and raw.existing_receipt.input_version == contract.raw_contract_version
            and raw.existing_receipt.output_json == artifact[key]
            and raw.started_at == projected(measured["started"][0]) and raw.completed_at == projected(measured["completed"][0])
            and raw.latency_ns == measured["duration_ns"] and raw.output_unit == unit and raw.output_basis == basis
            and raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
            "LP03_EDGE_LANE_ORIGINAL_COMPONENT_OUTPUT_AND_TIME")
    _native_require(deterministic_json(dependency.producer_invocation_contract) == deterministic_json(contracts[0])
        and deterministic_json(dependency.consumer_invocation_contract) == deterministic_json(contracts[1]),
        "LP03_EDGE_LANE_DEPENDENCY_CONTRACTS")
    return producer,dependency,artifact,contracts


def project_executed_metric_v1(*, operation):
    """Select the actual original value; this pending projection is not availability."""
    from .context import _native_require
    from .persistence import _EvidenceLaneOperationV1
    from .models import EvidenceValueProjectionRecordV1, EvidenceAbsenceV1, _LP03_MARKET_METRIC_PROFILES_V1, _LP03_SHARPE_PROJECTION_PROFILES_V1
    from .serialization import safe_json_loads
    _native_require(type(operation) is _EvidenceLaneOperationV1 and operation.phase == "BUILDING_RECORDS",
                    "LP03_PROJECTION_ORIGINAL_EXECUTION_REQUIRED")
    _EvidenceLaneOperationV1._assert_original_v1(operation)
    raw, contract = operation.raw, operation.exchange[1]
    _native_require(raw is not None and contract.math_id in ("MATH-06", "MATH-07", "MATH-02", "MATH-01", "MATH-03", "MATH-04", "MATH-05", "MATH-08", "MATH-09", "MATH-10", "MATH-11", "MATH-14", "MATH-15", "MATH-16", "MATH-17", "MATH-18", "MATH-19", "MATH-20", "MATH-21", "MATH-22", "MATH-23", "MATH-24", "MATH-25", "MATH-12", "MATH-13", "MATH-26", "MATH-27", "MATH-28", "MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52")
                    and raw.existing_receipt.output_json == operation.raw_original
                    and raw.existing_receipt.implementation_id == contract.raw_implementation_id,
                    "LP03_PROJECTION_ORIGINAL_RAW_JOIN")
    _native_require(raw.existing_receipt.output_json == operation.exchange[2]["raw_output_json"],
                    "LP03_PROJECTION_RAW_VALUE_CHANGED")
    held_out = contract.math_id in ("MATH-20", "MATH-21")
    recorded_dr = contract.math_id == "MATH-22"
    ope_point = contract.math_id in ("MATH-23", "MATH-24", "MATH-25")
    private_execution = contract.math_id in ("MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45")
    analytic = contract.math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37")
    quantum = contract.math_id in ("MATH-50", "MATH-51", "MATH-52")
    supplementary_refs = ()
    numerical_conversion_ref = EvidenceAbsenceV1("IDENTITY_NO_NUMERICAL_CONVERSION")
    output_unit, output_basis = raw.output_unit, raw.output_basis
    edge = contract.math_id == "MATH-02"
    brier = contract.math_id == "MATH-08"
    multiple = contract.math_id in ("MATH-12", "MATH-13")
    pbo = contract.math_id == "MATH-19"
    sharpe = contract.math_id in _LP03_SHARPE_PROJECTION_PROFILES_V1
    spa = contract.math_id == "MATH-16"
    reality = contract.math_id == "MATH-15"
    bootstrap = contract.math_id == "MATH-14"
    wilson = contract.math_id == "MATH-11"
    calibration = contract.math_id == "MATH-10"
    log_loss = contract.math_id == "MATH-09"
    research = contract.math_id == "MATH-26"
    kelly27 = contract.math_id == "MATH-27"
    kelly28 = contract.math_id == "MATH-28"
    cashflow = contract.math_id in ("MATH-06","MATH-07")
    market = contract.math_id in _LP03_MARKET_METRIC_PROFILES_V1
    if edge:
        from .specification import decode_evidence_raw_output_v1
        value = decode_evidence_raw_output_v1("MATH-02",raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536,maximum_nodes=4096)
    elif cashflow:
        from .specification import decode_evidence_raw_output_v1
        decode_evidence_raw_output_v1(contract.math_id,raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536,maximum_nodes=4096)
        value=safe_json_loads(raw.existing_receipt.output_json)["expected_net_cash"]
    elif multiple:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_multiple_testing_value_v1
        decoded = decode_evidence_raw_output_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        rejected = set(decoded["rejected_original_indices"])
        value = _evidence_multiple_testing_value_v1(dict(rows=[dict(original_index=index, adjusted_p=p, rejected=index in rejected)
            for index, p in enumerate(decoded["adjusted_p_values"])], correction=decoded["correction"], largest_rank=decoded["largest_rank"]),
            math_id=contract.math_id)
    elif quantum:
        rule = EVIDENCE_PROJECTION_CONTRACTS_V1[contract.math_id]
        receipt = _EvidenceLaneOperationV1._require_original_quantum_constructor_v1(operation)
        value = safe_json_loads(deterministic_json(receipt))
        field, metric = rule.original_field, rule.output_name
        if contract.math_id in ("MATH-50", "MATH-51"):
            supplementary_refs = (operation.unit_of_work_id + "::QUANTUM_TRACE",)
    elif private_execution:
        rule = EVIDENCE_PROJECTION_CONTRACTS_V1[contract.math_id]
        data = project_evidence_raw_data_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_raw_bytes=65536, maximum_raw_nodes=4096, maximum_projection_bytes=65536, maximum_projection_nodes=4096,
            output_unit=output_unit, output_basis=output_basis)
        value = safe_json_loads(data.projection_data_json.decode("utf-8"))["projected_value"][rule.output_name]
        field, metric = rule.original_field, rule.output_name
    elif analytic:
        from .models import EvidenceAnalyticBinary64ConversionRecordV1
        from .serialization import _native_strict_json

        projection = EVIDENCE_PROJECTION_CONTRACTS_V1[contract.math_id]
        conversion = operation.analytic_conversion_record
        _native_require(type(conversion) is EvidenceAnalyticBinary64ConversionRecordV1
            and conversion.original_raw_receipt_ref == raw.record_id
            and conversion.output_field == projection.original_field
            and (conversion.output_unit, conversion.measurement_basis) == (output_unit, output_basis),
            "LP03_ANALYTIC_PROJECTION_ORIGINAL_CONVERSION")
        original_wire = _native_strict_json(operation.raw_original.encode("utf-8"), max_bytes=65536, max_nodes=4096)
        decimal_text = original_wire if projection.original_field == "$" else original_wire[projection.original_field]
        _native_require(decimal_text == conversion.original_decimal_text, "LP03_ANALYTIC_PROJECTION_EXACT_RAW_TEXT")
        encoded = conversion.certificate_json_or_absence
        value = (_native_strict_json(encoded.encode("utf-8"), max_bytes=65536, max_nodes=128, binary64_numbers=True)["analytic_value"]
            if type(encoded) is str else EvidenceAbsenceV1("NUMERICAL_CONVERSION_UNAVAILABLE"))
        field, metric = projection.original_field, projection.output_name
        numerical_conversion_ref = conversion.record_id
    elif ope_point:
        from .models import _LP03_OPE_POINT_PROJECTION_PROFILES_V1, _evidence_recorded_ope_point_projection_v1
        from .specification import decode_evidence_raw_output_v1

        field, metric, output_basis, _ = _LP03_OPE_POINT_PROJECTION_PROFILES_V1[contract.math_id]
        raw_result = decode_evidence_raw_output_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = _evidence_recorded_ope_point_projection_v1(contract.math_id, raw_result if field == "$" else raw_result[field])
    elif recorded_dr:
        from .specification import decode_evidence_raw_output_v1

        profile = operation.attempt.registration.protocol.numeric_profile
        raw_result = decode_evidence_raw_output_v1("MATH-22",raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536,maximum_nodes=4096)
        uncertainty = operation.recorded_dr_records[-1]
        _native_require(uncertainty.original_estimator_ref == raw.record_id, "LP03_DR_ORIGINAL_UNCERTAINTY_LINK")
        value = dict(estimate=raw_result["doubly_robust_estimate"], raw_result_ref=raw.record_id,
            uncertainty_ref=uncertainty.record_id, uncertainty_target=uncertainty.target)
        supplementary_refs = tuple(row.record_id for row in operation.recorded_dr_records)
        output_unit,output_basis=profile["output_unit"],profile["target"]
    elif held_out:
        from .models import _evidence_heldout_projection_value_v1
        from .specification import decode_evidence_raw_output_v1

        profile = operation.attempt.registration.protocol.numeric_profile
        originals, folds, paths = operation.heldout_score_records
        topology = decode_evidence_raw_output_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        is_fold = contract.math_id == "MATH-20"
        topology_key, metric = ("folds", "split_indices") if is_fold else ("paths", "cpcv_paths")
        score_key = "fold_score_refs" if is_fold else "path_score_refs"
        value = _evidence_heldout_projection_value_v1(dict(
            topology=topology[topology_key], topology_receipt_ref=raw.record_id,
            coverage_disposition="COMPLETE_ORIGINAL_HELD_OUT_SCORES",
            **{score_key: tuple(row.record_id for row in (folds if is_fold else paths))}), contract.math_id)
        supplementary_refs = tuple(row.record_id for row in (*folds, *paths))
        output_unit, output_basis = profile["output_unit"], profile["measurement_basis"]
    elif pbo:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_cscv_result_v1
        value = _evidence_cscv_result_v1(decode_evidence_raw_output_v1("MATH-19",
            raw.existing_receipt.output_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096))
    elif sharpe:
        from .specification import decode_evidence_raw_output_v1
        metric, field, _, _ = _LP03_SHARPE_PROJECTION_PROFILES_V1[contract.math_id]
        decoded = decode_evidence_raw_output_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = decoded[field]
    elif spa:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_spa_value_v1
        decoded = decode_evidence_raw_output_v1("MATH-16", raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = _evidence_spa_value_v1(dict(decoded))
    elif reality:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_reality_check_value_v1
        decoded = decode_evidence_raw_output_v1("MATH-15", raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = _evidence_reality_check_value_v1(dict(decoded))
    elif bootstrap:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_bootstrap_value_v1
        decoded = decode_evidence_raw_output_v1("MATH-14", raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = _evidence_bootstrap_value_v1(dict(decoded))
    elif wilson:
        from .specification import decode_evidence_raw_output_v1
        decoded = decode_evidence_raw_output_v1("MATH-11", raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = (decoded["lower"], decoded["upper"])
    elif brier or log_loss or calibration:
        from .specification import decode_evidence_raw_output_v1
        decoded = decode_evidence_raw_output_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = decoded["expected_calibration_error" if calibration else "mean_log_loss" if log_loss else "mean_brier_score"]
    elif contract.math_id == "MATH-05" or kelly27:
        from .specification import decode_evidence_raw_output_v1
        decoded = decode_evidence_raw_output_v1(contract.math_id, raw.existing_receipt.output_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)
        value = safe_json_loads(raw.existing_receipt.output_json)["raw_fraction" if kelly27 else "relative_spread_ratio"]
    else:
        value = safe_json_loads(raw.existing_receipt.output_json)
        _native_require(type(value) is str, "LP03_PROJECTION_RAW_VALUE_CHANGED")
    return EvidenceValueProjectionRecordV1(**operation.header,
        record_id=operation.unit_of_work_id + "::PROJECTION", original_raw_receipt_ref=raw.record_id,
        original_raw_schema_ref=contract.raw_output_schema_ref, original_implementation_ref=contract.raw_implementation_id,
        measured_run_ref=operation.attempt.grant_record.record_id, lane=operation.attempt.request.lane,
        attempt_ref=operation.attempt.grant_record.record_id,
        field_selections=(("expected_net_cash","expected_net_cash"),) if cashflow else (("$","edge"),) if edge else (("raw_fraction", "full_kelly_fraction"),) if kelly27 else
            ((_LP03_MARKET_METRIC_PROFILES_V1[contract.math_id][1], _LP03_MARKET_METRIC_PROFILES_V1[contract.math_id][0]),) if market else
            (("doubly_robust_estimate", "dr_value_and_uncertainty"),) if recorded_dr else ((field, metric),) if ope_point or analytic or private_execution or quantum else ((topology_key, metric),) if held_out else (("$", "rejections_and_adjusted_p"),) if multiple else (("[probability_of_backtest_overfitting,S,split_count,logits,splits]", "pbo_receipt"),) if pbo else ((field, metric),) if sharpe else (("[statistic,p_value,reject,candidate_means,long_run_variances,consistent_valid_columns,simulated_statistics,recenter_variant]", "spa_receipt"),) if spa else (("[statistic,p_value,reject,candidate_means,simulated_statistics,recenter_policy]", "reality_check_receipt"),) if reality else (("[sample_mean,lower,upper,bootstrap_distribution,seed,replicates,expected_block_length,interval_method]", "bootstrap_distribution_and_interval"),) if bootstrap else (("[lower,upper]", "interval"),) if wilson else (("expected_calibration_error", "ece"),) if calibration else (("mean_log_loss", "log_loss"),) if log_loss else (("mean_brier_score", "brier_score"),) if brier else (("$", "bounded_fraction" if kelly28 else "evi" if research else "mid"),),
        evidence_projection_schema_ref=("LP03::" + contract.math_id + "::PROJECTION_V1" if cashflow or edge or market or kelly27 or kelly28 or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or analytic or private_execution or quantum or multiple else "LP03::MATH-08::PROJECTION_V1" if brier else
            "LP03::MATH-26::PROJECTION_V1" if research else "QTT_LP03_MATH_03_MID_PROJECTION_V1_5"),
        projected_value=value,
        output_unit=output_unit, output_basis=output_basis,
        numerical_conversion_ref_or_absence=numerical_conversion_ref,
        supplementary_measurement_refs=supplementary_refs, publication_ref=operation.publication_ref)

def register_measured_lane_v1(*, operation, terminal_record):
    """Construct only the selected original result; CONTROL owns its atomic append."""
    from .context import _native_require
    from .persistence import _EvidenceLaneOperationV1, EvidenceAvailabilityHandleV1
    from .models import EvidenceLaneRegistrationRecordV1
    from .lifecycle import EvidenceAttemptStateV1
    from .cohort_compiler import ReplayPaperCohortCompilerV1
    _native_require(type(operation) is _EvidenceLaneOperationV1 and operation.finalization_phase == "BUILDING",
                    "LP03_LANE_REGISTRATION_ORIGINAL_OPERATION")
    attempt, registration = operation.attempt, operation.attempt.registration
    math_id = operation.exchange[1].math_id
    edge = attempt.payload.component_closure == ("MATH-01","MATH-02")
    metric_id = {"MATH-02":"CONFORMANCE::MATH-02::edge", "MATH-03": "CONFORMANCE::MATH-03::mid", "MATH-08": "CONFORMANCE::MATH-08::brier_score", "MATH-09": "CONFORMANCE::MATH-09::log_loss", "MATH-10": "CONFORMANCE::MATH-10::ece", "MATH-11": "CONFORMANCE::MATH-11::interval", "MATH-14": "CONFORMANCE::MATH-14::bootstrap_distribution_and_interval", "MATH-15": "CONFORMANCE::MATH-15::reality_check_receipt", "MATH-16": "CONFORMANCE::MATH-16::spa_receipt",
                 "MATH-19": "CONFORMANCE::MATH-19::pbo_receipt",
                  "MATH-20": "CONFORMANCE::MATH-20::split_indices",
                  "MATH-21": "CONFORMANCE::MATH-21::cpcv_paths",
                  "MATH-22": "CONFORMANCE::MATH-22::dr_value_and_uncertainty",
                  "MATH-23": "CONFORMANCE::MATH-23::ips_value",
                  "MATH-24": "CONFORMANCE::MATH-24::snips_value",
                  "MATH-25": "CONFORMANCE::MATH-25::switch_value_and_selected_tau",
                 "MATH-17": "CONFORMANCE::MATH-17::psr", "MATH-18": "CONFORMANCE::MATH-18::dsr",
                 "MATH-12": "CONFORMANCE::MATH-12::rejections_and_adjusted_p", "MATH-13": "CONFORMANCE::MATH-13::rejections_and_adjusted_p",
                 "MATH-26": "CONFORMANCE::MATH-26::evi", "MATH-01": "CONFORMANCE::MATH-01::p_market",
                 "MATH-04": "CONFORMANCE::MATH-04::spread", "MATH-05": "CONFORMANCE::MATH-05::relative_spread",
                 "MATH-27": "CONFORMANCE::MATH-27::full_kelly_fraction",
                 "MATH-28": "CONFORMANCE::MATH-28::bounded_fraction",
                 "MATH-06": "CONFORMANCE::MATH-06::expected_net_cash",
                 "MATH-07": "CONFORMANCE::MATH-07::expected_net_cash"}.get(math_id)
    incomplete_reasons = ()
    if math_id in ("MATH-50", "MATH-51", "MATH-52"):
        expected_calls = 1
        rule = EVIDENCE_PROJECTION_CONTRACTS_V1[math_id]
        metric_id = f"CONFORMANCE::{math_id}::{rule.output_name}"
    elif math_id in ("MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45"):
        expected_calls = 1
        rule = EVIDENCE_PROJECTION_CONTRACTS_V1[math_id]
        metric_id = f"CONFORMANCE::{math_id}::{rule.output_name}"
    elif math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37"):
        from .models import EvidenceAnalyticBinary64ConversionRecordV1, EvidenceAbsenceV1

        expected_calls = 1
        conversion = operation.analytic_conversion_record
        projection = EVIDENCE_PROJECTION_CONTRACTS_V1[math_id]
        metric_id = f"CONFORMANCE::{math_id}::{projection.output_name}"
        _native_require(type(conversion) is EvidenceAnalyticBinary64ConversionRecordV1,
            "LP03_ANALYTIC_LANE_CONVERSION_RECORD_UNAVAILABLE")
        if type(conversion.certificate_json_or_absence) is EvidenceAbsenceV1:
            incomplete_reasons = ("NUMERICAL_CONVERSION_UNAVAILABLE",)
    elif math_id == "MATH-22":
        expected_calls = 2
        _native_require(type(operation.recorded_dr_records) is tuple and 1 <= len(operation.recorded_dr_records) <= 2,
            "LP03_DR_LANE_UNCERTAINTY_RECORD_UNAVAILABLE")
        uncertainty = operation.recorded_dr_records[-1]
        if uncertainty.availability_disposition == "UNCERTAINTY_UNAVAILABLE":
            incomplete_reasons = ("UNCERTAINTY_UNAVAILABLE",)
    elif math_id in ("MATH-20", "MATH-21"):
        from .evidence_execution import _heldout_computation_count_v1
        expected_calls = _heldout_computation_count_v1(math_id, operation.exchange[0]._resolution.authoritative_values)
        _native_require(operation.heldout_score_records is not None
            and len(operation.heldout_score_records[0]) == expected_calls - 1, "LP03_LANE_HELD_OUT_INCOMPLETE")
    else:
        expected_calls = 2 if edge else 1
    from .evidence_execution import _evidence_lane_completion_v1
    _native_require(terminal_record is operation.final_state and terminal_record.state is EvidenceAttemptStateV1.COLLECTION_COMPLETE
                    and metric_id is not None and registration.binding_record.required_metric_ids == (metric_id,)
                    and registration.binding_record.component_closure == (("MATH-01","MATH-02") if edge else (math_id,))
                    and _evidence_lane_completion_v1(attempt.payload, operation.exchange[4], expected_calls),
                    "LP03_LANE_SELECTED_COLLECTION_REQUIRED")
    if edge:
        _require_evidence_probability_edge_lane_v1(operation)
    slot = ReplayPaperCohortCompilerV1.resolve_evidence_expected_slot_v1(registration.compiler, operation=operation, math_id=math_id)
    _native_require(slot.input_lock_id == attempt.payload.input_lock_ref and slot.cohort_template_id == math_id
                    and slot.lane == attempt.request.lane.value, "LP03_LANE_ORIGINAL_SLOT")
    observed = EvidenceAvailabilityHandleV1._require_current_v1(operation.availability, operation=operation,
        purpose="EVIDENCE_LANE_REGISTRATION_V1", current_grant=attempt.handle, clock=operation.issuer.clock)
    common = dict(operation.header)
    common.update(producing_owner="AGENT_ORCH1", producing_principal=operation.issuer.host.public_configuration.service_principal,
        created_wall_ns=observed[0], causation_ref=terminal_record.record_id)
    return EvidenceLaneRegistrationRecordV1(**common, record_id=attempt.grant_record.record_id + "::LANE_REGISTRATION",
        lane=attempt.request.lane, attempt_ref=attempt.grant_record.record_id, terminal_receipt_ref=terminal_record.record_id,
        original_result_ref=operation.records.result_record_ref, original_store_id=operation.publication_ref.store_id,
        result_slot=slot.expected_result_contract_id,
        common_plan_refs=(attempt.payload.input_assembly_ref.record_id, registration.records[0].record_id,
                          registration.records[1].record_id, attempt.payload.scenario_plan_ref.record_id, attempt.payload.protocol_ref),
        accepted_publication_ref=operation.publication_ref, all_metric_projection_refs=(operation.records.result_record_ref,), incomplete_reasons=incomplete_reasons)


def _build_ready_conformance_v1(*, operation, observed):
    """Compare the selected measured closure with its independently preregistered literal."""
    from .context import _native_require
    from .errors import ContractValidationError, ReasonCode
    from .models import EvidencePipelineConformanceV1, EvidenceAbsenceV1, EvidenceRecordHeaderV1, _LP03_MARKET_METRIC_PROFILES_V1, _LP03_SHARPE_PROJECTION_PROFILES_V1
    from .models import _LP03_ORIGINAL_PRIVATE_BINARY64_EXECUTION_IDS_V1
    from .persistence import _EvidenceConformanceOperationV1
    _native_require(type(operation) is _EvidenceConformanceOperationV1 and operation.phase == "PARENTS_READBACK",
                    "LP03_CONFORMANCE_ORIGINAL_READBACK_REQUIRED")
    registration = operation.registration
    bound, protocol = registration.binding_record, registration.protocol
    policy, claim = registration.registration_policy
    comparator = policy["comparator_plan"]
    edge = bound.component_closure == ("MATH-01","MATH-02")
    brier = bound.component_closure == ("MATH-08",)
    multiple = bound.component_closure in (("MATH-12",), ("MATH-13",))
    pbo = bound.component_closure == ("MATH-19",)
    held_out = bound.component_closure in (("MATH-20",), ("MATH-21",))
    recorded_dr = bound.component_closure == ("MATH-22",)
    ope_point = bound.component_closure in (("MATH-23",), ("MATH-24",), ("MATH-25",))
    if ope_point:
        from .models import _LP03_OPE_POINT_PROJECTION_PROFILES_V1
        point_field, point_metric, point_basis, point_implementation = _LP03_OPE_POINT_PROJECTION_PROFILES_V1[bound.component_closure[0]]
    if held_out:
        from .parameter_policy import _LP03_HELDOUT_ANALYSIS_PROFILE_V1, _LP03_HELDOUT_PROTOCOL_METRICS_V1
    sharpe = bound.component_closure in (("MATH-17",), ("MATH-18",))
    spa = bound.component_closure == ("MATH-16",)
    reality = bound.component_closure == ("MATH-15",)
    bootstrap = bound.component_closure == ("MATH-14",)
    wilson = bound.component_closure == ("MATH-11",)
    calibration = bound.component_closure == ("MATH-10",)
    log_loss = bound.component_closure == ("MATH-09",)
    research = bound.component_closure == ("MATH-26",)
    kelly27 = bound.component_closure == ("MATH-27",)
    kelly28 = bound.component_closure == ("MATH-28",)
    kelly = kelly27 or kelly28
    math_id = bound.component_closure[-1] if edge else bound.component_closure[0]
    cashflow = math_id in ("MATH-06","MATH-07")
    market = math_id in _LP03_MARKET_METRIC_PROFILES_V1
    private_execution = math_id in ("MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45")
    analytic = math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37")
    binary64_execution = math_id in _LP03_ORIGINAL_PRIVATE_BINARY64_EXECUTION_IDS_V1
    quantum = math_id in ("MATH-50", "MATH-51", "MATH-52")
    private_values = analytic or private_execution or quantum
    if private_values:
        analytic_rule = EVIDENCE_PROJECTION_CONTRACTS_V1[math_id]
        analytic_metric = f"CONFORMANCE::{math_id}::{analytic_rule.output_name}"
    if sharpe:
        sharpe_metric, sharpe_field, sharpe_implementation, sharpe_basis = _LP03_SHARPE_PROJECTION_PROFILES_V1[math_id]
    metric_id = ("CONFORMANCE::MATH-22::dr_value_and_uncertainty" if recorded_dr else f"CONFORMANCE::{math_id}::{point_metric}" if ope_point else analytic_metric if private_values else _LP03_HELDOUT_PROTOCOL_METRICS_V1[math_id][0] if held_out else "CONFORMANCE::"+math_id+"::expected_net_cash" if cashflow else "CONFORMANCE::MATH-02::edge" if edge else "CONFORMANCE::MATH-28::bounded_fraction" if kelly28 else
        "CONFORMANCE::MATH-27::full_kelly_fraction" if kelly27 else
        "CONFORMANCE::" + math_id + "::" + _LP03_MARKET_METRIC_PROFILES_V1[math_id][0] if market else
        "CONFORMANCE::MATH-26::evi" if research else "CONFORMANCE::" + math_id + "::rejections_and_adjusted_p" if multiple else "CONFORMANCE::MATH-19::pbo_receipt" if pbo else f"CONFORMANCE::{math_id}::{sharpe_metric}" if sharpe else "CONFORMANCE::MATH-16::spa_receipt" if spa else "CONFORMANCE::MATH-15::reality_check_receipt" if reality else "CONFORMANCE::MATH-14::bootstrap_distribution_and_interval" if bootstrap else "CONFORMANCE::MATH-11::interval" if wilson else "CONFORMANCE::MATH-10::ece" if calibration else "CONFORMANCE::MATH-09::log_loss" if log_loss else "CONFORMANCE::MATH-08::brier_score" if brier else "CONFORMANCE::MATH-03::mid")
    if edge:
        from .specification import decode_evidence_raw_output_v1
        expected_json = comparator["expected_raw_record_json"]
        expected = decode_evidence_raw_output_v1("MATH-02",expected_json.encode("ascii"),maximum_bytes=128,maximum_nodes=4)
    elif cashflow:
        from .serialization import _native_strict_json
        expected_json=comparator["expected_raw_record_json"]
        expected=_native_strict_json(expected_json.encode("utf-8"),max_bytes=65536,max_nodes=4096)["expected_net_cash"]
    elif kelly27:
        texts = comparator["expected_raw_texts"]
        expected_json = deterministic_json(dict(raw_fraction=texts[0], sizing_candidate=texts[1]))
        expected = texts[0]
    elif kelly28:
        texts = comparator["expected_raw_texts"]
        expected_json, expected = deterministic_json(texts[0]), texts[0]
    elif market:
        texts = comparator["expected_raw_texts"]
        expected_json = deterministic_json(dict(relative_spread_ratio=texts[0], relative_spread_bps=texts[1]) if math_id == "MATH-05" else texts[0])
        expected = texts[0]
    elif multiple:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_multiple_testing_value_v1
        expected_json = comparator["expected_raw_record_json"]
        expected_raw = decode_evidence_raw_output_v1(math_id, expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        rejected = set(expected_raw["rejected_original_indices"])
        expected = _evidence_multiple_testing_value_v1(dict(rows=[dict(original_index=index, adjusted_p=p, rejected=index in rejected)
            for index,p in enumerate(expected_raw["adjusted_p_values"])], correction=expected_raw["correction"],largest_rank=expected_raw["largest_rank"]),math_id=math_id)
        _native_require(comparator["comparison"] == "ORDERED_BINARY64_MULTIPLE_TESTING_IDENTITY", "LP03_CONFORMANCE_INDEPENDENT_EXPECTATION_MISMATCH")
    elif quantum:
        from .specification import decode_evidence_raw_output_v1

        expected_json = comparator["expected_raw_record_json"]
        expected = decode_evidence_raw_output_v1(math_id, expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        _native_require(deterministic_json(expected) == expected_json, "LP03_QUANTUM_CONFORMANCE_PREREGISTERED_RAW")
    elif private_execution:
        expected_json = comparator["expected_raw_record_json"]
        data = project_evidence_raw_data_v1(math_id, expected_json.encode("utf-8"),
            maximum_raw_bytes=65536, maximum_raw_nodes=4096, maximum_projection_bytes=65536, maximum_projection_nodes=4096,
            output_unit=protocol.numeric_profile["output_unit"], output_basis=protocol.numeric_profile["output_basis"])
        expected = safe_json_loads(data.projection_data_json.decode("utf-8"))["projected_value"][analytic_rule.output_name]
    elif analytic:
        from math import isfinite
        import struct

        expected_json = comparator["expected_raw_record_json"]
        expected = struct.unpack(">d", bytes.fromhex(comparator["expected_analytic_binary64_bits"]))[0]
        _native_require(isfinite(expected), "LP03_ANALYTIC_CONFORMANCE_EXPECTED_BINARY64")
    elif ope_point:
        from .specification import decode_evidence_raw_output_v1

        expected_json = comparator["expected_raw_record_json"]
        result = decode_evidence_raw_output_v1(math_id, expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        expected = result if point_field == "$" else result[point_field]
    elif recorded_dr:
        from .specification import decode_evidence_raw_output_v1

        expected_json = comparator["expected_raw_record_json"]
        raw_expectation = decode_evidence_raw_output_v1("MATH-22",expected_json.encode("utf-8"),maximum_bytes=65536,maximum_nodes=4096)
        expected = raw_expectation["doubly_robust_estimate"]
        if any(lane.lane_registration.incomplete_reasons == ("UNCERTAINTY_UNAVAILABLE",)
                for lane in operation.lanes):
            raise ContractValidationError(ReasonCode.EVIDENCE_METRIC_INCOMPLETE,
                "LP03_DR_UNCERTAINTY_UNAVAILABLE")
        _native_require(comparator["expected_uncertainty_disposition"] == "ORIGINAL_CONDITIONAL_RECORDED_SCORE_INTERVAL",
            "LP03_DR_UNCERTAINTY_UNAVAILABLE")
    elif held_out:
        from .specification import decode_evidence_raw_output_v1
        expected_json = comparator["expected_raw_record_json"]
        topology_key = "folds" if math_id == "MATH-20" else "paths"
        expected = decode_evidence_raw_output_v1(math_id, expected_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)[topology_key]
    elif pbo:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_cscv_result_v1
        expected_json = comparator["expected_raw_record_json"]
        expected = _evidence_cscv_result_v1(decode_evidence_raw_output_v1("MATH-19", expected_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096))
    elif sharpe:
        from .specification import decode_evidence_raw_output_v1
        expected_json = comparator["expected_raw_record_json"]
        expected = decode_evidence_raw_output_v1(math_id, expected_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)[sharpe_field]
    elif spa:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_spa_value_v1
        expected_json = comparator["expected_raw_record_json"]
        expected_raw = decode_evidence_raw_output_v1("MATH-16", expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        expected = _evidence_spa_value_v1(dict(expected_raw))
    elif reality:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_reality_check_value_v1
        expected_json = comparator["expected_raw_record_json"]
        expected_raw = decode_evidence_raw_output_v1("MATH-15", expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        expected = _evidence_reality_check_value_v1(dict(expected_raw))
    elif bootstrap:
        from .specification import decode_evidence_raw_output_v1
        from .models import _evidence_bootstrap_value_v1
        expected_json = comparator["expected_raw_record_json"]
        expected_raw = decode_evidence_raw_output_v1("MATH-14", expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        expected = _evidence_bootstrap_value_v1(dict(expected_raw))
    elif wilson:
        from .specification import decode_evidence_raw_output_v1
        expected_json = comparator["expected_raw_record_json"]
        expected_raw = decode_evidence_raw_output_v1("MATH-11", expected_json.encode("utf-8"), maximum_bytes=65536, maximum_nodes=4096)
        expected = (expected_raw["lower"], expected_raw["upper"])
    elif brier or log_loss or calibration:
        from .specification import decode_evidence_raw_output_v1
        expected_json = comparator["expected_raw_record_json"]
        expected = decode_evidence_raw_output_v1(math_id, expected_json.encode("utf-8"),
            maximum_bytes=65536, maximum_nodes=4096)["expected_calibration_error" if calibration else "mean_log_loss" if log_loss else "mean_brier_score"]
    else:
        expected = comparator["expected_raw_value"]
        expected_json = deterministic_json(expected)
    _native_require(bound.component_closure == (("MATH-01","MATH-02") if edge else (math_id,)) and bound.required_metric_ids == (metric_id,)
                    and protocol.analysis_profile == ("DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1" if recorded_dr else "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1" if ope_point else "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1" if analytic else "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1" if binary64_execution else "DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1" if private_execution else "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1" if quantum else _LP03_HELDOUT_ANALYSIS_PROFILE_V1 if held_out else "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1" if cashflow else "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1" if edge else
                        "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1" if kelly else
                        "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1" if market else
                        "DETERMINISTIC_EXACT_DECIMAL_EVI_CONFORMANCE_V1" if research else
                        "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1" if multiple else "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1" if pbo else "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1" if sharpe else "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_SPA_CONFORMANCE_V1" if spa else "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_CONFORMANCE_V1" if reality else "DETERMINISTIC_ORDERED_STATIONARY_BOOTSTRAP_CONFORMANCE_V1" if bootstrap else "DETERMINISTIC_AS241_BINARY64_WILSON_CONFORMANCE_V1" if wilson else "DETERMINISTIC_EXACT_BINARY64_CALIBRATION_CONFORMANCE_V1" if calibration else "DETERMINISTIC_CERTIFIED_BINARY64_LOG_LOSS_CONFORMANCE_V1" if log_loss else
                        "DETERMINISTIC_EXACT_BINARY64_BRIER_CONFORMANCE_V1" if brier else
                        "DETERMINISTIC_RAW_IDENTITY_CONFORMANCE_V1")
                    and comparator["comparison"] == ("EXACT_ORIGINAL_DR_AND_CONDITIONAL_SCORE_INTERVAL" if recorded_dr else "EXACT_ORIGINAL_RECORDED_OPE_POINT_IDENTITY" if ope_point else "EXACT_ORIGINAL_DECIMAL_AND_CERTIFIED_STATISTICAL_CONVERSION" if analytic else "EXACT_ORIGINAL_PRIVATE_EXECUTION_BINARY64_IDENTITY" if binary64_execution else "EXACT_ORIGINAL_PRIVATE_EXECUTION_DECIMAL_IDENTITY" if private_execution else "EXACT_ORIGINAL_QUANTUM_RAW_AND_CONSTRUCTOR_IDENTITY" if quantum else "EXACT_ORIGINAL_TOPOLOGY_AND_COMPLETE_HELD_OUT_SCORE_IDENTITY" if held_out else "EXACT_ORDERED_DECIMAL_SIGNED_TOTAL_CASHFLOW_IDENTITY" if cashflow else "EXACT_MARKET_REGISTERED_CONVERSION_BINARY64_EDGE_IDENTITY" if edge else
                        "EXACT_ORDERED_DECIMAL_KELLY_IDENTITY" if kelly else
                        "EXACT_ORDERED_DECIMAL_MARKET_IDENTITY" if market else "EXACT_ORDERED_DECIMAL_EVI_IDENTITY" if research else
                        "ORDERED_BINARY64_MULTIPLE_TESTING_IDENTITY" if multiple else "ORDERED_BINARY64_CSCV_COMPLETE_RAW_IDENTITY" if pbo else "ORDERED_BINARY64_SHARPE_COMPLETE_RAW_IDENTITY" if sharpe else "ORDERED_COMPLETE_FAMILY_SPA_RECORD_IDENTITY" if spa else "ORDERED_COMPLETE_FAMILY_REALITY_CHECK_RECORD_IDENTITY" if reality else "ORDERED_STATIONARY_BOOTSTRAP_RECORD_IDENTITY" if bootstrap else "ORDERED_AS241_WILSON_ENDPOINT_IDENTITY" if wilson else "EXACT_BINARY64_CALIBRATION_IDENTITY" if calibration else "CERTIFIED_BINARY64_LOG_LOSS_IDENTITY" if log_loss else "EXACT_BINARY64_BRIER_IDENTITY" if brier else "ANALYTIC_IDENTITY")
                    and claim.metric_id == metric_id
                    and claim.comparator_ref == comparator["expectation_owner_ref" if cashflow or edge or brier or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or private_values or multiple or research or market or kelly else "baseline_ref"],
                    "LP03_CONFORMANCE_SELECTED_INDEPENDENT_PLAN")
    measurements = []
    if private_execution or quantum:
        from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
        private_implementation = _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1[math_id].implementation_id
    for lane, expected_lane in zip(operation.lanes, ("REPLAY", "PAPER")):
        raw, records = lane.raw, lane.records
        projection, segment = tuple(row.typed_payload.record for row in records.receipt_records[1:3])
        expected_calls = 2 if edge else 1
        if held_out:
            originals, folds, paths = lane.heldout_score_records
            expected_calls = 1 + len(folds)
            _native_require(len(records.receipt_records) == 3 + len(originals) + len(folds) + len(paths)
                and tuple(row.existing_receipt.output_json for row in originals) == comparator["expected_fold_raw_json"]
                and all(raw_score.existing_receipt.output_json == fold.original_scorer_raw_json
                    and fold.scorer_raw_receipt_ref == raw_score.record_id
                    and fold.topology_raw_ref == raw.record_id for fold, raw_score in zip(folds, originals, strict=True))
                and projection.supplementary_measurement_refs == tuple(row.record_id for row in (*folds, *paths)),
                "LP03_CONFORMANCE_HELD_OUT_ROSTER")
        if recorded_dr:
            original_rows = lane.recorded_dr_records
            _native_require(type(original_rows) is tuple and len(original_rows) == 2 and len(records.receipt_records) == 5,
                "LP03_DR_UNCERTAINTY_UNAVAILABLE")
            groups,uncertainty=original_rows
            _native_require(uncertainty.original_estimator_ref == raw.record_id
                and groups.record_id == uncertainty.group_measurement_ref
                and projection.supplementary_measurement_refs == (groups.record_id,uncertainty.record_id)
                and projection.projected_value["uncertainty_ref"] == uncertainty.record_id
                and uncertainty.availability_disposition == "ORIGINAL_CONDITIONAL_RECORDED_SCORE_INTERVAL",
                "LP03_DR_CONFORMANCE_ORIGINAL_UNCERTAINTY")
            expected_calls = 2
        if edge:
            producer,dependency,_artifact,_contracts = _require_evidence_probability_edge_lane_v1(lane)
            _native_require(producer.existing_receipt.output_json == protocol.numeric_profile["producer_expected_raw_json"]
                == comparator["producer_expected_raw_json"],"LP03_EDGE_CONFORMANCE_PREREGISTERED_PRODUCER")
        elif analytic:
            conversion = lane.analytic_conversion_record
            _native_require(conversion is not None and len(records.receipt_records) == 4
                and conversion.original_raw_receipt_ref == raw.record_id
                and conversion.record_id == projection.numerical_conversion_ref_or_absence
                and segment.aggregate_refs[4:] == (conversion.record_id,),
                "LP03_ANALYTIC_CONFORMANCE_ORIGINAL_RECEIPT_ROSTER")
            if (type(conversion.certificate_json_or_absence) is EvidenceAbsenceV1
                    and lane.lane_registration.incomplete_reasons == ("NUMERICAL_CONVERSION_UNAVAILABLE",)):
                raise ContractValidationError(ReasonCode.EVIDENCE_METRIC_INCOMPLETE,
                    "LP03_NUMERICAL_CONVERSION_UNAVAILABLE")
            _native_require(type(conversion.certificate_json_or_absence) is str
                and lane.lane_registration.incomplete_reasons == (), "LP03_NUMERICAL_CONVERSION_UNAVAILABLE")
        elif quantum:
            from .persistence import _EvidenceLaneOperationV1

            constructor = _EvidenceLaneOperationV1._require_original_quantum_constructor_v1(lane)
            is_trace = math_id in ("MATH-50", "MATH-51")
            _native_require(len(records.receipt_records) == (4 if is_trace else 3)
                and (not is_trace or records.receipt_records[3].typed_payload.reconstruct(QuantumTraceValidationReceiptV1) == constructor)
                and deterministic_json(projection.projected_value) == deterministic_json(constructor)
                == lane.exchange[2]["quantum_constructor_receipt_json"],
                "LP03_QUANTUM_CONFORMANCE_ORIGINAL_TYPED_RECEIPT")
        elif not held_out and not recorded_dr:
            _native_require(len(records.receipt_records) == 3,"LP03_CONFORMANCE_ORIGINAL_RECEIPT_ROSTER")
        _native_require(lane.attempt.request.lane.value == expected_lane
                        and raw.existing_receipt.output_json == expected_json
                        and (quantum or deterministic_json(projection.projected_value["estimate"] if recorded_dr else projection.projected_value["topology"] if held_out else projection.projected_value) == deterministic_json(expected))
                        and projection.original_raw_receipt_ref == raw.record_id
                        and projection.original_implementation_ref == raw.existing_receipt.implementation_id == (
                            "qku/economic_math.py::" + math_id + "::ST12C-CURRENTIZED-1.0" if research or kelly or analytic else private_implementation if private_execution or quantum else "MATH-22::1.1.0" if recorded_dr else point_implementation if ope_point else math_id + "::2.0.0" if held_out else "MATH-19::2.0.0" if pbo else sharpe_implementation if sharpe else "MATH-16::2.0.0" if spa else "MATH-15::2.0.0" if reality else "MATH-14::2.0.0" if bootstrap else "MATH-10::2.0.0" if calibration else math_id + ("::2.0.0" if cashflow else "::1.1R1"))
                        and projection.output_unit == (protocol.numeric_profile["output_unit"] if held_out else raw.output_unit) and projection.output_unit == (protocol.numeric_profile["output_unit"] if cashflow or edge or market or kelly or held_out or recorded_dr or ope_point or private_values else protocol.numeric_profile["utility_unit"] if research else
                            "mixed; member-specific" if reality or spa or pbo else "statistic_unit" if bootstrap else "probability" if sharpe or multiple or calibration or wilson else "nats/sample" if log_loss else "squared probability error" if brier else "USD/CONTRACT")
                        and projection.output_basis == (protocol.numeric_profile["measurement_basis"] if held_out else protocol.numeric_profile["target"] if recorded_dr else raw.output_basis) and projection.output_basis == (protocol.numeric_profile["target"] if recorded_dr else point_basis if ope_point else analytic_rule.basis_requirement if private_values else protocol.numeric_profile["measurement_basis"] if cashflow or edge or market or kelly or held_out else "EXPECTED_VALUE_OF_INFORMATION_PER_DECISION" if research else
                            "adjusted_p_and_rejection_mask" if multiple else "probability_of_backtest_overfitting" if pbo else sharpe_basis if sharpe else "studentized_loss_differential_spa_p_value" if spa else "benchmark_candidate_loss_differential_p_value" if reality else "bootstrap_statistic_distribution_and_interval" if bootstrap else "lower_upper_probability_interval" if wilson else "absolute_calibration_gap" if calibration else "per_sample_natural_log_loss" if log_loss else "PER_SAMPLE_SQUARED_PROBABILITY" if brier else
                            "SAME_INSTRUMENT_SAME_SNAPSHOT_BEST_BID_ASK_MIDPOINT")
                        and projection.attempt_ref == lane.attempt.grant_record.record_id
                        and projection.publication_ref is lane.publication_ref
                        and lane.lane_registration.original_result_ref == projection.record_id
                        and not lane.lane_registration.incomplete_reasons,
                        "LP03_CONFORMANCE_INDEPENDENT_EXPECTATION_MISMATCH")
        from .evidence_execution import _evidence_lane_completion_v1
        complete = lane.exchange[4]
        _native_require(segment.count == complete["events"] and segment.first_event_ordinal == 0
                        and segment.last_event_ordinal == segment.count - 1
                        and len(segment.exact_ordered_events) == segment.count and not segment.gap_dispositions
                        and _evidence_lane_completion_v1(lane.attempt.payload, complete, expected_calls),
                        "LP03_CONFORMANCE_COMPLETE_EVENT_AND_PLAN_REQUIRED")
        plan_refs = lane.lane_registration.common_plan_refs
        _native_require(len(plan_refs) == 5, "LP03_CONFORMANCE_COMPLETE_EVENT_AND_PLAN_REQUIRED")
        assembly_ref, task_ref, family_ref, scenario_ref, protocol_ref = plan_refs
        _native_require((assembly_ref, task_ref, family_ref, protocol_ref) ==
            (registration.request.input_assembly_ref.record_id, registration.records[0].record_id,
             registration.records[1].record_id, bound.protocol_ref), "LP03_CONFORMANCE_COMPLETE_EVENT_AND_PLAN_REQUIRED")
        if scenario_ref != bound.scenario_plan_ref:
            raise ContractValidationError(ReasonCode.EVIDENCE_SCENARIO_MISMATCH,
                "LP03_CONFORMANCE_COMPLETE_EVENT_AND_PLAN_REQUIRED")
        snapshot = registration.preparation.input_assembly_members[2]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baseline_rows = tuple(item for part in lane.exchange[0]._source_slices for item in part.reconstructed_canonical_events
                              if item["record_ref"] == baseline_ref)
        _native_require(len(baseline_rows) == 1, "LP03_CONFORMANCE_ORIGINAL_BASELINE_REQUIRED")
        baseline = baseline_rows[0]["values"]["baseline"]
        _native_require((cashflow or edge or brier or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or private_values or multiple or research or market or kelly or comparator["baseline_ref"] == baseline_ref)
                        and records.journal_transaction.transaction_class == "SYNTHETIC_OPENING_BALANCE"
                        and raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT"
                        and len(records.journal_postings) == 2
                        and tuple((post.entry_side.value, post.amount_text, post.currency_or_asset, post.basis)
                                  for post in records.journal_postings) == (
                            ("DEBIT", str(baseline["cash"]), baseline["currency"], "SYNTHETIC_OPENING_BALANCE"),
                            ("CREDIT", str(baseline["cash"]), baseline["currency"], "SYNTHETIC_OPENING_BALANCE")),
                        "LP03_CONFORMANCE_ORIGINAL_ACCOUNTING_JOIN")
        measurement = dict(lane=expected_lane, attempt_ref=lane.attempt.grant_record.record_id,
            raw_ref=raw.record_id, projection_ref=projection.record_id, unit=projection.output_unit, basis=projection.output_basis,
            event_segment_ref=segment.record_id, journal_ref=records.journal_transaction.journal_transaction_id)
        if cashflow or edge or brier or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or held_out or recorded_dr or ope_point or private_values or multiple or market:
            measurement.update(actual_raw_record_json=raw.existing_receipt.output_json, expected_raw_record_json=expected_json,
                               projected_value_json=deterministic_json(projection.projected_value))
        else:
            measurement.update(actual_value=projection.projected_value, expected_value=expected)
        if analytic:
            measurement.update(numerical_conversion_ref=lane.analytic_conversion_record.record_id,
                original_analytic_binary64_bits=comparator["expected_analytic_binary64_bits"])
        if held_out:
            measurement.update(scorer_raw_refs=tuple(row.record_id for row in originals),
                fold_score_refs=tuple(row.record_id for row in folds), path_score_refs=tuple(row.record_id for row in paths))
        if edge:
            measurement.update(producer_raw_ref=producer.record_id,dependency_execution_ref=dependency.record_id,
                actual_producer_raw_json=producer.existing_receipt.output_json,
                expected_producer_raw_json=comparator["producer_expected_raw_json"])
        measurements.append(measurement)
    first, second = operation.lanes
    _native_require(first.exchange[1].owner_bindings == second.exchange[1].owner_bindings,
                    "LP03_CONFORMANCE_BINDING_CLOSURE_MISMATCH")
    exercised = first.exchange[1].owner_bindings
    if edge:
        first_contracts = _require_evidence_probability_edge_lane_v1(first)[3]
        second_contracts = _require_evidence_probability_edge_lane_v1(second)[3]
        exercised = tuple(binding for contract in first_contracts for binding in contract.owner_bindings)
        _native_require(exercised == tuple(binding for contract in second_contracts for binding in contract.owner_bindings)
            and len(set(exercised)) == len(exercised),"LP03_EDGE_CONFORMANCE_COMPLETE_BINDING_CLOSURE")
    record_id = bound.record_id + "::CONFORMANCE:R0"
    comparison_ref = bound.record_id + "::CONFORMANCE:COMPARISON"
    header = {member.name: getattr(bound, member.name) for member in fields(EvidenceRecordHeaderV1) if member.name != "kind"}
    header.update(record_id=record_id, causation_ref=bound.record_id, created_wall_ns=observed[0],
        producing_owner="QKU_COMPUTATION_CONTROL_PLANE",
        producing_principal=operation.service._measured_original[1].public_configuration.service_principal,
        source_lineage_refs=(first.lane_registration.record_id, second.lane_registration.record_id, claim.record_id))
    result = EvidencePipelineConformanceV1(**header, replay_attempt_ref=first.attempt.grant_record.record_id,
        paper_attempt_ref=second.attempt.grant_record.record_id, replay_registration_ref=first.lane_registration.record_id,
        paper_registration_ref=second.lane_registration.record_id, comparison_ref=comparison_ref,
        exercised_binding_ids=exercised, expected_unavailable_binding_ids=(),
        observed_unavailable_dispositions=(), independent_conformance_review_ref=EvidenceAbsenceV1("INDEPENDENT_REVIEW_PENDING"),
        receiver_ack_refs=EvidenceAbsenceV1("RECEIVER_ACKNOWLEDGEMENTS_PENDING"), terminal_state="READY_FOR_REVIEW")
    return result, dict(operation="LP03_SELECTED_CONFORMANCE_COMPARISON_V1", claim_ref=claim.record_id,
        protocol_ref=protocol.parameter_protocol_ref, independent_method=("PREREGISTERED_ORIGINAL_DR_AND_CONDITIONAL_SCORE_INTERVAL" if recorded_dr else "PREREGISTERED_ORIGINAL_RECORDED_OPE_POINT_ESTIMATOR" if ope_point else "PREREGISTERED_ORIGINAL_EXACT_DECIMAL_WITH_CERTIFIED_ANALYTIC_PROJECTION" if analytic else "PREREGISTERED_EXACT_ORIGINAL_PRIVATE_EXECUTION_VALUE" if private_execution else "PREREGISTERED_ORIGINAL_QUANTUM_RAW_AND_CONSTRUCTOR_IDENTITY" if quantum else "PREREGISTERED_ORIGINAL_TOPOLOGY_AND_HELD_OUT_SCORE_IDENTITY" if held_out else "PREREGISTERED_EXACT_ORDERED_DECIMAL_SIGNED_TOTAL_CASHFLOW_IDENTITY" if cashflow else "PREREGISTERED_MARKET_CONVERSION_PROBABILITY_EDGE_IDENTITY" if edge else
            "PREREGISTERED_EXACT_ORDERED_DECIMAL_MARKET_IDENTITY" if market else
            "PREREGISTERED_EXACT_ORDERED_DECIMAL_EVI_IDENTITY" if research else
            "PREREGISTERED_ORDERED_BINARY64_MULTIPLE_TESTING_IDENTITY" if multiple else "PREREGISTERED_ORDERED_BINARY64_CSCV_MODEL_IDENTITY" if pbo else "PREREGISTERED_ORDERED_BINARY64_SHARPE_MODEL_IDENTITY" if sharpe else "PREREGISTERED_ORDERED_COMPLETE_FAMILY_SPA_MODEL_IDENTITY" if spa else "PREREGISTERED_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_MODEL_IDENTITY" if reality else "PREREGISTERED_ORDERED_STATIONARY_BOOTSTRAP_MODEL_IDENTITY" if bootstrap else "PREREGISTERED_AS241_WILSON_ENDPOINT_MODEL_IDENTITY" if wilson else "PREREGISTERED_EXACT_BINARY64_CALIBRATION_IDENTITY" if calibration else "PREREGISTERED_CERTIFIED_BINARY64_LOG_LOSS_IDENTITY" if log_loss else "PREREGISTERED_EXACT_BINARY64_BRIER_IDENTITY" if brier else
            "PREREGISTERED_ANALYTIC_IDENTITY"),
        independent_plan=comparator, actual_measurements=tuple(measurements),
        original_parent_readbacks=operation.parent_readbacks, constructed_at=observed,
        outcome="BOTH_ORIGINAL_LANES_MATCH_INDEPENDENT_EXPECTATION", conformance_ref=record_id)


from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
import math
from threading import Lock
from types import MappingProxyType
from typing import Mapping, Protocol

from .agent_policy import (
    AgentCapabilityDecisionV1,
)
from .context import ComputationContextKeyV1, exact_decimal, parse_utc
from .dependency_graph import FROZEN_DEPENDENCY_RELATIONSHIPS
from .errors import (
    AuthorityDeniedError,
    ContractValidationError,
    IdempotencyContractError,
    PersistenceContractError,
    ReasonCode,
)
from .idempotency import (
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    IdempotencyOutcomeV1,
    canonical_request_json_v1,
)
from .input_lock import ImmutableReplayPaperInputLockV1, ST12F_TEMPLATE_IDS_V1
from .lifecycle import StateTransitionReceiptV1, TransitionDispositionV1
from .llm_gateway import (
    CanonicalNumericEvidenceValueV1,
    DeterministicEvidenceAnnotationContractV1,
)
from .model_risk import ModelRiskControlStateV1, ModelRiskEvidenceAssessmentV1
from .models import (
    BuildEvidenceBundleRequestV1,
    ComputationExecutionReceiptV1,
    FrozenFormulaOutputV1,
    NO_EFFECTS_V1,
    RegisterReplayPaperResultRequestV1,
    StackResultV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
    TypedValueKindV1,
    TypedValueRecordV1,
)
from .parameter_policy import initialize_st12f_parameter_registry_v1
from .persistence import PersistenceAdapterV1, PersistenceAvailabilityV1
from .protocols import IndependentReviewAuthorityResolverProtocolV1
from .quantum_benchmark import (
    QuantumClassicalNoTradeComparisonV1,
    QuantumTraceValidationReceiptV1,
)
from .receipts import (
    DurableComputationExecutionReceiptRecordV1,
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    ST12FEvidenceControlReceiptRecordV1,
    ST12FReceiptClassV1,
)
from .serialization import deterministic_json, safe_json_loads
from .economic_math import TRANCHE_C_MATH_SPECIFICATIONS
from .implementation_registry import (
    CURRENT_IMPLEMENTATION_REGISTRY,
    TRANCHE_C_IMPLEMENTATION_REGISTRY,
)
from .specification import CURRENT_FORMULA_REQUIREMENTS
from .stack_resolver import REGISTERED_FORMULA_STACKS


LANE_RESULT_SCHEMA_VERSION_V1 = "QTT_ST12F_LANE_RESULT_CONTRACTS_V1_4"
LANE_RESULT_CONTRACT_VERSION_V1 = "1.4"
DIVERGENCE_SCHEMA_VERSION_V1 = "QTT_ST12F_DIVERGENCE_ASSESSMENT_V1_4"
EVIDENCE_BUNDLE_SCHEMA_VERSION_V1 = "QTT_ST12F_COMPUTATION_EVIDENCE_BUNDLE_V1_4"
EVIDENCE_BUNDLE_CONTRACT_VERSION_V1 = "1.4"
ST12F_EVIDENCE_IDENTITIES_V1 = tuple(
    f"MATH-{number:02d}" for number in (*range(1, 46), 50, 51, 52)
)
ST12F_STATIC_NOT_APPLICABLE_MATH_IDS_V1 = (
    "MATH-01",
    "MATH-02",
    "MATH-03",
    "MATH-04",
    "MATH-05",
    "MATH-06",
    "MATH-07",
    "MATH-34",
    "MATH-35",
    "MATH-36",
)


def _required_evidence_identity_closure_v1(
    component_or_template_ref: str,
) -> tuple[str, ...]:
    """Return the selected component's exact ordered transitive upstream closure."""

    required = {component_or_template_ref}
    changed = True
    while changed:
        changed = False
        for relationship in FROZEN_DEPENDENCY_RELATIONSHIPS.values():
            if (
                relationship.consumer_math_spec_id in required
                and relationship.producer_math_spec_id not in required
            ):
                required.add(relationship.producer_math_spec_id)
                changed = True
    return tuple(
        identity
        for identity in ST12F_EVIDENCE_IDENTITIES_V1
        if identity in required
    )


@dataclass(frozen=True, slots=True)
class StaticEvidenceApplicabilityProofV1:
    """Deterministic proof that one non-metric math identity is out of scope."""

    proof_id: str
    math_spec_id: str
    component_or_template_ref: str
    input_lock_id: str
    formula_requirement_ref: str
    implementation_registry_ref: str
    dependency_graph_ref: str
    reason: str

    def __post_init__(self) -> None:
        for name in (
            "proof_id",
            "math_spec_id",
            "component_or_template_ref",
            "input_lock_id",
            "formula_requirement_ref",
            "implementation_registry_ref",
            "dependency_graph_ref",
            "reason",
        ):
            _text(getattr(self, name), name)
        expected_id = (
            "ST12F-STATIC-NOT-APPLICABLE::"
            f"{self.math_spec_id}::{self.component_or_template_ref}::"
            f"{self.input_lock_id}"
        )
        required_closure = _required_evidence_identity_closure_v1(
            self.component_or_template_ref
        )
        if (
            self.math_spec_id not in ST12F_STATIC_NOT_APPLICABLE_MATH_IDS_V1
            or self.math_spec_id in required_closure
            or self.proof_id != expected_id
            or not (
                self.math_spec_id in CURRENT_FORMULA_REQUIREMENTS
                or self.math_spec_id in TRANCHE_C_MATH_SPECIFICATIONS
            )
            or not (
                self.math_spec_id in CURRENT_IMPLEMENTATION_REGISTRY
                or self.math_spec_id in TRANCHE_C_IMPLEMENTATION_REGISTRY
            )
            or self.formula_requirement_ref
            != f"CURRENT_FORMULA_REQUIREMENTS::{self.math_spec_id}"
            or self.implementation_registry_ref
            != f"CURRENT_IMPLEMENTATION_REGISTRY::{self.math_spec_id}"
            or self.dependency_graph_ref
            != (
                "FROZEN_DEPENDENCY_RELATIONSHIPS::"
                f"{self.component_or_template_ref}::"
                "TRANSITIVE_UPSTREAM_CLOSURE"
            )
            or self.reason != "NOT_REQUIRED_BY_COMPONENT_DEPENDENCY_GRAPH"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "static applicability proof differs from the dependency-closed allowlist",
            )

    @classmethod
    def for_scope(
        cls,
        *,
        math_spec_id: str,
        component_or_template_ref: str,
        input_lock_id: str,
    ) -> "StaticEvidenceApplicabilityProofV1":
        return cls(
            proof_id=(
                "ST12F-STATIC-NOT-APPLICABLE::"
                f"{math_spec_id}::{component_or_template_ref}::{input_lock_id}"
            ),
            math_spec_id=math_spec_id,
            component_or_template_ref=component_or_template_ref,
            input_lock_id=input_lock_id,
            formula_requirement_ref=(
                f"CURRENT_FORMULA_REQUIREMENTS::{math_spec_id}"
            ),
            implementation_registry_ref=(
                f"CURRENT_IMPLEMENTATION_REGISTRY::{math_spec_id}"
            ),
            dependency_graph_ref=(
                "FROZEN_DEPENDENCY_RELATIONSHIPS::"
                f"{component_or_template_ref}::TRANSITIVE_UPSTREAM_CLOSURE"
            ),
            reason="NOT_REQUIRED_BY_COMPONENT_DEPENDENCY_GRAPH",
        )


@dataclass(frozen=True, slots=True)
class EvidenceMetricDefinitionV1:
    metric_id: str
    name: str
    family: str
    direction: str
    math_spec_ref: str
    canonical_owner: str
    actual_value_required: bool
    pass_label_substitution_allowed: bool
    fixture_may_be_empirical_evidence: bool

    def __post_init__(self) -> None:
        if any(
            not isinstance(getattr(self, name), str)
            or not getattr(self, name)
            or getattr(self, name) != getattr(self, name).strip()
            for name in ("metric_id", "name", "family", "direction", "math_spec_ref", "canonical_owner")
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "metric definition identities must be canonical text",
            )
        if (
            self.actual_value_required is not True
            or self.pass_label_substitution_allowed is not False
            or self.fixture_may_be_empirical_evidence is not False
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "metric definitions require values and forbid label/fixture substitution",
            )


ST12F_EVIDENCE_METRIC_DEFINITIONS_V1 = (
    EvidenceMetricDefinitionV1("ST12F-METRIC::001", "BrierScore", "CALIBRATION", "LOWER_IS_BETTER", "MATH-08", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::002", "LogLoss", "CALIBRATION", "LOWER_IS_BETTER", "MATH-09", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::003", "ExpectedCalibrationError", "CALIBRATION", "LOWER_IS_BETTER", "MATH-10", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::004", "WilsonInterval", "UNCERTAINTY", "INTERVAL", "MATH-11", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::005", "BenjaminiHochberg", "FDR", "CONTROL", "MATH-12", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::006", "BenjaminiYekutieli", "FDR", "CONTROL", "MATH-13", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::007", "StationaryBootstrap", "DEPENDENCE", "INTERVAL", "MATH-14", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::008", "WhiteRealityCheck", "DATA_SNOOPING", "TEST", "MATH-15", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::009", "HansenSPA", "DATA_SNOOPING", "TEST", "MATH-16", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::010", "ProbabilisticSharpeRatio", "RISK_ADJUSTED", "HIGHER_IS_BETTER", "MATH-17", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::011", "DeflatedSharpeRatio", "MULTIPLE_TESTING", "HIGHER_IS_BETTER", "MATH-18", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::012", "ProbabilityOfBacktestOverfitting", "OVERFIT", "LOWER_IS_BETTER", "MATH-19", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::013", "PurgedKFold", "LEAKAGE", "CONTROL", "MATH-20", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::014", "CombinatorialPurgedCV", "LEAKAGE", "CONTROL", "MATH-21", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::015", "DoublyRobustOPE", "OPE", "ESTIMATE", "MATH-22", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::016", "IPS", "OPE", "ESTIMATE", "MATH-23", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::017", "SNIPS", "OPE", "ESTIMATE", "MATH-24", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::018", "SWITCHOPE", "OPE", "ESTIMATE", "MATH-25", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::019", "ExpectedValueOfInformation", "RESEARCH_ALLOCATION", "HIGHER_IS_BETTER", "MATH-26", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::020", "Kelly", "SIZING", "BOUNDED", "MATH-27", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::021", "FractionalKelly", "SIZING", "BOUNDED", "MATH-28", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::022", "MeanVariance", "PORTFOLIO", "OPTIMIZE", "MATH-29", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::023", "CVaR", "TAIL_RISK", "LOWER_IS_BETTER", "MATH-30", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::024", "HistoricalES", "TAIL_RISK", "LOWER_IS_BETTER", "MATH-31", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::025", "ImplementationShortfall", "TCA", "LOWER_IS_BETTER", "MATH-32", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::026", "SpreadCost", "TCA", "LOWER_IS_BETTER", "MATH-33", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::027", "FillProbability", "FILL", "HIGHER_IS_BETTER", "MATH-37", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::028", "PartialFill", "FILL", "ESTIMATE", "MATH-38", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::029", "QueueEstimate", "QUEUE", "ESTIMATE", "MATH-39", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::030", "AdverseSelection", "TCA", "LOWER_IS_BETTER", "MATH-40", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::031", "LatencyDecay", "LATENCY", "HIGHER_REMAINING_EDGE_IS_BETTER", "MATH-41", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::032", "SquareRootImpact", "IMPACT", "LOWER_IS_BETTER", "MATH-42", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::033", "CapacityCrowding", "CAPACITY", "LOWER_IS_BETTER", "MATH-43", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::034", "CovarianceShrinkage", "PORTFOLIO", "PSD_REQUIRED", "MATH-44", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::035", "LCBNoTradeGate", "NO_TRADE", "STRICTLY_POSITIVE_TO_TRADE", "MATH-45", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::036", "QAOATraceValidation", "QUANTUM_TRACE", "VALIDATION_ONLY", "MATH-50", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::037", "VQETraceValidation", "QUANTUM_TRACE", "VALIDATION_ONLY", "MATH-51", "ComputationEvidenceServiceV1", True, False, False),
    EvidenceMetricDefinitionV1("ST12F-METRIC::038", "QuantumClassicalUtility", "QUANTUM_BENCHMARK", "SAME_BASIS_ONLY", "MATH-52", "ComputationEvidenceServiceV1", True, False, False),
)


@dataclass(frozen=True, slots=True)
class EvidenceOutputBindingV1:
    math_spec_id: str
    output_name: str
    output_type: str
    output_unit: str
    metric_id: str
    static_not_applicable_allowed: bool


ST12F_EVIDENCE_OUTPUT_BINDINGS_V1 = (
    EvidenceOutputBindingV1("MATH-01", "p_market", "Decimal", "probability", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-02", "edge_probability", "float64", "probability points", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-03", "mid", "Decimal", "currency/contract", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-04", "spread", "Decimal", "currency/contract", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-05", "relative_spread", "Decimal", "fraction", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-06", "expected_net_cash", "Decimal", "currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-07", "expected_net_cash", "Decimal", "currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-08", "brier_score", "float64", "squared probability", "ST12F-METRIC::001", False),
    EvidenceOutputBindingV1("MATH-09", "log_loss", "float64", "nats/sample", "ST12F-METRIC::002", False),
    EvidenceOutputBindingV1("MATH-10", "ece", "float64", "probability", "ST12F-METRIC::003", False),
    EvidenceOutputBindingV1("MATH-11", "interval", "[float64,float64]", "probability", "ST12F-METRIC::004", False),
    EvidenceOutputBindingV1("MATH-12", "rejections_and_adjusted_p", "typed vector", "probability", "ST12F-METRIC::005", False),
    EvidenceOutputBindingV1("MATH-13", "rejections_and_adjusted_p", "typed vector", "probability", "ST12F-METRIC::006", False),
    EvidenceOutputBindingV1("MATH-14", "bootstrap_distribution_and_interval", "typed record", "statistic unit", "ST12F-METRIC::007", False),
    EvidenceOutputBindingV1("MATH-15", "reality_check_receipt", "typed statistical result", "p-value", "ST12F-METRIC::008", False),
    EvidenceOutputBindingV1("MATH-16", "spa_receipt", "typed statistical result", "p-value", "ST12F-METRIC::009", False),
    EvidenceOutputBindingV1("MATH-17", "psr", "float64", "probability", "ST12F-METRIC::010", False),
    EvidenceOutputBindingV1("MATH-18", "dsr", "float64", "probability", "ST12F-METRIC::011", False),
    EvidenceOutputBindingV1("MATH-19", "pbo_receipt", "typed result", "probability", "ST12F-METRIC::012", False),
    EvidenceOutputBindingV1("MATH-20", "split_indices", "typed fold registry", "indices", "ST12F-METRIC::013", False),
    EvidenceOutputBindingV1("MATH-21", "cpcv_paths", "typed path registry", "indices", "ST12F-METRIC::014", False),
    EvidenceOutputBindingV1("MATH-22", "dr_value_and_uncertainty", "typed result", "reward", "ST12F-METRIC::015", False),
    EvidenceOutputBindingV1("MATH-23", "ips_value", "float64", "reward", "ST12F-METRIC::016", False),
    EvidenceOutputBindingV1("MATH-24", "snips_value", "float64", "reward", "ST12F-METRIC::017", False),
    EvidenceOutputBindingV1("MATH-25", "switch_value_and_selected_tau", "typed result", "reward", "ST12F-METRIC::018", False),
    EvidenceOutputBindingV1("MATH-26", "evi", "Decimal", "same utility basis", "ST12F-METRIC::019", False),
    EvidenceOutputBindingV1("MATH-27", "full_kelly_fraction", "Decimal", "fraction of approved risk capital", "ST12F-METRIC::020", False),
    EvidenceOutputBindingV1("MATH-28", "bounded_fraction", "Decimal", "fraction of approved risk capital", "ST12F-METRIC::021", False),
    EvidenceOutputBindingV1("MATH-29", "utility", "float64", "return-equivalent utility", "ST12F-METRIC::022", False),
    EvidenceOutputBindingV1("MATH-30", "cvar", "float64", "loss", "ST12F-METRIC::023", False),
    EvidenceOutputBindingV1("MATH-31", "expected_shortfall", "float64", "loss", "ST12F-METRIC::024", False),
    EvidenceOutputBindingV1("MATH-32", "implementation_shortfall", "Decimal", "currency", "ST12F-METRIC::025", False),
    EvidenceOutputBindingV1("MATH-33", "spread_cost", "Decimal", "currency", "ST12F-METRIC::026", False),
    EvidenceOutputBindingV1("MATH-34", "fee", "Decimal", "settlement currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-35", "signed_fee_or_rebate", "Decimal", "USD", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-36", "derived_yes_and_no_touches", "typed Decimal record", "currency", "EXPLICIT_ABSENCE", True),
    EvidenceOutputBindingV1("MATH-37", "fill_probability", "float64", "probability", "ST12F-METRIC::027", False),
    EvidenceOutputBindingV1("MATH-38", "expected_fill_quantity", "Decimal", "units", "ST12F-METRIC::028", False),
    EvidenceOutputBindingV1("MATH-39", "queue_ahead_estimate", "Decimal", "units", "ST12F-METRIC::029", False),
    EvidenceOutputBindingV1("MATH-40", "adverse_selection_cost", "Decimal", "currency", "ST12F-METRIC::030", False),
    EvidenceOutputBindingV1("MATH-41", "decayed_edge", "float64", "same edge", "ST12F-METRIC::031", False),
    EvidenceOutputBindingV1("MATH-42", "impact_fraction", "float64", "fraction of price", "ST12F-METRIC::032", False),
    EvidenceOutputBindingV1("MATH-43", "capacity_penalty", "float64", "utility", "ST12F-METRIC::033", False),
    EvidenceOutputBindingV1("MATH-44", "shrunk_covariance", "float64 matrix", "return covariance", "ST12F-METRIC::034", False),
    EvidenceOutputBindingV1("MATH-45", "gate_decision", "enum and LCB value", "declared", "ST12F-METRIC::035", False),
    EvidenceOutputBindingV1("MATH-50", "recomputed_objective", "typed quantum validation", "declared trace and economic bases", "ST12F-METRIC::036", False),
    EvidenceOutputBindingV1("MATH-51", "recomputed_objective", "typed quantum validation", "declared trace and economic bases", "ST12F-METRIC::037", False),
    EvidenceOutputBindingV1("MATH-52", "benchmark_delta_packet", "typed multi-metric record", "declared metrics", "ST12F-METRIC::038", False),
)

_EVIDENCE_OUTPUT_BINDING_BY_MATH_ID_V1 = MappingProxyType(
    {row.math_spec_id: row for row in ST12F_EVIDENCE_OUTPUT_BINDINGS_V1}
)

ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1: Mapping[str, str] = MappingProxyType(
    {
        "MATH-08": "per_sample_squared_probability",
        "MATH-09": "per_sample_natural_log_loss",
        "MATH-10": "absolute_calibration_gap",
        "MATH-11": "lower_upper_probability_interval",
        "MATH-12": "adjusted_p_and_rejection_mask",
        "MATH-13": "adjusted_p_and_rejection_mask",
        "MATH-14": "bootstrap_statistic_distribution_and_interval",
        "MATH-15": "benchmark_candidate_loss_differential_p_value",
        "MATH-16": "superior_predictive_ability_p_value",
        "MATH-17": "probability_sharpe_exceeds_benchmark",
        "MATH-18": "multiple_testing_adjusted_sharpe_probability",
        "MATH-19": "probability_of_backtest_overfitting",
        "MATH-20": "purged_fold_score_distribution",
        "MATH-21": "combinatorial_purged_path_score_distribution",
        "MATH-22": "off_policy_value_same_reward_basis",
        "MATH-23": "importance_weighted_policy_value",
        "MATH-24": "self_normalized_importance_policy_value",
        "MATH-25": "switch_estimator_policy_value",
        "MATH-26": "expected_value_of_information_per_decision",
        "MATH-27": "wealth_fraction",
        "MATH-28": "bounded_fractional_wealth_fraction",
        "MATH-29": "portfolio_weight_vector_and_objective",
        "MATH-30": "tail_loss_at_declared_alpha",
        "MATH-31": "historical_expected_shortfall_at_declared_alpha",
        "MATH-32": "arrival_to_execution_total_shortfall",
        "MATH-33": "quoted_spread_cost",
        "MATH-37": "fill_probability_on_declared_horizon",
        "MATH-38": "filled_fraction_of_requested_quantity",
        "MATH-39": "queue_position_or_ahead_quantity",
        "MATH-40": "post_fill_adverse_price_move_cost",
        "MATH-41": "remaining_edge_fraction_at_latency",
        "MATH-42": "square_root_impact_cost",
        "MATH-43": "capacity_crowding_penalty_or_limit",
        "MATH-44": "shrunk_covariance_matrix",
        "MATH-45": "execution_adjusted_lower_confidence_bound",
        "MATH-50": "trace_recomputed_objective_validation",
        "MATH-51": "trace_recomputed_objective_and_variance_validation",
        "MATH-52": "same_basis_quantum_classical_no_trade_comparison",
    }
)


@dataclass(frozen=True, slots=True)
class EvidenceProjectionContractV1:
    """Protocol 1.5 data semantics, not evidence of an original producer.

    Unit and basis requirements describe what the original operation must
    establish. They are not default currency, payout, horizon or source values.
    """

    math_spec_id: str
    schema_id: str
    output_name: str
    selection: str
    original_field: str
    unit_requirement: str
    basis_requirement: str
    direction_rule: str


_LP03_PROJECTION_ROWS_V1 = (
    (1, "p_market", "ROOT", "$", "original payout-normalized probability", "PAYOUT_NORMALIZED_PROBABILITY", "ORIGINAL_CLAIM_REQUIRED"),
    (2, "edge_probability", "ROOT", "$", "original probability points", "MODEL_MINUS_MARKET_PROBABILITY", "ORIGINAL_CLAIM_REQUIRED"),
    (3, "mid", "ROOT", "$", "original currency per contract", "ORIGINAL_SNAPSHOT_MIDPOINT", "ORIGINAL_CLAIM_REQUIRED"),
    (4, "spread", "ROOT", "$", "original currency per contract", "FULL_ASK_MINUS_BID", "ORIGINAL_CLAIM_REQUIRED"),
    (5, "relative_spread", "FIELD", "relative_spread_ratio", "original dimensionless ratio", "RELATIVE_SPREAD_RATIO", "ORIGINAL_CLAIM_REQUIRED"),
    (6, "expected_net_cash", "FIELD", "expected_net_cash", "original cashflow currency", "SIGNED_TOTAL_EXPECTED_NET_CASH", "ORIGINAL_CLAIM_REQUIRED"),
    (7, "expected_net_cash", "FIELD", "expected_net_cash", "original cashflow currency", "SIGNED_TOTAL_EXPECTED_NET_CASH", "ORIGINAL_CLAIM_REQUIRED"),
    (8, "brier_score", "FIELD", "mean_brier_score", "original squared probability", "PER_SAMPLE_SQUARED_PROBABILITY", "LOWER_IS_BETTER"),
    (9, "log_loss", "FIELD", "mean_log_loss", "original nats per sample", "PER_SAMPLE_NATURAL_LOG_LOSS", "LOWER_IS_BETTER"),
    (10, "ece", "FIELD", "expected_calibration_error", "original probability", "ABSOLUTE_CALIBRATION_GAP", "LOWER_IS_BETTER"),
    (11, "interval", "INTERVAL", "lower,upper", "original probability", "LOWER_UPPER_PROBABILITY_INTERVAL", "INTERVAL"),
    (12, "rejections_and_adjusted_p", "INDEXED", "adjusted_p_values,rejected_original_indices,correction,largest_rank", "original probability", "ORIGINAL_INDEXED_BH_ADJUSTED_P_AND_REJECTIONS", "CONTROL"),
    (13, "rejections_and_adjusted_p", "INDEXED", "adjusted_p_values,rejected_original_indices,correction,largest_rank", "original probability", "ORIGINAL_INDEXED_BY_ADJUSTED_P_AND_REJECTIONS", "CONTROL"),
    (14, "bootstrap_distribution_and_interval", "ROOT", "$", "original statistic unit", "ORIGINAL_STATIONARY_BOOTSTRAP_DISTRIBUTION_AND_INTERVAL", "INTERVAL"),
    (15, "reality_check_receipt", "ROOT", "$", "original p-value and loss-differential units", "ORIGINAL_CANDIDATE_FAMILY_REALITY_CHECK", "TEST"),
    (16, "spa_receipt", "ROOT", "$", "original p-value and loss-differential units", "ORIGINAL_STUDENTIZED_SPA_AND_RECENTERING", "TEST"),
    (17, "psr", "FIELD", "probabilistic_sharpe_ratio", "original probability", "PROBABILITY_SHARPE_EXCEEDS_BENCHMARK", "HIGHER_IS_BETTER"),
    (18, "dsr", "FIELD", "deflated_sharpe_ratio", "original probability", "MULTIPLE_TESTING_ADJUSTED_SHARPE_PROBABILITY", "HIGHER_IS_BETTER"),
    (19, "pbo_receipt", "ROOT", "$", "original probability and split diagnostics", "ORIGINAL_BACKTEST_OVERFITTING_SPLITS_AND_LOGITS", "LOWER_IS_BETTER"),
    (20, "split_indices", "FOLD_PRODUCER", "folds", "original preregistered scorer unit", "PURGED_FOLD_SCORE_DISTRIBUTION", "CONTROL"),
    (21, "cpcv_paths", "FOLD_PRODUCER", "paths", "original preregistered scorer unit", "COMBINATORIAL_PURGED_PATH_SCORE_DISTRIBUTION", "CONTROL"),
    (22, "dr_value_and_uncertainty", "UNCERTAINTY_PRODUCER", "doubly_robust_estimate", "original reward unit", "MEAN_CONDITIONAL_RECORDED_DR_SCORE", "ESTIMATE"),
    (23, "ips_value", "FIELD", "inverse_propensity_score_estimate", "original reward unit", "IMPORTANCE_WEIGHTED_POLICY_VALUE", "ESTIMATE"),
    (24, "snips_value", "FIELD", "self_normalized_ips_estimate", "original reward unit", "SELF_NORMALIZED_IMPORTANCE_POLICY_VALUE", "ESTIMATE"),
    (25, "switch_value_and_selected_tau", "ROOT", "$", "original reward unit", "ORIGINAL_HELD_OUT_SWITCH_VALUE_AND_PER_FOLD_TAU", "ESTIMATE"),
    (26, "evi", "ROOT", "$", "original utility unit", "EXPECTED_VALUE_OF_INFORMATION_PER_DECISION", "HIGHER_IS_BETTER"),
    (27, "full_kelly_fraction", "FIELD", "raw_fraction", "original fraction of approved risk capital", "RAW_KELLY_FRACTION_WITHOUT_POSITION_AUTHORITY", "BOUNDED"),
    (28, "bounded_fraction", "ROOT", "$", "original fraction of approved risk capital", "BOUNDED_FRACTIONAL_WEALTH_FRACTION", "BOUNDED"),
    (29, "utility", "CERTIFIED", "$", "original return-equivalent utility", "OBJECTIVE_FOR_ORIGINAL_INPUT_WEIGHTS", "HIGHER_FOR_SAME_ORIGINAL_WEIGHTS_AND_BASIS"),
    (30, "cvar", "CERTIFIED", "conditional_value_at_risk", "original loss unit", "TAIL_LOSS_AT_ORIGINAL_CONFIDENCE", "LOWER_IS_BETTER"),
    (31, "expected_shortfall", "CERTIFIED", "$", "original loss unit", "HISTORICAL_EXPECTED_SHORTFALL_AT_ORIGINAL_CONFIDENCE", "LOWER_IS_BETTER"),
    (32, "implementation_shortfall", "ROOT", "$", "original currency", "ARRIVAL_TO_EXECUTION_TOTAL_SHORTFALL", "LOWER_IS_BETTER"),
    (33, "spread_cost", "ROOT", "$", "original currency", "SIGNED_EXECUTION_MINUS_DECISION_MIDPOINT_TIMES_QUANTITY", "LOWER_IS_BETTER"),
    (34, "fee", "FIELD", "amount_after_rounding", "original settlement currency", "ORIGINAL_APPLICABLE_SCHEDULE_QUANTIZED_FEE", "ORIGINAL_CLAIM_REQUIRED"),
    (35, "signed_fee_or_rebate", "FIELD", "amount_after_rounding", "original schedule currency", "ORIGINAL_APPLICABLE_SCHEDULE_SIGNED_QUANTIZED_FEE_OR_REBATE", "ORIGINAL_CLAIM_REQUIRED"),
    (36, "derived_yes_and_no_touches", "ROOT", "$", "original currency per contract and sequence", "CURRENT_PUBLIC_2_0_0_FIVE_MEMBER_BOOK_TRANSFORM", "ORIGINAL_CLAIM_REQUIRED"),
    (37, "fill_probability", "CERTIFIED", "$", "original probability", "FILL_PROBABILITY_ON_ORIGINAL_CALIBRATED_HORIZON", "HIGHER_IS_BETTER"),
    (38, "expected_fill_quantity", "ROOT", "$", "original quantity unit", "EXPECTED_FILLED_QUANTITY_IN_DECLARED_UNITS", "ESTIMATE"),
    (39, "queue_ahead_estimate", "ROOT", "$", "original quantity unit", "ORIGINAL_ACKNOWLEDGED_QUEUE_AHEAD_QUANTITY", "ESTIMATE"),
    (40, "signed_post_fill_markout", "ROOT", "$", "original currency", "SIGNED_QUANTITY_TIMES_POST_FILL_MIDPOINT_MINUS_FILL_PRICE", "HIGHER_IS_BETTER"),
    (41, "decayed_edge", "ROOT", "$", "original edge unit", "REMAINING_EDGE_AMOUNT_AT_MEASURED_LATENCY", "HIGHER_REMAINING_EDGE_IS_BETTER"),
    (42, "impact_fraction", "ROOT", "$", "original fraction of price", "SQUARE_ROOT_FRACTIONAL_PRICE_IMPACT", "LOWER_IS_BETTER"),
    (43, "capacity_penalty", "ROOT", "$", "original penalty-scale utility unit", "CAPACITY_CROWDING_PENALTY", "LOWER_IS_BETTER"),
    (44, "shrunk_covariance", "ROOT", "$", "original return covariance unit", "ORIGINAL_SHRUNK_COVARIANCE_MATRIX", "PSD_REQUIRED"),
    (45, "gate_decision", "GATE", "lcb_net,trade_gate", "original edge unit", "EXECUTION_ADJUSTED_LOWER_CONFIDENCE_BOUND", "PRESENTATION_ONLY_NO_ORDER_AUTHORITY"),
    (50, "recomputed_objective", "QUANTUM_PRODUCER", "$", "original trace and economic units separately", "ORIGINAL_QAOA_TRACE_CONSTRUCTOR", "VALIDATION_ONLY"),
    (51, "recomputed_objective", "QUANTUM_PRODUCER", "$", "original expectation variance and economic units separately", "ORIGINAL_VQE_TRACE_CONSTRUCTOR", "VALIDATION_ONLY"),
    (52, "benchmark_delta_packet", "QUANTUM_PRODUCER", "$", "original eleven-dimension comparison basis", "ORIGINAL_QUANTUM_CLASSICAL_NO_TRADE_CONSTRUCTOR", "SAME_BASIS_ONLY"),
)
EVIDENCE_PROJECTION_CONTRACTS_V1 = MappingProxyType({
    f"MATH-{number:02d}": EvidenceProjectionContractV1(f"MATH-{number:02d}", f"LP03::MATH-{number:02d}::PROJECTION_V1",
        name, selection, field, unit, basis, direction)
    for number, name, selection, field, unit, basis, direction in _LP03_PROJECTION_ROWS_V1
})


@dataclass(frozen=True, slots=True)
class EvidenceProjectionDataV1:
    """Bounded data only; cannot be used as a VALUE_PROJECTION or live handle."""

    contract: EvidenceProjectionContractV1
    original_raw_json: bytes
    decoded_raw: object
    projection_data_json: bytes


def project_evidence_raw_data_v1(math_spec_id, raw, *, maximum_raw_bytes, maximum_raw_nodes,
                                 maximum_projection_bytes, maximum_projection_nodes,
                                 output_unit, output_basis, numerical_work=None):
    """Select protocol 1.5 data; the original operation must establish custody.

    The closed data envelope contains projected_value, numerical_conversion,
    output_unit and output_basis. Its whole byte/node cost includes certificates.
    Supplied unit/basis are data, never proof of their original source joins.
    Six supplementary/constructor routes intentionally deny this raw-only API.
    """
    from contextlib import nullcontext
    import json
    from .context import _native_require, _native_ident
    from .specification import decode_evidence_raw_output_v1
    from .serialization import _native_strict_json, _encode_evidence_projection_json_v1
    from .parameter_policy import _EvidenceNumericalWorkV1, certify_evidence_binary64_v1

    _native_require(type(math_spec_id) is str and math_spec_id in EVIDENCE_PROJECTION_CONTRACTS_V1,
                    "LP03_PROJECTION_SCHEMA_UNAVAILABLE")
    contract = EVIDENCE_PROJECTION_CONTRACTS_V1[math_spec_id]
    analytic = contract.selection == "CERTIFIED"
    _native_require(type(numerical_work) is _EvidenceNumericalWorkV1 if analytic else numerical_work is None,
                    "LP03_PROJECTION_NUMERICAL_WORK")
    with numerical_work if analytic else nullcontext():
        _native_require(type(maximum_projection_bytes) is int and 0 < maximum_projection_bytes <= 1048576
                        and type(maximum_projection_nodes) is int and 0 < maximum_projection_nodes <= 4096,
                        "LP03_PROJECTION_JSON_BUDGET")
        for value in (output_unit, output_basis):
            _native_require(type(value) is str and len(value) <= 256, "LP03_PROJECTION_UNIT_OR_BASIS")
        _native_ident(output_basis)
        if math_spec_id == "MATH-08":
            _native_require(output_unit == "squared probability error", "LP03_PROJECTION_UNIT_MISMATCH")
        else:
            _native_ident(output_unit)
        _native_require(output_basis == contract.basis_requirement, "LP03_PROJECTION_BASIS_MISMATCH")
        decoded = decode_evidence_raw_output_v1(math_spec_id, raw,
            maximum_bytes=maximum_raw_bytes, maximum_nodes=maximum_raw_nodes)
        if contract.selection in ("FOLD_PRODUCER", "UNCERTAINTY_PRODUCER", "QUANTUM_PRODUCER"):
            reason = {"FOLD_PRODUCER": "MISSING_PREDICTION_PRODUCER",
                      "UNCERTAINTY_PRODUCER": "UNCERTAINTY_UNAVAILABLE",
                      "QUANTUM_PRODUCER": "LP03_ORIGINAL_QUANTUM_CONSTRUCTOR_REQUIRED"}[contract.selection]
            _native_require(False, reason)
        # A second bounded data view keeps Decimal lexemes and native JSON
        # containers. Never traverse an externally supplied mapping proxy.
        wire = _native_strict_json(raw, max_bytes=maximum_raw_bytes,
                                  max_nodes=maximum_raw_nodes, binary64_numbers=True)
        certificate = None
        if contract.selection in ("ROOT", "FIELD", "CERTIFIED"):
            value = wire if contract.original_field == "$" else wire[contract.original_field]
            if analytic:
                original_decimal = numerical_work.parse_decimal_v1(value)
                original_certificate = certify_evidence_binary64_v1(original_decimal, math_id=math_spec_id,
                    unit=output_unit, basis=output_basis, work=numerical_work)
                # This graph comes only from the just-completed original helper.
                certificate = {name: dict(child) if type(child) is MappingProxyType else child
                               for name, child in original_certificate.items()}
                value = certificate["analytic_value"]
        elif contract.selection == "INTERVAL":
            _native_require(wire["lower"] <= wire["upper"], "LP03_PROJECTION_INTERVAL_ORDER")
            value = [wire["lower"], wire["upper"]]
        elif contract.selection == "GATE":
            _native_require((decoded["lcb_net"] > 0) is wire["trade_gate"], "LP03_PROJECTION_GATE_INCONSISTENT")
            value = dict(decision="POSITIVE_NET_LCB" if wire["trade_gate"] else "NONPOSITIVE_NET_LCB",
                         lcb_net=wire["lcb_net"], raw_gate=wire["trade_gate"], no_order_authority=True)
        else:
            _native_require(contract.selection == "INDEXED", "LP03_PROJECTION_SELECTION_UNAVAILABLE")
            p_values, indices = wire["adjusted_p_values"], wire["rejected_original_indices"]
            count = len(p_values)
            _native_require(count > 0 and 0 <= wire["largest_rank"] == len(indices) <= count
                            and len(set(indices)) == len(indices) and all(0 <= index < count for index in indices)
                            and indices == sorted(indices)
                            and all(0.0 <= p <= 1.0 for p in p_values) and wire["correction"] >= 1.0,
                            "LP03_PROJECTION_MULTIPLE_TESTING_DOMAIN")
            value = dict(rows=[], correction=wire["correction"], largest_rank=wire["largest_rank"])
        envelope = dict(projected_value={contract.output_name: value}, numerical_conversion=certificate,
                        output_unit=output_unit, output_basis=output_basis)
        if contract.selection == "INDEXED":
            # First pass admits the complete expansion without constructing any
            # row. Every row has one container, three keys and three scalars.
            # The empty envelope has 17 nodes, including correction/rank.
            _native_require(17 + 7 * count <= maximum_projection_nodes, "LP03_PROJECTION_JSON_NODES_OR_DEPTH")
            empty = _encode_evidence_projection_json_v1(envelope,
                maximum_bytes=maximum_projection_bytes, maximum_nodes=maximum_projection_nodes)
            selected = set(indices)
            size = len(empty) + max(0, count - 1)
            for index, p_value in enumerate(p_values):
                size += (len(b'{"adjusted_p":') + len(json.dumps(p_value, allow_nan=False))
                         + len(b',"original_index":') + len(str(index))
                         + len(b',"rejected":') + (4 if index in selected else 5) + 1)
                _native_require(size <= maximum_projection_bytes, "LP03_PROJECTION_JSON_BYTES")
            value["rows"] = [dict(original_index=index, adjusted_p=p_value, rejected=index in selected)
                             for index, p_value in enumerate(p_values)]
        available_bytes = maximum_projection_bytes
        if analytic:
            available_bytes = min(available_bytes,
                numerical_work.limits["max_serialized_bytes"] - numerical_work.consumed["serialized_bytes"])
            numerical_work._require(available_bytes > 0, "LP03_NUMERICAL_SERIALIZATION_EXHAUSTED")
        output = _encode_evidence_projection_json_v1(envelope,
            maximum_bytes=available_bytes, maximum_nodes=maximum_projection_nodes)
        if analytic:
            numerical_work._consumed["serialized_bytes"] += len(output)
            numerical_work._require(numerical_work.consumed["serialized_bytes"] <= numerical_work.limits["max_serialized_bytes"],
                                    "LP03_NUMERICAL_SERIALIZATION_EXHAUSTED")
        return EvidenceProjectionDataV1(contract, raw, decoded, output)


def _text(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be bounded canonical text",
        )
    return value


def _refs(value: object, name: str, *, required: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item or item != item.strip() for item in value)
        or len(value) != len(set(value))
        or (required and not value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be an ordered unique reference tuple",
        )
    return value


def _reason_tuple(value: object, name: str) -> tuple[ReasonCode, ...]:
    if (
        not isinstance(value, tuple)
        or any(type(code) is not ReasonCode for code in value)
        or len(value) != len(set(value))
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be an ordered unique ReasonCode tuple",
        )
    return value


def _freeze(value: object, name: str) -> object:
    if value is None or type(value) in {bool, int, str} or isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(
                ReasonCode.NONFINITE_NUMERIC_INPUT,
                f"{name} contains a nonfinite value",
            )
        return value
    if isinstance(value, tuple | list):
        return tuple(_freeze(item, name) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) or not key for key in value):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                f"{name} contains an invalid mapping key",
            )
        return MappingProxyType(
            {
                key: _freeze(item, f"{name}.{key}")
                for key, item in sorted(value.items())
            }
        )
    raise ContractValidationError(
        ReasonCode.CONTRACT_OR_TYPE_INVALID,
        f"{name} contains unsupported {type(value).__name__}",
    )


def _mapping(value: object, name: str, *, required: bool = True) -> Mapping[str, object]:
    frozen = _freeze(value, name)
    if not isinstance(frozen, Mapping) or (required and not frozen):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            f"{name} must be an immutable mapping",
        )
    return frozen


def _from_json_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            f"{name} must be a mapping",
        )
    return value


def _lane_post_init(value: object, *, lane: str) -> None:
    if getattr(value, "schema_version") != LANE_RESULT_SCHEMA_VERSION_V1 or getattr(
        value, "contract_version"
    ) != LANE_RESULT_CONTRACT_VERSION_V1:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            f"{lane} result schema or contract version differs",
        )
    template_id = _text(getattr(value, "cohort_template_id"), "cohort_template_id")
    if template_id not in ST12F_TEMPLATE_IDS_V1:
        raise ContractValidationError(
            ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
            "lane result template is not a certified cohort member",
        )
    expected = f"ST12F-{lane}-CONTRACT::{template_id}"
    if getattr(value, "expected_result_contract_id") != expected:
        raise ContractValidationError(
            ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
            "lane packet expected-result identity differs from its exact lane",
        )
    for name in (
        "result_id",
        "input_lock_id",
        "run_reference",
        "producer_identity",
        "accounting_definition",
    ):
        _text(getattr(value, name), name)
    for name in (
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
    ):
        object.__setattr__(value, name, _mapping(getattr(value, name), name))
    for name in ("failure_states", "limitations"):
        _refs(getattr(value, name), name)
    cutoff = parse_utc(getattr(value, "point_in_time_cutoff"), field_name="point_in_time_cutoff")
    started = parse_utc(getattr(value, "started_at"), field_name="started_at")
    completed = parse_utc(getattr(value, "completed_at"), field_name="completed_at")
    available = parse_utc(getattr(value, "available_at"), field_name="available_at")
    closed = parse_utc(getattr(value, "closed_at"), field_name="closed_at")
    if not cutoff <= started <= completed <= available <= closed:
        raise ContractValidationError(
            ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
            "lane result timestamps violate point-in-time sequence",
        )
    for name, parsed in (
        ("point_in_time_cutoff", cutoff),
        ("started_at", started),
        ("completed_at", completed),
        ("available_at", available),
        ("closed_at", closed),
    ):
        object.__setattr__(value, name, parsed)
    if type(getattr(value, "fixture_only_not_evidence")) is not bool:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "fixture_only_not_evidence must be an exact boolean",
        )


def _lane_from_mapping(cls: type[object], value: object) -> object:
    if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "lane-result payload field roster differs from the exact 26 fields",
        )
    payload = dict(value)
    for name in (
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
    ):
        payload[name] = _from_json_mapping(payload[name], name)
    payload["failure_states"] = tuple(payload["failure_states"])
    payload["limitations"] = tuple(payload["limitations"])
    return cls(**payload)


@dataclass(frozen=True, slots=True)
class ReplayResultContractV1:
    result_id: str
    schema_version: str
    contract_version: str
    cohort_template_id: str
    expected_result_contract_id: str
    input_lock_id: str
    run_reference: str
    producer_identity: str
    implementation_versions: Mapping[str, object]
    source_epochs: Mapping[str, object]
    point_in_time_cutoff: datetime
    accounting_definition: str
    scenario_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    economic_metrics: Mapping[str, object]
    tca_metrics: Mapping[str, object]
    fill_metrics: Mapping[str, object]
    latency_metrics: Mapping[str, object]
    capacity_metrics: Mapping[str, object]
    failure_states: tuple[str, ...]
    limitations: tuple[str, ...]
    started_at: datetime
    completed_at: datetime
    available_at: datetime
    closed_at: datetime
    fixture_only_not_evidence: bool

    def __post_init__(self) -> None:
        _lane_post_init(self, lane="REPLAY")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ReplayResultContractV1":
        return _lane_from_mapping(cls, value)  # type: ignore[return-value]

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class PaperResultContractV1:
    result_id: str
    schema_version: str
    contract_version: str
    cohort_template_id: str
    expected_result_contract_id: str
    input_lock_id: str
    run_reference: str
    producer_identity: str
    implementation_versions: Mapping[str, object]
    source_epochs: Mapping[str, object]
    point_in_time_cutoff: datetime
    accounting_definition: str
    scenario_policy: Mapping[str, object]
    resampling_policy: Mapping[str, object]
    economic_metrics: Mapping[str, object]
    tca_metrics: Mapping[str, object]
    fill_metrics: Mapping[str, object]
    latency_metrics: Mapping[str, object]
    capacity_metrics: Mapping[str, object]
    failure_states: tuple[str, ...]
    limitations: tuple[str, ...]
    started_at: datetime
    completed_at: datetime
    available_at: datetime
    closed_at: datetime
    fixture_only_not_evidence: bool

    def __post_init__(self) -> None:
        _lane_post_init(self, lane="PAPER")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "PaperResultContractV1":
        return _lane_from_mapping(cls, value)  # type: ignore[return-value]

    def canonical_json(self) -> str:
        return deterministic_json(self)


class DivergenceTerminalStateV1(StrEnum):
    CONSISTENT_WITHIN_LOCKED_THRESHOLDS = "CONSISTENT_WITHIN_LOCKED_THRESHOLDS"
    MATERIAL_DIVERGENCE_REVIEW_REQUIRED = "MATERIAL_DIVERGENCE_REVIEW_REQUIRED"
    INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE = (
        "INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE"
    )


@dataclass(frozen=True, slots=True)
class DivergenceAssessmentV1:
    assessment_id: str
    schema_version: str
    contract_version: str
    input_lock_id: str
    cohort_template_id: str
    replay_result_ref: str
    paper_result_ref: str
    metric_deltas: Mapping[str, Decimal]
    directional_agreement: bool
    calibration_delta: Decimal | None
    execution_cost_delta: Decimal | None
    fill_delta: Decimal | None
    latency_delta: Decimal | None
    capacity_delta: Decimal | None
    regime_delta: Decimal | None
    threshold_policy_refs: tuple[str, ...]
    typed_blockers: tuple[ReasonCode, ...]
    terminal_state: DivergenceTerminalStateV1

    def __post_init__(self) -> None:
        if self.schema_version != DIVERGENCE_SCHEMA_VERSION_V1 or self.contract_version != "1.4":
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "divergence schema differs")
        for name in (
            "assessment_id",
            "input_lock_id",
            "cohort_template_id",
            "replay_result_ref",
            "paper_result_ref",
        ):
            _text(getattr(self, name), name)
        if self.cohort_template_id not in ST12F_TEMPLATE_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
                "divergence template is outside the cohort",
            )
        deltas = _mapping(self.metric_deltas, "metric_deltas", required=False)
        converted: dict[str, Decimal] = {}
        for key, value in deltas.items():
            converted[key] = exact_decimal(value, field_name=f"metric_deltas.{key}")
        object.__setattr__(self, "metric_deltas", MappingProxyType(converted))
        if type(self.directional_agreement) is not bool:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "directional agreement must be boolean")
        for name in (
            "calibration_delta",
            "execution_cost_delta",
            "fill_delta",
            "latency_delta",
            "capacity_delta",
            "regime_delta",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, exact_decimal(value, field_name=name))
        _refs(self.threshold_policy_refs, "threshold_policy_refs")
        _reason_tuple(self.typed_blockers, "typed_blockers")
        if type(self.terminal_state) is not DivergenceTerminalStateV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "divergence terminal state must be typed")
        missing_delta = any(
            getattr(self, name) is None
            for name in (
                "calibration_delta",
                "execution_cost_delta",
                "fill_delta",
                "latency_delta",
                "capacity_delta",
                "regime_delta",
            )
        )
        incomparable = self.terminal_state is DivergenceTerminalStateV1.INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE
        if bool(missing_delta or self.typed_blockers) != incomparable:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "missing/conflicting deltas must remain explicit and incomparable",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "DivergenceAssessmentV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "divergence fields differ")
        payload = dict(value)
        payload["terminal_state"] = DivergenceTerminalStateV1(payload["terminal_state"])
        payload["typed_blockers"] = tuple(ReasonCode(code) for code in payload["typed_blockers"])
        payload["threshold_policy_refs"] = tuple(payload["threshold_policy_refs"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class EvidenceIdentityDispositionStateV1(StrEnum):
    APPLICABLE_EXECUTED_AND_RECEIPTED = "APPLICABLE_EXECUTED_AND_RECEIPTED"
    APPLICABLE_BLOCKED_WITH_TYPED_REASON = "APPLICABLE_BLOCKED_WITH_TYPED_REASON"
    NOT_APPLICABLE_WITH_PROOF = "NOT_APPLICABLE_WITH_PROOF"


@dataclass(frozen=True, slots=True)
class EvidenceIdentityDispositionV1:
    evidence_identity: str
    disposition: EvidenceIdentityDispositionStateV1
    evidence_record_refs: tuple[str, ...]
    blocker_codes: tuple[ReasonCode, ...]
    proof_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.evidence_identity not in ST12F_EVIDENCE_IDENTITIES_V1 or type(self.disposition) is not EvidenceIdentityDispositionStateV1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "evidence identity or disposition is outside the closed registry",
            )
        _refs(self.evidence_record_refs, "evidence_record_refs")
        _reason_tuple(self.blocker_codes, "blocker_codes")
        _refs(self.proof_refs, "proof_refs")
        if self.disposition is EvidenceIdentityDispositionStateV1.APPLICABLE_EXECUTED_AND_RECEIPTED:
            valid = (
                len(self.evidence_record_refs) == 1
                and not self.blocker_codes
                and not self.proof_refs
            )
        elif self.disposition is EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON:
            valid = (
                bool(self.blocker_codes)
                and not self.evidence_record_refs
                and not self.proof_refs
            )
        else:
            valid = (
                len(self.proof_refs) == 1
                and not self.evidence_record_refs
                and not self.blocker_codes
            )
        if not valid:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "evidence disposition lacks its required receipt, blocker, or proof",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "EvidenceIdentityDispositionV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "evidence disposition fields differ")
        payload = dict(value)
        payload["disposition"] = EvidenceIdentityDispositionStateV1(payload["disposition"])
        payload["evidence_record_refs"] = tuple(payload["evidence_record_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        payload["proof_refs"] = tuple(payload["proof_refs"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class EvidenceSectionV1:
    section_id: str
    identity_dispositions: tuple[EvidenceIdentityDispositionV1, ...]

    def __post_init__(self) -> None:
        _text(self.section_id, "section_id")
        if (
            not isinstance(self.identity_dispositions, tuple)
            or not self.identity_dispositions
            or any(type(row) is not EvidenceIdentityDispositionV1 for row in self.identity_dispositions)
            or len({row.evidence_identity for row in self.identity_dispositions}) != len(self.identity_dispositions)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "evidence section requires unique typed dispositions",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "EvidenceSectionV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "evidence section fields differ")
        return cls(
            section_id=value["section_id"],
            identity_dispositions=tuple(
                EvidenceIdentityDispositionV1.from_canonical_mapping(row)
                for row in value["identity_dispositions"]
            ),
        )


class EvidenceBundleTerminalStateV1(StrEnum):
    INCOMPLETE_MISSING_REPLAY = "INCOMPLETE_MISSING_REPLAY"
    INCOMPLETE_MISSING_PAPER = "INCOMPLETE_MISSING_PAPER"
    INCOMPLETE_CONFLICT = "INCOMPLETE_CONFLICT"
    READY_FOR_INDEPENDENT_REVIEW = "READY_FOR_INDEPENDENT_REVIEW"
    INDEPENDENT_REVIEW_REJECTED = "INDEPENDENT_REVIEW_REJECTED"
    CLOSED_INDEPENDENTLY_VALIDATED = "CLOSED_INDEPENDENTLY_VALIDATED"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


_EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1 = MappingProxyType(
    {
        (
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        ): "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
        (
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
        ): "BOTH_LANES_PRESENT_SAME_LOCK_ALL_REQUIRED_CONTROLS_COMPUTED",
        (
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        ): "SEPARATE_REVIEW_RECEIPT_PASS_AND_ZERO_HARD_VETOES",
        (
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
        ): "SEPARATE_REVIEW_RECEIPT_REJECT",
        (
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.STALE,
        ): "TTL_SOURCE_EPOCH_PARAMETER_IMPLEMENTATION_OR_CONTEXT_CHANGE",
        (
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.SUPERSEDED,
        ): "NEWER_VALIDATED_BUNDLE_VERSION_SAME_IDENTITY",
    }
)

_EVIDENCE_BUNDLE_INITIAL_STATES_V1 = frozenset(
    {
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
        EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT,
        EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
    }
)


class IndependentReviewDecisionV1(StrEnum):
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class IndependentReviewRecordV1:
    review_id: str
    schema_version: str
    contract_version: str
    prior_bundle_ref: str
    evidence_id: str
    evidence_bundle_version: str
    input_lock_id: str
    reviewer_identity: str
    bundle_producer_identity: str
    authority_receipt_ref: str
    reviewed_source_epoch_refs: tuple[str, ...]
    decision: IndependentReviewDecisionV1
    blocker_codes: tuple[ReasonCode, ...]
    reviewed_at: datetime
    valid_until: datetime
    no_self_review: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != "QTT_ST12F_INDEPENDENT_REVIEW_RECORD_V1_4" or self.contract_version != "1.4":
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "independent review schema differs")
        for name in (
            "review_id",
            "prior_bundle_ref",
            "evidence_id",
            "evidence_bundle_version",
            "input_lock_id",
            "reviewer_identity",
            "bundle_producer_identity",
            "authority_receipt_ref",
        ):
            _text(getattr(self, name), name)
        _refs(self.reviewed_source_epoch_refs, "reviewed_source_epoch_refs", required=True)
        _reason_tuple(self.blocker_codes, "blocker_codes")
        if type(self.decision) is not IndependentReviewDecisionV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "review decision must be typed")
        reviewed = parse_utc(self.reviewed_at, field_name="reviewed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "reviewed_at", reviewed)
        object.__setattr__(self, "valid_until", valid_until)
        if reviewed > valid_until:
            raise ContractValidationError(ReasonCode.ST12F_BUNDLE_STALE, "review validity precedes review")
        if type(self.no_self_review) is not bool or not self.no_self_review or self.reviewer_identity == self.bundle_producer_identity:
            raise ContractValidationError(ReasonCode.ST12F_SELF_REVIEW_FORBIDDEN, "bundle producer cannot independently review its own bundle")
        if (self.decision is IndependentReviewDecisionV1.VALIDATED and self.blocker_codes) or (
            self.decision is IndependentReviewDecisionV1.REJECTED and not self.blocker_codes
        ):
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "review decision and blockers differ")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "IndependentReviewRecordV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "independent review fields differ")
        payload = dict(value)
        payload["decision"] = IndependentReviewDecisionV1(payload["decision"])
        payload["reviewed_source_epoch_refs"] = tuple(payload["reviewed_source_epoch_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class FToGHandoffReferencesV1:
    handoff_id: str
    contract_version: str
    input_lock_id: str
    source_epoch_refs: tuple[str, ...]
    observed_at: datetime
    valid_until: datetime
    terminal_state: str
    evidence_bundle_ref: str
    no_trade_blocker_refs: tuple[str, ...]
    champion_challenger_evidence_refs: tuple[str, ...]
    portfolio_utility_refs: tuple[str, ...]
    quantum_classical_comparison_receipt_ref: str
    read_only: bool = True

    def __post_init__(self) -> None:
        _text(self.handoff_id, "handoff_id")
        _text(self.input_lock_id, "input_lock_id")
        if self.contract_version != "1.4":
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "F-to-G handoff contract version differs",
            )
        _refs(self.source_epoch_refs, "source_epoch_refs", required=True)
        observed = parse_utc(self.observed_at, field_name="observed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "valid_until", valid_until)
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.ST12F_BUNDLE_STALE,
                "F-to-G validity precedes observation",
            )
        if self.terminal_state != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "F-to-G handoff requires a closed independently validated bundle",
            )
        _text(self.evidence_bundle_ref, "evidence_bundle_ref")
        for name in (
            "no_trade_blocker_refs",
            "champion_challenger_evidence_refs",
            "portfolio_utility_refs",
        ):
            _refs(getattr(self, name), name)
        _text(self.quantum_classical_comparison_receipt_ref, "quantum_classical_comparison_receipt_ref")
        if type(self.read_only) is not bool or not self.read_only:
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "F-to-G handoff is read-only")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "FToGHandoffReferencesV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "F-to-G handoff fields differ")
        payload = dict(value)
        payload["source_epoch_refs"] = tuple(payload["source_epoch_refs"])
        for name in (
            "no_trade_blocker_refs",
            "champion_challenger_evidence_refs",
            "portfolio_utility_refs",
        ):
            payload[name] = tuple(payload[name])
        return cls(**payload)


_SECTION_FIELDS_V1 = (
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
)


@dataclass(frozen=True, slots=True)
class ComputationEvidenceBundleV1:
    evidence_id: str
    schema_version: str
    contract_version: str
    evidence_bundle_version: str
    component_or_template_ref: str
    input_lock_id: str
    actual_executed_component_versions: Mapping[str, object]
    actual_executed_stack_versions: Mapping[str, object]
    replay_result_ref: str
    paper_result_ref: str
    divergence_assessment_ref: str
    lane_execution_receipt_refs: tuple[str, ...]
    calibration_and_probability_quality: EvidenceSectionV1
    transaction_cost_decomposition: EvidenceSectionV1
    fill_and_queue_quality: EvidenceSectionV1
    latency_and_staleness: EvidenceSectionV1
    capacity_and_crowding: EvidenceSectionV1
    portfolio_marginal_contribution: EvidenceSectionV1
    false_discovery_and_overfit_controls: EvidenceSectionV1
    regime_and_scenario_outcomes: EvidenceSectionV1
    uncertainty_and_model_risk_reserves: EvidenceSectionV1
    agent_and_model_disagreement: EvidenceSectionV1
    no_trade_comparison: EvidenceSectionV1
    independent_review_state: str
    failure_and_negative_evidence_states: tuple[str, ...]
    source_and_provenance_refs: tuple[str, ...]
    d_evidence_reference_projection: ST12FEvidenceReferenceV1 | str
    g_handoff_projection: FToGHandoffReferencesV1 | str
    terminal_state: EvidenceBundleTerminalStateV1
    blocker_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        if self.schema_version != EVIDENCE_BUNDLE_SCHEMA_VERSION_V1 or self.contract_version != EVIDENCE_BUNDLE_CONTRACT_VERSION_V1:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "evidence-bundle schema differs")
        for name in (
            "evidence_id",
            "evidence_bundle_version",
            "component_or_template_ref",
            "input_lock_id",
            "replay_result_ref",
            "paper_result_ref",
            "divergence_assessment_ref",
            "independent_review_state",
        ):
            _text(getattr(self, name), name)
        object.__setattr__(self, "actual_executed_component_versions", _mapping(self.actual_executed_component_versions, "actual_executed_component_versions", required=False))
        object.__setattr__(self, "actual_executed_stack_versions", _mapping(self.actual_executed_stack_versions, "actual_executed_stack_versions", required=False))
        _refs(self.lane_execution_receipt_refs, "lane_execution_receipt_refs")
        _refs(self.failure_and_negative_evidence_states, "failure_and_negative_evidence_states")
        _refs(self.source_and_provenance_refs, "source_and_provenance_refs", required=True)
        _reason_tuple(self.blocker_codes, "blocker_codes")
        if type(self.terminal_state) is not EvidenceBundleTerminalStateV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "bundle terminal state must be typed")
        dispositions: list[EvidenceIdentityDispositionV1] = []
        for field_name in _SECTION_FIELDS_V1:
            section = getattr(self, field_name)
            if type(section) is not EvidenceSectionV1 or section.section_id != field_name:
                raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID, "bundle evidence section identity differs")
            dispositions.extend(section.identity_dispositions)
        identities = tuple(row.evidence_identity for row in dispositions)
        if identities != ST12F_EVIDENCE_IDENTITIES_V1:
            raise ContractValidationError(ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID, "bundle must dispose every one of the 48 evidence identities exactly once")
        closed = self.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
        if closed:
            if (
                type(self.d_evidence_reference_projection) is not ST12FEvidenceReferenceV1
                or self.d_evidence_reference_projection.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
                or type(self.g_handoff_projection) is not FToGHandoffReferencesV1
                or self.blocker_codes
                or self.independent_review_state != self.terminal_state.value
            ):
                raise ContractValidationError(ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED, "closed bundle requires segregated validation and exact projections")
        elif self.d_evidence_reference_projection != "UNAVAILABLE" or self.g_handoff_projection != "UNAVAILABLE":
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "non-closed bundle cannot project to D or G")

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ComputationEvidenceBundleV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "bundle payload differs from exact 30-field roster")
        payload = dict(value)
        for name in _SECTION_FIELDS_V1:
            payload[name] = EvidenceSectionV1.from_canonical_mapping(payload[name])
        payload["lane_execution_receipt_refs"] = tuple(payload["lane_execution_receipt_refs"])
        payload["failure_and_negative_evidence_states"] = tuple(payload["failure_and_negative_evidence_states"])
        payload["source_and_provenance_refs"] = tuple(payload["source_and_provenance_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        payload["terminal_state"] = EvidenceBundleTerminalStateV1(payload["terminal_state"])
        if payload["d_evidence_reference_projection"] != "UNAVAILABLE":
            payload["d_evidence_reference_projection"] = (
                ST12FEvidenceReferenceV1.from_canonical_mapping(
                    payload["d_evidence_reference_projection"]
                )
            )
        if payload["g_handoff_projection"] != "UNAVAILABLE":
            payload["g_handoff_projection"] = FToGHandoffReferencesV1.from_canonical_mapping(payload["g_handoff_projection"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class RegisteredLaneResultOutcomeV1:
    registered_result: ReplayResultContractV1 | PaperResultContractV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        value = self.registered_result
        if type(value) not in {ReplayResultContractV1, PaperResultContractV1}:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "lane outcome requires one exact REPLAY or PAPER contract",
            )
        _refs(self.receipt_refs, "receipt_refs")
        if value.fixture_only_not_evidence:
            expected: tuple[str, ...] = ()
        else:
            lane = "REPLAY" if type(value) is ReplayResultContractV1 else "PAPER"
            expected = (
                f"ST12F-RECEIPT::{value.result_id}::{lane}_REGISTRATION",
            )
        if self.receipt_refs != expected:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "lane outcome receipt refs differ from the exact produced receipt",
            )


@dataclass(frozen=True, slots=True)
class BuiltEvidenceBundleOutcomeV1:
    evidence_bundle: ComputationEvidenceBundleV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        bundle = self.evidence_bundle
        if type(bundle) is not ComputationEvidenceBundleV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "bundle outcome requires one exact evidence bundle",
            )
        _refs(self.receipt_refs, "receipt_refs", required=True)
        expected = [
            f"ST12F-RECEIPT::{bundle.evidence_bundle_version}::"
            "EVIDENCE_BUNDLE_VERSION"
        ]
        if (
            bundle.terminal_state
            is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
        ):
            if (
                type(bundle.d_evidence_reference_projection)
                is not ST12FEvidenceReferenceV1
                or type(bundle.g_handoff_projection)
                is not FToGHandoffReferencesV1
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "closed outcome lacks its exact D/G projections",
                )
            expected.extend(
                (
                    "ST12F-RECEIPT::"
                    f"{bundle.d_evidence_reference_projection.reference_id}::"
                    "D_EVIDENCE_REFERENCE",
                    "ST12F-RECEIPT::"
                    f"{bundle.g_handoff_projection.handoff_id}::"
                    "G_HANDOFF_REFERENCE",
                )
            )
        if self.receipt_refs != tuple(expected):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "bundle outcome receipt refs differ from exact public production",
            )


@dataclass(frozen=True, slots=True)
class RegisterEvidenceControlRequestV1:
    """Private request for durable non-review ST12-F control custody."""

    request_id: str
    requested_at: datetime
    principal_id: str
    context: ComputationContextKeyV1
    idempotency_key: str
    traceparent: str
    tracestate: str
    input_lock_id: str

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "principal_id",
            "idempotency_key",
            "traceparent",
            "input_lock_id",
        ):
            _text(getattr(self, name), name)
        if not isinstance(self.tracestate, str):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "tracestate must be text",
            )
        if type(self.context) is not ComputationContextKeyV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private control request requires one exact context",
            )
        object.__setattr__(
            self,
            "requested_at",
            parse_utc(self.requested_at, field_name="requested_at"),
        )

    @classmethod
    def from_bundle_request(
        cls,
        request: BuildEvidenceBundleRequestV1,
        *,
        idempotency_suffix: str,
    ) -> "RegisterEvidenceControlRequestV1":
        if type(request) is not BuildEvidenceBundleRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private control request source must be exact OP15 custody",
            )
        _text(idempotency_suffix, "idempotency_suffix")
        return cls(
            request_id=f"{request.request_id}::CONTROL::{idempotency_suffix}",
            requested_at=request.requested_at,
            principal_id=request.principal_id,
            context=request.context,
            idempotency_key=(
                f"{request.idempotency_key}::CONTROL::{idempotency_suffix}"
            ),
            traceparent=request.traceparent,
            tracestate=request.tracestate,
            input_lock_id=request.input_lock_id,
        )


@dataclass(frozen=True, slots=True)
class EvidenceCacheSnapshotV1:
    generation: int
    effective_watermark: datetime
    recorded_watermark: datetime
    lane_results: Mapping[object, object]
    slot_results: Mapping[object, object]
    divergence: Mapping[object, object]
    bundles: Mapping[object, object]
    current_bundles: Mapping[object, object]
    reviews: Mapping[object, object]
    d_references: Mapping[object, object]
    g_handoffs: Mapping[object, object]

    def __post_init__(self) -> None:
        if (
            isinstance(self.generation, bool)
            or not isinstance(self.generation, int)
            or self.generation < 0
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "cache generation must be a nonnegative integer",
            )
        object.__setattr__(
            self,
            "effective_watermark",
            parse_utc(
                self.effective_watermark,
                field_name="effective_watermark",
            ),
        )
        object.__setattr__(
            self,
            "recorded_watermark",
            parse_utc(
                self.recorded_watermark,
                field_name="recorded_watermark",
            ),
        )
        for name in (
            "lane_results",
            "slot_results",
            "divergence",
            "bundles",
            "current_bundles",
            "reviews",
            "d_references",
            "g_handoffs",
        ):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise ContractValidationError(
                    ReasonCode.CONTRACT_OR_TYPE_INVALID,
                    f"cache {name} must be a mapping",
                )
            object.__setattr__(self, name, MappingProxyType(dict(value)))


@dataclass(frozen=True, slots=True)
class _EvidenceAdmissionResultV1:
    component_versions: Mapping[str, object]
    stack_versions: Mapping[str, object]
    provenance_refs: tuple[str, ...]
    negative_states: tuple[str, ...]
    divergence: DivergenceAssessmentV1 | None
    model_risk: ModelRiskEvidenceAssessmentV1 | None
    review: IndependentReviewRecordV1 | None


@dataclass(frozen=True, slots=True)
class FToDEvidenceReferenceQueryV1:
    """Exact read-only D query; it carries no activation or execution authority."""

    query_id: str
    requested_evidence_id: str
    requested_component_or_template_ref: str
    expected_input_lock_id: str
    expected_source_epoch_refs: tuple[str, ...]
    evaluated_at: datetime
    request_read_lineage_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "query_id",
            "requested_evidence_id",
            "requested_component_or_template_ref",
            "expected_input_lock_id",
        ):
            _text(getattr(self, name), name)
        _refs(
            self.expected_source_epoch_refs,
            "expected_source_epoch_refs",
            required=True,
        )
        _refs(
            self.request_read_lineage_refs,
            "request_read_lineage_refs",
            required=True,
        )
        object.__setattr__(
            self,
            "evaluated_at",
            parse_utc(self.evaluated_at, field_name="evaluated_at"),
        )


class CohortCompilationResolverProtocolV1(Protocol):
    def resolve_input_lock(
        self,
        input_lock_id: str,
        *,
        decision_cutoff: datetime,
    ) -> ImmutableReplayPaperInputLockV1: ...

    def resolve_expected_slot(
        self,
        compilation_id: str,
        lane: str,
        expected_result_contract_id: str,
        *,
        decision_cutoff: datetime,
    ) -> object: ...


class IndependentReviewResolverProtocolV1(Protocol):
    def resolve_review(
        self,
        review_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> IndependentReviewRecordV1: ...


class EvidenceBundleCandidateResolverProtocolV1(Protocol):
    def resolve_bundle_candidate(
        self, request: BuildEvidenceBundleRequestV1
    ) -> ComputationEvidenceBundleV1: ...


def lane_packet_from_typed_record_v1(
    record: TypedValueRecordV1,
    *,
    lane: str,
) -> ReplayResultContractV1 | PaperResultContractV1:
    if type(record) is not TypedValueRecordV1:
        raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "lane packet wrapper must be exact TypedValueRecordV1")
    raw = {field.name: field.value for field in record.fields}
    expected_fields = {field.name for field in fields(ReplayResultContractV1)}
    if set(raw) != expected_fields:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "typed lane packet does not carry the exact 26-field roster")
    json_fields = {
        "implementation_versions",
        "source_epochs",
        "scenario_policy",
        "resampling_policy",
        "economic_metrics",
        "tca_metrics",
        "fill_metrics",
        "latency_metrics",
        "capacity_metrics",
        "failure_states",
        "limitations",
    }
    time_fields = {"point_in_time_cutoff", "started_at", "completed_at", "available_at", "closed_at"}
    payload: dict[str, object] = {}
    for field in record.fields:
        if field.name in json_fields:
            if field.kind is not TypedValueKindV1.TEXT:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, f"{field.name} must contain canonical JSON text")
            payload[field.name] = safe_json_loads(field.value)
        elif field.name in time_fields:
            if field.kind is not TypedValueKindV1.TEXT:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, f"{field.name} must contain a UTC timestamp")
            payload[field.name] = parse_utc(field.value, field_name=field.name)
        elif field.name == "fixture_only_not_evidence":
            if field.kind is not TypedValueKindV1.BOOLEAN:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "fixture flag must be typed boolean")
            payload[field.name] = field.value
        else:
            if field.kind is not TypedValueKindV1.TEXT:
                raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, f"{field.name} must be typed text")
            payload[field.name] = field.value
    cls = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1 if lane == "PAPER" else None
    if cls is None:
        raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "lane must be exact REPLAY or PAPER")
    return cls.from_canonical_mapping(payload)


def _source_epoch_refs(lock: ImmutableReplayPaperInputLockV1) -> tuple[str, ...]:
    return tuple(f"{key}={lock.source_epochs[key]}" for key in sorted(lock.source_epochs))


@dataclass(frozen=True, slots=True)
class IndependentReviewAuthorityRequestV1:
    """Private no-effect request created only by the segregated review producer."""

    request_id: str
    requested_at: datetime
    principal_id: str
    capability_bundle_id: str
    context: ComputationContextKeyV1
    idempotency_key: str
    traceparent: str
    tracestate: str
    prior_bundle_ref: str
    input_lock_id: str
    component_or_template_ref: str
    reviewer_identity: str
    bundle_producer_identity: str

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "principal_id",
            "capability_bundle_id",
            "idempotency_key",
            "traceparent",
            "prior_bundle_ref",
            "input_lock_id",
            "component_or_template_ref",
            "reviewer_identity",
            "bundle_producer_identity",
        ):
            _text(getattr(self, name), name)
        if not isinstance(self.tracestate, str):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "tracestate must be text",
            )
        if type(self.context) is not ComputationContextKeyV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private review authority requires one exact context",
            )
        if self.reviewer_identity == self.bundle_producer_identity:
            raise AuthorityDeniedError(
                ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
                "private review authority cannot authorize self-review",
            )
        object.__setattr__(
            self,
            "requested_at",
            parse_utc(self.requested_at, field_name="requested_at"),
        )

    @property
    def operation_name(self) -> str:
        return "build_evidence_bundle"

    @property
    def component_ids(self) -> tuple[str, ...]:
        return (self.component_or_template_ref,)

    @property
    def parameter_ids(self) -> tuple[str, ...]:
        return ()


class IndependentEvidenceReviewV1:
    """Private segregated producer for pre-OP15 independent-review custody."""

    @classmethod
    def bind_measured_review_v1(cls, *, parent_resolver, host_binding, persistence_adapter):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .context import _native_require
        from .models import EvidenceKeyPurposeV1, EvidenceStoreRoleV1
        from .persistence import _EvidenceBoundStoreV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        ComputationEvidenceServiceV1._assert_measured_binding_v1(parent_resolver)
        issuer = parent_resolver._measured_original[0]
        _native_require(cls is IndependentEvidenceReviewV1 and type(host_binding) is EvidenceHostBindingV1
                        and type(persistence_adapter) is SQLiteReferenceAdapterV1
                        and host_binding.signing_purpose is EvidenceKeyPurposeV1.INDEPENDENT_REVIEW,
                        "LP03_REVIEW_ORIGINAL_ROLE_REQUIRED")
        config, producer = host_binding.public_configuration, parent_resolver._measured_original[1].public_configuration
        retained = persistence_adapter._evidence_store_binding_v1
        _native_require(retained.binding.role is EvidenceStoreRoleV1.REVIEW
                        and config.service_owner == "INDEPENDENT_EVIDENCE_REVIEW"
                        and config.service_principal == retained.binding.allowed_writer_principal
                        and config.service_principal != producer.service_principal
                        and config.service_principal != issuer.host.public_configuration.service_principal
                        and config.store_bindings == producer.store_bindings
                        and config.verification_keys == producer.verification_keys
                        and config.deployment_id == producer.deployment_id and config.origin is producer.origin
                        and config.generation == producer.generation
                        and config.environment_identity == producer.environment_identity
                        and config.package_identity_ref == producer.package_identity_ref,
                        "LP03_REVIEW_ORIGINAL_ROLE_SEPARATION")
        _EvidenceBoundStoreV1._require_original_objects_v1(retained, host_binding, persistence_adapter)
        with issuer.lock:
            _native_require(issuer.operation is None and issuer.measured_review_binding is None,
                            "LP03_MEASURED_REVIEW_ALREADY_BOUND_OR_BUSY")
            result = object.__new__(cls)
            result._measured_original = (issuer, parent_resolver, host_binding, persistence_adapter, retained, result)
            issuer.measured_review_binding = (result, result._measured_original)
            return result

    def _assert_measured_binding_v1(self):
        from .context import _native_require
        original = getattr(self, "_measured_original", None)
        _native_require(type(self) is IndependentEvidenceReviewV1 and type(original) is tuple and len(original) == 6
                        and original[5] is self and original[0].measured_review_binding is not None
                        and original[0].measured_review_binding[0] is self
                        and original[0].measured_review_binding[1] is original
                        and original[3]._evidence_store_binding_v1 is original[4], "LP03_MEASURED_REVIEW_BINDING_CHANGED")
        ComputationEvidenceServiceV1._assert_measured_binding_v1(original[1])
        _native_require(original[1]._measured_original[0] is original[0], "LP03_REVIEW_PARENT_OWNER_CHANGED")

    def review_measured_conformance_v1(self, candidate_ref):
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService
        from .persistence import _EvidenceReviewOperationV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        IndependentEvidenceReviewV1._assert_measured_binding_v1(self)
        operation = AgentOrchService._admit_evidence_review_v1(self._measured_original[0].service,
            reviewer=self, candidate_ref=candidate_ref)
        with _EvidenceReviewOperationV1._scope_v1(operation):
            if operation.phase == "COMMITTED_AND_READBACK":
                SQLiteReferenceAdapterV1._evidence_read_review_v1(operation.store, operation, stage="REVIEW")
            else:
                ComputationEvidenceServiceV1.resolve_measured_review_parent_v1(self._measured_original[1], operation)
                _EvidenceReviewOperationV1._prepare_decision_v1(operation)
                SQLiteReferenceAdapterV1._evidence_commit_review_v1(operation.store, operation, stage="REVIEW")
            _EvidenceReviewOperationV1._check_current_v1(operation)
            return operation.record

    @staticmethod
    def _bounded_review_decimal_v1(value, limits):
        """Exact decimal conversion with original input/work bounds before allocation."""
        import re
        from fractions import Fraction
        from .context import _native_require
        _native_require(type(value) is str and len(value) <= limits["max_serialized_bytes"]
                        and value.isascii(), "LP03_REVIEW_NUMERIC_TEXT_BOUND")
        parsed = re.fullmatch(r"([+-]?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?", value)
        _native_require(parsed is not None, "LP03_REVIEW_DECIMAL_ENCODING")
        sign, whole, fraction, exponent_text = parsed.groups()
        fraction = fraction or ""
        exponent_text = exponent_text or "0"
        exponent_digits = exponent_text.lstrip("+-").lstrip("0") or "0"
        work = limits["max_work_bits"]
        _native_require(len(exponent_digits) <= len(str(work)), "LP03_REVIEW_NUMERIC_WORK_BOUND")
        exponent = int(("-" if exponent_text.startswith("-") else "") + exponent_digits) - len(fraction)
        digits = (whole + fraction).lstrip("0") or "0"
        trailing = len(digits) - len(digits.rstrip("0")) if digits != "0" else 0
        if trailing:
            digits, exponent = digits[:-trailing], exponent + trailing
        # 10**n < 2**(4*n); these conservative bounds precede every large
        # integer/power allocation, independently of ambient Decimal context.
        _native_require(max(4 * (len(digits) + max(exponent, 0)) + 1,
                            4 * max(-exponent, 0) + 1) <= work, "LP03_REVIEW_NUMERIC_WORK_BOUND")
        coefficient = int(digits) * (-1 if sign == "-" else 1)
        numerator = coefficient * 10**exponent if exponent >= 0 else coefficient
        denominator = 1 if exponent >= 0 else 10**(-exponent)
        result = Fraction(numerator, denominator)
        _native_require(max(abs(result.numerator).bit_length(), result.denominator.bit_length()) <= limits["max_input_bits"],
                        "LP03_REVIEW_NUMERIC_INPUT_BOUND")
        return result

    @staticmethod
    def _bounded_review_midpoint_v1(bid, ask, limits):
        from fractions import Fraction
        from .context import _native_require
        _native_require(type(bid) is Fraction and type(ask) is Fraction, "LP03_REVIEW_RATIONAL_TYPE")
        bn, bd, an, ad = (abs(bid.numerator).bit_length(), bid.denominator.bit_length(),
                          abs(ask.numerator).bit_length(), ask.denominator.bit_length())
        _native_require(max(bn, bd, an, ad) <= limits["max_input_bits"]
                        and max(max(bn + ad, an + bd) + 1, bd + ad + 1) <= limits["max_work_bits"],
                        "LP03_REVIEW_NUMERIC_WORK_BOUND")
        return (bid + ask) / 2

    @staticmethod
    def _charge_brier_review_artifact_v1(value, *, work):
        """Bound the complete native-data artifact before formatting or signing."""
        from .context import _native_require
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .serialization import _encode_evidence_projection_json_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            remaining = min(1048576, work.limits["max_serialized_bytes"] - work.consumed["serialized_bytes"])
            work._require(remaining > 0, "LP03_NUMERICAL_SERIALIZATION_EXHAUSTED")
            raw = _encode_evidence_projection_json_v1(value, maximum_bytes=remaining, maximum_nodes=4096)
            work._consumed["serialized_bytes"] += len(raw)
            return value

    @staticmethod
    def _bounded_review_probability_edge_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Certify represented binary64 model-minus-market data, without source authority.

        The original calibration state is required but this arithmetic model
        supplies no calibration or market-source custody. Exact rational
        subtraction and a nearest-even cell preserve the public float result,
        including its signed zero. No formula or Decimal conversion runs here.
        """
        import struct
        from math import isfinite, nextafter, inf, copysign
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(map(len, (input_json, raw_json, expected_json))) <= work.limits["max_serialized_bytes"],
                "LP03_EDGE_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-02", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-02", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-02", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            left, right = (inputs[name] for name in ("calibrated_model_probability", "market_implied_probability"))
            work._require(type(inputs["calibration_state"]) is str
                and inputs["calibration_state"] == "CALIBRATED_FOR_DECLARED_CONTEXT"
                and all(type(value) is float and isfinite(value) for value in (left, right, raw, expected, projected_value))
                and 0.0 <= left <= 1.0 and 0.0 <= right <= 1.0,
                "LP03_EDGE_REVIEW_TYPED_DOMAIN")
            # The fixed finite binary64 domain bounds rational/midpoint text;
            # reserve both the emitted fragment and the complete proof before
            # arithmetic. This same work retains earlier charges on every call.
            reserve = 2 * (sum(map(len, (input_json, raw_json, expected_json))) + 16000)
            work._require(work._consumed["serialized_bytes"] + reserve <= work.limits["max_serialized_bytes"],
                "LP03_EDGE_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            bits = lambda value: struct.pack(">d", value).hex()
            work._consumed["input_values"] += 5
            left_ratio, right_ratio = (work._binary64_ratio(value, original_input=True) for value in (left, right))
            # Also bound the observed original/expected/projection values on
            # this same admission, even when one will fail the result join.
            for value in (raw, expected, projected_value):work._binary64_ratio(value, original_input=True)
            exact = work._subtract(left_ratio, right_ratio)
            work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length(), 1075))
            work._consumed["integer_operations"] += 1
            candidate = float(exact)
            if work._compare(exact, work._fraction(0)) == 0:
                negative_zero = left == right == 0.0 and copysign(1.0, left) < 0.0 and copysign(1.0, right) > 0.0
                candidate = -0.0 if negative_zero else 0.0
            work._require(isfinite(candidate), "LP03_EDGE_REVIEW_FINITE_CANDIDATE")
            actual, previous, following = (work._binary64_ratio(value) for value in
                (candidate, nextafter(candidate, -inf), nextafter(candidate, inf)))
            two = work._fraction(2)
            lower = work._divide(work._add(previous, actual), two)
            upper = work._divide(work._add(actual, following), two)
            even = int(bits(candidate), 16) % 2 == 0
            low_order, high_order = work._compare(exact, lower), work._compare(exact, upper)
            work._require((low_order > 0 or low_order == 0 and even)
                and (high_order < 0 or high_order == 0 and even), "LP03_EDGE_REVIEW_NEAREST_EVEN_CELL")
            work._require(bits(raw) == bits(expected) == bits(projected_value) == bits(candidate)
                and raw_json == expected_json, "LP03_EDGE_REVIEW_RESULT_OR_EXPECTATION_MISMATCH")
            fragment = work._emit(dict(model_bits=bits(left), market_bits=bits(right), exact_difference=exact,
                candidate_bits=bits(candidate), lower_midpoint=lower, upper_midpoint=upper,
                tie_flag=int(low_order == 0 or high_order == 0), typed_input_json=input_json.decode("utf-8"),
                original_raw_json=raw_json.decode("utf-8"), preregistered_raw_json=expected_json.decode("utf-8")))
            summary = {name: dict(value) if type(value) is MappingProxyType else value for name, value in fragment.items()}
            proof = dict(profile="REPRESENTED_BINARY64_MODEL_MINUS_MARKET_NEAREST_EVEN_V1",
                math_id="MATH-02", unit="probability points", basis="CALIBRATED_MODEL_MINUS_PAYOUT_NORMALIZED_MARKET_PROBABILITY",
                intermediate_observation_scope="EXACT_DIFFERENCE_AND_ROUNDING_CELL_DERIVED_NOT_OBSERVED",
                authority_scope="SOFTWARE_ARITHMETIC_MODEL_ONLY_NO_CALIBRATION_MARKET_SOURCE_OR_TRADING_AUTHORITY", summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_brier_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Independent exact arithmetic; no original formula is invoked here.

        This conservative profile proves every ordered arithmetic intermediate
        exactly representable in binary64. Nonexact data retain a failed proof;
        no tolerance, changed precision or conversion certificate is substituted.
        Original signed-zero spelling remains in input/raw JSON observations.
        """
        from math import isfinite
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                          and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                          "LP03_BRIER_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-08", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-08", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-08", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            rows, outcomes = inputs["probability_rows"], inputs["outcome_indices"]
            work._require(type(rows) is tuple and bool(rows) and type(outcomes) is tuple and len(rows) == len(outcomes)
                          and type(rows[0]) is tuple and len(rows[0]) >= 2
                          and all(type(row) is tuple and len(row) == len(rows[0]) for row in rows)
                          and all(type(value) is int and 0 <= value < len(rows[0]) for value in outcomes)
                          and len(raw["per_observation"]) == len(expected["per_observation"]) == len(rows),
                          "LP03_BRIER_REVIEW_COMPLETE_TYPED_ROSTER")
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_BRIER_REVIEW_BINARY64_INPUT")
                # The existing statistical helper rejects -0.0. This separate
                # closed admission retains its original wire representation and
                # uses rational zero only for the independently checked algebra.
                return work._binary64_ratio(value, original_input=True)
            def representable(value):
                work._bits(max(abs(value.numerator).bit_length(), value.denominator.bit_length(), 1075))
                work._consumed["integer_operations"] += 1
                candidate = float(value)
                work._require(isfinite(candidate)
                              and work._compare(work._binary64_ratio(candidate), value) == 0,
                              "LP03_BRIER_REVIEW_NONEXACT_BINARY64_INTERMEDIATE")
                return value
            zero, one, two = work._fraction(0), work._fraction(1), work._fraction(2)
            def emitted(values):
                # These are this work object's own just-created bounded
                # fragments. Keep exact native containers for the final
                # artifact encoder; arbitrary caller mappings never enter it.
                fragment = work._emit(values)
                return {name: dict(value) if type(value) is MappingProxyType else value for name, value in fragment.items()}
            total, proofs = zero, []
            for ordinal, (row, outcome) in enumerate(zip(rows, outcomes)):
                probability_total, score = zero, zero
                for index, value in enumerate(row):
                    probability = observed(value)
                    work._require(work._compare(probability, zero) >= 0 and work._compare(probability, one) <= 0,
                                  "LP03_BRIER_REVIEW_PROBABILITY_DOMAIN")
                    probability_total = representable(work._add(probability_total, probability))
                    residual = representable(work._subtract(probability, one if index == outcome else zero))
                    square = representable(work._multiply(residual, residual))
                    score = representable(work._add(score, square))
                work._require(work._compare(probability_total, one) == 0 and work._compare(score, two) <= 0,
                              "LP03_BRIER_REVIEW_SIMPLEX_OR_SCORE_DOMAIN")
                work._require(work._compare(observed(raw["per_observation"][ordinal]), score) == 0
                              and work._compare(observed(expected["per_observation"][ordinal]), score) == 0,
                              "LP03_BRIER_REVIEW_OBSERVATION_SCORE_MISMATCH")
                total = representable(work._add(total, score))
                proofs.append(emitted(dict(row_position=ordinal, outcome_index=outcome, score=score,
                                           ordered_score_prefix=total)))
            mean = representable(work._divide(total, work._exact(len(rows))))
            work._require(work._compare(observed(raw["mean_brier_score"]), mean) == 0
                          and work._compare(observed(expected["mean_brier_score"]), mean) == 0
                          and work._compare(observed(projected_value), mean) == 0 and raw_json == expected_json,
                          "LP03_BRIER_REVIEW_MEAN_OR_EXPECTATION_MISMATCH")
            summary = emitted(dict(mean_brier_score=mean, observation_count=len(rows), class_count=len(rows[0]),
                typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8")))
            proof = dict(profile="EXACT_BINARY64_ORDERED_INTERMEDIATES_V1",
                row_identity="ORDERED_SYNTHETIC_ROWS_NO_SAMPLE_IDS", per_observation=tuple(proofs), summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)

    @staticmethod
    def _bounded_review_log_loss_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Independent rational enclosures and binary64 cells for M09 data.

        Rounded row sums and the rounded score sum are derived witnesses;
        the original callable does not expose either intermediate. Source,
        raw and expected wire bytes retain signed zero and scalar types.
        This calculation supplies no source or execution authority.
        """
        from math import isfinite, nextafter, inf
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_LOG_LOSS_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-09", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-09", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-09", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            rows, outcomes = inputs["probability_rows"], inputs["outcome_indices"]
            work._require(type(rows) is tuple and 0 < len(rows) <= 4096 and type(outcomes) is tuple
                and len(rows) == len(outcomes) and type(rows[0]) is tuple and 2 <= len(rows[0]) <= 4096
                and all(type(row) is tuple and len(row) == len(rows[0]) for row in rows)
                and all(type(value) is int and 0 <= value < len(rows[0]) for value in outcomes)
                and len(raw["per_observation"]) == len(expected["per_observation"]) == len(rows),
                "LP03_LOG_LOSS_REVIEW_COMPLETE_TYPED_ROSTER")
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_LOG_LOSS_REVIEW_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            def bits(value):
                return struct.pack(">d", value).hex()
            def emitted(values):
                fragment = work._emit(values)
                return {name: dict(value) if type(value) is MappingProxyType else value for name, value in fragment.items()}
            zero, one, two = work._fraction(0), work._fraction(1), work._fraction(2)
            def cell(candidate, lower, upper, label):
                work._require(type(candidate) is float and isfinite(candidate), "LP03_LOG_LOSS_FINITE_CELL_REQUIRED")
                previous, following = nextafter(candidate, -inf), nextafter(candidate, inf)
                work._require(isfinite(previous) and isfinite(following), "LP03_LOG_LOSS_FINITE_CELL_REQUIRED")
                actual, before, after = (work._binary64_ratio(value) for value in (candidate, previous, following))
                low_mid = work._divide(work._add(before, actual), two)
                high_mid = work._divide(work._add(actual, after), two)
                even = int(bits(candidate), 16) & 1 == 0
                lo, hi = work._compare(lower, low_mid), work._compare(upper, high_mid)
                work._require(work._compare(lower, upper) <= 0 and (lo > 0 or lo == 0 and even)
                    and (hi < 0 or hi == 0 and even), "LP03_LOG_LOSS_NEAREST_EVEN_CELL_UNPROVEN")
                return actual, emitted(dict(operation=label, candidate_bits=bits(candidate), candidate=actual,
                    exact_lower=lower, exact_upper=upper, lower_midpoint=low_mid, upper_midpoint=high_mid,
                    tie_rule="NEAREST_EVEN"))
            def derived(exact, label):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = float(exact)
                actual, proof = cell(candidate, exact, exact, label)
                return candidate, actual, proof
            epsilon = observed(inputs["clip_epsilon"])
            work._require(work._compare(epsilon, zero) > 0 and work._compare(epsilon, work._fraction(1, 2)) < 0,
                "LP03_LOG_LOSS_EPSILON_DOMAIN")
            upper_float, upper, upper_proof = derived(work._subtract(one, epsilon), "DERIVED_ONE_MINUS_EPSILON")
            # The original row validator uses 8 * ulp(1.0) * row width. Both
            # factors and their product are exact for this bounded roster.
            tolerance = work._multiply(work._fraction(1, 2**49), work._exact(len(rows[0])))
            total, proofs = zero, []
            for ordinal, (row, outcome) in enumerate(zip(rows, outcomes)):
                values, row_total = [], zero
                for value in row:
                    probability = observed(value)
                    work._require(work._compare(probability, zero) >= 0 and work._compare(probability, one) <= 0,
                        "LP03_LOG_LOSS_PROBABILITY_DOMAIN")
                    values.append(probability)
                    row_total = work._add(row_total, probability)
                _, row_sum, row_proof = derived(row_total, "DERIVED_ROW_FSUM")
                _, row_error, _row_error_proof = derived(work._subtract(row_sum, one), "DERIVED_ROW_SUM_MINUS_ONE")
                absolute_error = work._subtract(zero, row_error) if work._compare(row_error, zero) < 0 else row_error
                work._require(work._compare(absolute_error, tolerance) <= 0, "LP03_LOG_LOSS_ROW_SUM_DOMAIN")
                probability = values[outcome]
                lower_index = 0 if work._compare(probability, epsilon) >= 0 else 1
                lower_selected = probability if lower_index == 0 else epsilon
                upper_index = 0 if work._compare(lower_selected, upper) <= 0 else 1
                clipped = lower_selected if upper_index == 0 else upper
                score_float = raw["per_observation"][ordinal]
                score = observed(score_float)
                observed(expected["per_observation"][ordinal])
                if work._compare(clipped, one) == 0:
                    log_lower = log_upper = zero
                    work._require(bits(score_float) == "8000000000000000", "LP03_LOG_LOSS_NEGATED_LOG_ONE_SIGN")
                else:
                    log_lower, log_upper = work._log_enclosure(work._divide(one, clipped))
                    work._require(work._compare(score, zero) > 0, "LP03_LOG_LOSS_POSITIVE_SCORE_REQUIRED")
                actual, logarithm = cell(score_float, log_lower, log_upper, "OBSERVED_NEGATED_LOG")
                work._require(bits(score_float) == bits(expected["per_observation"][ordinal]),
                    "LP03_LOG_LOSS_OBSERVATION_EXPECTATION_MISMATCH")
                total = work._add(total, actual)
                selection = emitted(dict(row_position=ordinal, outcome_index=outcome, lower_selected_index=lower_index,
                    upper_selected_index=upper_index, original_selected_bits=bits(row[outcome]), clipped=clipped))
                proofs.append(dict(selection=selection, derived_row_sum=row_proof,
                    derived_row_difference=_row_error_proof, logarithm=logarithm))
            sum_float, rounded_sum, sum_proof = derived(total, "DERIVED_UNOBSERVED_SCORE_FSUM")
            count = work._exact(len(rows))
            count_float, rounded_count, count_proof = derived(count, "DERIVED_EXACT_ROW_COUNT")
            work._require(work._compare(count, rounded_count) == 0, "LP03_LOG_LOSS_ROW_COUNT_NOT_EXACT")
            mean_float, mean, mean_proof = derived(work._divide(rounded_sum, rounded_count), "DERIVED_FINAL_DIVISION")
            for value in (raw["mean_log_loss"], expected["mean_log_loss"], projected_value):
                observed(value)
                work._require(bits(value) == bits(mean_float), "LP03_LOG_LOSS_MEAN_OR_EXPECTATION_MISMATCH")
            work._require(raw_json == expected_json, "LP03_LOG_LOSS_RAW_EXPECTATION_WIRE_MISMATCH")
            summary = emitted(dict(observation_count=len(rows), class_count=len(rows[0]), epsilon=epsilon,
                upper_clip=upper, derived_rounded_sum=rounded_sum, mean_log_loss=mean,
                typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8")))
            proof = dict(profile="RATIONAL_LOG_ENCLOSURES_BINARY64_NEAREST_EVEN_V1",
                intermediate_observation_scope="ROW_AND_SCORE_SUMS_ARE_DERIVED_NOT_OBSERVED",
                upper_clip_proof=upper_proof, per_observation=tuple(proofs), derived_score_sum=sum_proof,
                exact_row_count=count_proof, final_division=mean_proof, summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)

    @staticmethod
    def _bounded_review_spa_v1(input_json, raw_json, expected_json, projected_value, *, expected_environment, work):
        """Finite complete-column M16 SPA model, never family/significance authority.

        This consumes model input columns only. A runtime source route must
        separately prove the original complete material trial-family custody.
        Native formula intermediates are derived, never claimed as observed.
        """
        from math import isfinite, nextafter, inf, copysign, isqrt
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1, _EvidenceBootstrapReplayV1
        from .specification import decode_evidence_raw_output_v1
        from .evidence_execution import _worker_environment_v1
        from .models import EvidenceEnvironmentIdentityV1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_SPA_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-16", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-16", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-16", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            values, sign, seed, replicates, block, alpha, variant = (inputs[name] for name in (
                "loss_differentials", "sign_convention", "seed", "replicates", "expected_block_length", "alpha", "recenter_variant"))
            positive = "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"
            negative = "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"
            work._require(type(values) is tuple and 3 <= len(values) <= 4
                and type(values[0]) is tuple and 1 <= len(values[0]) <= 2
                and all(type(row) is tuple and len(row) == len(values[0]) for row in values)
                and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for row in values for value in row)
                and type(sign) is str and sign in (positive, negative)
                and type(block) is float and isfinite(block) and 1.0 <= block <= len(values)
                and type(seed) is int and seed.bit_length() <= 256
                and type(replicates) is int and 1 <= replicates <= 4 and len(values) * replicates <= 16
                and type(alpha) is float and isfinite(alpha) and 0.0 < alpha < 1.0
                and type(variant) is str and variant == "HANSEN_CONSISTENT_LOG_LOG_THRESHOLD"
                and type(projected_value) is MappingProxyType and set(projected_value) == set(raw)
                and all(type(projected_value[key]) is tuple for key in ("candidate_means", "long_run_variances",
                    "consistent_valid_columns", "simulated_statistics")),
                "LP03_SPA_REVIEW_TYPED_DOMAIN")
            work._require(type(expected_environment) is EvidenceEnvironmentIdentityV1
                and _worker_environment_v1() == expected_environment, "LP03_SPA_ENVIRONMENT_MISMATCH")
            environment_json = deterministic_json(expected_environment)
            source_bytes = sum(len(value) for value in (input_json, raw_json, expected_json))
            count, candidates = len(values), len(values[0])
            max_cells = candidates * (2 + 2 * count + 5 + 15 * (count - 1) + count * (count - 1) // 2 + 10) + replicates * (1 + 7 * candidates) + 1
            work._require(max_cells <= 213, "LP03_SPA_COMPLETE_CELL_CAPACITY")
            # Bound emitted fragments and complete proof before arithmetic or
            # construction of the original review replay. Candidate-only cells
            # retain every derived bit pattern; the profile fixes their full
            # operation/operand/branch reconstruction. Log certificates retain
            # exact finite-series parameters, not repeated large ratio texts.
            reserve = 2 * (64 * 180 + max_cells * 52 + 2 * candidates * 128
                + 2 * source_bytes + 6 * len(environment_json.encode("utf-8")) + 2000)
            work._require(work.consumed["serialized_bytes"] + reserve <= work.limits["max_serialized_bytes"],
                "LP03_SPA_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(192 + 64 * 18 + max_cells + 2 * candidates * 10 + 64 <= 4096,
                "LP03_SPA_REVIEW_COMPLETE_NODE_LAYOUT")
            work._assert_bootstrap_custody_v1()
            original_replays = tuple(work._bootstrap_invocations)
            original_draw_count = work.consumed["random_draws"]
            zero, one, two = work._fraction(0), work._fraction(1), work._fraction(2)
            cells, log_certificates = [], []
            def bits(value):
                return struct.pack(">d", value).hex()
            def ratio(value):
                work._require(type(value) is float and isfinite(value), "LP03_SPA_FINITE_CELL_REQUIRED")
                return work._binary64_ratio(value)
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_SPA_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            def rounding_cell(candidate):
                work._require(type(candidate) is float and isfinite(candidate)
                    and isfinite(nextafter(candidate, -inf)) and isfinite(nextafter(candidate, inf)),
                    "LP03_SPA_FINITE_CELL_REQUIRED")
                lower = work._divide(work._add(ratio(nextafter(candidate, -inf)), ratio(candidate)), two)
                upper = work._divide(work._add(ratio(candidate), ratio(nextafter(candidate, inf))), two)
                return lower, upper, int(bits(candidate), 16) & 1 == 0
            def rounded(exact, *, negative_zero=False):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = (-0.0 if negative_zero else 0.0) if exact.numerator == 0 else float(exact)
                lower, upper, even = rounding_cell(candidate)
                low_test, high_test = work._compare(exact, lower), work._compare(exact, upper)
                work._require((low_test > 0 or low_test == 0 and even)
                    and (high_test < 0 or high_test == 0 and even), "LP03_SPA_NEAREST_EVEN_CELL_UNPROVEN")
                return candidate
            def append(candidate):
                # The fixed profile reconstructs every operation and operand
                # from original inputs and preceding certified values. Every
                # candidate bit pattern remains in exact execution order.
                work._require(len(cells) < max_cells, "LP03_SPA_COMPLETE_CELL_CAPACITY")
                emitted = work._emit(dict(position=len(cells), candidate=bits(candidate)))
                work._require(len(deterministic_json(emitted).encode("utf-8")) <= 52,
                    "LP03_SPA_CELL_BYTE_BOUND")
                cells.append(emitted["candidate"])
                return candidate
            def square_root(value):
                exact = ratio(value)
                work._require(work._compare(exact, zero) >= 0 and work._compare(exact, work._fraction(32)) <= 0,
                    "LP03_SPA_SQRT_DOMAIN")
                # This counts a DERIVED square-root certificate, not an
                # observed call to the native formula's math.sqrt.
                work._consumed["square_roots"] += 1
                if exact.numerator == 0:
                    return 0.0
                exponent = work._int_sum(exact.numerator.bit_length(), -exact.denominator.bit_length())
                pivot = (work._fraction(work._shift(1, exponent)) if exponent >= 0
                    else work._fraction(1, work._shift(1, -exponent)))
                if work._compare(exact, pivot) < 0:
                    exponent = work._int_sum(exponent, -1)
                work._require(-1074 <= exponent <= 5, "LP03_SPA_SQRT_BINARY64_INPUT_RANGE")
                scale = work._int_sum(52, -(exponent // 2))
                numerator = work._shift(exact.numerator, work._int_product(2, scale))
                work._bits(max(numerator.bit_length(), exact.denominator.bit_length()))
                work._consumed["integer_operations"] += 1
                quotient = numerator // exact.denominator
                work._bits(quotient.bit_length())
                work._consumed["integer_operations"] += 1
                floor_root = isqrt(quotient)
                candidate = rounded(work._fraction(floor_root, work._shift(1, scale)))
                following = nextafter(candidate, inf)
                midpoint = work._divide(work._add(ratio(candidate), ratio(following)), two)
                comparison = work._compare(exact, work._multiply(midpoint, midpoint))
                if comparison > 0 or comparison == 0 and int(bits(candidate), 16) & 1:
                    candidate = following
                lower, upper, even = rounding_cell(candidate)
                low_test = work._compare(exact, work._multiply(lower, lower))
                high_test = work._compare(exact, work._multiply(upper, upper))
                work._require(work._compare(lower, zero) >= 0
                    and (low_test > 0 or low_test == 0 and even)
                    and (high_test < 0 or high_test == 0 and even), "LP03_SPA_SQUARED_MIDPOINT_CELL_UNPROVEN")
                return candidate
            def logarithm(value):
                exact = ratio(value)
                work._require(work._compare(exact, one) > 0 and work._compare(exact, work._fraction(4)) <= 0,
                    "LP03_SPA_LOG_DOMAIN")
                terms = 64 if value >= 2.0 else 16
                z = work._divide(work._subtract(exact, one), work._add(exact, one))
                square, power, total = work._multiply(z, z), z, zero
                for index in range(terms):
                    work._consumed["log_series_terms"] += 1
                    denominator = work._fraction(work._int_sum(work._int_product(2, index), 1))
                    total = work._add(total, work._divide(power, denominator))
                    power = work._multiply(power, square)
                lower = work._multiply(two, total)
                remainder = work._divide(work._multiply(two, power),
                    work._multiply(work._fraction(work._int_sum(work._int_product(2, terms), 1)), work._subtract(one, square)))
                upper = work._add(lower, remainder)
                candidate = rounded(work._divide(work._add(lower, upper), two))
                cell_low, cell_high, _ = rounding_cell(candidate)
                work._require(work._compare(cell_low, lower) < 0 and work._compare(upper, cell_high) < 0,
                    "LP03_SPA_LOG_ENCLOSURE_CELL_UNPROVEN")
                work._require(len(log_certificates) < 2 * candidates, "LP03_SPA_LOG_CERTIFICATE_CAPACITY")
                certificate = dict(work._emit(dict(position=len(cells), input_bits=bits(value), terms=terms, candidate=bits(candidate))))
                work._require(len(deterministic_json(certificate).encode("utf-8")) <= 128,
                    "LP03_SPA_LOG_CERTIFICATE_BYTE_BOUND")
                log_certificates.append(certificate)
                return candidate
            def op(label, kind, *operands):
                # Labels assist the implementation and independent fixture;
                # the signed profile fixes the full schedule, not these labels.
                work._require(type(label) is str and len(label) <= 32 and 1 <= len(operands) <= 4,
                    "LP03_SPA_OPERATION_LAYOUT")
                xs = tuple(ratio(value) for value in operands)
                if kind == "SQRT":
                    work._require(len(xs) == 1, "LP03_SPA_OPERATION_LAYOUT")
                    return append(square_root(operands[0]))
                if kind == "LOG":
                    work._require(len(xs) == 1, "LP03_SPA_OPERATION_LAYOUT")
                    return append(logarithm(operands[0]))
                if kind == "FSUM":
                    exact = zero
                    for value in xs:
                        exact = work._add(exact, value)
                    negative_zero = False
                elif kind == "POW":
                    work._require(len(xs) == 2 and xs[1].denominator == 1 and 1 <= xs[1].numerator <= 3
                        and work._compare(xs[0], zero) >= 0 and work._compare(xs[0], one) <= 0,
                        "LP03_SPA_INTEGER_POWER_DOMAIN")
                    exact = one
                    for _ in range(xs[1].numerator):
                        exact = work._multiply(exact, xs[0])
                    negative_zero = False
                else:
                    work._require(kind in ("ADD", "SUB", "MUL", "DIV") and len(xs) == 2,
                        "LP03_SPA_OPERATION_LAYOUT")
                    exact = {"ADD": work._add, "SUB": work._subtract, "MUL": work._multiply, "DIV": work._divide}[kind](*xs)
                    signs = tuple(copysign(1.0, value) < 0 for value in operands)
                    negative_zero = (signs[0] != signs[1]) if kind in ("MUL", "DIV") else (
                        operands[0] == operands[1] == 0.0 and signs[0] and (signs[1] if kind == "ADD" else not signs[1]))
                return append(rounded(exact, negative_zero=negative_zero))
            for value in (*(value for row in values for value in row), block, alpha):
                observed(value)
            work._exact(seed)
            work._exact(replicates)
            n, m, reps = count, candidates, replicates
            matrix = tuple(tuple(value if sign == positive else -value for value in row) for row in values)
            def maximum(values):
                result = 0.0
                for value in values:
                    work._consumed["comparisons"] += 1
                    if value > result:
                        result = value
                return result
            columns=[[row[j] for row in matrix] for j in range(m)]
            def mean(label,values):return op(label+'_MEAN','DIV',op(label+'_SUM','FSUM',*values),float(n))
            means=[mean('C'+str(j),column) for j,column in enumerate(columns)]
            variances=[]
            for j,column in enumerate(columns):
                prefix='V'+str(j);center=mean(prefix,column)
                demeaned=[op(prefix+'_D'+str(i),'SUB',v,center) for i,v in enumerate(column)]
                restart=op(prefix+'_RESTART','DIV',1.0,block)
                variance=op(prefix+'_VAR0','DIV',op(prefix+'_SQSUM','FSUM',*(op(prefix+'_S'+str(i),'MUL',v,v) for i,v in enumerate(demeaned))),float(n))
                for lag in range(1,n):
                    tag=prefix+'_L'+str(lag)
                    weight=op(tag+'_W','ADD',
                        op(tag+'_LEFT','MUL',op(tag+'_COMPLEMENT','SUB',1.0,op(tag+'_FRACTION0','DIV',float(lag),float(n))),op(tag+'_POWER0','POW',op(tag+'_BASE0','SUB',1.0,restart),float(lag))),
                        op(tag+'_RIGHT','MUL',op(tag+'_FRACTION1','DIV',float(lag),float(n)),op(tag+'_POWER1','POW',op(tag+'_BASE1','SUB',1.0,restart),float(n-lag))))
                    covariance=op(tag+'_COV','DIV',op(tag+'_COVSUM','FSUM',*(op(tag+'_P'+str(i),'MUL',demeaned[i],demeaned[i+lag]) for i in range(n-lag))),float(n))
                    variance=op(tag+'_VAR','ADD',variance,op(tag+'_CONTRIB','MUL',op(tag+'_TWOW','MUL',2.0,weight),covariance))
                variances.append(maximum((variance,)))
            valid=[];standardized=[];thresholds=[]
            for j,(center,variance) in enumerate(zip(means,variances)):
                tag='T'+str(j)
                work._consumed["comparisons"] += 1
                if variance<=0:
                    work._consumed["comparisons"] += 1
                    work._require(center <= 0.0, 'LP03_SPA_POSITIVE_MEAN_ZERO_LONG_RUN_VARIANCE')
                    valid.append(False);standardized.append(None);thresholds.append(None);continue
                twice_variance_per_observation=op(tag+'_TWOVAR','MUL',op(tag+'_VARPER','DIV',variance,float(n)),2.0)
                inner_log=op(tag+'_LOG_N','LOG',float(n));outer_log=op(tag+'_LOG_LOG_N','LOG',inner_log)
                threshold=-op(tag+'_ROOT_THRESHOLD','SQRT',op(tag+'_THRESHOLD_PRODUCT','MUL',twice_variance_per_observation,outer_log))
                work._consumed["comparisons"] += 1
                thresholds.append(bits(threshold));valid.append(center>=threshold)
                standardized.append(op(tag+'_STANDARDIZED','DIV',op(tag+'_PRODUCT','MUL',op(tag+'_ROOT_N','SQRT',float(n)),center),op(tag+'_ROOT_VAR','SQRT',variance)))
            statistic=maximum(v for v in standardized if v is not None)
            recentered=[center if flag else 0.0 for center,flag in zip(means,valid)]
            # Unlike M15's all-zero branch, SPA constructs the original replay and
            # selects the whole time sample even when no column has positive variance.
            replay=_EvidenceBootstrapReplayV1(work,seed=seed,input_json=input_json.decode('utf-8'),environment_json=environment_json)
            draws=[];indices=[];simulated=[]
            def draw(method,rep,pos,threshold):
                actual,row=replay._draw_v1(method,n.bit_length() if method=='GETRANDBITS' else 53,
                    replicate=rep,position=pos,**(dict(population=n) if method=='GETRANDBITS' else dict(threshold=threshold)))
                work._require(len(deterministic_json(row).encode('utf-8'))<=180,'LP03_SPA_DRAW_BYTE_BOUND')
                draws.append(row)
                return actual
            def pick(rep,pos,threshold):
                while True:
                    value=draw('GETRANDBITS',rep,pos,threshold)
                    if value<n:return value
            for rep in range(reps):
                tag='R'+str(rep);threshold=op(tag+'_RESTART','DIV',1.0,block)
                current=pick(rep,0,threshold);sample=[current]
                for pos in range(1,n):
                    current=pick(rep,pos,threshold) if draw('RANDOM_U53',rep,pos,threshold)<threshold else (current+1)%n
                    sample.append(current)
                indices.append(tuple(sample));statistics=[]
                for j,(column,center,variance) in enumerate(zip(columns,recentered,variances)):
                    work._consumed["comparisons"] += 1
                    if variance<=0:continue
                    label=tag+'_C'+str(j)
                    root=op(label+'_ROOT_N','SQRT',float(n))
                    sampled=op(label+'_MEAN','DIV',op(label+'_SUM','FSUM',*(column[i] for i in sample)),float(n))
                    numerator=op(label+'_NUM','MUL',root,op(label+'_CENTER','SUB',sampled,center))
                    statistics.append(op(label+'_STAT','DIV',numerator,op(label+'_ROOT_VAR','SQRT',variance)))
                simulated.append(maximum(statistics))
            work._consumed["comparisons"] += len(simulated)
            exceedances=sum(value>=statistic for value in simulated)
            probability=op('PLUS_ONE_P_VALUE','DIV',float(1+exceedances),float(reps+1))
            model=dict(statistic=statistic,p_value=probability,reject=probability<=alpha,candidate_means=means,
                long_run_variances=variances,consistent_valid_columns=valid,simulated_statistics=simulated,recenter_variant=variant)
            work._consumed["comparisons"] += 1
            for output in (raw, expected):
                for value in (output["statistic"], output["p_value"], *output["candidate_means"],
                        *output["long_run_variances"], *output["simulated_statistics"]):
                    observed(value)
                work._require(deterministic_json(output) == deterministic_json(model), "LP03_SPA_ORDERED_OUTPUT_MISMATCH")
            work._require(raw_json == expected_json and deterministic_json(projected_value) == raw_json.decode("utf-8"),
                "LP03_SPA_RAW_EXPECTATION_PROJECTION_MISMATCH")
            summary = dict(work._emit(dict(statistic_bits=bits(statistic), p_value_bits=bits(probability),
                reject_flag=int(model["reject"]), seed=seed, replicates=replicates, observations=count, candidates=candidates,
                exceedances=exceedances, typed_input_json=input_json.decode("utf-8"),
                original_raw_json=raw_json.decode("utf-8"), preregistered_raw_json=expected_json.decode("utf-8"),
                environment_json=environment_json)))
            proof = dict(profile="ORDERED_MT19937_HANSEN_SPA_COMPACT_CELLS_MODEL_V1",
                intermediate_observation_scope="ALL_FORMULA_INDICES_AND_ARITHMETIC_DERIVED_NOT_OBSERVED",
                replay_observation_scope="ORIGINAL_REVIEW_REPLAY_METHOD_RETURNS_ONLY",
                statistical_authority="NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION",
                model_provenance="CPYTHON_RANDOM_INTEGER_SEED_AND_DERIVED_LIBM_CELLS_NOT_COMPILER_BINARY_ATTESTATION",
                cell_candidates=tuple(cells), log_certificates=tuple(log_certificates), draws=tuple(draws), indices=tuple(indices),
                oriented_matrix_bits=tuple(tuple(bits(value) for value in row) for row in matrix),
                consistency_threshold_bits=tuple(thresholds), summary=summary)
            replay._complete_v1(proof)
            work._assert_bootstrap_custody_v1()
            work._require(len(work._bootstrap_invocations) == len(original_replays) + 1
                and all(work._bootstrap_invocations[index] is original for index, original in enumerate(original_replays))
                and work._bootstrap_invocations[-1][0] is replay
                and work.consumed["random_draws"] == original_draw_count + len(draws),
                "LP03_SPA_ORIGINAL_REPLAY_ROSTER_CHANGED")
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_reality_check_v1(input_json, raw_json, expected_json, projected_value, *, expected_environment, work):
        """Finite complete-column M15 model, never family/significance authority.

        This consumes model input columns only. A runtime source route must
        separately prove the original complete material trial-family custody.
        Native formula intermediates are derived, never claimed as observed.
        """
        from math import isfinite, nextafter, inf, copysign, isqrt
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1, _EvidenceBootstrapReplayV1
        from .specification import decode_evidence_raw_output_v1
        from .evidence_execution import _worker_environment_v1
        from .models import EvidenceEnvironmentIdentityV1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_REALITY_CHECK_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-15", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-15", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-15", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            values, sign, seed, replicates, block, alpha = (inputs[name] for name in (
                "loss_differentials", "sign_convention", "seed", "replicates", "expected_block_length", "alpha"))
            positive = "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER"
            negative = "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"
            work._require(type(values) is tuple and 2 <= len(values) <= 4
                and type(values[0]) is tuple and 1 <= len(values[0]) <= 2
                and all(type(row) is tuple and len(row) == len(values[0]) for row in values)
                and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for row in values for value in row)
                and type(sign) is str and sign in (positive, negative)
                and type(block) is float and isfinite(block) and 1.0 <= block <= len(values)
                and type(seed) is int and seed.bit_length() <= 256
                and type(replicates) is int and 1 <= replicates <= 4 and len(values) * replicates <= 16
                and type(alpha) is float and isfinite(alpha) and 0.0 < alpha < 1.0
                and type(projected_value) is MappingProxyType and set(projected_value) == set(raw)
                and type(projected_value["candidate_means"]) is type(projected_value["simulated_statistics"]) is tuple,
                "LP03_REALITY_CHECK_REVIEW_TYPED_DOMAIN")
            work._require(type(expected_environment) is EvidenceEnvironmentIdentityV1
                and _worker_environment_v1() == expected_environment, "LP03_REALITY_CHECK_ENVIRONMENT_MISMATCH")
            environment_json = deterministic_json(expected_environment)
            source_bytes = sum(len(value) for value in (input_json, raw_json, expected_json))
            count, candidates = len(values), len(values[0])
            max_cells = 3 * candidates + 1 + 4 * candidates * replicates + 2
            # Every possible bounded draw row is <=180 ASCII bytes; arithmetic
            # rows have <=4 operand bit strings and are <=240. Reserve emitted
            # fragments AND the full proof before constructing any replay.
            reserve = 2 * (64 * 180 + max_cells * 240 + 2 * source_bytes + 6 * len(environment_json.encode("utf-8")) + 2000)
            work._require(work.consumed["serialized_bytes"] + reserve <= work.limits["max_serialized_bytes"],
                "LP03_REALITY_CHECK_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(192 + 64 * 18 + max_cells * 12 + 32 <= 4096,
                "LP03_REALITY_CHECK_REVIEW_COMPLETE_NODE_LAYOUT")
            work._assert_bootstrap_custody_v1()
            original_replays = tuple(work._bootstrap_invocations)
            original_draw_count = work.consumed["random_draws"]
            def bits(value):
                return struct.pack(">d", value).hex()
            def ratio(value):
                work._require(type(value) is float and isfinite(value), "LP03_REALITY_CHECK_FINITE_CELL_REQUIRED")
                return work._binary64_ratio(value)
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_REALITY_CHECK_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            for value in (*(value for row in values for value in row), block, alpha):
                observed(value)
            work._exact(seed)
            work._exact(replicates)
            zero, two = work._fraction(0), work._fraction(2)
            cells, draws, indices, simulated = [], [], [], []
            def rounded(exact, *, negative_zero=False):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = (-0.0 if negative_zero else 0.0) if exact.numerator == 0 else float(exact)
                work._require(isfinite(candidate), "LP03_REALITY_CHECK_FINITE_CELL_REQUIRED")
                before, after = nextafter(candidate, -inf), nextafter(candidate, inf)
                low = work._divide(work._add(ratio(before), ratio(candidate)), two)
                high = work._divide(work._add(ratio(candidate), ratio(after)), two)
                even = int(bits(candidate), 16) & 1 == 0
                low_test, high_test = work._compare(exact, low), work._compare(exact, high)
                work._require((low_test > 0 or low_test == 0 and even)
                    and (high_test < 0 or high_test == 0 and even), "LP03_REALITY_CHECK_NEAREST_EVEN_CELL_UNPROVEN")
                return candidate
            def append(label, kind, operands, candidate):
                work._require(len(cells) < max_cells and len(label) <= 24 and len(operands) <= 4,
                    "LP03_REALITY_CHECK_REVIEW_COMPLETE_NODE_LAYOUT")
                row = dict(work._emit(dict(operation=label, kind=kind,
                    operands_json=deterministic_json(tuple(bits(value) for value in operands)), candidate=bits(candidate))))
                work._require(len(deterministic_json(row).encode("utf-8")) <= 240,
                    "LP03_REALITY_CHECK_CELL_BYTE_BOUND")
                cells.append(row)
                return candidate
            def op(label, kind, left, right):
                first, second = ratio(left), ratio(right)
                exact = {"ADD": work._add, "SUB": work._subtract, "MUL": work._multiply, "DIV": work._divide}[kind](first, second)
                left_sign, right_sign = copysign(1.0, left) < 0, copysign(1.0, right) < 0
                negative_zero = (left_sign != right_sign) if kind in ("MUL", "DIV") else (
                    left == right == 0.0 and left_sign and (right_sign if kind == "ADD" else not right_sign))
                return append(label, kind, (left, right), rounded(exact, negative_zero=negative_zero))
            def total(label, operands):
                # Under |x|<=1 and n<=4 no fsum intermediate can overflow.
                # Exact zero from fsum is +0; a nonzero negative underflow keeps
                # its rounded sign through the subsequent ordered division.
                exact = zero
                for value in operands:
                    exact = work._add(exact, ratio(value))
                return append(label, "FSUM", operands, rounded(exact))
            def square_root_count():
                # n in [2,4]. A fixed 2^-52 grid brackets sqrt(n); integer
                # midpoint squares choose the nearest-even representable cell.
                scaled = work._shift(count, 104)
                work._consumed["square_roots"] += 1
                root = isqrt(scaled)
                midpoint_integer = work._int_sum(work._int_product(2, root), 1)
                comparison = work._compare(work._fraction(work._int_product(4, scaled)),
                    work._fraction(work._int_product(midpoint_integer, midpoint_integer)))
                if comparison > 0 or comparison == 0 and root & 1:
                    root = work._int_sum(root, 1)
                candidate = rounded(work._fraction(root, work._shift(1, 52)))
                low = work._divide(work._add(ratio(nextafter(candidate, -inf)), ratio(candidate)), two)
                high = work._divide(work._add(ratio(candidate), ratio(nextafter(candidate, inf))), two)
                lo = work._compare(work._fraction(count), work._multiply(low, low))
                hi = work._compare(work._fraction(count), work._multiply(high, high))
                even = int(bits(candidate), 16) & 1 == 0
                work._require((lo > 0 or lo == 0 and even) and (hi < 0 or hi == 0 and even),
                    "LP03_REALITY_CHECK_SQRT_CELL_UNPROVEN")
                return append("SQRT_N", "SQRT", (float(count),), candidate)
            matrix = tuple(tuple(value if sign == positive else -value for value in row) for row in values)
            means = tuple(op("MEAN_" + str(column), "DIV",
                total("SUM_" + str(column), tuple(row[column] for row in matrix)), float(count)) for column in range(candidates))
            root = square_root_count()
            observed_statistics = tuple(op("OBSERVED_" + str(column), "MUL", root, mean) for column, mean in enumerate(means))
            def maximum(statistics):
                # Original max(0.0, max(...)) retains the first zero on ties.
                chosen, value = -1, 0.0
                for column, candidate in enumerate(statistics):
                    work._consumed["comparisons"] += 1
                    if candidate > value:
                        chosen, value = column, candidate
                return value, chosen
            statistic, observed_column = maximum(observed_statistics)
            all_zero = all(value == 0.0 for row in matrix for value in row)
            replay, selected, threshold, exceedances = None, [], None, -1
            if all_zero:
                branch = "ALL_ZERO_NO_RNG_CONSTRUCTION"
                simulated, p_value = [0.0] * replicates, 1.0
            else:
                branch = "COMPLETE_FAMILY_CENTERED_STATIONARY_REPLAY"
                threshold = op("RESTART_THRESHOLD", "DIV", 1.0, block)
                replay = _EvidenceBootstrapReplayV1(work, seed=seed, input_json=input_json.decode("utf-8"), environment_json=environment_json)
                def draw(kind, width, replicate, position):
                    actual, row = replay._draw_v1(kind, width, replicate=replicate, position=position,
                        **(dict(population=count) if kind == "GETRANDBITS" else dict(threshold=threshold)))
                    work._require(len(deterministic_json(row).encode("utf-8")) <= 180, "LP03_REALITY_CHECK_DRAW_BYTE_BOUND")
                    draws.append(row)
                    return actual
                def pick(replicate, position):
                    while True:
                        candidate = draw("GETRANDBITS", count.bit_length(), replicate, position)
                        if candidate < count:
                            return candidate
                exceedances = 0
                for replicate in range(replicates):
                    current = pick(replicate, 0)
                    row = [current]
                    for position in range(1, count):
                        uniform = draw("RANDOM_U53", 53, replicate, position)
                        current = pick(replicate, position) if uniform < threshold else (current + 1) % count
                        row.append(current)
                    indices.append(tuple(row))
                    statistics = []
                    for column, center in enumerate(means):
                        prefix = "REPLICATE_" + str(replicate)
                        sampled = total(prefix + "_SUM_" + str(column), tuple(matrix[index][column] for index in row))
                        mean = op(prefix + "_MEAN_" + str(column), "DIV", sampled, float(count))
                        recentered = op(prefix + "_CENTER_" + str(column), "SUB", mean, center)
                        statistics.append(op(prefix + "_STATISTIC_" + str(column), "MUL", root, recentered))
                    value, column = maximum(statistics)
                    simulated.append(value)
                    selected.append(column)
                    work._consumed["comparisons"] += 1
                    if value >= statistic:
                        exceedances = work._int_sum(exceedances, 1)
                p_value = op("PLUS_ONE_P_VALUE", "DIV", float(work._int_sum(exceedances, 1)), float(work._int_sum(replicates, 1)))
            work._consumed["comparisons"] += 1
            reject = p_value <= alpha
            model = dict(statistic=statistic, p_value=p_value, reject=reject, candidate_means=means,
                simulated_statistics=tuple(simulated), recenter_policy="CENTER_EACH_COMPLETE_MATERIAL_CANDIDATE_AT_ITS_SAMPLE_MEAN")
            for output in (raw, expected):
                for value in (output["statistic"], output["p_value"], *output["candidate_means"], *output["simulated_statistics"]):
                    observed(value)
                work._require(deterministic_json(output) == deterministic_json(model), "LP03_REALITY_CHECK_ORDERED_OUTPUT_MISMATCH")
            work._require(raw_json == expected_json and deterministic_json(projected_value) == raw_json.decode("utf-8"),
                "LP03_REALITY_CHECK_RAW_EXPECTATION_PROJECTION_MISMATCH")
            summary = dict(work._emit(dict(statistic_bits=bits(statistic), p_value_bits=bits(p_value), reject_flag=int(reject),
                seed=seed, replicates=replicates, observations=count, candidates=candidates,
                threshold_bits="NOT_EVALUATED" if threshold is None else bits(threshold), exceedances=exceedances,
                typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8"), environment_json=environment_json)))
            proof = dict(profile="ORDERED_MT19937_WHITE_REALITY_CHECK_MODEL_V1", branch=branch,
                intermediate_observation_scope="ALL_FORMULA_INDICES_AND_ARITHMETIC_DERIVED_NOT_OBSERVED",
                replay_observation_scope="NO_REPLAY_CONSTRUCTED" if replay is None else "ORIGINAL_REVIEW_REPLAY_METHOD_RETURNS_ONLY",
                statistical_authority="NO_EMPIRICAL_FAMILY_OR_SIGNIFICANCE_CERTIFICATION",
                model_provenance="CPYTHON_RANDOM_INTEGER_SEED_GETRANDBITS_RANDOM_MODEL_NOT_COMPILER_BINARY_ATTESTATION",
                draws=tuple(draws), indices=tuple(indices), oriented_matrix_bits=tuple(tuple(bits(value) for value in row) for row in matrix),
                observed_selected_column=observed_column, replicate_selected_columns=tuple(selected), cells=tuple(cells), summary=summary)
            if replay is not None:
                replay._complete_v1(proof)
            work._assert_bootstrap_custody_v1()
            work._require(len(work._bootstrap_invocations) == len(original_replays) + (0 if replay is None else 1)
                and all(work._bootstrap_invocations[index] is original for index, original in enumerate(original_replays))
                and (replay is None or work._bootstrap_invocations[-1][0] is replay)
                and work.consumed["random_draws"] == original_draw_count + len(draws),
                "LP03_REALITY_CHECK_ORIGINAL_REPLAY_ROSTER_CHANGED")
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_bootstrap_v1(input_json, raw_json, expected_json, projected_value, *, expected_environment, work):
        """Bounded ordered stationary-bootstrap model, never coverage authority.

        Replay RNG returns are observed only in this review-side replay. All
        formula indices, sums, divisions and Type-7 stages are derived; no
        intermediate observation inside the original native formula is claimed.
        """
        from math import isfinite, nextafter, inf, copysign
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1, _EvidenceBootstrapReplayV1
        from .specification import decode_evidence_raw_output_v1
        from .evidence_execution import _worker_environment_v1
        from .models import EvidenceEnvironmentIdentityV1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_BOOTSTRAP_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-14", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-14", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-14", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            values, block, seed, replicates, confidence, method = (inputs[name] for name in (
                "series", "expected_block_length", "seed", "replicates", "confidence", "interval_method"))
            work._require(type(values) is tuple and 2 <= len(values) <= 8
                and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for value in values)
                and type(block) is float and isfinite(block) and 1.0 <= block <= len(values)
                and type(seed) is int and seed.bit_length() <= 256
                and type(replicates) is int and 1 <= replicates <= 4 and len(values) * replicates <= 16
                and type(confidence) is float and isfinite(confidence) and 0.0 < confidence < 1.0
                and type(method) is str and method == "PERCENTILE_TYPE7"
                and type(projected_value) is MappingProxyType
                and set(projected_value) == set(raw) and type(projected_value["bootstrap_distribution"]) is tuple,
                "LP03_BOOTSTRAP_REVIEW_TYPED_DOMAIN")
            work._require(type(expected_environment) is EvidenceEnvironmentIdentityV1
                and _worker_environment_v1() == expected_environment, "LP03_BOOTSTRAP_ENVIRONMENT_MISMATCH")
            environment_json = deterministic_json(expected_environment)
            source_bytes = sum(len(value) for value in (input_json, raw_json, expected_json))
            # Closed ASCII number/token inputs. 64 draw rows <=220 bytes each,
            # 26 arithmetic rows <=300, and escaped original texts are bounded
            # before constructing the replay. Both fragments and full artifact
            # are included; no draw count truncation substitutes for exhaustion.
            reserve = 2 * (64 * 220 + 26 * 300 + 2 * source_bytes + 6 * len(environment_json.encode("utf-8")) + 2000)
            work._require(work.consumed["serialized_bytes"] + reserve <= work.limits["max_serialized_bytes"],
                "LP03_BOOTSTRAP_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(128 + 64 * 18 + 26 * 12 + 16 * 2 <= 4096,
                "LP03_BOOTSTRAP_REVIEW_COMPLETE_NODE_LAYOUT")
            def bits(value):
                return struct.pack(">d", value).hex()
            def ratio(value):
                work._require(type(value) is float and isfinite(value), "LP03_BOOTSTRAP_FINITE_CELL_REQUIRED")
                return work._binary64_ratio(value)
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_BOOTSTRAP_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            for value in (*values, block, confidence):
                observed(value)
            work._exact(seed)
            work._exact(replicates)
            zero, two = work._fraction(0), work._fraction(2)
            cells, draws, indices, distribution = [], [], [], []
            def rounded(exact, *, negative_zero=False):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = (-0.0 if negative_zero else 0.0) if exact.numerator == 0 else float(exact)
                work._require(isfinite(candidate), "LP03_BOOTSTRAP_FINITE_CELL_REQUIRED")
                before, after = nextafter(candidate, -inf), nextafter(candidate, inf)
                low = work._divide(work._add(ratio(before), ratio(candidate)), two)
                high = work._divide(work._add(ratio(candidate), ratio(after)), two)
                even = int(bits(candidate), 16) & 1 == 0
                low_test, high_test = work._compare(exact, low), work._compare(exact, high)
                work._require((low_test > 0 or low_test == 0 and even)
                    and (high_test < 0 or high_test == 0 and even), "LP03_BOOTSTRAP_NEAREST_EVEN_CELL_UNPROVEN")
                return candidate
            def append(label, kind, operands, candidate):
                work._require(len(cells) < 26 and len(label) <= 24 and len(operands) <= 8,
                    "LP03_BOOTSTRAP_REVIEW_COMPLETE_NODE_LAYOUT")
                row = dict(work._emit(dict(operation=label, kind=kind,
                    operands_json=deterministic_json(tuple(bits(value) for value in operands)), candidate=bits(candidate))))
                work._require(len(deterministic_json(row).encode("utf-8")) <= 300,
                    "LP03_BOOTSTRAP_CELL_BYTE_BOUND")
                cells.append(row)
                return candidate
            def op(label, kind, left, right):
                first, second = ratio(left), ratio(right)
                exact = {"ADD": work._add, "SUB": work._subtract, "MUL": work._multiply, "DIV": work._divide}[kind](first, second)
                left_sign, right_sign = copysign(1.0, left) < 0, copysign(1.0, right) < 0
                negative_zero = (left_sign != right_sign) if kind in ("MUL", "DIV") else (
                    left == right == 0.0 and left_sign and (right_sign if kind == "ADD" else not right_sign))
                return append(label, kind, (left, right), rounded(exact, negative_zero=negative_zero))
            def total(label, operands):
                # Under |x|<=1 and n<=8 no fsum intermediate can overflow.
                # Exact zero from fsum is +0; a nonzero negative underflow keeps
                # its rounded sign through the subsequent ordered division.
                exact = zero
                for value in operands:
                    exact = work._add(exact, ratio(value))
                return append(label, "FSUM", operands, rounded(exact))
            threshold = op("RESTART_THRESHOLD", "DIV", 1.0, block)
            replay = _EvidenceBootstrapReplayV1(work, seed=seed, input_json=input_json.decode("utf-8"),
                environment_json=environment_json)
            def draw(kind, width, replicate, position):
                actual, row = replay._draw_v1(kind, width, replicate=replicate, position=position,
                    **(dict(population=len(values)) if kind == "GETRANDBITS" else dict(threshold=threshold)))
                work._require(len(deterministic_json(row).encode("utf-8")) <= 220,
                    "LP03_BOOTSTRAP_DRAW_BYTE_BOUND")
                draws.append(row)
                return actual
            def pick(replicate, position):
                while True:
                    candidate = draw("GETRANDBITS", len(values).bit_length(), replicate, position)
                    if candidate < len(values):
                        return candidate
            for replicate in range(replicates):
                current = pick(replicate, 0)
                row = [current]
                for position in range(1, len(values)):
                    uniform = draw("RANDOM_U53", 53, replicate, position)
                    current = pick(replicate, position) if uniform < threshold else (current + 1) % len(values)
                    row.append(current)
                indices.append(tuple(row))
                sampled_sum = total("REPLICATE_SUM_" + str(replicate), tuple(values[index] for index in row))
                distribution.append(op("REPLICATE_MEAN_" + str(replicate), "DIV", sampled_sum, float(len(values))))
            alpha = op("ALPHA", "DIV", op("CONFIDENCE_COMPLEMENT", "SUB", 1.0, confidence), 2.0)
            sample_mean = op("SAMPLE_MEAN", "DIV", total("SAMPLE_SUM", values), float(len(values)))
            upper_probability = op("UPPER_PROBABILITY", "SUB", 1.0, alpha)
            order = tuple(sorted(range(replicates), key=lambda index: distribution[index]))
            selections = []
            def percentile(prefix, probability):
                position = op(prefix + "_POSITION", "MUL", probability, float(replicates - 1))
                exact_position = ratio(position)
                work._consumed["integer_operations"] += 1
                lower, remainder = divmod(exact_position.numerator, exact_position.denominator)
                upper = lower if remainder == 0 else lower + 1
                work._require(0 <= lower <= upper < replicates, "LP03_BOOTSTRAP_TYPE7_INDEX")
                selections.append((lower, upper))
                if lower == upper:
                    return distribution[order[lower]]
                weight = op(prefix + "_WEIGHT", "SUB", position, float(lower))
                complement = op(prefix + "_COMPLEMENT", "SUB", 1.0, weight)
                left = op(prefix + "_LEFT", "MUL", distribution[order[lower]], complement)
                right = op(prefix + "_RIGHT", "MUL", distribution[order[upper]], weight)
                return op(prefix + "_RESULT", "ADD", left, right)
            lower, upper = percentile("LOWER", alpha), percentile("UPPER", upper_probability)
            model = dict(sample_mean=sample_mean, lower=lower, upper=upper, bootstrap_distribution=tuple(distribution),
                seed=seed, replicates=replicates, expected_block_length=block, interval_method=method)
            for output in (raw, expected):
                for value in (output["sample_mean"], output["lower"], output["upper"], *output["bootstrap_distribution"]):
                    observed(value)
                work._require(deterministic_json(output) == deterministic_json(model), "LP03_BOOTSTRAP_ORDERED_OUTPUT_MISMATCH")
            work._require(raw_json == expected_json and deterministic_json(projected_value) == raw_json.decode("utf-8"),
                "LP03_BOOTSTRAP_RAW_EXPECTATION_PROJECTION_MISMATCH")
            summary = dict(work._emit(dict(sample_mean_bits=bits(sample_mean), lower_bits=bits(lower), upper_bits=bits(upper),
                seed=seed, replicates=replicates, threshold_bits=bits(threshold),
                typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8"), environment_json=environment_json)))
            proof = dict(profile="ORDERED_MT19937_STATIONARY_BOOTSTRAP_TYPE7_MODEL_V1",
                intermediate_observation_scope="ALL_FORMULA_INDICES_AND_ARITHMETIC_DERIVED_NOT_OBSERVED",
                replay_observation_scope="ORIGINAL_REVIEW_REPLAY_METHOD_RETURNS_ONLY",
                statistical_authority="NO_COVERAGE_OR_EMPIRICAL_CERTIFICATION",
                model_provenance="CPYTHON_RANDOM_INTEGER_SEED_GETRANDBITS_RANDOM_MODEL_NOT_COMPILER_BINARY_ATTESTATION",
                draws=tuple(draws), indices=tuple(indices), stable_order=order, percentile_indices=tuple(selections),
                cells=tuple(cells), summary=summary)
            replay._complete_v1(proof)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_deflated_sharpe_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Bounded ordered DSR source-model conformance, never trial support.

        Intermediate sqrt/erfc values are derived, not native observations.
        The exact erfc enclosure proves one RN source-model cell; it does not
        attest a platform libm implementation, coverage, or source authority.
        """
        import struct
        from math import isfinite, nextafter, inf, isqrt
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_DSR_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-18", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-18", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-18", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            estimate, reference = inputs["candidate_estimated_sharpe"], 0.0
            sharpes, effective = inputs["complete_material_trial_sharpes"], inputs["effective_independent_trial_count"]
            count = inputs["candidate_independent_equivalent_observations"]
            skewness, kurtosis = inputs["candidate_sample_skewness"], inputs["candidate_sample_non_excess_kurtosis"]
            # This finite conformance profile declares exact-conversion support
            # before arithmetic. It neither floors ESS nor supplies assumptions.
            work._require(type(count) is int and 2 <= count <= 2**53
                and type(sharpes) is tuple and 2 <= len(sharpes) <= 5
                and all(type(value) is float and isfinite(value) and -1.0 <= value <= 1.0 for value in sharpes)
                and type(effective) is float and isfinite(effective) and 1.0 < effective <= len(sharpes)
                and all(type(value) is float and isfinite(value) for value in (estimate, skewness, kurtosis))
                and kurtosis >= 1.0, "LP03_DSR_REVIEW_TYPED_DOMAIN")
            max_cells = 128
            source_bytes = sum(len(value) for value in (input_json, raw_json, expected_json))
            base_reserve = 2 * (max_cells * 52 + 6 * source_bytes + 3000 + 4 * 900)
            work._require(work.consumed["serialized_bytes"] + base_reserve <= work.limits["max_serialized_bytes"],
                "LP03_DSR_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(256 + max_cells + 4 * 24 <= 4096, "LP03_DSR_REVIEW_COMPLETE_NODE_LAYOUT")
            def bits(value):
                return struct.pack(">d", value).hex()
            def ratio(value):
                work._require(type(value) is float and isfinite(value), "LP03_DSR_FINITE_CELL_REQUIRED")
                return work._binary64_ratio(value)
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_DSR_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            def emitted(values):
                result = work._emit(values)
                return {name: dict(value) if type(value) is MappingProxyType else value for name, value in result.items()}
            zero, one, two = work._fraction(0), work._fraction(1), work._fraction(2)
            original_count = work._exact(count)
            for value in (*sharpes, effective, estimate, skewness, kurtosis): observed(value)
            cells = []
            def cell(candidate, lower, upper, *, squared=False):
                previous, following = nextafter(candidate, -inf), nextafter(candidate, inf)
                work._require(isfinite(candidate) and isfinite(previous) and isfinite(following),
                    "LP03_DSR_FINITE_CELL_REQUIRED")
                actual, before, after = ratio(candidate), ratio(previous), ratio(following)
                low_mid = work._divide(work._add(before, actual), two)
                high_mid = work._divide(work._add(actual, after), two)
                even = int(bits(candidate), 16) & 1 == 0
                if squared:
                    work._require(work._compare(lower, zero) >= 0 and work._compare(actual, zero) >= 0,
                        "LP03_DSR_SQRT_DOMAIN")
                    low_comparison = 1 if work._compare(low_mid, zero) < 0 else work._compare(lower, work._multiply(low_mid, low_mid))
                    high_comparison = work._compare(upper, work._multiply(high_mid, high_mid))
                else:
                    low_comparison, high_comparison = work._compare(lower, low_mid), work._compare(upper, high_mid)
                work._require(work._compare(lower, upper) <= 0
                    and (low_comparison > 0 or low_comparison == 0 and even)
                    and (high_comparison < 0 or high_comparison == 0 and even),
                    "LP03_DSR_NEAREST_EVEN_CELL_UNPROVEN")
                return actual
            def append(label, kind, left, right, candidate):
                work._require(len(cells) < max_cells and len(label) <= 24,
                    "LP03_DSR_REVIEW_COMPLETE_NODE_LAYOUT")
                row = emitted(dict(position=len(cells), candidate=bits(candidate)))
                work._require(len(deterministic_json(row).encode("utf-8")) <= 52, "LP03_DSR_CELL_BYTE_BOUND")
                # This profile reconstructs every original operation/operand
                # from the complete ordered inputs and preceding cell bits.
                cells.append(row["candidate"])
                return candidate
            def rounded(exact, *, negative_zero=False):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                try:
                    candidate = -0.0 if exact == 0 and negative_zero else float(exact)
                except OverflowError:
                    work._require(False, "LP03_DSR_FINITE_CELL_REQUIRED")
                cell(candidate, exact, exact)
                return candidate
            def op(label, kind, left, right):
                first, second = ratio(left), ratio(right)
                exact = {"ADD": work._add, "SUB": work._subtract, "MUL": work._multiply, "DIV": work._divide}[kind](first, second)
                # Rational zero does not determine the IEEE signed-zero bit.
                # Preserve original RN signs, including underflow from nonzero.
                left_negative, right_negative = int(bits(left), 16) >> 63, int(bits(right), 16) >> 63
                negative_zero = bool(left_negative ^ right_negative) if kind in ("MUL", "DIV") else (
                    left == 0.0 and right == 0.0 and bool(left_negative) and
                    (bool(right_negative) if kind == "ADD" else not right_negative))
                return append(label, kind, left, right, rounded(exact, negative_zero=negative_zero))
            def square_root(label, value):
                original = ratio(value)
                work._require(work._compare(original, zero) >= 0, "LP03_DSR_SQRT_DOMAIN")
                if work._compare(original, zero) == 0:
                    candidate = 0.0
                else:
                    # floor(log2(original)) from bounded integer comparison.
                    exponent = work._int_sum(original.numerator.bit_length(), -original.denominator.bit_length())
                    power = work._fraction(work._shift(1, exponent)) if exponent >= 0 else work._fraction(1, work._shift(1, -exponent))
                    if work._compare(original, power) < 0:
                        exponent = work._int_sum(exponent, -1)
                    quantum = max(-1074, exponent // 2 - 52)
                    scale = work._fraction(work._shift(1, 2 * quantum)) if quantum >= 0 else work._fraction(1, work._shift(1, -2 * quantum))
                    scaled = work._divide(original, scale)
                    work._bits(max(scaled.numerator.bit_length(), scaled.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient = scaled.numerator // scaled.denominator
                    work._bits(quotient.bit_length())
                    work._consumed["square_roots"] += 1
                    root = isqrt(quotient)
                    midpoint = work._fraction(work._int_sum(work._int_product(2, root), 1), 2)
                    comparison = work._compare(scaled, work._multiply(midpoint, midpoint))
                    if comparison > 0 or comparison == 0 and root & 1:
                        root = work._int_sum(root, 1)
                    step = work._fraction(work._shift(1, quantum)) if quantum >= 0 else work._fraction(1, work._shift(1, -quantum))
                    candidate = rounded(work._multiply(work._fraction(root), step))
                cell(candidate, original, original, squared=True)
                return append(label, "SQRT", value, 0.0, candidate)
            def atan_interval(denominator):
                x = work._fraction(1, denominator)
                square, power, partial = work._multiply(x, x), x, zero
                for index in range(64):
                    term = work._divide(power, work._fraction(work._int_sum(work._int_product(2, index), 1)))
                    partial = work._subtract(partial, term) if index & 1 else work._add(partial, term)
                    power = work._multiply(power, square)
                return partial, work._add(partial, work._divide(power, work._fraction(129)))
            def sqrt_pi_interval():
                first_low, first_high = atan_interval(5)
                second_low, second_high = atan_interval(239)
                low = work._subtract(work._multiply(work._fraction(16), first_low), work._multiply(work._fraction(4), second_high))
                high = work._subtract(work._multiply(work._fraction(16), first_high), work._multiply(work._fraction(4), second_low))
                upper = work._sqrt_upper(high)
                numerator = work._shift(low.numerator, 256)
                work._bits(max(numerator.bit_length(), low.denominator.bit_length()))
                work._consumed["integer_operations"] += 1
                quotient = numerator // low.denominator
                work._bits(quotient.bit_length())
                work._consumed["square_roots"] += 1
                root = isqrt(quotient)
                lower = work._fraction(root, work._shift(1, 128))
                work._require(work._compare(work._multiply(lower, lower), low) <= 0
                    and work._compare(low, high) <= 0 and work._compare(lower, one) > 0,
                    "LP03_DSR_PI_SQRT_ENCLOSURE")
                return lower, upper
            def erfc_enclosure(argument):
                original = ratio(argument)
                magnitude = work._subtract(zero, original) if work._compare(original, zero) < 0 else original
                work._require(work._compare(magnitude, two) <= 0,
                    "LP03_DSR_DECLARED_ERFC_ARGUMENT_REGION_UNAVAILABLE")
                sqrt_low, sqrt_high = sqrt_pi_interval()
                # Finite declared regions prevent tiny binary64 denominators
                # from entering 129th powers. All products are still preflighted.
                if work._compare(magnitude, work._fraction(1, work._shift(1, 60))) <= 0:
                    lower, upper = work._subtract(one, work._multiply(two, magnitude)), one
                    branch, terms = "SMALL_ARGUMENT", 0
                else:
                    square, power, factorial, partial = work._multiply(magnitude, magnitude), magnitude, 1, zero
                    for index in range(64):
                        divisor = work._int_product(factorial, work._int_sum(work._int_product(2, index), 1))
                        term = work._divide(power, work._fraction(divisor))
                        partial = work._subtract(partial, term) if index & 1 else work._add(partial, term)
                        power = work._multiply(power, square)
                        factorial = work._int_product(factorial, work._int_sum(index, 1))
                    remainder = work._divide(power, work._fraction(work._int_product(factorial, 129)))
                    integral_low = partial if work._compare(partial, zero) >= 0 else zero
                    integral_high = work._add(partial, remainder)
                    work._require(work._compare(integral_low, integral_high) <= 0, "LP03_DSR_INTEGRAL_ENCLOSURE")
                    erf_low = work._divide(work._multiply(two, integral_low), sqrt_high)
                    erf_high = work._divide(work._multiply(two, integral_high), sqrt_low)
                    if work._compare(erf_low, zero) < 0: erf_low = zero
                    if work._compare(erf_high, one) > 0: erf_high = one
                    work._require(work._compare(erf_low, erf_high) <= 0, "LP03_DSR_ERF_ENCLOSURE")
                    lower, upper = work._subtract(one, erf_high), work._subtract(one, erf_low)
                    branch, terms = "EXP_INTEGRAL_64", 64
                if work._compare(original, zero) < 0:
                    lower, upper = work._subtract(two, upper), work._subtract(two, lower)
                scale = work._shift(1, 128)
                def outward(value, ceiling):
                    numerator = work._int_product(value.numerator, scale)
                    work._bits(max(numerator.bit_length(), value.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient, remainder = divmod(numerator, value.denominator)
                    return work._int_sum(quotient, 1) if ceiling and remainder else quotient
                low_integer, high_integer = outward(lower, False), outward(upper, True)
                compact_low, compact_high = work._fraction(low_integer, scale), work._fraction(high_integer, scale)
                work._require(work._compare(compact_low, lower) <= 0 and work._compare(lower, upper) <= 0
                    and work._compare(upper, compact_high) <= 0, "LP03_DSR_OUTWARD_ENCLOSURE")
                candidate = rounded(work._divide(work._add(compact_low, compact_high), two))
                cell(candidate, compact_low, compact_high)
                certificate = emitted(dict(argument_bits=bits(argument), derived_erfc_bits=bits(candidate),
                    lower_numerator=low_integer, upper_numerator=high_integer, fraction_bits=128,
                    branch=branch, integral_terms=terms, machin_terms_per_series=64, sqrt_fraction_bits=128,
                    interpretation="DERIVED_UNOBSERVED_ERFC_SOURCE_MODEL_CELL"))
                return candidate, certificate
            inverse_certificates, log_certificates = [], []
            def negate(label, value):
                exact = work._subtract(zero, ratio(value))
                return append(label, "NEGATE", value, 0.0, rounded(exact, negative_zero=not bool(int(bits(value), 16) >> 63)))
            def polynomial(label, coefficients, value):
                result = coefficients[0]
                for index, coefficient in enumerate(coefficients[1:], 1):
                    result = op(label + str(index) + "M", "MUL", result, value)
                    result = op(label + str(index) + "A", "ADD", result, coefficient)
                return result
            def logarithm(label, value):
                # Original tail sequence is log(r), unary negation, then sqrt.
                # Certify negative log output separately from the sign flip.
                positive_low, positive_high = work._log_enclosure(work._divide(one, ratio(value)))
                lower, upper = work._subtract(zero, positive_high), work._subtract(zero, positive_low)
                candidate = rounded(work._divide(work._add(lower, upper), two))
                cell(candidate, lower, upper)
                scale = work._shift(1, 128)
                def outward(bound, ceiling):
                    numerator = work._int_product(bound.numerator, scale)
                    work._bits(max(numerator.bit_length(), bound.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient, remainder = divmod(numerator, bound.denominator)
                    return work._int_sum(quotient, 1) if ceiling and remainder else quotient
                low_integer, high_integer = outward(lower, False), outward(upper, True)
                compact_low, compact_high = work._fraction(low_integer, scale), work._fraction(high_integer, scale)
                work._require(work._compare(compact_low, lower) <= 0 and work._compare(upper, compact_high) <= 0,
                    "LP03_DSR_LOG_OUTWARD_ENCLOSURE")
                cell(candidate, compact_low, compact_high)
                work._require(len(log_certificates) < 2, "LP03_DSR_LOG_CERTIFICATE_CAPACITY")
                certificate = emitted(dict(position=len(cells), input_bits=bits(value), candidate_bits=bits(candidate),
                    lower_numerator=low_integer, upper_numerator=high_integer, fraction_bits=128, terms_per_series=64))
                work._require(len(deterministic_json(certificate).encode("utf-8")) <= 900, "LP03_DSR_LOG_CERTIFICATE_BYTES")
                log_certificates.append(certificate)
                return append(label, "LOG", value, 0.0, candidate)
            def inverse_normal(label, probability):
                work._consumed["comparisons"] += 2
                above_zero, below_one = probability > 0.0, probability < 1.0
                work._require(above_zero and below_one, "LP03_DSR_ROUNDED_QUANTILE_DOMAIN")
                q = op(label + "Q", "SUB", probability, 0.5)
                work._consumed["comparisons"] += 1
                if abs(q) <= 0.425:
                    branch = "CENTRAL"
                    squared = op(label + "Q2", "MUL", q, q)
                    r = op(label + "R", "SUB", 0.180625, squared)
                    numerator_coefficients, denominator_coefficients = ((2509.0809287301227, 33430.57558358813, 67265.7709270087, 45921.95393154987, 13731.69376550946, 1971.5909503065513, 133.14166789178438, 3.3871328727963665), (5226.495278852854, 28729.085735721943, 39307.89580009271, 21213.794301586597, 5394.196021424751, 687.1870074920579, 42.31333070160091, 1.0))
                    numerator = polynomial(label + "N", numerator_coefficients, r)
                    numerator = op(label + "NUMQ", "MUL", numerator, q)
                    denominator = polynomial(label + "D", denominator_coefficients, r)
                    result = op(label + "QUOTIENT", "DIV", numerator, denominator)
                else:
                    work._consumed["comparisons"] += 1
                    r = probability if q <= 0.0 else op(label + "TAIL", "SUB", 1.0, probability)
                    logged = logarithm(label + "LOG", r)
                    r = square_root(label + "SQRT", negate(label + "NEGLOG", logged))
                    work._consumed["comparisons"] += 1
                    if r <= 5.0:
                        branch = "TAIL_LE_FIVE"
                        r = op(label + "SHIFT", "SUB", r, 1.6)
                        numerator_coefficients, denominator_coefficients = ((0.0007745450142783414, 0.022723844989269184, 0.2417807251774506, 1.2704582524523684, 3.6478483247632045, 5.769497221460691, 4.630337846156546, 1.4234371107496835), (1.0507500716444169e-09, 0.0005475938084995345, 0.015198666563616457, 0.14810397642748008, 0.6897673349851, 1.6763848301838038, 2.053191626637759, 1.0))
                    else:
                        branch = "TAIL_GT_FIVE"
                        r = op(label + "SHIFT", "SUB", r, 5.0)
                        numerator_coefficients, denominator_coefficients = ((2.0103343992922881e-07, 2.7115555687434876e-05, 0.0012426609473880784, 0.026532189526576124, 0.29656057182850487, 1.7848265399172913, 5.463784911164114, 6.657904643501103), (2.0442631033899397e-15, 1.421511758316446e-07, 1.8463183175100548e-05, 0.0007868691311456133, 0.014875361290850615, 0.1369298809227358, 0.599832206555888, 1.0))
                    numerator = polynomial(label + "N", numerator_coefficients, r)
                    denominator = polynomial(label + "D", denominator_coefficients, r)
                    result = op(label + "QUOTIENT", "DIV", numerator, denominator)
                    work._consumed["comparisons"] += 1
                    if q < 0.0: result = negate(label + "NEGSIGN", result)
                result = op(label + "SCALE", "MUL", result, 1.0)
                result = op(label + "LOCATION", "ADD", 0.0, result)
                work._require(len(inverse_certificates) < 2, "LP03_DSR_INVERSE_CERTIFICATE_CAPACITY")
                certificate = emitted(dict(call=label, probability_bits=bits(probability), q_bits=bits(q),
                    branch=branch, result_bits=bits(result), interpretation="DERIVED_AS241_SOURCE_MODEL_NOT_EXACT_QUANTILE"))
                work._require(len(deterministic_json(certificate).encode("utf-8")) <= 900, "LP03_DSR_INVERSE_CERTIFICATE_BYTES")
                inverse_certificates.append(certificate)
                return result
            def exact_sum(label, values):
                total = zero
                for value in values: total = work._add(total, ratio(value))
                return append(label, "FSUM_SOURCE_MODEL", 0.0, 0.0, rounded(total))
            size_float = rounded(work._fraction(len(sharpes)))
            mean = op("TRIAL_MEAN", "DIV", exact_sum("TRIAL_FSUM", sharpes), size_float)
            # The original variance helper recomputes its own mean.
            center = op("VARIANCE_CENTER", "DIV", exact_sum("CENTER_FSUM", sharpes), size_float)
            squared_differences = []
            for index, value in enumerate(sharpes):
                difference = op("TRIAL_DIFF" + str(index), "SUB", value, center)
                # Distinct original **2 operation; its exact RN model is a
                # square, not an observed native multiply/pow intermediate.
                exact = work._multiply(ratio(difference), ratio(difference))
                squared_differences.append(append("TRIAL_POW2" + str(index), "POW2_SOURCE_MODEL", difference, 2.0, rounded(exact)))
            variance = op("TRIAL_VARIANCE", "DIV", exact_sum("SQUARES_FSUM", squared_differences),
                rounded(work._fraction(work._int_sum(len(sharpes), -1))))
            # Preserve Python's original left-to-right evaluation order, and
            # both inverse-CDF calls even for zero original trial variance.
            variance_root = square_root("VARIANCE_SQRT", variance)
            gamma = 0.5772156649015329
            complement_gamma = op("ONE_MINUS_GAMMA", "SUB", 1.0, gamma)
            first_probability = op("P1", "SUB", 1.0, op("P1_DIVISION", "DIV", 1.0, effective))
            first_quantile = inverse_normal("Q1", first_probability)
            first_term = op("FIRST_TERM", "MUL", complement_gamma, first_quantile)
            e_count = op("COUNT_TIMES_E", "MUL", effective, 2.718281828459045)
            second_probability = op("P2", "SUB", 1.0, op("P2_DIVISION", "DIV", 1.0, e_count))
            second_quantile = inverse_normal("Q2", second_probability)
            second_term = op("SECOND_TERM", "MUL", gamma, second_quantile)
            threshold_sum = op("THRESHOLD_SUM", "ADD", first_term, second_term)
            threshold_factor = op("THRESHOLD_FACTOR", "MUL", variance_root, threshold_sum)
            reference = op("EXPECTED_MAXIMUM", "ADD", mean, threshold_factor)
            skew_estimate = op("SKEW_ESTIMATE", "MUL", skewness, estimate)
            initial = op("ONE_MINUS_SKEW", "SUB", 1.0, skew_estimate)
            excess = op("KURTOSIS_MINUS_ONE", "SUB", kurtosis, 1.0)
            quarter = op("KURTOSIS_QUARTER", "DIV", excess, 4.0)
            first_estimate = op("KURTOSIS_ESTIMATE", "MUL", quarter, estimate)
            second_estimate = op("KURTOSIS_ESTIMATE2", "MUL", first_estimate, estimate)
            denominator = op("DENOMINATOR_SQUARED", "ADD", initial, second_estimate)
            work._consumed["comparisons"] += 1
            work._require(denominator > 0.0, "LP03_DSR_POSITIVE_DENOMINATOR_REQUIRED")
            difference = op("ESTIMATE_DIFFERENCE", "SUB", estimate, reference)
            count_minus_one = work._int_sum(original_count.numerator, -1)
            support_root = square_root("SUPPORT_SQRT", rounded(work._fraction(count_minus_one)))
            numerator = op("SCORE_NUMERATOR", "MUL", difference, support_root)
            denominator_root = square_root("DENOMINATOR_SQRT", denominator)
            score = op("ZSCORE", "DIV", numerator, denominator_root)
            complement = op("CDF_LOCATION_MINUS", "SUB", 0.0, score)
            scale = op("CDF_SIGMA_SQRT2", "MUL", 1.0, 1.4142135623730951)
            argument = op("CDF_ERFC_ARGUMENT", "DIV", complement, scale)
            erfc, certificate = erfc_enclosure(argument)
            probability = op("CDF_HALF", "MUL", 0.5, erfc)
            for field, derived in (("deflated_sharpe_ratio", probability), ("expected_maximum_sharpe_threshold", reference),
                ("trial_mean_sharpe", mean), ("trial_sharpe_variance", variance)):
                for actual in (raw[field], expected[field]):
                    observed(actual)
                    work._require(bits(actual) == bits(derived), "LP03_DSR_RAW_OR_EXPECTATION_MISMATCH")
            observed(projected_value)
            work._require(bits(projected_value) == bits(probability), "LP03_DSR_PROJECTION_MISMATCH")
            work._require(raw_json == expected_json, "LP03_DSR_RAW_EXPECTATION_WIRE_MISMATCH")
            summary = emitted(dict(independent_equivalent_observations=count, count_minus_one=count_minus_one,
                effective_trial_count_bits=bits(effective), complete_trial_count=len(sharpes),
                score_bits=bits(score), probability_bits=bits(probability),
                typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8")))
            proof = dict(profile="ORDERED_BINARY64_DSR_AS241_ERFC_MODEL_CONFORMANCE_V1",
                intermediate_observation_scope="ALL_FSUM_POW_SQRT_AS241_ERFC_AND_ARITHMETIC_STAGES_DERIVED_NOT_OBSERVED",
                statistical_authority="NO_INDEPENDENCE_SUPPORT_OR_STATISTICAL_COVERAGE_CERTIFICATION",
                model_provenance="CPYTHON_V3_14_6_DSR_AS241_ERFC_SOURCE_MODEL_NOT_LIBM_BINARY_ATTESTATION",
                declared_support_maximum=2**53, declared_erfc_argument_magnitude_maximum=2,
                declared_complete_trial_capacity=5, declared_trial_sharpe_magnitude_maximum=1,
                inverse_certificates=tuple(inverse_certificates), log_certificates=tuple(log_certificates),
                erfc_enclosure=certificate, cell_candidates=tuple(cells), summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_recorded_ope_v1(math_id, input_json, raw_json, expected_json, *, work):
        """Reconstruct the ordered original recorded OPE scores and nested switch selection."""
        import math
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1

        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(math_id in ("MATH-22","MATH-23","MATH-24","MATH-25")
                and all(type(value) is bytes and 0 < len(value) <= 65536 for value in (input_json,raw_json,expected_json)),
                "LP03_OPE_REVIEW_BOUNDED_WIRE")
            inputs = decode_evidence_public_invocation_inputs_v1(math_id,input_json,maximum_bytes=65536,maximum_nodes=4096)
            actual = decode_evidence_raw_output_v1(math_id,raw_json,maximum_bytes=65536,maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1(math_id,expected_json,maximum_bytes=65536,maximum_nodes=4096)
            zero, one = 0.0, 1.0
            tolerance = 1e-12

            def represented(value):
                work._require(type(value) is float and math.isfinite(value), "LP03_OPE_REVIEW_ORIGINAL_BINARY64")
                work._consumed["input_values"] += 1
                work._binary64_ratio(value, original_input=True)
                return value

            def round_to_binary64(value, *, negative_zero=False):
                work._bits(max(abs(value.numerator).bit_length(), value.denominator.bit_length(), 1075))
                result = -0.0 if value == 0 and negative_zero else float(value)
                work._require(math.isfinite(result), "LP03_OPE_REVIEW_BINARY64_OVERFLOW")
                ratio = work._binary64_ratio(result)
                previous, next_value = math.nextafter(result, -math.inf), math.nextafter(result, math.inf)
                two = work._fraction(2)
                if math.isfinite(previous):
                    lower = work._divide(work._add(work._binary64_ratio(previous), ratio), two)
                else:
                    spacing = work._subtract(work._binary64_ratio(next_value), ratio)
                    lower = work._subtract(ratio, work._divide(spacing, two))
                if math.isfinite(next_value):
                    upper = work._divide(work._add(work._binary64_ratio(next_value), ratio), two)
                else:
                    spacing = work._subtract(ratio, work._binary64_ratio(previous))
                    upper = work._add(ratio, work._divide(spacing, two))
                even = int.from_bytes(struct.pack(">d", result), "big") & 1 == 0
                low, high = work._compare(lower, value), work._compare(value, upper)
                work._require((low < 0 or low == 0 and even) and (high < 0 or high == 0 and even),
                    "LP03_OPE_REVIEW_ROUND_NEAREST_EVEN")
                return result

            def multiply_or_divide(left, right, operation):
                rational = operation(work._binary64_ratio(left), work._binary64_ratio(right))
                negative_zero = math.copysign(1.0, left) != math.copysign(1.0, right)
                return round_to_binary64(rational, negative_zero=negative_zero)

            def add(left, right):
                rational = work._add(work._binary64_ratio(left), work._binary64_ratio(right))
                negative_zero = math.copysign(1.0, left) < 0 and math.copysign(1.0, right) < 0
                return round_to_binary64(rational, negative_zero=negative_zero)

            def mul(left, right):
                return multiply_or_divide(left, right, work._multiply)

            def div(left, right):
                return multiply_or_divide(left, right, work._divide)

            def unlogged_support_ratio(probability, propensity):
                try:
                    return div(probability, propensity)
                except OverflowError:
                    # The frozen switch bias sum compares a positive infinite
                    # action ratio with the threshold. No ratio is published.
                    return math.inf

            def summed(values):
                exact = work._fraction(0)
                for value in values:
                    exact = work._add(exact, work._binary64_ratio(value))
                return round_to_binary64(exact)

            row_scores,weights,lineage=[],[],[]
            switch_rows=[]
            if math_id=="MATH-24":
                weight_values,reward_values=inputs["weights"],inputs["rewards"]
                work._require(type(weight_values) is type(reward_values) is tuple and 0<len(weight_values)==len(reward_values)<=64,
                    "LP03_OPE_REVIEW_ALIGNED_WEIGHTS_AND_REWARDS")
                for weight,reward in zip(weight_values,reward_values,strict=True):
                    wx,rx=represented(weight),represented(reward)
                    work._require(wx >= zero,"LP03_OPE_REVIEW_NONNEGATIVE_WEIGHT")
                    weights.append(wx)
                    row_scores.append(mul(wx, rx))
            else:
                rows=inputs["logged_rows"]
                work._require(type(rows) is tuple and 0<len(rows)<=64,"LP03_OPE_REVIEW_LOGGED_ROW_ROSTER")
                identities=set()
                for row in rows:
                    name,action=row["row_id"],row["logged_action_index"]
                    mu=tuple(represented(value) for value in row["behavior_action_probabilities"])
                    pi=tuple(represented(value) for value in row["target_action_probabilities"])
                    q=tuple(represented(value) for value in row["cross_fitted_reward_model_predictions"])
                    reward=represented(row["reward"])
                    work._require(type(name) is str and name not in identities and type(action) is int
                        and 0<=action<len(mu)==len(pi)==len(q)<=16 and row["cross_fitted_prediction"] is True
                        and all(zero<=value<=one for value in (*mu,*pi))
                        and all(behavior>zero or target==zero for behavior,target in zip(mu,pi,strict=True)),
                        "LP03_OPE_REVIEW_ORIGINAL_SUPPORT")
                    for policy_probabilities in (mu, pi):
                        deviation = add(summed(policy_probabilities), -one)
                        work._require(abs(deviation) <= tolerance, "LP03_OPE_REVIEW_ORIGINAL_SIMPLEX_TOLERANCE")
                    identities.add(name)
                    weight=zero if pi[action]==zero else div(pi[action], mu[action])
                    if math_id in ("MATH-22","MATH-25"):
                        control=summed(tuple(mul(probability, fit)
                            for probability,fit in zip(pi,q,strict=True)))
                        residual=add(reward, -q[action])
                        corrected=mul(weight, residual)
                        if math_id == "MATH-25":
                            support = tuple((probability, unlogged_support_ratio(probability, propensity) if probability else None)
                                for probability, propensity in zip(pi,mu,strict=True))
                            switch_rows.append(dict(row_id=name, fold_id=row["fold_id"], reward=reward, weight=weight,
                                direct=control, weighted_residual=corrected, all_action_support=support))
                            continue
                        score=add(control, corrected)
                    else:
                        score=mul(weight, reward)
                    weights.append(weight)
                    row_scores.append(score)
                    lineage.append(name)
            if math_id == "MATH-25":
                lower, upper = (represented(inputs[name]) for name in ("reward_lower_bound", "reward_upper_bound"))
                reward_range = add(upper, -lower)
                work._require(lower < upper and all(lower <= row["reward"] <= upper for row in switch_rows),
                    "LP03_SWITCH_REVIEW_ORIGINAL_REWARD_BOUNDS")
                folds = inputs["outer_fold_count"]
                taus = inputs["tau_grid"]
                work._require(type(folds) is int and 2 <= folds <= 8
                    and {row["fold_id"] for row in switch_rows} == set(range(folds))
                    and type(taus) is tuple and 0 < len(taus) <= 16, "LP03_SWITCH_REVIEW_ORIGINAL_PLAN")
                thresholds = tuple(None if type(tau) is str and tau == "INF" else represented(tau) for tau in taus)
                work._require(all(value is None if index == len(thresholds)-1 and taus[index] == "INF"
                    else value is not None and value >= zero for index, value in enumerate(thresholds))
                    and all(left is not None and (right is None or left < right)
                        for left, right in zip(thresholds, thresholds[1:])), "LP03_SWITCH_REVIEW_ORIGINAL_TAU_GRID")

                def rounded_mean(values):
                    return div(summed(values), float(len(values)))

                def score(row, threshold):
                    direct = row["direct"]
                    correction = row["weighted_residual"]
                    return add(direct, correction if threshold is None or row["weight"] <= threshold else zero)

                results, held_out, lineage = [], [], []
                for fold in range(folds):
                    training = tuple(row for row in switch_rows if row["fold_id"] != fold)
                    test = tuple(row for row in switch_rows if row["fold_id"] == fold)
                    work._require(len(training) >= 2 and bool(test), "LP03_SWITCH_REVIEW_ORIGINAL_FOLD_SUPPORT")
                    criteria = []
                    for label, threshold in zip(taus, thresholds, strict=True):
                        values = tuple(score(row, threshold) for row in training)
                        center = rounded_mean(values)
                        squared = []
                        for value in values:
                            difference = add(value, -center)
                            # The implementation's point statistic uses the host binary64 power.
                            # Use that primitive at this coordinate and independently derive every
                            # difference, mean, fold roster, bound, and selection around it.
                            squared_term = math.pow(difference, 2.0)
                            work._require(math.isfinite(squared_term), "LP03_SWITCH_REVIEW_FINITE_VARIANCE_SQUARE")
                            work._binary64_ratio(squared_term)
                            squared.append(squared_term)
                        sample_variance = div(summed(squared), float(len(training)-1))
                        variance = div(sample_variance, float(len(training)))
                        discarded_mass = tuple(summed(probability for probability, ratio in row["all_action_support"]
                            if threshold is not None and ratio is not None and ratio > threshold) for row in training)
                        bias = mul(reward_range, rounded_mean(discarded_mass))
                        bias_square = mul(bias, bias)
                        upper_mse = add(variance, bias_square)
                        criteria.append(dict(tau=label, variance_of_mean=float(variance), bias_upper_bound=float(bias),
                            estimated_mse_upper_bound=float(upper_mse)))
                    selected = min(range(len(taus)), key=lambda index: (criteria[index]["estimated_mse_upper_bound"], index))
                    scores = tuple(score(row, thresholds[selected]) for row in test)
                    held_out.extend(scores)
                    results.append(dict(outer_fold=fold, selected_tau=taus[selected], criteria=tuple(criteria),
                        held_out_row_values=tuple(map(float, scores))))
                    lineage.append(dict(outer_fold=fold, training_row_ids=tuple(row["row_id"] for row in training),
                        held_out_row_ids=tuple(row["row_id"] for row in test)))
                computed = dict(switch_ope_estimate=float(rounded_mean(held_out)), held_out_row_values=tuple(map(float, held_out)),
                    outer_fold_results=tuple(results), selection_rule="MIN_ESTIMATED_MSE_UPPER_BOUND_THEN_SMALLEST_TAU",
                    clipping_applied=False)
                work._require(deterministic_json(computed) == deterministic_json(actual) == deterministic_json(expected)
                    == raw_json.decode("utf-8") == expected_json.decode("utf-8"), "LP03_SWITCH_REVIEW_ORIGINAL_SELECTION_ARITHMETIC")
                return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(dict(
                    method="ORIGINAL_NESTED_SWITCH_POINT_ESTIMATOR_V1", math_id=math_id, ordered_fold_lineage=tuple(lineage),
                    typed_input_json=input_json.decode("utf-8"), original_estimator_raw_json=raw_json.decode("utf-8"),
                    independent_scope="ORIGINAL_POINT_ESTIMATOR_ARITHMETIC"), work=work)
            total=summed(weights)
            squared=summed(tuple(mul(value, value) for value in weights))
            if total>zero:
                work._require(squared>zero,"LP03_OPE_REVIEW_POSITIVE_SQUARED_MASS")
                ess=div(mul(total, total), squared)
            else:
                work._require(math_id!="MATH-24","LP03_OPE_REVIEW_POSITIVE_WEIGHT_SUM")
                ess=zero
            estimate = div(summed(row_scores), total if math_id == "MATH-24" else float(len(row_scores)))
            expected_key={"MATH-22":"doubly_robust_estimate","MATH-23":"inverse_propensity_score_estimate",
                "MATH-24":"self_normalized_ips_estimate"}[math_id]
            computed={expected_key:float(estimate),"effective_sample_size":float(ess)}
            if math_id=="MATH-24":
                computed["weight_sum"]=float(total)
            else:
                computed.update(row_values=tuple(map(float,row_scores)),importance_weights=tuple(map(float,weights)),
                    clipping_applied=False)
            work._require(deterministic_json(computed)==deterministic_json(actual)==deterministic_json(expected)
                ==raw_json.decode("utf-8")==expected_json.decode("utf-8"),"LP03_OPE_REVIEW_ORIGINAL_ESTIMATOR_ARITHMETIC")
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(dict(
                method="ORDERED_RECORDED_OPE_BINARY64_V1",math_id=math_id,ordered_row_ids=tuple(lineage),
                typed_input_json=input_json.decode("utf-8"),original_estimator_raw_json=raw_json.decode("utf-8"),
                independent_scope="ORIGINAL_POINT_ESTIMATOR_ARITHMETIC"),work=work)

    @staticmethod
    def _bounded_review_fold_topology_v1(math_id, input_json, raw_json, *, work):
        """Verify purging, embargo, and exact assignments before held-out scoring."""
        import struct
        from itertools import combinations
        from math import isfinite
        from .context import _native_require, _native_ident
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1

        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(type(math_id) is str and math_id in ("MATH-20","MATH-21")
                and all(type(value) is bytes and 0 < len(value) <= 65536 for value in (input_json,raw_json)),
                "LP03_FOLD_TOPOLOGY_PROFILE")
            inputs=decode_evidence_public_invocation_inputs_v1(math_id,input_json,maximum_bytes=65536,maximum_nodes=4096)
            actual=decode_evidence_raw_output_v1(math_id,raw_json,maximum_bytes=65536,maximum_nodes=4096)
            rows,embargo=inputs["sample_intervals"],inputs["embargo_duration"]
            combinatorial=math_id=="MATH-21"
            group_count=inputs["N_groups" if combinatorial else "folds"]
            test_count=inputs["k_test_groups"] if combinatorial else 1
            work._require(type(rows) is tuple and 2 <= len(rows) <= 8
                and type(group_count) is int and 2 <= group_count <= min(4,len(rows))
                and type(test_count) is int and (test_count==1 or (group_count,test_count)==(4,2))
                and type(embargo) is float and isfinite(embargo) and 0 <= embargo <= 1_000_000,
                "LP03_FOLD_TOPOLOGY_COMPLETE_DOMAIN")
            roster=tuple(combinations(range(group_count),test_count))
            # All outputs are bounded by the original roster before walking
            # split cells or emitting diagnostics.
            work._require(2*(len(input_json)+len(raw_json)) + 1800*len(roster) + 2048
                <= work.limits["max_serialized_bytes"] - work.consumed["serialized_bytes"],
                "LP03_FOLD_TOPOLOGY_COMPLETE_BYTES")
            if combinatorial:
                work._require(inputs["aggregation_rule"]=="ALL_PATHS_NO_CHERRY_PICKING",
                    "LP03_FOLD_TOPOLOGY_AGGREGATION_PROFILE")
            def bits(value):return struct.pack(">d",value).hex()
            def observed(value):
                work._require(type(value) is float and isfinite(value) and -1_000_000 <= value <= 1_000_000,
                    "LP03_FOLD_TOPOLOGY_INTERVAL_DOMAIN")
                work._consumed["input_values"] += 1
                return work._binary64_ratio(value,original_input=True)
            declared=[]
            for row in rows:
                work._require(isinstance(row,Mapping) and set(row)=={"sample_id","start","end"},
                    "LP03_FOLD_TOPOLOGY_INTERVAL_FIELDS")
                identifier=row["sample_id"]
                _native_ident(identifier)
                start,end=observed(row["start"]),observed(row["end"])
                work._require(work._compare(start,end)<0,"LP03_FOLD_TOPOLOGY_HALF_OPEN_INTERVAL")
                declared.append((identifier,row["start"],row["end"],start,end))
            work._require(len({row[0] for row in declared})==len(declared),"LP03_FOLD_TOPOLOGY_DUPLICATE_SAMPLE")
            # Count each sort comparison explicitly, with the original lexical
            # tiebreak between represented intervals.
            ordered=[]
            for row in declared:
                position=len(ordered)
                while position:
                    prior=ordered[position-1]
                    difference=work._compare(row[3],prior[3]) or work._compare(row[4],prior[4])
                    if difference>0 or difference==0 and row[0]>prior[0]:
                        break
                    position-=1
                ordered.insert(position,row)
            width,surplus=divmod(len(ordered),group_count)
            blocks=tuple(tuple(range(i*width+min(i,surplus),(i+1)*width+min(i+1,surplus)))
                for i in range(group_count))
            embargo_ratio=observed(embargo)
            layouts,splits=[],[]
            for index,selection in enumerate(roster):
                test_indices=tuple(row for group in selection for row in blocks[group])
                test_set=set(test_indices)
                tests=tuple(ordered[row] for row in test_indices)
                merged=[]
                for _name,start_float,end_float,start,end in tests:
                    if not merged or work._compare(start,merged[-1][3])>0:
                        merged.append((start_float,end_float,start,end))
                    elif work._compare(end,merged[-1][3])>0:
                        merged[-1]=(merged[-1][0],end_float,merged[-1][2],end)
                thresholds=[]
                for _,end_float,_,end in merged:
                    exact=work._add(end,embargo_ratio)
                    work._bits(max(abs(exact.numerator).bit_length(),exact.denominator.bit_length())+1076)
                    work._consumed["integer_operations"] += 1
                    negative_zero = bits(end_float) == bits(embargo) == "8000000000000000"
                    represented=-0.0 if exact==0 and negative_zero else float(exact)
                    thresholds.append((end,work._binary64_ratio(represented),bits(represented)))
                training,purged,embargoed=[],[],[]
                for row_index,(name,_start,_end,start,end) in enumerate(ordered):
                    if row_index in test_set:
                        continue
                    overlaps=any(work._compare(start,test[4])<0 and work._compare(test[3],end)<0 for test in tests)
                    if overlaps:
                        purged.append(name)
                    elif any(work._compare(left,start)<=0 and work._compare(start,right)<0 for left,right,_ in thresholds):
                        embargoed.append(name)
                    else:
                        training.append(name)
                partition=dict(test_sample_ids=tuple(row[0] for row in tests),train_sample_ids=tuple(training),
                    purged_sample_ids=tuple(purged),embargoed_sample_ids=tuple(embargoed),
                    merged_test_intervals=tuple((start,end) for start,end,_,_ in merged))
                partition.update(dict(split_id=index,test_groups=selection) if combinatorial else dict(fold_id=index))
                splits.append(partition)
                layouts.append(dict(ordinal=index,ordered_test_indices=test_indices,ordinal_groups=selection,
                    embargo_boundary_bits=tuple(bits_text for _,_,bits_text in thresholds)))
            if combinatorial:
                if test_count==1:
                    assignments=(tuple(range(group_count)),)
                else:
                    # The closed N=4,k=2 case has one complementary partner
                    # per split, so original pivot order determines all paths.
                    assignments=tuple((i,roster.index(tuple(group for group in range(4) if group not in roster[i])))
                        for i in range(3))
                paths=tuple(dict(path_id=index,split_ids=assignment,
                    test_group_partition=tuple(roster[split] for split in assignment)) for index,assignment in enumerate(assignments))
                expected=dict(N_groups=group_count,k_test_groups=test_count,split_count=len(splits),
                    expected_path_count=len(paths),path_count=len(paths),aggregation_rule=inputs["aggregation_rule"],
                    splits=tuple(splits),paths=paths)
            else:
                expected=dict(ordered_sample_ids=tuple(row[0] for row in ordered),
                    interval_semantics="HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE",
                    embargo_basis="TIME_DURATION_AFTER_MERGED_TEST_INTERVAL",folds=tuple(splits))
            work._require(deterministic_json(actual)==deterministic_json(expected)==raw_json.decode("utf-8"),
                "LP03_FOLD_TOPOLOGY_ORIGINAL_RESULT_MISMATCH")
            proof=dict(math_id=math_id,ordered_original_ids=tuple(row[0] for row in ordered),
                balanced_blocks=blocks,split_assignments=tuple(layouts),typed_input_json=input_json.decode("utf-8"),
                actual_topology_json=raw_json.decode("utf-8"),held_out_score_coverage="TOPOLOGY_ONLY_NO_SCORE_RECEIPTS")
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof,work=work)



    @staticmethod
    def _bounded_review_pbo_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Verify the bounded original CSCV output with ordered binary64 cells."""
        from itertools import combinations
        from math import inf, isfinite, nextafter
        import struct
        from .context import _native_require, _native_ident
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1

        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(raw) is bytes and 0 < len(raw) <= 65536 for raw in (input_json, raw_json, expected_json)),
                "LP03_PBO_REVIEW_WIRE")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-19", input_json, maximum_bytes=65536, maximum_nodes=4096)
            actual = decode_evidence_raw_output_v1("MATH-19", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            declared = decode_evidence_raw_output_v1("MATH-19", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            matrix, strategies, group_count = (inputs[key] for key in ("performance_matrix", "strategy_ids", "S"))
            work._require(type(matrix) is tuple and 2 <= len(matrix) <= 8
                and type(strategies) is tuple and 1 <= len(strategies) <= 4 and all(
                    type(name) is str and 0 < len(name) <= 128 for name in strategies)
                and type(group_count) is int and group_count in (2, 4) and len(matrix) % group_count == 0
                and all(type(row) is tuple and len(row) == len(strategies) for row in matrix),
                "LP03_PBO_REVIEW_COMPLETE_DOMAIN")
            for name in strategies:
                _native_ident(name)
            work._require(len(set(strategies)) == len(strategies), "LP03_PBO_REVIEW_STRATEGY_ROSTER")
            width = len(matrix) // group_count
            roster = tuple(combinations(range(group_count), group_count // 2))
            work._require(sum(map(len, (input_json, raw_json, expected_json))) * 2 + len(roster) * 2200 + 2048
                <= work.limits["max_serialized_bytes"] - work.consumed["serialized_bytes"],
                "LP03_PBO_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(len(roster) == actual["split_count"] == declared["split_count"]
                == len(actual["splits"]) == len(declared["splits"]) == len(actual["logits"]) == len(declared["logits"])
                and actual["S"] == declared["S"] == group_count, "LP03_PBO_REVIEW_COMPLETE_SPLIT_ROSTER")
            # Closed roster implies at most six splits, with at most four
            # training and four test means per split. The encoded proof is
            # charged against the original remaining allowance before signing.
            zero, one, two = (work._fraction(value) for value in (0, 1, 2))

            def bits(value):
                return struct.pack(">d", value).hex()

            def observed(value):
                work._require(type(value) is float and isfinite(value), "LP03_PBO_REVIEW_BINARY64_INPUT")
                work._consumed["input_values"] += 1
                return work._binary64_ratio(value, original_input=True)

            def cell(number, lower, upper):
                before, after = nextafter(number, -inf), nextafter(number, inf)
                work._require(isfinite(before) and isfinite(after), "LP03_PBO_REVIEW_FINITE_CELL")
                ratio = work._binary64_ratio(number)
                lo = work._divide(work._add(work._binary64_ratio(before), ratio), two)
                hi = work._divide(work._add(work._binary64_ratio(after), ratio), two)
                even = int(bits(number), 16) & 1 == 0
                first, last = work._compare(lo, lower), work._compare(upper, hi)
                work._require(work._compare(lower, upper) <= 0 and (first < 0 or first == 0 and even)
                    and (last < 0 or last == 0 and even), "LP03_PBO_REVIEW_NEAREST_EVEN_CELL")
                return ratio

            def rounded(value):
                work._bits(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                result = float(value)
                return result, cell(result, value, value)

            matrix_ratios = []
            minus_one = work._subtract(zero, one)
            for row in matrix:
                ratios = tuple(observed(value) for value in row)
                work._require(all(work._compare(ratio, minus_one) >= 0 and work._compare(ratio, one) <= 0
                    for ratio in ratios), "LP03_PBO_REVIEW_PERFORMANCE_DOMAIN")
                matrix_ratios.append(ratios)
            blocks = tuple(tuple(range(index * width, (index + 1) * width)) for index in range(group_count))

            def means(indices):
                rows = []
                for column in range(len(strategies)):
                    total = zero
                    for index in indices:
                        total = work._add(total, matrix_ratios[index][column])
                    sum_float, sum_ratio = rounded(total)
                    mean, mean_ratio = rounded(work._divide(sum_ratio, work._fraction(len(indices))))
                    rows.append((bits(sum_float), bits(mean), mean_ratio))
                return tuple(rows)

            results = []
            unfavorable = 0
            for ordinal, train_groups in enumerate(roster):
                train_rows = tuple(index for g in train_groups for index in blocks[g])
                test_rows = tuple(index for g in range(group_count) if g not in train_groups for index in blocks[g])
                train_means, test_means = means(train_rows), means(test_rows)
                winner = 0
                for index in range(1, len(strategies)):
                    comparison = work._compare(train_means[index][2], train_means[winner][2])
                    if comparison > 0 or comparison == 0 and strategies[index] < strategies[winner]:
                        winner = index
                comparisons = tuple(work._compare(row[2], test_means[winner][2]) for row in test_means)
                below, ties = comparisons.count(-1), comparisons.count(0)
                rank_twice = work._int_sum(work._int_product(2, below), work._int_sum(ties, 1))
                rank, rank_ratio = rounded(work._fraction(rank_twice, 2))
                relative, relative_ratio = rounded(work._divide(rank_ratio, work._fraction(len(strategies) + 1)))
                complement, complement_ratio = rounded(work._subtract(one, relative_ratio))
                odds, odds_ratio = rounded(work._divide(relative_ratio, complement_ratio))
                log_sign = work._compare(odds_ratio, one)
                if log_sign == 0:
                    low = high = zero
                elif log_sign > 0:
                    low, high = work._log_enclosure(odds_ratio)
                else:
                    lo_magnitude, hi_magnitude = work._log_enclosure(work._divide(one, odds_ratio))
                    low, high = work._subtract(zero, hi_magnitude), work._subtract(zero, lo_magnitude)
                raw_split, expected_split = actual["splits"][ordinal], declared["splits"][ordinal]
                logit = raw_split["logit"]
                log_ratio = observed(logit)
                cell(logit, low, high)
                work._require(work._compare(log_ratio, zero) == log_sign and (log_sign != 0 or bits(logit) == "0000000000000000"),
                    "LP03_PBO_REVIEW_LOG_SIGN")
                for result, split in ((actual, raw_split), (declared, expected_split)):
                    work._require(split["train_groups"] == train_groups and split["is_winner_strategy_id"] == strategies[winner],
                        "LP03_PBO_REVIEW_GROUP_OR_WINNER")
                    for value, derived in ((split["oos_midrank_worst_1_best_n"], rank), (split["relative_rank"], relative),
                            (split["logit"], logit), (result["logits"][ordinal], logit)):
                        observed(value)
                        work._require(bits(value) == bits(derived), "LP03_PBO_REVIEW_SPLIT_COORDINATE_MISMATCH")
                unfavorable += int(log_sign <= 0)
                # Retain a fixed-size outward dyadic enclosure of log(odds).
                scale = work._shift(1, 128)
                def outward(bound, ceiling):
                    scaled = work._int_product(bound.numerator, scale)
                    work._bits(max(abs(scaled).bit_length(), bound.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient, remainder = divmod(scaled, bound.denominator)
                    return work._int_sum(quotient, 1) if ceiling and remainder else quotient
                low_int, high_int = outward(low, False), outward(high, True)
                cell(logit, work._fraction(low_int, scale), work._fraction(high_int, scale))
                results.append(dict(train_groups=train_groups, train_rows=train_rows, test_rows=test_rows,
                    training_cells=tuple((total, mean) for total, mean, _ in train_means),
                    testing_cells=tuple((total, mean) for total, mean, _ in test_means),
                    winner_column=winner, lower_count=below, tie_count=ties, rank_bits=bits(rank),
                    relative_rank_bits=bits(relative), complement_bits=bits(complement), odds_bits=bits(odds),
                    logit_bits=bits(logit), dyadic_log_interval=(low_int, high_int), fraction_bits=128))
            fraction, _ = rounded(work._fraction(unfavorable, len(roster)))
            for record in (actual, declared, projected_value):
                # This profile projects the complete heterogeneous PBO record.
                work._require(deterministic_json(record) == deterministic_json(declared),
                    "LP03_PBO_REVIEW_RAW_OR_PROJECTED_RECORD_MISMATCH")
            work._require(raw_json == expected_json and bits(actual["probability_of_backtest_overfitting"]) == bits(fraction),
                "LP03_PBO_REVIEW_RESULT_OR_WIRE_MISMATCH")
            proof = dict(profile="ORDERED_BINARY64_CSCV_LOG_MODEL_CONFORMANCE_V1", contiguous_blocks=blocks, splits=tuple(results),
                unfavorable_splits=unfavorable, probability_bits=bits(fraction), typed_input_json=input_json.decode("utf-8"),
                raw_json=raw_json.decode("utf-8"), expected_json=expected_json.decode("utf-8"),
                intermediate_observation_scope="DERIVED_ORDERED_CSCV_ARITHMETIC_ONLY",
                statistical_authority="NO_EMPIRICAL_OVERFITTING_OR_GENERALIZATION_CERTIFICATION")
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)



    @staticmethod
    def _bounded_review_probabilistic_sharpe_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Bounded ordered PSR source-model conformance, never statistical support.

        Intermediate sqrt/erfc values are derived, not native observations.
        The exact erfc enclosure proves one RN source-model cell; it does not
        attest a platform libm implementation, coverage, or source authority.
        """
        import struct
        from math import isfinite, nextafter, inf, isqrt
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_SHARPE_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-17", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-17", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-17", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            estimate, reference = inputs["estimated_sharpe"], inputs["reference_sharpe"]
            count = inputs["independent_equivalent_observations"]
            skewness, kurtosis = inputs["sample_skewness"], inputs["sample_non_excess_kurtosis"]
            # This finite conformance profile declares exact-conversion support
            # before arithmetic. It neither floors ESS nor supplies assumptions.
            work._require(type(count) is int and 2 <= count <= 2**53
                and all(type(value) is float and isfinite(value) for value in (estimate, reference, skewness, kurtosis))
                and kurtosis >= 1.0, "LP03_SHARPE_REVIEW_TYPED_DOMAIN")
            max_cells = 24
            source_bytes = sum(len(value) for value in (input_json, raw_json, expected_json))
            base_reserve = 2 * max_cells * 200 + 2 * (6 * source_bytes + 2400)
            work._require(work.consumed["serialized_bytes"] + base_reserve <= work.limits["max_serialized_bytes"],
                "LP03_SHARPE_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(160 + 12 * max_cells <= 4096, "LP03_SHARPE_REVIEW_COMPLETE_NODE_LAYOUT")
            def bits(value):
                return struct.pack(">d", value).hex()
            def ratio(value):
                work._require(type(value) is float and isfinite(value), "LP03_SHARPE_FINITE_CELL_REQUIRED")
                return work._binary64_ratio(value)
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_SHARPE_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            def emitted(values):
                result = work._emit(values)
                return {name: dict(value) if type(value) is MappingProxyType else value for name, value in result.items()}
            zero, one, two = work._fraction(0), work._fraction(1), work._fraction(2)
            original_count = work._exact(count)
            for value in (estimate, reference, skewness, kurtosis): observed(value)
            cells = []
            def cell(candidate, lower, upper, *, squared=False):
                previous, following = nextafter(candidate, -inf), nextafter(candidate, inf)
                work._require(isfinite(candidate) and isfinite(previous) and isfinite(following),
                    "LP03_SHARPE_FINITE_CELL_REQUIRED")
                actual, before, after = ratio(candidate), ratio(previous), ratio(following)
                low_mid = work._divide(work._add(before, actual), two)
                high_mid = work._divide(work._add(actual, after), two)
                even = int(bits(candidate), 16) & 1 == 0
                if squared:
                    work._require(work._compare(lower, zero) >= 0 and work._compare(actual, zero) >= 0,
                        "LP03_SHARPE_SQRT_DOMAIN")
                    low_comparison = 1 if work._compare(low_mid, zero) < 0 else work._compare(lower, work._multiply(low_mid, low_mid))
                    high_comparison = work._compare(upper, work._multiply(high_mid, high_mid))
                else:
                    low_comparison, high_comparison = work._compare(lower, low_mid), work._compare(upper, high_mid)
                work._require(work._compare(lower, upper) <= 0
                    and (low_comparison > 0 or low_comparison == 0 and even)
                    and (high_comparison < 0 or high_comparison == 0 and even),
                    "LP03_SHARPE_NEAREST_EVEN_CELL_UNPROVEN")
                return actual
            def append(label, kind, left, right, candidate):
                work._require(len(cells) < max_cells and len(label) <= 24,
                    "LP03_SHARPE_REVIEW_COMPLETE_NODE_LAYOUT")
                row = emitted(dict(operation=label, kind=kind, left=bits(left), right=bits(right), candidate=bits(candidate)))
                # Exact rational operands and both adjacent midpoint bounds are
                # uniquely reconstructible from these binary64 bit strings.
                cells.append(row)
                return candidate
            def rounded(exact, *, negative_zero=False):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                try:
                    candidate = -0.0 if exact == 0 and negative_zero else float(exact)
                except OverflowError:
                    work._require(False, "LP03_SHARPE_FINITE_CELL_REQUIRED")
                cell(candidate, exact, exact)
                return candidate
            def op(label, kind, left, right):
                first, second = ratio(left), ratio(right)
                exact = {"ADD": work._add, "SUB": work._subtract, "MUL": work._multiply, "DIV": work._divide}[kind](first, second)
                # Rational zero does not determine the IEEE signed-zero bit.
                # Preserve original RN signs, including underflow from nonzero.
                left_negative, right_negative = int(bits(left), 16) >> 63, int(bits(right), 16) >> 63
                negative_zero = bool(left_negative ^ right_negative) if kind in ("MUL", "DIV") else (
                    left == 0.0 and right == 0.0 and bool(left_negative) and
                    (bool(right_negative) if kind == "ADD" else not right_negative))
                return append(label, kind, left, right, rounded(exact, negative_zero=negative_zero))
            def square_root(label, value):
                original = ratio(value)
                work._require(work._compare(original, zero) >= 0, "LP03_SHARPE_SQRT_DOMAIN")
                if work._compare(original, zero) == 0:
                    candidate = 0.0
                else:
                    # floor(log2(original)) from bounded integer comparison.
                    exponent = work._int_sum(original.numerator.bit_length(), -original.denominator.bit_length())
                    power = work._fraction(work._shift(1, exponent)) if exponent >= 0 else work._fraction(1, work._shift(1, -exponent))
                    if work._compare(original, power) < 0:
                        exponent = work._int_sum(exponent, -1)
                    quantum = max(-1074, exponent // 2 - 52)
                    scale = work._fraction(work._shift(1, 2 * quantum)) if quantum >= 0 else work._fraction(1, work._shift(1, -2 * quantum))
                    scaled = work._divide(original, scale)
                    work._bits(max(scaled.numerator.bit_length(), scaled.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient = scaled.numerator // scaled.denominator
                    work._bits(quotient.bit_length())
                    work._consumed["square_roots"] += 1
                    root = isqrt(quotient)
                    midpoint = work._fraction(work._int_sum(work._int_product(2, root), 1), 2)
                    comparison = work._compare(scaled, work._multiply(midpoint, midpoint))
                    if comparison > 0 or comparison == 0 and root & 1:
                        root = work._int_sum(root, 1)
                    step = work._fraction(work._shift(1, quantum)) if quantum >= 0 else work._fraction(1, work._shift(1, -quantum))
                    candidate = rounded(work._multiply(work._fraction(root), step))
                cell(candidate, original, original, squared=True)
                return append(label, "SQRT", value, 0.0, candidate)
            def atan_interval(denominator):
                x = work._fraction(1, denominator)
                square, power, partial = work._multiply(x, x), x, zero
                for index in range(64):
                    term = work._divide(power, work._fraction(work._int_sum(work._int_product(2, index), 1)))
                    partial = work._subtract(partial, term) if index & 1 else work._add(partial, term)
                    power = work._multiply(power, square)
                return partial, work._add(partial, work._divide(power, work._fraction(129)))
            def sqrt_pi_interval():
                first_low, first_high = atan_interval(5)
                second_low, second_high = atan_interval(239)
                low = work._subtract(work._multiply(work._fraction(16), first_low), work._multiply(work._fraction(4), second_high))
                high = work._subtract(work._multiply(work._fraction(16), first_high), work._multiply(work._fraction(4), second_low))
                upper = work._sqrt_upper(high)
                numerator = work._shift(low.numerator, 256)
                work._bits(max(numerator.bit_length(), low.denominator.bit_length()))
                work._consumed["integer_operations"] += 1
                quotient = numerator // low.denominator
                work._bits(quotient.bit_length())
                work._consumed["square_roots"] += 1
                root = isqrt(quotient)
                lower = work._fraction(root, work._shift(1, 128))
                work._require(work._compare(work._multiply(lower, lower), low) <= 0
                    and work._compare(low, high) <= 0 and work._compare(lower, one) > 0,
                    "LP03_SHARPE_PI_SQRT_ENCLOSURE")
                return lower, upper
            def erfc_enclosure(argument):
                original = ratio(argument)
                magnitude = work._subtract(zero, original) if work._compare(original, zero) < 0 else original
                work._require(work._compare(magnitude, two) <= 0,
                    "LP03_SHARPE_DECLARED_ERFC_ARGUMENT_REGION_UNAVAILABLE")
                sqrt_low, sqrt_high = sqrt_pi_interval()
                # Finite declared regions prevent tiny binary64 denominators
                # from entering 129th powers. All products are still preflighted.
                if work._compare(magnitude, work._fraction(1, work._shift(1, 60))) <= 0:
                    lower, upper = work._subtract(one, work._multiply(two, magnitude)), one
                    branch, terms = "SMALL_ARGUMENT", 0
                else:
                    square, power, factorial, partial = work._multiply(magnitude, magnitude), magnitude, 1, zero
                    for index in range(64):
                        divisor = work._int_product(factorial, work._int_sum(work._int_product(2, index), 1))
                        term = work._divide(power, work._fraction(divisor))
                        partial = work._subtract(partial, term) if index & 1 else work._add(partial, term)
                        power = work._multiply(power, square)
                        factorial = work._int_product(factorial, work._int_sum(index, 1))
                    remainder = work._divide(power, work._fraction(work._int_product(factorial, 129)))
                    integral_low = partial if work._compare(partial, zero) >= 0 else zero
                    integral_high = work._add(partial, remainder)
                    work._require(work._compare(integral_low, integral_high) <= 0, "LP03_SHARPE_INTEGRAL_ENCLOSURE")
                    erf_low = work._divide(work._multiply(two, integral_low), sqrt_high)
                    erf_high = work._divide(work._multiply(two, integral_high), sqrt_low)
                    if work._compare(erf_low, zero) < 0: erf_low = zero
                    if work._compare(erf_high, one) > 0: erf_high = one
                    work._require(work._compare(erf_low, erf_high) <= 0, "LP03_SHARPE_ERF_ENCLOSURE")
                    lower, upper = work._subtract(one, erf_high), work._subtract(one, erf_low)
                    branch, terms = "EXP_INTEGRAL_64", 64
                if work._compare(original, zero) < 0:
                    lower, upper = work._subtract(two, upper), work._subtract(two, lower)
                scale = work._shift(1, 128)
                def outward(value, ceiling):
                    numerator = work._int_product(value.numerator, scale)
                    work._bits(max(numerator.bit_length(), value.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient, remainder = divmod(numerator, value.denominator)
                    return work._int_sum(quotient, 1) if ceiling and remainder else quotient
                low_integer, high_integer = outward(lower, False), outward(upper, True)
                compact_low, compact_high = work._fraction(low_integer, scale), work._fraction(high_integer, scale)
                work._require(work._compare(compact_low, lower) <= 0 and work._compare(lower, upper) <= 0
                    and work._compare(upper, compact_high) <= 0, "LP03_SHARPE_OUTWARD_ENCLOSURE")
                candidate = rounded(work._divide(work._add(compact_low, compact_high), two))
                cell(candidate, compact_low, compact_high)
                certificate = emitted(dict(argument_bits=bits(argument), derived_erfc_bits=bits(candidate),
                    lower_numerator=low_integer, upper_numerator=high_integer, fraction_bits=128,
                    branch=branch, integral_terms=terms, machin_terms_per_series=64, sqrt_fraction_bits=128,
                    interpretation="DERIVED_UNOBSERVED_ERFC_SOURCE_MODEL_CELL"))
                return candidate, certificate
            skew_estimate = op("SKEW_ESTIMATE", "MUL", skewness, estimate)
            initial = op("ONE_MINUS_SKEW", "SUB", 1.0, skew_estimate)
            excess = op("KURTOSIS_MINUS_ONE", "SUB", kurtosis, 1.0)
            quarter = op("KURTOSIS_QUARTER", "DIV", excess, 4.0)
            first_estimate = op("KURTOSIS_ESTIMATE", "MUL", quarter, estimate)
            second_estimate = op("KURTOSIS_ESTIMATE2", "MUL", first_estimate, estimate)
            denominator = op("DENOMINATOR_SQUARED", "ADD", initial, second_estimate)
            work._consumed["comparisons"] += 1
            work._require(denominator > 0.0, "LP03_SHARPE_POSITIVE_DENOMINATOR_REQUIRED")
            difference = op("ESTIMATE_DIFFERENCE", "SUB", estimate, reference)
            count_minus_one = work._int_sum(original_count.numerator, -1)
            support_root = square_root("SUPPORT_SQRT", rounded(work._fraction(count_minus_one)))
            numerator = op("SCORE_NUMERATOR", "MUL", difference, support_root)
            denominator_root = square_root("DENOMINATOR_SQRT", denominator)
            score = op("ZSCORE", "DIV", numerator, denominator_root)
            complement = op("CDF_LOCATION_MINUS", "SUB", 0.0, score)
            scale = op("CDF_SIGMA_SQRT2", "MUL", 1.0, 1.4142135623730951)
            argument = op("CDF_ERFC_ARGUMENT", "DIV", complement, scale)
            erfc, certificate = erfc_enclosure(argument)
            probability = op("CDF_HALF", "MUL", 0.5, erfc)
            for field, derived in (("probabilistic_sharpe_ratio", probability), ("z_score", score)):
                for actual in (raw[field], expected[field]):
                    observed(actual)
                    work._require(bits(actual) == bits(derived), "LP03_SHARPE_RAW_OR_EXPECTATION_MISMATCH")
            observed(projected_value)
            work._require(bits(projected_value) == bits(probability), "LP03_SHARPE_PROJECTION_MISMATCH")
            work._require(raw_json == expected_json, "LP03_SHARPE_RAW_EXPECTATION_WIRE_MISMATCH")
            summary = emitted(dict(independent_equivalent_observations=count, count_minus_one=count_minus_one,
                score_bits=bits(score), probability_bits=bits(probability),
                typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8")))
            proof = dict(profile="ORDERED_BINARY64_PSR_ERFC_MODEL_CONFORMANCE_V1",
                intermediate_observation_scope="ALL_SQRT_ERFC_AND_ARITHMETIC_STAGES_DERIVED_NOT_OBSERVED",
                statistical_authority="NO_INDEPENDENCE_SUPPORT_OR_STATISTICAL_COVERAGE_CERTIFICATION",
                model_provenance="CPYTHON_V3_14_6_NORMALDIST_ERFC_SOURCE_MODEL_NOT_LIBM_BINARY_ATTESTATION",
                declared_support_maximum=2**53, declared_erfc_argument_magnitude_maximum=2,
                erfc_enclosure=certificate, cells=tuple(cells), summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_wilson_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Bounded AS241/Wilson model conformance, not coverage certification.

        Every inverse-normal and Wilson intermediate is derived, not observed.
        The tagged CPython AS241 model is not a compiler-to-binary attestation.
        Only original final endpoint bits are compared with the model result.
        """
        from math import isfinite, nextafter, inf, isqrt
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_WILSON_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-11", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-11", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-11", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            successes, trials, confidence = inputs["successes"], inputs["trials"], inputs["confidence"]
            work._require(type(successes) is int and type(trials) is int and 0 <= successes <= trials <= 2**53
                and trials > 0 and type(confidence) is float and isfinite(confidence) and 0.0 < confidence < 1.0
                and type(projected_value) is tuple and len(projected_value) == 2,
                "LP03_WILSON_REVIEW_TYPED_DOMAIN")
            # A fixed instruction roster, not a variable-size source history.
            # Each compact row is at most 200 ASCII bytes. Reserve both its
            # emitted fragment and its eventual complete-artifact copy before
            # allocating the roster. Tail enclosure has a separate exact bound.
            max_cells = 64
            source_bytes = sum(len(value) for value in (input_json, raw_json, expected_json))
            base_reserve = 2 * max_cells * 200 + 2 * (6 * source_bytes + 1400)
            work._require(work.consumed["serialized_bytes"] + base_reserve <= work.limits["max_serialized_bytes"],
                "LP03_WILSON_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            work._require(96 + 12 * max_cells <= 4096, "LP03_WILSON_REVIEW_COMPLETE_NODE_LAYOUT")
            def bits(value):
                return struct.pack(">d", value).hex()
            def ratio(value):
                work._require(type(value) is float and isfinite(value), "LP03_WILSON_FINITE_CELL_REQUIRED")
                return work._binary64_ratio(value)
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_WILSON_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            def emitted(values):
                result = work._emit(values)
                return {name: dict(value) if type(value) is MappingProxyType else value for name, value in result.items()}
            zero, one, two = work._fraction(0), work._fraction(1), work._fraction(2)
            original_successes, original_trials = work._exact(successes), work._exact(trials)
            observed(confidence)
            cells = []
            log_proof = None
            def cell(candidate, lower, upper, *, squared=False):
                previous, following = nextafter(candidate, -inf), nextafter(candidate, inf)
                work._require(isfinite(candidate) and isfinite(previous) and isfinite(following),
                    "LP03_WILSON_FINITE_CELL_REQUIRED")
                actual, before, after = ratio(candidate), ratio(previous), ratio(following)
                low_mid = work._divide(work._add(before, actual), two)
                high_mid = work._divide(work._add(actual, after), two)
                even = int(bits(candidate), 16) & 1 == 0
                if squared:
                    work._require(work._compare(lower, zero) >= 0 and work._compare(actual, zero) >= 0,
                        "LP03_WILSON_SQRT_DOMAIN")
                    low_comparison = 1 if work._compare(low_mid, zero) < 0 else work._compare(lower, work._multiply(low_mid, low_mid))
                    high_comparison = work._compare(upper, work._multiply(high_mid, high_mid))
                else:
                    low_comparison, high_comparison = work._compare(lower, low_mid), work._compare(upper, high_mid)
                work._require(work._compare(lower, upper) <= 0
                    and (low_comparison > 0 or low_comparison == 0 and even)
                    and (high_comparison < 0 or high_comparison == 0 and even),
                    "LP03_WILSON_NEAREST_EVEN_CELL_UNPROVEN")
                return actual
            def append(label, kind, left, right, candidate):
                work._require(len(cells) < max_cells and len(label) <= 24,
                    "LP03_WILSON_REVIEW_COMPLETE_NODE_LAYOUT")
                row = emitted(dict(operation=label, kind=kind, left=bits(left), right=bits(right), candidate=bits(candidate)))
                # Exact rational operands and both adjacent midpoint bounds are
                # uniquely reconstructible from these binary64 bit strings.
                cells.append(row)
                return candidate
            def rounded(exact):
                work._bits(max(abs(exact.numerator).bit_length(), exact.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = float(exact)
                cell(candidate, exact, exact)
                return candidate
            def op(label, kind, left, right):
                first, second = ratio(left), ratio(right)
                exact = {"ADD": work._add, "SUB": work._subtract, "MUL": work._multiply, "DIV": work._divide}[kind](first, second)
                return append(label, kind, left, right, rounded(exact))
            def square_root(label, value):
                original = ratio(value)
                work._require(work._compare(original, zero) >= 0, "LP03_WILSON_SQRT_DOMAIN")
                if work._compare(original, zero) == 0:
                    candidate = 0.0
                else:
                    # floor(log2(original)) from bounded integer comparison.
                    exponent = work._int_sum(original.numerator.bit_length(), -original.denominator.bit_length())
                    power = work._fraction(work._shift(1, exponent)) if exponent >= 0 else work._fraction(1, work._shift(1, -exponent))
                    if work._compare(original, power) < 0:
                        exponent = work._int_sum(exponent, -1)
                    quantum = max(-1074, exponent // 2 - 52)
                    scale = work._fraction(work._shift(1, 2 * quantum)) if quantum >= 0 else work._fraction(1, work._shift(1, -2 * quantum))
                    scaled = work._divide(original, scale)
                    work._bits(max(scaled.numerator.bit_length(), scaled.denominator.bit_length()))
                    work._consumed["integer_operations"] += 1
                    quotient = scaled.numerator // scaled.denominator
                    work._bits(quotient.bit_length())
                    work._consumed["square_roots"] += 1
                    root = isqrt(quotient)
                    midpoint = work._fraction(work._int_sum(work._int_product(2, root), 1), 2)
                    comparison = work._compare(scaled, work._multiply(midpoint, midpoint))
                    if comparison > 0 or comparison == 0 and root & 1:
                        root = work._int_sum(root, 1)
                    step = work._fraction(work._shift(1, quantum)) if quantum >= 0 else work._fraction(1, work._shift(1, -quantum))
                    candidate = rounded(work._multiply(work._fraction(root), step))
                cell(candidate, original, original, squared=True)
                return append(label, "SQRT", value, 0.0, candidate)
            def polynomial(prefix, coefficients, value):
                result = coefficients[0]
                for index, coefficient in enumerate(coefficients[1:], 1):
                    result = op(prefix + str(index) + "M", "MUL", result, value)
                    result = op(prefix + str(index) + "A", "ADD", result, coefficient)
                return result
            tail = op("CONF_COMPLEMENT", "SUB", 1.0, confidence)
            half_tail = op("HALF_COMPLEMENT", "DIV", tail, 2.0)
            probability = op("NORMAL_PROBABILITY", "SUB", 1.0, half_tail)
            work._require(0.5 < probability < 1.0, "LP03_WILSON_ROUNDED_QUANTILE_DOMAIN")
            q = op("AS241_Q", "SUB", probability, 0.5)
            if q <= 0.425:
                branch = "CENTRAL"
                square = op("AS241_Q_SQUARED", "MUL", q, q)
                r = op("AS241_CENTRAL_R", "SUB", 0.180625, square)
                numerator_coefficients = (2.5090809287301226727e3, 3.3430575583588128105e4,
                    6.7265770927008700853e4, 4.5921953931549871457e4, 1.3731693765509461125e4,
                    1.9715909503065514427e3, 1.3314166789178437745e2, 3.3871328727963666080)
                denominator_coefficients = (5.2264952788528545610e3, 2.8729085735721942674e4,
                    3.9307895800092710610e4, 2.1213794301586595867e4, 5.3941960214247511077e3,
                    6.8718700749205790830e2, 4.2313330701600911252e1, 1.0)
            else:
                r = op("AS241_TAIL_R", "SUB", 1.0, probability)
                log_lower, log_upper = work._log_enclosure(work._divide(one, ratio(r)))
                # Enclose -log(r) without calling libm. A candidate alone is
                # insufficient: the complete enclosure must fit its exact cell.
                log_mid = work._divide(work._add(log_lower, log_upper), two)
                logarithm = rounded(log_mid)
                cell(logarithm, log_lower, log_upper)
                def decimal_digits_bound(integer):
                    # 30103/100000 > log10(2); bound text before str().
                    product = work._int_product(abs(integer).bit_length(), 30103)
                    padded = work._int_sum(product, 99999)
                    work._consumed["integer_operations"] += 1
                    return work._int_sum(1, padded // 100000)
                enclosure_bound = 700 + sum(decimal_digits_bound(value.numerator) + decimal_digits_bound(value.denominator)
                    for value in (log_lower, log_upper))
                work._require(work.consumed["serialized_bytes"] + base_reserve + 2 * enclosure_bound
                    <= work.limits["max_serialized_bytes"], "LP03_WILSON_REVIEW_COMPLETE_BYTES_EXHAUSTED")
                log_proof = emitted(dict(input_bits=bits(r), candidate_bits=bits(logarithm), lower=log_lower, upper=log_upper,
                    terms=64, interpretation="DERIVED_ROUNDED_NEGATIVE_LOG"))
                r = square_root("AS241_TAIL_SQRT", logarithm)
                if r <= 5.0:
                    branch = "TAIL_LE_FIVE"
                    r = op("AS241_TAIL_SHIFT", "SUB", r, 1.6)
                    numerator_coefficients = (7.74545014278341407640e-4, 2.27238449892691845833e-2,
                        2.41780725177450611770e-1, 1.27045825245236838258, 3.64784832476320460504,
                        5.76949722146069140550, 4.63033784615654529590, 1.42343711074968357734)
                    denominator_coefficients = (1.05075007164441684324e-9, 5.47593808499534494600e-4,
                        1.51986665636164571966e-2, 1.48103976427480074590e-1, 6.89767334985100004550e-1,
                        1.67638483018380384940, 2.05319162663775882187, 1.0)
                else:
                    branch = "TAIL_GT_FIVE"
                    r = op("AS241_TAIL_SHIFT", "SUB", r, 5.0)
                    numerator_coefficients = (2.01033439929228813265e-7, 2.71155556874348757815e-5,
                        1.24266094738807843860e-3, 2.65321895265761230930e-2, 2.96560571828504891230e-1,
                        1.78482653991729133580, 5.46378491116411436990, 6.65790464350110377720)
                    denominator_coefficients = (2.04426310338993978564e-15, 1.42151175831644588870e-7,
                        1.84631831751005468180e-5, 7.86869131145613259100e-4, 1.48753612908506148525e-2,
                        1.36929880922735805310e-1, 5.99832206555887937690e-1, 1.0)
            numerator = polynomial("N", numerator_coefficients, r)
            if branch == "CENTRAL":
                numerator = op("AS241_NUM_Q", "MUL", numerator, q)
            denominator = polynomial("D", denominator_coefficients, r)
            normal = op("AS241_QUOTIENT", "DIV", numerator, denominator)
            scaled_normal = op("AS241_SCALE", "MUL", normal, 1.0)
            z = op("AS241_LOCATION", "ADD", 0.0, scaled_normal)
            work._require(z > 0.0, "LP03_WILSON_POSITIVE_Z_REQUIRED")
            sf, nf = rounded(original_successes), rounded(original_trials)
            phat = op("WILSON_PHAT", "DIV", sf, nf)
            z2 = op("WILSON_Z2", "MUL", z, z)
            zn = op("WILSON_Z2_N", "DIV", z2, nf)
            denominator = op("WILSON_DENOM", "ADD", 1.0, zn)
            twice_n = op("WILSON_TWO_N", "MUL", 2.0, nf)
            center_bias = op("WILSON_CENTER_BIAS", "DIV", z2, twice_n)
            center_numerator = op("WILSON_CENTER_NUM", "ADD", phat, center_bias)
            center = op("WILSON_CENTER", "DIV", center_numerator, denominator)
            half_factor = op("WILSON_HALF_FACTOR", "DIV", z, denominator)
            complement = op("WILSON_COMPLEMENT", "SUB", 1.0, phat)
            variance = op("WILSON_VARIANCE", "MUL", phat, complement)
            per_trial = op("WILSON_PER_TRIAL", "DIV", variance, nf)
            four_n = op("WILSON_FOUR_N", "MUL", 4.0, nf)
            four_n2 = op("WILSON_FOUR_N2", "MUL", four_n, nf)
            adjusted = op("WILSON_ADJUSTMENT", "DIV", z2, four_n2)
            radicand = op("WILSON_RADICAND", "ADD", per_trial, adjusted)
            root = square_root("WILSON_SQRT", radicand)
            half = op("WILSON_HALF", "MUL", half_factor, root)
            lower_candidate = op("WILSON_LOWER", "SUB", center, half)
            upper_candidate = op("WILSON_UPPER", "ADD", center, half)
            lower_index = 0 if lower_candidate <= 0.0 else 1
            upper_index = 0 if upper_candidate >= 1.0 else 1
            lower = 0.0 if lower_index == 0 else lower_candidate
            upper = 1.0 if upper_index == 0 else upper_candidate
            for name, value, projected in (("lower", lower, projected_value[0]), ("upper", upper, projected_value[1])):
                for actual in (raw[name], expected[name], projected):
                    observed(actual)
                    work._require(bits(actual) == bits(value), "LP03_WILSON_ENDPOINT_OR_EXPECTATION_MISMATCH")
            work._require(raw_json == expected_json, "LP03_WILSON_RAW_EXPECTATION_WIRE_MISMATCH")
            summary = emitted(dict(successes=successes, trials=trials, confidence_bits=bits(confidence),
                branch=branch, lower_selected_index=lower_index, upper_selected_index=upper_index,
                lower_bits=bits(lower), upper_bits=bits(upper), typed_input_json=input_json.decode("utf-8"),
                original_raw_json=raw_json.decode("utf-8"), preregistered_raw_json=expected_json.decode("utf-8")))
            proof = dict(profile="AS241_ORDERED_BINARY64_WILSON_MODEL_CONFORMANCE_V1",
                intermediate_observation_scope="ALL_INVERSE_NORMAL_AND_WILSON_STAGES_DERIVED_NOT_OBSERVED",
                statistical_authority="NO_EXACT_QUANTILE_OR_COVERAGE_CERTIFICATION",
                model_provenance="CPYTHON_V3_14_6_AS241_SOURCE_MODEL_NOT_COMPILER_BINARY_ATTESTATION",
                log_enclosure=log_proof, cells=tuple(cells), summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_multiple_testing_v1(math_id, input_json, raw_json, expected_json, projected_json, *, work):
        """Pure original BH/BY binary64 derivation, without source authority.

        All intermediate values, including the harmonic fsum, are derived.
        Only the original raw output is an observed native result. Every
        rounded operation is enclosed by its exact nearest-even cell.
        """
        import struct
        from math import isfinite, nextafter, inf
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .specification import decode_evidence_raw_output_v1
        from .serialization import _native_strict_json
        from .parameter_policy import _EvidenceNumericalWorkV1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(type(math_id) is str and math_id in ("MATH-12", "MATH-13"), "LP03_MULTIPLE_REVIEW_PROFILE")
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json, projected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json, projected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_MULTIPLE_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1(math_id, input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1(math_id, raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1(math_id, expected_json, maximum_bytes=65536, maximum_nodes=4096)
            projection = _native_strict_json(projected_json, max_bytes=65536, max_nodes=4096, binary64_numbers=True)
            ps, q = inputs["p_values"], inputs["q"]
            work._require(type(ps) is tuple and 0 < len(ps) <= 4096
                and all(type(p) is float and isfinite(p) and 0 <= p <= 1 for p in ps)
                and type(q) is float and isfinite(q) and 0 < q < 1, "LP03_MULTIPLE_REVIEW_TYPED_ROSTER")
            # Count the complete closed layout before allocating any expanded
            # hypothesis, reciprocal, cell or indexed-projection arrays. The
            # rejected roster is scalar canonical JSON text in this schema.
            count = len(ps)
            cell_count = 6 * count if math_id == "MATH-12" else 7 * count + 1
            proof_nodes = 33 + 101 * count if math_id == "MATH-12" else 46 + 114 * count
            work._require(proof_nodes <= 4096 and 7 + 7 * count <= 4096
                and 128 + 128 * count <= 65536, "LP03_MULTIPLE_REVIEW_COMPLETE_LAYOUT_EXHAUSTED")
            # Reserve an outer-container bound and both copies of the known
            # summary strings. Each emitted fragment subsequently reserves its
            # own eventual whole-proof copy before being retained.
            final_reserved = 2048 + 24 * count
            summary_reserved = 2 * (1024 + 6 * sum(len(value) for value in (input_json, raw_json, expected_json, projected_json))
                + 6 * count * (len(str(count)) + 1))
            work._require(work.consumed["serialized_bytes"] + final_reserved + summary_reserved <= work.limits["max_serialized_bytes"],
                "LP03_MULTIPLE_REVIEW_COMPLETE_BYTES_EXHAUSTED")
            def bits(value):return struct.pack(">d", value).hex()
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_MULTIPLE_REVIEW_BINARY64_INPUT")
                return value, work._binary64_ratio(value, original_input=True)
            def emit(value, *, summary=False):
                nonlocal final_reserved, summary_reserved
                from fractions import Fraction
                upper = 2
                for name, child in value.items():
                    upper += len(name.encode("utf-8")) + 8
                    if type(child) is Fraction:upper += max(1, child.numerator.bit_length()) + max(1, child.denominator.bit_length()) + 40
                    elif type(child) is int:upper += max(1, child.bit_length()) + 1
                    elif type(child) is str:upper += 6 * len(child.encode("utf-8")) + 2
                    else:work._require(False, "LP03_MULTIPLE_REVIEW_FRAGMENT_TYPE")
                pending = 0 if summary else summary_reserved
                work._require(work.consumed["serialized_bytes"] + final_reserved + pending + 2 * upper <= work.limits["max_serialized_bytes"],
                    "LP03_MULTIPLE_REVIEW_COMPLETE_BYTES_EXHAUSTED")
                before = work.consumed["serialized_bytes"]
                frozen = work._emit(value)
                final_reserved += work.consumed["serialized_bytes"] - before
                if summary:summary_reserved = 0
                return {key: dict(child) if type(child) is MappingProxyType else child for key, child in frozen.items()}
            cells = []
            def rounded(value, operation, *, negative_zero=False):
                work._bits(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = -0.0 if value == 0 and negative_zero else float(value)
                work._require(isfinite(candidate), "LP03_MULTIPLE_REVIEW_FINITE_CELL")
                previous, following = nextafter(candidate, -inf), nextafter(candidate, inf)
                work._require(isfinite(previous) and isfinite(following), "LP03_MULTIPLE_REVIEW_FINITE_CELL")
                represented = work._binary64_ratio(candidate)
                lower = work._divide(work._add(work._binary64_ratio(previous), represented), work._fraction(2))
                upper = work._divide(work._add(represented, work._binary64_ratio(following)), work._fraction(2))
                low, high = work._compare(value, lower), work._compare(value, upper)
                even = int.from_bytes(struct.pack(">d", candidate), "big") % 2 == 0
                work._require((low > 0 or low == 0 and even) and (high < 0 or high == 0 and even),
                    "LP03_MULTIPLE_REVIEW_NEAREST_EVEN_CELL_UNPROVEN")
                cells.append(emit(dict(operation=operation, exact_result=value, candidate_bits=bits(candidate), tie_rule="NEAREST_EVEN")))
                return candidate, represented
            def negative(value):return bits(value)[0] in "89abcdef"
            def multiply(first, second, operation):
                return rounded(work._multiply(first[1], second[1]), operation,
                    negative_zero=negative(first[0]) != negative(second[0]))
            def divide(first, second, operation):
                return rounded(work._divide(first[1], second[1]), operation,
                    negative_zero=negative(first[0]) != negative(second[0]))
            one = (1.0, work._fraction(1))
            probabilities = tuple(observed(p) for p in ps); q_value = observed(q)
            count_value = (float(count), work._exact(count))
            order = tuple(sorted(range(count), key=lambda i: (ps[i], i)))
            if math_id == "MATH-13":
                harmonic = tuple(divide(one, (float(rank), work._exact(rank)), "HARMONIC_TERM::" + str(rank)) for rank in range(1, count + 1))
                exact_sum = work._fraction(0)
                for term in harmonic:exact_sum = work._add(exact_sum, term[1])
                correction = rounded(exact_sum, "DERIVED_UNOBSERVED_HARMONIC_FSUM")
            else:correction = one
            largest, thresholds = 0, []
            for rank, original_index in enumerate(order, 1):
                rank_value = (float(rank), work._exact(rank))
                numerator = multiply(rank_value, q_value, "THRESHOLD_NUMERATOR::" + str(rank))
                denominator = multiply(count_value, correction, "THRESHOLD_DENOMINATOR::" + str(rank))
                threshold = divide(numerator, denominator, "THRESHOLD_DIVISION::" + str(rank))
                rejected = work._compare(probabilities[original_index][1], threshold[1]) <= 0
                if rejected:largest = rank
                thresholds.append(emit(dict(rank=rank, original_index=original_index, satisfies_threshold=int(rejected),
                    derived_threshold_bits=bits(threshold[0]), largest_rank_prefix=largest)))
            rejected_indices = tuple(sorted(order[:largest]))
            running, adjusted, reverse = one, [None] * count, []
            for rank in range(count, 0, -1):
                original_index = order[rank - 1]
                first = multiply(probabilities[original_index], count_value, "ADJUSTMENT_COUNT::" + str(rank))
                second = multiply(first, correction, "ADJUSTMENT_CORRECTION::" + str(rank))
                candidate = divide(second, (float(rank), work._exact(rank)), "ADJUSTMENT_DIVISION::" + str(rank))
                chosen = 0 if work._compare(running[1], candidate[1]) <= 0 else 1
                if chosen:running = candidate
                clamped = 0 if work._compare(one[1], running[1]) <= 0 else 1
                adjusted[original_index] = one if clamped == 0 else running
                reverse.append(emit(dict(rank=rank, original_index=original_index, running_selected_index=chosen,
                    clamp_selected_index=clamped, derived_adjusted_bits=bits(adjusted[original_index][0]))))
            work._require(type(raw["largest_rank"]) is int and raw["largest_rank"] == largest
                and type(raw["rejected_original_indices"]) is tuple and all(type(i) is int for i in raw["rejected_original_indices"])
                and raw["rejected_original_indices"] == rejected_indices and len(raw["adjusted_p_values"]) == count,
                "LP03_MULTIPLE_REVIEW_RAW_REJECTIONS")
            for actual, derived in zip((*raw["adjusted_p_values"], raw["correction"]), (*adjusted, correction)):
                observed(actual)
                work._require(bits(actual) == bits(derived[0]), "LP03_MULTIPLE_REVIEW_RAW_BINARY64_JOIN")
            work._require(raw_json == expected_json, "LP03_MULTIPLE_REVIEW_RAW_EXPECTATION_WIRE_MISMATCH")
            projected = dict(rows=[dict(original_index=i, adjusted_p=adjusted[i][0], rejected=i in rejected_indices)
                for i in range(count)], correction=correction[0], largest_rank=largest)
            work._require(deterministic_json(projection).encode("utf-8") == projected_json == deterministic_json(projected).encode("utf-8"),
                "LP03_MULTIPLE_REVIEW_INDEXED_PROJECTION_JOIN")
            summary = emit(dict(math_id=math_id, hypothesis_count=count, largest_rank=largest, rejected_original_indices_json=deterministic_json(rejected_indices),
                correction_bits=bits(correction[0]), typed_input_json=input_json.decode("utf-8"), original_raw_json=raw_json.decode("utf-8"),
                preregistered_raw_json=expected_json.decode("utf-8"), projected_value_json=projected_json.decode("utf-8")), summary=True)
            work._require(len(cells) == cell_count, "LP03_MULTIPLE_REVIEW_COMPLETE_CELL_ROSTER")
            proof = dict(profile="ORDERED_BINARY64_BH_BY_NEAREST_EVEN_V1", intermediate_observation_scope="ALL_INTERMEDIATES_AND_HARMONIC_FSUM_ARE_DERIVED_NOT_OBSERVED",
                sorted_source_indices=order, rounding_cells=tuple(cells), forward_thresholds=tuple(thresholds), reverse_adjustments=tuple(reverse), summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    @staticmethod
    def _bounded_review_calibration_v1(input_json, raw_json, expected_json, projected_value, *, work):
        """Exact ordered M10 conformance over its two original bin policies.

        Every derived binary64 operation must be exact. Other valid native
        calculations remain outside this closed proof profile. Row means and
        sums are derived witnesses, not separately observed native results.
        """
        from math import isfinite
        import struct
        from .context import _native_require
        from .input_resolver import decode_evidence_public_invocation_inputs_v1
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .specification import decode_evidence_raw_output_v1
        _native_require(type(work) is _EvidenceNumericalWorkV1, "LP03_ORIGINAL_NUMERICAL_WORK_REQUIRED")
        with work:
            work._require(all(type(value) is bytes for value in (input_json, raw_json, expected_json))
                and sum(len(value) for value in (input_json, raw_json, expected_json)) <= work.limits["max_serialized_bytes"],
                "LP03_CALIBRATION_REVIEW_INPUT_BYTES")
            inputs = decode_evidence_public_invocation_inputs_v1("MATH-10", input_json, maximum_bytes=65536, maximum_nodes=4096)
            raw = decode_evidence_raw_output_v1("MATH-10", raw_json, maximum_bytes=65536, maximum_nodes=4096)
            expected = decode_evidence_raw_output_v1("MATH-10", expected_json, maximum_bytes=65536, maximum_nodes=4096)
            ps, ys, policy, count = (inputs[key] for key in ("probabilities", "outcomes", "bin_policy", "bin_count"))
            work._require(type(ps) is tuple and 0 < len(ps) <= 4096 and type(ys) is tuple and len(ys) == len(ps)
                and type(count) is int and 0 < count <= 4096 and type(policy) is str
                and policy in ("EQUAL_WIDTH", "EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES")
                and all(type(value) is int and value in (0, 1) for value in ys)
                and (policy == "EQUAL_WIDTH" or count <= len(ps)), "LP03_CALIBRATION_REVIEW_TYPED_ROSTER")
            def bits(value): return struct.pack(">d", value).hex()
            def observed(value):
                work._consumed["input_values"] += 1
                work._require(type(value) is float and isfinite(value), "LP03_CALIBRATION_REVIEW_BINARY64_INPUT")
                return work._binary64_ratio(value, original_input=True)
            def exact(value):
                work._bits(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) + 1076)
                work._consumed["integer_operations"] += 1
                candidate = float(value)
                work._require(isfinite(candidate), "LP03_CALIBRATION_REVIEW_FINITE_INTERMEDIATE")
                represented = work._binary64_ratio(candidate)
                work._require(work._compare(represented, value) == 0, "LP03_CALIBRATION_REVIEW_NONEXACT_BINARY64_INTERMEDIATE")
                return value
            def emitted(values):
                fragment = work._emit(values)
                return {key: dict(value) if type(value) is MappingProxyType else value for key, value in fragment.items()}
            def matches(value, rational):
                represented = observed(value)
                work._require(work._compare(represented, rational) == 0 and bits(value) == bits(float(rational)),
                    "LP03_CALIBRATION_REVIEW_OBSERVED_INTERMEDIATE_MISMATCH")
            zero, one = work._fraction(0), work._fraction(1)
            probabilities = tuple(observed(value) for value in ps)
            work._require(all(work._compare(value, zero) >= 0 and work._compare(value, one) <= 0 for value in probabilities),
                "LP03_CALIBRATION_REVIEW_PROBABILITY_DOMAIN")
            outcomes = tuple(work._exact(value) for value in ys)
            n, requested = work._exact(len(ps)), work._exact(count)
            work._require(raw["bin_policy"] == expected["bin_policy"] == policy
                and type(raw["requested_bin_count"]) is type(expected["requested_bin_count"]) is int
                and raw["requested_bin_count"] == expected["requested_bin_count"] == count,
                "LP03_CALIBRATION_REVIEW_ORIGINAL_BIN_POLICY")
            # Sorting native finite floats has the original stable tie order,
            # including equal signed zeros. No callback or resampling occurs.
            order = tuple(sorted(range(len(ps)), key=ps.__getitem__))
            edge_values, edge_proofs = [], []
            for index in range(count + 1):
                quantile = exact(work._divide(work._exact(index), requested))
                if policy == "EQUAL_WIDTH":
                    result = quantile
                    edge_proofs.append(emitted(dict(edge_ordinal=index, probability=quantile, derived_edge=result)))
                else:
                    position = exact(work._multiply(quantile, work._subtract(n, one)))
                    # The finite roster bounds both native integer conversions.
                    work._bits(max(abs(position.numerator).bit_length(), position.denominator.bit_length()) + 1)
                    work._consumed["integer_operations"] += 1
                    lower = position.numerator // position.denominator
                    upper = lower if position.denominator == 1 else work._int_sum(lower, 1)
                    work._require(0 <= lower <= upper < len(ps), "LP03_CALIBRATION_REVIEW_QUANTILE_INDEX")
                    low, high = probabilities[order[lower]], probabilities[order[upper]]
                    if lower == upper:
                        weight, complement, first, second, result = zero, one, low, zero, low
                    else:
                        weight = exact(work._subtract(position, work._exact(lower)))
                        complement = exact(work._subtract(one, weight))
                        first, second = exact(work._multiply(low, complement)), exact(work._multiply(high, weight))
                        result = exact(work._add(first, second))
                    edge_proofs.append(emitted(dict(edge_ordinal=index, probability=quantile, position=position,
                        lower_index=lower, upper_index=upper, lower_source_index=order[lower], upper_source_index=order[upper],
                        weight=weight, complement=complement, first_product=first, second_product=second, derived_edge=result)))
                edge_values.append(result)
            if policy == "EQUAL_FREQUENCY_TYPE7_COLLAPSE_DUPLICATES":
                edge_values[0], edge_values[-1] = zero, one
                edges = []
                for value in edge_values:
                    if not edges or work._compare(value, edges[-1]) > 0:
                        edges.append(value)
                if len(edges) < 2:
                    edges = [zero, one]
            else:
                edges = edge_values
            work._require(len(raw["effective_edges"]) == len(expected["effective_edges"]) == len(edges)
                and len(raw["bins"]) == len(expected["bins"]) == len(edges) - 1, "LP03_CALIBRATION_REVIEW_EDGE_ROSTER")
            for value, edge in zip(raw["effective_edges"], edges): matches(value, edge)
            total, bin_proofs, memberships = zero, [], []
            for ordinal, (left, right, row) in enumerate(zip(edges, edges[1:], raw["bins"])):
                inclusive = ordinal == len(edges) - 2
                selected = tuple(index for index, value in enumerate(probabilities)
                    if work._compare(left, value) <= 0 and (work._compare(value, right) < 0
                        or inclusive and work._compare(value, right) == 0))
                memberships.extend(selected)
                work._require(type(row["bin_index"]) is type(row["count"]) is int
                    and row["bin_index"] == ordinal and row["count"] == len(selected)
                    and row["right_inclusive"] is inclusive, "LP03_CALIBRATION_REVIEW_BIN_MEMBERSHIP")
                matches(row["left"], left); matches(row["right"], right)
                if not selected:
                    work._require(row["mean_confidence"] is row["empirical_frequency"] is row["absolute_gap"] is None,
                        "LP03_CALIBRATION_REVIEW_EMPTY_BIN")
                    bin_proofs.append(dict(member_indices=(), arithmetic=emitted(dict(bin_index=ordinal, count=0,
                        state="EMPTY_ORIGINAL_BIN", ordered_ece_prefix=total))))
                    continue
                # fsum is mathematically an exact sum followed by one rounding;
                # this profile admits only sums with no rounding at that step.
                sum_p, sum_y = zero, zero
                for index in selected:
                    sum_p = work._add(sum_p, probabilities[index])
                    sum_y = work._add(sum_y, outcomes[index])
                sum_p, sum_y, size = exact(sum_p), exact(sum_y), work._exact(len(selected))
                confidence, frequency = exact(work._divide(sum_p, size)), exact(work._divide(sum_y, size))
                difference = exact(work._subtract(confidence, frequency))
                gap = work._subtract(zero, difference) if work._compare(difference, zero) < 0 else difference
                weight = exact(work._divide(size, n))
                contribution = exact(work._multiply(weight, gap))
                total = exact(work._add(total, contribution))
                for value, derived in ((row["mean_confidence"], confidence), (row["empirical_frequency"], frequency), (row["absolute_gap"], gap)):
                    matches(value, derived)
                bin_proofs.append(dict(member_indices=selected, arithmetic=emitted(dict(bin_index=ordinal, count=len(selected),
                    state="NONEMPTY_ORIGINAL_BIN", derived_probability_sum=sum_p, derived_outcome_sum=sum_y,
                    mean_confidence=confidence, empirical_frequency=frequency, absolute_gap=gap,
                    weight=weight, contribution=contribution, ordered_ece_prefix=total))))
            work._require(len(memberships) == len(ps) and sorted(memberships) == list(range(len(ps))),
                "LP03_CALIBRATION_REVIEW_COMPLETE_MEMBERSHIP")
            for value in (raw["expected_calibration_error"], expected["expected_calibration_error"], projected_value): matches(value, total)
            work._require(raw_json == expected_json, "LP03_CALIBRATION_REVIEW_RAW_EXPECTATION_WIRE_MISMATCH")
            summary = emitted(dict(observation_count=len(ps), requested_bin_count=count, effective_bin_count=len(edges) - 1,
                expected_calibration_error=total, bin_policy=policy, typed_input_json=input_json.decode("utf-8"),
                original_raw_json=raw_json.decode("utf-8"), preregistered_raw_json=expected_json.decode("utf-8")))
            proof = dict(profile="EXACT_BINARY64_ORDERED_CALIBRATION_INTERMEDIATES_V1",
                intermediate_observation_scope="SUMS_AND_INTERMEDIATE_ARITHMETIC_ARE_DERIVED_NOT_OBSERVED",
                sorted_source_indices=order, edge_calculations=tuple(edge_proofs), bin_calculations=tuple(bin_proofs), summary=summary)
            return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(proof, work=work)


    def _calculate_measured_brier_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_forecast_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1
        protocol = operation.registration.protocol
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_BINARY64_BRIER_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_BRIER_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_FORECAST_EVALUATION_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_forecast_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-08"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_BRIER_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-08"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_BRIER_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-08::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-08::1.1R1"
                            and projection.output_unit == lane.raw.output_unit == "squared probability error"
                            and projection.output_basis == lane.raw.output_basis == "PER_SAMPLE_SQUARED_PROBABILITY"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = IndependentEvidenceReviewV1._bounded_review_brier_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projection.projected_value,
                work=operation.numerical_work)
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            bounded, limits = IndependentEvidenceReviewV1._bounded_review_decimal_v1, protocol.numerical_work_limits
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and bounded(debit.amount_text, limits) == bounded(credit.amount_text, limits) == bounded(baseline["cash"], limits)
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        _EvidenceReviewOperationV1._check_current_v1(operation)
        calculation = dict(method="EXACT_RATIONAL_BRIER_WITH_BINARY64_INTERMEDIATE_PROOFS", lane_calculations=tuple(calculations),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        return IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=operation.numerical_work)


    def _calculate_measured_log_loss_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_log_loss_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        registration = operation.registration
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_CERTIFIED_BINARY64_LOG_LOSS_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_LOG_LOSS_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_LOG_LOSS_EVALUATION_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_log_loss_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-09"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_LOG_LOSS_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-09"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_LOG_LOSS_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-09::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-09::1.1R1"
                            and projection.output_unit == lane.raw.output_unit == "nats/sample"
                            and projection.output_basis == lane.raw.output_basis == "per_sample_natural_log_loss"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = IndependentEvidenceReviewV1._bounded_review_log_loss_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projection.projected_value,
                work=operation.numerical_work)
            with work:
                value = work._binary64_ratio(projection.projected_value, original_input=True)
                work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                              "LP03_LOG_LOSS_RESULT_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="RATIONAL_LOG_LOSS_FROM_ORIGINAL_DATASET_AND_CLIP_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation


    def _calculate_measured_spa_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_spa_source_slices_v1, _evidence_spa_projection_mapping_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _evidence_canonical_object_v1
        registration = operation.registration
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_SPA_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_SPA_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_SPA_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_spa_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-16"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_SPA_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-16"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_SPA_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-16::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-16::2.0.0"
                            and projection.output_unit == lane.raw.output_unit == "mixed; member-specific"
                            and projection.output_basis == lane.raw.output_basis == "studentized_loss_differential_spa_p_value"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            _native_require(protocol.formula_seed_bindings == registration.preparation.plan.formula_seed_bindings
                == (("MATH-16", typed["seed"]),), "LP03_SPA_REVIEW_ORIGINAL_SEED_AND_REPLAY_ROSTER")
            work._assert_bootstrap_custody_v1()
            original_replays = tuple(work._bootstrap_invocations)
            projected = _evidence_spa_projection_mapping_v1(projection.projected_value)
            proof = IndependentEvidenceReviewV1._bounded_review_spa_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projected,
                expected_environment=registration.preparation.plan.exact_environment_identity, work=operation.numerical_work)
            work._assert_bootstrap_custody_v1()
            _native_require(len(work._bootstrap_invocations) == len(original_replays) + 1
                and all(work._bootstrap_invocations[index] is original for index, original in enumerate(original_replays))
                and len(original_replays) == len(calculations)
                and work._bootstrap_invocations[-1][0].completed[2] == deterministic_json(proof),
                "LP03_SPA_REVIEW_ORIGINAL_COMPLETED_PROOF")
            with work:
                enclosure = work._shift(1, 540)
                coordinates = ((projected["statistic"], 0, enclosure), (projected["p_value"], 0, 1),
                    *((value, -1, 1) for value in projected["candidate_means"]),
                    *((value, 0, 32) for value in projected["long_run_variances"]),
                    *((value, 0, enclosure) for value in projected["simulated_statistics"]))
                for endpoint, low, high in coordinates:
                    value = work._binary64_ratio(endpoint, original_input=True)
                    work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0
                        and work._compare(value, work._fraction(low)) >= 0 and work._compare(value, work._fraction(high)) <= 0,
                        "LP03_SPA_RESULT_MEMBER_OUT_OF_BOUNDS")
                work._require(projected["p_value"] > 0.0 and projected["reject"] is (projected["p_value"] <= typed["alpha"]),
                    "LP03_SPA_RESULT_REJECT_JOIN")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload=_evidence_canonical_object_v1(
                    deterministic_json(event["payload"]).encode("utf-8"), max_bytes=65536),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_SPA_FROM_ORIGINAL_COMPLETE_FAMILY_AND_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation


    def _calculate_measured_reality_check_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_reality_check_source_slices_v1, _evidence_reality_check_projection_mapping_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _evidence_canonical_object_v1
        registration = operation.registration
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_REALITY_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_REALITY_CHECK_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_reality_check_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-15"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_REALITY_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-15"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_REALITY_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-15::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-15::2.0.0"
                            and projection.output_unit == lane.raw.output_unit == "mixed; member-specific"
                            and projection.output_basis == lane.raw.output_basis == "benchmark_candidate_loss_differential_p_value"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            _native_require(protocol.formula_seed_bindings == registration.preparation.plan.formula_seed_bindings
                == (("MATH-15", typed["seed"]),), "LP03_REALITY_REVIEW_ORIGINAL_SEED_AND_REPLAY_ROSTER")
            work._assert_bootstrap_custody_v1()
            original_replays = tuple(work._bootstrap_invocations)
            all_zero = all(value == 0.0 for row in typed["loss_differentials"] for value in row)
            projected = _evidence_reality_check_projection_mapping_v1(projection.projected_value)
            proof = IndependentEvidenceReviewV1._bounded_review_reality_check_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projected,
                expected_environment=registration.preparation.plan.exact_environment_identity, work=operation.numerical_work)
            work._assert_bootstrap_custody_v1()
            _native_require(len(work._bootstrap_invocations) == len(original_replays) + (0 if all_zero else 1)
                and all(work._bootstrap_invocations[index] is original for index, original in enumerate(original_replays))
                and (all_zero and proof["branch"] == "ALL_ZERO_NO_RNG_CONSTRUCTION" and not proof["draws"]
                    or not all_zero and work._bootstrap_invocations[-1][0].completed[2] == deterministic_json(proof)),
                "LP03_REALITY_REVIEW_ORIGINAL_COMPLETED_PROOF")
            with work:
                coordinates = ((projected["statistic"], 0, 2), (projected["p_value"], 0, 1),
                    *((value, -1, 1) for value in projected["candidate_means"]),
                    *((value, 0, 4) for value in projected["simulated_statistics"]))
                for endpoint, low, high in coordinates:
                    value = work._binary64_ratio(endpoint, original_input=True)
                    work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0
                        and work._compare(value, work._fraction(low)) >= 0 and work._compare(value, work._fraction(high)) <= 0,
                        "LP03_REALITY_RESULT_MEMBER_OUT_OF_BOUNDS")
                work._require(projected["p_value"] > 0.0 and projected["reject"] is (projected["p_value"] <= typed["alpha"]),
                    "LP03_REALITY_RESULT_REJECT_JOIN")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload=_evidence_canonical_object_v1(
                    deterministic_json(event["payload"]).encode("utf-8"), max_bytes=65536),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_REALITY_CHECK_FROM_ORIGINAL_COMPLETE_FAMILY_AND_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation


    def _calculate_measured_bootstrap_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_bootstrap_source_slices_v1, _evidence_bootstrap_projection_mapping_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _evidence_canonical_object_v1
        registration = operation.registration
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_ORDERED_STATIONARY_BOOTSTRAP_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_BOOTSTRAP_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_STATIONARY_BOOTSTRAP_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_bootstrap_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-14"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_BOOTSTRAP_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-14"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_BOOTSTRAP_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-14::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-14::2.0.0"
                            and projection.output_unit == lane.raw.output_unit == "statistic_unit"
                            and projection.output_basis == lane.raw.output_basis == "bootstrap_statistic_distribution_and_interval"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            _native_require(protocol.formula_seed_bindings == registration.preparation.plan.formula_seed_bindings
                == (("MATH-14", typed["seed"]),) and len(work._bootstrap_invocations) == len(calculations),
                "LP03_BOOTSTRAP_REVIEW_ORIGINAL_SEED_AND_REPLAY_ROSTER")
            projected = _evidence_bootstrap_projection_mapping_v1(projection.projected_value)
            proof = IndependentEvidenceReviewV1._bounded_review_bootstrap_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projected,
                expected_environment=registration.preparation.plan.exact_environment_identity, work=operation.numerical_work)
            _native_require(len(work._bootstrap_invocations) == len(calculations) + 1
                and work._bootstrap_invocations[-1][0].completed[2] == deterministic_json(proof),
                "LP03_BOOTSTRAP_REVIEW_ORIGINAL_COMPLETED_PROOF")
            with work:
                for endpoint in (projected["sample_mean"], projected["lower"], projected["upper"], *projected["bootstrap_distribution"]):
                    value = work._binary64_ratio(endpoint, original_input=True)
                    work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                                  "LP03_BOOTSTRAP_RESULT_ENDPOINT_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload=_evidence_canonical_object_v1(
                    deterministic_json(event["payload"]).encode("utf-8"), max_bytes=65536),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_STATIONARY_BOOTSTRAP_FROM_ORIGINAL_SERIES_AND_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation


    def _calculate_measured_wilson_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_wilson_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        registration = operation.registration
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_AS241_BINARY64_WILSON_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_WILSON_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_BERNOULLI_COUNT_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_wilson_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-11"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_WILSON_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-11"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_WILSON_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-11::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-11::1.1R1"
                            and projection.output_unit == lane.raw.output_unit == "probability"
                            and projection.output_basis == lane.raw.output_basis == "lower_upper_probability_interval"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = IndependentEvidenceReviewV1._bounded_review_wilson_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projection.projected_value,
                work=operation.numerical_work)
            with work:
                for endpoint in projection.projected_value:
                    value = work._binary64_ratio(endpoint, original_input=True)
                    work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                                  "LP03_WILSON_RESULT_ENDPOINT_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload_json=deterministic_json(event["payload"]),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_WILSON_FROM_ORIGINAL_COUNTS_AND_CONFIDENCE_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation


    def _calculate_measured_quantum_constructor_v1(self, operation, baseline_slice, snapshot):
        """Review the paired raw results and original typed constructor bytes."""
        from .context import _native_require
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import (_evidence_independent_quantum_raw_v1, _evidence_original_quantum_sources_v1,
            _evidence_original_execution_source_material_digest_v1)
        from .persistence import _EvidenceLaneOperationV1, _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1

        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        math_id = protocol.numeric_profile["math_id"]
        original = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        proof = original[8]
        association = registration.review_numerical_original
        _native_require(association == (operation, None) and operation.numerical_result_original is None
            and work is operation.original[15] and proof["profile"] == "ORIGINAL_QUANTUM_CONSTRUCTOR_ADMISSION_V1",
            "LP03_QUANTUM_REVIEW_ORIGINAL_NUMERICAL_CUSTODY")
        expected = proof["expected_raw_record_json"]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(item for item in baseline_slice.reconstructed_canonical_events if item["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_QUANTUM_REVIEW_ORIGINAL_BASELINE")
        baseline = baselines[0]["values"]["baseline"]
        lanes = []
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER"), strict=True):
            raw, records, exchange = lane.raw, lane.records, lane.exchange
            projection, segment = tuple(row.typed_payload.record for row in records.receipt_records[1:3])
            packet = EvidenceInvocationInputsV1._require_original_v1(exchange[0], lane.attempt)
            _native_require(packet.math_spec_id == math_id and segment.count == 1 and not segment.gap_dispositions
                and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_ORIGINAL_QUANTUM_INPUT",
                "LP03_QUANTUM_REVIEW_ORIGINAL_LANE")
            source = segment.exact_ordered_events[0]["payload"]
            parts, values, scope = _evidence_original_quantum_sources_v1(source, math_id=math_id)
            _native_require(deterministic_json(values) == deterministic_json(packet.authoritative_values)
                and _evidence_original_execution_source_material_digest_v1(source, parts) == proof["original_quantum_source_material_sha256"]
                and tuple(part.original_record_refs[0].record_id for part in parts) == protocol.coverage_eligibility["source_record_refs"]
                and scope["original_lock_id"] == proof["original_lock_id"] == lane.attempt.payload.input_lock_ref
                and proof["original_quantum_lock"] == lane.attempt.payload.component_and_callback_pins["quantum_original_lock"]
                and deterministic_json(scope["original_economic_basis"]) == deterministic_json(proof["original_economic_basis"]),
                "LP03_QUANTUM_REVIEW_ORIGINAL_PREREGISTERED_INPUTS")
            for part in parts:
                joined = tuple(item for item in exchange[0]._source_slices if item.original_record_refs == part.original_record_refs)
                _native_require(len(joined) == 1 and deterministic_json(joined[0]) == deterministic_json(part),
                    "LP03_QUANTUM_REVIEW_ORIGINAL_PUBLISHED_SOURCE")
            receipt = _EvidenceLaneOperationV1._require_original_quantum_constructor_v1(lane)
            original_json = exchange[2]["quantum_constructor_receipt_json"]
            _native_require(deterministic_json(receipt) == original_json == deterministic_json(projection.projected_value)
                and projection.original_raw_receipt_ref == raw.record_id,
                "LP03_QUANTUM_REVIEW_ORIGINAL_TYPED_PROJECTION")
            control_ref = "ORIGINAL_COMPARISON_DURABLE_COMPUTATION_ONLY"
            if math_id != "MATH-52":
                trace = records.receipt_records[3]
                control_ref = trace.record_id
                _native_require(trace.typed_payload.reconstruct(QuantumTraceValidationReceiptV1) == receipt
                    and projection.supplementary_measurement_refs == (control_ref,),
                    "LP03_QUANTUM_REVIEW_ORIGINAL_SPECIAL_CONTROL")
            else:
                _native_require(len(records.receipt_records) == 3 and not projection.supplementary_measurement_refs,
                    "LP03_QUANTUM_REVIEW_ORIGINAL_COMPARISON_ROSTER")
            independent = _evidence_independent_quantum_raw_v1(math_id, values, work=work)
            _native_require(deterministic_json(independent) == raw.existing_receipt.output_json == expected,
                "LP03_QUANTUM_REVIEW_INDEPENDENT_ORIGINAL_RAW")
            debit, credit = records.journal_postings
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                and debit.amount_text == credit.amount_text == baseline["cash"],
                "LP03_QUANTUM_REVIEW_ORIGINAL_BALANCED_NO_EFFECT")
            lanes.append(dict(lane=name, raw_ref=raw.record_id, projection_ref=projection.record_id, event_segment_ref=segment.record_id,
                original_source_payload_json=deterministic_json(source), original_raw_json=raw.existing_receipt.output_json,
                constructor_json=original_json, trace_control_ref_or_absence=control_ref,
                native_invocation=_evidence_canonical_object_v1(deterministic_json(exchange[2]["invocation_measurement"]).encode("utf-8")),
                baseline_ref=baseline_ref, baseline_amount=baseline["cash"],
                posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculated = dict(method="ORIGINAL_MEASURED_QUANTUM_CONSTRUCTOR_REVIEW_V1", math_id=math_id,
            lane_calculations=tuple(lanes), independent_registration_proof=proof,
            registration_numerical_consumption=dict(original[7]), original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed))
        result = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculated, work=work))
        _native_require(registration.review_numerical_original is association and registration.numerical_original is original
            and work._original is operation.original[16], "LP03_QUANTUM_REVIEW_ORIGINAL_NUMERICAL_CUSTODY")
        completion = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), result, deterministic_json(result))
        operation.numerical_result_original = completion
        registration.review_numerical_original = (operation, completion)
        _EvidenceReviewOperationV1._check_current_v1(operation)
        return result


    def _calculate_measured_private_execution_v1(self, operation, baseline_slice, snapshot):
        """Review exact original lane values and prepare signed proof data."""
        from hashlib import sha256

        from .context import _native_require
        from .errors import ReasonCode
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import (_evidence_independent_decimal_execution_v1, _evidence_original_binary_book_bounds_v1,
            _evidence_original_private_input_profile_v1, _evidence_original_private_inputs_v1,
            _evidence_original_execution_source_material_digest_v1)
        from .persistence import _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1

        registration = operation.registration
        protocol, work = registration.protocol, operation.numerical_work
        math_id = protocol.numeric_profile["math_id"]
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        expected = registered[8]["expected_raw_record_json"]
        association = registration.review_numerical_original
        _native_require(association == (operation, None) and operation.numerical_result_original is None
            and work is operation.original[15], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        anchors = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(anchors) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = anchors[0]["values"]["baseline"]
        lanes = []
        common = None
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER"), strict=True):
            raw, records, exchange = lane.raw, lane.records, lane.exchange
            projection, segment = tuple(row.typed_payload.record for row in records.receipt_records[1:])
            _native_require(projection.original_raw_receipt_ref == raw.record_id
                and segment.count == 1 and not segment.gap_dispositions
                and segment.exact_ordered_events[0]["kind"] == _evidence_original_private_input_profile_v1(math_id)[1],
                "LP03_PRIVATE_EXECUTION_REVIEW_ORIGINAL_RESULT")
            source = segment.exact_ordered_events[0]["payload"]
            parts, values, authority = _evidence_original_private_inputs_v1(source, math_id=math_id)
            original = EvidenceInvocationInputsV1._require_original_v1(exchange[0], lane.attempt)
            if math_id in ("MATH-36", "MATH-39", "MATH-41", "MATH-42", "MATH-43", "MATH-44"):
                material = _evidence_original_execution_source_material_digest_v1(source, parts)
                material_field = ("original_queue_source_material_sha256" if math_id == "MATH-39"
                    else "original_binary_book_source_material_sha256" if math_id == "MATH-36"
                    else "original_binary64_source_material_sha256")
                _native_require(material == registered[8][material_field],
                    "LP03_QUEUE_REVIEW_REGISTERED_SOURCE_MATERIAL" if math_id == "MATH-39"
                    else "LP03_BINARY_BOOK_REVIEW_REGISTERED_SOURCE_MATERIAL" if math_id == "MATH-36"
                    else "LP03_BINARY64_REVIEW_REGISTERED_SOURCE_MATERIAL")
            else:
                material = deterministic_json(tuple(part.reconstructed_canonical_events[0] for part in parts))
            if common is None:
                common = material
            _native_require(material == common and math_id == original.math_spec_id
                and deterministic_json(values) == deterministic_json(original.authoritative_values)
                and tuple(part.original_record_refs[0].record_id for part in parts) == protocol.coverage_eligibility["source_record_refs"]
                and (authority["unit"], authority["basis"]) == (projection.output_unit, projection.output_basis),
                "LP03_PRIVATE_EXECUTION_REVIEW_ORIGINAL_ASSOCIATION")
            for part in parts:
                joined = tuple(item for item in exchange[0]._source_slices if item.original_record_refs == part.original_record_refs)
                _native_require(len(joined) == 1 and deterministic_json(joined[0]) == deterministic_json(part),
                    "LP03_PRIVATE_EXECUTION_REVIEW_ORIGINAL_SLICE")
            if math_id == "MATH-36":
                _evidence_original_binary_book_bounds_v1(registered[8]["claim_bounds"], values, work=work)
            independent_raw, arithmetic = _evidence_independent_decimal_execution_v1(math_id, values, work=work,
                authority=authority["exact_original_authority"])
            projected = (dict(lcb_net=independent_raw["lcb_net"], raw_gate=independent_raw["trade_gate"],
                no_order_authority=True, decision=arithmetic["decision"]) if math_id == "MATH-45"
                else independent_raw["amount_after_rounding"] if math_id == "MATH-35" else independent_raw)
            if math_id == "MATH-41":
                work._require(raw.existing_receipt.output_json == deterministic_json(independent_raw),
                    "LP03_MEASURED_DECAY_NATIVE_ROUNDING_UNCERTIFIED", reason=ReasonCode.EVIDENCE_NUMERIC_UNCERTIFIED)
            _native_require(raw.existing_receipt.output_json == deterministic_json(independent_raw) == expected
                and deterministic_json(projection.projected_value) == deterministic_json(projected),
                "LP03_PRIVATE_EXECUTION_REVIEW_INDEPENDENT_ARITHMETIC")
            debit, credit = records.journal_postings
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                and debit.amount_text == credit.amount_text == baseline["cash"],
                "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            lanes.append(dict(lane=name, raw_ref=raw.record_id, projection_ref=projection.record_id,
                event_segment_ref=segment.record_id, original_source_payload_json=deterministic_json(source),
                original_raw_json=deterministic_json(independent_raw), projected_json=deterministic_json(projected),
                native_invocation=_evidence_canonical_object_v1(deterministic_json(exchange[2]["invocation_measurement"]).encode("utf-8")),
                independent_arithmetic_sha256=sha256(deterministic_json(arithmetic).encode("utf-8")).hexdigest(),
                original_authority_sha256=sha256(deterministic_json(authority["exact_original_authority"]).encode("utf-8")).hexdigest(),
                baseline_ref=baseline_ref, baseline_amount=baseline["cash"], posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method=("ORIGINAL_PRIVATE_EXECUTION_BINARY64_REVIEW_V2" if math_id in ("MATH-41", "MATH-42", "MATH-43", "MATH-44")
            else "ORIGINAL_PRIVATE_EXECUTION_DECIMAL_REVIEW_V1"), math_id=math_id,
            lane_calculations=tuple(lanes), independent_registration_proof=registered[8],
            registration_numerical_consumption=dict(registered[7]), original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed))
        result = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is association and registration.numerical_original is registered
            and work._original is operation.original[16], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        completion = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), result, deterministic_json(result))
        operation.numerical_result_original = completion
        registration.review_numerical_original = (operation, completion)
        _EvidenceReviewOperationV1._check_current_v1(operation)
        return result

    def _calculate_measured_private_analytic_v1(self, operation, baseline_slice, snapshot):
        """Review the original source, measured raw value and certified projection."""
        from hashlib import sha256
        import struct

        from .context import _native_require
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import _evidence_analytic_private_sources_v1, _evidence_independent_private_analytic_calculation_v1
        from .persistence import _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1

        registration = operation.registration
        protocol, work = registration.protocol, operation.numerical_work
        profile = protocol.numeric_profile
        math_id = profile["math_id"]
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        association = registration.review_numerical_original
        _native_require(association == (operation, None) and operation.numerical_result_original is None
            and work is operation.original[15], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        expected = registration.registration_policy[0]["comparator_plan"]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baseline_rows = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baseline_rows) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baseline_rows[0]["values"]["baseline"]
        lanes = []
        sources = None
        for lane, lane_name in zip(operation.parent.lanes, ("REPLAY", "PAPER"), strict=True):
            raw, records, exchange = lane.raw, lane.records, lane.exchange
            projection, segment, conversion = tuple(row.typed_payload.record for row in records.receipt_records[1:])
            _native_require(conversion is lane.analytic_conversion_record
                and conversion.original_raw_receipt_ref == raw.record_id
                and projection.numerical_conversion_ref_or_absence == conversion.record_id
                and conversion.numerical_work_limits == profile["conversion_work_limits"]
                and type(conversion.certificate_json_or_absence) is str
                and segment.count == 1 and not segment.gap_dispositions
                and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_PRIVATE_ANALYTIC_INPUT",
                "LP03_ANALYTIC_REVIEW_ORIGINAL_CONVERSION_AND_EVENT")
            source = segment.exact_ordered_events[0]["payload"]
            parts, inputs, scope = _evidence_analytic_private_sources_v1(source, math_id=math_id)
            original = EvidenceInvocationInputsV1._require_original_v1(exchange[0], lane.attempt)
            material = deterministic_json(tuple(part.reconstructed_canonical_events[0] for part in parts))
            if sources is None:
                sources = material
            _native_require(material == sources and original.math_spec_id == math_id
                and deterministic_json(inputs) == deterministic_json(original.authoritative_values)
                and tuple(part.original_record_refs[0].record_id for part in parts) == protocol.coverage_eligibility["source_record_refs"]
                and (scope["unit"], scope["basis"]) == (projection.output_unit, projection.output_basis)
                and (math_id != "MATH-29" or conversion.original_input_weights_ref_or_absence == parts[0].original_record_refs[0]),
                "LP03_ANALYTIC_REVIEW_ORIGINAL_INPUT_ASSOCIATION")
            for part in parts:
                joined = tuple(item for item in exchange[0]._source_slices if item.original_record_refs == part.original_record_refs)
                _native_require(len(joined) == 1 and deterministic_json(joined[0]) == deterministic_json(part),
                    "LP03_ANALYTIC_REVIEW_ORIGINAL_SLICE")
            raw_json = raw.existing_receipt.output_json
            cert_json = conversion.certificate_json_or_absence
            calculated = _evidence_independent_private_analytic_calculation_v1(math_id, inputs, raw_json=raw_json,
                certificate_json=cert_json, work=work, unit=scope["unit"], basis=scope["basis"])
            bits = struct.pack(">d", projection.projected_value).hex()
            _native_require(raw_json == expected["expected_raw_record_json"]
                and bits == calculated["original_analytic_binary64_bits"] == expected["expected_analytic_binary64_bits"],
                "LP03_ANALYTIC_REVIEW_ORIGINAL_PREREGISTERED_VALUE")
            debit, credit = records.journal_postings
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                and debit.amount_text == credit.amount_text == baseline["cash"]
                and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"],
                "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            lanes.append(dict(lane=lane_name, raw_ref=raw.record_id, projection_ref=projection.record_id,
                conversion_ref=conversion.record_id, event_segment_ref=segment.record_id,
                original_source_payload_json=deterministic_json(source), raw_output_json=raw_json,
                original_binary64_bits=bits, certificate_json=cert_json,
                conversion_record_json=deterministic_json(conversion),
                native_invocation=_evidence_canonical_object_v1(
                    deterministic_json(exchange[2]["invocation_measurement"]).encode("utf-8")),
                independent_proof_sha256=sha256(deterministic_json(calculated).encode("utf-8")).hexdigest(),
                baseline_ref=baseline_ref, baseline_amount=baseline["cash"], posted_debit=debit.amount_text,
                posted_credit=credit.amount_text))
        calculation = dict(method="ORIGINAL_PRIVATE_ANALYTIC_REVIEW_V1", math_id=math_id, lane_calculations=tuple(lanes),
            independent_registration_proof=registered[8], registration_numerical_consumption=dict(registered[7]),
            original_numerical_limits=dict(protocol.numerical_work_limits), review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(work.consumed))
        result = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is association and registration.numerical_original is registered
            and work._original is operation.original[16], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original_result = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), result, deterministic_json(result))
        operation.numerical_result_original = original_result
        registration.review_numerical_original = (operation, original_result)
        _EvidenceReviewOperationV1._check_current_v1(operation)
        return result


    def _calculate_measured_recorded_ope_point_v1(self, operation, baseline_slice, snapshot):
        """Recompute the two measured point estimates over their exact original rows."""
        from hashlib import sha256
        from .context import _native_require
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import _evidence_recorded_ope_source_data_v1, _LP03_OPE_POINT_PROJECTION_PROFILES_V1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1
        from .specification import decode_evidence_raw_output_v1

        registration = operation.registration
        work = operation.numerical_work
        protocol = registration.protocol
        profile = protocol.numeric_profile
        math_id = profile["math_id"]
        field, _, basis, implementation = _LP03_OPE_POINT_PROJECTION_PROFILES_V1[math_id]
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        association = registration.review_numerical_original
        _native_require(association == (operation, None) and operation.numerical_result_original is None
            and work is operation.original[15], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        expected = registration.registration_policy[0]["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baseline_rows = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baseline_rows) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baseline_rows[0]["values"]["baseline"]
        lanes = []
        common_originals = None
        with work:
            for lane, lane_name in zip(operation.parent.lanes, ("REPLAY", "PAPER"), strict=True):
                raw, records, segment_exchange = lane.raw, lane.records, lane.exchange
                projection, segment = tuple(row.typed_payload.record for row in records.receipt_records[1:3])
                _native_require(segment.count == 1 and not segment.gap_dispositions
                    and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_RECORDED_OPE_POINT",
                    "LP03_OPE_POINT_REVIEW_ORIGINAL_EVENT")
                source = segment.exact_ordered_events[0]["payload"]
                parts, inputs, row_ids, _ = _evidence_recorded_ope_source_data_v1(source, math_id=math_id)
                original = EvidenceInvocationInputsV1._require_original_v1(segment_exchange[0], lane.attempt)
                input_wire = deterministic_json(inputs).encode("utf-8")
                _native_require(original.math_spec_id == math_id
                    and input_wire == deterministic_json(original.authoritative_values).encode("utf-8")
                    and row_ids == profile["ordered_original_row_ids"]
                    and tuple(part.original_record_refs[0].record_id for part in parts) == protocol.coverage_eligibility["source_record_refs"]
                    and projection.original_raw_receipt_ref == raw.record_id
                    and projection.original_implementation_ref == raw.existing_receipt.implementation_id == implementation
                    and projection.output_basis == basis, "LP03_OPE_POINT_REVIEW_ORIGINAL_ASSOCIATION")
                for part in parts:
                    joined = tuple(item for item in segment_exchange[0]._source_slices if item.original_record_refs == part.original_record_refs)
                    _native_require(len(joined) == 1 and deterministic_json(joined[0]) == deterministic_json(part),
                        "LP03_OPE_POINT_REVIEW_ORIGINAL_SLICE")
                material = deterministic_json(tuple(part.reconstructed_canonical_events[0] for part in parts))
                if common_originals is None:
                    common_originals = material
                _native_require(material == common_originals, "LP03_OPE_POINT_REVIEW_PAIRED_ORIGINAL_ROWS")
                actual = raw.existing_receipt.output_json.encode("utf-8")
                result = decode_evidence_raw_output_v1(math_id, actual, maximum_bytes=65536, maximum_nodes=4096)
                projected = result if field == "$" else result[field]
                _native_require(deterministic_json(projected) == deterministic_json(projection.projected_value),
                    "LP03_OPE_POINT_REVIEW_ORIGINAL_POINT_PROJECTION")
                estimate = IndependentEvidenceReviewV1._bounded_review_recorded_ope_v1(math_id, input_wire, actual, expected, work=work)
                debit, credit = records.journal_postings
                amounts = tuple(work._exact(work.parse_decimal_v1(value)) for value in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                    "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
                _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                    and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"], "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
                measurement = _evidence_canonical_object_v1(deterministic_json(segment_exchange[2]["invocation_measurement"]).encode("utf-8"))
                lanes.append(dict(lane=lane_name, raw_ref=raw.record_id, projection_ref=projection.record_id,
                    event_segment_ref=segment.record_id, original_source_payload_json=deterministic_json(source),
                    raw_output_json=actual.decode("utf-8"), exact_projection_json=deterministic_json(projected),
                    native_observation=measurement, independent_proof_sha256=sha256(deterministic_json(estimate).encode("utf-8")).hexdigest(),
                    baseline_ref=baseline_ref, baseline_amount=baseline["cash"],
                    posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORIGINAL_RECORDED_OPE_POINT_ESTIMATOR_REVIEW_V1", math_id=math_id, lane_calculations=tuple(lanes),
            original_policy_value_authority="ABSENT_SOFTWARE_CONFORMANCE_ONLY", independent_registration_proof=registered[8],
            registration_numerical_consumption=dict(registered[7]), original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed))
        result = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is association and registration.numerical_original is registered
            and work._original is operation.original[16], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original_result = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), result, deterministic_json(result))
        operation.numerical_result_original = original_result
        registration.review_numerical_original = (operation, original_result)
        return result

    def _calculate_measured_recorded_dr_v1(self, operation, baseline_slice, snapshot):
        """Independently review the original estimator and exact conditional interval."""
        from hashlib import sha256
        from .context import _native_require
        from .evidence_execution import measure_dr_score_uncertainty_v1
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import _evidence_dr_original_source_data_v1, _evidence_dr_review_source_capsule_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1

        registration,work=operation.registration,operation.numerical_work
        protocol=registration.protocol
        profile=protocol.numeric_profile
        registered=_EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        association=registration.review_numerical_original
        _native_require(association==(operation,None) and operation.numerical_result_original is None
            and work is operation.original[15], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        policy,claim=registration.registration_policy
        expected=policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        baseline_ref=snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines=tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"]==baseline_ref)
        _native_require(len(baselines)==1,"LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline=baselines[0]["values"]["baseline"]
        common_capsule = None
        lanes=[]
        with work:
            for lane,name in zip(operation.parent.lanes,("REPLAY","PAPER"),strict=True):
                groups,uncertainty=lane.recorded_dr_records
                projection=lane.records.receipt_records[1].typed_payload.record
                segment=lane.records.receipt_records[2].typed_payload.record
                event=segment.exact_ordered_events[0]
                _native_require(segment.count==1 and not segment.gap_dispositions
                    and event["kind"]=="SYNTHETIC_RECORDED_DR_UNCERTAINTY"
                    and uncertainty.availability_disposition=="ORIGINAL_CONDITIONAL_RECORDED_SCORE_INTERVAL",
                    "LP03_DR_REVIEW_ORIGINAL_COMPLETE_EVENT")
                fold_refs=projection.supplementary_measurement_refs
                raw_ref=lane.raw.record_id
                source=event["payload"]
                parts,values,original_policy,policy_json,original_fit_after_first_label=_evidence_dr_original_source_data_v1(source,original_raw_ref=raw_ref)
                original=EvidenceInvocationInputsV1._require_original_v1(lane.exchange[0],lane.attempt)
                input_wire=deterministic_json(values).encode("utf-8")
                actual=lane.raw.existing_receipt.output_json.encode("utf-8")
                _native_require(original.math_spec_id=="MATH-22" and not original_fit_after_first_label
                    and input_wire==deterministic_json(original.authoritative_values).encode("utf-8")
                    and tuple(part.original_record_refs[0].record_id for part in parts)==protocol.coverage_eligibility["source_record_refs"]
                    and fold_refs==(groups.record_id,uncertainty.record_id)
                    and uncertainty.group_measurement_ref==groups.record_id
                    and uncertainty.original_estimator_ref==groups.original_estimator_ref==raw_ref
                    and projection.original_raw_receipt_ref==raw_ref and projection.output_basis==profile["target"]
                    and original_policy["protocol_ref"]==protocol.parameter_protocol_ref,
                    "LP03_DR_REVIEW_ORIGINAL_ESTIMATOR_AND_UNCERTAINTY_JOIN")
                for part in parts:
                    actual_parts=tuple(row for row in lane.exchange[0]._source_slices if row.original_record_refs==part.original_record_refs)
                    _native_require(len(actual_parts)==1 and deterministic_json(actual_parts[0])==deterministic_json(part),
                        "LP03_DR_REVIEW_ORIGINAL_SOURCE_CUSTODY")
                capsule, access_wall_ns = _evidence_dr_review_source_capsule_v1(source)
                if common_capsule is None:
                    common_capsule = capsule
                _native_require(capsule == common_capsule, "LP03_DR_REVIEW_PAIRED_SOURCE_CUSTODY")
                estimate=IndependentEvidenceReviewV1._bounded_review_recorded_ope_v1("MATH-22",input_wire,actual,expected,work=work)
                limits=lane.attempt.payload.budgets
                frame_bytes=min(limits.frame_byte_limit,limits.segment_max_bytes,limits.max_input_bytes)
                certificate=measure_dr_score_uncertainty_v1(actual,input_json=input_wire,policy_json=policy_json,
                    maximum_input_bytes=frame_bytes,maximum_input_nodes=4096,
                    maximum_output_bytes=frame_bytes,maximum_output_nodes=4096,work=work)
                _native_require(certificate==uncertainty.numeric_certificate_json.encode("utf-8"),
                    "LP03_DR_REVIEW_ORIGINAL_CONDITIONAL_CERTIFICATE_CONFORMANCE")
                debit,credit=lane.records.journal_postings
                amounts=tuple(work._exact(work.parse_decimal_v1(value)) for value in (debit.amount_text,credit.amount_text,baseline["cash"]))
                work._require(work._compare(amounts[0],amounts[1])==work._compare(amounts[1],amounts[2])==0,
                    "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
                _native_require(debit.entry_side.value=="DEBIT" and credit.entry_side.value=="CREDIT"
                    and debit.currency_or_asset==credit.currency_or_asset==baseline["currency"],"LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
                lanes.append(dict(lane=name,event_segment_ref=segment.record_id,original_raw_ref=raw_ref,projection_ref=projection.record_id,
                    group_measurement_ref=groups.record_id,uncertainty_ref=uncertainty.record_id,
                    original_source_access_wall_ns=access_wall_ns,
                    original_source_payload_sha256=sha256(deterministic_json(source).encode("utf-8")).hexdigest(),
                    original_estimator_json=actual.decode("utf-8"),
                    recorded_score_certificate_json=certificate.decode("utf-8"),
                    native_uncertainty_observation=_evidence_canonical_object_v1(deterministic_json(uncertainty.native_measurement).encode("utf-8")),
                    independent_estimator_derivation_sha256=sha256(deterministic_json(estimate).encode("utf-8")).hexdigest(),
                    baseline_ref=baseline_ref,posted_debit=debit.amount_text,posted_credit=credit.amount_text))
        result=dict(method="ORIGINAL_RECORDED_DR_ESTIMATOR_AND_CONDITIONAL_SCORE_INTERVAL",math_id="MATH-22",
            target="MEAN_CONDITIONAL_RECORDED_DR_SCORE",lane_calculations=tuple(lanes),
            original_policy_value_authority="ABSENT_SOFTWARE_CONFORMANCE_ONLY",
            original_source_capsule_json=common_capsule,
            independent_registration_proof=registered[8],registration_numerical_consumption=dict(registered[7]),
            original_numerical_limits=dict(protocol.numerical_work_limits),review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(work.consumed))
        result=_evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(result,work=work))
        _native_require(registration.review_numerical_original is association and registration.numerical_original is registered
            and work._original is operation.original[16],"LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original_result=(work,work._original,work.limits,work._decimal_admissions,work._math26_context_prefix,
            tuple(work.consumed.items()),result,deterministic_json(result))
        operation.numerical_result_original=original_result
        registration.review_numerical_original=(operation,original_result)
        return result

    def _calculate_measured_heldout_v1(self, operation, baseline_slice, snapshot):
        """Independently reconstruct topology and every original held-out score."""
        from hashlib import sha256
        from .context import _native_require
        from .evidence_execution import _prepare_evidence_heldout_scorer_inputs_v1, _worker_invocation_contract_v1
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import _evidence_heldout_source_data_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        from .specification import decode_evidence_raw_output_v1

        from .serialization import _evidence_canonical_object_v1

        def datum(value):
            return _evidence_canonical_object_v1(deterministic_json(value).encode("utf-8"))

        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        profile = protocol.numeric_profile
        math_id, scorer_id = profile["topology_math_id"], profile["scorer_math_id"]
        compact = math_id == "MATH-21"
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        association = registration.review_numerical_original
        _native_require(association == (operation, None) and operation.numerical_result_original is None
            and work is operation.original[15], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        policy, claim = registration.registration_policy
        comparator = policy["comparator_plan"]
        expected_topology = comparator["expected_raw_record_json"].encode("utf-8")
        expected_folds = tuple(text.encode("utf-8") for text in comparator["expected_fold_raw_json"])
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        originals = tuple(item for item in baseline_slice.reconstructed_canonical_events if item["record_ref"] == baseline_ref)
        _native_require(len(originals) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = originals[0]["values"]["baseline"]
        lanes = []
        source_payload_json = None
        original_source_identity = None
        with work:
            lower, upper = tuple(work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
            for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER"), strict=True):
                projection = lane.records.receipt_records[1].typed_payload.record
                segment = lane.records.receipt_records[2].typed_payload.record
                _native_require(segment.count == 1 and not segment.gap_dispositions
                    and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_HELD_OUT_FOLD_SCORING",
                    "LP03_HELD_OUT_REVIEW_ORIGINAL_SEGMENT")
                event = segment.exact_ordered_events[0]
                parts, inputs, trace = _evidence_heldout_source_data_v1(event["payload"])
                packet, contract, result, _, _, _ = lane.exchange
                resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
                scorer = _worker_invocation_contract_v1(result["scorer_invocation_contract"])
                source_refs = tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in parts)
                _native_require(resolution.math_spec_id == contract.math_id == math_id and scorer.math_id == scorer_id
                    and deterministic_json(resolution.authoritative_values) == deterministic_json(inputs)
                    and tuple(ref["record_id"] for ref in source_refs) == protocol.coverage_eligibility["source_record_refs"]
                    and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                    and projection.output_unit == profile["output_unit"] and projection.output_basis == profile["measurement_basis"],
                    "LP03_HELD_OUT_REVIEW_ORIGINAL_INPUT_AND_PROJECTION")
                for part in parts:
                    actual = tuple(candidate for candidate in packet._source_slices
                        if candidate.original_record_refs == part.original_record_refs)
                    _native_require(len(actual) == 1 and deterministic_json(actual[0]) == deterministic_json(part),
                        "LP03_HELD_OUT_REVIEW_ACTUAL_SOURCE_CUSTODY")
                source_identity = deterministic_json(tuple(item.reconstructed_canonical_events[0] for item in parts))
                if source_payload_json is None:
                    source_payload_json = deterministic_json(event["payload"])
                    original_source_identity = source_identity
                _native_require(source_identity == original_source_identity, "LP03_HELD_OUT_REVIEW_PAIRED_SOURCES")
                topology_wire = lane.raw.existing_receipt.output_json.encode("utf-8")
                work._require(topology_wire == expected_topology, "LP03_HELD_OUT_REVIEW_EXPECTED_TOPOLOGY")
                topology_proof = IndependentEvidenceReviewV1._bounded_review_fold_topology_v1(math_id,
                    deterministic_json(inputs).encode("utf-8"), topology_wire, work=work)
                prepared = _prepare_evidence_heldout_scorer_inputs_v1(topology_math_id=math_id,
                    topology_raw_json=topology_wire, scored_trace=trace, scorer_contract=scorer,
                    maximum_input_bytes=min(lane.attempt.payload.budgets.max_input_bytes,
                        lane.attempt.payload.budgets.segment_max_bytes,
                        lane.attempt.payload.budgets.frame_byte_limit), maximum_nodes=4096)
                raw_scores, fold_scores, path_scores = lane.heldout_score_records
                _native_require(len(raw_scores) == len(fold_scores) == len(expected_folds) == len(prepared),
                    "LP03_HELD_OUT_REVIEW_ALL_SCORE_RECEIPTS")
                scored_rows = []
                for original, fold, expected, source in zip(raw_scores, fold_scores, expected_folds, prepared, strict=True):
                    ordinal, train_ref, sample_refs, input_wire = source
                    _native_require(fold.fold_or_split_ordinal == ordinal and fold.training_membership_receipt_ref == train_ref
                        and deterministic_json(fold.ordered_sample_receipt_rows) == deterministic_json(sample_refs)
                        and fold.scorer_raw_receipt_ref == original.record_id and fold.topology_raw_ref == lane.raw.record_id
                        and fold.original_trace_source_ref == parts[-2].original_record_refs[0]
                        and fold.original_outcome_source_ref == parts[-1].original_record_refs[0]
                        and fold.original_scorer_raw_json == original.existing_receipt.output_json,
                        "LP03_HELD_OUT_REVIEW_SCORE_RECEIPT_LINEAGE")
                    actual = original.existing_receipt.output_json.encode("utf-8")
                    score = decode_evidence_raw_output_v1(scorer_id, actual, maximum_bytes=65536, maximum_nodes=4096)
                    mean = score["mean_brier_score" if scorer_id == "MATH-08" else "mean_log_loss"]
                    numerical_review = (IndependentEvidenceReviewV1._bounded_review_brier_v1 if scorer_id == "MATH-08"
                        else IndependentEvidenceReviewV1._bounded_review_log_loss_v1)
                    proof = numerical_review(input_wire, actual, expected, mean, work=work)
                    for value in (mean, *score["per_observation"]):
                        ratio = work._binary64_ratio(value, original_input=True)
                        work._require(work._compare(lower, ratio) <= 0 and work._compare(ratio, upper) <= 0,
                            "LP03_HELD_OUT_REVIEW_SCORE_BOUND")
                    measured = fold.scorer_invocation_measurement
                    retained = dict(ordinal=ordinal, fold_score_ref=fold.record_id, raw_score_ref=original.record_id,
                        original_raw_json=fold.original_scorer_raw_json,
                        derivation_sha256=sha256(deterministic_json(proof).encode("utf-8")).hexdigest())
                    if compact:
                        topology_clock = result["invocation_measurement"]
                        _native_require(measured["outcome"] == "SUCCESS" and all(measured[key] == topology_clock[key]
                            for key in ("clock_domain_id", "process_identity_ref", "boot_identity_ref", "clock_declarations")),
                            "LP03_CPCV_REVIEW_SHARED_ORIGINAL_SCORER_CLOCK")
                        retained.update(lineage_sha256=sha256(deterministic_json(dict(
                            training_receipt_ref=train_ref, sample_receipts=sample_refs)).encode("utf-8")).hexdigest(),
                            scorer_observation={key: measured[key] for key in ("started", "completed", "duration_ns", "cpu_ns")})
                    else:
                        retained.update(training_receipt_ref=train_ref, sample_receipts=sample_refs,
                            scorer_invocation=datum(measured))
                    scored_rows.append(retained)
                debit, credit = lane.records.journal_postings
                amounts = tuple(work._exact(work.parse_decimal_v1(text))
                    for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                    "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
                _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                    and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                    and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                    "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
                lanes.append(dict(lane=name, event_segment_ref=segment.record_id, raw_ref=lane.raw.record_id,
                    projection_ref=projection.record_id, source_record_refs=source_refs,
                    source_access_wall_ns=tuple(part.access_wall_ns for part in parts),
                    topology_derivation_sha256=sha256(deterministic_json(topology_proof).encode("utf-8")).hexdigest(),
                    topology_invocation=datum(result["invocation_measurement"]), fold_scores=tuple(scored_rows),
                    path_scores=tuple(dict(record_id=path.record_id, ordinal=path.path_ordinal,
                        fold_refs=path.ordered_fold_score_refs, sample_ids=path.ordered_sample_ids,
                        score_bits=path.ordered_original_score_bits, exact_average=datum(path.exact_average)) for path in path_scores),
                    posted_debit=debit.amount_text, posted_credit=credit.amount_text, baseline_ref=baseline_ref))
        method = ("ORIGINAL_TOPOLOGY_AND_COMPLETE_HELD_OUT_SCORING_COMPACT_V1" if compact
            else "ORIGINAL_TOPOLOGY_AND_COMPLETE_HELD_OUT_SCORING")
        calculation = dict(method=method, topology_math_id=math_id,
            scorer_math_id=scorer_id, scorer_pin=(profile["scorer_implementation_id"], profile["scorer_specification_id"],
                protocol.parameter_protocol_ref), topology_raw_json=expected_topology.decode("utf-8"),
            original_source_payload_json=source_payload_json, lane_calculations=tuple(lanes),
            registration_bound_proof=registered[8], registration_numerical_consumption=dict(registered[7]),
            original_numerical_limits=dict(protocol.numerical_work_limits), review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is association and registration.numerical_original is registered
            and work._original is operation.original[16], "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_cscv_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_cscv_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1
        registration = operation.registration
        protocol = registration.protocol
        math_id = "MATH-19"
        basis = "probability_of_backtest_overfitting"
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1"
                        and protocol.selected_metric_ids == ("CONFORMANCE::MATH-19::pbo_receipt",)
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_CSCV_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_CSCV_MATRIX_AND_GROUP_POLICY",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_cscv_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == math_id
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_CSCV_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_CSCV_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == math_id + "::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-19::2.0.0"
                            and projection.output_unit == lane.raw.output_unit == "mixed; member-specific"
                            and projection.output_basis == lane.raw.output_basis == basis
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = IndependentEvidenceReviewV1._bounded_review_pbo_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projection.projected_value,
                work=operation.numerical_work)
            with work:
                value = work._binary64_ratio(projection.projected_value["probability_of_backtest_overfitting"], original_input=True)
                work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                              "LP03_CSCV_RESULT_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload=_evidence_canonical_object_v1(
                    deterministic_json(event["payload"]).encode("utf-8"), max_bytes=65536),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_CSCV_FROM_ORIGINAL_MATRIX_AND_GROUP_POLICY", math_id=math_id, lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_sharpe_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_sharpe_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_canonical_object_v1, _evidence_frozen_data_v1
        registration = operation.registration
        protocol = registration.protocol
        math_id = protocol.numeric_profile["math_id"]
        basis = "probability_sharpe_exceeds_benchmark" if math_id == "MATH-17" else "multiple_testing_adjusted_sharpe_probability"
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1"
                        and math_id in ("MATH-17", "MATH-18")
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_SHARPE_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_SHARPE_LEDGER_AND_MOMENTS",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_sharpe_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == event["payload"]["math_id"] == math_id
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_SHARPE_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_SHARPE_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == math_id + "::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == math_id + ("::1.1.0" if math_id == "MATH-17" else "::2.0.0")
                            and projection.output_unit == lane.raw.output_unit == "probability"
                            and projection.output_basis == lane.raw.output_basis == basis
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = (IndependentEvidenceReviewV1._bounded_review_probabilistic_sharpe_v1 if math_id == "MATH-17"
                else IndependentEvidenceReviewV1._bounded_review_deflated_sharpe_v1)(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projection.projected_value,
                work=operation.numerical_work)
            with work:
                value = work._binary64_ratio(projection.projected_value, original_input=True)
                work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                              "LP03_SHARPE_RESULT_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload=_evidence_canonical_object_v1(
                    deterministic_json(event["payload"]).encode("utf-8"), max_bytes=65536),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_SHARPE_FROM_ORIGINAL_COMPLETE_LEDGER_AND_MOMENTS", math_id=math_id, lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_calibration_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_calibration_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        registration = operation.registration
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_BINARY64_CALIBRATION_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_CALIBRATION_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_CALIBRATION_EVALUATION_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_calibration_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-10"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_CALIBRATION_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-10"]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_CALIBRATION_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "MATH-10::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == "MATH-10::2.0.0"
                            and projection.output_unit == lane.raw.output_unit == "probability"
                            and projection.output_basis == lane.raw.output_basis == "absolute_calibration_gap"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = IndependentEvidenceReviewV1._bounded_review_calibration_v1(input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, projection.projected_value,
                work=operation.numerical_work)
            with work:
                value = work._binary64_ratio(projection.projected_value, original_input=True)
                work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                              "LP03_CALIBRATION_RESULT_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="EXACT_CALIBRATION_FROM_ORIGINAL_DATASET_AND_BIN_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_multiple_testing_v1(self, operation, baseline_slice, snapshot):
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_multiple_testing_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _evidence_decode_source_values_v1, _parse_typed
        from .persistence import _EvidenceReviewOperationV1, _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        registration = operation.registration
        protocol = registration.protocol
        math_id = protocol.selected_metric_ids[0].split("::")[1]
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        work = operation.numerical_work
        _native_require(original_association == (operation, None) and operation.numerical_result_original is None,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        consumed_registration = dict(registered[7])
        claim = registration.registration_policy[1]
        with work:
            lower, upper = (work._exact(work.parse_decimal_v1(text)) for text in (claim.fixed_lower, claim.fixed_upper))
        _native_require(protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1"
                        and operation.numerical_work is operation.original[15] and operation.numerical_work is not None,
                        "LP03_MULTIPLE_REVIEW_ORIGINAL_PROFILE")
        policy = operation.registration.registration_policy[0]
        expected_json = policy["comparator_plan"]["expected_raw_record_json"].encode("utf-8")
        calculations = []
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline = baselines[0]["values"]["baseline"]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_MULTIPLE_TESTING_BATCH",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_multiple_testing_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == math_id
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_MULTIPLE_REVIEW_ORIGINAL_ROSTER")
            typed = {}
            for source, binding in zip(sources, FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_MULTIPLE_REVIEW_ORIGINAL_SOURCE_CHANGED")
                values = _evidence_decode_source_values_v1(source.reconstructed_canonical_events[0])
                typed[binding.input_name] = _parse_typed(values[binding.exact_field_path], binding)
            input_json = deterministic_json(typed).encode("utf-8")
            _native_require(input_json == deterministic_json(resolution.authoritative_values).encode("utf-8")
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == math_id + "::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id == math_id + "::1.1R1"
                            and projection.output_unit == lane.raw.output_unit == "probability"
                            and projection.output_basis == lane.raw.output_basis == "adjusted_p_and_rejection_mask"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = IndependentEvidenceReviewV1._bounded_review_multiple_testing_v1(math_id, input_json,
                lane.raw.existing_receipt.output_json.encode("utf-8"), expected_json, deterministic_json(projection.projected_value).encode("utf-8"),
                work=operation.numerical_work)
            with work:
                for row in projection.projected_value.rows:
                    value = work._binary64_ratio(row.adjusted_p, original_input=True)
                    work._require(work._compare(value, lower) >= 0 and work._compare(value, upper) <= 0,
                                  "LP03_MULTIPLE_RESULT_COORDINATE_OUT_OF_BOUNDS")
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact(work.parse_decimal_v1(text)) for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                original_source_payload_json=deterministic_json(event["payload"]),
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value), unit=projection.output_unit,
                basis=projection.output_basis, baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="ORDERED_MULTIPLE_TESTING_FROM_ORIGINAL_DECLARED_LEDGER_AND_Q_POLICY", lane_calculations=tuple(calculations),
            registration_bound_proof={key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),
            numerical_consumption_before_final_encoding=dict(operation.numerical_work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_probability_edge_v1(self,operation,baseline_slice,snapshot):
        """Independently review M01, its actual conversion, then original M02."""
        from .context import _native_require
        from .models import _evidence_probability_edge_chain_sources_v1
        from .input_resolver import EvidenceInvocationInputsV1, _extract
        from .parameter_policy import (_bounded_evidence_market_review_v1,
            _bounded_evidence_probability_conversion_review_v1)
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _native_strict_json
        registration,work = operation.registration,operation.numerical_work
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        _native_require(protocol.analysis_profile == "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1"
            and registration.envelope_entry[3].component_closure == ("MATH-01","MATH-02")
            and work is operation.original[15] and work._original is operation.original[16]
            and operation.numerical_result_original is None and original_association[0] is operation
            and original_association[1] is None,"LP03_EDGE_REVIEW_ORIGINAL_PROFILE")
        consumed_registration = dict(registered[7])
        _native_require(dict(work.limits) == dict(protocol.numerical_work_limits,
            max_serialized_bytes=protocol.numerical_work_limits["max_serialized_bytes"]-consumed_registration["serialized_bytes"]),
            "LP03_EDGE_REVIEW_ORIGINAL_CUMULATIVE_ALLOWANCE")
        profile = protocol.numeric_profile
        comparator = registration.registration_policy[0]["comparator_plan"]
        expected_producer_json = profile["producer_expected_raw_json"]
        _native_require(expected_producer_json == comparator["producer_expected_raw_json"],
                        "LP03_EDGE_REVIEW_PREREGISTERED_PRODUCER_JOIN")
        expected_producer_text = _native_strict_json(expected_producer_json.encode("ascii"),max_bytes=4096,max_nodes=4)
        expected_edge_json = comparator["expected_raw_record_json"].encode("ascii")
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"]==baseline_ref)
        _native_require(len(baselines)==1,"LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline,calculations = baselines[0]["values"]["baseline"],[]
        original_source_payload_json = None
        original_source_facts = None
        for lane,name in zip(operation.parent.lanes,("REPLAY","PAPER"),strict=True):
            producer,dependency,artifact,contracts = _require_evidence_probability_edge_lane_v1(lane)
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(segment.count==len(segment.exact_ordered_events)==1
                and segment.first_event_ordinal==segment.last_event_ordinal==0 and not segment.gap_dispositions
                and segment.exact_ordered_events[0]["kind"]=="SYNTHETIC_SAME_SNAPSHOT_PROBABILITY_EDGE",
                "LP03_EDGE_REVIEW_COMPLETE_EVENT")
            event = segment.exact_ordered_events[0]
            sources = _evidence_probability_edge_chain_sources_v1(event["payload"])
            packets = lane.attempt.invocations
            resolutions = tuple(EvidenceInvocationInputsV1._require_original_v1(packet,lane.attempt) for packet in packets)
            rows = (*resolutions[0].inputs,*resolutions[1].external_inputs)
            _native_require(tuple(part.original_record_refs[0].record_id for part in sources)
                == tuple(row.packet_id for row in rows)==protocol.coverage_eligibility["source_record_refs"],
                "LP03_EDGE_REVIEW_ORIGINAL_SOURCE_ROSTER")
            for source,row in zip(sources,rows,strict=True):
                originals = tuple(part for part in packets[0]._source_slices if part.original_record_refs==source.original_record_refs)
                _native_require(len(originals)==1 and deterministic_json(source)==deterministic_json(originals[0])
                    and originals[0].reconstructed_canonical_events[0]["producer_receipt_id"]==row.producer_receipt_id,
                    "LP03_EDGE_REVIEW_ORIGINAL_SOURCE_CHANGED")
            original_events = tuple(part.reconstructed_canonical_events[0] for part in sources)
            _native_require(deterministic_json(profile["contract_context"])==deterministic_json(original_events[0]["values"]["contract_context"])
                and deterministic_json(profile["model_context"])==deterministic_json(original_events[2]["values"]["probability_edge_context"])
                and projection.original_raw_receipt_ref==lane.raw.record_id and projection.lane.value==name
                and projection.output_unit==lane.raw.output_unit==profile["output_unit"]
                and projection.output_basis==lane.raw.output_basis==profile["measurement_basis"],
                "LP03_EDGE_REVIEW_ORIGINAL_DECLARED_CONTEXT")
            source_texts = tuple((row.input_name,_extract(event["values"],row.field_path))
                for row,event in zip(resolutions[0].inputs,original_events[:2],strict=True))
            producer_text = _native_strict_json(producer.existing_receipt.output_json.encode("utf-8"),max_bytes=65536,max_nodes=4)
            producer_proof = _bounded_evidence_market_review_v1("MATH-01",source_texts,lower_text="0",upper_text="1",
                raw_texts=(producer_text,),expected_texts=(expected_producer_text,),projected_text=producer_text,work=work)
            # Conversion certification must immediately consume the completed
            # same-work M01 proof. No intervening numerical admission is made.
            conversion_proof = _bounded_evidence_probability_conversion_review_v1(producer_proof,
                producer_input_json=artifact["producer_input_json"].encode("utf-8"),
                producer_raw_json=artifact["producer_output_json"].encode("utf-8"),
                conversion_receipt_json=artifact["conversion_receipt_json"].encode("utf-8"),
                consumer_input_json=artifact["consumer_input_json"].encode("utf-8"),work=work)
            edge_proof = IndependentEvidenceReviewV1._bounded_review_probability_edge_v1(
                artifact["consumer_input_json"].encode("utf-8"),lane.raw.existing_receipt.output_json.encode("utf-8"),
                expected_edge_json,projection.projected_value,work=work)
            _native_require(len(lane.records.journal_postings)==2,"LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit,credit=lane.records.journal_postings
            with work:
                amounts=tuple(work._exact_market_decimal_v1(work._parse_market_decimal_v1(text))
                    for text in (debit.amount_text,credit.amount_text,baseline["cash"]))
                work._require(work._compare(amounts[0],amounts[1])==work._compare(amounts[1],amounts[2])==0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value=="DEBIT" and credit.entry_side.value=="CREDIT"
                and debit.currency_or_asset==credit.currency_or_asset==baseline["currency"]
                and debit.basis==credit.basis=="SYNTHETIC_OPENING_BALANCE","LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            source_payload_json = deterministic_json(event["payload"])
            source_data = _native_strict_json(source_payload_json.encode("utf-8"),max_bytes=65536,max_nodes=4096)
            source_facts = dict(source_data,source_slices=[
                {key:value for key,value in body.items() if key!="access_wall_ns"} for body in source_data["source_slices"]])
            access_clocks = tuple(source.access_wall_ns for source in sources)
            if original_source_payload_json is None:
                original_source_payload_json,original_source_facts = source_payload_json,source_facts
            else:
                _native_require(original_source_facts == source_facts,
                                "LP03_EDGE_REVIEW_SHARED_ORIGINAL_SOURCES")
            # Immutable source facts are shared only after exact equality.
            # Preserve each lane's four actual acquisition clocks separately.
            calculations.append(dict(lane=name,event_segment_ref=segment.record_id,source_access_wall_ns=access_clocks,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,record_id=part.original_record_refs[0].record_id)
                                         for part in sources),
                producer_proof=producer_proof,conversion_proof=conversion_proof,edge_proof=edge_proof,
                producer_raw_ref=producer.record_id,dependency_execution_ref=dependency.record_id,
                chain_artifact_json=dependency.chain_artifact_json,
                aggregate_measurement=dict(
                    **{key:dependency.invocation_measurement[key] for key in (
                        "clock_domain_id","boot_identity_ref","process_identity_ref",
                        "started","completed","duration_ns","cpu_ns","outcome")},
                    clock_declarations={name:dict(
                        implementation=dependency.invocation_measurement["clock_declarations"][name]["implementation"],
                        reported_resolution_ns=tuple(dependency.invocation_measurement["clock_declarations"][name]["reported_resolution_ns"]),
                        uncertainty_ns_or_absence=dict(dependency.invocation_measurement["clock_declarations"][name]["uncertainty_ns_or_absence"]))
                        for name in ("wall","monotonic","process_cpu")}),
                producer_contract=dict(dependency.producer_invocation_contract),consumer_contract=dict(dependency.consumer_invocation_contract),
                raw_ref=lane.raw.record_id,projection_ref=projection.record_id,
                projected_value_json=deterministic_json(projection.projected_value),unit=projection.output_unit,
                basis=projection.output_basis,baseline_ref=baseline_ref,posted_debit=debit.amount_text,posted_credit=credit.amount_text))
        calculation=dict(method="ORIGINAL_MARKET_CONVERSION_AND_BINARY64_EDGE_FROM_FOUR_SOURCES",
            producer_projection_policy="RAW_IDENTITY_INTERNAL_DEPENDENCY_ONLY_NO_SEPARATE_METRIC",
            original_source_payload_json=original_source_payload_json,lane_calculations=tuple(calculations),
            registration_bound_proof={key:dict(value) if type(value)is MappingProxyType else value for key,value in registered[8].items()},
            registration_numerical_consumption=consumed_registration,original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits),numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        calculation=_evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation,work=work))
        _native_require(registration.review_numerical_original is original_association
            and registration.numerical_original is registered and work._original is operation.original[16],
            "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original=(work,work._original,work.limits,work._decimal_admissions,work._math26_context_prefix,
            tuple(work.consumed.items()),calculation,deterministic_json(calculation))
        operation.numerical_result_original=original
        registration.review_numerical_original=(operation,original)
        return calculation

    def _calculate_measured_cashflow_v1(self, operation, baseline_slice, snapshot):
        """Independent ordered Decimal proof over both original signed-total cashflow lanes."""
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_cashflow_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _extract
        from .parameter_policy import _bounded_evidence_binary_cashflow_review_v1, _bounded_evidence_multi_outcome_cashflow_review_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1"
                        and work is operation.original[15] and work._original is operation.original[16]
                        and operation.numerical_result_original is None
                        and original_association[0] is operation and original_association[1] is None,
                        "LP03_CASHFLOW_REVIEW_ORIGINAL_PROFILE")
        consumed_registration = dict(registered[7])
        _native_require(dict(work.limits) == dict(protocol.numerical_work_limits,
            max_serialized_bytes=protocol.numerical_work_limits["max_serialized_bytes"] - consumed_registration["serialized_bytes"]),
            "LP03_CASHFLOW_REVIEW_ORIGINAL_CUMULATIVE_ALLOWANCE")
        profile = protocol.numeric_profile
        math_id = registration.envelope_entry[3].component_closure[0]
        claim = registration.registration_policy[1]
        from .serialization import _native_strict_json
        expected = _native_strict_json(registration.registration_policy[0]["comparator_plan"]["expected_raw_record_json"].encode("utf-8"),
            max_bytes=65536,max_nodes=4096)
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline, calculations = baselines[0]["values"]["baseline"], []
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_SIGNED_TOTAL_CASHFLOW_CONTEXT",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_cashflow_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == math_id
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_CASHFLOW_REVIEW_ORIGINAL_ROSTER")
            native = {}
            for source, binding in zip(sources, bindings):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_CASHFLOW_REVIEW_ORIGINAL_SOURCE_CHANGED")
                original_event = originals[0].reconstructed_canonical_events[0]
                metadata = original_event["values"]["cashflow_context"]
                _native_require(all(deterministic_json(metadata[key]) == deterministic_json(profile[key]) for key in (
                    "currency","input_snapshot_ref","event_ref","instrument_ref","horizon_ref","horizon_end_wall_ns",
                    "cashflow_basis","account_basis","account_context_ref","outcome_ids","ordered_outcome_roles")),
                    "LP03_CASHFLOW_REVIEW_ORIGINAL_ACCOUNT_BASIS")
                native[binding.input_name] = _extract(original_event["values"], binding.exact_field_path)
            raw = _native_strict_json(lane.raw.existing_receipt.output_json.encode("utf-8"),max_bytes=65536,max_nodes=4096)
            fields = (("expected_net_cash","expected_net_cash_if_filled","expected_terminal_cashflow","p_lose") if math_id == "MATH-06" else
                ("expected_net_cash","expected_net_cash_if_filled","expected_terminal_cashflow","outcome_ids",
                 "normalized_probabilities","original_probability_sum","normalization_applied"))
            _native_require(type(raw) is dict and set(raw) == set(expected) == set(fields),
                "LP03_CASHFLOW_REVIEW_ORIGINAL_RAW_SHAPE")
            def field_pairs(record):
                return tuple((key,tuple(record[key]) if key in ("outcome_ids","normalized_probabilities")
                    else record[key]) for key in fields)
            raw_fields,expected_fields = field_pairs(raw),field_pairs(expected)
            _native_require(type(projection.projected_value) is str
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == math_id + "::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id
                                == lane.exchange[1].raw_implementation_id == math_id + "::2.0.0"
                            and projection.output_unit == lane.raw.output_unit == profile["output_unit"]
                            and projection.output_basis == lane.raw.output_basis == profile["measurement_basis"]
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            names = (("p_win","p_void","fill_probability","entry_trade_cashflow_total",
                "win_terminal_cashflow_total","lose_terminal_cashflow_total","void_terminal_cashflow_total",
                "no_fill_cashflow_total","platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total",
                "exit_slippage_reserve_total","market_impact_reserve_total","latency_adverse_selection_reserve_total",
                "capital_time_cost_reserve_total") if math_id == "MATH-06" else
                ("probability_simplex_tolerance","fill_probability","entry_trade_cashflow_total","no_fill_cashflow_total",
                 "platform_fee_total","builder_fee_total","other_fee_total","expected_rebate_total","exit_slippage_reserve_total",
                 "market_impact_reserve_total","latency_adverse_selection_reserve_total","capital_time_cost_reserve_total"))
            arguments = dict(cashflow_basis=native["cashflow_basis"],lower_text=claim.fixed_lower,upper_text=claim.fixed_upper,
                raw_fields=raw_fields,expected_fields=expected_fields,projected_text=projection.projected_value,work=work)
            if math_id == "MATH-07":
                arguments.update(outcome_ids=tuple(native["outcome_ids"]),probability_texts=tuple(native["outcome_probabilities"]),
                    terminal_texts=tuple(native["outcome_terminal_cashflow_totals"]))
            prove = _bounded_evidence_binary_cashflow_review_v1 if math_id == "MATH-06" else _bounded_evidence_multi_outcome_cashflow_review_v1
            proof = prove(tuple((key,native[key]) for key in names),**arguments)
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact_cashflow_decimal_v1(work._parse_cashflow_decimal_v1(text))
                    for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"] == profile["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id, unit=projection.output_unit,
                basis=projection.output_basis,cashflow_context={key:profile[key] for key in (
                    "currency","input_snapshot_ref","event_ref","instrument_ref","horizon_ref","horizon_end_wall_ns",
                    "cashflow_basis","account_basis","account_context_ref","outcome_ids","ordered_outcome_roles")},baseline_ref=baseline_ref,
                posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="EXACT_ORDERED_DECIMAL_CASHFLOW_FROM_ORIGINAL_SIGNED_TOTAL_SOURCES", math_id=math_id,
            lane_calculations=tuple(calculations), registration_bound_proof={
                key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        # The existing complete-artifact encoder is shared; both lane proofs,
        # accounting inputs and final encoding consume this one review allowance.
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_market_v1(self, operation, baseline_slice, snapshot):
        """Independent ordered Decimal proof over both original market lanes."""
        from .context import _native_require
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .models import _evidence_market_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1, _extract
        from .parameter_policy import _bounded_evidence_market_review_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1
        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1"
                        and work is operation.original[15] and work._original is operation.original[16]
                        and operation.numerical_result_original is None
                        and original_association[0] is operation and original_association[1] is None,
                        "LP03_MARKET_REVIEW_ORIGINAL_PROFILE")
        consumed_registration = dict(registered[7])
        _native_require(dict(work.limits) == dict(protocol.numerical_work_limits,
            max_serialized_bytes=protocol.numerical_work_limits["max_serialized_bytes"] - consumed_registration["serialized_bytes"]),
            "LP03_MARKET_REVIEW_ORIGINAL_CUMULATIVE_ALLOWANCE")
        profile = protocol.numeric_profile
        math_id = registration.envelope_entry[3].component_closure[0]
        claim = registration.registration_policy[1]
        expected = registration.registration_policy[0]["comparator_plan"]["expected_raw_texts"]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline, calculations = baselines[0]["values"]["baseline"], []
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_MARKET_PRICE_CONTEXT",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_market_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == math_id
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_MARKET_REVIEW_ORIGINAL_ROSTER")
            native = {}
            for source, binding in zip(sources, bindings):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_MARKET_REVIEW_ORIGINAL_SOURCE_CHANGED")
                original_event = originals[0].reconstructed_canonical_events[0]
                root = "market_state" if binding.accepted_upstream_owner_id == "SelectedVenuePublicMarketDataOwnerV1" else "contract_semantics"
                _native_require(original_event["values"][root]["currency"] == profile["price_currency"]
                                and original_event["scope"]["input_snapshot_id"] == profile["snapshot_ref"],
                                "LP03_MARKET_REVIEW_ORIGINAL_PRICE_BASIS")
                native[binding.input_name] = _extract(original_event["values"], binding.exact_field_path)
            from .serialization import _native_strict_json
            raw = _native_strict_json(lane.raw.existing_receipt.output_json.encode("utf-8"), max_bytes=65536, max_nodes=8)
            _native_require(type(raw) is dict and set(raw) == {"relative_spread_ratio", "relative_spread_bps"}
                            if math_id == "MATH-05" else type(raw) is str, "LP03_MARKET_REVIEW_ORIGINAL_RAW_SHAPE")
            raw_texts = (raw["relative_spread_ratio"], raw["relative_spread_bps"]) if math_id == "MATH-05" else (raw,)
            _native_require(all(type(text) is str for text in raw_texts) and type(projection.projected_value) is str
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == math_id + "::OUTPUT"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id
                                == math_id + "::1.1R1"
                            and projection.output_unit == lane.raw.output_unit == profile["output_unit"]
                            and projection.output_basis == lane.raw.output_basis == profile["measurement_basis"]
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            names = ("contract_price", "payout_per_winning_contract") if math_id == "MATH-01" else ("best_bid", "best_ask", "payout")
            proof = _bounded_evidence_market_review_v1(math_id, tuple((key, native[key]) for key in names),
                lower_text=claim.fixed_lower, upper_text=claim.fixed_upper, raw_texts=raw_texts,
                expected_texts=tuple(expected), projected_text=projection.projected_value, work=work)
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact_market_decimal_v1(work._parse_market_decimal_v1(text))
                    for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id, unit=projection.output_unit,
                basis=projection.output_basis, price_currency=profile["price_currency"], snapshot_ref=profile["snapshot_ref"], baseline_ref=baseline_ref,
                posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="EXACT_ORDERED_DECIMAL_MARKET_FROM_ORIGINAL_PRICE_SOURCES", math_id=math_id,
            lane_calculations=tuple(calculations), registration_bound_proof={
                key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        # The existing complete-artifact encoder is shared; both lane proofs,
        # accounting inputs and final encoding consume this one review allowance.
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_kelly27_v1(self, operation, baseline_slice, snapshot):
        """Independent ordered Decimal proof over both original probability/payoff lanes."""
        from .context import _native_require
        from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
        from .models import _evidence_kelly27_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1
        from .parameter_policy import _bounded_evidence_kelly_review_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _native_strict_json
        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1"
                        and work is operation.original[15] and work._original is operation.original[16]
                        and operation.numerical_result_original is None
                        and original_association[0] is operation and original_association[1] is None,
                        "LP03_KELLY27_REVIEW_ORIGINAL_PROFILE")
        consumed_registration = dict(registered[7])
        _native_require(dict(work.limits) == dict(protocol.numerical_work_limits,
            max_serialized_bytes=protocol.numerical_work_limits["max_serialized_bytes"] - consumed_registration["serialized_bytes"]),
            "LP03_KELLY27_REVIEW_ORIGINAL_CUMULATIVE_ALLOWANCE")
        profile = protocol.numeric_profile
        expected = registration.registration_policy[0]["comparator_plan"]["expected_raw_texts"]
        claim = registration.registration_policy[1]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline, calculations = baselines[0]["values"]["baseline"], []
        bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-27"].bindings
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_KELLY_PROBABILITY_PAYOFF_CONTEXT",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_kelly27_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-27"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_KELLY27_REVIEW_ORIGINAL_ROSTER")
            native = {}
            for source, binding in zip(sources, bindings):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_KELLY27_REVIEW_ORIGINAL_SOURCE_CHANGED")
                original_event = originals[0].reconstructed_canonical_events[0]
                metadata = original_event["values"]["private_source_context"]
                _native_require(all(metadata[key] == profile[key] for key in (
                    "risk_capital_basis_ref", "risk_capital_currency", "instrument_ref", "horizon_ref", "sizing_decision_ref")),
                    "LP03_KELLY27_REVIEW_ORIGINAL_UTILITY_BASIS")
                native[binding.input_name] = original_event["values"][binding.input_name]
            raw = _native_strict_json(lane.raw.existing_receipt.output_json.encode("utf-8"), max_bytes=65536, max_nodes=8)
            _native_require(type(raw) is dict and set(raw) == {"raw_fraction", "sizing_candidate"}
                            and all(type(value) is str for value in raw.values()) and type(projection.projected_value) is str
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "LP03::MATH-27::RAW_V1"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id
                                == "qku/economic_math.py::MATH-27::ST12C-CURRENTIZED-1.0"
                            and projection.output_unit == lane.raw.output_unit == profile["output_unit"]
                            and projection.output_basis == lane.raw.output_basis == profile["measurement_basis"] == "wealth_fraction"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = _bounded_evidence_kelly_review_v1("MATH-27", tuple((key, native[key]) for key in ("win_probability", "net_odds")),
                lower_text=claim.fixed_lower, upper_text=claim.fixed_upper,
                raw_texts=(raw["raw_fraction"], raw["sizing_candidate"]), projected_text=projection.projected_value,
                expected_texts=tuple(expected), work=work)
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact_kelly_decimal_v1(work._parse_kelly_decimal_v1(text))
                    for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id, unit=projection.output_unit,
                basis=projection.output_basis, risk_capital_basis_ref=profile["risk_capital_basis_ref"],
                risk_capital_currency=profile["risk_capital_currency"], instrument_ref=profile["instrument_ref"],
                horizon_ref=profile["horizon_ref"], sizing_decision_ref=profile["sizing_decision_ref"], baseline_ref=baseline_ref,
                posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="EXACT_ORDERED_DECIMAL_MATH27_FROM_ORIGINAL_PROBABILITY_PAYOFF_SOURCES",
            lane_calculations=tuple(calculations), registration_bound_proof={
                key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        # The existing complete-artifact encoder is shared; both lane proofs,
        # accounting inputs and final encoding consume this one review allowance.
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_kelly28_v1(self, operation, baseline_slice, snapshot):
        """Independent ordered Decimal proof over both original publication/constraint lanes."""
        from .context import _native_require
        from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
        from .models import _evidence_kelly28_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1
        from .parameter_policy import _bounded_evidence_kelly_review_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _native_strict_json
        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1"
                        and work is operation.original[15] and work._original is operation.original[16]
                        and operation.numerical_result_original is None
                        and original_association[0] is operation and original_association[1] is None,
                        "LP03_KELLY28_REVIEW_ORIGINAL_PROFILE")
        consumed_registration = dict(registered[7])
        _native_require(dict(work.limits) == dict(protocol.numerical_work_limits,
            max_serialized_bytes=protocol.numerical_work_limits["max_serialized_bytes"] - consumed_registration["serialized_bytes"]),
            "LP03_KELLY28_REVIEW_ORIGINAL_CUMULATIVE_ALLOWANCE")
        profile = protocol.numeric_profile
        expected = registration.registration_policy[0]["comparator_plan"]["expected_raw_texts"]
        claim = registration.registration_policy[1]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline, calculations = baselines[0]["values"]["baseline"], []
        bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-28"].bindings
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_FRACTIONAL_KELLY_CONTEXT",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_kelly28_source_slices_v1(event["payload"])
            consumer_scope = registration.envelope_entry[3].assembly_scope
            _native_require(event["payload"]["consumer_decision_wall_ns"] == consumer_scope.snapshot_decision_wall_ns
                and event["payload"]["consumer_cutoff_wall_ns"] == consumer_scope.snapshot_pit_cutoff_wall_ns,
                "LP03_KELLY28_REVIEW_CONSUMER_CLOCK_JOIN")
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-28"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_KELLY28_REVIEW_ORIGINAL_ROSTER")
            native = {}
            for source, binding in zip(sources, bindings):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_KELLY28_REVIEW_ORIGINAL_SOURCE_CHANGED")
                original_event = originals[0].reconstructed_canonical_events[0]
                if binding.input_name == "full_kelly_fraction":
                    metadata = original_event["values"]["published_source_context"]["original_source_payload"]["source_slices"][0]["reconstructed_canonical_events"][0]["values"]["private_source_context"]
                else:
                    metadata = original_event["values"]["private_source_context"]
                _native_require(all(metadata[key] == profile[key] for key in (
                    "risk_capital_basis_ref", "risk_capital_currency", "instrument_ref", "horizon_ref", "sizing_decision_ref")),
                    "LP03_KELLY28_REVIEW_ORIGINAL_UTILITY_BASIS")
                native[binding.input_name] = original_event["values"][binding.input_name]
            raw = _native_strict_json(lane.raw.existing_receipt.output_json.encode("utf-8"), max_bytes=65536, max_nodes=8)
            _native_require(type(raw) is str and type(projection.projected_value) is str
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "LP03::MATH-28::RAW_V1"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id
                                == "qku/economic_math.py::MATH-28::ST12C-CURRENTIZED-1.0"
                            and projection.output_unit == lane.raw.output_unit == profile["output_unit"]
                            and projection.output_basis == lane.raw.output_basis == profile["measurement_basis"] == "bounded_fractional_wealth_fraction"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = _bounded_evidence_kelly_review_v1("MATH-28", tuple((key, native[key]) for key in ("full_kelly_fraction", "fraction_multiplier", "risk_caps")),
                lower_text=claim.fixed_lower, upper_text=claim.fixed_upper,
                raw_texts=(raw,), projected_text=projection.projected_value,
                expected_texts=tuple(expected), work=work)
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact_kelly_decimal_v1(work._parse_kelly_decimal_v1(text))
                    for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id, unit=projection.output_unit,
                basis=projection.output_basis, risk_capital_basis_ref=profile["risk_capital_basis_ref"],
                risk_capital_currency=profile["risk_capital_currency"], instrument_ref=profile["instrument_ref"],
                horizon_ref=profile["horizon_ref"], sizing_decision_ref=profile["sizing_decision_ref"], baseline_ref=baseline_ref,
                posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="EXACT_ORDERED_DECIMAL_MATH28_FROM_ORIGINAL_PUBLISHED_KELLY_AND_CONSTRAINTS",
            lane_calculations=tuple(calculations), registration_bound_proof={
                key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        # The existing complete-artifact encoder is shared; both lane proofs,
        # accounting inputs and final encoding consume this one review allowance.
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_math26_v1(self, operation, baseline_slice, snapshot):
        """Independent ordered Decimal proof over both original research lanes."""
        from .context import _native_require
        from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
        from .models import _evidence_research_source_slices_v1
        from .input_resolver import EvidenceInvocationInputsV1
        from .parameter_policy import _bounded_evidence_math26_review_v1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import _evidence_frozen_data_v1, _native_strict_json
        registration, work = operation.registration, operation.numerical_work
        protocol = registration.protocol
        registered = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
        original_association = registration.review_numerical_original
        _native_require(protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_EVI_CONFORMANCE_V1"
                        and work is operation.original[15] and work._original is operation.original[16]
                        and operation.numerical_result_original is None
                        and original_association[0] is operation and original_association[1] is None,
                        "LP03_MATH26_REVIEW_ORIGINAL_PROFILE")
        consumed_registration = dict(registered[7])
        _native_require(dict(work.limits) == dict(protocol.numerical_work_limits,
            max_serialized_bytes=protocol.numerical_work_limits["max_serialized_bytes"] - consumed_registration["serialized_bytes"]),
            "LP03_MATH26_REVIEW_ORIGINAL_CUMULATIVE_ALLOWANCE")
        profile = protocol.numeric_profile
        expected = registration.registration_policy[0]["comparator_plan"]["expected_raw_value"]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        baselines = tuple(row for row in baseline_slice.reconstructed_canonical_events if row["record_ref"] == baseline_ref)
        _native_require(len(baselines) == 1, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
        baseline, calculations = baselines[0]["values"]["baseline"], []
        bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-26"].bindings
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                            and segment.last_event_ordinal == 0 and not segment.gap_dispositions
                            and segment.exact_ordered_events[0]["kind"] == "SYNTHETIC_RESEARCH_DECISION",
                            "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
            event = segment.exact_ordered_events[0]
            sources = _evidence_research_source_slices_v1(event["payload"])
            packet = lane.exchange[0]
            resolution = EvidenceInvocationInputsV1._require_original_v1(packet, lane.attempt)
            _native_require(resolution.math_spec_id == "MATH-26"
                            and tuple(part.original_record_refs[0].record_id for part in sources)
                            == tuple(row.packet_id for row in resolution.inputs)
                            == protocol.coverage_eligibility["source_record_refs"], "LP03_MATH26_REVIEW_ORIGINAL_ROSTER")
            native = {}
            for source, binding in zip(sources, bindings):
                originals = tuple(part for part in packet._source_slices if part.original_record_refs == source.original_record_refs)
                _native_require(len(originals) == 1 and deterministic_json(source) == deterministic_json(originals[0]),
                                "LP03_MATH26_REVIEW_ORIGINAL_SOURCE_CHANGED")
                original_event = originals[0].reconstructed_canonical_events[0]
                metadata = original_event["values"]["private_source_context"]
                _native_require(all(metadata[key] == profile[key] for key in (
                    "utility_unit", "utility_basis_ref", "horizon_ref", "research_decision_ref")),
                    "LP03_MATH26_REVIEW_ORIGINAL_UTILITY_BASIS")
                native[binding.input_name] = original_event["values"][binding.input_name]
            raw_text = _native_strict_json(lane.raw.existing_receipt.output_json.encode("utf-8"), max_bytes=65536, max_nodes=1)
            _native_require(type(raw_text) is str and type(projection.projected_value) is str
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.original_raw_schema_ref == "LP03::MATH-26::RAW_V1"
                            and projection.original_implementation_ref == lane.raw.existing_receipt.implementation_id
                                == "qku/economic_math.py::MATH-26::ST12C-CURRENTIZED-1.0"
                            and projection.output_unit == lane.raw.output_unit == profile["utility_unit"]
                            and projection.output_basis == lane.raw.output_basis == "EXPECTED_VALUE_OF_INFORMATION_PER_DECISION"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            proof = _bounded_evidence_math26_review_v1(native["current_action_values"], native["new_information_scenarios"],
                native["acquisition_cost"], lower_text=profile["utility_lower"], upper_text=profile["utility_upper"],
                cost_cap_text=profile["cost_cap"], raw_text=raw_text, projected_text=projection.projected_value,
                expected_text=expected, work=work)
            _native_require(len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            debit, credit = lane.records.journal_postings
            with work:
                amounts = tuple(work._exact_math26_decimal_v1(work._parse_math26_decimal_v1(text))
                    for text in (debit.amount_text, credit.amount_text, baseline["cash"]))
                work._require(work._compare(amounts[0], amounts[1]) == work._compare(amounts[1], amounts[2]) == 0,
                              "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id,
                source_record_refs=tuple(dict(store_id=part.original_record_refs[0].store_id,
                    record_id=part.original_record_refs[0].record_id) for part in sources), proof=proof,
                raw_ref=lane.raw.record_id, projection_ref=projection.record_id, unit=projection.output_unit,
                basis=projection.output_basis, utility_basis_ref=profile["utility_basis_ref"], horizon_ref=profile["horizon_ref"],
                research_decision_ref=profile["research_decision_ref"], baseline_ref=baseline_ref,
                posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        calculation = dict(method="EXACT_ORDERED_DECIMAL_MATH26_FROM_ORIGINAL_RESEARCH_SOURCES",
            lane_calculations=tuple(calculations), registration_bound_proof={
                key: dict(value) if type(value) is MappingProxyType else value for key, value in registered[8].items()},
            registration_numerical_consumption=consumed_registration, original_numerical_limits=dict(protocol.numerical_work_limits),
            review_numerical_limits=dict(work.limits), numerical_consumption_before_final_encoding=dict(work.consumed),
            result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")
        # The existing complete-artifact encoder is shared; both lane proofs,
        # accounting inputs and final encoding consume this one review allowance.
        calculation = _evidence_frozen_data_v1(IndependentEvidenceReviewV1._charge_brier_review_artifact_v1(calculation, work=work))
        _native_require(registration.review_numerical_original is original_association
                        and registration.numerical_original is registered and work._original is operation.original[16],
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        original = (work, work._original, work.limits, work._decimal_admissions, work._math26_context_prefix,
            tuple(work.consumed.items()), calculation, deterministic_json(calculation))
        operation.numerical_result_original = original
        registration.review_numerical_original = (operation, original)
        return calculation

    def _calculate_measured_conformance_v1(self, operation):
        """Independent exact arithmetic over originally recorded event members."""
        from .context import _native_require
        from .persistence import _EvidenceReviewOperationV1
        from .serialization import safe_json_loads, deterministic_json
        from .input_resolver import _EvidenceOwnerPacketCustodyV1
        IndependentEvidenceReviewV1._assert_measured_binding_v1(self)
        _native_require(type(operation) is _EvidenceReviewOperationV1 and operation.reviewer is self
                        and operation.phase == "PARENTS_READBACK", "LP03_REVIEW_ORIGINAL_CALCULATION_SCOPE")
        snapshot = operation.registration.preparation.input_assembly_members[2]
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        selections = tuple(selection for selection in operation.registration.envelope_entry[3].assembly_scope.source_selections
            if selection.selection.record_refs == (baseline_ref,))
        _native_require(len(selections) == 1, "LP03_REVIEW_ORIGINAL_BASELINE_SELECTION")
        selection = selections[0]
        custodies = tuple(custody for custody, policies in operation.registration.policies
            if all(ref in custody.rights_by_id for ref in selection.required_original_rights_refs))
        _native_require(len(custodies) == 1, "LP03_REVIEW_ORIGINAL_BASELINE_OWNER")
        baseline_slice = _EvidenceOwnerPacketCustodyV1._read_admitted_slice_v1(custodies[0], operation, selection)
        from .input_resolver import _require_evidence_source_slice_roster_v1
        baseline_sources = _require_evidence_source_slice_roster_v1(operation, (baseline_slice,), subject=operation)
        operation.baseline_slice = baseline_slice
        operation.baseline_original = (baseline_slice, deterministic_json(baseline_slice), baseline_sources)
        _EvidenceReviewOperationV1._check_current_v1(operation)
        _EvidenceReviewOperationV1._assert_original_v1(operation, canonical=True)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_probability_edge_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_multiple_testing_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_quantum_constructor_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile in ("DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1"):
            return IndependentEvidenceReviewV1._calculate_measured_private_execution_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_private_analytic_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_recorded_ope_point_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_recorded_dr_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1":
            return IndependentEvidenceReviewV1._calculate_measured_heldout_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_cscv_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_sharpe_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-16::spa_receipt",):
            return IndependentEvidenceReviewV1._calculate_measured_spa_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-15::reality_check_receipt",):
            return IndependentEvidenceReviewV1._calculate_measured_reality_check_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-14::bootstrap_distribution_and_interval",):
            return IndependentEvidenceReviewV1._calculate_measured_bootstrap_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-11::interval",):
            return IndependentEvidenceReviewV1._calculate_measured_wilson_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-10::ece",):
            return IndependentEvidenceReviewV1._calculate_measured_calibration_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-09::log_loss",):
            return IndependentEvidenceReviewV1._calculate_measured_log_loss_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-08::brier_score",):
            return IndependentEvidenceReviewV1._calculate_measured_brier_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-26::evi",):
            return IndependentEvidenceReviewV1._calculate_measured_math26_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-28::bounded_fraction",):
            return IndependentEvidenceReviewV1._calculate_measured_kelly28_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-27::full_kelly_fraction",):
            return IndependentEvidenceReviewV1._calculate_measured_kelly27_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_cashflow_v1(self, operation, baseline_slice, snapshot)
        if operation.registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1":
            return IndependentEvidenceReviewV1._calculate_measured_market_v1(self, operation, baseline_slice, snapshot)
        expected_text = operation.registration.registration_policy[0]["comparator_plan"]["expected_raw_value"]
        limits = operation.registration.protocol.numerical_work_limits
        bounded = IndependentEvidenceReviewV1._bounded_review_decimal_v1
        expected = bounded(expected_text, limits)
        calculations = []
        paired_scenario_values = None
        for lane, name in zip(operation.parent.lanes, ("REPLAY", "PAPER")):
            projection = lane.records.receipt_records[1].typed_payload.record
            segment = lane.records.receipt_records[2].typed_payload.record
            scope = lane.attempt.payload.causal_timeline_v1()
            if scope is None:
                _native_require(len(segment.exact_ordered_events) == segment.count == 1 and segment.first_event_ordinal == 0
                                and segment.last_event_ordinal == 0 and not segment.gap_dispositions,
                                "LP03_REVIEW_COMPLETE_EVENT_REQUIRED")
                event = segment.exact_ordered_events[0]
            else:
                event, scenario_values = IndependentEvidenceReviewV1._review_causal_midpoint_timeline_v1(
                    operation, lane, segment, scope)
                if paired_scenario_values is None:
                    from random import Random
                    from .evidence_execution import _worker_environment_v1

                    _native_require(_worker_environment_v1() == scope.scenario_plan.exact_environment_identity,
                                    "LP03_REVIEW_CAUSAL_SCENARIO_ENVIRONMENT")
                    for receipt in scenario_values:
                        seed = int(receipt["encoded_coordinate"], 16)
                        _native_require(Random(seed).getrandbits(53) == receipt["uniform53_bits"],
                                        "LP03_REVIEW_CAUSAL_SCENARIO_RECIPE")
                    paired_scenario_values = scenario_values
                else:
                    _native_require(scenario_values == paired_scenario_values, "LP03_REVIEW_PAIRED_SCENARIO_VALUES")
            book = event["payload"]["market_state"]
            bid, ask = bounded(book["best_bid"], limits), bounded(book["best_ask"], limits)
            independent = IndependentEvidenceReviewV1._bounded_review_midpoint_v1(bid, ask, limits)
            raw_value = safe_json_loads(lane.raw.existing_receipt.output_json)
            _native_require(type(raw_value) is str and bid <= ask and independent == expected
                            and bounded(raw_value, limits) == expected and bounded(projection.projected_value, limits) == expected
                            and projection.lane.value == name and projection.original_raw_receipt_ref == lane.raw.record_id
                            and projection.output_unit == lane.raw.output_unit == "USD/CONTRACT"
                            and projection.output_basis == lane.raw.output_basis == "SAME_INSTRUMENT_SAME_SNAPSHOT_BEST_BID_ASK_MIDPOINT"
                            and lane.raw.accounting_class == "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",
                            "LP03_REVIEW_INDEPENDENT_VALUE_OR_BASIS_MISMATCH")
            baselines = tuple(item for item in baseline_slice.reconstructed_canonical_events
                              if item["record_ref"] == baseline_ref)
            _native_require(len(baselines) == 1 and len(lane.records.journal_postings) == 2, "LP03_REVIEW_ORIGINAL_ACCOUNTING_REQUIRED")
            baseline = baselines[0]["values"]["baseline"]
            debit, credit = lane.records.journal_postings
            _native_require(debit.entry_side.value == "DEBIT" and credit.entry_side.value == "CREDIT"
                            and bounded(debit.amount_text, limits) == bounded(credit.amount_text, limits) == bounded(baseline["cash"], limits)
                            and debit.currency_or_asset == credit.currency_or_asset == baseline["currency"]
                            and debit.basis == credit.basis == "SYNTHETIC_OPENING_BALANCE",
                            "LP03_REVIEW_BALANCED_BASELINE_MISMATCH")
            calculations.append(dict(lane=name, event_segment_ref=segment.record_id, source_record_ref=event["source_record_ref"],
                bid=str(bid), ask=str(ask), independent_value_rational=(independent.numerator, independent.denominator),
                raw_ref=lane.raw.record_id, raw_value=raw_value, projection_ref=projection.record_id,
                projection_value=projection.projected_value, unit=projection.output_unit, basis=projection.output_basis,
                baseline_ref=baseline_ref, posted_debit=debit.amount_text, posted_credit=credit.amount_text))
        return dict(method="EXACT_RATIONAL_MIDPOINT_FROM_ORIGINAL_EVENT", lane_calculations=tuple(calculations),
                    preregistered_expected=expected_text, result="BOTH_LANES_MATCH_PREREGISTERED_EXPECTATION")

    @staticmethod
    def _review_causal_midpoint_timeline_v1(operation, lane, segment, scope):
        """Join the independently read lane rows to the signed original event plan."""
        from bisect import bisect_left
        from .context import _native_require
        from .evidence_execution import (_EvidenceTimelineLaneStateV1, _evidence_lane_completion_v1,
            _evidence_timeline_coordinate_receipt_v1, _evidence_timeline_event_key_v1, _require_evidence_timeline_outcome_v1)
        from .input_resolver import _evidence_original_timeline_inputs_v1
        from .models import EvidenceCausalTimelineScopeV1, EvidenceStepOutcomeV1
        from .serialization import deterministic_json

        registration = operation.registration
        grant = lane.attempt.payload
        committed_scope = EvidenceCausalTimelineScopeV1.from_canonical_mapping(
            registration.records[0].observation_plan["causal_timeline"])
        original_slices = registration.preparation.input_assembly_members[1]
        originals = _evidence_original_timeline_inputs_v1(committed_scope, original_slices)
        ordered = tuple(sorted(originals, key=_evidence_timeline_event_key_v1))
        _native_require(scope == committed_scope and _evidence_lane_completion_v1(grant, lane.exchange[4], 1)
                        and segment.attempt_ref == grant.grant_ref and segment.lane is grant.lane
                        and segment.count == len(segment.exact_ordered_events) == len(ordered)
                        and segment.first_event_ordinal == 0 and segment.last_event_ordinal == len(ordered) - 1
                        and not segment.gap_dispositions, "LP03_REVIEW_CAUSAL_ORIGINAL_COMPLETION")
        refs = tuple(pin.source_record_ref for pin in scope.component_input_pins)
        formula = None
        scenario_values = []
        domain = _EvidenceTimelineLaneStateV1(grant, scope)
        for row, original in zip(segment.exact_ordered_events, ordered, strict=True):
            ordinal = bisect_left(scope.decision_wall_ns, original.availability_wall_ns)
            _native_require(row["decision_ordinal"] == ordinal and row["decision_wall_ns"] == scope.decision_wall_ns[ordinal]
                            and deterministic_json(row["event"]) == deterministic_json(original),
                            "LP03_REVIEW_CAUSAL_EVENT_AVAILABILITY")
            receipts = row["scenario_values"]
            _native_require(tuple(_evidence_timeline_coordinate_receipt_v1(value) for value in receipts) ==
                            tuple(value for value in scope.coordinates if value[4] == original.local_ordinal),
                            "LP03_REVIEW_CAUSAL_COORDINATE_ASSIGNMENT")
            scenario_values.extend(receipts)
            domain.begin_v1(original, decision_wall_ns=row["decision_wall_ns"])
            outcomes = tuple(EvidenceStepOutcomeV1.from_canonical_mapping(value) for value in row["outcomes"])
            visible = frozenset(event.source_record_ref for event in originals if event.availability_wall_ns <= row["decision_wall_ns"])
            visible |= frozenset(pin.source_record_ref for pin in scope.component_input_pins
                                 if pin.availability_wall_ns <= row["decision_wall_ns"])
            for pin, outcome in zip(scope.callbacks, outcomes, strict=True):
                _require_evidence_timeline_outcome_v1(outcome, grant=grant, event=original, pin=pin,
                    source_refs=visible, final_event=original is ordered[-1])
                domain.apply_v1(original, outcome, decision_wall_ns=row["decision_wall_ns"])
                if outcome.component_requests:
                    domain.require_component_v1(original)
            _native_require(row["domain_state"] == domain.view_v1(), "LP03_REVIEW_CAUSAL_DOMAIN_PREFIX")
            requests = tuple(request for outcome in outcomes for request in outcome.component_requests)
            body = row["component_event_or_none"]
            _native_require(len(requests) == int(body is not None), "LP03_REVIEW_CAUSAL_COMPONENT_OUTCOME")
            if body is not None:
                _native_require(formula is None and requests[0].math_id == "MATH-03"
                                and requests[0].original_input_refs == refs
                                and all(pin.availability_wall_ns <= row["decision_wall_ns"] for pin in scope.component_input_pins)
                                and lane.exchange[2]["event_ordinal"] == original.local_ordinal,
                                "LP03_REVIEW_CAUSAL_COMPONENT_DISPATCH")
                formula = body
        first_ref = refs[0]
        sources = tuple(row for part in original_slices if first_ref in part.original_record_refs
                        for row in part.reconstructed_canonical_events if row["record_ref"] == first_ref.record_id)
        _native_require(len(sources) == 1 and formula is not None and formula["kind"] == "SYNTHETIC_BOOK_SNAPSHOT",
                        "LP03_REVIEW_CAUSAL_ORIGINAL_BOOK_INPUT")
        source = sources[0]
        _native_require(formula["payload"] == source["values"] and formula["origin"] == source["origin"]
                        and formula["source_record_ref"] == {"store_id": first_ref.store_id, "record_id": first_ref.record_id}
                        and formula["availability_wall_ns"] == source["native_clocks"]["available_time"],
                        "LP03_REVIEW_CAUSAL_ORIGINAL_BOOK_INPUT")
        return formula, tuple(scenario_values)

    def __init__(
        self,
        cohort_resolver: CohortCompilationResolverProtocolV1,
        persistence_adapter: PersistenceAdapterV1,
        authority_resolver: IndependentReviewAuthorityResolverProtocolV1,
    ) -> None:
        if (
            not isinstance(persistence_adapter, PersistenceAdapterV1)
            or persistence_adapter.availability
            is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE
        ):
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "independent review requires available ST12-C persistence",
            )
        if not callable(getattr(cohort_resolver, "resolve_input_lock", None)):
            raise ContractValidationError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "independent review requires the canonical input-lock resolver",
            )
        if not isinstance(
            authority_resolver,
            IndependentReviewAuthorityResolverProtocolV1,
        ):
            raise AuthorityDeniedError(
                ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
                "independent review requires the exact authority resolver protocol",
            )
        self._cohort_resolver = cohort_resolver
        self._persistence = persistence_adapter
        self._authority_resolver = authority_resolver

    def review_ready_bundle(
        self,
        review: IndependentReviewRecordV1,
        *,
        principal_id: str,
        capability_bundle_id: str,
        context: ComputationContextKeyV1,
        component_or_template_ref: str,
        traceparent: str,
        tracestate: str,
    ) -> EconomicReceiptEventSpineV1:
        if type(review) is not IndependentReviewRecordV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "review producer requires the exact independent-review record",
            )
        for name, value in (
            ("principal_id", principal_id),
            ("capability_bundle_id", capability_bundle_id),
            ("component_or_template_ref", component_or_template_ref),
            ("traceparent", traceparent),
        ):
            _text(value, name)
        if type(context) is not ComputationContextKeyV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "review producer requires one exact context",
            )
        if not isinstance(tracestate, str):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "tracestate must be text",
            )
        context_ref = context.context_id
        authority_request = IndependentReviewAuthorityRequestV1(
            request_id=(
                "ST12F-INDEPENDENT-REVIEW-AUTHORITY::"
                f"{review.review_id}"
            ),
            requested_at=review.reviewed_at,
            principal_id=principal_id,
            capability_bundle_id=capability_bundle_id,
            context=context,
            idempotency_key=(
                "ST12F-INDEPENDENT-REVIEW-AUTHORITY::"
                f"{review.review_id}"
            ),
            traceparent=traceparent,
            tracestate=tracestate,
            prior_bundle_ref=review.prior_bundle_ref,
            input_lock_id=review.input_lock_id,
            component_or_template_ref=component_or_template_ref,
            reviewer_identity=review.reviewer_identity,
            bundle_producer_identity=review.bundle_producer_identity,
        )
        authority_decision = self._authority_resolver.admit_operation(
            authority_request
        )
        authority_valid = (
            type(authority_decision) is AgentCapabilityDecisionV1
            and authority_decision.authorizes_independent_review(
                principal_id=principal_id,
                reviewer_identity=review.reviewer_identity,
                authority_receipt_ref=review.authority_receipt_ref,
                context_ref=context_ref,
                input_lock_id=review.input_lock_id,
                component_or_template_ref=component_or_template_ref,
            )
        )
        if not authority_valid:
            raise AuthorityDeniedError(
                ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
                "review authority does not match the private no-effect request",
            )
        authority_row = (
            self._authority_resolver
            .resolve_preexisting_agent_orch_decision_receipt(
                authority_decision.agent_orch_receipt_ref
            )
        )
        required_row_fields = {
            "object_type": "AgentDecisionReceiptV1",
            "control_plane_only": True,
            "fake_receipt_created": False,
            "live_execution_created": False,
            "order_submission_created": False,
            "runtime_side_effect_allowed": False,
            "source_truth_created": False,
        }
        if (
            not isinstance(authority_row, Mapping)
            or authority_row.get("row_id")
            != authority_decision.agent_orch_receipt_ref
            or any(
                authority_row.get(name) != value
                for name, value in required_row_fields.items()
            )
        ):
            raise AuthorityDeniedError(
                ReasonCode.SEGREGATION_OF_DUTIES_VIOLATION,
                "review authority row is absent, mismatched, or effect-bearing",
            )

        cutoff = review.reviewed_at
        parent_rows = tuple(
            row
            for row in self._persistence.reconstruct_as_of(
                effective_cutoff=cutoff,
                recorded_cutoff=cutoff,
                aggregate_scope=(),
            )
            if type(row) is EconomicReceiptEventSpineV1
            and row.record_id == review.prior_bundle_ref
        )
        if len(parent_rows) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review parent is not durable before the review cutoff",
            )
        parent_spine = parent_rows[0]
        if (
            type(parent_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or parent_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review parent is not an evidence-bundle receipt",
            )
        parent = parent_spine.typed_payload.reconstruct(
            ComputationEvidenceBundleV1
        )
        lock = self._cohort_resolver.resolve_input_lock(
            review.input_lock_id,
            decision_cutoff=cutoff,
        )
        if (
            parent.terminal_state
            is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            or parent.evidence_id != review.evidence_id
            or parent.input_lock_id != review.input_lock_id
            or parent.component_or_template_ref != component_or_template_ref
            or parent.evidence_bundle_version == review.evidence_bundle_version
            or review.reviewed_source_epoch_refs != _source_epoch_refs(lock)
            or review.bundle_producer_identity == review.reviewer_identity
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review does not bind the exact READY parent, candidate, lock, or scope",
            )

        record_id = (
            f"ST12F-RECEIPT::{review.review_id}::INDEPENDENT_REVIEW_VERSION"
        )
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=record_id,
            receipt_class=ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
            operation_id="ST12F-PRIVATE::INDEPENDENT_REVIEW",
            request_id=authority_decision.request_id,
            idempotency_key=(
                f"{authority_decision.idempotency_key}::REVIEW::{review.review_id}"
            ),
            contract_type=type(review).__name__,
            contract_id=review.review_id,
            contract_version=review.contract_version,
            input_lock_id_or_explicit_absence=review.input_lock_id,
            parent_version_ref_or_explicit_absence=review.prior_bundle_ref,
            canonical_contract_json=review.canonical_json(),
            source_record_refs=(
                review.prior_bundle_ref,
                review.authority_receipt_ref,
            ),
            parameter_value_refs=lock.parameter_value_refs,
            source_epoch_refs=_source_epoch_refs(lock),
            typed_reason_codes=review.blocker_codes,
            terminal_state=review.decision.value,
            fixture_only_not_evidence=False,
        )
        spine = EconomicReceiptEventSpineV1(
            record_id=record_id,
            record_type=EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL,
            schema_version="QTT_ST12F_EVIDENCE_CONTROL_RECEIPT_SPINE_V1",
            semantic_owner="IndependentEvidenceReviewV1",
            implementation_owner="IndependentEvidenceReviewV1",
            context_ref=context_ref,
            effective_at=review.reviewed_at,
            recorded_at=review.reviewed_at,
            causation_id=lock.causation_id,
            correlation_id=lock.correlation_id,
            traceparent=traceparent,
            tracestate=tracestate,
            sequence=0,
            aggregate_id=review.review_id,
            aggregate_version=1,
            authority_class="INDEPENDENT_REVIEW_NO_EFFECT",
            typed_payload=payload,
            no_effect_flags=NO_EFFECTS_V1,
        )
        transition = StateTransitionReceiptV1(
            transition_id=f"ST12F-CONTROL-STATE::{record_id}",
            aggregate_id=f"ST12F-CONTROL::{record_id}",
            transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
            prior_state="NEW",
            event_class="ST12F_INDEPENDENT_REVIEW_COMMITTED",
            candidate_state="ACTIVE",
            disposition=TransitionDispositionV1.ACCEPTED,
            event_identity=record_id,
            aggregate_version_before=0,
            aggregate_version_after=1,
            effective_at=review.reviewed_at,
            recorded_at=review.reviewed_at,
            reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
            reconciliation_required=False,
        )
        transaction = self._persistence.begin_transaction()
        try:
            self._persistence.insert_receipt_record(transaction, spine)
            self._persistence.insert_state_transition(transaction, transition)
            transaction.commit()
        except BaseException:
            if transaction.is_active:
                transaction.rollback()
            raise
        persisted = self._persistence.get_record(record_id)
        if type(persisted) is not EconomicReceiptEventSpineV1:
            raise PersistenceContractError(
                ReasonCode.OWNER_DATA_MISSING,
                "committed independent-review receipt is absent",
            )
        return persisted


class ComputationEvidenceServiceV1:
    """One evidence owner over injected compiler, review, and ST12-C owners."""

    supports_typed_reference_query = True

    @classmethod
    def bind_measured_evidence_v1(cls, *, host_binding, issuer, issuer_context, cohort_resolver):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceIssuerContextV1, EvidenceHostBindingV1
        from .context import _native_require
        from .models import EvidenceKeyPurposeV1
        from .cohort_compiler import ReplayPaperCohortCompilerV1
        state = EvidenceIssuerContextV1._identity_for_owner_v1(issuer_context, issuer)
        _native_require(cls is ComputationEvidenceServiceV1 and type(host_binding) is EvidenceHostBindingV1
                        and type(cohort_resolver) is ReplayPaperCohortCompilerV1 and state.supervisor is not None
                        and host_binding.signing_purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER
                        and len(state.supervisor._lane_platforms) == 2
                        and all(lane._host is host_binding for lane in state.supervisor._lane_platforms),
                        "LP03_MEASURED_EVIDENCE_ORIGINAL_BINDING")
        with state.lock:
            _native_require(state.operation is None and state.measured_evidence_binding is None,
                            "LP03_MEASURED_EVIDENCE_ALREADY_BOUND_OR_BUSY")
            result = object.__new__(cls)
            result._measured_original = (state, host_binding, cohort_resolver, issuer_context, issuer, result)
            state.measured_evidence_binding = (result, result._measured_original)
            return result

    def _assert_measured_binding_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceIssuerContextV1
        from .context import _native_require
        original = getattr(self, "_measured_original", None)
        _native_require(type(self) is ComputationEvidenceServiceV1 and type(original) is tuple and len(original) == 6
                        and original[5] is self and EvidenceIssuerContextV1._identity_for_owner_v1(original[3], original[4]) is original[0]
                        and original[0].measured_evidence_binding is not None
                        and original[0].measured_evidence_binding[0] is self
                        and original[0].measured_evidence_binding[1] is original,
                        "LP03_MEASURED_EVIDENCE_BINDING_CHANGED")

    def build_measured_bundle_v1(self, experiment_ref):
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService
        ComputationEvidenceServiceV1._assert_measured_binding_v1(self)
        return AgentOrchService._build_evidence_ready_conformance_v1(self._measured_original[4],
            service=self, experiment_ref=experiment_ref, issuer_context=self._measured_original[3])

    def build_reviewed_bundle_v1(self, candidate_ref, review_ref):
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService
        ComputationEvidenceServiceV1._assert_measured_binding_v1(self)
        return AgentOrchService._build_reviewed_evidence_conformance_v1(self._measured_original[4],
            service=self, candidate_ref=candidate_ref, review_ref=review_ref, issuer_context=self._measured_original[3])

    def create_measured_delivery_v1(self, candidate_ref, *, receiver_context):
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService
        ComputationEvidenceServiceV1._assert_measured_binding_v1(self)
        return AgentOrchService._issue_evidence_delivery_v1(self._measured_original[4], service=self,
            candidate_ref=candidate_ref, receiver_context=receiver_context, issuer_context=self._measured_original[3])

    def close_measured_bundle_v1(self, candidate_ref, *, receiver_ack_refs):
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService
        ComputationEvidenceServiceV1._assert_measured_binding_v1(self)
        return AgentOrchService._close_evidence_conformance_v1(self._measured_original[4], service=self,
            candidate_ref=candidate_ref, receiver_ack_refs=receiver_ack_refs, issuer_context=self._measured_original[3])

    def resolve_measured_review_parent_v1(self, operation):
        from .context import _native_require
        from .persistence import _EvidenceReviewOperationV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        ComputationEvidenceServiceV1._assert_measured_binding_v1(self)
        _native_require(type(operation) is _EvidenceReviewOperationV1 and operation.reviewer._measured_original[1] is self
                        and operation.phase == "ADMITTED_AND_READBACK", "LP03_REVIEW_ORIGINAL_PARENT_RESOLVER_SCOPE")
        SQLiteReferenceAdapterV1._evidence_read_review_v1(operation.issuer.control_store, operation, stage="PARENTS")
        return operation.parent.record

    def __init__(
        self,
        cohort_resolver: CohortCompilationResolverProtocolV1,
        persistence_adapter: PersistenceAdapterV1,
        *,
        bundle_candidate_resolver: EvidenceBundleCandidateResolverProtocolV1 | None = None,
        producer_identity: str = "ComputationEvidenceServiceV1",
    ) -> None:
        if not isinstance(persistence_adapter, PersistenceAdapterV1) or persistence_adapter.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "OP14/OP15 require existing available ST12-C persistence")
        if not callable(getattr(cohort_resolver, "resolve_input_lock", None)) or not callable(getattr(cohort_resolver, "resolve_expected_slot", None)):
            raise ContractValidationError(ReasonCode.INPUT_OWNER_MISMATCH, "evidence service requires the canonical compiler resolver")
        self._cohort_resolver = cohort_resolver
        self._persistence = persistence_adapter
        self._bundle_candidate_resolver = bundle_candidate_resolver
        self._producer_identity = _text(producer_identity, "producer_identity")
        minimum = datetime.min.replace(tzinfo=UTC)
        self._cache_snapshot = EvidenceCacheSnapshotV1(
            generation=0,
            effective_watermark=minimum,
            recorded_watermark=minimum,
            lane_results={},
            slot_results={},
            divergence={},
            bundles={},
            current_bundles={},
            reviews={},
            d_references={},
            g_handoffs={},
        )
        self._cache_publication_lock = Lock()
        now = datetime.now(UTC)
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=now,
            recorded_cutoff=now,
        )

    @staticmethod
    def _contract_type_for_receipt_class(
        receipt_class: ST12FReceiptClassV1,
    ) -> type[object]:
        mapping: Mapping[ST12FReceiptClassV1, type[object]] = {
            ST12FReceiptClassV1.REPLAY_REGISTRATION: ReplayResultContractV1,
            ST12FReceiptClassV1.PAPER_REGISTRATION: PaperResultContractV1,
            ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT: DivergenceAssessmentV1,
            ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT: ModelRiskEvidenceAssessmentV1,
            ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION: QuantumTraceValidationReceiptV1,
            ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION: DeterministicEvidenceAnnotationContractV1,
            ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION: ComputationEvidenceBundleV1,
            ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION: IndependentReviewRecordV1,
            ST12FReceiptClassV1.D_EVIDENCE_REFERENCE: ST12FEvidenceReferenceV1,
            ST12FReceiptClassV1.G_HANDOFF_REFERENCE: FToGHandoffReferencesV1,
        }
        try:
            return mapping[receipt_class]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "receipt class is not owned by OP14/OP15",
            ) from exc

    def _records_as_of(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> tuple[object, ...]:
        effective = parse_utc(effective_cutoff, field_name="effective_cutoff")
        recorded = parse_utc(recorded_cutoff, field_name="recorded_cutoff")
        return self._persistence.reconstruct_as_of(
            effective_cutoff=effective,
            recorded_cutoff=recorded,
            aggregate_scope=(),
        )

    def _durable_receipt_spines(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> tuple[EconomicReceiptEventSpineV1, ...]:
        rows = self._persistence.reconstruct_as_of(
            effective_cutoff=parse_utc(
                effective_cutoff,
                field_name="effective_cutoff",
            ),
            recorded_cutoff=parse_utc(
                recorded_cutoff,
                field_name="recorded_cutoff",
            ),
            aggregate_scope=(),
        )
        return tuple(
            sorted(
                (
                    row
                    for row in rows
                    if type(row) is EconomicReceiptEventSpineV1
                    and type(row.typed_payload) is ST12FEvidenceControlReceiptRecordV1
                ),
                key=lambda row: (row.recorded_at, row.record_id),
            )
        )

    def _durable_computation_spines(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> tuple[EconomicReceiptEventSpineV1, ...]:
        return tuple(
            sorted(
                (
                    row
                    for row in self._records_as_of(
                        effective_cutoff=effective_cutoff,
                        recorded_cutoff=recorded_cutoff,
                    )
                    if type(row) is EconomicReceiptEventSpineV1
                    and row.record_type
                    is EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
                    and type(row.typed_payload)
                    is DurableComputationExecutionReceiptRecordV1
                ),
                key=lambda row: (row.recorded_at, row.record_id),
            )
        )

    def _spine_as_of(
        self,
        record_ref: str,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> EconomicReceiptEventSpineV1:
        matches = tuple(
            row
            for row in self._records_as_of(
                effective_cutoff=effective_cutoff,
                recorded_cutoff=recorded_cutoff,
            )
            if type(row) is EconomicReceiptEventSpineV1
            and row.record_id == record_ref
        )
        if len(matches) != 1:
            raise PersistenceContractError(
                ReasonCode.OWNER_DATA_MISSING,
                "receipt is absent at the explicit effective/recorded cutoff",
            )
        return matches[0]

    def _validate_receipt_lock_metadata(
        self,
        spine: EconomicReceiptEventSpineV1,
        *,
        decision_cutoff: datetime,
    ) -> None:
        payload = spine.typed_payload
        assert type(payload) is ST12FEvidenceControlReceiptRecordV1
        if payload.input_lock_id_or_explicit_absence == "EXPLICIT_ABSENCE":
            if payload.parameter_value_refs or payload.source_epoch_refs:
                raise ContractValidationError(
                    ReasonCode.SCHEMA_MISMATCH,
                    "lock-absent receipt carries parameter or epoch pins",
                )
            return
        lock = self._cohort_resolver.resolve_input_lock(
            payload.input_lock_id_or_explicit_absence,
            decision_cutoff=decision_cutoff,
        )
        if (
            payload.parameter_value_refs != lock.parameter_value_refs
            or payload.source_epoch_refs != _source_epoch_refs(lock)
        ):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "receipt parameter or epoch pins differ from the canonical input lock",
            )

    @staticmethod
    def _natural_slot(
        value: ReplayResultContractV1 | PaperResultContractV1,
        lane: str,
    ) -> tuple[str, str, str, str]:
        return (
            value.input_lock_id,
            lane,
            value.cohort_template_id,
            value.expected_result_contract_id,
        )

    @staticmethod
    def _validate_contract_visibility(
        value: object,
        *,
        evaluation_time: datetime,
    ) -> None:
        evaluation = parse_utc(
            evaluation_time,
            field_name="evaluation_time",
        )
        observed = getattr(value, "observed_at", None)
        if observed is None:
            observed = getattr(value, "reviewed_at", None)
        valid_until = getattr(value, "valid_until", None)
        if (
            isinstance(observed, datetime)
            and evaluation < parse_utc(observed, field_name="observed_at")
        ) or (
            isinstance(valid_until, datetime)
            and evaluation > parse_utc(valid_until, field_name="valid_until")
        ):
            raise ContractValidationError(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "contract is not visible at the explicit decision cutoff",
            )

    def _rebuild_caches_from_durable_receipts(
        self,
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> EvidenceCacheSnapshotV1:
        effective = parse_utc(effective_cutoff, field_name="effective_cutoff")
        recorded = parse_utc(recorded_cutoff, field_name="recorded_cutoff")
        observed_snapshot = self._cache_snapshot
        effective = max(effective, observed_snapshot.effective_watermark)
        recorded = max(recorded, observed_snapshot.recorded_watermark)
        lane_results: dict[str, ReplayResultContractV1 | PaperResultContractV1] = {}
        slots: dict[tuple[str, str, str, str], str] = {}
        divergence: dict[str, DivergenceAssessmentV1] = {}
        bundles: dict[str, ComputationEvidenceBundleV1] = {}
        bundle_rows: list[
            tuple[str, ComputationEvidenceBundleV1, str]
        ] = []
        current: dict[tuple[str, str, str], str] = {}
        reviews: dict[str, IndependentReviewRecordV1] = {}
        d_references: dict[str, ST12FEvidenceReferenceV1] = {}
        g_handoffs: dict[str, FToGHandoffReferencesV1] = {}
        for spine in self._durable_receipt_spines(
            effective_cutoff=effective,
            recorded_cutoff=recorded,
        ):
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class in {
                ST12FReceiptClassV1.COHORT_COMPILATION,
                ST12FReceiptClassV1.INPUT_LOCK,
            }:
                continue
            expected_type = self._contract_type_for_receipt_class(payload.receipt_class)
            value = payload.reconstruct(expected_type)
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=recorded,
            )
            if type(value) in {ReplayResultContractV1, PaperResultContractV1}:
                lane = (
                    "REPLAY"
                    if type(value) is ReplayResultContractV1
                    else "PAPER"
                )
                assert isinstance(value, ReplayResultContractV1 | PaperResultContractV1)
                slot = self._natural_slot(value, lane)
                if (
                    value.result_id in lane_results
                    and deterministic_json(lane_results[value.result_id])
                    != deterministic_json(value)
                ):
                    raise ContractValidationError(
                        ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                        "durable result identity binds competing canonical packets",
                    )
                previous_id = slots.get(slot)
                if previous_id is not None and deterministic_json(lane_results[previous_id]) != deterministic_json(value):
                    raise ContractValidationError(
                        ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                        "durable natural slot has competing canonical packets",
                    )
                lane_results[value.result_id] = value
                slots[slot] = value.result_id
            elif type(value) is DivergenceAssessmentV1:
                divergence[value.assessment_id] = value
            elif type(value) is ComputationEvidenceBundleV1:
                bundles[spine.record_id] = value
                bundles[value.evidence_bundle_version] = value
                bundle_rows.append(
                    (
                        spine.record_id,
                        value,
                        payload.parent_version_ref_or_explicit_absence,
                    )
                )
            elif type(value) is IndependentReviewRecordV1:
                reviews[value.review_id] = value
                reviews[spine.record_id] = value
            elif type(value) is ST12FEvidenceReferenceV1:
                d_references[value.reference_id] = value
                d_references[spine.record_id] = value
            elif type(value) is FToGHandoffReferencesV1:
                g_handoffs[value.handoff_id] = value
                g_handoffs[spine.record_id] = value
        identities = {
            (
                value.evidence_id,
                value.input_lock_id,
                value.component_or_template_ref,
            )
            for _, value, _ in bundle_rows
        }
        for identity in identities:
            current[identity] = self._bundle_leaf_ref(
                tuple(
                    row
                    for row in bundle_rows
                    if (
                        row[1].evidence_id,
                        row[1].input_lock_id,
                        row[1].component_or_template_ref,
                    )
                    == identity
                )
            )
        candidate = EvidenceCacheSnapshotV1(
            generation=0,
            effective_watermark=effective,
            recorded_watermark=recorded,
            lane_results=lane_results,
            slot_results=slots,
            divergence=divergence,
            bundles=bundles,
            current_bundles=current,
            reviews=reviews,
            d_references=d_references,
            g_handoffs=g_handoffs,
        )
        with self._cache_publication_lock:
            current_snapshot = self._cache_snapshot
            if (
                current_snapshot.effective_watermark > effective
                or current_snapshot.recorded_watermark > recorded
            ):
                return current_snapshot
            published = replace(
                candidate,
                generation=current_snapshot.generation + 1,
            )
            self._cache_snapshot = published
            return published

    def _load_contract(
        self,
        record_ref: str,
        expected_type: type[object],
        *,
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
    ) -> object:
        spine = self._spine_as_of(
            record_ref,
            effective_cutoff=effective_cutoff,
            recorded_cutoff=recorded_cutoff,
        )
        if type(spine) is not EconomicReceiptEventSpineV1 or type(spine.typed_payload) is not ST12FEvidenceControlReceiptRecordV1:
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "typed ST12-F receipt is absent")
        value = spine.typed_payload.reconstruct(expected_type)
        self._validate_receipt_lock_metadata(
            spine,
            decision_cutoff=recorded_cutoff,
        )
        self._validate_contract_visibility(
            value,
            evaluation_time=effective_cutoff,
        )
        return value

    def resolve_lane_result(
        self,
        result_id: str,
        lane: str,
        *,
        decision_cutoff: datetime,
    ) -> ReplayResultContractV1 | PaperResultContractV1:
        expected_type = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1 if lane == "PAPER" else None
        if expected_type is None:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "lane must be exact")
        receipt_ref = f"ST12F-RECEIPT::{result_id}::{lane}_REGISTRATION"
        value = self._load_contract(
            receipt_ref,
            expected_type,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        if type(value) is not expected_type:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "REPLAY/PAPER packets are non-interchangeable")
        return value  # type: ignore[return-value]

    def resolve_bundle(
        self,
        bundle_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> ComputationEvidenceBundleV1:
        value = self._load_contract(
            bundle_ref,
            ComputationEvidenceBundleV1,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        return value  # type: ignore[return-value]

    def resolve_review(
        self,
        review_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> IndependentReviewRecordV1:
        receipt_ref = (
            review_ref
            if review_ref.startswith("ST12F-RECEIPT::")
            else f"ST12F-RECEIPT::{review_ref}::INDEPENDENT_REVIEW_VERSION"
        )
        value = self._load_contract(
            receipt_ref,
            IndependentReviewRecordV1,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        return value  # type: ignore[return-value]

    def resolve_control_receipt(
        self,
        receipt_ref: str,
        expected_type: type[object],
        *,
        decision_cutoff: datetime,
    ) -> object:
        """Canonical read path for every OP14/OP15 receipt class."""

        return self._load_contract(
            receipt_ref,
            expected_type,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )

    def resolve_g_handoff(
        self,
        handoff_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> FToGHandoffReferencesV1:
        receipt_ref = (
            handoff_ref
            if handoff_ref.startswith("ST12F-RECEIPT::")
            else f"ST12F-RECEIPT::{handoff_ref}::G_HANDOFF_REFERENCE"
        )
        value = self._load_contract(
            receipt_ref,
            FToGHandoffReferencesV1,
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        )
        return value  # type: ignore[return-value]

    @staticmethod
    def _contract_receipt_parts(
        contract: object,
    ) -> tuple[
        ST12FReceiptClassV1,
        str,
        str,
        tuple[str, ...],
        str,
        tuple[ReasonCode, ...],
    ]:
        if type(contract) is ReplayResultContractV1:
            return (
                ST12FReceiptClassV1.REPLAY_REGISTRATION,
                contract.result_id,
                "EXPLICIT_ABSENCE",
                (contract.run_reference,),
                "REPLAY_REGISTERED",
                (),
            )
        if type(contract) is PaperResultContractV1:
            return (
                ST12FReceiptClassV1.PAPER_REGISTRATION,
                contract.result_id,
                "EXPLICIT_ABSENCE",
                (contract.run_reference,),
                "PAPER_REGISTERED",
                (),
            )
        if type(contract) is DivergenceAssessmentV1:
            return (
                ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT,
                contract.assessment_id,
                "EXPLICIT_ABSENCE",
                (contract.replay_result_ref, contract.paper_result_ref),
                contract.terminal_state.value,
                contract.typed_blockers,
            )
        if type(contract) is ModelRiskEvidenceAssessmentV1:
            return (
                ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT,
                contract.assessment_id,
                "EXPLICIT_ABSENCE",
                contract.receipt_refs,
                contract.terminal_state,
                contract.blocker_codes,
            )
        if type(contract) is QuantumTraceValidationReceiptV1:
            return (
                ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION,
                contract.receipt_id,
                "EXPLICIT_ABSENCE",
                (
                    contract.trace_id,
                    contract.strongest_classical_receipt_ref,
                    contract.no_trade_receipt_ref,
                ),
                contract.terminal_state,
                (),
            )
        if type(contract) is DeterministicEvidenceAnnotationContractV1:
            return (
                ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION,
                contract.annotation_id,
                "EXPLICIT_ABSENCE",
                tuple(
                    dict.fromkeys(
                        (
                            *contract.evidence_bundle_refs,
                            *(row.evidence_receipt_ref for row in contract.canonical_numeric_evidence),
                            *contract.deterministic_numeric_recheck_receipt_refs,
                        )
                    )
                ),
                "ANNOTATION_VALIDATED_NO_EFFECT",
                (),
            )
        if type(contract) is ComputationEvidenceBundleV1:
            return (
                ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION,
                contract.evidence_bundle_version,
                "EXPLICIT_ABSENCE",
                contract.source_and_provenance_refs,
                contract.terminal_state.value,
                contract.blocker_codes,
            )
        if type(contract) is IndependentReviewRecordV1:
            return (
                ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
                contract.review_id,
                contract.prior_bundle_ref,
                (contract.prior_bundle_ref, contract.authority_receipt_ref),
                contract.decision.value,
                contract.blocker_codes,
            )
        if type(contract) is ST12FEvidenceReferenceV1:
            return (
                ST12FReceiptClassV1.D_EVIDENCE_REFERENCE,
                contract.reference_id,
                contract.evidence_ref,
                (contract.evidence_ref,),
                contract.terminal_state,
                (),
            )
        if type(contract) is FToGHandoffReferencesV1:
            return (
                ST12FReceiptClassV1.G_HANDOFF_REFERENCE,
                contract.handoff_id,
                contract.evidence_bundle_ref,
                tuple(
                    dict.fromkeys(
                        (
                            contract.evidence_bundle_ref,
                            *contract.no_trade_blocker_refs,
                            *contract.champion_challenger_evidence_refs,
                            *contract.portfolio_utility_refs,
                            contract.quantum_classical_comparison_receipt_ref,
                        )
                    )
                ),
                contract.terminal_state,
                (),
            )
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "OP14/OP15 contract is outside the receipt allowlist",
        )

    def _receipt(
        self,
        *,
        request: (
            RegisterReplayPaperResultRequestV1
            | BuildEvidenceBundleRequestV1
            | RegisterEvidenceControlRequestV1
        ),
        contract: object,
        input_lock: ImmutableReplayPaperInputLockV1,
        bundle_parent_ref: str | None = None,
    ) -> EconomicReceiptEventSpineV1:
        (
            receipt_class,
            contract_id,
            parent_ref,
            source_refs,
            terminal_state,
            reason_codes,
        ) = self._contract_receipt_parts(contract)
        if receipt_class is ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
            if bundle_parent_ref is None:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle receipt construction requires the service-resolved durable parent",
                )
            parent_ref = _text(bundle_parent_ref, "bundle_parent_ref")
        elif bundle_parent_ref is not None:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "non-bundle receipt cannot carry a bundle parent override",
            )
        record_id = f"ST12F-RECEIPT::{contract_id}::{receipt_class.value}"
        operation_id = (
            "ST10-OP::14"
            if type(request) is RegisterReplayPaperResultRequestV1
            else "ST10-OP::15"
            if type(request) is BuildEvidenceBundleRequestV1
            else "ST12F-PRIVATE::REGISTER_CONTROL"
        )
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=record_id,
            receipt_class=receipt_class,
            operation_id=operation_id,
            request_id=request.request_id,
            idempotency_key=request.idempotency_key,
            contract_type=type(contract).__name__,
            contract_id=contract_id,
            contract_version=getattr(contract, "contract_version"),
            input_lock_id_or_explicit_absence=input_lock.input_lock_id,
            parent_version_ref_or_explicit_absence=parent_ref,
            canonical_contract_json=deterministic_json(contract),
            source_record_refs=source_refs,
            parameter_value_refs=input_lock.parameter_value_refs,
            source_epoch_refs=_source_epoch_refs(input_lock),
            typed_reason_codes=reason_codes,
            terminal_state=terminal_state,
            fixture_only_not_evidence=False,
        )
        return EconomicReceiptEventSpineV1(
            record_id=record_id,
            record_type=EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL,
            schema_version="QTT_ST12F_EVIDENCE_CONTROL_RECEIPT_SPINE_V1",
            semantic_owner="ComputationEvidenceServiceV1",
            implementation_owner="ComputationEvidenceServiceV1",
            context_ref=request.context.context_id,
            effective_at=input_lock.decision_time,
            recorded_at=request.requested_at,
            causation_id=input_lock.causation_id,
            correlation_id=input_lock.correlation_id,
            traceparent=request.traceparent,
            tracestate=request.tracestate,
            sequence=0,
            aggregate_id=contract_id,
            aggregate_version=1,
            authority_class="EVIDENCE_CUSTODY_NO_EFFECT",
            typed_payload=payload,
            no_effect_flags=NO_EFFECTS_V1,
        )

    def _persist_many(
        self,
        *,
        request: (
            RegisterReplayPaperResultRequestV1
            | BuildEvidenceBundleRequestV1
            | RegisterEvidenceControlRequestV1
        ),
        spines: tuple[EconomicReceiptEventSpineV1, ...],
        primary_record_ref: str,
        identity_class: str,
        extra_transitions: tuple[StateTransitionReceiptV1, ...] = (),
    ) -> EconomicReceiptEventSpineV1:
        if not spines or primary_record_ref not in {row.record_id for row in spines}:
            raise ContractValidationError(
                ReasonCode.INCOMPLETE_CONTRACT,
                "atomic ST12-F persistence requires a primary receipt",
            )
        canonical_request = deterministic_json(
            {
                "request": safe_json_loads(canonical_request_json_v1(request)),
                "contracts": [
                    safe_json_loads(row.typed_payload.canonical_contract_json)
                    for row in spines
                ],
            }
        )
        claim = IdempotencyClaimReceiptV1(
            claim_id=f"ST12F-IDEMPOTENCY::{request.idempotency_key}::{identity_class}",
            idempotency_key=request.idempotency_key,
            identity_class=identity_class,
            canonical_request_json=canonical_request,
            claim_state=IdempotencyClaimStateV1.ACQUIRED,
            result_record_ref=None,
            created_at=request.requested_at,
            completed_at=None,
            failure_code=None,
        )
        transaction = self._persistence.begin_transaction()
        try:
            acquisition = self._persistence.acquire_idempotency_claim(transaction, claim)
            if acquisition.outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD:
                transaction.rollback()
                original = self._persistence.get_record(acquisition.original_result_ref or "")
                if type(original) is not EconomicReceiptEventSpineV1:
                    raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "idempotent result receipt is absent")
                return original
            if acquisition.outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD:
                raise IdempotencyContractError(ReasonCode.IDEMPOTENCY_CONFLICT, "same key binds a different canonical request")
            if acquisition.outcome is not IdempotencyOutcomeV1.ACQUIRED:
                raise IdempotencyContractError(ReasonCode.IDEMPOTENCY_IN_PROGRESS, "same canonical request is already in progress")
            for spine in spines:
                self._persistence.insert_receipt_record(transaction, spine)
                self._persistence.insert_state_transition(
                    transaction,
                    StateTransitionReceiptV1(
                        transition_id=f"ST12F-CONTROL-STATE::{spine.record_id}",
                        aggregate_id=f"ST12F-CONTROL::{spine.record_id}",
                        transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
                        prior_state="NEW",
                        event_class="ST12F_CONTROL_RECEIPT_COMMITTED",
                        candidate_state="ACTIVE",
                        disposition=TransitionDispositionV1.ACCEPTED,
                        event_identity=spine.record_id,
                        aggregate_version_before=0,
                        aggregate_version_after=1,
                        effective_at=spine.effective_at,
                        recorded_at=spine.recorded_at,
                        reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                        reconciliation_required=False,
                    ),
                )
            for transition in extra_transitions:
                self._persistence.insert_state_transition(transaction, transition)
            self._persistence.insert_state_transition(
                transaction,
                StateTransitionReceiptV1(
                    transition_id=f"{claim.claim_id}::ACQUIRED",
                    aggregate_id=claim.claim_id,
                    transition_family="IDEMPOTENCY_CLAIM_STATE_MACHINE_V1",
                    prior_state="UNSEEN",
                    event_class=f"{identity_class}_ACQUIRED",
                    candidate_state="ACQUIRED",
                    disposition=TransitionDispositionV1.ACCEPTED,
                    event_identity=request.request_id,
                    aggregate_version_before=0,
                    aggregate_version_after=1,
                    effective_at=request.requested_at,
                    recorded_at=request.requested_at,
                    reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                    reconciliation_required=False,
                ),
            )
            self._persistence.insert_state_transition(
                transaction,
                StateTransitionReceiptV1(
                    transition_id=f"{claim.claim_id}::COMPLETED",
                    aggregate_id=claim.claim_id,
                    transition_family="IDEMPOTENCY_CLAIM_STATE_MACHINE_V1",
                    prior_state="ACQUIRED",
                    event_class=f"{identity_class}_COMPLETED",
                    candidate_state="COMPLETED",
                    disposition=TransitionDispositionV1.ACCEPTED,
                    event_identity=request.request_id,
                    aggregate_version_before=1,
                    aggregate_version_after=2,
                    effective_at=request.requested_at,
                    recorded_at=request.requested_at,
                    reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                    reconciliation_required=False,
                ),
            )
            self._persistence.bind_idempotency_result(
                transaction,
                acquisition.claim_ref,
                primary_record_ref,
                request.requested_at,
            )
            transaction.commit()
            primary = self._persistence.get_record(primary_record_ref)
            if type(primary) is not EconomicReceiptEventSpineV1:
                raise PersistenceContractError(
                    ReasonCode.OWNER_DATA_MISSING,
                    "committed primary ST12-F receipt is absent",
                )
            return primary
        except BaseException:
            if transaction.is_active:
                transaction.rollback()
            raise

    def register_result(
        self,
        request: RegisterReplayPaperResultRequestV1,
        packet: ReplayResultContractV1 | PaperResultContractV1 | None = None,
    ) -> RegisteredLaneResultOutcomeV1:
        initialize_st12f_parameter_registry_v1()
        if type(request) is not RegisterReplayPaperResultRequestV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP14 delegate requires exact request")
        value = lane_packet_from_typed_record_v1(request.result_packet, lane=request.lane) if packet is None else packet
        expected_type = ReplayResultContractV1 if request.lane == "REPLAY" else PaperResultContractV1
        if type(value) is not expected_type:
            raise ContractValidationError(ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN, "OP14 rejects cross-lane packet substitution")
        lock = self._cohort_resolver.resolve_input_lock(
            request.input_lock_id,
            decision_cutoff=request.requested_at,
        )
        if value.input_lock_id != lock.input_lock_id or request.input_lock_id != lock.input_lock_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "caller and packet lock assertions differ from canonical lock")
        slot = self._cohort_resolver.resolve_expected_slot(
            request.cohort_instance_id,
            request.lane,
            value.expected_result_contract_id,
            decision_cutoff=request.requested_at,
        )
        if (
            getattr(slot, "input_lock_id", None) != lock.input_lock_id
            or getattr(slot, "cohort_template_id", None) != value.cohort_template_id
            or value.point_in_time_cutoff != lock.point_in_time_cutoff
            or dict(value.implementation_versions) != dict(lock.implementation_versions)
            or dict(value.source_epochs) != dict(lock.source_epochs)
            or value.accounting_definition != deterministic_json(lock.accounting_definition)
        ):
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "lane packet differs from exact lock/slot/version/epoch/accounting pins")
        natural_slot = self._natural_slot(value, request.lane)
        durable_lanes, durable_slots = self._durable_lane_index(
            decision_cutoff=request.requested_at,
        )
        existing_id = durable_slots.get(natural_slot)
        if existing_id is not None:
            existing = durable_lanes[existing_id]
            if deterministic_json(existing) == deterministic_json(value):
                receipt_class = (
                    ST12FReceiptClassV1.REPLAY_REGISTRATION
                    if request.lane == "REPLAY"
                    else ST12FReceiptClassV1.PAPER_REGISTRATION
                )
                return RegisteredLaneResultOutcomeV1(
                    registered_result=existing,
                    receipt_refs=(
                        f"ST12F-RECEIPT::{existing.result_id}::"
                        f"{receipt_class.value}",
                    ),
                )
            raise ContractValidationError(ReasonCode.ST12F_RESULT_SLOT_CONFLICT, "a competing result already owns this immutable slot")
        if value.fixture_only_not_evidence:
            return RegisteredLaneResultOutcomeV1(value, ())
        spine = self._receipt(
            request=request,
            contract=value,
            input_lock=lock,
        )
        slot_identity = "::".join(natural_slot)
        slot_transition = StateTransitionReceiptV1(
            transition_id=f"ST12F-NATURAL-SLOT::{slot_identity}::OWNED",
            aggregate_id=f"ST12F-NATURAL-SLOT::{slot_identity}",
            transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
            prior_state="NEW",
            event_class="ST12F_RESULT_SLOT_OWNED",
            candidate_state="ACTIVE",
            disposition=TransitionDispositionV1.ACCEPTED,
            event_identity=spine.record_id,
            aggregate_version_before=0,
            aggregate_version_after=1,
            effective_at=value.closed_at,
            recorded_at=value.closed_at,
            reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
            reconciliation_required=False,
        )
        try:
            persisted = self._persist_many(
                request=request,
                spines=(spine,),
                primary_record_ref=spine.record_id,
                identity_class="ST10-OP::14",
                extra_transitions=(slot_transition,),
            )
        except PersistenceContractError as exc:
            check_lanes, check_slots = self._durable_lane_index(
                decision_cutoff=request.requested_at,
            )
            owner_id = check_slots.get(natural_slot)
            if (
                owner_id is not None
                and deterministic_json(check_lanes[owner_id])
                == deterministic_json(value)
            ):
                receipt_class = (
                    ST12FReceiptClassV1.REPLAY_REGISTRATION
                    if request.lane == "REPLAY"
                    else ST12FReceiptClassV1.PAPER_REGISTRATION
                )
                return RegisteredLaneResultOutcomeV1(
                    registered_result=check_lanes[owner_id],
                    receipt_refs=(
                        f"ST12F-RECEIPT::{owner_id}::{receipt_class.value}",
                    ),
                )
            if owner_id is not None:
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "a competing durable result owns this immutable natural slot",
                ) from exc
            raise
        committed = persisted.typed_payload.reconstruct(expected_type)
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        return RegisteredLaneResultOutcomeV1(
            registered_result=committed,  # type: ignore[arg-type]
            receipt_refs=(persisted.record_id,),
        )

    def _durable_lane_index(
        self,
        *,
        decision_cutoff: datetime,
    ) -> tuple[
        dict[str, ReplayResultContractV1 | PaperResultContractV1],
        dict[tuple[str, str, str, str], str],
    ]:
        lanes: dict[str, ReplayResultContractV1 | PaperResultContractV1] = {}
        slots: dict[tuple[str, str, str, str], str] = {}
        for spine in self._durable_receipt_spines(
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        ):
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class not in {
                ST12FReceiptClassV1.REPLAY_REGISTRATION,
                ST12FReceiptClassV1.PAPER_REGISTRATION,
            }:
                continue
            lane = (
                "REPLAY"
                if payload.receipt_class is ST12FReceiptClassV1.REPLAY_REGISTRATION
                else "PAPER"
            )
            expected = ReplayResultContractV1 if lane == "REPLAY" else PaperResultContractV1
            value = payload.reconstruct(expected)
            assert isinstance(value, ReplayResultContractV1 | PaperResultContractV1)
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=decision_cutoff,
            )
            if (
                value.result_id in lanes
                and deterministic_json(lanes[value.result_id])
                != deterministic_json(value)
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "durable result identity binds competing canonical packets",
                )
            slot = self._natural_slot(value, lane)
            owner = slots.get(slot)
            if owner is not None and deterministic_json(lanes[owner]) != deterministic_json(value):
                raise ContractValidationError(
                    ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                    "durable natural slot contains competing results",
                )
            lanes[value.result_id] = value
            slots[slot] = value.result_id
        return lanes, slots

    def _validate_divergence(
        self,
        assessment: DivergenceAssessmentV1,
        *,
        decision_cutoff: datetime,
    ) -> None:
        if type(assessment) is not DivergenceAssessmentV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "divergence must be exact typed contract")
        replay = self.resolve_lane_result(
            assessment.replay_result_ref,
            "REPLAY",
            decision_cutoff=decision_cutoff,
        )
        paper = self.resolve_lane_result(
            assessment.paper_result_ref,
            "PAPER",
            decision_cutoff=decision_cutoff,
        )
        if replay.input_lock_id != assessment.input_lock_id or paper.input_lock_id != assessment.input_lock_id or replay.cohort_template_id != assessment.cohort_template_id or paper.cohort_template_id != assessment.cohort_template_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "divergence inputs do not share one lock/template")

    def register_control(
        self,
        request: RegisterEvidenceControlRequestV1,
        contract: object,
    ) -> EconomicReceiptEventSpineV1:
        """Private durable writer for the four non-review control classes."""

        if type(request) is not RegisterEvidenceControlRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "control registration requires the exact private request",
            )
        allowed = {
            DivergenceAssessmentV1,
            ModelRiskEvidenceAssessmentV1,
            QuantumTraceValidationReceiptV1,
            DeterministicEvidenceAnnotationContractV1,
        }
        if type(contract) not in allowed:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "private control registration rejects bundle, review, D, and G custody",
            )
        lock = self._cohort_resolver.resolve_input_lock(
            request.input_lock_id,
            decision_cutoff=request.requested_at,
        )
        if getattr(contract, "input_lock_id", None) != lock.input_lock_id:
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "control input lock differs from the private request",
            )
        if type(contract) is DivergenceAssessmentV1:
            self._validate_divergence(
                contract,
                decision_cutoff=request.requested_at,
            )
        spine = self._receipt(request=request, contract=contract, input_lock=lock)
        receipt_class, *_ = self._contract_receipt_parts(contract)
        persisted = self._persist_many(
            request=request,
            spines=(spine,),
            primary_record_ref=spine.record_id,
            identity_class=f"ST12F-PRIVATE::REGISTER_CONTROL::{receipt_class.value}",
        )
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        return persisted

    def build_bundle(
        self,
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1 | None = None,
    ) -> BuiltEvidenceBundleOutcomeV1:
        initialize_st12f_parameter_registry_v1()
        if type(request) is not BuildEvidenceBundleRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "OP15 requires the exact public request",
            )
        if candidate is None and self._bundle_candidate_resolver is not None:
            candidate = self._bundle_candidate_resolver.resolve_bundle_candidate(request)
        if type(candidate) is not ComputationEvidenceBundleV1:
            raise ContractValidationError(ReasonCode.CONTRACT_OR_TYPE_INVALID, "OP15 requires exact request and canonical candidate")
        lock = self._cohort_resolver.resolve_input_lock(
            request.input_lock_id,
            decision_cutoff=request.requested_at,
        )
        if candidate.input_lock_id != lock.input_lock_id or candidate.component_or_template_ref != request.component_id or request.required_lanes != ("REPLAY", "PAPER"):
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "OP15 scope differs from canonical lock/component/dual lane")
        bundle_record_ref = f"ST12F-RECEIPT::{candidate.evidence_bundle_version}::EVIDENCE_BUNDLE_VERSION"
        try:
            existing_bundle_spine = self._spine_as_of(
                bundle_record_ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
        except PersistenceContractError:
            existing_bundle_spine = None
        if existing_bundle_spine is not None:
            if type(existing_bundle_spine) is not EconomicReceiptEventSpineV1:
                raise PersistenceContractError(
                    ReasonCode.PERSISTENCE_CONFLICT,
                    "bundle version identity is owned by a non-receipt record",
                )
            existing_bundle = existing_bundle_spine.typed_payload.reconstruct(
                ComputationEvidenceBundleV1
            )
            if deterministic_json(existing_bundle) != deterministic_json(candidate):
                raise PersistenceContractError(
                    ReasonCode.PERSISTENCE_CONFLICT,
                    "immutable bundle version already binds different evidence",
                )
            existing_refs: list[str] = [bundle_record_ref]
            if candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
                assert type(candidate.d_evidence_reference_projection) is ST12FEvidenceReferenceV1
                assert type(candidate.g_handoff_projection) is FToGHandoffReferencesV1
                existing_refs.extend(
                    (
                        f"ST12F-RECEIPT::{candidate.d_evidence_reference_projection.reference_id}::D_EVIDENCE_REFERENCE",
                        f"ST12F-RECEIPT::{candidate.g_handoff_projection.handoff_id}::G_HANDOFF_REFERENCE",
                    )
                )
            for ref in existing_refs:
                self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            return BuiltEvidenceBundleOutcomeV1(
                evidence_bundle=existing_bundle,
                receipt_refs=tuple(existing_refs),
            )
        previous_ref = self._durable_current_bundle_ref(
            candidate.evidence_id,
            candidate.input_lock_id,
            candidate.component_or_template_ref,
            decision_cutoff=request.requested_at,
        )
        expected_parent = previous_ref or "EXPLICIT_ABSENCE"
        previous = (
            None
            if previous_ref is None
            else self.resolve_bundle(
                previous_ref,
                decision_cutoff=request.requested_at,
            )
        )
        self._validate_bundle_transition(previous, candidate)

        replay = (
            None
            if candidate.replay_result_ref == "EXPLICIT_ABSENCE"
            else self.resolve_lane_result(
                candidate.replay_result_ref,
                "REPLAY",
                decision_cutoff=request.requested_at,
            )
        )
        paper = (
            None
            if candidate.paper_result_ref == "EXPLICIT_ABSENCE"
            else self.resolve_lane_result(
                candidate.paper_result_ref,
                "PAPER",
                decision_cutoff=request.requested_at,
            )
        )
        self._validate_bundle_lanes(candidate, lock, replay, paper)
        admission = self._admit_bundle_evidence(
            request=request,
            candidate=candidate,
            lock=lock,
            replay=replay,
            paper=paper,
        )
        divergence = admission.divergence
        if divergence is not None:
            if divergence.assessment_id != candidate.divergence_assessment_ref:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle divergence reference differs from its contract",
                )
            self._validate_divergence(
                divergence,
                decision_cutoff=request.requested_at,
            )
        self._validate_bundle_divergence(candidate, divergence)
        model_risk = admission.model_risk
        review = admission.review
        self._validate_bundle_model_risk(
            request=request,
            previous_ref=previous_ref,
            previous=previous,
            candidate=candidate,
            lock=lock,
            model_risk=model_risk,
            review=review,
        )
        self._validate_bundle_review(
            request=request,
            lock=lock,
            previous_ref=previous_ref,
            previous=previous,
            candidate=candidate,
            review=review,
        )
        self._validate_bundle_transition_guard(
            request=request,
            previous_ref=previous_ref,
            previous=previous,
            candidate=candidate,
            lock=lock,
        )

        self._validate_closed_projections(
            candidate,
            bundle_record_ref=bundle_record_ref,
            lock=lock,
        )
        bundle_spine = self._receipt(
            request=request,
            contract=candidate,
            input_lock=lock,
            bundle_parent_ref=expected_parent,
        )
        spines: list[EconomicReceiptEventSpineV1] = [bundle_spine]
        if candidate.terminal_state is EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
            assert type(candidate.d_evidence_reference_projection) is ST12FEvidenceReferenceV1
            assert type(candidate.g_handoff_projection) is FToGHandoffReferencesV1
            spines.extend(
                (
                    self._receipt(request=request, contract=candidate.d_evidence_reference_projection, input_lock=lock),
                    self._receipt(request=request, contract=candidate.g_handoff_projection, input_lock=lock),
                )
            )
        parent_aggregate = (
            "ST12F-BUNDLE-PARENT::"
            f"{candidate.evidence_id}::{candidate.input_lock_id}::"
            f"{candidate.component_or_template_ref}::ROOT"
            if previous_ref is None
            else f"ST12F-BUNDLE-PARENT::{previous_ref}"
        )
        parent_edge = StateTransitionReceiptV1(
            transition_id=(
                f"{parent_aggregate}::CHILD::{bundle_spine.record_id}"
            ),
            aggregate_id=parent_aggregate,
            transition_family="UNIT_OF_WORK_STATE_MACHINE_V1",
            prior_state="NEW",
            event_class="ST12F_BUNDLE_CHILD_PUBLISHED",
            candidate_state="ACTIVE",
            disposition=TransitionDispositionV1.ACCEPTED,
            event_identity=bundle_spine.record_id,
            aggregate_version_before=0,
            aggregate_version_after=1,
            effective_at=request.requested_at,
            recorded_at=request.requested_at,
            reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
            reconciliation_required=False,
        )
        try:
            persisted = self._persist_many(
                request=request,
                spines=tuple(spines),
                primary_record_ref=bundle_spine.record_id,
                identity_class="ST10-OP::15",
                extra_transitions=(parent_edge,),
            )
        except PersistenceContractError as exc:
            try:
                concurrent = self._spine_as_of(
                    bundle_record_ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                raise exc
            if (
                type(concurrent.typed_payload)
                is not ST12FEvidenceControlReceiptRecordV1
                or concurrent.typed_payload.receipt_class
                is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
            ):
                raise exc
            concurrent_bundle = concurrent.typed_payload.reconstruct(
                ComputationEvidenceBundleV1
            )
            if deterministic_json(concurrent_bundle) != deterministic_json(candidate):
                raise exc
            concurrent_refs = tuple(row.record_id for row in spines)
            for ref in concurrent_refs:
                self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            return BuiltEvidenceBundleOutcomeV1(
                evidence_bundle=concurrent_bundle,
                receipt_refs=concurrent_refs,
            )
        value = persisted.typed_payload.reconstruct(ComputationEvidenceBundleV1)
        self._rebuild_caches_from_durable_receipts(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        return BuiltEvidenceBundleOutcomeV1(
            evidence_bundle=value,
            receipt_refs=tuple(row.record_id for row in spines),
        )

    def _durable_current_bundle_ref(
        self,
        evidence_id: str,
        input_lock_id: str,
        component_or_template_ref: str,
        *,
        decision_cutoff: datetime,
    ) -> str | None:
        matches: list[
            tuple[str, ComputationEvidenceBundleV1, str]
        ] = []
        for spine in self._durable_receipt_spines(
            effective_cutoff=decision_cutoff,
            recorded_cutoff=decision_cutoff,
        ):
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
                continue
            value = payload.reconstruct(ComputationEvidenceBundleV1)
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=decision_cutoff,
            )
            if (
                value.evidence_id == evidence_id
                and value.input_lock_id == input_lock_id
                and value.component_or_template_ref == component_or_template_ref
            ):
                matches.append(
                    (
                        spine.record_id,
                        value,
                        payload.parent_version_ref_or_explicit_absence,
                    )
                )
        return None if not matches else self._bundle_leaf_ref(tuple(matches))

    @staticmethod
    def _bundle_leaf_ref(
        rows: tuple[tuple[str, ComputationEvidenceBundleV1, str], ...],
    ) -> str:
        by_ref = {record_ref: value for record_ref, value, _ in rows}
        parent_by_ref = {record_ref: parent for record_ref, _, parent in rows}
        if len(by_ref) != len(rows) or len(parent_by_ref) != len(rows):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage repeats an immutable receipt identity",
            )
        missing_parents = {
            parent
            for parent in parent_by_ref.values()
            if parent != "EXPLICIT_ABSENCE" and parent not in by_ref
        }
        if missing_parents:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage has a missing parent receipt",
            )

        children_by_ref: dict[str, list[str]] = {ref: [] for ref in by_ref}
        for child_ref, parent_ref in parent_by_ref.items():
            if parent_ref != "EXPLICIT_ABSENCE":
                children_by_ref[parent_ref].append(child_ref)
        if any(len(children) > 1 for children in children_by_ref.values()):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage is branched",
            )

        for start_ref in by_ref:
            visited: set[str] = set()
            current_ref = start_ref
            while current_ref != "EXPLICIT_ABSENCE":
                if current_ref in visited:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "durable bundle lineage is cyclic",
                    )
                visited.add(current_ref)
                current_ref = parent_by_ref[current_ref]

        roots = tuple(
            ref
            for ref, parent_ref in parent_by_ref.items()
            if parent_ref == "EXPLICIT_ABSENCE"
        )
        leaves = tuple(
            ref for ref, children in children_by_ref.items() if not children
        )
        if len(roots) != 1 or len(leaves) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage is disconnected",
            )

        traversed: set[str] = set()
        current_ref = roots[0]
        previous: ComputationEvidenceBundleV1 | None = None
        while True:
            traversed.add(current_ref)
            current = by_ref[current_ref]
            ComputationEvidenceServiceV1._validate_bundle_transition(
                previous,
                current,
            )
            children = children_by_ref[current_ref]
            if not children:
                break
            previous = current
            current_ref = children[0]
        if traversed != set(by_ref):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable bundle lineage is disconnected",
            )
        return leaves[0]

    @staticmethod
    def _ordered_unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(values))

    @staticmethod
    def _validate_bound_output_value(
        value: object,
        *,
        output_type: str,
    ) -> None:
        def finite_numeric(item: object) -> bool:
            if isinstance(item, bool):
                return False
            if isinstance(item, int):
                return True
            if isinstance(item, float):
                return math.isfinite(item)
            if isinstance(item, str):
                try:
                    return exact_decimal(item, field_name="actual_value").is_finite()
                except ContractValidationError:
                    return False
            return False

        valid = False
        if output_type == "Decimal":
            valid = finite_numeric(value)
        elif output_type == "float64":
            valid = (
                not isinstance(value, bool)
                and isinstance(value, int | float)
                and math.isfinite(float(value))
            )
        elif output_type == "[float64,float64]":
            valid = (
                isinstance(value, list)
                and len(value) == 2
                and all(finite_numeric(item) for item in value)
            )
        elif output_type == "float64 matrix":
            valid = (
                isinstance(value, list)
                and bool(value)
                and all(isinstance(row, list) and bool(row) for row in value)
                and len({len(row) for row in value}) == 1
                and all(finite_numeric(item) for row in value for item in row)
            )
        elif output_type in {
            "typed vector",
            "typed fold registry",
            "typed path registry",
        }:
            valid = isinstance(value, list) and bool(value)
        elif output_type in {
            "typed record",
            "typed statistical result",
            "typed result",
            "typed Decimal record",
            "enum and LCB value",
            "typed multi-metric record",
        }:
            valid = isinstance(value, Mapping) and bool(value)
        if not valid:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable evidence output has the wrong type or a nonfinite value",
            )

    def _validate_computation_evidence_receipt(
        self,
        spine: EconomicReceiptEventSpineV1,
        *,
        binding: EvidenceOutputBindingV1,
        lock: ImmutableReplayPaperInputLockV1,
        component_or_template_ref: str,
        decision_cutoff: datetime,
    ) -> tuple[str, QuantumClassicalNoTradeComparisonV1 | None]:
        if (
            spine.record_type
            is not EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
            or type(spine.typed_payload)
            is not DurableComputationExecutionReceiptRecordV1
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "executed evidence does not resolve to a durable computation receipt",
            )
        payload = spine.typed_payload
        receipt = payload.existing_receipt
        expected_implementation = str(
            lock.implementation_versions.get(binding.math_spec_id, "")
        )
        if (
            payload.record_id != spine.record_id
            or receipt.specification_id != binding.math_spec_id
            or not expected_implementation
            or receipt.implementation_id != expected_implementation
            or payload.input_snapshot_ref != lock.input_lock_id
            or payload.consumer_ref != component_or_template_ref
            or payload.failure_code is not None
            or payload.no_order_authority_flag is not True
            or spine.effective_at > decision_cutoff
            or spine.recorded_at > decision_cutoff
            or payload.output_unit != binding.output_unit
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "durable computation receipt fails its math/lock/scope/version/cutoff join",
            )
        expected_basis = ST12F_METRIC_OUTPUT_BASIS_BY_MATH_ID_V1.get(
            binding.math_spec_id
        )
        if expected_basis is not None and payload.output_basis != expected_basis:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "metric evidence output basis differs from the owner matrix",
            )
        output = safe_json_loads(receipt.output_json)
        if not isinstance(output, Mapping) or binding.output_name not in output:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "durable computation output omits its exact canonical value path",
            )
        actual = output[binding.output_name]
        self._validate_bound_output_value(actual, output_type=binding.output_type)
        comparison: QuantumClassicalNoTradeComparisonV1 | None = None
        if binding.math_spec_id == "MATH-52":
            try:
                comparison = QuantumClassicalNoTradeComparisonV1.from_canonical_mapping(
                    actual
                )
            except (ContractValidationError, TypeError, ValueError) as exc:
                raise ContractValidationError(
                    ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                    "MATH-52 output is not the exact 11-dimensional comparison",
                ) from exc
            if (
                comparison.input_lock_id != lock.input_lock_id
                or len(fields(comparison.comparison_basis)) != 11
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                    "MATH-52 comparison differs from the lock or 11-dimensional basis",
                )
        return receipt.implementation_id, comparison

    def _validate_quantum_evidence_receipt(
        self,
        spine: EconomicReceiptEventSpineV1,
        *,
        math_spec_id: str,
        lock: ImmutableReplayPaperInputLockV1,
        decision_cutoff: datetime,
    ) -> str:
        if (
            type(spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "MATH-50/51 evidence is not a quantum trace-validation receipt",
            )
        value = spine.typed_payload.reconstruct(
            QuantumTraceValidationReceiptV1
        )
        self._validate_receipt_lock_metadata(
            spine,
            decision_cutoff=decision_cutoff,
        )
        implementation = str(lock.implementation_versions.get(math_spec_id, ""))
        if (
            value.math_spec_id != math_spec_id
            or value.input_lock_id != lock.input_lock_id
            or not implementation
            or not set(_source_epoch_refs(lock))
            <= set(value.comparison_basis.version_epoch_pins)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_QUANTUM_TRACE_INVALID,
                "quantum evidence differs from exact math, lock, implementation, or epochs",
            )
        return implementation

    @staticmethod
    def _flatten_dispositions(
        candidate: ComputationEvidenceBundleV1,
    ) -> tuple[EvidenceIdentityDispositionV1, ...]:
        rows = tuple(
            row
            for section_name in _SECTION_FIELDS_V1
            for row in getattr(candidate, section_name).identity_dispositions
        )
        if tuple(row.evidence_identity for row in rows) != ST12F_EVIDENCE_IDENTITIES_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "evidence dispositions differ from exact owner math order",
            )
        return rows

    def _stack_truth(
        self,
        request: BuildEvidenceBundleRequestV1,
        *,
        consumed_refs: set[str],
        component_receipt_refs: Mapping[str, str],
    ) -> tuple[Mapping[str, object], tuple[str, ...]]:
        stack_rows: list[tuple[str, str, object]] = []
        declared_membership = False
        for ref in request.evidence_record_refs:
            if ref in consumed_refs:
                continue
            try:
                spine = self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                continue
            if (
                spine.record_type
                is not EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
                or type(spine.typed_payload)
                is not DurableComputationExecutionReceiptRecordV1
            ):
                continue
            payload = spine.typed_payload
            output = safe_json_loads(payload.existing_receipt.output_json)
            if not isinstance(output, Mapping):
                continue
            declared = output.get("stack_id")
            if payload.existing_receipt.specification_id.startswith("STACK::"):
                if not isinstance(declared, str) or not declared:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack receipt output omits stack_id",
                    )
                stack = REGISTERED_FORMULA_STACKS.get(declared)
                component_outputs = output.get("component_outputs")
                expected_stack_fields = {
                    field.name for field in fields(StackResultV1)
                }
                if (
                    stack is None
                    or set(output) != expected_stack_fields
                    or payload.existing_receipt.specification_id
                    != f"STACK::{declared}"
                    or payload.input_snapshot_ref != request.input_lock_id
                    or payload.consumer_ref != request.component_id
                    or not isinstance(component_outputs, list)
                    or output.get("no_authority_flag") is not True
                    or output.get("terminal_route")
                    != "DETERMINISTIC_DEPENDENCY_CLOSED_STACK_RESULT"
                    or not isinstance(output.get("result_id"), str)
                    or not output["result_id"]
                    or not isinstance(output.get("evidence_refs"), list)
                    or not isinstance(output.get("conversion_receipt_refs"), list)
                ):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack receipt differs from the exact StackResultV1 contract",
                    )
                if tuple(output["evidence_refs"]) != payload.dependency_receipt_refs:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack result evidence refs differ from durable dependencies",
                    )
                ordered_component_refs: list[str] = []
                ordered_math_ids: list[str] = []
                expected_component_fields = {
                    field.name for field in fields(FrozenFormulaOutputV1)
                }
                for component_output in component_outputs:
                    if not isinstance(component_output, Mapping):
                        raise ContractValidationError(
                            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                            "stack component output is not a canonical mapping",
                        )
                    refs = component_output.get("receipt_refs")
                    math_spec_id = component_output.get("math_spec_id")
                    implementation_id = component_output.get("implementation_id")
                    dependency_payload: object | None = None
                    if isinstance(refs, list) and len(refs) == 1:
                        try:
                            dependency_spine = self._spine_as_of(
                                str(refs[0]),
                                effective_cutoff=request.requested_at,
                                recorded_cutoff=request.requested_at,
                            )
                        except PersistenceContractError:
                            dependency_spine = None
                        if (
                            dependency_spine is not None
                            and dependency_spine.record_type
                            is EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT
                            and type(dependency_spine.typed_payload)
                            is DurableComputationExecutionReceiptRecordV1
                        ):
                            dependency_payload = dependency_spine.typed_payload
                    if (
                        set(component_output) != expected_component_fields
                        or not isinstance(refs, list)
                        or len(refs) != 1
                        or component_output.get("no_authority_flag") is not True
                        or not isinstance(math_spec_id, str)
                        or math_spec_id not in component_receipt_refs
                        or refs[0] != component_receipt_refs[math_spec_id]
                        or type(dependency_payload)
                        is not DurableComputationExecutionReceiptRecordV1
                        or dependency_payload.existing_receipt.specification_id
                        != math_spec_id
                        or implementation_id
                        != dependency_payload.existing_receipt.implementation_id
                    ):
                        raise ContractValidationError(
                            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                            "stack component output differs from exact durable custody",
                        )
                    ordered_math_ids.append(math_spec_id)
                    ordered_component_refs.append(str(refs[0]))
                if (
                    tuple(ordered_math_ids) != stack.component_ids
                    or tuple(ordered_component_refs)
                    != payload.dependency_receipt_refs
                ):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack component and dependency order differs from registry",
                    )
                if not set(ordered_component_refs) <= set(component_receipt_refs.values()):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "stack dependency refs are not consumed component receipts",
                    )
                stack_rows.append((declared, ref, stack.stack_version))
                consumed_refs.add(ref)
            elif isinstance(declared, str) and declared in REGISTERED_FORMULA_STACKS:
                declared_membership = True
        if declared_membership and not stack_rows:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "component receipt declares stack membership without stack custody",
            )
        if len({row[0] for row in stack_rows}) != len(stack_rows):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "duplicate durable stack receipts were consumed",
            )
        ordered = tuple(sorted(stack_rows, key=lambda row: row[0]))
        return (
            MappingProxyType({stack_id: version for stack_id, _, version in ordered}),
            tuple(ref for _, ref, _ in ordered),
        )

    def _find_control_in_request(
        self,
        request: BuildEvidenceBundleRequestV1,
        receipt_class: ST12FReceiptClassV1,
        expected_type: type[object],
    ) -> tuple[object | None, str | None]:
        matches: list[tuple[object, str]] = []
        for ref in request.evidence_record_refs:
            try:
                spine = self._spine_as_of(
                    ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                continue
            if (
                type(spine) is EconomicReceiptEventSpineV1
                and type(spine.typed_payload) is ST12FEvidenceControlReceiptRecordV1
                and spine.typed_payload.receipt_class is receipt_class
            ):
                value = spine.typed_payload.reconstruct(expected_type)
                self._validate_receipt_lock_metadata(
                    spine,
                    decision_cutoff=request.requested_at,
                )
                self._validate_contract_visibility(
                    value,
                    evaluation_time=request.requested_at,
                )
                matches.append((value, ref))
        if len(matches) > 1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "OP15 evidence roster contains duplicate control classes",
            )
        return (None, None) if not matches else matches[0]

    def _find_review_for_request(
        self,
        request: BuildEvidenceBundleRequestV1,
    ) -> tuple[IndependentReviewRecordV1 | None, str | None]:
        durable, receipt_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
            IndependentReviewRecordV1,
        )
        if durable is not None:
            assert type(durable) is IndependentReviewRecordV1
            return durable, receipt_ref
        return None, None

    def _admit_bundle_evidence(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
        replay: ReplayResultContractV1 | None,
        paper: PaperResultContractV1 | None,
    ) -> _EvidenceAdmissionResultV1:
        dispositions = self._flatten_dispositions(candidate)
        consumed: set[str] = set()
        lock_ref = f"ST12F-RECEIPT::{lock.input_lock_id}::INPUT_LOCK"
        lane_refs = candidate.lane_execution_receipt_refs
        for ref in (lock_ref, *lane_refs):
            self._spine_as_of(
                ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
            consumed.add(ref)

        component_versions: dict[str, object] = {}
        component_receipt_refs: dict[str, str] = {}
        math_refs: list[str] = []
        quantum_refs: dict[str, str] = {}
        math52_ref: str | None = None
        static_refs: list[str] = []
        disposition_negative: list[str] = []
        actual_metric_ids: list[str] = []
        executed_identity_ids: list[str] = []
        static_identity_ids: list[str] = []
        for disposition in dispositions:
            math_spec_id = disposition.evidence_identity
            binding = _EVIDENCE_OUTPUT_BINDING_BY_MATH_ID_V1[math_spec_id]
            if (
                disposition.disposition
                is EvidenceIdentityDispositionStateV1.APPLICABLE_BLOCKED_WITH_TYPED_REASON
            ):
                disposition_negative.extend(
                    f"DISPOSITION::{math_spec_id}::{code.value}"
                    for code in disposition.blocker_codes
                )
                continue
            if (
                disposition.disposition
                is EvidenceIdentityDispositionStateV1.NOT_APPLICABLE_WITH_PROOF
            ):
                if not binding.static_not_applicable_allowed:
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                        "metric evidence cannot be replaced by static N/A proof",
                    )
                proof = StaticEvidenceApplicabilityProofV1.for_scope(
                    math_spec_id=math_spec_id,
                    component_or_template_ref=candidate.component_or_template_ref,
                    input_lock_id=lock.input_lock_id,
                )
                if disposition.proof_refs != (proof.proof_id,):
                    raise ContractValidationError(
                        ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                        "static N/A reference does not reconstruct to the exact proof",
                    )
                static_refs.append(proof.proof_id)
                static_identity_ids.append(math_spec_id)
                consumed.add(proof.proof_id)
                continue

            ref = disposition.evidence_record_refs[0]
            if ref not in request.evidence_record_refs:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "executed disposition receipt is absent from the OP15 roster",
                )
            spine = self._spine_as_of(
                ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
            if math_spec_id in {"MATH-50", "MATH-51"}:
                implementation = self._validate_quantum_evidence_receipt(
                    spine,
                    math_spec_id=math_spec_id,
                    lock=lock,
                    decision_cutoff=request.requested_at,
                )
                quantum_refs[math_spec_id] = ref
            else:
                implementation, _comparison = (
                    self._validate_computation_evidence_receipt(
                        spine,
                        binding=binding,
                        lock=lock,
                        component_or_template_ref=(
                            candidate.component_or_template_ref
                        ),
                        decision_cutoff=request.requested_at,
                    )
                )
                if math_spec_id == "MATH-52":
                    math52_ref = ref
                else:
                    math_refs.append(ref)
            component_versions[math_spec_id] = implementation
            component_receipt_refs[math_spec_id] = ref
            executed_identity_ids.append(math_spec_id)
            consumed.add(ref)
            if binding.metric_id != "EXPLICIT_ABSENCE":
                actual_metric_ids.append(binding.metric_id)

        complete_states = {
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
            EvidenceBundleTerminalStateV1.STALE,
            EvidenceBundleTerminalStateV1.SUPERSEDED,
        }
        expected_metric_ids = tuple(
            row.metric_id for row in ST12F_EVIDENCE_METRIC_DEFINITIONS_V1
        )
        required_closure = set(
            _required_evidence_identity_closure_v1(
                candidate.component_or_template_ref
            )
        )
        expected_static_identity_ids = tuple(
            identity
            for identity in ST12F_STATIC_NOT_APPLICABLE_MATH_IDS_V1
            if identity not in required_closure
        )
        expected_executed_identity_ids = tuple(
            identity
            for identity in ST12F_EVIDENCE_IDENTITIES_V1
            if identity not in expected_static_identity_ids
        )
        if (
            candidate.terminal_state in complete_states
            and tuple(actual_metric_ids) != expected_metric_ids
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "complete bundle lacks all 38 ordered actual metric values",
            )
        if candidate.terminal_state in complete_states and (
            tuple(executed_identity_ids) != expected_executed_identity_ids
            or tuple(static_identity_ids) != expected_static_identity_ids
            or len(executed_identity_ids) + len(static_identity_ids) != 48
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "complete bundle partition differs from the selected component dependency closure",
            )

        divergence, divergence_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT,
            DivergenceAssessmentV1,
        )
        model_risk, model_risk_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT,
            ModelRiskEvidenceAssessmentV1,
        )
        annotation, annotation_ref = self._find_control_in_request(
            request,
            ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION,
            DeterministicEvidenceAnnotationContractV1,
        )
        review, review_ref = self._find_review_for_request(request)
        for ref in (divergence_ref, model_risk_ref, annotation_ref, review_ref):
            if ref is not None:
                consumed.add(ref)

        stack_versions, stack_refs = self._stack_truth(
            request,
            consumed_refs=consumed,
            component_receipt_refs=component_receipt_refs,
        )
        stale_or_supersession_refs: list[str] = []
        for ref in request.evidence_record_refs:
            if ref in consumed:
                continue
            if candidate.terminal_state not in {
                EvidenceBundleTerminalStateV1.STALE,
                EvidenceBundleTerminalStateV1.SUPERSEDED,
            }:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "OP15 roster contains an unconsumed evidence reference",
                )
            spine = self._spine_as_of(
                ref,
                effective_cutoff=request.requested_at,
                recorded_cutoff=request.requested_at,
            )
            if (
                type(spine.typed_payload)
                is not ST12FEvidenceControlReceiptRecordV1
                or spine.typed_payload.receipt_class
                not in {
                    ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION,
                    ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION,
                    ST12FReceiptClassV1.D_EVIDENCE_REFERENCE,
                }
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "STALE/SUPERSEDED proof reference is not durable custody",
                )
            stale_or_supersession_refs.append(ref)
            consumed.add(ref)

        provenance = self._ordered_unique(
            [
                lock_ref,
                *lane_refs,
                *math_refs,
                *stack_refs,
                *(() if divergence_ref is None else (divergence_ref,)),
                *(() if model_risk_ref is None else (model_risk_ref,)),
                *(() if "MATH-50" not in quantum_refs else (quantum_refs["MATH-50"],)),
                *(() if "MATH-51" not in quantum_refs else (quantum_refs["MATH-51"],)),
                *(() if math52_ref is None else (math52_ref,)),
                *(() if annotation_ref is None else (annotation_ref,)),
                *(() if review_ref is None else (review_ref,)),
                *stale_or_supersession_refs,
                *static_refs,
            ]
        )
        if (
            len(request.evidence_record_refs) != len(provenance)
            or set(request.evidence_record_refs) != set(provenance)
        ):
            raise ContractValidationError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "OP15 evidence roster differs from the exact consumed-reference union",
            )

        negative: list[str] = []
        if replay is not None:
            negative.extend(
                f"REPLAY_FAILURE::{value}" for value in replay.failure_states
            )
        if paper is not None:
            negative.extend(
                f"PAPER_FAILURE::{value}" for value in paper.failure_states
            )
        if type(divergence) is DivergenceAssessmentV1:
            negative.extend(
                f"DIVERGENCE::{code.value}" for code in divergence.typed_blockers
            )
        negative.extend(disposition_negative)
        if type(model_risk) is ModelRiskEvidenceAssessmentV1:
            review_validated = (
                type(review) is IndependentReviewRecordV1
                and review.decision is IndependentReviewDecisionV1.VALIDATED
            )
            negative.extend(
                f"NO_TRADE::{row.condition_id}"
                for row in model_risk.no_trade_condition_outcomes
                if row.active
                and not (
                    row.condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
                    and review_validated
                )
            )
            negative.extend(
                f"MODEL_RISK::{row.control_id}"
                for row in model_risk.control_evidence
                if row.state
                is ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON
            )
        if type(review) is IndependentReviewRecordV1:
            negative.extend(
                f"REVIEW::{code.value}" for code in review.blocker_codes
            )
        negative.extend(
            f"LIFECYCLE::{code.value}" for code in candidate.blocker_codes
        )
        exact_negative = self._ordered_unique(negative)
        if (
            dict(candidate.actual_executed_component_versions)
            != component_versions
            or dict(candidate.actual_executed_stack_versions)
            != dict(stack_versions)
            or candidate.source_and_provenance_refs != provenance
            or candidate.failure_and_negative_evidence_states != exact_negative
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "caller bundle truth fields differ from durable canonical reconstruction",
            )
        return _EvidenceAdmissionResultV1(
            component_versions=MappingProxyType(component_versions),
            stack_versions=stack_versions,
            provenance_refs=provenance,
            negative_states=exact_negative,
            divergence=(
                divergence if type(divergence) is DivergenceAssessmentV1 else None
            ),
            model_risk=(
                model_risk
                if type(model_risk) is ModelRiskEvidenceAssessmentV1
                else None
            ),
            review=(review if type(review) is IndependentReviewRecordV1 else None),
        )

    @staticmethod
    def _validate_bundle_transition(
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
    ) -> None:
        state = candidate.terminal_state
        if candidate.independent_review_state != state.value:
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "bundle review state differs from its immutable terminal state",
            )
        if previous is None:
            if state not in _EVIDENCE_BUNDLE_INITIAL_STATES_V1:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    "bundle lifecycle root is not owner-certified",
                )
            return
        if (
            candidate.evidence_id != previous.evidence_id
            or candidate.input_lock_id != previous.input_lock_id
            or candidate.component_or_template_ref
            != previous.component_or_template_ref
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "bundle lifecycle transition changes its exact three-part identity",
            )
        if (
            candidate.evidence_bundle_version == previous.evidence_bundle_version
            or (previous.terminal_state, state)
            not in _EVIDENCE_BUNDLE_TRANSITION_GUARDS_V1
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "bundle lifecycle transition or immutable version identity is invalid",
            )

    @staticmethod
    def _validate_bundle_lanes(
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
        replay: ReplayResultContractV1 | None,
        paper: PaperResultContractV1 | None,
    ) -> None:
        state = candidate.terminal_state
        if (replay is None) != (state is EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "missing REPLAY evidence requires its exact immutable incomplete state",
            )
        if (paper is None) != (state is EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "missing PAPER evidence requires its exact immutable incomplete state",
            )
        present = tuple(row for row in (replay, paper) if row is not None)
        if any(
            row.fixture_only_not_evidence
            or row.input_lock_id != lock.input_lock_id
            or row.cohort_template_id != candidate.component_or_template_ref
            for row in present
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
                "bundle lanes must be real evidence under one exact lock and template",
            )
        expected_receipts = tuple(
            f"ST12F-RECEIPT::{row.result_id}::{('REPLAY' if type(row) is ReplayResultContractV1 else 'PAPER')}_REGISTRATION"
            for row in present
        )
        if candidate.lane_execution_receipt_refs != expected_receipts:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "bundle lane receipt references are not the exact committed spine IDs",
            )
        if state in {
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
            EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.STALE,
        } and not candidate.blocker_codes:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "incomplete, rejected, or stale bundle requires typed blockers",
            )

    @staticmethod
    def _validate_bundle_divergence(
        candidate: ComputationEvidenceBundleV1,
        divergence: object | None,
    ) -> None:
        state = candidate.terminal_state
        missing_lane = state in {
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_REPLAY,
            EvidenceBundleTerminalStateV1.INCOMPLETE_MISSING_PAPER,
        }
        if missing_lane:
            valid = (
                candidate.divergence_assessment_ref == "EXPLICIT_ABSENCE"
                and divergence is None
            )
        else:
            expected_terminal = (
                DivergenceTerminalStateV1.INCOMPARABLE_MISSING_OR_CONFLICTING_EVIDENCE
                if state is EvidenceBundleTerminalStateV1.INCOMPLETE_CONFLICT
                else DivergenceTerminalStateV1.CONSISTENT_WITHIN_LOCKED_THRESHOLDS
            )
            valid = (
                type(divergence) is DivergenceAssessmentV1
                and candidate.divergence_assessment_ref
                == divergence.assessment_id
                and candidate.replay_result_ref == divergence.replay_result_ref
                and candidate.paper_result_ref == divergence.paper_result_ref
                and divergence.terminal_state is expected_terminal
            )
        if not valid:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "bundle lifecycle state lacks its exact dual-lane divergence proof",
            )

    def _validate_bundle_model_risk(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        previous_ref: str | None,
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
        model_risk: ModelRiskEvidenceAssessmentV1 | None,
        review: IndependentReviewRecordV1 | None,
    ) -> None:
        if candidate.terminal_state not in {
            EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW,
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        }:
            return
        if type(model_risk) is not ModelRiskEvidenceAssessmentV1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "READY/CLOSED bundle requires a typed model-risk assessment",
            )
        comparison = model_risk.permanent_no_trade_comparison
        non_review_veto = any(
            row.active and row.condition_id != "INDEPENDENT_REVIEW_NOT_CLOSED"
            for row in model_risk.no_trade_condition_outcomes
        )
        controls_pass = all(
            row.state is not ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON
            and row.current
            for row in model_risk.control_evidence
        )
        basis = model_risk.adjudication_basis
        lane_values = tuple(
            row for row in (basis.replay_lane, basis.paper_lane) if row is not None
        )
        if (
            model_risk.input_lock_id != candidate.input_lock_id
            or basis.expected_component_or_template_ref
            != candidate.component_or_template_ref
            or len(lane_values) != 2
            or any(
                row.input_lock_id != candidate.input_lock_id
                or row.component_or_template_ref
                != candidate.component_or_template_ref
                or not row.observed_at
                <= request.requested_at
                <= row.valid_until
                for row in lane_values
            )
            or not basis.evaluated_at
            <= request.requested_at
            <= basis.required_evidence_valid_until
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "model-risk assessment differs from the bundle lock/scope/cutoff join",
            )
        if (
            non_review_veto
            or not controls_pass
            or comparison.execution_adjusted_lcb <= 0
            or comparison.candidate_utility <= comparison.strongest_classical_utility
            or comparison.candidate_utility <= comparison.no_trade_utility
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "READY/CLOSED bundle has an unresolved deterministic hard veto",
            )
        review_condition = next(
            row
            for row in model_risk.no_trade_condition_outcomes
            if row.condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
        )
        if (
            candidate.terminal_state
            is EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
        ):
            if (
                not review_condition.active
                or review is not None
                or model_risk.terminal_state != "READY_FOR_INDEPENDENT_REVIEW"
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_MODEL_RISK_VETO,
                    "READY model risk must preserve only the review-pending condition",
                )
            return
        if candidate.terminal_state is EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED:
            if (
                type(review) is not IndependentReviewRecordV1
                or review.decision is not IndependentReviewDecisionV1.REJECTED
                or not review_condition.active
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_MODEL_RISK_VETO,
                    "rejected bundle requires the pre-existing rejected review join",
                )
            return
        review_ref = (
            None
            if review is None
            else f"ST12F-RECEIPT::{review.review_id}::INDEPENDENT_REVIEW_VERSION"
        )
        model_risk_ref = (
            f"ST12F-RECEIPT::{model_risk.assessment_id}::MODEL_RISK_ASSESSMENT"
        )
        if (
            type(review) is not IndependentReviewRecordV1
            or review.decision is not IndependentReviewDecisionV1.VALIDATED
            or previous_ref is None
            or previous is None
            or previous.terminal_state
            is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            or review.prior_bundle_ref != previous_ref
            or review.evidence_bundle_version != candidate.evidence_bundle_version
            or review_ref is None
            or basis.independent_review_receipt_ref != review_ref
            or review_condition.active
            or any(row.active for row in model_risk.no_trade_condition_outcomes)
            or model_risk.terminal_state != "CLOSED_INDEPENDENTLY_VALIDATED"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "closed model risk lacks exact parent/candidate/review reconciliation",
            )
        model_risk_spine = self._spine_as_of(
            model_risk_ref,
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        review_spine = self._spine_as_of(
            review_ref,
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        if (
            type(model_risk_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or model_risk_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT
            or model_risk_spine.typed_payload.operation_id
            != "ST12F-PRIVATE::REGISTER_CONTROL"
            or model_risk_spine.implementation_owner
            != "ComputationEvidenceServiceV1"
            or type(review_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or review_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION
            or not review_spine.recorded_at
            <= model_risk_spine.recorded_at
            <= request.requested_at
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "model-risk and review receipts do not preserve pre-existing segregated custody",
            )
        model_risk.assert_independent_review_join(
            assessment_receipt_ref=model_risk_ref,
            parent_ready_bundle_ref=previous_ref,
            reviewed_parent_bundle_ref=review.prior_bundle_ref,
            candidate_bundle_version=candidate.evidence_bundle_version,
            reviewed_candidate_bundle_version=review.evidence_bundle_version,
            review_receipt_ref=review_ref,
            reviewer_authority_receipt_ref=review.authority_receipt_ref,
            input_lock_id=lock.input_lock_id,
            component_or_template_ref=candidate.component_or_template_ref,
            source_epoch_refs=model_risk_spine.typed_payload.source_epoch_refs,
            reviewed_source_epoch_refs=review.reviewed_source_epoch_refs,
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
            review_recorded_at=review_spine.recorded_at,
        )

    def _validate_bundle_review(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        lock: ImmutableReplayPaperInputLockV1,
        previous_ref: str | None,
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
        review: object | None,
    ) -> None:
        state = candidate.terminal_state
        if state not in {
            EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED,
            EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED,
        }:
            if state is EvidenceBundleTerminalStateV1.SUPERSEDED:
                return
            if review is not None:
                raise ContractValidationError(
                    ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                    "non-review lifecycle state cannot consume a review decision",
                )
            return
        expected_decision = (
            IndependentReviewDecisionV1.REJECTED
            if state is EvidenceBundleTerminalStateV1.INDEPENDENT_REVIEW_REJECTED
            else IndependentReviewDecisionV1.VALIDATED
        )
        review_spine: EconomicReceiptEventSpineV1 | None = None
        if type(review) is IndependentReviewRecordV1:
            review_ref = (
                f"ST12F-RECEIPT::{review.review_id}::INDEPENDENT_REVIEW_VERSION"
            )
            try:
                review_spine = self._spine_as_of(
                    review_ref,
                    effective_cutoff=request.requested_at,
                    recorded_cutoff=request.requested_at,
                )
            except PersistenceContractError:
                review_spine = None
        if (
            type(review) is not IndependentReviewRecordV1
            or type(review_spine) is not EconomicReceiptEventSpineV1
            or type(review_spine.typed_payload)
            is not ST12FEvidenceControlReceiptRecordV1
            or review_spine.typed_payload.receipt_class
            is not ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION
            or review_spine.typed_payload.operation_id
            != "ST12F-PRIVATE::INDEPENDENT_REVIEW"
            or review_spine.implementation_owner != "IndependentEvidenceReviewV1"
            or review_spine.typed_payload.request_id == request.request_id
            or previous_ref is None
            or previous is None
            or previous.terminal_state is not EvidenceBundleTerminalStateV1.READY_FOR_INDEPENDENT_REVIEW
            or review.prior_bundle_ref != previous_ref
            or review.evidence_id != candidate.evidence_id
            or review.evidence_bundle_version != candidate.evidence_bundle_version
            or review.input_lock_id != lock.input_lock_id
            or review.bundle_producer_identity != self._producer_identity
            or review.reviewer_identity == self._producer_identity
            or review.decision is not expected_decision
            or review.reviewed_source_epoch_refs != _source_epoch_refs(lock)
            or not review.reviewed_at <= request.requested_at <= review.valid_until
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review does not bind the exact prior/candidate/version/lock/epoch custody",
            )

    def _validate_bundle_transition_guard(
        self,
        *,
        request: BuildEvidenceBundleRequestV1,
        previous_ref: str | None,
        previous: ComputationEvidenceBundleV1 | None,
        candidate: ComputationEvidenceBundleV1,
        lock: ImmutableReplayPaperInputLockV1,
    ) -> None:
        state = candidate.terminal_state
        if state is EvidenceBundleTerminalStateV1.STALE:
            prior_reference = (
                None
                if previous is None
                else previous.d_evidence_reference_projection
            )
            if (
                previous_ref is None
                or previous is None
                or type(prior_reference) is not ST12FEvidenceReferenceV1
                or prior_reference.evidence_ref != previous_ref
                or prior_reference.evidence_state
                is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            ):
                raise ContractValidationError(
                    ReasonCode.ST12F_BUNDLE_STALE,
                    "CLOSED to STALE requires an exact prior closed D reference",
                )
            current = self._cohort_resolver.canonical_snapshot
            context_fields = (
                "market_scope",
                "venue_scope",
                "instrument_scope",
                "data_semantics_version",
                "venue_semantics_version",
                "accounting_definition",
                "fee_assumptions",
                "spread_assumptions",
                "slippage_assumptions",
                "fill_and_queue_assumptions",
                "latency_and_staleness_assumptions",
                "capacity_and_crowding_assumptions",
                "portfolio_and_cash_context",
                "resampling_policy",
                "scenario_set_id",
            )
            stale_triggers = (
                prior_reference.valid_until < request.requested_at,
                dict(current.source_epochs) != dict(lock.source_epochs),
                current.parameter_policy_version != lock.parameter_policy_version
                or current.parameter_value_refs != lock.parameter_value_refs,
                dict(current.formula_specification_versions)
                != dict(lock.formula_specification_versions)
                or dict(current.implementation_versions)
                != dict(lock.implementation_versions),
                any(
                    getattr(current, name) != getattr(lock, name)
                    for name in context_fields
                ),
            )
            if not any(stale_triggers):
                raise ContractValidationError(
                    ReasonCode.ST12F_BUNDLE_STALE,
                    "CLOSED to STALE requires a mechanically proven TTL, source-epoch, parameter, implementation, or context change",
                )
            return
        if state is not EvidenceBundleTerminalStateV1.SUPERSEDED:
            return
        if previous_ref is None or previous is None:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "CLOSED to SUPERSEDED requires a durable closed predecessor",
            )

        durable_spines = self._durable_receipt_spines(
            effective_cutoff=request.requested_at,
            recorded_cutoff=request.requested_at,
        )
        spines_by_ref = {spine.record_id: spine for spine in durable_spines}
        prior_spine = spines_by_ref.get(previous_ref)
        if prior_spine is None:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "CLOSED to SUPERSEDED predecessor receipt is not durable",
            )

        for spine in durable_spines:
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if (
                payload.receipt_class
                is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION
                or spine.record_id == previous_ref
                or spine.record_id not in request.evidence_record_refs
                or not prior_spine.recorded_at
                < spine.recorded_at
                <= request.requested_at
            ):
                continue
            newer = payload.reconstruct(ComputationEvidenceBundleV1)
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=request.requested_at,
            )
            if (
                newer.terminal_state
                is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
                or newer.evidence_id != previous.evidence_id
                or newer.component_or_template_ref
                != previous.component_or_template_ref
                or newer.input_lock_id == previous.input_lock_id
            ):
                continue
            newer_lock = self._cohort_resolver.resolve_input_lock(
                newer.input_lock_id,
                decision_cutoff=request.requested_at,
            )
            reference = newer.d_evidence_reference_projection
            if (
                type(reference) is not ST12FEvidenceReferenceV1
                or reference.evidence_state
                is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
                or reference.evidence_ref != spine.record_id
                or reference.evidence_id != newer.evidence_id
                or reference.component_or_template_ref
                != newer.component_or_template_ref
                or reference.input_lock_id != newer.input_lock_id
                or reference.evidence_bundle_version
                != newer.evidence_bundle_version
                or reference.source_epoch_refs != _source_epoch_refs(newer_lock)
                or not reference.observed_at
                <= request.requested_at
                <= reference.valid_until
                or self._durable_current_bundle_ref(
                    newer.evidence_id,
                    newer.input_lock_id,
                    newer.component_or_template_ref,
                    decision_cutoff=request.requested_at,
                )
                != spine.record_id
            ):
                continue
            reference_receipt_ref = (
                f"ST12F-RECEIPT::{reference.reference_id}::D_EVIDENCE_REFERENCE"
            )
            reference_spine = spines_by_ref.get(reference_receipt_ref)
            if (
                reference_spine is None
                or reference_receipt_ref not in request.evidence_record_refs
                or type(reference_spine.typed_payload)
                is not ST12FEvidenceControlReceiptRecordV1
                or reference_spine.typed_payload.receipt_class
                is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE
                or reference_spine.typed_payload.reconstruct(
                    ST12FEvidenceReferenceV1
                )
                != reference
            ):
                continue
            independently_reviewed = False
            for review_spine in durable_spines:
                review_payload = review_spine.typed_payload
                assert type(review_payload) is ST12FEvidenceControlReceiptRecordV1
                if (
                    review_payload.receipt_class
                    is not ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION
                    or review_spine.record_id not in request.evidence_record_refs
                    or review_payload.operation_id
                    != "ST12F-PRIVATE::INDEPENDENT_REVIEW"
                    or review_spine.implementation_owner
                    != "IndependentEvidenceReviewV1"
                ):
                    continue
                review = review_payload.reconstruct(IndependentReviewRecordV1)
                if (
                    review.prior_bundle_ref
                    == payload.parent_version_ref_or_explicit_absence
                    and review.evidence_id == newer.evidence_id
                    and review.evidence_bundle_version
                    == newer.evidence_bundle_version
                    and review.input_lock_id == newer.input_lock_id
                    and review.decision is IndependentReviewDecisionV1.VALIDATED
                    and review.bundle_producer_identity == self._producer_identity
                    and review.reviewer_identity != self._producer_identity
                    and review.reviewed_source_epoch_refs
                    == reference.source_epoch_refs
                    and review.reviewed_at
                    <= request.requested_at
                    <= review.valid_until
                    and review_payload.request_id != request.request_id
                ):
                    independently_reviewed = True
                    break
            if independently_reviewed:
                return
        raise ContractValidationError(
            ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
            "CLOSED to SUPERSEDED requires a referenced, newer, current, valid, independently reviewed closed bundle",
        )

    @staticmethod
    def _validate_closed_projections(
        candidate: ComputationEvidenceBundleV1,
        *,
        bundle_record_ref: str,
        lock: ImmutableReplayPaperInputLockV1,
    ) -> None:
        if candidate.terminal_state is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED:
            return
        reference = candidate.d_evidence_reference_projection
        handoff = candidate.g_handoff_projection
        if (
            type(reference) is not ST12FEvidenceReferenceV1
            or type(handoff) is not FToGHandoffReferencesV1
            or reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or reference.evidence_id != candidate.evidence_id
            or reference.evidence_ref != bundle_record_ref
            or reference.evidence_bundle_version != candidate.evidence_bundle_version
            or reference.component_or_template_ref != candidate.component_or_template_ref
            or reference.input_lock_id != lock.input_lock_id
            or reference.source_epoch_refs != _source_epoch_refs(lock)
            or reference.lane != "REPLAY_PAPER"
            or reference.terminal_state != candidate.terminal_state.value
            or reference.no_effect_flags != NO_EFFECTS_V1
            or handoff.evidence_bundle_ref != bundle_record_ref
            or handoff.input_lock_id != lock.input_lock_id
            or handoff.source_epoch_refs != _source_epoch_refs(lock)
            or handoff.terminal_state != candidate.terminal_state.value
            or not handoff.read_only
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "closed bundle D/G projections differ from canonical custody",
            )

    def receipt_exists(
        self,
        receipt_ref: str,
        *,
        evaluated_at: datetime,
    ) -> bool:
        cutoff = parse_utc(evaluated_at, field_name="evaluated_at")
        try:
            matches = tuple(
                row
                for row in self._records_as_of(
                    effective_cutoff=cutoff,
                    recorded_cutoff=cutoff,
                )
                if getattr(row, "record_id", None) == receipt_ref
            )
        except PersistenceContractError:
            return False
        return len(matches) == 1

    def resolve_numeric_evidence(
        self,
        *,
        numeric_fact_id: str,
        evidence_ref: str,
        evaluated_at: datetime,
    ) -> CanonicalNumericEvidenceValueV1:
        cutoff = parse_utc(evaluated_at, field_name="evaluated_at")
        durable_spines = self._durable_receipt_spines(
            effective_cutoff=cutoff,
            recorded_cutoff=cutoff,
        )
        matches: list[
            tuple[
                EconomicReceiptEventSpineV1,
                DeterministicEvidenceAnnotationContractV1,
                CanonicalNumericEvidenceValueV1,
            ]
        ] = []
        for spine in durable_spines:
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if (
                payload.receipt_class
                is not ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION
            ):
                continue
            annotation = payload.reconstruct(
                DeterministicEvidenceAnnotationContractV1
            )
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=cutoff,
            )
            self._validate_contract_visibility(
                annotation,
                evaluation_time=cutoff,
            )
            for value in annotation.canonical_numeric_evidence:
                if (
                    value.numeric_fact_id == numeric_fact_id
                    and value.evidence_ref == evidence_ref
                ):
                    matches.append((spine, annotation, value))
        if not matches:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact is absent from canonical annotation custody at the explicit cutoff",
            )
        canonical_values = {
            deterministic_json(value) for _, _, value in matches
        }
        if len(canonical_values) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact has conflicting canonical annotation custody",
            )
        annotation_spine, annotation, value = max(
            matches,
            key=lambda row: (
                row[0].recorded_at,
                row[0].effective_at,
                row[0].record_id,
            ),
        )
        d_matches: list[
            tuple[EconomicReceiptEventSpineV1, ST12FEvidenceReferenceV1]
        ] = []
        for spine in durable_spines:
            payload = spine.typed_payload
            assert type(payload) is ST12FEvidenceControlReceiptRecordV1
            if payload.receipt_class is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
                continue
            reference = payload.reconstruct(ST12FEvidenceReferenceV1)
            if reference.evidence_ref != evidence_ref:
                continue
            self._validate_receipt_lock_metadata(
                spine,
                decision_cutoff=cutoff,
            )
            self._validate_contract_visibility(
                reference,
                evaluation_time=cutoff,
            )
            d_matches.append((spine, reference))
        if len(d_matches) != 1:
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact requires one exact visible D evidence reference",
            )
        d_spine, reference = d_matches[0]
        bundle = self.resolve_bundle(
            evidence_ref,
            decision_cutoff=cutoff,
        )
        current_ref = self._durable_current_bundle_ref(
            bundle.evidence_id,
            bundle.input_lock_id,
            bundle.component_or_template_ref,
            decision_cutoff=cutoff,
        )
        if (
            value.evidence_bundle_ref != evidence_ref
            or evidence_ref not in annotation.evidence_bundle_refs
            or bundle.terminal_state
            is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
            or bundle.d_evidence_reference_projection != reference
            or current_ref != evidence_ref
            or reference.evidence_state
            is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or value.input_lock_id != bundle.input_lock_id
            or value.input_lock_id != annotation.input_lock_id
            or value.source_epoch_refs != reference.source_epoch_refs
            or value.source_epoch_refs != annotation.source_epoch_refs
            or not value.observed_at <= cutoff <= value.valid_until
            or value.evidence_receipt_ref != d_spine.record_id
            or value.numeric_recheck_receipt_ref != annotation_spine.record_id
            or not self.receipt_exists(
                value.evidence_receipt_ref,
                evaluated_at=cutoff,
            )
            or not self.receipt_exists(
                value.numeric_recheck_receipt_ref,
                evaluated_at=cutoff,
            )
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_LLM_ANNOTATION_INVALID,
                "numeric fact differs from current canonical bundle, D, lock, epoch, or recheck custody",
            )
        return value

    def read_evidence_reference(
        self,
        context: object,
        *,
        causation_id: str,
        correlation_id: str,
        query: FToDEvidenceReferenceQueryV1 | None = None,
    ) -> ST12FEvidenceReferenceV1:
        observed = parse_utc(getattr(context, "as_of"), field_name="as_of")

        def unavailable() -> ST12FEvidenceReferenceV1:
            return ST12FEvidenceReferenceV1(
                evidence_state=ST12FEvidenceStateV1.EVIDENCE_INSUFFICIENT_FAIL_CLOSED,
                evidence_ref="EXPLICIT_ABSENCE",
                lane="REPLAY_PAPER",
                dataset_grade_ref="EXPLICIT_ABSENCE",
                venue_semantic_binding_ref="EXPLICIT_ABSENCE",
                cross_venue_equivalence_ref="EXPLICIT_ABSENCE",
                observed_at=observed,
                valid_until=observed,
                policy_version="ST12F_EVIDENCE_POLICY_V1_4",
                causation_id=causation_id,
                correlation_id=correlation_id,
            )

        if (
            type(query) is not FToDEvidenceReferenceQueryV1
            or query.evaluated_at != observed
        ):
            return unavailable()
        candidates: list[tuple[EconomicReceiptEventSpineV1, ST12FEvidenceReferenceV1]] = []
        try:
            durable_spines = self._durable_receipt_spines(
                effective_cutoff=observed,
                recorded_cutoff=observed,
            )
            for spine in durable_spines:
                payload = spine.typed_payload
                assert type(payload) is ST12FEvidenceControlReceiptRecordV1
                if payload.receipt_class is not ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
                    continue
                reference = payload.reconstruct(ST12FEvidenceReferenceV1)
                self._validate_receipt_lock_metadata(
                    spine,
                    decision_cutoff=observed,
                )
                if (
                    reference.evidence_id == query.requested_evidence_id
                    and reference.component_or_template_ref
                    == query.requested_component_or_template_ref
                    and reference.input_lock_id == query.expected_input_lock_id
                ):
                    candidates.append((spine, reference))
        except (ContractValidationError, PersistenceContractError):
            return unavailable()
        if not candidates:
            return unavailable()
        _, reference = candidates[-1]
        current_bundle_ref = self._durable_current_bundle_ref(
            reference.evidence_id,
            reference.input_lock_id,
            reference.component_or_template_ref,
            decision_cutoff=observed,
        )
        try:
            bundle = self.resolve_bundle(
                reference.evidence_ref,
                decision_cutoff=observed,
            )
        except (ContractValidationError, PersistenceContractError):
            return unavailable()
        if (
            reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            or reference.evidence_ref != current_bundle_ref
            or reference.evidence_ref
            not in {row.record_id for row in durable_spines}
            or reference.component_or_template_ref != query.requested_component_or_template_ref
            or reference.input_lock_id != query.expected_input_lock_id
            or reference.source_epoch_refs != query.expected_source_epoch_refs
            or reference.terminal_state != EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED.value
            or reference.lane != "REPLAY_PAPER"
            or reference.no_effect_flags != NO_EFFECTS_V1
            or not reference.observed_at <= query.evaluated_at <= reference.valid_until
            or bundle.evidence_id != query.requested_evidence_id
            or bundle.component_or_template_ref != query.requested_component_or_template_ref
            or bundle.input_lock_id != query.expected_input_lock_id
            or bundle.evidence_bundle_version != reference.evidence_bundle_version
            or bundle.terminal_state is not EvidenceBundleTerminalStateV1.CLOSED_INDEPENDENTLY_VALIDATED
            or bundle.d_evidence_reference_projection != reference
        ):
            return unavailable()
        return reference

    @property
    def immutable_indexes(self) -> Mapping[str, Mapping[object, object]]:
        snapshot = self._cache_snapshot
        return MappingProxyType(
            {
                "lane_results": snapshot.lane_results,
                "slot_results": snapshot.slot_results,
                "divergence": snapshot.divergence,
                "bundles": snapshot.bundles,
                "current_bundles": snapshot.current_bundles,
                "reviews": snapshot.reviews,
                "d_references": snapshot.d_references,
                "g_handoffs": snapshot.g_handoffs,
            }
        )


if (
    len(fields(ReplayResultContractV1)) != 26
    or len(fields(PaperResultContractV1)) != 26
    or len(fields(DivergenceAssessmentV1)) != 18
    or len(fields(ComputationEvidenceBundleV1)) != 30
    or len(ST12F_EVIDENCE_IDENTITIES_V1) != 48
):
    raise ContractValidationError(
        ReasonCode.SCHEMA_MISMATCH,
        "ST12-F canonical contract denominator differs from owner closure",
    )
