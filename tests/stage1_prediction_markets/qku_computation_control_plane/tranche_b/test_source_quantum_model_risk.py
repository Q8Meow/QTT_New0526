import ast
import json
import math
from collections import Counter
from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FROZEN_ONLINE_CURRENTIZATION_RECEIPTS,
    NUMERIC_VALUE_AUTHORITY_BINDINGS,
    PRIMARY_SOURCE_REGISTRY,
    SOURCE_CONFLICT_RESOLUTIONS,
    SOURCE_CURRENTIZATION_REGISTRY,
    SOURCE_POPULATION_COUNTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    invoke_formula_v34,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    GOLDEN_VECTOR_BY_MATH_ID,
    ORACLE_PACK,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (
    QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    FROZEN_FORMULA_REQUIREMENTS,
)


def test_source_and_numeric_authority_populations_are_exact() -> None:
    assert len(PRIMARY_SOURCE_REGISTRY) == 55
    assert dict(SOURCE_POPULATION_COUNTS) == {
        "EXTERNAL_PRIMARY_OR_OFFICIAL_SOURCE": 24,
        "OWNER_FORMAL_DERIVATION": 30,
        "OWNER_ARCHITECTURE_OR_POLICY": 1,
    }
    assert len(SOURCE_CONFLICT_RESOLUTIONS) == 1
    assert len(SOURCE_CURRENTIZATION_REGISTRY) == 7
    assert len(FROZEN_ONLINE_CURRENTIZATION_RECEIPTS) == 5
    assert len(NUMERIC_VALUE_AUTHORITY_BINDINGS) == 621
    assert Counter(
        row.subject_kind for row in NUMERIC_VALUE_AUTHORITY_BINDINGS.values()
    ) == {"PARAMETER": 479, "FORMULA_INPUT": 142}
    assert all(
        row.source_semantics_do_not_authenticate_runtime_number
        for row in NUMERIC_VALUE_AUTHORITY_BINDINGS.values()
    )


def test_polymarket_conflict_retains_evidence_and_runtime_numeric_owner() -> None:
    conflict = next(iter(SOURCE_CONFLICT_RESOLUTIONS.values()))

    assert conflict.source_ids == (
        "SRC-POLYMARKET-GLOBAL-FEES-2026-07-29",
        "SRC-POLYMARKET-HELP-MAKER-REBATES-2026-07-29",
        "SRC-POLYMARKET-HELP-TRADING-FEES-2026-07-29",
    )
    assert len(conflict.conflicting_atoms) == 3
    assert {
        atom["maker_rebate_share"] for atom in conflict.conflicting_atoms
    } == {"25%", "20%", "15%"}
    assert (
        conflict.numeric_value_authority
        == "PolymarketPerMarketFeeCapabilityOrHealthSnapshotV1"
    )
    assert conflict.terminal_state == "RESOLVED_TO_RUNTIME_BINDING_REQUIRED"
    assert "builder fees remain separate and additive" in conflict.resolution


def test_frozen_online_receipts_are_build_evidence_not_runtime_fetchers() -> None:
    assert all(
        row.live_refetch_state == "SUCCEEDED_2026-07-29"
        and row.retrieved_date == "2026-07-29"
        for row in FROZEN_ONLINE_CURRENTIZATION_RECEIPTS.values()
    )

    package_root = Path(
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
    )
    runtime_modules = (
        "bindings.py",
        "contextual_computability.py",
        "input_resolver.py",
        "service.py",
        "source_policy.py",
        "stack_resolver.py",
    )
    forbidden_imports = {
        "httpx",
        "requests",
        "urllib",
        "zipfile",
        "webbrowser",
    }
    from tools.validate_no_runtime_artifacts import kalshi_fee_native_admission_v1

    owner_path = (
        "src/qtt/stage1_prediction_markets/"
        "qku_computation_control_plane/source_policy.py"
    )

    def rejected_imports(relative: str, tree: ast.Module):
        admitted, admission_errors = kalshi_fee_native_admission_v1(relative, tree)
        quote_nodes = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "urllib.parse"
            and node.level == 0
            and tuple((alias.name, alias.asname) for alias in node.names)
            == (("quote", None),)
        ]
        quote_node = (
            quote_nodes[0]
            if relative == owner_path
            and not admission_errors
            and len(admitted) == 2
            and {position[0] for position in admitted} == {"Import", "Call"}
            and len(quote_nodes) == 1
            else None
        )
        imports = set()
        for node in ast.walk(tree):
            if node is quote_node:
                continue
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.module or "").split(".", 1)[0])
        return imports & forbidden_imports, admission_errors

    for name in runtime_modules:
        path = package_root / name
        blocked, errors = rejected_imports(
            path.as_posix(), ast.parse(path.read_text(encoding="utf-8"))
        )
        assert not errors, (name, errors)
        assert not blocked, (name, blocked)

    # Reuse the existing independent test literal without copying its template.
    fixture_tree = ast.parse(Path(
        "tests/source_evidence/"
        "test_source_fact_binding_connector_semantic_readiness_static.py"
    ).read_text(encoding="utf-8"))
    fixture_values = [
        node.value for node in fixture_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name)
                and target.id == "_KALSHI_INDEPENDENT_NATIVE_TEMPLATE"
                for target in node.targets)
    ]
    assert len(fixture_values) == 1
    receiver = ast.literal_eval(fixture_values[0])
    assert isinstance(receiver, str)
    quote = "from urllib.parse import quote\n"
    approved = quote + receiver
    assert rejected_imports(owner_path, ast.parse("x = 1")) == (set(), ())
    assert rejected_imports(owner_path, ast.parse(quote + "x = 1")) == ({"urllib"}, ())
    assert rejected_imports(owner_path, ast.parse(approved)) == (set(), ())
    positions, errors = kalshi_fee_native_admission_v1(owner_path, ast.parse(approved))
    assert len(positions) == 2 and errors == ()
    assert {position[0] for position in positions} == {"Import", "Call"}

    for declaration in (
        quote + quote,
        "from urllib.parse import quote as quote\n",
        "from urllib.parse import quote as encoded\n",
        quote + "from urllib.parse import quote as encoded\n",
        "from urllib.parse import quote, urlencode\n",
        "from urllib.parse import quote, quote\n",
        "from .urllib.parse import quote\n",
        "from ..urllib.parse import quote\n",
        "from urllib.parse import *\n",
        "import urllib\n",
        "import urllib.parse\n",
        "from urllib import parse\n",
    ):
        assert rejected_imports(owner_path, ast.parse(declaration + receiver)) == (
            {"urllib"}, ()
        )
    for wrong_path in (
        (package_root / "bindings.py").as_posix(),
        owner_path.upper(),
        owner_path + ".copy",
    ):
        assert rejected_imports(wrong_path, ast.parse(approved)) == ({"urllib"}, ())
    for extra, expected_root in (
        ("\nimport urllib.request\n", "urllib"),
        ("\nfrom urllib.request import urlopen\n", "urllib"),
        ("\nimport httpx\n", "httpx"),
        ("\nimport requests\n", "requests"),
        ("\nimport zipfile\n", "zipfile"),
        ("\nimport webbrowser\n", "webbrowser"),
    ):
        assert rejected_imports(owner_path, ast.parse(approved + extra)) == (
            {expected_root}, ()
        )
    for malformed in (
        receiver.replace('"GET"', '"POST"'),
        receiver.replace("import http.client", "pass"),
        receiver.replace("connection.close()", "pass"),
        receiver + receiver,
    ):
        blocked, errors = rejected_imports(owner_path, ast.parse(quote + malformed))
        assert errors
        assert "urllib" in blocked


def test_latency_classes_are_exactly_eight_point_in_time_and_22_nearline() -> None:
    by_latency = {
        latency: tuple(
            row.math_spec_id
            for row in FROZEN_FORMULA_REQUIREMENTS.values()
            if row.raw["latency_class"] == latency
        )
        for latency in {
            str(row.raw["latency_class"])
            for row in FROZEN_FORMULA_REQUIREMENTS.values()
        }
    }

    assert by_latency["POINT_IN_TIME"] == (
        "MATH-01",
        "MATH-02",
        "MATH-03",
        "MATH-04",
        "MATH-05",
        "MATH-06",
        "MATH-07",
        "MATH-36",
    )
    assert len(by_latency["OFFLINE_OR_NEARLINE"]) == 22


def test_high_risk_model_routes_are_exact_and_independently_declared() -> None:
    rows = {
        entry.oracle.math_spec_id: json.loads(entry.oracle_row_json)
        for entry in ORACLE_PACK
    }
    high_risk_ids = tuple(
        math_id
        for math_id, row in rows.items()
        if row["secondary_route_state"] == "EXECUTABLE"
    )

    assert high_risk_ids == (
        "MATH-15",
        "MATH-16",
        "MATH-18",
        "MATH-19",
        "MATH-20",
        "MATH-21",
        "MATH-25",
        "MATH-48",
        "MATH-49",
    )
    assert all(
        rows[math_id]["secondary_route_ref"]
        == f"independent_oracle_reference/secondary_routes.py::"
        f"check_{math_id.lower().replace('-', '_')}"
        for math_id in high_risk_ids
    )
    assert all(
        row["secondary_route_state"]
        == "NOT_APPLICABLE_WITH_TYPED_REASON"
        for math_id, row in rows.items()
        if math_id not in high_risk_ids
    )


def test_quantum_readiness_is_structural_with_classical_fallback_only() -> None:
    quantum_ids = ("MATH-46", "MATH-47", "MATH-48", "MATH-49")

    assert tuple(QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID) == quantum_ids
    for math_id, row in QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID.items():
        assert row.maturity_state == "STRUCTURALLY_READY"
        assert row.structural_readiness_matches_executable_oracle is True
        assert row.qpu_or_simulator_authority is False
        assert row.classical_baseline
        assert "classical" in row.fallback.casefold()
        inputs = json.loads(GOLDEN_VECTOR_BY_MATH_ID[math_id].inputs_json)
        result = invoke_formula_v34(math_id, inputs)
        assert result is not None

    math_47 = invoke_formula_v34(
        "MATH-47",
        json.loads(GOLDEN_VECTOR_BY_MATH_ID["MATH-47"].inputs_json),
    )
    assert all(
        math.isclose(
            row["qubo_energy"],
            row["ising_energy"],
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        for row in math_47["exhaustive_parity_rows"]
    )
    math_48 = invoke_formula_v34(
        "MATH-48",
        json.loads(GOLDEN_VECTOR_BY_MATH_ID["MATH-48"].inputs_json),
    )
    assert (
        math_48["conversion_penalty_adequacy"][
            "matches_native_feasible_optimum"
        ]
        is True
    )
    math_49 = invoke_formula_v34(
        "MATH-49",
        json.loads(GOLDEN_VECTOR_BY_MATH_ID["MATH-49"].inputs_json),
    )
    assert math_49["one_hot_expansion_applied"] is False
