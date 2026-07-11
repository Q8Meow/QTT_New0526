from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import CARD_NAMES, EXPECTED_FAMILY_COUNTS, card_rows
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.objects import CORE_OBJECTS, DISTINCT_OBJECTS, INTEGRATED_OBJECTS
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.policy import GENERIC_TOOL_OPERATIONS, PERMANENT_QTT_LAWS, SHORT_HORIZON_FIELDS, STABLE_VALIDATOR_RULE_IDS, STRATEGY_TEMPLATES


ROOT=Path(__file__).resolve().parents[2]


def test_compact_card_object_strategy_and_policy_closure() -> None:
    assert len(CARD_NAMES)==213
    assert {family:sum(card_id.startswith(family) for card_id,_ in CARD_NAMES) for family in EXPECTED_FAMILY_COUNTS}==EXPECTED_FAMILY_COUNTS
    assert len(CORE_OBJECTS)==59 and len(INTEGRATED_OBJECTS)==191 and len(DISTINCT_OBJECTS)==233
    assert len(set(CORE_OBJECTS)&set(INTEGRATED_OBJECTS))==17
    assert len(STRATEGY_TEMPLATES)==38 and len(SHORT_HORIZON_FIELDS)==47
    assert len(STABLE_VALIDATOR_RULE_IDS)==11 and len(GENERIC_TOOL_OPERATIONS)==5 and len(PERMANENT_QTT_LAWS)==12
    assert len([row for row in card_rows() if row["formula_family"]=="J"] )==8
    assert all(row["callable_ref"] and row["no_order_authority"] and row["no_connector_read"] for row in card_rows())


def test_builder_and_validator_pass_without_external_inputs() -> None:
    build=subprocess.run([sys.executable,"tools/build_pr169_qku_formula_exp1.py","--repo-root","."],cwd=ROOT,text=True,capture_output=True,check=False)
    assert build.returncode==0,build.stdout+build.stderr
    validate=subprocess.run([sys.executable,"tools/validate_pr169_qku_formula_exp1.py","--repo-root","."],cwd=ROOT,text=True,capture_output=True,check=False)
    assert validate.returncode==0,validate.stdout+validate.stderr


def test_no_parallel_or_surface_specific_truth_and_no_qtt_digest_authority() -> None:
    root=ROOT/"docs/master_plan/generated/pr169_qku_formula_exp1"
    names={path.name for path in root.iterdir()}
    assert not any(token in name for name in names for token in ("_future","_hint","_maybe","mobile","telegram","checksum","digest"))
    assert len([name for name in names if name.endswith(".report.json")])==1
