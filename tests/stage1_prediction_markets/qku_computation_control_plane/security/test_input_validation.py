from decimal import Decimal
from itertools import permutations

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    canonical_probability_decimal,
    decimal_context_v1,
    exact_decimal,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    NumericDomainError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    QuantityAndFrictionTermsV1,
    compute_math_01_binary_implied_probability,
    compute_math_03_orderbook_midpoint,
    compute_math_06_binary_contract_expected_net_cash,
    compute_math_07_multi_outcome_expected_net_cash,
    compute_math_08_brier_score,
    normalize_probability_vector,
)


def _terms(quantity: str = "1") -> QuantityAndFrictionTermsV1:
    return QuantityAndFrictionTermsV1(
        Decimal(quantity),
        Decimal("0.02"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
    )


def test_general_decimal_boundary_remains_exact_while_probability_is_centralized() -> None:
    assert exact_decimal("0.42") == Decimal("0.42")
    context = decimal_context_v1()
    accepted_text = f"1e{context.Emax}"
    overflow_text = f"1e{context.Emax + 1}"
    assert exact_decimal(accepted_text) == Decimal(accepted_text)
    with pytest.raises(NumericDomainError) as caught:
        exact_decimal(overflow_text)
    assert caught.value.reason_code is ReasonCode.INVALID_NUMERIC_INPUT

    with pytest.raises(NumericDomainError) as caught:
        exact_decimal(0.42)
    assert caught.value.reason_code is ReasonCode.FLOAT_DECIMAL_CONTAMINATION

    class NumericLookingObject:
        def __str__(self) -> str:
            return "0.5"

    for unsupported in (
        (0, (1, 2, 3), -2),
        [0, (1, 2, 3), -2],
        NumericLookingObject(),
    ):
        with pytest.raises(NumericDomainError) as caught:
            exact_decimal(unsupported)  # type: ignore[arg-type]
        assert caught.value.reason_code is ReasonCode.INVALID_NUMERIC_INPUT

    assert canonical_probability_decimal(0.42) == Decimal("0.42")
    assert canonical_probability_decimal("0.42") == Decimal("0.42")
    for value in (True, float("nan"), float("inf"), -0.01, 1.01):
        with pytest.raises(NumericDomainError):
            canonical_probability_decimal(value)  # type: ignore[arg-type]
    with pytest.raises(NumericDomainError):
        compute_math_01_binary_implied_probability("1.01", "1.00")
    with pytest.raises(NumericDomainError):
        compute_math_03_orderbook_midpoint(
            "0.4",
            "0.5",
            stale=1,  # type: ignore[arg-type]
        )
    assert compute_math_08_brier_score(0.7, 1) == pytest.approx(0.09)

    # V35 transport fixtures are data-shape evidence, never accepted source data.
    import json
    import struct
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
        _bounded_probability_json_v1,
        _decode_prediction_artifact_v1,
        _iter_prediction_artifact_frames_v1,
        _probability_binary64_v1,
    )

    literal = '{"a":[1,true,null],"b":"é"}'
    assert _bounded_probability_json_v1({"b": "é", "a": (1, True, None)}, max_bytes=28) == literal
    assert len(literal.encode("utf-8")) == 28
    with pytest.raises(ContractValidationError):
        _bounded_probability_json_v1({"b": "é", "a": (1, True, None)}, max_bytes=27)
    shared = ["x"]
    assert _bounded_probability_json_v1([shared, shared], max_bytes=13) == '[["x"],["x"]]'
    cyclic = []
    cyclic.append(cyclic)
    for invalid in (cyclic, {"a": float("nan")}, {"a": Decimal("1")}, {"a": "\ud800"}, {"a": 10**101}):
        with pytest.raises(ContractValidationError):
            _bounded_probability_json_v1(invalid, max_bytes=65536)
    for invalid in ("0.5", "0X1.0P-1", "0x1p-1", "0x1.0000000000000p+2000", "nan", True):
        with pytest.raises(ContractValidationError):
            _probability_binary64_v1(invalid)
    assert _probability_binary64_v1("0x1.0000000000000p-1", probability=True) == 0.5
    assert struct.pack("!d", _probability_binary64_v1("-0x0.0p+0")) == bytes.fromhex("8000000000000000")
    with pytest.raises(ContractValidationError):
        _probability_binary64_v1("-0x0.0p+0", probability=True)

    fixed = b'{"content":{"tuple":[{"binary64":"-0x0.0p+0"},[true,3]]},"ordinal":0,"path":[],"tag":"VALUE"}\n'
    frames = tuple(_iter_prediction_artifact_frames_v1((-0.0, [True, 3]), max_bytes=len(fixed), max_frames=1))
    assert frames == (fixed,)
    restored, count = _decode_prediction_artifact_v1(fixed, max_bytes=len(fixed), max_frames=1)
    assert count == 1 and type(restored) is tuple and type(restored[1]) is list
    assert restored[1] == [True, 3]
    assert struct.pack("!d", restored[0]) == bytes.fromhex("8000000000000000")
    for broken in (fixed[:-1], fixed + fixed, fixed.replace(b'"ordinal":0', b'"ordinal":true'),
                   fixed.replace(b'"path":[]', b'"path":[0]'), fixed.replace(b'"tag":"VALUE"', b'"tag":"OBJECT"')):
        with pytest.raises(ContractValidationError):
            _decode_prediction_artifact_v1(broken, max_bytes=len(broken), max_frames=2)
    # The independently specified root header and exact ordered scalar children.
    large = [0] * 4100
    split = tuple(_iter_prediction_artifact_frames_v1(large, max_bytes=400000, max_frames=4101))
    assert split[0] == b'{"content":4100,"ordinal":0,"path":[],"tag":"LIST"}\n'
    assert len(split) == 4101
    for ordinal, frame in enumerate(split[1:], 1):
        assert json.loads(frame) == {"content": 0, "ordinal": ordinal, "path": [ordinal - 1], "tag": "VALUE"}
    decoded, count = _decode_prediction_artifact_v1(b"".join(split), max_bytes=400000, max_frames=4101)
    assert decoded == large and count == 4101
    with pytest.raises(ContractValidationError):
        tuple(_iter_prediction_artifact_frames_v1(large, max_bytes=400000, max_frames=4100))

    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as numerical
    # Independent rational means: mean(mean(1,3),mean(10)) = 6, not 14/3.
    reduced = numerical._probability_cluster_functional_bank_v1(
        (((1.0,), (3.0,)), ((10.0,),)), ("mean",), ((0, 0), (1, 1)),
        max_rows=3, max_targets=1, max_plan_cells=4)
    assert reduced["original"] == {"mean": "0x1.8000000000000p+2"}
    assert tuple(row["values"]["mean"] for row in reduced["records"]) == (
        "0x1.0000000000000p+1", "0x1.4000000000000p+3")
    assert reduced["independent_cluster_count"] == 2 and reduced["source_row_count"] == 3
    smallest = float.fromhex("0x0.0000000000001p-1022")
    underflow = numerical._probability_cluster_functional_bank_v1(
        (((smallest,), (0.0,)), ((smallest,),)), ("mean",), ((0, 0), (1, 1)),
        max_rows=3, max_targets=1, max_plan_cells=4)
    assert underflow["original"] == {"mean": "0x0.0000000000001p-1022"}
    assert underflow["records"][0] == {"replicate": 0, "status": "INVALID", "values": None, "reason": "FUNCTIONAL_UNDERFLOW"}
    assert underflow["records"][1]["status"] == "VALID"
    unavailable = numerical._probability_bootstrap_bank_v1(underflow["records"], 2, ["mean"])
    assert unavailable["state"] == "UNAVAILABLE_INVALID_REPLICATE" and unavailable["failed_replicates"] == (0,)
    assert numerical._probability_prediction_feature_cells_v1(3, 5, 7, 2) == 54
    numerical._probability_selected_scaler_v1((0.0,), (1.0,), (1.0,), 200)
    for means, variances, scales in (((1e20,), (1.0,), (1.0,)), ((0.0,), (0.0,), (1.0,))):
        with pytest.raises(NumericDomainError):
            numerical._probability_selected_scaler_v1(means, variances, scales, 200)
    bank = [{"replicate": index, "status": "VALID", "values": {"q": "0x1.0000000000000p-2"}, "reason": None}
            for index in range(1000)]
    interval = numerical._probability_prediction_interval_v1(bank, 1000, ("q",))
    assert interval["intervals"] == (("q", 0.25, 0.25),)
    bank[0] = {"replicate": 0, "status": "INVALID", "values": None, "reason": "ZERO_VARIANCE"}
    assert numerical._probability_prediction_interval_v1(bank, 1000, ("q",))["state"] == "ABSTAIN"
    for invalid in ("0.25", "0x1p-2", "-0x0.0p+0", "0x1.0000000000000p+1", True):
        bank[-1]["values"]["q"] = invalid
        with pytest.raises(ContractValidationError) as failure:
            numerical._probability_prediction_interval_v1(bank, 1000, ("q",))
        assert failure.value.reason_code is ReasonCode.SCHEMA_MISMATCH
    _exercise_v35_frozen_numerical_vectors()
    _exercise_v35_ood_envelope()
    _exercise_v35_synthetic_fit_interfaces()
    _exercise_v35_continuous_refits()


def test_math_06_float_surface_boundaries_equivalence_and_quantity_linearity() -> None:
    common = ("0.55", "-0.45", "0", "0", "0", "0")
    as_float = compute_math_06_binary_contract_expected_net_cash(
        "1",
        0.6,
        *common,
    )
    as_string = compute_math_06_binary_contract_expected_net_cash(
        "1",
        "0.6",
        *common,
    )
    assert as_float == as_string == Decimal("0.15")
    assert compute_math_06_binary_contract_expected_net_cash(
        "1",
        0.0,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    ) == Decimal("-1")
    assert compute_math_06_binary_contract_expected_net_cash(
        "1",
        1.0,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    ) == Decimal("2")
    one = compute_math_06_binary_contract_expected_net_cash(
        "1",
        0.6,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    )
    two = compute_math_06_binary_contract_expected_net_cash(
        "2",
        0.6,
        "2",
        "-1",
        "0",
        "0",
        "0",
        "0",
    )
    assert two == 2 * one
    for value in (True, float("nan"), float("inf"), -0.01, 1.01):
        with pytest.raises(NumericDomainError):
            compute_math_06_binary_contract_expected_net_cash(
                "1",
                value,
                "1",
                "0",
                "0",
                "0",
                "0",
                "0",
            )


def test_math_07_receipt_normalization_equivalence_and_permutation_invariance() -> None:
    receipt = normalize_probability_vector((0.1, 0.2, 0.7000000000000001))
    assert receipt.normalization_applied
    assert receipt.original_sum == Decimal("1.0")
    assert receipt.tolerance > 0
    assert receipt.canonical_decimal_vector == (
        Decimal("0.1"),
        Decimal("0.2"),
        Decimal("0.7000000000000001"),
    )
    assert sum(receipt.normalized_decimal_vector, Decimal(0)) == Decimal(1)

    float_result = compute_math_07_multi_outcome_expected_net_cash(
        (0.2, 0.3, 0.5),
        ("1.0", "-0.2", "0.1"),
        _terms(),
    )
    string_result = compute_math_07_multi_outcome_expected_net_cash(
        ("0.2", "0.3", "0.5"),
        ("1.0", "-0.2", "0.1"),
        _terms(),
    )
    assert float_result == string_result == Decimal("0.17")
    paired = ((0.2, "1.0"), (0.3, "-0.2"), (0.5, "0.1"))
    for permuted in permutations(paired):
        assert compute_math_07_multi_outcome_expected_net_cash(
            tuple(item[0] for item in permuted),
            tuple(item[1] for item in permuted),
            _terms(),
        ) == float_result
    assert compute_math_07_multi_outcome_expected_net_cash(
        (1.0, 0.0),
        ("2", "-9"),
        QuantityAndFrictionTermsV1(
            Decimal("1"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
    ) == Decimal("2")


def test_math_07_rejects_nonfinite_outside_tolerance_and_mismatch() -> None:
    invalid = (
        ((float("nan"), 0.0), ("1", "2")),
        ((float("inf"), 0.0), ("1", "2")),
        ((0.4, 0.4), ("1", "2")),
        ((0.5, 0.5), ("1",)),
    )
    for probabilities, payoffs in invalid:
        with pytest.raises(NumericDomainError):
            compute_math_07_multi_outcome_expected_net_cash(
                probabilities,
                payoffs,
                _terms(),
            )


def _exercise_v35_frozen_numerical_vectors():
    """All 23 supplied literal cases exercise real subjects; no fitted/market evidence."""
    from fractions import Fraction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as subject
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import _V35_DRIFT_VECTOR_ROWS_V1 as vectors
    assert sum(len(vectors[key]) for key in ("codec", "reducers", "tapes", "ranks", "drift")) == 23
    for row in vectors["codec"]:
        assert subject._probability_functional_scalar_v1(row["token"]) == Fraction(row["ratio"])
    for row in vectors["reducers"]:
        clusters = tuple(tuple(tuple(float.fromhex(token) for token in values) for values in cluster) for cluster in row["clusters"])
        bank = subject._probability_cluster_functional_bank_v1(clusters, ("t0",), tuple(tuple(plan) for plan in row["plans"]),
            max_rows=sum(map(len, clusters)), max_targets=1, max_plan_cells=sum(map(len, row["plans"])))
        assert tuple(bank["original"].values()) == tuple(row["original"])
        actual = tuple(record["reason"] if record["status"] == "INVALID" else tuple(record["values"].values()) for record in bank["records"])
        assert actual == tuple(value if type(value) is str else tuple(value) for value in row["records"])
    for row in vectors["tapes"]:
        assert subject._probability_resampling_indices_v1(list(row["starts"]),
            [Fraction.from_float(float.fromhex(value)) for value in row["uniforms"]], row["n"], row["block"]) == tuple(row["indices"])
    for row in vectors["ranks"]:
        series = tuple(Fraction(i) for i in range(1, row["B"] + 1))
        assert tuple(subject._probability_inverse_ecdf_v1(series, Fraction(p)) for p in row["probabilities"]) == tuple(row["ranks"])
    for row in vectors["drift"]:
        names = tuple(row["targets"])
        banks = []
        for partition in ("R", "W"):
            records = []
            for block in row["blocks"]:
                for _ in range(block["count"]):
                    records.append(dict(replicate=len(records), status="VALID", values=dict(zip(names, block[partition], strict=True)), reason=None))
            banks.append(subject._probability_bootstrap_bank_v1(records, row["B"], list(names)))
        result = subject._derive_probability_drift_result_v1(dict(zip(names, row["R"], strict=True)),
                                                            dict(zip(names, row["W"], strict=True)), *banks)
        rows = result["rows"]
        actual = dict(exceedances=tuple(item["tail_numerator"] - 1 for item in rows),
            pvalues=tuple(str(item["pvalue"]) for item in rows), adjusted=tuple(str(item["adjusted_pvalue"]) for item in rows),
            rejected=tuple(i for i, item in enumerate(rows) if item["adjusted_pvalue"] <= Fraction(1, 20)),
            outside=tuple(item["outside_reference_band"] for item in rows),
            material=tuple(i for i, item in enumerate(rows) if item["material_breach"]))
        assert actual == {key: tuple(value) for key, value in row["expected"].items()}
    originals = ("1:0:draw:0:row:0", "V35_OCCURRENCE:0:existing", "V35_OCCURRENCE:01:x", "V35_OCCURRENCE:word:x")
    assert subject._probability_prediction_occurrence_prefix_v1(originals) == "V35_OCCURRENCE:1:"
    assert originals == ("1:0:draw:0:row:0", "V35_OCCURRENCE:0:existing", "V35_OCCURRENCE:01:x", "V35_OCCURRENCE:word:x")


def _exercise_v35_ood_envelope():
    """Independent rank expectations; synthetic fixed scalars, without fitting."""
    from fractions import Fraction
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as subject
    artifact = dict(schema="QTT_MODEL_DATA_ONLY_V35", kind="CALIBRATED_LOGISTIC", feature_names=["f"],
        environment={"python": "3.14.7", "numpy": "2.5.2", "scipy": "1.18.1", "scikit-learn": "1.9.0"},
        scaler=dict(mean=["0x0.0p+0"], var=["0x1.0000000000000p+0"],
                    scale=["0x1.0000000000000p+0"], n_samples_seen=97),
        coefficients=["0x0.0p+0"], intercept="0x0.0p+0", classes=[0, 1],
        calibration=dict(method="sigmoid", response="decision_function", a="-0x1.0000000000000p+0", b="0x0.0p+0"),
        fit_ids=[f"fit:{i}" for i in range(97)], calibration_ids=[f"cal:{i}" for i in range(100)],
        final_ids=[f"final:{i}" for i in range(30)])
    arguments = dict(artifact=artifact, feature_names=("f",),
        calibration_clusters=tuple(((float(i),),) for i in range(1, 101)),
        current_cluster=((101.0,),), schedule_ref="synthetic-schedule", calibration_schedule_ref="synthetic-schedule",
        current_schedule_ref="synthetic-schedule", max_rows=201, max_feature_cells=201)
    outside = subject._probability_ood_cluster_envelope_v1(**arguments)
    assert outside["pvalue"] == Fraction(1, 101) and outside["state"] == "OOD"
    assert outside["tail_denominator"] == 101
    assert outside["model_use_authorized"] is outside["source_authentication"] is outside["empirical_coverage_proven"] is False
    tied = subject._probability_ood_cluster_envelope_v1(**{**arguments, "current_cluster": ((100.0,),)})
    assert tied["pvalue"] == Fraction(2, 101) and tied["state"] == "IN_SUPPORT"
    prefix = subject._probability_ood_cluster_envelope_v1(**{**arguments, "current_cluster": ((0.0,), (101.0,))})
    assert prefix["current_prefix_maximum"] == 101.0 and prefix["pvalue"] == Fraction(1, 101)
    unequal = subject._probability_ood_cluster_envelope_v1(**{**arguments,
        "calibration_clusters": tuple(((float(i),), (float(i) / 2,)) for i in range(1, 101))})
    assert unequal["pvalue"] == outside["pvalue"] and unequal["tail_denominator"] == 101
    for change in ({"current_schedule_ref": "different"}, {"feature_names": ("unknown",)},
                   {"calibration_clusters": arguments["calibration_clusters"][:-1]},
                   {"max_rows": 100}, {"max_feature_cells": 100},
                   {"current_cluster": ((float("nan"),),)}, {"current_cluster": ((True,),)},
                   {"current_cluster": (("101",),)}):
        with pytest.raises(NumericDomainError):
            subject._probability_ood_cluster_envelope_v1(**{**arguments, **change})


def _exercise_v35_synthetic_fit_interfaces():
    """Port-shape/bank control flow only, never NumPy or estimator qualification.

    Synthetic integer/array and deterministic generator ports make these cases
    available to the existing CI group without fitting in a CI interpreter.
    The real pinned library and model-profile parity checks remain mandatory.
    """
    import sys
    from types import SimpleNamespace
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as subject
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    class Integer:
        def __init__(self, value):
            self.value = value
        def item(self):
            return self.value
    class Boolean(Integer):
        pass
    class Array:
        def __init__(self, value, *, shape=(1,), kind="i"):
            self.value, self.shape, self.dtype = Integer(value), shape, SimpleNamespace(kind=kind)
        def __getitem__(self, index):
            assert index == 0
            return self.value
    generated = []
    class Generator:
        def __init__(self, seed):
            generated.append(seed)
        def integers(self, low, high, *, size, dtype, endpoint):
            assert low == 0 and size == high and dtype is Integer and endpoint is False
            return [0] * size
    synthetic_numpy = SimpleNamespace(ndarray=Array, integer=Integer, bool_=Boolean, int64=Integer,
        __version__="SYNTHETIC_INTERFACE_ONLY", random=SimpleNamespace(
            Generator=Generator, PCG64=lambda seed: seed, SeedSequence=lambda values: tuple(values)))
    with patch.dict(sys.modules, {"numpy": synthetic_numpy}):
        for value in (0, 1, 100):
            assert subject._probability_prediction_iterations_v1("CALIBRATED_LOGISTIC", Array(value)) == value
            assert subject._probability_prediction_iterations_v1("HUBER", value) == value
            assert subject._probability_prediction_iterations_v1("HUBER", Integer(value)) == value
        for raw in (True, 0.0, "0", [0], Array(True), Array(0.0), Array(-1), Array(101),
                    Array(0, shape=()), Array(0, shape=(1, 1)), Array(0, kind="f"), Array(0, kind="b")):
            with pytest.raises(ContractValidationError) as error:
                subject._probability_prediction_iterations_v1("CALIBRATED_LOGISTIC", raw)
            assert error.value.reason_code is ReasonCode.SCHEMA_MISMATCH
        for raw in (True, 0.0, "0", [0], Array(0), Boolean(False), Integer(True), -1, 101):
            with pytest.raises(ContractValidationError) as error:
                subject._probability_prediction_iterations_v1("HUBER", raw)
            assert error.value.reason_code is ReasonCode.SCHEMA_MISMATCH

        def partition(prefix, count, start):
            return tuple((f"{prefix}:cluster:{i}", start + i + 2, start + i + 2,
                start + i, start + i + 1, (
                    ("V35_OCCURRENCE:0:original" if prefix == "fit" and i == 0 else f"{prefix}:negative:{i}", (-1.0,), 0),
                    (f"{prefix}:positive:{i}", (1.0,), 1))) for i in range(count))
        fit, calibration = partition("fit", 97, 0), partition("cal", 100, 200)
        final_rows = ("1:0:draw:0:row:0", *(f"final:row:{i}" for i in range(1, 30)))
        original_ids = tuple(row[0] for cluster in (*fit, *calibration) for row in cluster[5])
        arguments = dict(fit_clusters=fit, calibration_clusters=calibration,
            final_cluster_ids=tuple(f"final:cluster:{i}" for i in range(30)), final_row_ids=final_rows,
            final_start_ns=500, feature_names=("f",), requests=(("query", (0.0,)),),
            input_lock_id="synthetic-input", prediction_input_lock_id="synthetic-query", plan_id="synthetic-plan",
            master_seed=7, replicate_count=1000, method="PAIRED_IID_CLUSTERS", block_length=None,
            fit_cutoff_ns=100, calibration_cutoff_ns=400, embargo_ns=0,
            max_plan_cells=197000, max_expanded_rows=200, max_prediction_cells=1001,
            max_feature_cells=606, max_fit_calls=3003)
        synthetic_model = dict(schema="QTT_MODEL_DATA_ONLY_V35", kind="CALIBRATED_LOGISTIC", feature_names=["f"],
            environment={"python": "SYNTHETIC_INTERFACE_ONLY", "numpy": "SYNTHETIC_INTERFACE_ONLY",
                         "scipy": "SYNTHETIC_INTERFACE_ONLY", "scikit-learn": "SYNTHETIC_INTERFACE_ONLY"},
            scaler=dict(mean=["0x0.0p+0"], var=["0x1.0000000000000p+0"],
                        scale=["0x1.0000000000000p+0"], n_samples_seen=194),
            coefficients=["0x0.0p+0"], intercept="0x0.0p+0", classes=[0, 1],
            calibration=dict(method="sigmoid", response="decision_function", a="-0x1.0000000000000p+0", b="0x0.0p+0"),
            fit_ids=[row[0] for cluster in fit for row in cluster[5]],
            calibration_ids=[row[0] for cluster in calibration for row in cluster[5]], final_ids=list(final_rows))
        calls = []
        interface_failure = ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "synthetic malformed native iteration counter")
        mode = "interface"
        actual_fit = subject._probability_fit_prediction_v1
        native_fault_entries, verification_entries = [], []

        def fit_with_nonfinite_output(fault, fit_rows, cal_rows, final_ids,
                                      feature_names, request_values, kind, work):
            # These library ports expose declared fitted-output faults to the
            # real fit owner. They do not fit or qualify numerical libraries.
            from contextlib import nullcontext
            import math

            class Vector(tuple):
                def __gt__(self, other):
                    return tuple(value > other for value in self)
                def tolist(self):
                    return list(self)
                def ravel(self):
                    def flatten(value):
                        if isinstance(value, (tuple, list)):
                            for child in value:
                                yield from flatten(child)
                        else:
                            yield value
                    return Vector(flatten(self))

            def array(value, **kwargs):
                if isinstance(value, (tuple, list)):
                    return Vector(array(child) if isinstance(child, (tuple, list)) else child
                                  for child in value)
                return value

            def finite(value):
                if isinstance(value, (tuple, list)):
                    return tuple(flag for child in value for flag in finite(child))
                return (math.isfinite(value),)

            class SyntheticConvergenceWarning(UserWarning):
                pass

            class FittedClassifier:
                def __init__(self, **kwargs):
                    self.n_iter_ = Array(0) if kind == "CALIBRATED_LOGISTIC" else 0
                    self.scale_ = float("inf") if fault == "huber_scale" else 1.0
                    self.coef_ = Vector((Vector((float("inf") if fault == "coefficient" else 0.0,)),))
                    self.intercept_ = Vector((float("nan") if fault == "intercept" else 0.0,))
                    self.classes_ = Vector((0, 1))

            class Scaler:
                def __init__(self, **kwargs):
                    self.mean_, self.var_, self.scale_ = Vector((0.0,)), Vector((1.0,)), Vector((1.0,))
                    self.n_samples_seen_ = len(fit_rows)

            class Pipeline:
                def __init__(self, steps):
                    self.named_steps = dict(steps)
                def fit(self, values, labels):
                    native_fault_entries.append(fault)
                    return self
                def decision_function(self, values):
                    return Vector(0.0 for _ in values)

            class Calibrator:
                def __init__(self, estimator, **kwargs):
                    self.calibrated_classifiers_ = [SimpleNamespace(calibrators=[SimpleNamespace(
                        a_=float("inf") if fault == "sigmoid_a" else 0.0,
                        b_=float("nan") if fault == "sigmoid_b" else 0.0)])]
                def fit(self, values, labels):
                    return self

            def verification_port(*args):
                verification_entries.append(fault)
                return 0.0, 0.0, None

            fit_numpy = SimpleNamespace(**vars(synthetic_numpy), float64=float,
                asarray=array, ascontiguousarray=array, array=array, all=all,
                isfinite=finite, array_equal=lambda left, right: left == right)
            modules = {
                "numpy": fit_numpy,
                "scipy": SimpleNamespace(__version__="SYNTHETIC_INTERFACE_ONLY"),
                "sklearn": SimpleNamespace(__version__="SYNTHETIC_INTERFACE_ONLY"),
                "sklearn.preprocessing": SimpleNamespace(StandardScaler=Scaler),
                "sklearn.linear_model": SimpleNamespace(LogisticRegression=FittedClassifier, HuberRegressor=FittedClassifier),
                "sklearn.pipeline": SimpleNamespace(Pipeline=Pipeline),
                "sklearn.calibration": SimpleNamespace(CalibratedClassifierCV=Calibrator),
                "sklearn.frozen": SimpleNamespace(FrozenEstimator=lambda value: value),
                "sklearn.exceptions": SimpleNamespace(ConvergenceWarning=SyntheticConvergenceWarning),
                "threadpoolctl": SimpleNamespace(threadpool_limits=lambda **kwargs: nullcontext()),
            }
            with patch.dict(sys.modules, modules), patch.object(
                    subject, "_probability_checked_sigmoid_v1", verification_port):
                return actual_fit(fit_rows, cal_rows, final_ids, feature_names, request_values, kind, work)

        def fitted(fit_rows, cal_rows, final_ids, feature_names, request_values, kind, work):
            calls.append((len(fit_rows), len(cal_rows)))
            assert final_ids is final_rows and kind == "CALIBRATED_LOGISTIC"
            if len(calls) > 1:
                labels = tuple(row[0] for row in (*fit_rows, *cal_rows))
                assert all(label.startswith("V35_OCCURRENCE:1:") for label in labels)
                assert not set(labels).intersection((*original_ids, *final_rows))
            faults = {2: "coefficient", 3: "intercept", 4: "sigmoid_a", 5: "sigmoid_b"}
            if mode == "nonfinite_outputs" and len(calls) in faults:
                return fit_with_nonfinite_output(faults[len(calls)], fit_rows, cal_rows,
                    final_ids, feature_names, request_values, kind, work)
            work["base_fit_calls"] += 1
            if len(calls) == 2 and mode != "complete":
                if mode == "interface":
                    raise interface_failure
                raise subject._ProbabilityNumericalFailureV1("ZERO_VARIANCE")
            work["calibration_fit_calls"] += 1
            work["calibration_verification_calls"] += 1
            return {"model": synthetic_model,
                    "requests": ((0.0, 0.5),), "fit_calls": 2, "max_absolute_parity_error": 0.0}
        def work_origin():
            return {"base_fit_calls": 0, "calibration_fit_calls": 0, "calibration_verification_calls": 0}
        with patch.object(subject, "_probability_fit_prediction_v1", fitted):
            with pytest.raises(NumericDomainError):
                subject._probability_construct_prediction_bank_v1(**{**arguments, "max_fit_calls": 3002}, work=work_origin())
            assert calls == generated == []
            with pytest.raises(ContractValidationError) as failure:
                subject._probability_construct_prediction_bank_v1(**arguments, work=work_origin())
            assert failure.value is interface_failure and len(calls) == 2
            assert len(generated) == 2000 and len(set(generated)) == 2000
            calls.clear(); generated.clear(); mode = "numerical"
            work = work_origin()
            bank = subject._probability_construct_prediction_bank_v1(**arguments, work=work)
        assert len(calls) == 1001 and len(generated) == 2000
        assert tuple(record["replicate"] for record in bank["records"]) == tuple(range(1000))
        assert bank["records"][0] == {"replicate": 0, "status": "INVALID", "values": None, "reason": "ZERO_VARIANCE"}
        assert all(record["status"] == "VALID" and record["values"] == {"query": "0x1.0000000000000p-1"}
                   for record in bank["records"][1:])
        assert bank["state"] == "UNAVAILABLE_INVALID_REPLICATE" and bank["intervals"] is None
        assert bank["successful_fit_calls"] == 2000
        assert work == {"base_fit_calls": 1001, "calibration_fit_calls": 1000, "calibration_verification_calls": 1000}
        assert tuple(row[0] for cluster in (*fit, *calibration) for row in cluster[5]) == original_ids
        assert bank["model_use_authorized"] is bank["source_authentication"] is bank["target_environment_qualified"] is False
        calls.clear(); generated.clear(); mode = "nonfinite_outputs"
        work = work_origin()
        with patch.object(subject, "_probability_fit_prediction_v1", fitted):
            failed_bank = subject._probability_construct_prediction_bank_v1(**arguments, work=work)
        assert native_fault_entries == ["coefficient", "intercept", "sigmoid_a", "sigmoid_b"]
        assert verification_entries == []
        assert len(calls) == 1001 and len(generated) == 2000
        assert tuple(row["replicate"] for row in failed_bank["records"]) == tuple(range(1000))
        assert failed_bank["records"][:4] == [
            {"replicate": ordinal, "status": "INVALID", "values": None, "reason": "CANONICAL_FLOAT_HEX"}
            for ordinal in range(4)]
        assert all(row["status"] == "VALID" for row in failed_bank["records"][4:])
        assert failed_bank["state"] == "UNAVAILABLE_INVALID_REPLICATE" and failed_bank["intervals"] is None
        # Two faults precede calibration, two precede verification. The 997
        # successful fits include the original and retain the full denominator.
        assert failed_bank["successful_fit_calls"] == 1994
        assert work == {"base_fit_calls": 1001, "calibration_fit_calls": 999, "calibration_verification_calls": 997}
        assert failed_bank["model_use_authorized"] is failed_bank["source_authentication"] is False
        # The continuous scale has the same finite-export boundary, with no
        # calibration work. This is one synthetic fitted-output interface call.
        from decimal import Decimal
        huber_rows = tuple((row[0], row[1], Decimal(row[2])) for cluster in fit for row in cluster[5])
        huber_calibration = tuple((row[0], row[1], Decimal(row[2])) for cluster in calibration for row in cluster[5])
        huber_work = work_origin()
        with pytest.raises(subject._ProbabilityNumericalFailureV1) as scale_failure:
            fit_with_nonfinite_output("huber_scale", huber_rows, huber_calibration,
                final_rows, ("f",), ((0.0,),), "HUBER", huber_work)
        assert scale_failure.value.detail == "CANONICAL_FLOAT_HEX"
        assert huber_work == {"base_fit_calls": 1, "calibration_fit_calls": 0, "calibration_verification_calls": 0}
        assert native_fault_entries[-1] == "huber_scale" and verification_entries == []
        # Native bank construction, complete framing, decoding and locked-value
        # admission are exercised together. Only the explicitly synthetic
        # generator/fitter ports above are substituted; this is no model fit.
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
            _iter_prediction_artifact_frames_v1, _decode_prediction_artifact_v1)
        calls.clear(); generated.clear(); mode = "complete"
        with patch.object(subject, "_probability_fit_prediction_v1", fitted):
            complete = subject._probability_construct_prediction_bank_v1(**arguments, work=work_origin())
        assert len(calls) == 1001 and len(generated) == 2000
        frames = tuple(_iter_prediction_artifact_frames_v1(complete, max_bytes=8_000_000, max_frames=4096))
        decoded, frame_count = _decode_prediction_artifact_v1(b"".join(frames), max_bytes=8_000_000, max_frames=4096)
        assert frame_count == len(frames) and decoded == complete
        admitted = subject._probability_read_locked_prediction_bank_v1(decoded,
            input_lock_id="synthetic-input", prediction_input_lock_id="synthetic-query",
            feature_names=("f",), requests=(("query", (0.0,)),))
        assert admitted["values"] == (("query", 0.5, 0.5, 0.5),)
        assert admitted["model_use_authorized"] is admitted["source_authentication"] is admitted["record_authenticity_proven"] is False
        for query in ((("query", (-0.0,)),), (("query", (1.0,)),), (("other-query", (0.0,)),)):
            with pytest.raises(NumericDomainError):
                subject._probability_read_locked_prediction_bank_v1(decoded,
                    input_lock_id="synthetic-input", prediction_input_lock_id="synthetic-query",
                    feature_names=("f",), requests=query)


def _exercise_v35_continuous_refits():
    """Synthetic fitter/RNG ports isolate full-refit orchestration, never fitting.

    The actual original conformal reducer and complete-bank consumer run against
    independent rank/value expectations. No market coverage, library, resource
    measurement or target-model qualification is inferred from these fixtures.
    """
    import json
    import sys
    import time
    from dataclasses import replace
    from fractions import Fraction
    from types import MappingProxyType, SimpleNamespace
    from unittest.mock import patch
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as subject
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import ContinuousScoreResultV2

    generated, random_calls, calls = [], [], []
    integer_dtype = object()
    class Generator:
        def __init__(self, seed):
            self.seed = seed
            generated.append(seed)
        def integers(self, low, high, *, size, dtype, endpoint):
            assert low == 0 and high == size and dtype is integer_dtype and endpoint is False
            random_calls.append((self.seed, "integers", size))
            return [0] * size
        def random(self, *, size, dtype):
            assert dtype is float
            random_calls.append((self.seed, "random", size))
            return [0.5 if i % 2 == 0 else 0.75 for i in range(size)]
    synthetic_numpy = SimpleNamespace(int64=integer_dtype, float64=float,
        __version__="SYNTHETIC_INTERFACE_ONLY", random=SimpleNamespace(
            Generator=Generator, PCG64=lambda seed: seed, SeedSequence=lambda values: tuple(values)))
    def partition(prefix, count, start):
        return tuple((f"{prefix}:cluster:{i}", start + i + 2, start + i + 2, start + i, start + i + 1,
            tuple(("V35_OCCURRENCE:0:original" if prefix == "fit" and i == j == 0 else f"{prefix}:{i}:{j}",
                   ((-1.0, 1.0, 2.0)[j],), Decimal(i + 1))
                  for j in range(3 if i == 0 else 2))) for i in range(count))
    fit, calibration = partition("fit", 97, 0), partition("cal", 100, 200)
    final_rows = ("1:0:draw:0:row:0", *(f"final:row:{i}" for i in range(1, 30)))
    source_ids = tuple(row[0] for cluster in (*fit, *calibration) for row in cluster[5])
    allocations = MappingProxyType(dict(index_bytes=1_576_000, prediction_bytes=8008,
        lineage_bytes=1_000_000, fitted_state_bytes=50_000, numerical_scratch_bytes=500_000,
        python_object_bytes=20_000_000, artifact_bytes=2_000_000, storage_bytes=2_000_000))
    envelope = MappingProxyType(dict(max_source_clusters=227, max_expanded_rows_per_replicate=300,
        max_prediction_targets=1, max_memory_bytes=25_141_184, max_duration_ns=60_000_000_000))
    parameters = dict(fit_clusters=fit, calibration_clusters=calibration, final_row_ids=final_rows,
        final_cluster_ids=tuple(f"final:cluster:{i}" for i in range(30)), final_start_ns=500,
        feature_names=("f",), requests=(("query", (0.0,)),), fit_cutoff_ns=100,
        calibration_cutoff_ns=400, embargo_ns=0, max_rows=396, max_feature_cells=897,
        unit="SYNTHETIC::USD_PER_CONTRACT", input_lock_id="SYNTHETIC::LOCK",
        prediction_input_lock_id="SYNTHETIC::QUERY-LOCK", plan_id="SYNTHETIC::CONTINUOUS-PLAN",
        master_seed=7, replicate_count=1000, method="PAIRED_IID_CLUSTERS", block_length=None,
        max_plan_cells=197000, max_expanded_rows=300, max_prediction_cells=1001, max_fit_calls=1001,
        max_model_bytes=50_000, max_record_bytes=256, max_total_bank_bytes=2_000_000,
        resource_envelope=envelope, allocation_calculation=allocations,
        work_roster=MappingProxyType(dict(base_fit_calls=1001, calibration_fit_calls=0, calibration_verification_calls=0)))
    mode = ["complete"]
    malformed = ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "SYNTHETIC malformed Huber metadata")
    def fitted(fit_rows, cal_rows, final_ids, feature_names, request_values, kind, work):
        ordinal = len(calls) - 1
        observed_ids = (tuple(row[0] for row in fit_rows), tuple(row[0] for row in cal_rows))
        # Assert every occurrence immediately; retain bounded count evidence,
        # not thousands of additional copies of the synthetic row namespaces.
        calls.append((len(fit_rows), len(cal_rows)))
        assert kind == "HUBER" and final_ids is final_rows and feature_names == ("f",)
        assert all(type(row[2]) is Decimal for row in (*fit_rows, *cal_rows))
        if ordinal < 0:
            assert len(fit_rows) == 195 and len(cal_rows) == 201
            assert observed_ids == (tuple(row[0] for c in fit for row in c[5]),
                                    tuple(row[0] for c in calibration for row in c[5]))
        else:
            assert all(name.startswith("V35_OCCURRENCE:1:") for group in observed_ids for name in group)
            assert not set(name for group in observed_ids for name in group) & set((*source_ids, *final_rows))
            assert len(set(name for group in observed_ids for name in group)) == len(fit_rows) + len(cal_rows)
        work["base_fit_calls"] += 1
        if mode[0] == "original-failure" and ordinal == -1:
            raise subject._ProbabilityNumericalFailureV1("ZERO_VARIANCE")
        if mode[0] == "numerical" and ordinal == 17:
            raise subject._ProbabilityNumericalFailureV1("ZERO_VARIANCE")
        if mode[0] == "interface" and ordinal == 7:
            raise malformed
        value = -2.0 if ordinal == -1 else float(ordinal - 500)
        model = dict(schema="QTT_MODEL_DATA_ONLY_V35", kind="HUBER", feature_names=["f"],
            environment={key: "SYNTHETIC_INTERFACE_ONLY" for key in ("python", "numpy", "scipy", "scikit-learn")},
            scaler=dict(mean=["0x0.0p+0"], var=["0x1.0000000000000p+0"], scale=["0x1.0000000000000p+0"], n_samples_seen=len(fit_rows)),
            coefficients=["0x0.0p+0"], intercept=value.hex(), classes=[], calibration=None, scale="0x1.0000000000000p+0",
            fit_ids=list(observed_ids[0]), calibration_ids=list(observed_ids[1]), final_ids=list(final_ids))
        return dict(model=model, requests=((value, value),), calibration_predictions=(0.0,) * len(cal_rows),
                    fit_calls=1, max_absolute_parity_error=0.0)
    def origin():
        return dict(base_fit_calls=0, calibration_fit_calls=0, calibration_verification_calls=0)
    def construct(**changes):
        work, attempt = origin(), {}
        result = subject._probability_construct_continuous_bank_v1(**{**parameters, **changes},
            deadline_ns=time.monotonic_ns() + 60_000_000_000, work=work, attempt=attempt)
        return (*result, work, attempt)
    def read(bank, **changes):
        binding = dict(input_lock_id=parameters["input_lock_id"], prediction_input_lock_id=parameters["prediction_input_lock_id"],
            feature_names=("f",), requests=parameters["requests"], unit=parameters["unit"], max_record_bytes=256)
        return subject._probability_read_continuous_bank_v1(bank, **{**binding, **changes})

    with patch.dict(sys.modules, {"numpy": synthetic_numpy}), patch.object(subject, "_probability_fit_prediction_v1", fitted):
        for change in ({"max_fit_calls": 1000}, {"max_plan_cells": 196999}, {"max_prediction_cells": 1000},
                       {"max_expanded_rows": 299}, {"max_feature_cells": 896}, {"max_rows": 395},
                       {"master_seed": True}, {"replicate_count": 999}, {"max_record_bytes": 1},
                       {"max_total_bank_bytes": 1}, {"block_length": 2},
                       {"resource_envelope": MappingProxyType({**envelope, "max_source_clusters": 226})},
                       {"resource_envelope": MappingProxyType({**envelope, "max_memory_bytes": 25_141_183})},
                       {"allocation_calculation": MappingProxyType({**allocations, "index_bytes": 1_575_999})},
                       {"allocation_calculation": MappingProxyType({**allocations, "prediction_bytes": 8007})},
                       {"allocation_calculation": MappingProxyType({**allocations, "artifact_bytes": 1})},
                       {"allocation_calculation": MappingProxyType({**allocations, "storage_bytes": 1})},
                       {"work_roster": MappingProxyType(dict(base_fit_calls=1, calibration_fit_calls=0, calibration_verification_calls=0))}):
            with pytest.raises((NumericDomainError, ContractValidationError)):
                construct(**change)
            assert calls == generated == random_calls == []
        complete, conformal, work, attempt = construct()
        assert complete.state == "COMPLETE" and complete.partition_codes == (1, 2)
        assert len(calls) == 1001 and work == dict(complete.actual_fit_calls) == dict(parameters["work_roster"])
        assert generated == [(7, code, r) for r in range(1000) for code in (1, 2)]
        assert random_calls == [((7, code, r), "integers", size) for r in range(1000) for code, size in ((1, 97), (2, 100))]
        assert complete.plans == ((tuple(0 for _ in range(97)), tuple(0 for _ in range(100))),) * 1000
        assert complete.expanded_row_counts == ((291, 300),) * 1000
        records = tuple(json.loads(row) for row in complete.records)
        assert tuple(row["replicate"] for row in records) == tuple(range(1000))
        assert tuple(row["values"]["query"] for row in records) == tuple(float(i - 500).hex() for i in range(1000))
        # Sorted ranks 25 and 975 of -500,...,499; not expectations from the subject.
        assert read(complete) == (("query", (-476.0).hex(), (474.0).hex()),)
        assert complete.original_predictions == (("query", (-2.0).hex()),)
        assert conformal["fit_calls"] == 1 and conformal["actual_fit_calls"] == origin() | {"base_fit_calls": 1}
        assert conformal["cluster_residuals"] == tuple(Fraction(i) for i in range(1, 101))
        assert conformal["rank"] == 96 and conformal["q"] == Fraction(96)
        assert conformal["decimal34_values"] == (("query", "-2", "-98", "94"),)
        assert conformal["model_use_authorized"] is conformal["empirical_coverage_proven"] is False
        assert tuple(conformal["model"]["final_ids"]) == final_rows
        assert complete.occurrence_prefix == "V35_OCCURRENCE:1:"
        assert attempt["preflight"]["fit_calls"] == 1001 and attempt["preflight"]["feature_cells"] == 897
        assert attempt["preflight"]["memory_bytes"] == 25_141_184
        score = ContinuousScoreResultV2("query", "PM-QAML-MARKOUT-V2", "SYNTHETIC::HUBER",
            Decimal("-2"), Decimal("-98"), Decimal("94"), parameters["unit"], "SYNTHETIC::UNCERTAINTY",
            "SYNTHETIC", "SYNTHETIC::USE-LIMIT", "SCORE_RESEARCH_ONLY")
        assert score.predicted_value < 0 and score.upper_value > 1
        for changes in ({"unit": "PROBABILITY"}, {"input_lock_id": "other"},
                        {"requests": (("query", (-0.0,)),)}, {"requests": (("other", (0.0,)),)}):
            with pytest.raises(NumericDomainError):
                read(complete, **changes)
        with pytest.raises(ContractValidationError):
            replace(complete, records=complete.records[:-1])
        with pytest.raises(NumericDomainError):
            read(replace(complete, records=tuple(reversed(complete.records))))
        with pytest.raises(NumericDomainError):
            read(replace(complete, plans=(((97,) * 97, (0,) * 100), *complete.plans[1:])))
        with pytest.raises(NumericDomainError):
            subject._probability_read_locked_prediction_bank_v1(complete,
                input_lock_id=parameters["input_lock_id"], prediction_input_lock_id=parameters["prediction_input_lock_id"],
                feature_names=("f",), requests=parameters["requests"])

        calls.clear(); generated.clear(); random_calls.clear(); mode[0] = "numerical"
        unavailable, _, failed_work, failed_attempt = construct()
        assert len(calls) == 1001 and failed_work == dict(parameters["work_roster"])
        assert len(unavailable.records) == 1000 and unavailable.state == "UNAVAILABLE_INVALID_REPLICATE"
        assert json.loads(unavailable.records[17]) == dict(replicate=17, status="INVALID", values=None, reason="ZERO_VARIANCE")
        assert unavailable.descriptive_bounds is None and read(unavailable) is None
        assert failed_attempt["state"] == unavailable.state

        for failure_mode, expected_calls, expected_prefix, expected_ordinal in (
                ("original-failure", 1, 0, -1), ("interface", 9, 7, 7)):
            calls.clear(); generated.clear(); random_calls.clear(); mode[0] = failure_mode
            prefix_work, prefix_attempt = origin(), {}
            with pytest.raises((NumericDomainError, ContractValidationError)) as error:
                subject._probability_construct_continuous_bank_v1(**parameters,
                    deadline_ns=time.monotonic_ns() + 60_000_000_000, work=prefix_work, attempt=prefix_attempt)
            assert len(calls) == expected_calls and prefix_work["base_fit_calls"] == expected_calls
            assert len(prefix_attempt["records"]) == expected_prefix
            assert prefix_attempt["active_ordinal"] == expected_ordinal
            assert prefix_attempt["state"] == "INCOMPLETE_UNAVAILABLE" and "bank" not in prefix_attempt
            assert prefix_attempt["failure"] is error.value
            if failure_mode == "interface":
                assert error.value is malformed
                assert tuple(row["replicate"] for row in prefix_attempt["records"]) == tuple(range(7))
            else:
                assert prefix_attempt["original"] is None

        calls.clear(); generated.clear(); random_calls.clear(); mode[0] = "complete"
        expired = ContractValidationError(ReasonCode.RESOURCE_BOUND_EXCEEDED, "SYNTHETIC deadline")
        def deadline_observation():
            if len(calls) == 9:
                raise expired
        prefix_work, prefix_attempt = origin(), {}
        with patch.object(subject, "_probability_work_observation_v1", deadline_observation):
            with pytest.raises(ContractValidationError) as error:
                subject._probability_construct_continuous_bank_v1(**parameters,
                    deadline_ns=time.monotonic_ns() + 60_000_000_000, work=prefix_work, attempt=prefix_attempt)
        assert error.value is expired and prefix_work["base_fit_calls"] == 9
        assert tuple(row["replicate"] for row in prefix_attempt["records"]) == tuple(range(8))
        assert prefix_attempt["state"] == "INCOMPLETE_UNAVAILABLE" and "bank" not in prefix_attempt

        calls.clear(); generated.clear(); random_calls.clear()
        stationary, _, stationary_work, _ = construct(method="PAIRED_STATIONARY_CLUSTERS", block_length=2)
        assert stationary.plans == ((tuple(i % 2 for i in range(97)), tuple(i % 2 for i in range(100))),) * 1000
        assert stationary.expanded_row_counts == ((243, 250),) * 1000
        assert generated == [(7, code, r) for r in range(1000) for code in (1, 2)]
        assert random_calls == [((7, code, r), operation, size) for r in range(1000)
            for code, size in ((1, 97), (2, 100)) for operation in ("integers", "random")]
        assert len(calls) == 1001 and stationary_work == dict(parameters["work_roster"])
        # The larger preregistered branch keeps all 5,000 ordinals. These are
        # explicit synthetic allowances, not a precision decision or model run.
        calls.clear(); generated.clear(); random_calls.clear()
        larger_allocation = MappingProxyType({**allocations, "index_bytes": 7_880_000,
            "prediction_bytes": 40_008, "python_object_bytes": 100_000_000,
            "artifact_bytes": 6_000_000, "storage_bytes": 6_000_000})
        larger_work = MappingProxyType(dict(base_fit_calls=5001, calibration_fit_calls=0, calibration_verification_calls=0))
        larger, _, actual_larger_work, _ = construct(replicate_count=5000, max_fit_calls=5001,
            max_plan_cells=985000, max_prediction_cells=5001, max_total_bank_bytes=6_000_000,
            allocation_calculation=larger_allocation, work_roster=larger_work,
            resource_envelope=MappingProxyType({**envelope, "max_memory_bytes": 115_477_184}))
        assert len(calls) == 5001 and actual_larger_work == dict(larger_work)
        assert generated == [(7, code, r) for r in range(5000) for code in (1, 2)]
        assert tuple(json.loads(row)["replicate"] for row in larger.records) == tuple(range(5000))
        assert read(larger) == (("query", (-376.0).hex(), (4374.0).hex()),)
    _exercise_v35_continuous_consumer(parameters, complete, conformal, unavailable)


def _exercise_v35_continuous_consumer(parameters, complete, conformal, unavailable):
    """Synthetic registered-boundary mechanics; no PIT, issuer or model acceptance.

    The existing synthetic issuer port supplies only this in-memory test. The
    numerical environment/constructor and PIT partition port are explicitly
    isolated here; the preceding cases exercise actual refit orchestration.
    Production environment checks and source acquisition remain unchanged.
    """
    import time
    from contextlib import contextmanager
    from dataclasses import dataclass
    from types import MappingProxyType, SimpleNamespace
    from unittest.mock import patch
    from tests.stage1_prediction_markets.qku_computation_control_plane.tranche_e import _synthetic_probability_issuance
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import input_resolver as consumer
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import implementation_registry as numerical
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
        _ProbabilityRevocationCutV1, _ProbabilityAdmissionLimitsV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
        InMemoryPersistenceAdapterV1, ProbabilityProducerReadLimitsV1)
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.protocols import ProbabilityIssuerReadRequestV1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _bounded_probability_json_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, OwnerAdapterError

    @dataclass(frozen=True)
    class SyntheticModel:
        model_kind: str
        feature_names: tuple
        replicate_count: int
        export_text: str
    @dataclass(frozen=True)
    class SyntheticSnapshot:
        model: SyntheticModel
        read_ns: int
        result: None = None
    @dataclass(frozen=True)
    class SyntheticManifest:
        task_id: str
    @dataclass(frozen=True)
    class SyntheticLabel:
        target_unit: str

    for mode in ("complete", "invalid-bank", "short-work", "different-seed", "different-unit", "different-B",
                 "source-replaced", "prefix-failure"):
        resolver, reader, initial_requests = _synthetic_probability_issuance()
        initial_requests = tuple(request for request in initial_requests if request.role in ("SOURCE_RIGHTS", "MODEL_BUILD"))
        now = time.time_ns()
        with resolver._resolve_probability_issuer_context_v1(initial_requests, evaluated_ns=now) as issued:
            admissions = tuple(resolver._admit_probability_issuer_v1(request, trusted_snapshot=issued) for request in initial_requests)
        scope = initial_requests[0].scope
        deadline = time.monotonic_ns() + 60_000_000_000
        projected = {name: value for name, value in parameters.items() if name not in
                     {"max_model_bytes", "max_record_bytes", "max_total_bank_bytes"}}
        projected.update(uncertainty_packet_ref="SYNTHETIC::UNCERTAINTY", evidence_level="SYNTHETIC_ORCHESTRATION_ONLY",
                         use_limit_ref="SYNTHETIC::USE-LIMIT")
        if mode == "different-seed":
            projected["master_seed"] = 8
        if mode == "different-unit":
            projected["unit"] = "SYNTHETIC::OTHER-UNIT"
        if mode == "different-B":
            projected["replicate_count"] = 5000
        source = MappingProxyType(dict(manifest=SyntheticManifest("PM-QAML-MARKOUT-V2"),
            continuous_parameters=MappingProxyType(projected),
            feature_rows=(("SYNTHETIC::ROW", None, SyntheticLabel(parameters["unit"])),)))
        cut = _ProbabilityRevocationCutV1("SYNTHETIC::CHECKPOINT", 0, None, (), now, now + 30_000_000_000)
        fence = consumer._ProbabilityDependencyFenceV1(persistence=InMemoryPersistenceAdapterV1(),
            issuer_resolver=resolver, scope=scope, issuer_snapshot=issued, source_issuer_ref=initial_requests[0].issuer_ref,
            stream_ref="SYNTHETIC::STREAM", baseline_ref="SYNTHETIC::BASELINE", baseline_ordinal=0,
            baseline_invalidated_refs=(), cut=cut, max_prepared=8, max_pending=2, max_records=32,
            initial_latch=False, construction_inputs=source)
        snapshot = SyntheticSnapshot(SyntheticModel("HUBER", ("f",), 1000,
            _bounded_probability_json_v1(conformal["model"], max_bytes=50_000)), time.time_ns())
        read_limits = ProbabilityProducerReadLimitsV1(1024, 8_000_000, 500_000, 5000, deadline)
        materialized = dict(snapshot=snapshot, read_request=SimpleNamespace(limits=read_limits),
            limits=_ProbabilityAdmissionLimitsV1(1000, 1000, 1, 50_000, 256, 2_000_000))
        dependencies = tuple(dict.fromkeys(("SYNTHETIC::USE-LIMIT",
            *(ref for admission in admissions for ref in admission.authority_dependency_refs))))
        result_ref = "SYNTHETIC::CONTINUOUS-RESULT"
        entry = fence._register_v1(snapshot, kind="MATERIALIZATION", view=resolver._probability_last_issuer_view_v1,
            dependency_refs=dependencies, valid_until_ns=cut.valid_until_ns, value_node_limit=8_000_000,
            metadata=dict(materialization=materialized, construction_source=source,
                construction_pin=consumer._probability_construction_pin_v1(source, max_nodes=8_000_000),
                construction_pin_limit=8_000_000, intent='{"result_ref":"SYNTHETIC::CONTINUOUS-RESULT"}'))
        producer = ProbabilityIssuerReadRequestV1("COMPUTATION", scope, (result_ref,), "SYNTHETIC::COMPUTATION")
        calls = []
        @contextmanager
        def synthetic_environment(**kwargs):
            assert kwargs["deadline_ns"] == deadline and kwargs["valid_until_ns"] <= cut.valid_until_ns
            yield
        def original_partition_port(original_source, original_snapshot, original_parameters, *, target_kind):
            assert original_source is source and original_snapshot is snapshot
            assert original_parameters is source["continuous_parameters"] and target_kind == "CONTINUOUS"
        native_failure = ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "SYNTHETIC interface failure prefix")
        def numerical_port(**kwargs):
            calls.append(kwargs)
            assert kwargs["fit_clusters"] is parameters["fit_clusters"]
            assert kwargs["calibration_clusters"] is parameters["calibration_clusters"]
            assert kwargs["resource_envelope"] is parameters["resource_envelope"]
            assert kwargs["replicate_count"] == 1000 and kwargs["unit"] == parameters["unit"]
            assert (kwargs["max_model_bytes"], kwargs["max_record_bytes"], kwargs["max_total_bank_bytes"]) == (50_000, 256, 2_000_000)
            if mode == "prefix-failure":
                kwargs["work"]["base_fit_calls"] = 9
                kwargs["attempt"].update(state="INCOMPLETE_UNAVAILABLE", active_ordinal=7,
                    records=complete.records[:7], failure=native_failure)
                raise native_failure
            bank = unavailable if mode == "invalid-bank" else complete
            kwargs["work"].update(dict(bank.actual_fit_calls))
            if mode == "short-work":
                kwargs["work"]["base_fit_calls"] = 1
            if mode == "source-replaced":
                fence._construction_inputs_v1 = MappingProxyType(dict(source))
            kwargs["attempt"].update(state=bank.state, bank=bank)
            return bank, conformal
        with patch.object(numerical, "_probability_numerical_work_v1", synthetic_environment), \
             patch.object(numerical, "_probability_construct_continuous_bank_v1", numerical_port), \
             patch.object(consumer, "_probability_bind_prediction_partitions_v1", original_partition_port):
            call = dict(construction=(materialized, source), issuer_resolver=resolver,
                        producer_request=producer, deadline_ns=deadline)
            if mode == "complete":
                result = consumer._construct_probability_continuous_result_v1(**call)
                assert result["refit_bank"] is complete and result["diagnostic"] is conformal
                assert result["descriptive_bootstrap_bounds"] == (("query", (-476.0).hex(), (474.0).hex()),)
                assert len(result["results"]) == 1
                score = result["results"][0]
                assert (score.predicted_value, score.lower_value, score.upper_value, score.unit) == (
                    Decimal("-2"), Decimal("-98"), Decimal("94"), parameters["unit"])
                assert result["accepted"] is result["source_authentication"] is result["model_use_authorized"] is False
                assert fence._registrations[id(score)]["metadata"]["continuous_refit_bank"] is complete
                assert len(calls) == 1 and entry["metadata"]["continuous_attempt"]["work"]["base_fit_calls"] == 1001
                assert entry["metadata"]["continuous_attempt"]["state"] == "RESEARCH_RESULT_REGISTERED"
            else:
                with pytest.raises((ContractValidationError, OwnerAdapterError)) as error:
                    consumer._construct_probability_continuous_result_v1(**call)
                assert not any(row["kind"] == "CANDIDATE" for row in fence._registrations.values())
                if mode in ("different-unit", "different-B"):
                    assert calls == []
                else:
                    assert len(calls) == 1 and result_ref in fence._reserved_result_refs_v1
                    retained = entry["metadata"]["continuous_attempt"]
                    assert retained["state"] == "UNAVAILABLE_RETAINED_ATTEMPT" and retained["failure"] is error.value
                    if mode == "prefix-failure":
                        assert error.value is native_failure and retained["failure"] is native_failure
                        assert retained["work"]["base_fit_calls"] == 9
                        assert retained["numerical_attempt"]["records"] == complete.records[:7]
                    if mode == "invalid-bank":
                        assert retained["bank"] is unavailable and retained["state"] == "UNAVAILABLE_RETAINED_ATTEMPT"
