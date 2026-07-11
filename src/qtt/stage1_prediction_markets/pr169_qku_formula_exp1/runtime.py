from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import math
from typing import Any, Iterable, Mapping, Sequence

from .catalog import CARD_NAMES, card_rows
from .family_j import FAMILY_J_CALLABLES, FormulaDomainError


CARD_BY_ID = {card_id: name for card_id, name in CARD_NAMES}
CARD_ID_BY_NAME = {name: card_id for card_id, name in CARD_NAMES}


@dataclass(frozen=True)
class FormulaInputResolutionV1:
    resolution_id: str
    workflow_id: str
    task_id: str
    qku_id: str
    binding_id: str
    formula_id: str
    formula_version: str
    input_name: str
    required_flag: bool
    criticality: str
    expected_type: str
    expected_unit: str
    expected_basis: str
    resolved_value: Any
    resolved_type: str
    resolved_unit: str
    resolved_basis: str
    producer_value_ref: str
    freshness_state: str
    authority_class: str
    responsible_agent_id: str
    missing_state: str | None = None
    conflict_state: str | None = None


@dataclass(frozen=True)
class FormulaInvocationPlanV1:
    invocation_plan_id: str
    logical_evaluation_id: str
    qku_id: str
    ordered_formula_ids: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    input_lock_ref: str
    execution_mode: str
    fallback: str
    consumer_ref: str


@dataclass(frozen=True)
class FormulaEvaluationReceiptV1:
    logical_evaluation_id: str
    attempt_number: int
    formula_id: str
    formula_version: str
    input_lock_ref: str
    resolved_input_map: Mapping[str, Any]
    output_value: Any
    output_unit: str
    numeric_backend: str
    deterministic_state: str
    error_or_missing_input_state: str | None
    dependency_receipt_refs: tuple[str, ...]
    no_order_authority: bool = True
    no_connector_read: bool = True


def _finite(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FormulaDomainError(f"DOMAIN_VIOLATION:{name}") from exc
    if not math.isfinite(result):
        raise FormulaDomainError(f"NUMERICAL_ERROR:{name}")
    return result


def _values(inputs: Mapping[str, Any], key: str = "values") -> list[float]:
    values = [_finite(value, key) for value in inputs.get(key, ())]
    if not values:
        raise FormulaDomainError(f"MISSING_REQUIRED_INPUT:{key}")
    return values


def _core_formula(card_id: str, inputs: Mapping[str, Any]) -> Any:
    name = CARD_BY_ID[card_id]
    if name == "TOTAL_REALIZED_NET_CASH":
        return math.fsum(_values(inputs, "realized_net_cash"))
    if name in {"BRANCH_NET_CASH", "SCENARIO_CASHFLOW_RECONCILIATION_RESIDUAL"}:
        branch = _finite(inputs["exit_or_settlement_cash"], "exit_or_settlement_cash") - _finite(inputs["entry_cash"], "entry_cash") - math.fsum(_values(inputs, "unique_costs")) + math.fsum(_values(inputs, "unique_rebates"))
        return branch if name == "BRANCH_NET_CASH" else _finite(inputs["branch_net_cash"], "branch_net_cash") - branch
    if name == "EXPECTED_NET_CASH_SCENARIO":
        probabilities, cash = _values(inputs, "probabilities"), _values(inputs, "branch_net_cash")
        if len(probabilities) != len(cash) or abs(math.fsum(probabilities) - 1.0) > 1e-9 or any(p < 0 for p in probabilities):
            raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return math.fsum(p * value for p, value in zip(probabilities, cash))
    if name == "NET_CASH_VELOCITY":
        seconds = _finite(inputs["expected_holding_seconds"], "expected_holding_seconds")
        if seconds <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:expected_holding_seconds")
        return _finite(inputs["net_cash_lcb"], "net_cash_lcb") / seconds
    if name == "CAPITAL_TIME_EFFICIENCY":
        capital, seconds = _finite(inputs["capital_at_risk"], "capital_at_risk"), _finite(inputs["expected_holding_seconds"], "expected_holding_seconds")
        if capital <= 0 or seconds <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:capital_time")
        return _finite(inputs["net_cash_lcb"], "net_cash_lcb") / (capital * seconds)
    if name == "REQUIRED_EXIT_PROFIT":
        required = [
            _finite(inputs[key], key) for key in (
                "owner_minimum_cash_profit", "round_trip_cost_uncertainty_hurdle",
                "capital_opportunity_cost_hurdle", "risk_reserve_hurdle"
            )
        ]
        required.append(_finite(inputs["minimum_profit_bps"], "minimum_profit_bps") * _finite(inputs["deployed_capital"], "deployed_capital") / 10000.0)
        return max(required)
    if name in {"DEPTH_WALK_SELL_PROCEEDS", "DEPTH_WALK_BUY_COST"}:
        requested = _finite(inputs["quantity"], "quantity")
        levels = inputs.get("levels", ())
        remaining, gross = requested, 0.0
        for level in levels:
            take = min(remaining, _finite(level["quantity"], "level_quantity"))
            gross += take * _finite(level["price"], "level_price")
            remaining -= take
            if remaining <= 0: break
        filled = requested - remaining
        return {"gross_cash": gross, "fillable_quantity": filled, "vwap": gross / filled if filled else None}
    if name in {"NO_TRADE_MARGIN", "OBJECTIVE_GAP", "ECONOMIC_UTILITY_GAP", "CHAMPION_CHALLENGER_REGRET", "CAPITAL_TIME_ROTATION", "CANCEL_REPLACE_VALUE", "REVERSE_ANNEAL_IMPROVEMENT", "POSTPROCESSING_IMPROVEMENT"}:
        return _finite(inputs["left"], "left") - _finite(inputs["right"], "right")
    if name in {"ORDERBOOK_IMBALANCE", "CAPITAL_UTILIZATION", "FEASIBLE_SAMPLE_RATE", "CHAIN_BREAK_FRACTION", "OPTIMIZATION_TARGET_SUCCESS_RATE"}:
        numerator, denominator = _finite(inputs["numerator"], "numerator"), _finite(inputs["denominator"], "denominator")
        if denominator <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:denominator")
        return numerator / denominator
    if name == "MICROPRICE":
        bid, ask = _finite(inputs["best_bid"], "best_bid"), _finite(inputs["best_ask"], "best_ask")
        bid_size, ask_size = _finite(inputs["bid_size"], "bid_size"), _finite(inputs["ask_size"], "ask_size")
        if bid_size + ask_size <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:book_size")
        return (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
    if name == "FILL_SURVIVAL_HAZARD":
        integrated = math.fsum(_values(inputs, "hazard_increments"))
        if integrated < 0: raise FormulaDomainError("DOMAIN_VIOLATION:hazard")
        return 1.0 - math.exp(-integrated)
    if name == "BRIER_SCORE":
        probabilities, outcomes = _values(inputs, "probabilities"), _values(inputs, "outcomes")
        if len(probabilities) != len(outcomes) or any(not 0 <= p <= 1 for p in probabilities): raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return math.fsum((p-y)**2 for p,y in zip(probabilities,outcomes))/len(probabilities)
    if name == "LOG_LOSS":
        probabilities, outcomes = _values(inputs, "probabilities"), _values(inputs, "outcomes")
        if len(probabilities) != len(outcomes) or any(not 0 < p < 1 for p in probabilities): raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return -math.fsum(y*math.log(p)+(1-y)*math.log(1-p) for p,y in zip(probabilities,outcomes))/len(probabilities)
    if name == "WEIGHTED_EFFECTIVE_SAMPLE_SIZE":
        weights = _values(inputs, "weights")
        if any(w < 0 for w in weights) or math.fsum(w*w for w in weights) == 0: raise FormulaDomainError("DOMAIN_VIOLATION:weights")
        return math.fsum(weights)**2 / math.fsum(w*w for w in weights)
    if name in {"BENJAMINI_HOCHBERG_FDR", "BENJAMINI_YEKUTIEL_FDR"}:
        p_values, q = _values(inputs, "p_values"), _finite(inputs["q"], "q")
        if any(not 0 <= p <= 1 for p in p_values) or not 0 < q < 1: raise FormulaDomainError("DOMAIN_VIOLATION:p_values_or_q")
        ordered = sorted(enumerate(p_values), key=lambda item: item[1])
        harmonic = math.fsum(1/i for i in range(1,len(p_values)+1)) if name.endswith("YEKUTIELI_FDR") else 1.0
        selected = [index for rank,(index,p) in enumerate(ordered,1) if p <= rank*q/(len(p_values)*harmonic)]
        cutoff = max((p_values[index] for index in selected), default=-1.0)
        return {"selected_indices": sorted(index for index,p in enumerate(p_values) if p <= cutoff), "cutoff": cutoff}
    if name in {"FINANCIAL_LOSS_CVAR", "LIQUIDITY_ADJUSTED_CVAR"}:
        losses, alpha = _values(inputs, "losses"), _finite(inputs["alpha"], "alpha")
        if not 0 < alpha < 1: raise FormulaDomainError("DOMAIN_VIOLATION:alpha")
        weights = [_finite(v,"weights") for v in inputs.get("weights", [1/len(losses)]*len(losses))]
        if len(weights)!=len(losses) or any(w<0 for w in weights) or abs(math.fsum(weights)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:weights")
        candidates = sorted(set(losses))
        return min(eta + math.fsum(w*max(loss-eta,0) for w,loss in zip(weights,losses))/(1-alpha) for eta in candidates)
    if name == "EXPOSURE_HERFINDAHL":
        shares = _values(inputs, "shares")
        if any(s<0 for s in shares) or abs(math.fsum(shares)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:shares")
        return math.fsum(s*s for s in shares)
    if name == "DIVERSIFICATION_ENTROPY":
        shares = _values(inputs, "shares")
        if any(s<0 for s in shares) or abs(math.fsum(shares)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:shares")
        entropy=-math.fsum(s*math.log(s) for s in shares if s>0)
        return {"entropy":entropy,"effective_count":math.exp(entropy)}
    if name == "MAX_DRAWDOWN":
        values=_values(inputs,"equity")
        peak=values[0]; drawdown=0.0
        for value in values: peak=max(peak,value); drawdown=max(drawdown,peak-value)
        return drawdown
    if name in {"OUTCOME_SUM_CONSISTENCY", "COMPLEMENT_CONSISTENCY"}:
        return math.fsum(_values(inputs, "probabilities")) - 1.0
    if name in {"LOGICAL_IMPLICATION", "DATE_MONOTONICITY", "SUBSET_SUPERSET"}:
        return _finite(inputs["probability_subset"],"probability_subset")-_finite(inputs["probability_superset"],"probability_superset")
    if name == "INTERSECTION_BOUND":
        return _finite(inputs["probability_intersection"],"probability_intersection")-min(_finite(inputs["probability_a"],"probability_a"),_finite(inputs["probability_b"],"probability_b"))
    if name == "SELECTION_OVERLAP":
        left,right=set(inputs.get("left",())),set(inputs.get("right",()))
        union=left|right
        return 1.0 if not union else len(left&right)/len(union)
    if name == "SOLUTION_ENTROPY":
        probabilities=_values(inputs,"probabilities")
        if any(p<0 for p in probabilities) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return -math.fsum(p*math.log(p) for p in probabilities if p>0)
    if name == "QUANTUM_TIME_TO_SOLUTION":
        probability=_finite(inputs["p_success"],"p_success"); target=_finite(inputs["p_target"],"p_target"); run=_finite(inputs["run_seconds"],"run_seconds")
        if not 0<=probability<=1 or not 0<target<1 or run<=0: raise FormulaDomainError("DOMAIN_VIOLATION:tts")
        runs=math.inf if probability==0 else 1 if probability==1 else math.ceil(math.log(1-target)/math.log(1-probability))
        return {"required_runs":runs,"time_to_solution":math.inf if math.isinf(runs) else runs*run}
    if name == "PARETO_DOMINANCE":
        left,right=inputs["left"],inputs["right"]; senses=inputs["senses"]
        no_worse=[]; better=[]
        for a,b,sense in zip(left,right,senses):
            if sense=="MAXIMIZE": no_worse.append(a>=b); better.append(a>b)
            else: no_worse.append(a<=b); better.append(a<b)
        return all(no_worse) and any(better)
    if name == "FORMULA_INPUT_RESOLUTION_COVERAGE":
        rows=list(inputs.get("requirements",()))
        required=[row for row in rows if row.get("required")]
        resolved=[row for row in required if row.get("resolved_valid")]
        return {"coverage":len(resolved)/max(len(required),1),"critical_missing_count":sum(bool(row.get("critical")) and not row.get("resolved_valid") for row in required),"missing_fields":[row.get("name") for row in required if not row.get("resolved_valid")]}
    if name == "FORMULA_RESULT_FRESHNESS":
        reference=_finite(inputs["reference_time"],"reference_time"); windows=list(inputs.get("windows",()))
        if not windows: raise FormulaDomainError("MISSING_REQUIRED_INPUT:windows")
        remaining=[_finite(row["valid_until"],"valid_until")-reference for row in windows]
        ratios=[max(0.0,min(1.0,remain/_finite(row["ttl"],"ttl"))) for remain,row in zip(remaining,windows)]
        return {"result_remaining_ttl":min(remaining),"result_freshness":min(ratios),"fresh":min(remaining)>=0}
    if name == "END_TO_END_DECISION_LATENCY":
        components={key:_finite(value,key) for key,value in dict(inputs.get("components",{})).items()}
        return {"total_decision_latency_ms":math.fsum(components.values()),"components":components,"reconciliation_residual":0.0}
    if name == "LATENCY_BUDGET_SLACK":
        total=_finite(inputs["total_decision_latency_ms"],"total_decision_latency_ms")
        latency=_finite(inputs["latency_budget_ms"],"latency_budget_ms")-total
        ttl=_finite(inputs["min_material_valid_until_ms"],"min_material_valid_until_ms")-(_finite(inputs["input_lock_time_ms"],"input_lock_time_ms")+total)
        return {"latency_slack_ms":latency,"ttl_slack_ms":ttl,"latency_pass":latency>=0 and ttl>=0}
    if name == "FORMULA_WORK_ITEM_PRIORITY_VECTOR":
        return tuple(inputs[key] for key in ("severity_desc","economic_ttl_asc","hard_dependency_block_count_desc","downstream_blocked_value_desc","value_of_information_per_compute_desc","queue_age_desc","deterministic_tie_break_key_asc"))
    # Existing central callables own these equivalent aliases. The generic
    # interface fails closed until their exact resolved output is supplied.
    if "current_equivalent_output" not in inputs:
        raise FormulaDomainError("MISSING_REQUIRED_INPUT:current_equivalent_output")
    value=inputs["current_equivalent_output"]
    if isinstance(value,float) and not math.isfinite(value): raise FormulaDomainError("NUMERICAL_ERROR:current_equivalent_output")
    return value


def evaluate_formula(formula_id: str, version: str, resolved_input_map: Mapping[str, Any]) -> Any:
    card_id = formula_id if formula_id in CARD_BY_ID else CARD_ID_BY_NAME.get(formula_id)
    if card_id is None:
        for row in card_rows():
            if row["canonical_formula_or_procedure_id"] == formula_id:
                card_id = row["card_id"]
                break
    if card_id is None:
        raise KeyError(formula_id)
    if version != "1.0.0":
        raise FormulaDomainError("CONFLICTING_INPUTS:formula_version")
    if card_id in FAMILY_J_CALLABLES:
        return FAMILY_J_CALLABLES[card_id](resolved_input_map)
    return _core_formula(card_id, resolved_input_map)


def _topological_order(nodes: Sequence[str], edges: Sequence[tuple[str, str]]) -> tuple[str, ...]:
    incoming={node:0 for node in nodes}; outgoing={node:[] for node in nodes}
    for source,target in edges:
        if source not in incoming or target not in incoming: raise FormulaDomainError("CONFLICTING_INPUTS:dependency_edge")
        incoming[target]+=1; outgoing[source].append(target)
    ready=sorted(node for node,count in incoming.items() if count==0); ordered=[]
    while ready:
        node=ready.pop(0); ordered.append(node)
        for target in sorted(outgoing[node]):
            incoming[target]-=1
            if incoming[target]==0: ready.append(target); ready.sort()
    if len(ordered)!=len(nodes): raise FormulaDomainError("CONFLICTING_INPUTS:FORMULA_DEPENDENCY_CYCLE")
    return tuple(ordered)


class FormulaQKUService:
    """One bounded, deterministic five-operation computation interface."""

    def __init__(self, qku_rows: Iterable[Mapping[str, Any]] = ()) -> None:
        self._qku_rows=tuple(dict(row) for row in qku_rows)

    def query_applicable_qkus(self, context: Mapping[str, Any], agent_duty: str, stage: str, mode: str) -> list[dict[str, Any]]:
        result=[]
        for row in self._qku_rows:
            if row.get("agent_duties") and agent_duty not in row["agent_duties"]: continue
            if row.get("stages") and stage not in row["stages"]: continue
            if row.get("modes") and mode not in row["modes"]: continue
            if row.get("market") and row["market"] != context.get("market"): continue
            result.append(dict(row))
        limit=int(context.get("query_limit",100))
        return sorted(result,key=lambda row:str(row["qku_id"]))[:limit]

    def resolve_formula_inputs(self, plan: Mapping[str, Any], input_lock: Mapping[str, Any]) -> list[FormulaInputResolutionV1]:
        rows=[]
        for requirement in plan.get("input_requirements",()):
            name=str(requirement["name"]); producer=str(requirement.get("producer_field",name)); value=input_lock.get(producer)
            expected_unit=str(requirement.get("unit","declared")); actual_unit=str(input_lock.get("units",{}).get(producer,expected_unit))
            missing=value is None; mismatch=actual_unit!=expected_unit
            rows.append(FormulaInputResolutionV1(
                resolution_id=f"{plan['logical_evaluation_id']}:{name}",workflow_id=str(plan["workflow_id"]),task_id=str(plan["task_id"]),
                qku_id=str(plan["qku_id"]),binding_id=str(plan["binding_id"]),formula_id=str(plan["formula_id"]),formula_version=str(plan.get("formula_version","1.0.0")),
                input_name=name,required_flag=bool(requirement.get("required",True)),criticality=str(requirement.get("criticality","CRITICAL")),expected_type=str(requirement.get("type","number")),
                expected_unit=expected_unit,expected_basis=str(requirement.get("basis","declared")),resolved_value=value,resolved_type=type(value).__name__,resolved_unit=actual_unit,
                resolved_basis=str(input_lock.get("bases",{}).get(producer,requirement.get("basis","declared"))),producer_value_ref=f"{input_lock.get('input_lock_ref','input-lock')}:{producer}",
                freshness_state=str(input_lock.get("freshness",{}).get(producer,"FRESH")),authority_class=str(requirement.get("authority_class","RESOLVED_SNAPSHOT")),
                responsible_agent_id=str(plan["responsible_agent_id"]),missing_state="MISSING_REQUIRED_INPUT" if missing and requirement.get("required",True) else None,
                conflict_state="UNIT_MISMATCH" if mismatch else None,
            ))
        return rows

    def evaluate_formula(self, formula_id: str, version: str, resolved_input_map: Mapping[str, Any], *, logical_evaluation_id: str, input_lock_ref: str, attempt_number: int=1) -> FormulaEvaluationReceiptV1:
        try:
            output=evaluate_formula(formula_id,version,resolved_input_map); error=None
        except FormulaDomainError as exc:
            output=None; error=str(exc).split(":",1)[0]
        return FormulaEvaluationReceiptV1(logical_evaluation_id,attempt_number,formula_id,version,input_lock_ref,dict(resolved_input_map),output,str(resolved_input_map.get("output_unit","declared")),"PYTHON_STDLIB_DETERMINISTIC","DETERMINISTIC",error,())

    def evaluate_qku_dag(self, qku_id: str, binding_set: Sequence[Mapping[str, Any]], input_lock: Mapping[str, Any]) -> list[FormulaEvaluationReceiptV1]:
        nodes=[str(row["formula_id"]) for row in binding_set]; edges=[tuple(edge) for row in binding_set for edge in row.get("dependency_edges",())]
        ordered=_topological_order(nodes,edges); by_id={str(row["formula_id"]):row for row in binding_set}; receipts=[]; values=dict(input_lock)
        for formula_id in ordered:
            row=by_id[formula_id]; mapped={name:values[source] for name,source in row.get("input_map",{}).items() if source in values}
            receipt=self.evaluate_formula(formula_id,str(row.get("version","1.0.0")),mapped,logical_evaluation_id=str(input_lock["logical_evaluation_id"]),input_lock_ref=str(input_lock["input_lock_ref"])); receipts.append(receipt)
            if receipt.error_or_missing_input_state is None:
                values[str(row.get("output_field",formula_id))]=receipt.output_value
        return receipts

    def evaluate_trade_plan_scenarios(self, candidate_set: Sequence[Mapping[str, Any]], scenario_set: Sequence[Mapping[str, Any]], no_trade_candidate: Mapping[str, Any]) -> dict[str, Any]:
        def utility(candidate: Mapping[str, Any]) -> float:
            values=[]
            for scenario in scenario_set:
                values.append(_finite(candidate["scenario_net_cash"][scenario["scenario_id"]],"scenario_net_cash")*_finite(scenario["probability"],"probability"))
            return math.fsum(values)-_finite(candidate.get("risk_reserve",0),"risk_reserve")
        no_trade=utility(no_trade_candidate); ranked=sorted(({"candidate_id":c["candidate_id"],"robust_utility":utility(c),"no_trade_margin":utility(c)-no_trade} for c in candidate_set),key=lambda row:(-row["robust_utility"],str(row["candidate_id"])))
        champion=ranked[0] if ranked and ranked[0]["no_trade_margin"]>0 else {"candidate_id":no_trade_candidate["candidate_id"],"robust_utility":no_trade,"no_trade_margin":0.0}
        return {"ranked_candidates":ranked,"champion":champion,"eligibility_state":"CHAMPION_ELIGIBLE" if champion["candidate_id"]!=no_trade_candidate["candidate_id"] else "DETERMINISTIC_NO_TRADE","authority_state":"CANDIDATE_ONLY_NO_ORDER_AUTHORITY"}
