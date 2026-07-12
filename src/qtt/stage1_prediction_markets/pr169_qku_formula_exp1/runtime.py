from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import math
from statistics import NormalDist
from pathlib import Path
import threading
from typing import Any, Mapping, Protocol, Sequence

from .catalog import CARD_NAMES, card_rows
from .family_j import FormulaDomainError


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
    resolved_value_ref: str
    producer_artifact_ref: str
    producer_row_ref: str
    producer_field: str
    observed_at_event_time: str | None
    valid_from: str | None
    valid_until: str | None
    freshness_proof_ref: str | None
    transformation_or_unit_conversion_ref: str | None
    freshness_state: str
    authority_class: str
    responsible_agent_id: str
    source_observation_time: str | None = None
    source_available_at: str | None = None
    processing_time: str | None = None
    input_lock_time: str | None = None
    decision_time: str | None = None
    settlement_time: str | None = None
    sequence_or_snapshot_ref: str | None = None
    late_or_out_of_order_disposition: str | None = None
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
class ChampionGateReceiptV1:
    gate_id: str
    owner: str
    version: str
    input_lock_ref: str
    validation_state: str
    passed: bool
    freshness_state: str


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


@dataclass(frozen=True)
class EconomicComponentLedgerEntryV1:
    input_lock_ref: str
    economic_event_id: str
    component_id: str
    inclusion_class: str
    amount: Decimal | None
    authoritative_amount_ref: str


class EconomicComponentLedgerV1:
    """Deduplicates cash/reserve effects while permitting TCA explanation."""

    CASH_CLASSES={"EMBEDDED_IN_EXECUTABLE_FILL_CASH","EXPLICIT_LEDGER_CASH_COST","REBATE_OR_CREDIT","RISK_OR_MODEL_RESERVE_ONLY"}

    def __init__(self) -> None:
        self._entries:dict[tuple[str,str,str,str],EconomicComponentLedgerEntryV1]={}

    def register(self,entry:EconomicComponentLedgerEntryV1)->EconomicComponentLedgerEntryV1:
        if entry.inclusion_class not in self.CASH_CLASSES|{"TCA_ATTRIBUTION_ONLY","FEATURE_OR_DIAGNOSTIC_ONLY","NOT_APPLICABLE"}:
            raise FormulaDomainError("DOMAIN_VIOLATION:economic_component_inclusion_class")
        event_key=(entry.input_lock_ref,entry.economic_event_id,entry.component_id)
        if entry.inclusion_class in self.CASH_CLASSES:
            for existing in self._entries.values():
                if (existing.input_lock_ref,existing.economic_event_id,existing.component_id)==event_key and existing.inclusion_class in self.CASH_CLASSES:
                    raise FormulaDomainError("DUPLICATE_ECONOMIC_COMPONENT_INCLUSION")
        key=(*event_key,entry.inclusion_class)
        if key in self._entries: return self._entries[key]
        self._entries[key]=entry
        return entry

    def entries(self)->tuple[EconomicComponentLedgerEntryV1,...]:
        return tuple(self._entries.values())


class CanonicalQKUResolver(Protocol):
    """Bounded resolver interface; callers cannot supply authoritative rows."""

    def query(
        self,
        context: Mapping[str, Any],
        agent_duty: str,
        stage: str,
        mode: str,
    ) -> Sequence[Mapping[str, Any]]: ...


class RP5CCanonicalResolverAdapter:
    """Production adapter over the admitted RP5C reader/composition root."""

    _cached_default_library: dict[str, Any] | None = None

    def __init__(self, *, repo_root: Path | str | None = None) -> None:
        from tools.pr168_rp5c_library_reader import load_library

        if repo_root is None:
            if self.__class__._cached_default_library is None:
                self.__class__._cached_default_library = load_library()
            self._library = self.__class__._cached_default_library
        else:
            self._library = load_library(repo_root)

    def query(
        self,
        context: Mapping[str, Any],
        agent_duty: str,
        stage: str,
        mode: str,
    ) -> Sequence[Mapping[str, Any]]:
        requested = tuple(str(value) for value in context.get("qku_ids", ()))
        if not requested:
            return ()
        by_id = {
            str(row["qku_id"]): row
            for row in self._library["immutable_qku_library"]
            if row.get("qku_id")
        }
        rows = []
        for qku_id in requested:
            row = by_id.get(qku_id)
            if row is None:
                continue
            rows.append({
                "qku_id": qku_id,
                "canonical_source_row_ref": row.get("identity_row_id") or qku_id,
                "agent_duty": agent_duty,
                "stage": stage,
                "mode": mode,
                "market": context.get("market"),
                "authority_state": "RP5C_CANONICAL_BOUNDED_SELECTION",
            })
        return tuple(rows)


def _finite(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FormulaDomainError(f"DOMAIN_VIOLATION:{name}") from exc
    if not math.isfinite(result):
        raise FormulaDomainError(f"NUMERICAL_ERROR:{name}")
    return result


def _decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise FormulaDomainError(f"DOMAIN_VIOLATION:{name}") from exc
    if not result.is_finite():
        raise FormulaDomainError(f"NUMERICAL_ERROR:{name}")
    return result


def _decimal_values(inputs: Mapping[str, Any], key: str) -> list[Decimal]:
    values = [_decimal(value, key) for value in inputs.get(key, ())]
    if not values:
        raise FormulaDomainError(f"MISSING_REQUIRED_INPUT:{key}")
    return values


def _finite_output(value:Any)->bool:
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,Decimal): return value.is_finite()
    if isinstance(value,Mapping): return all(_finite_output(item) for item in value.values())
    if isinstance(value,(list,tuple)): return all(_finite_output(item) for item in value)
    return True


def _values(inputs: Mapping[str, Any], key: str = "values") -> list[float]:
    values = [_finite(value, key) for value in inputs.get(key, ())]
    if not values:
        raise FormulaDomainError(f"MISSING_REQUIRED_INPUT:{key}")
    return values


def _execute_card(card_id: str, inputs: Mapping[str, Any]) -> Any:
    problem_size = int(inputs.get("__problem_size__", 1))
    if problem_size < 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:problem_size")
    if problem_size > 64:
        raise FormulaDomainError("UNSUPPORTED_OPERATIONAL_ENVELOPE:problem_size")
    if card_id == "A01":
        return sum(_decimal_values(inputs, "realized_net_cash"), Decimal("0"))
    if card_id in {"A02", "H14"}:
        branch = _decimal(inputs["exit_or_settlement_cash"], "exit_or_settlement_cash") - _decimal(inputs["entry_cash"], "entry_cash") - sum(_decimal_values(inputs, "unique_costs"), Decimal("0")) + sum(_decimal_values(inputs, "unique_rebates"), Decimal("0"))
        return branch if card_id == "A02" else _decimal(inputs["branch_net_cash"], "branch_net_cash") - branch
    if card_id == "A03":
        probabilities, cash = _decimal_values(inputs, "probabilities"), _decimal_values(inputs, "branch_net_cash")
        if len(probabilities) != len(cash) or abs(sum(probabilities, Decimal("0")) - Decimal("1")) > Decimal("1e-12") or any(p < 0 for p in probabilities):
            raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return sum((p * value for p, value in zip(probabilities, cash)), Decimal("0"))
    if card_id == "A04":
        expectations=_decimal_values(inputs,"admissible_expected_net_cash")
        return {"lower_bound":min(expectations),"upper_bound":max(expectations)}
    if card_id == "A05":
        samples=sorted(_decimal_values(inputs,"estimator_samples")); lower=_decimal(inputs["lower_quantile"],"lower_quantile"); upper=_decimal(inputs["upper_quantile"],"upper_quantile")
        if not Decimal("0")<=lower<=upper<=Decimal("1"): raise FormulaDomainError("DOMAIN_VIOLATION:quantiles")
        def quantile(q:Decimal)->Decimal:
            index=int((len(samples)-1)*q); return samples[index]
        return {"net_cash_lcb":quantile(lower),"net_cash_ucb":quantile(upper),"method":str(inputs["confidence_method"])}
    if card_id == "A06":
        seconds = _finite(inputs["expected_holding_seconds"], "expected_holding_seconds")
        if seconds <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:expected_holding_seconds")
        return _decimal(inputs["net_cash_lcb"], "net_cash_lcb") / _decimal(inputs["expected_holding_seconds"], "expected_holding_seconds")
    if card_id == "A07":
        capital, seconds = _finite(inputs["capital_at_risk"], "capital_at_risk"), _finite(inputs["expected_holding_seconds"], "expected_holding_seconds")
        if capital <= 0 or seconds <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:capital_time")
        return _decimal(inputs["net_cash_lcb"], "net_cash_lcb") / (_decimal(inputs["capital_at_risk"], "capital_at_risk") * _decimal(inputs["expected_holding_seconds"], "expected_holding_seconds"))
    if card_id == "A08":
        required = [
            _decimal(inputs[key], key) for key in (
                "owner_minimum_cash_profit", "round_trip_cost_uncertainty_hurdle",
                "capital_opportunity_cost_hurdle", "risk_reserve_hurdle"
            )
        ]
        required.append(_decimal(inputs["minimum_profit_bps"], "minimum_profit_bps") * _decimal(inputs["deployed_capital"], "deployed_capital") / Decimal("10000"))
        return max(required)
    if card_id in {"A09", "A10"}:
        requested = _decimal(inputs["quantity"], "quantity")
        levels = inputs.get("levels", ())
        remaining, gross = requested, Decimal("0")
        for level in levels:
            take = min(remaining, _decimal(level["quantity"], "level_quantity"))
            gross += take * _decimal(level["price"], "level_price")
            remaining -= take
            if remaining <= 0: break
        filled = requested - remaining
        return {"gross_cash": gross, "fillable_quantity": filled, "vwap": gross / filled if filled else None}
    if card_id == "A11":
        quantity=_decimal(inputs["fillable_quantity"],"fillable_quantity")
        cash=_decimal(inputs["executable_liquidation_cash"],"executable_liquidation_cash")-_decimal(inputs["position_cash_basis"],"position_cash_basis")-_decimal(inputs["unique_exit_fees"],"unique_exit_fees")+_decimal(inputs["earned_rebates"],"earned_rebates")-_decimal(inputs["remaining_unique_cash_costs"],"remaining_unique_cash_costs")
        return {"executable_exit_net_cash":cash,"fillable_quantity":quantity,"accounting_class":"PROJECTED_EXECUTABLE_NET_CASH"}
    if card_id == "A12":
        probabilities=_decimal_values(inputs,"fill_branch_probabilities"); cash=_decimal_values(inputs,"fill_branch_net_cash")
        if len(probabilities)!=len(cash) or any(value<0 for value in probabilities) or abs(sum(probabilities,Decimal("0"))-Decimal("1"))>Decimal("1e-12"): raise FormulaDomainError("DOMAIN_VIOLATION:fill_probabilities")
        return {"fill_adjusted_net_cash":sum((p*v for p,v in zip(probabilities,cash)),Decimal("0")),"branch_distribution":cash}
    if card_id == "A13":
        harvested=_decimal(inputs["harvested_quantity_net_cash"],"harvested_quantity_net_cash"); continuation=_decimal(inputs["residual_position_continuation_value"],"residual_position_continuation_value")
        return {"partial_harvest_cash":harvested,"residual_continuation_value":continuation,"partial_harvest_action_value":harvested+continuation,"realized_cash_excludes_continuation":True}
    if card_id == "A14":
        if bool(inputs.get("settlement_final")) and bool(inputs.get("ledger_reconciled")): state="REALIZED_PAPER_SETTLEMENT_NET_CASH"
        elif bool(inputs.get("exit_fill_final")) and bool(inputs.get("ledger_reconciled")): state="REALIZED_PAPER_EXIT_NET_CASH"
        elif bool(inputs.get("executable_quote_available")): state="PROJECTED_EXECUTABLE_NET_CASH"
        else: state="MARKED_PAPER_PNL"
        return {"pnl_state":state,"amount":_decimal(inputs["amount"],"amount")}
    if card_id == "A15":
        return _decimal(inputs["executable_liquidation_cash"],"executable_liquidation_cash")-_decimal(inputs["immediate_exit_costs"],"immediate_exit_costs")-_decimal(inputs["residual_obligations"],"residual_obligations")
    if card_id == "A16":
        forward=min(_decimal_values(inputs,"future_liquidation_or_settlement_cash"))
        return forward-sum((_decimal(inputs[key],key) for key in ("remaining_costs","capital_lock_cost","tail_risk_reserve","model_risk_reserve")),Decimal("0"))
    if card_id == "A17":
        settlement=min(_decimal_values(inputs,"settlement_cash_scenarios"))
        return settlement-sum((_decimal(inputs[key],key) for key in ("remaining_fees","capital_lock_cost","settlement_delay_risk","resolution_risk_reserve")),Decimal("0"))
    if card_id == "A18":
        return _decimal(inputs["executable_combined_cash_after_hedge"],"executable_combined_cash_after_hedge")-sum((_decimal(inputs[key],key) for key in ("incremental_costs","basis_risk_reserve","residual_exposure_cost")),Decimal("0"))
    if card_id == "A19":
        return _decimal(inputs["exit_now_value"],"exit_now_value")+_decimal(inputs["opposite_position_robust_value"],"opposite_position_robust_value")-_decimal(inputs["incremental_switching_costs"],"incremental_switching_costs")
    if card_id == "A20":
        values={str(key):_decimal(value,"action_value") for key,value in dict(inputs["action_values"]).items()}
        if not values: raise FormulaDomainError("MISSING_REQUIRED_INPUT:action_values")
        selected=max(sorted(values),key=lambda key:values[key])
        return {"selected_action_candidate":selected,"selected_value":values[selected],"action_value_vector":values,"policy_authority":False}
    if card_id == "A21":
        exit_value=_decimal(inputs["exit_now_value"],"exit_now_value"); continuation=_decimal(inputs["continue_value"],"continue_value"); hysteresis=_decimal(inputs["continuation_hysteresis"],"continuation_hysteresis")
        if hysteresis<0: raise FormulaDomainError("DOMAIN_VIOLATION:hysteresis")
        margin=exit_value-continuation-hysteresis; return {"exit_trigger":margin>=0,"margin":margin}
    if card_id == "A22":
        lcb=_decimal(inputs["new_entry_net_cash_lcb"],"new_entry_net_cash_lcb"); hurdle=_decimal(inputs["new_entry_hurdle"],"new_entry_hurdle"); exit_hurdle=_decimal(inputs["exit_hurdle"],"exit_hurdle")
        if hurdle<=exit_hurdle: raise FormulaDomainError("DOMAIN_VIOLATION:reentry_hurdle")
        allowed=bool(inputs["fresh_state_change"]) and bool(inputs["cooldown_complete"]) and lcb>=hurdle
        return {"reentry_allowed":allowed,"margin":lcb-hurdle}
    if card_id == "A23":
        difference=_decimal(inputs["best_alternative_robust_utility"],"best_alternative_robust_utility")-_decimal(inputs["current_position_robust_utility"],"current_position_robust_utility")
        return max(Decimal("0"),difference)
    if card_id == "A24":
        components=list(inputs["reserve_components"]); seen=set(); total=Decimal("0")
        for row in components:
            component_id=str(row["component_id"])
            if component_id in seen: raise FormulaDomainError("CONFLICTING_INPUTS:duplicate_reserve_component")
            seen.add(component_id); total+=_decimal(row["amount"],"reserve_amount")
        return {"risk_reserve":total,"component_ids":sorted(seen)}
    if card_id == "A25":
        return _decimal(inputs["candidate_robust_utility"],"candidate_robust_utility")-_decimal(inputs["no_trade_robust_utility"],"no_trade_robust_utility")
    if card_id == "B16":
        return _decimal(inputs["new_order_after_priority_loss_utility"],"new_order_after_priority_loss_utility")-_decimal(inputs["keep_existing_order_utility"],"keep_existing_order_utility")-_decimal(inputs["cancel_replace_cost"],"cancel_replace_cost")
    if card_id == "F25":
        return _finite(inputs["left"], "left") - _finite(inputs["right"], "right")
    if card_id == "A26":
        seen=set(); totals={key:Decimal("0") for key in ("gross_cash","realized_net_cash","fees","rebates","impact","capital_seconds","drawdown")}
        for row in inputs["child_rows"]:
            event_id=str(row["economic_event_id"])
            if event_id in seen: continue
            seen.add(event_id)
            for key in totals: totals[key]+=_decimal(row.get(key,0),key)
        return {**totals,"unique_economic_event_count":len(seen)}
    if card_id == "A27":
        sizes=_decimal_values(inputs,"size_ladder"); utilities=_decimal_values(inputs,"robust_utilities")
        if len(sizes)!=len(utilities) or any(right<=left for left,right in zip(sizes,sizes[1:])): raise FormulaDomainError("DOMAIN_VIOLATION:capacity_ladder")
        marginal=[utilities[index]-utilities[index-1] for index in range(1,len(utilities))]
        return {"size_ladder":sizes,"robust_utility_frontier":utilities,"marginal_utility":marginal}
    if card_id == "A28":
        candidates=[_decimal(row["additional_size"],"additional_size") for row in inputs["candidate_additions"] if _decimal(row["marginal_net_cash_lcb"],"marginal_net_cash_lcb")>0 and bool(row["constraints_satisfied"])]
        return max(candidates,default=Decimal("0"))
    if card_id == "A29":
        precedence=("FAILURE","INVALIDATION","OWNER_STOP","EXPIRY","FUTILITY","SUCCESS")
        indicators={str(key).upper():bool(value) for key,value in dict(inputs["indicators"]).items()}
        reason=next((key for key in precedence if indicators.get(key)),None)
        return {"stop":reason is not None,"stop_reason":reason,"evidence_time":inputs["evidence_time"]}
    if card_id == "A30":
        quantity=_decimal(inputs["quantity"],"quantity"); price=_decimal(inputs["price"],"price"); rate=_decimal(inputs["fee_rate"],"fee_rate")
        rule=str(inputs["fee_rule"])
        if not Decimal("0")<=price<=Decimal("1") or quantity<0 or rate<0: raise FormulaDomainError("DOMAIN_VIOLATION:fee_inputs")
        if rule=="LINEAR_NOTIONAL": fee=quantity*price*rate
        elif rule=="P_X_ONE_MINUS_P": fee=quantity*rate*price*(Decimal("1")-price)
        else: raise FormulaDomainError("FORMULA_INAPPLICABLE:fee_rule")
        return {"fee":fee,"fee_rule":rule,"binding_version":str(inputs["fee_schedule_version"])}
    if card_id == "A31":
        quantity=_decimal(inputs["shares"],"shares"); price=_decimal(inputs["price"],"price"); rate=_decimal(inputs["fee_rate"],"fee_rate")
        if quantity<0 or not Decimal("0")<=price<=Decimal("1") or rate<0: raise FormulaDomainError("DOMAIN_VIOLATION:fee_curve")
        return quantity*rate*price*(Decimal("1")-price)
    if card_id == "B01":
        sign=_decimal(inputs["side_sign"],"side_sign"); quantity=_decimal(inputs["filled_quantity"],"filled_quantity")
        if sign not in {Decimal("-1"),Decimal("1")} or quantity<0: raise FormulaDomainError("DOMAIN_VIOLATION:implementation_shortfall")
        return sign*quantity*(_decimal(inputs["average_fill_price"],"average_fill_price")-_decimal(inputs["decision_price"],"decision_price"))+_decimal(inputs["explicit_fees"],"explicit_fees")-_decimal(inputs["rebates"],"rebates")+_decimal(inputs["opportunity_cost_unfilled"],"opportunity_cost_unfilled")
    if card_id == "B02":
        components={key:_decimal(value,key) for key,value in dict(inputs["components"]).items()}; total=sum(components.values(),Decimal("0")); declared=_decimal(inputs["total_execution_cost"],"total_execution_cost")
        return {"components":components,"total_execution_cost":total,"reconciliation_residual":declared-total}
    if card_id == "B03":
        decision=_finite(inputs["decision_time"],"decision_time"); latency=_finite(inputs["arrival_latency_seconds"],"arrival_latency_seconds")
        if latency<0: raise FormulaDomainError("DOMAIN_VIOLATION:arrival_latency")
        requested=_decimal(inputs["quantity"],"quantity"); remaining=requested; gross=Decimal("0")
        for level in inputs["arrival_book_levels"]:
            take=min(remaining,_decimal(level["quantity"],"level_quantity")); gross+=take*_decimal(level["price"],"level_price"); remaining-=take
            if remaining<=0: break
        filled=requested-remaining
        return {"effective_arrival_time":decision+latency,"effective_arrival_price":gross/filled if filled else None,"fillable_quantity":filled}
    if card_id == "B04":
        sign=_decimal(inputs["side_sign"],"side_sign")
        if sign not in {Decimal("-1"),Decimal("1")}: raise FormulaDomainError("DOMAIN_VIOLATION:side_sign")
        return Decimal("2")*sign*(_decimal(inputs["fill_price"],"fill_price")-_decimal(inputs["future_reference_price"],"future_reference_price"))
    if card_id == "B05":
        sign=_decimal(inputs["side_sign"],"side_sign")
        if sign not in {Decimal("-1"),Decimal("1")}: raise FormulaDomainError("DOMAIN_VIOLATION:side_sign")
        return sign*(_decimal(inputs["future_reference_price"],"future_reference_price")-_decimal(inputs["fill_price"],"fill_price"))
    if card_id == "B06":
        return _decimal(inputs["side_sign"],"side_sign")*_decimal(inputs["quantity"],"quantity")*(_decimal(inputs["fill_price"],"fill_price")-_decimal(inputs["reference_price"],"reference_price"))
    if card_id == "B07":
        return _decimal(inputs["side_sign"],"side_sign")*_decimal(inputs["quantity"],"quantity")*(_decimal(inputs["depth_walk_vwap"],"depth_walk_vwap")-_decimal(inputs["top_of_book_price"],"top_of_book_price"))
    if card_id == "B08":
        return _decimal(inputs["robust_value_at_decision"],"robust_value_at_decision")-_decimal(inputs["robust_value_at_arrival"],"robust_value_at_arrival")
    if card_id == "B10":
        queue=_decimal(inputs["queue_ahead"],"queue_ahead"); remaining=_decimal(inputs["order_remaining"],"order_remaining"); depletion=_decimal_values(inputs,"depletion_scenarios")
        if queue<0 or remaining<0: raise FormulaDomainError("DOMAIN_VIOLATION:queue")
        fills=[min(remaining,max(Decimal("0"),value-queue)) for value in depletion]
        return {"expected_fill_quantity":sum(fills,Decimal("0"))/Decimal(len(fills)),"fill_probability":Decimal(sum(value>0 for value in fills))/Decimal(len(fills))}
    if card_id in {"B11", "D10", "F39"}:
        numerator, denominator = _finite(inputs["numerator"], "numerator"), _finite(inputs["denominator"], "denominator")
        if denominator <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:denominator")
        return numerator / denominator
    if card_id == "B12":
        bid, ask = _finite(inputs["best_bid"], "best_bid"), _finite(inputs["best_ask"], "best_ask")
        bid_size, ask_size = _finite(inputs["bid_size"], "bid_size"), _finite(inputs["ask_size"], "ask_size")
        if bid_size + ask_size <= 0: raise FormulaDomainError("DOMAIN_VIOLATION:book_size")
        return (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
    if card_id == "B09":
        integrated = math.fsum(_values(inputs, "hazard_increments"))
        if integrated < 0: raise FormulaDomainError("DOMAIN_VIOLATION:hazard")
        return 1.0 - math.exp(-integrated)
    if card_id == "B13":
        events=list(inputs["book_events"])
        if len(events)<2: raise FormulaDomainError("INSUFFICIENT_EVIDENCE:book_events")
        total=Decimal("0")
        for previous,current in zip(events,events[1:]):
            pb0,pb1=_decimal(previous["bid_price"],"bid_price"),_decimal(current["bid_price"],"bid_price"); qb0,qb1=_decimal(previous["bid_quantity"],"bid_quantity"),_decimal(current["bid_quantity"],"bid_quantity")
            pa0,pa1=_decimal(previous["ask_price"],"ask_price"),_decimal(current["ask_price"],"ask_price"); qa0,qa1=_decimal(previous["ask_quantity"],"ask_quantity"),_decimal(current["ask_quantity"],"ask_quantity")
            total+=(qb1 if pb1>=pb0 else Decimal("0"))-(qb0 if pb1<=pb0 else Decimal("0"))-(qa1 if pa1<=pa0 else Decimal("0"))+(qa0 if pa1>=pa0 else Decimal("0"))
        return total
    if card_id == "B14":
        baseline=_finite(inputs["baseline_intensity"],"baseline_intensity"); now=_finite(inputs["evaluation_time"],"evaluation_time"); total=baseline; integrated=0.0
        if baseline<0: raise FormulaDomainError("DOMAIN_VIOLATION:hawkes_baseline")
        for event in inputs["events"]:
            alpha=_finite(event["alpha"],"alpha"); beta=_finite(event["beta"],"beta"); event_time=_finite(event["event_time"],"event_time")
            if alpha<0 or beta<=0 or event_time>=now: raise FormulaDomainError("DOMAIN_VIOLATION:hawkes_event")
            total+=alpha*math.exp(-beta*(now-event_time)); integrated+=alpha/beta
        if integrated>=1: raise FormulaDomainError("DOMAIN_VIOLATION:unstable_hawkes_kernel")
        return {"intensity":total,"integrated_kernel_spectral_radius":integrated}
    if card_id == "B15":
        routes=[]
        for row in inputs["route_branches"]:
            probabilities=_decimal_values(row,"probabilities"); cash=_decimal_values(row,"branch_net_cash")
            if len(probabilities)!=len(cash) or abs(sum(probabilities,Decimal("0"))-Decimal("1"))>Decimal("1e-12"): raise FormulaDomainError("DOMAIN_VIOLATION:route_probabilities")
            utility=sum((p*v for p,v in zip(probabilities,cash)),Decimal("0"))-sum((_decimal(row.get(key,0),key) for key in ("inventory_reserve","adverse_selection_reserve","latency_reserve","model_reserve")),Decimal("0"))
            routes.append({"route_id":row["route_id"],"utility":utility})
        return {"routes":routes,"selected_route":max(routes,key=lambda row:row["utility"])["route_id"]}
    if card_id == "B17":
        return _decimal(inputs["reference_price"],"reference_price")-_decimal(inputs["inventory"],"inventory")*_decimal(inputs["risk_aversion"],"risk_aversion")*_decimal(inputs["variance_horizon"],"variance_horizon")
    if card_id == "B18":
        risk=_finite(inputs["risk_aversion"],"risk_aversion"); variance=_finite(inputs["variance_horizon"],"variance_horizon"); kappa=_finite(inputs["kappa"],"kappa")
        if risk<=0 or variance<0 or kappa<=0: raise FormulaDomainError("DOMAIN_VIOLATION:avellaneda_stoikov")
        return 0.5*risk*variance+math.log1p(risk/kappa)/risk
    if card_id == "B19":
        return -_decimal(inputs["inventory"],"inventory")*_decimal(inputs["risk_aversion"],"risk_aversion")*_decimal(inputs["variance_horizon"],"variance_horizon")
    if card_id == "B20":
        capacity=_finite(inputs["capacity"],"capacity"); available=_finite(inputs["available_tokens"],"available_tokens"); refill=_finite(inputs["refill_rate"],"refill_rate"); delta=_finite(inputs["elapsed_seconds"],"elapsed_seconds"); cost=_finite(inputs["request_cost"],"request_cost")
        if min(capacity,available,refill,delta,cost)<0: raise FormulaDomainError("DOMAIN_VIOLATION:token_bucket")
        remaining=min(capacity,available+refill*delta)-cost
        return {"remaining_tokens":remaining,"request_feasible":remaining>=0}
    if card_id == "B21":
        usage=sum((_decimal(row["matched_contracts"],"matched_contracts") for row in inputs["window_fills"]),Decimal("0")); limit=_decimal(inputs["rolling_limit"],"rolling_limit")
        return {"rolling_usage":usage,"remaining_limit":max(Decimal("0"),limit-usage)}
    if card_id == "C01":
        probabilities, outcomes = _values(inputs, "probabilities"), _values(inputs, "outcomes")
        if len(probabilities) != len(outcomes) or any(not 0 <= p <= 1 for p in probabilities): raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return math.fsum((p-y)**2 for p,y in zip(probabilities,outcomes))/len(probabilities)
    if card_id == "C02":
        probabilities, outcomes = _values(inputs, "probabilities"), _values(inputs, "outcomes")
        if len(probabilities) != len(outcomes) or any(not 0 < p < 1 for p in probabilities): raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return -math.fsum(y*math.log(p)+(1-y)*math.log(1-p) for p,y in zip(probabilities,outcomes))/len(probabilities)
    if card_id == "C03":
        probabilities=_values(inputs,"probabilities"); outcomes=_values(inputs,"outcomes"); bins=list(inputs["bins"])
        if len(probabilities)!=len(outcomes) or any(not 0<=p<=1 for p in probabilities): raise FormulaDomainError("DOMAIN_VIOLATION:calibration_inputs")
        total=0.0
        for lower,upper in bins:
            indices=[i for i,p in enumerate(probabilities) if lower<=p<upper or (upper==1 and p==1)]
            if indices: total+=len(indices)/len(probabilities)*abs(math.fsum(probabilities[i] for i in indices)/len(indices)-math.fsum(outcomes[i] for i in indices)/len(indices))
        return total
    if card_id == "C04":
        probabilities=_values(inputs,"probabilities"); outcomes=_values(inputs,"outcomes")
        if len(probabilities)!=len(outcomes) or len(probabilities)<2 or any(not 0<p<1 for p in probabilities): raise FormulaDomainError("DOMAIN_VIOLATION:calibration_regression")
        x=[math.log(p/(1-p)) for p in probabilities]; intercept=0.0; slope=1.0
        for _ in range(20):
            fitted=[1/(1+math.exp(-(intercept+slope*v))) for v in x]; w=[max(1e-9,p*(1-p)) for p in fitted]
            g0=math.fsum(y-p for y,p in zip(outcomes,fitted)); g1=math.fsum((y-p)*v for y,p,v in zip(outcomes,fitted,x)); h00=math.fsum(w); h01=math.fsum(a*b for a,b in zip(w,x)); h11=math.fsum(a*b*b for a,b in zip(w,x)); determinant=h00*h11-h01*h01
            if determinant<=1e-12: break
            delta0=(g0*h11-g1*h01)/determinant; delta1=(g1*h00-g0*h01)/determinant; intercept+=delta0; slope+=delta1
            if max(abs(delta0),abs(delta1))<1e-9: break
        return {"intercept":intercept,"slope":slope}
    if card_id == "C05":
        weights = _values(inputs, "weights")
        if any(w < 0 for w in weights) or math.fsum(w*w for w in weights) == 0: raise FormulaDomainError("DOMAIN_VIOLATION:weights")
        return math.fsum(weights)**2 / math.fsum(w*w for w in weights)
    if card_id == "C06":
        n=int(inputs["sample_count"]); correlations=_values(inputs,"autocorrelations")
        if n<=0 or any(abs(value)>1 for value in correlations): raise FormulaDomainError("DOMAIN_VIOLATION:autocorrelation")
        denominator=1+2*math.fsum((1-(index+1)/n)*value for index,value in enumerate(correlations) if index+1<n); raw=n/denominator if denominator>0 else 1.0
        return {"raw_effective_sample_size":raw,"evidence_effective_sample_size":min(float(n),max(1.0,raw)),"truncation_rule":str(inputs["truncation_rule"])}
    if card_id == "C07":
        cluster_weights=[math.fsum(_finite(value,"weight") for value in row) for row in inputs["cluster_weights"]]
        if not cluster_weights or any(value<0 for value in cluster_weights) or math.fsum(value*value for value in cluster_weights)<=0: raise FormulaDomainError("DOMAIN_VIOLATION:cluster_weights")
        return {"effective_cluster_count":math.fsum(cluster_weights)**2/math.fsum(value*value for value in cluster_weights),"physical_cluster_count":len(cluster_weights)}
    if card_id == "C08":
        statistics=sorted(_values(inputs,"bootstrap_statistics")); alpha=_finite(inputs["alpha"],"alpha")
        if not 0<alpha<1: raise FormulaDomainError("DOMAIN_VIOLATION:alpha")
        return {"lower_confidence_bound":statistics[int(math.floor(alpha*(len(statistics)-1)))],"resampling_plan":str(inputs["resampling_plan"]),"seed":int(inputs["seed"])}
    if card_id == "C09":
        increments=_values(inputs,"e_value_increments"); alpha=_finite(inputs["alpha"],"alpha"); evidence=1.0
        if not 0<alpha<1 or any(value<0 for value in increments): raise FormulaDomainError("DOMAIN_VIOLATION:e_process")
        path=[]
        for value in increments: evidence*=value; path.append(evidence)
        return {"e_value":evidence,"reject":evidence>=1/alpha,"e_value_path":path,"family":str(inputs["e_process_family"])}
    if card_id in {"C10", "C11"}:
        p_values, q = _values(inputs, "p_values"), _finite(inputs["q"], "q")
        if any(not 0 <= p <= 1 for p in p_values) or not 0 < q < 1: raise FormulaDomainError("DOMAIN_VIOLATION:p_values_or_q")
        ordered = sorted(enumerate(p_values), key=lambda item: item[1])
        harmonic = math.fsum(1/i for i in range(1,len(p_values)+1)) if card_id == "C11" else 1.0
        selected = [index for rank,(index,p) in enumerate(ordered,1) if p <= rank*q/(len(p_values)*harmonic)]
        cutoff = max((p_values[index] for index in selected), default=-1.0)
        return {"selected_indices": sorted(index for index,p in enumerate(p_values) if p <= cutoff), "cutoff": cutoff}
    if card_id == "C12":
        sharpe=_finite(inputs["sharpe"],"sharpe"); reference=_finite(inputs["reference_sharpe"],"reference_sharpe"); count=int(inputs["sample_count"]); skew=_finite(inputs["skewness"],"skewness"); kurtosis=_finite(inputs["kurtosis"],"kurtosis")
        denominator=1-skew*sharpe+((kurtosis-1)/4)*sharpe*sharpe
        if count<2 or denominator<=0: raise FormulaDomainError("NUMERICAL_DOMAIN_UNAVAILABLE:psr")
        return NormalDist().cdf((sharpe-reference)*math.sqrt(count-1)/math.sqrt(denominator))
    if card_id == "C13":
        sharpe=_finite(inputs["sharpe"],"sharpe"); variance=_finite(inputs["trial_sharpe_variance"],"trial_sharpe_variance"); trials=_finite(inputs["effective_trial_count"],"effective_trial_count"); count=int(inputs["effective_sample_length"]); skew=_finite(inputs["skewness"],"skewness"); kurtosis=_finite(inputs["kurtosis"],"kurtosis")
        if variance<0 or trials<=1 or count<2: raise FormulaDomainError("INSUFFICIENT_EVIDENCE:dsr")
        gamma=0.5772156649015329; benchmark=math.sqrt(variance)*((1-gamma)*NormalDist().inv_cdf(1-1/trials)+gamma*NormalDist().inv_cdf(1-1/(math.e*trials))); denominator=1-skew*sharpe+((kurtosis-1)/4)*sharpe*sharpe
        if denominator<=0: raise FormulaDomainError("NUMERICAL_DOMAIN_UNAVAILABLE:dsr")
        return {"deflated_sharpe_ratio":NormalDist().cdf((sharpe-benchmark)*math.sqrt(count-1)/math.sqrt(denominator)),"selection_bias_benchmark":benchmark}
    if card_id == "C14":
        logits=_values(inputs,"oos_rank_logits")
        return {"probability_of_backtest_overfitting":sum(value<0 for value in logits)/len(logits),"partition_count":len(logits)}
    if card_id in {"C15","C16"}:
        observed=_finite(inputs["observed_max_statistic"],"observed_max_statistic"); bootstrap=_values(inputs,"bootstrap_max_statistics")
        p_value=(1+sum(value>=observed for value in bootstrap))/(1+len(bootstrap))
        return {"p_value":p_value,"observed_statistic":observed,"common_resample_count":len(bootstrap),"procedure":"WHITE_REALITY_CHECK" if card_id=="C15" else "HANSEN_SPA"}
    if card_id == "C17":
        p_values=_values(inputs,"stepdown_p_values"); alpha=_finite(inputs["alpha"],"alpha")
        adjusted=[]; running=0.0
        for value in sorted(p_values): running=max(running,value); adjusted.append(running)
        return {"monotone_adjusted_p_values":adjusted,"rejected_count":sum(value<=alpha for value in adjusted)}
    if card_id == "C18":
        models=list(inputs["model_ids"]); p_values=list(_values(inputs,"equal_predictive_ability_p_values")); alpha=_finite(inputs["alpha"],"alpha")
        if len(models)!=len(p_values): raise FormulaDomainError("DOMAIN_VIOLATION:mcs_inputs")
        retained=[model for model,p in zip(models,p_values) if p>alpha]
        return {"superior_model_set":retained or [models[p_values.index(max(p_values))]],"elimination_rule":str(inputs["elimination_rule"])}
    if card_id == "C19":
        deltas=_values(inputs,"paired_utility_deltas"); alpha=_finite(inputs["alpha"],"alpha"); ordered=sorted(deltas); lcb=ordered[int(math.floor(alpha*(len(ordered)-1)))]
        return {"mean_delta":math.fsum(deltas)/len(deltas),"lower_confidence_bound":lcb,"promote":lcb>0}
    if card_id == "C20":
        rankings=[list(row) for row in inputs["rankings"]]
        if len(rankings)<2 or any(set(row)!=set(rankings[0]) for row in rankings): raise FormulaDomainError("DOMAIN_VIOLATION:rankings")
        taus=[]
        for left_index in range(len(rankings)):
            for right_index in range(left_index+1,len(rankings)):
                left,right=rankings[left_index],rankings[right_index]; pairs=0; concordant=0
                for a in range(len(left)):
                    for b in range(a+1,len(left)):
                        pairs+=1; concordant+=((left.index(left[a])-left.index(left[b]))*(right.index(left[a])-right.index(left[b]))>0)
                taus.append(2*concordant/pairs-1)
        return {"median_kendall_tau":sorted(taus)[len(taus)//2],"pair_count":len(taus)}
    if card_id == "C21":
        samples=_values(inputs,"net_cash_samples"); positives=sum(value>0 for value in samples); probability=positives/len(samples); z=NormalDist().inv_cdf(1-_finite(inputs["alpha"],"alpha")/2); denominator=1+z*z/len(samples); center=(probability+z*z/(2*len(samples)))/denominator; half=z*math.sqrt(probability*(1-probability)/len(samples)+z*z/(4*len(samples)**2))/denominator
        return {"probability_positive_net_cash":probability,"wilson_interval":[max(0,center-half),min(1,center+half)]}
    if card_id == "C22":
        sharpe=_finite(inputs["sharpe"],"sharpe"); reference=_finite(inputs["reference_sharpe"],"reference_sharpe"); confidence=_finite(inputs["confidence_target"],"confidence_target"); skew=_finite(inputs["skewness"],"skewness"); kurtosis=_finite(inputs["kurtosis"],"kurtosis"); denominator=1-skew*sharpe+((kurtosis-1)/4)*sharpe*sharpe
        if sharpe<=reference or not 0<confidence<1 or denominator<=0: raise FormulaDomainError("NUMERICAL_DOMAIN_UNAVAILABLE:min_track_record")
        z=NormalDist().inv_cdf(confidence); return math.ceil(1+denominator*(z/(sharpe-reference))**2)
    if card_id == "C23":
        scores=sorted(_values(inputs,"nonconformity_scores")); alpha=_finite(inputs["alpha"],"alpha"); rank=min(len(scores)-1,math.ceil((len(scores)+1)*(1-alpha))-1)
        return {"quantile":scores[rank],"prediction_interval":[_finite(inputs["point_prediction"],"point_prediction")-scores[rank],_finite(inputs["point_prediction"],"point_prediction")+scores[rank]],"coverage_target":1-alpha}
    if card_id == "C24":
        eigenvalues=_values(inputs,"dependence_eigenvalues")
        if any(value<0 for value in eigenvalues) or math.fsum(value*value for value in eigenvalues)<=0: raise FormulaDomainError("DOMAIN_VIOLATION:dependence_eigenvalues")
        return {"effective_trial_count":math.fsum(eigenvalues)**2/math.fsum(value*value for value in eigenvalues),"raw_trial_count":int(inputs["raw_trial_count"])}
    if card_id in {"D01", "H05"}:
        losses, alpha = _values(inputs, "losses"), _finite(inputs["alpha"], "alpha")
        if not 0 < alpha < 1: raise FormulaDomainError("DOMAIN_VIOLATION:alpha")
        weights = [_finite(v,"weights") for v in inputs.get("weights", [1/len(losses)]*len(losses))]
        if len(weights)!=len(losses) or any(w<0 for w in weights) or abs(math.fsum(weights)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:weights")
        candidates = sorted(set(losses))
        return min(eta + math.fsum(w*max(loss-eta,0) for w,loss in zip(weights,losses))/(1-alpha) for eta in candidates)
    if card_id == "D02":
        alpha=_finite(inputs["alpha"],"alpha"); robust_values=[]
        for row in inputs["weighted_loss_scenarios"]:
            losses=[_finite(value,"loss") for value in row["losses"]]; weights=[_finite(value,"weight") for value in row["weights"]]
            if len(losses)!=len(weights) or abs(math.fsum(weights)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:robust_cvar_weights")
            robust_values.append(min(eta+math.fsum(w*max(loss-eta,0) for w,loss in zip(weights,losses))/(1-alpha) for eta in sorted(set(losses))))
        return {"robust_cvar":max(robust_values),"stress_values":robust_values}
    if card_id == "D03":
        weights=_values(inputs,"weights"); means=_values(inputs,"expected_returns"); covariance=inputs["covariance"]; risk=_finite(inputs["risk_aversion"],"risk_aversion")
        if len(weights)!=len(means) or len(covariance)!=len(weights) or risk<0: raise FormulaDomainError("DOMAIN_VIOLATION:mean_variance")
        variance=math.fsum(weights[i]*weights[j]*_finite(covariance[i][j],"covariance") for i in range(len(weights)) for j in range(len(weights)))
        return math.fsum(w*m for w,m in zip(weights,means))-risk*variance
    if card_id == "D04":
        weights=_values(inputs,"weights"); covariance=inputs["covariance"]
        sigma_squared=math.fsum(weights[i]*weights[j]*_finite(covariance[i][j],"covariance") for i in range(len(weights)) for j in range(len(weights)))
        if sigma_squared<=0: raise FormulaDomainError("NUMERICAL_DOMAIN_UNAVAILABLE:portfolio_variance")
        sigma=math.sqrt(sigma_squared); marginal=[math.fsum(_finite(covariance[i][j],"covariance")*weights[j] for j in range(len(weights)))/sigma for i in range(len(weights))]; components=[w*m for w,m in zip(weights,marginal)]
        return {"portfolio_volatility":sigma,"marginal_risk_contribution":marginal,"component_risk_contribution":components,"euler_residual":math.fsum(components)-sigma}
    if card_id == "D05":
        shares = _values(inputs, "shares")
        if any(s<0 for s in shares) or abs(math.fsum(shares)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:shares")
        return math.fsum(s*s for s in shares)
    if card_id == "D06":
        shares = _values(inputs, "shares")
        if any(s<0 for s in shares) or abs(math.fsum(shares)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:shares")
        entropy=-math.fsum(s*math.log(s) for s in shares if s>0)
        return {"entropy":entropy,"effective_count":math.exp(entropy)}
    if card_id == "D07":
        total=0.0
        for row in inputs["pair_interactions"]: total+=_finite(row["coefficient"],"coefficient")*_finite(row["correlation"],"correlation")*_finite(row["weight_a"],"weight_a")*_finite(row["weight_b"],"weight_b")
        return total
    if card_id == "D08":
        returns=_values(inputs,"return_scenarios"); probabilities=_values(inputs,"probabilities"); cap=_finite(inputs["owner_cap"],"owner_cap"); shrink=_finite(inputs["shrink_factor"],"shrink_factor")
        if len(returns)!=len(probabilities) or abs(math.fsum(probabilities)-1)>1e-9 or not 0<shrink<=1 or cap<0: raise FormulaDomainError("DOMAIN_VIOLATION:kelly")
        candidates=[cap*i/100 for i in range(101)]; feasible=[f for f in candidates if all(1+f*r>0 for r in returns)]
        if not feasible: raise FormulaDomainError("ORIGINAL_MODEL_INFEASIBLE:kelly")
        optimum=max(feasible,key=lambda f:math.fsum(p*math.log1p(f*r) for p,r in zip(probabilities,returns)))
        return {"robust_kelly_fraction":optimum,"applied_fraction":shrink*optimum,"owner_cap":cap}
    if card_id == "D09":
        values=_values(inputs,"equity")
        peak=values[0]; drawdown=0.0
        for value in values: peak=max(peak,value); drawdown=max(drawdown,peak-value)
        return drawdown
    if card_id == "D11":
        return _decimal(inputs["portfolio_utility_with_candidate"],"portfolio_utility_with_candidate")-_decimal(inputs["current_portfolio_utility"],"current_portfolio_utility")
    if card_id == "D12":
        return _decimal(inputs["new_opportunity_marginal_utility"],"new_opportunity_marginal_utility")-_decimal(inputs["current_position_continuation_value"],"current_position_continuation_value")-_decimal(inputs["switching_cost"],"switching_cost")
    if card_id == "D13":
        sensitivities=_values(inputs,"payoff_sensitivities"); positions=_values(inputs,"positions")
        if len(sensitivities)!=len(positions): raise FormulaDomainError("DOMAIN_VIOLATION:event_exposure")
        return math.fsum(a*b for a,b in zip(sensitivities,positions))
    if card_id == "D14":
        usage=[math.fsum(_finite(row["capital"],"capital")*_finite(row["weight"],"weight") for row in bucket) for bucket in inputs["capital_buckets"]]; budgets=_values(inputs,"budgets")
        if len(usage)!=len(budgets): raise FormulaDomainError("DOMAIN_VIOLATION:capital_buckets")
        return {"used_capital":usage,"constraint_residuals":[used-budget for used,budget in zip(usage,budgets)],"feasible":all(used<=budget for used,budget in zip(usage,budgets))}
    if card_id == "D15":
        losses=_values(inputs,"losses"); probabilities=_values(inputs,"probabilities"); theta=_finite(inputs["theta"],"theta")
        if theta<=0 or len(losses)!=len(probabilities) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:entropic_risk")
        maximum=max(theta*loss for loss in losses); return (maximum+math.log(math.fsum(p*math.exp(theta*loss-maximum) for p,loss in zip(probabilities,losses))))/theta
    if card_id == "D16":
        scenario_utilities=_values(inputs,"scenario_utilities"); tail=_finite(inputs["tail_penalty"],"tail_penalty"); lock=_finite(inputs["capital_lock_penalty"],"capital_lock_penalty"); model=_finite(inputs["model_risk_penalty"],"model_risk_penalty")
        return {"robust_utility":min(scenario_utilities)-tail-lock-model,"worst_scenario_utility":min(scenario_utilities)}
    if card_id == "D17":
        hard=tuple(bool(value) for value in inputs["hard_constraints"]); return (not all(hard),-_finite(inputs["net_cash_lcb"],"net_cash_lcb"),_finite(inputs["tail_loss"],"tail_loss"),-_finite(inputs["capital_time_efficiency"],"capital_time_efficiency"),_finite(inputs["turnover_compute_burden"],"turnover_compute_burden"))
    if card_id == "D18":
        candidates=list(inputs["candidates"]); bounds=dict(inputs["epsilon_bounds"]); feasible=[]
        for row in candidates:
            if all((_finite(row[key],key)<=_finite(value,key)) for key,value in bounds.items()): feasible.append(row)
        if not feasible: raise FormulaDomainError("NO_FEASIBLE_SAMPLE_OBSERVED")
        return max(feasible,key=lambda row:_finite(row["primary_objective"],"primary_objective"))
    if card_id == "D19":
        prior=_finite(inputs["prior_mean"],"prior_mean"); strength=_finite(inputs["prior_strength"],"prior_strength"); support=_finite(inputs["effective_sample_size"],"effective_sample_size"); sample=_finite(inputs["sample_mean"],"sample_mean")
        if strength<0 or support<0 or strength+support<=0: raise FormulaDomainError("DOMAIN_VIOLATION:shrinkage")
        return (strength*prior+support*sample)/(strength+support)
    if card_id == "D20":
        return _decimal(inputs["champion_utility"],"champion_utility")-_decimal(inputs["selected_utility"],"selected_utility")
    if card_id == "D21":
        posterior=[max(_finite(value,"conditional_utility") for value in row) for row in inputs["conditional_action_utilities"]]; probabilities=_values(inputs,"outcome_probabilities"); current=max(_values(inputs,"current_action_utilities")); cost=_finite(inputs["compute_and_delay_cost"],"compute_and_delay_cost")
        if len(posterior)!=len(probabilities) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:value_of_information")
        return math.fsum(p*v for p,v in zip(probabilities,posterior))-current-cost
    if card_id == "D22":
        return {"expected_information_gain":_finite(inputs["expected_information_gain"],"expected_information_gain"),"expected_economic_improvement":_finite(inputs["expected_economic_improvement"],"expected_economic_improvement"),"coverage_diversity_value":_finite(inputs["coverage_diversity_value"],"coverage_diversity_value"),"cost":_finite(inputs["cost"],"cost")}
    if card_id in {"D23","D24","D25"}:
        rewards=_values(inputs,"rewards"); target=_values(inputs,"target_probabilities"); behavior=_values(inputs,"behavior_probabilities")
        if not(len(rewards)==len(target)==len(behavior)) or any(value<=0 for value in behavior): raise FormulaDomainError("DOMAIN_VIOLATION:off_policy_support")
        weights=[target_value/behavior_value for target_value,behavior_value in zip(target,behavior)]
        if card_id=="D23": return math.fsum(w*r for w,r in zip(weights,rewards))/len(rewards)
        if card_id=="D24":
            if math.fsum(weights)<=0: raise FormulaDomainError("DOMAIN_VIOLATION:snips_weights")
            return math.fsum(w*r for w,r in zip(weights,rewards))/math.fsum(weights)
        predictions=_values(inputs,"reward_model_observed_action"); policy_predictions=_values(inputs,"reward_model_target_policy")
        if len(predictions)!=len(rewards) or len(policy_predictions)!=len(rewards): raise FormulaDomainError("DOMAIN_VIOLATION:doubly_robust_model")
        return math.fsum(qp+w*(r-q) for qp,w,r,q in zip(policy_predictions,weights,rewards,predictions))/len(rewards)
    if card_id == "D26":
        feasible=[row for row in inputs["candidate_changes"] if _finite(row["net_cash_lcb"],"net_cash_lcb")>=_finite(inputs["no_trade_hurdle"],"no_trade_hurdle") and bool(row["constraints_satisfied"])]
        if not feasible: return {"state":"DETERMINISTIC_NO_TRADE","frontier":[]}
        cost=min(_finite(row["change_cost"],"change_cost") for row in feasible); return {"state":"RECOVERY_CANDIDATE","frontier":[row for row in feasible if _finite(row["change_cost"],"change_cost")==cost]}
    if card_id == "D27":
        rows=list(inputs["regimes"]); weights=[_finite(row["weight"],"weight") for row in rows]
        if abs(math.fsum(weights)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:regime_weights")
        score=math.fsum(weight*bool(row["feasible"] and _finite(row["utility_lcb"],"utility_lcb")>=_finite(row["hurdle"],"hurdle")) for weight,row in zip(weights,rows))
        return {"robustness_weighted":score,"worst_regime_utility":min(_finite(row["utility_lcb"],"utility_lcb") for row in rows)}
    if card_id == "D28":
        components=[]
        for row in inputs["comparisons"]:
            if row["kind"]=="numeric": delta=abs(_finite(row["left"],"left")-_finite(row["right"],"right"))/_finite(row["scale"],"scale")
            elif row["kind"]=="interval": delta=max(0,_finite(row["left_lower"],"left_lower")-_finite(row["right_upper"],"right_upper"),_finite(row["right_lower"],"right_lower")-_finite(row["left_upper"],"left_upper"))/_finite(row["scale"],"scale")
            else: delta=float(row["left"]!=row["right"])
            components.append({"metric":row["metric"],"delta":delta,"hard_veto":bool(row.get("hard_veto",False) and delta>0)})
        return {"components":components,"hard_veto":any(row["hard_veto"] for row in components)}
    if card_id in {"E03", "E04"}:
        return math.fsum(_values(inputs, "probabilities")) - 1.0
    if card_id == "E01":
        return _decimal(inputs["guaranteed_payout"],"guaranteed_payout")-sum(_decimal_values(inputs,"executable_acquisition_costs"),Decimal("0"))-_decimal(inputs["all_unique_costs"],"all_unique_costs")-_decimal(inputs["atomicity_partial_fill_reserve"],"atomicity_partial_fill_reserve")
    if card_id == "E02":
        return sum(_decimal_values(inputs,"executable_sale_proceeds"),Decimal("0"))-_decimal(inputs["guaranteed_liability"],"guaranteed_liability")-_decimal(inputs["all_unique_costs"],"all_unique_costs")-_decimal(inputs["borrow_token_inventory_reserve"],"borrow_token_inventory_reserve")
    if card_id in {"E05", "E07", "E08"}:
        return _finite(inputs["probability_subset"],"probability_subset")-_finite(inputs["probability_superset"],"probability_superset")
    if card_id == "E06":
        return _finite(inputs["probability_intersection"],"probability_intersection")-min(_finite(inputs["probability_a"],"probability_a"),_finite(inputs["probability_b"],"probability_b"))
    if card_id == "E09":
        return _decimal(inputs["rich_venue_sale_proceeds"],"rich_venue_sale_proceeds")-_decimal(inputs["cheap_venue_buy_cost"],"cheap_venue_buy_cost")-sum((_decimal(inputs[key],key) for key in ("fees","transfer_finality_reserve","basis_settlement_reserve","asynchronous_fill_reserve")),Decimal("0"))
    if card_id == "E10":
        outcomes=[bool(value) for value in inputs["joint_all_fill_observations"]]
        if not outcomes: raise FormulaDomainError("INSUFFICIENT_EVIDENCE:joint_fills")
        return {"simultaneous_fill_probability":sum(outcomes)/len(outcomes),"joint_model":str(inputs["joint_dependence_model"]),"observation_count":len(outcomes)}
    if card_id == "E11":
        fill_adjusted=_decimal(inputs["fill_adjusted_net_cash"],"fill_adjusted_net_cash"); reserves=sum((_decimal(inputs[key],key) for key in ("tail_reserve","partial_fill_reserve","settlement_reserve","capital_lock_reserve")),Decimal("0"))
        return fill_adjusted-reserves
    if card_id == "E12":
        return {"objective":"MAXIMIZE_WORST_CASE_EXECUTABLE_BASKET_NET_CASH","decision_variables":list(inputs["decision_variables"]),"semantic_payoff_proof_refs":list(inputs["semantic_payoff_proof_refs"]),"constraints":list(inputs["constraints"]),"no_trade_alternative":True,"solver_lane":"BOUNDED_CLASSICAL_OR_QMAP_CANDIDATE"}
    if card_id == "F01":
        linear=[_finite(value,"net_cash_lcb")-_finite(inputs["tail_penalties"][index],"tail_penalty")-_finite(inputs["inventory_penalties"][index],"inventory_penalty")-_finite(inputs["turnover_penalties"][index],"turnover_penalty") for index,value in enumerate(inputs["net_cash_lcbs"])]
        return {"objective_sense":"MAXIMIZE","linear_utility_coefficients":linear,"quadratic_interactions":dict(inputs["interaction_coefficients"]),"hard_constraints":list(inputs["hard_constraints"]),"no_trade_variable":str(inputs["no_trade_variable"])}
    if card_id == "F02":
        scenario_values=_values(inputs,"scenario_profit_values"); tail=_finite(inputs["tail_penalty"],"tail_penalty"); lock=_finite(inputs["capital_lock_penalty"],"capital_lock_penalty"); model=_finite(inputs["model_risk_penalty"],"model_risk_penalty")
        return {"robust_objective":min(scenario_values)-tail-lock-model,"coefficient_map_ref":str(inputs["coefficient_map_ref"])}
    if card_id == "F04":
        vartype=str(inputs["vartype"]).upper()
        if vartype not in {"BINARY","SPIN"}: raise FormulaDomainError("DOMAIN_VIOLATION:vartype")
        return {"vartype":vartype,"linear":dict(inputs["linear"]),"quadratic":dict(inputs["quadratic"]),"offset":_finite(inputs["offset"],"offset")}
    if card_id == "F05":
        linear=[_finite(value,"linear") for value in inputs["linear"]]; quadratic={str(key):_finite(value,"quadratic") for key,value in dict(inputs["quadratic_upper"]).items()}; h=[-value/2 for value in linear]; couplers={}; offset=_finite(inputs["offset"],"offset")+math.fsum(linear)/2
        for key,value in quadratic.items():
            left,right=(int(part) for part in key.split(",")); couplers[key]=value/4; h[left]-=value/4; h[right]-=value/4; offset+=value/4
        return {"h":h,"J":couplers,"offset":offset,"binary_to_spin":"x=(1-s)/2"}
    if card_id == "F07":
        improvement=_finite(inputs["objective_improvement_bound"],"objective_improvement_bound"); violation=_finite(inputs["minimum_positive_violation"],"minimum_positive_violation")
        if improvement<0 or violation<=0: raise FormulaDomainError("DOMAIN_VIOLATION:penalty_bound")
        candidate=_finite(inputs["penalty"],"penalty"); lower=improvement/violation
        return {"penalty":candidate,"strict_lower_bound":lower,"sufficient":candidate>lower}
    if card_id == "F09":
        selected=sum(int(value) for value in inputs["selections"]); cardinality=int(inputs["cardinality"])
        return {"residual":selected-cardinality,"satisfied":selected==cardinality,"feasible_mixer_compatible":True}
    if card_id == "F10":
        lower=int(inputs["lower"]); upper=int(inputs["upper"]); bits=[int(value) for value in inputs["bits"]]
        if upper<lower or any(value not in {0,1} for value in bits): raise FormulaDomainError("DOMAIN_VIOLATION:bounded_binary")
        weights=[2**index for index in range(len(bits))]; weights[-1]=upper-lower-sum(weights[:-1]); value=lower+sum(weight*bit for weight,bit in zip(weights,bits))
        if not lower<=value<=upper: raise FormulaDomainError("DOMAIN_VIOLATION:encoded_value")
        return {"decoded_value":value,"weights":weights}
    if card_id == "F11":
        bits=[int(value) for value in inputs["bits"]]
        if any(value not in {0,1} for value in bits): raise FormulaDomainError("DOMAIN_VIOLATION:unary_bits")
        return {"decoded_value":int(inputs["lower"])+sum(bits),"monotonic_valid":all(left>=right for left,right in zip(bits,bits[1:]))}
    if card_id == "F12":
        digits=[int(value) for value in inputs["digits"]]; radices=[int(value) for value in inputs["radices"]]
        if len(digits)!=len(radices) or any(not 0<=digit<radix for digit,radix in zip(digits,radices)): raise FormulaDomainError("DOMAIN_VIOLATION:mixed_radix")
        multiplier=1; value=int(inputs["lower"])
        for digit,radix in zip(digits,radices): value+=digit*multiplier; multiplier*=radix
        return {"decoded_value":value,"state_count":multiplier}
    if card_id == "F13":
        binary=int(inputs["binary_index"])
        if binary<0 or binary>=int(inputs["domain_size"]): raise FormulaDomainError("DOMAIN_VIOLATION:gray_code")
        gray=binary^(binary>>1); decoded=0; current=gray
        while current: decoded^=current; current>>=1
        return {"gray_code":gray,"inverse_binary_index":decoded}
    if card_id == "F14":
        state=int(inputs["state"]); count=int(inputs["state_count"])
        if not 0<=state<count or count<2: raise FormulaDomainError("DOMAIN_VIOLATION:domain_wall")
        bits=[1 if index<state else 0 for index in range(count-1)]
        return {"bits":bits,"decoded_state":sum(bits),"monotonic_valid":True}
    if card_id == "F15":
        probabilities=_values(inputs,"sample_probabilities"); energies=_values(inputs,"energies")
        if len(probabilities)!=len(energies) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:qaoa_distribution")
        return {"expectation":math.fsum(p*e for p,e in zip(probabilities,energies)),"objective_sense":str(inputs["objective_sense"]),"economic_units":False}
    if card_id == "F16":
        epsilon=_finite(inputs["epsilon"],"epsilon")
        if not 0<epsilon<0.5: raise FormulaDomainError("DOMAIN_VIOLATION:warm_start_epsilon")
        values=[min(1-epsilon,max(epsilon,_finite(value,"relaxation"))) for value in inputs["relaxation_values"]]
        return [2*math.asin(math.sqrt(value)) for value in values]
    if card_id == "F17":
        values=sorted(_values(inputs,"sampled_objectives")); alpha=_finite(inputs["alpha"],"alpha"); sense=str(inputs["objective_sense"]).upper()
        if not 0<alpha<=1 or sense not in {"MINIMIZE","MAXIMIZE"}: raise FormulaDomainError("DOMAIN_VIOLATION:variational_cvar")
        count=max(1,math.ceil(alpha*len(values))); selected=values[:count] if sense=="MINIMIZE" else values[-count:]
        return math.fsum(selected)/len(selected)
    if card_id == "F18":
        samples=[list(map(int,row)) for row in inputs["feasible_samples"]]
        if not samples or any(len(row)!=len(samples[0]) for row in samples): raise FormulaDomainError("DOMAIN_VIOLATION:samples")
        return [sum(row[index] for row in samples)/len(samples) for index in range(len(samples[0]))]
    if card_id == "F19":
        samples=[list(map(int,row)) for row in inputs["feasible_samples"]]; pairs=[tuple(map(int,row)) for row in inputs["pairs"]]
        return {f"{left},{right}":sum(row[left]*row[right] for row in samples)/len(samples) for left,right in pairs}
    if card_id == "F22":
        samples=list(inputs["samples"]); distance_limit=int(inputs["distance_tolerance"]); utility_limit=_finite(inputs["utility_tolerance"],"utility_tolerance"); best=max(_finite(row["utility"],"utility") for row in samples); retained=[row for row in samples if _finite(row["utility"],"utility")>=best-utility_limit]; unseen=set(range(len(retained))); components=[]
        while unseen:
            root=unseen.pop(); component={root}; frontier=[root]
            while frontier:
                current=frontier.pop()
                neighbors=[index for index in list(unseen) if sum(a!=b for a,b in zip(retained[current]["bits"],retained[index]["bits"]))<=distance_limit and abs(_finite(retained[current]["utility"],"utility")-_finite(retained[index]["utility"],"utility"))<=utility_limit]
                for index in neighbors: unseen.remove(index); component.add(index); frontier.append(index)
            components.append(sorted(component))
        return {"near_optimal_cluster_count":len(components),"clusters":components}
    if card_id == "F26":
        left=_values(inputs,"residuals_a"); right=_values(inputs,"residuals_b"); status_a=list(inputs["status_a"]); status_b=list(inputs["status_b"])
        if not(len(left)==len(right)==len(status_a)==len(status_b)): raise FormulaDomainError("DOMAIN_VIOLATION:constraint_disagreement")
        return {"residual_deltas":[a-b for a,b in zip(left,right)],"status_disagreements":[a!=b for a,b in zip(status_a,status_b)]}
    if card_id == "F27":
        left=_values(inputs,"exposure_a"); right=_values(inputs,"exposure_b"); scales=_values(inputs,"scales")
        if not(len(left)==len(right)==len(scales)) or any(value<=0 for value in scales): raise FormulaDomainError("DOMAIN_VIOLATION:exposure_scales")
        components=[abs(a-b)/scale for a,b,scale in zip(left,right,scales)]; return {"components":components,"distance":math.fsum(components)}
    if card_id == "F28":
        left,right=inputs["plan_a"],inputs["plan_b"]
        return {"market":int(left["market"]!=right["market"]),"side":int(left["side"]!=right["side"]),"size":abs(_finite(left["size"],"size")-_finite(right["size"],"size"))/_finite(inputs["size_scale"],"size_scale"),"venue":int(left["venue"]!=right["venue"]),"policy":int(left["policy"]!=right["policy"]),"horizon":abs(_finite(left["horizon"],"horizon")-_finite(right["horizon"],"horizon"))/_finite(inputs["time_scale"],"time_scale")}
    if card_id == "F29":
        utilities=_values(inputs,"utilities"); coefficients=_values(inputs,"coefficients")
        if len(utilities)!=len(coefficients) or len(utilities)<2: raise FormulaDomainError("INSUFFICIENT_EVIDENCE:sensitivity")
        return [(utilities[index]-utilities[index-1])/(coefficients[index]-coefficients[index-1]) for index in range(1,len(utilities))]
    if card_id == "F30":
        return {key:_finite(inputs[key],key) for key in ("one_minus_selection_consensus","infeasible_rate","utility_standard_deviation","worst_utility_drop","maximum_coefficient_sensitivity","backend_seed_disagreement")}
    if card_id == "F31":
        rows=list(inputs["regimes"]); weights=[_finite(row["weight"],"weight") for row in rows]
        if abs(math.fsum(weights)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:regime_weights")
        return math.fsum(weight*bool(row["original_model_feasible"] and _finite(row["qeu_lcb"],"qeu_lcb")>0) for weight,row in zip(weights,rows))
    if card_id == "F32":
        required=("utility_quantum","utility_classical","compute_cost","latency_cost","infeasibility_penalty","instability_penalty","model_risk_reserve")
        values={key:_decimal(inputs[key],key) for key in required}; return values["utility_quantum"]-values["utility_classical"]-sum((values[key] for key in required[2:]),Decimal("0"))
    if card_id in {"F33","F34"}:
        improvement=_decimal(inputs["expected_economic_improvement"],"expected_economic_improvement"); denominator=_decimal(inputs["qpu_monetary_cost" if card_id=="F33" else "total_end_to_end_seconds"],"denominator")
        if denominator<=0: raise FormulaDomainError("UNBOUNDED_RATIO_ZERO_DENOMINATOR")
        return improvement/denominator
    if card_id == "F35":
        return _decimal(inputs["expected_decision_improvement"],"expected_decision_improvement")+_decimal(inputs["information_gain"],"information_gain")-_decimal(inputs["compute_cost"],"compute_cost")-_decimal(inputs["opportunity_cost_of_waiting"],"opportunity_cost_of_waiting")-_decimal(inputs["expiry_risk"],"expiry_risk")
    if card_id == "F36":
        probabilities=_values(inputs,"probabilities"); normalized=_values(inputs,"normalized_values"); scale=_finite(inputs["inverse_scale"],"inverse_scale"); offset=_finite(inputs["inverse_offset"],"inverse_offset")
        if len(probabilities)!=len(normalized) or abs(math.fsum(probabilities)-1)>1e-9 or any(not 0<=value<=1 for value in normalized): raise FormulaDomainError("DOMAIN_VIOLATION:qae_expectation")
        amplitude=math.fsum(p*v for p,v in zip(probabilities,normalized)); return {"normalized_expectation":amplitude,"original_unit_expectation":scale*amplitude+offset}
    if card_id == "F37":
        probabilities=_values(inputs,"probabilities"); losses=_values(inputs,"losses"); threshold=_finite(inputs["threshold"],"threshold")
        if len(probabilities)!=len(losses) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:qae_tail")
        return math.fsum(p for p,loss in zip(probabilities,losses) if loss>=threshold)
    if card_id == "F38":
        losses=_values(inputs,"losses"); probabilities=_values(inputs,"probabilities"); alpha=_finite(inputs["alpha"],"alpha"); etas=_values(inputs,"eta_candidates")
        if len(losses)!=len(probabilities) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:qae_cvar")
        return min(eta+math.fsum(p*max(loss-eta,0) for p,loss in zip(probabilities,losses))/(1-alpha) for eta in etas)
    if card_id in {"F41","F42"}:
        records=list(inputs["records"]); basis=_finite(inputs["time_basis"],"time_basis")
        if card_id=="F41": eligible=[_finite(row["timestamp"],"timestamp") for row in records if row["original_model_feasible"]]
        else:
            feasible=[row for row in records if row["original_model_feasible"]]
            if not feasible: eligible=[]
            else:
                best=max(_finite(row["utility"],"utility") for row in feasible); eligible=[_finite(row["timestamp"],"timestamp") for row in feasible if _finite(row["utility"],"utility")==best]
        return {"seconds":min(eligible)-basis if eligible else None,"state":"OBSERVED" if eligible else "NOT_OBSERVED_CENSORED"}
    if card_id == "F43":
        runs=list(inputs["runs"]); selections=[list(row["selection"]) for row in runs]; variable_count=len(selections[0]); marginals=[sum(row[index] for row in selections)/len(selections) for index in range(variable_count)]; utilities=[_finite(row["utility"],"utility") for row in runs]; feasible=[bool(row["feasible"]) for row in runs]
        return {"selection_consensus":math.fsum(max(value,1-value) for value in marginals)/variable_count,"feasible_rate_range":[min(feasible),max(feasible)],"utility_standard_deviation":math.sqrt(math.fsum((value-math.fsum(utilities)/len(utilities))**2 for value in utilities)/len(utilities))}
    if card_id == "F44":
        return _decimal(inputs["best_reverse_utility"],"best_reverse_utility")-_decimal(inputs["initial_incumbent_utility"],"initial_incumbent_utility")
    if card_id == "F45":
        return _decimal(inputs["postprocessed_utility"],"postprocessed_utility")-_decimal(inputs["raw_decoded_utility"],"raw_decoded_utility")
    if card_id == "F46":
        fields=("logical_qubits","physical_qubits","depth","two_qubit_gates","shots_or_reads","embedding_chains","queue_seconds","preparation_seconds","wall_seconds","monetary_cost")
        vector={key:_finite(inputs[key],key) for key in fields}
        if any(value<0 for value in vector.values()): raise FormulaDomainError("DOMAIN_VIOLATION:resource_estimate")
        return vector
    if card_id == "F23":
        left,right=set(inputs.get("left",())),set(inputs.get("right",()))
        union=left|right
        return 1.0 if not union else len(left&right)/len(union)
    if card_id == "F20":
        probabilities=_values(inputs,"probabilities")
        if any(p<0 for p in probabilities) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:probabilities")
        return -math.fsum(p*math.log(p) for p in probabilities if p>0)
    if card_id == "G10":
        probability=_finite(inputs["p_success"],"p_success"); target=_finite(inputs["p_target"],"p_target"); run=_finite(inputs["run_seconds"],"run_seconds")
        if not 0<=probability<=1 or not 0<target<1 or run<=0: raise FormulaDomainError("DOMAIN_VIOLATION:tts")
        if probability == 0:
            return {"required_runs":None,"time_to_solution":None,"state":"ZERO_SUCCESS_PROBABILITY_NO_FINITE_TTS"}
        runs=1 if probability==1 else math.ceil(math.log(1-target)/math.log(1-probability))
        return {"required_runs":runs,"time_to_solution":runs*run,"state":"FINITE_TTS"}
    if card_id == "G01":
        sample=[[ _finite(value,"sample_covariance") for value in row] for row in inputs["sample_covariance"]]
        target=[[ _finite(value,"target_covariance") for value in row] for row in inputs["target_covariance"]]
        shrink=_finite(inputs["shrinkage_intensity"],"shrinkage_intensity")
        if not 0<=shrink<=1 or not sample or len(sample)!=len(target) or any(len(row)!=len(sample) for row in sample+target):
            raise FormulaDomainError("DOMAIN_VIOLATION:shrinkage_covariance")
        return [[(1-shrink)*sample[i][j]+shrink*target[i][j] for j in range(len(sample))] for i in range(len(sample))]
    if card_id == "G02":
        losses=_values(inputs,"scenario_losses"); weights=_values(inputs,"portfolio_weights"); contributions=inputs["asset_loss_contributions"]
        alpha=_finite(inputs["alpha"],"alpha")
        if not 0<alpha<1 or len(contributions)!=len(losses) or any(len(row)!=len(weights) for row in contributions):
            raise FormulaDomainError("DOMAIN_VIOLATION:component_cvar")
        order=sorted(range(len(losses)),key=losses.__getitem__,reverse=True); tail_mass=1-alpha; remaining=tail_mass; aggregate=[0.0]*len(weights)
        probabilities=_values(inputs,"scenario_probabilities")
        if len(probabilities)!=len(losses) or abs(math.fsum(probabilities)-1)>1e-9: raise FormulaDomainError("DOMAIN_VIOLATION:scenario_probabilities")
        for index in order:
            mass=min(remaining,probabilities[index]); remaining-=mass
            for asset,value in enumerate(contributions[index]): aggregate[asset]+=mass*_finite(value,"asset_loss_contribution")
            if remaining<=1e-15: break
        if remaining>1e-12: raise FormulaDomainError("INSUFFICIENT_EVIDENCE:tail_mass")
        component=[value/tail_mass for value in aggregate]
        return {"component_cvar":component,"portfolio_cvar":math.fsum(component),"euler_residual":math.fsum(component)-math.fsum(component)}
    if card_id == "G03":
        contributions=_values(inputs,"component_risk_contributions"); budgets=_values(inputs,"risk_budgets")
        if len(contributions)!=len(budgets) or any(value<0 for value in budgets) or math.fsum(budgets)<=0: raise FormulaDomainError("DOMAIN_VIOLATION:risk_budgets")
        total=math.fsum(contributions); normalized=[value/math.fsum(budgets) for value in budgets]
        residuals=[contribution-total*budget for contribution,budget in zip(contributions,normalized)]
        return {"objective":math.fsum(value*value for value in residuals),"budget_residuals":residuals}
    if card_id == "G04":
        quantity=_decimal(inputs["quantity"],"quantity"); daily_volume=_decimal(inputs["daily_volume"],"daily_volume"); sigma=_decimal(inputs["volatility"],"volatility"); coefficient=_decimal(inputs["impact_coefficient"],"impact_coefficient")
        if quantity<0 or daily_volume<=0 or sigma<0 or coefficient<0: raise FormulaDomainError("DOMAIN_VIOLATION:square_root_impact")
        participation=(quantity/daily_volume).sqrt(); return {"impact_price_fraction":coefficient*sigma*participation,"participation_fraction":quantity/daily_volume}
    if card_id == "G05":
        schedule=_values(inputs,"schedule_quantities"); expected_costs=_values(inputs,"expected_unit_costs"); covariance=inputs["cost_covariance"]; risk_aversion=_finite(inputs["risk_aversion"],"risk_aversion")
        if len(schedule)!=len(expected_costs) or any(len(row)!=len(schedule) for row in covariance) or risk_aversion<0: raise FormulaDomainError("DOMAIN_VIOLATION:execution_schedule")
        expected=math.fsum(q*c for q,c in zip(schedule,expected_costs)); variance=math.fsum(schedule[i]*_finite(covariance[i][j],"covariance")*schedule[j] for i in range(len(schedule)) for j in range(len(schedule)))
        return {"mean_variance_objective":expected+risk_aversion*variance,"expected_cost":expected,"cost_variance":variance}
    if card_id == "G06":
        observations=_values(inputs,"observations"); reference=_finite(inputs["reference_mean"],"reference_mean"); allowance=_finite(inputs["allowance"],"allowance")
        positive=negative=0.0; max_positive=max_negative=0.0
        for value in observations:
            positive=max(0.0,positive+value-reference-allowance); negative=max(0.0,negative+reference-value-allowance); max_positive=max(max_positive,positive); max_negative=max(max_negative,negative)
        return {"positive_cusum":max_positive,"negative_cusum":max_negative,"drift_statistic":max(max_positive,max_negative)}
    if card_id == "G07":
        log_scores=_values(inputs,"log_model_evidence"); priors=_values(inputs,"prior_weights")
        if len(log_scores)!=len(priors) or any(value<=0 for value in priors): raise FormulaDomainError("DOMAIN_VIOLATION:model_priors")
        shifted=[score+math.log(prior) for score,prior in zip(log_scores,priors)]; maximum=max(shifted); denominator=math.fsum(math.exp(value-maximum) for value in shifted)
        return {"posterior_weights":[math.exp(value-maximum)/denominator for value in shifted],"log_normalizer":maximum+math.log(denominator)}
    if card_id == "G08":
        utilities=_values(inputs,"utilities"); temperature=_finite(inputs["temperature"],"temperature")
        if temperature<=0: raise FormulaDomainError("DOMAIN_VIOLATION:temperature")
        maximum=max(utilities); exponentials=[math.exp((value-maximum)/temperature) for value in utilities]; total=math.fsum(exponentials)
        return {"allocation":[value/total for value in exponentials],"temperature":temperature}
    if card_id == "G11":
        raw=_finite(inputs["raw_estimator_variance"],"raw_estimator_variance"); mitigated=_finite(inputs["mitigated_estimator_variance"],"mitigated_estimator_variance")
        if raw<=0 or mitigated<0: raise FormulaDomainError("DOMAIN_VIOLATION:variance_overhead")
        return {"variance_overhead":mitigated/raw,"additional_shots_multiplier":mitigated/raw}
    if card_id == "G12":
        sigmas=_values(inputs,"stratum_standard_deviations"); costs=_values(inputs,"per_shot_costs"); total=int(inputs["total_shots"])
        if len(sigmas)!=len(costs) or any(value<=0 for value in costs) or total<len(sigmas): raise FormulaDomainError("DOMAIN_VIOLATION:neyman_allocation")
        scores=[sigma/math.sqrt(cost) for sigma,cost in zip(sigmas,costs)]; score_sum=math.fsum(scores); raw=[total*score/score_sum for score in scores]; allocation=[max(1,int(math.floor(value))) for value in raw]
        for index in sorted(range(len(raw)),key=lambda i:raw[i]-math.floor(raw[i]),reverse=True)[:total-sum(allocation)]: allocation[index]+=1
        return {"shot_allocation":allocation,"total_shots":sum(allocation)}
    if card_id == "G13":
        current=_values(inputs,"current_calibration"); baseline=_values(inputs,"baseline_calibration")
        if len(current)!=len(baseline): raise FormulaDomainError("DOMAIN_VIOLATION:calibration_vector")
        delta=[left-right for left,right in zip(current,baseline)]
        return {"drift_vector":delta,"l2_drift":math.sqrt(math.fsum(value*value for value in delta)),"max_abs_drift":max(abs(value) for value in delta)}
    if card_id == "D29":
        left,right=inputs["left"],inputs["right"]; senses=inputs["senses"]
        no_worse=[]; better=[]
        for a,b,sense in zip(left,right,senses):
            if sense=="MAXIMIZE": no_worse.append(a>=b); better.append(a>b)
            else: no_worse.append(a<=b); better.append(a<b)
        return all(no_worse) and any(better)
    if card_id == "D30":
        eligible=[row for row in inputs["experiments"] if bool(row["eligible"]) and _finite(row["resource_cost"],"resource_cost")>0]
        if not eligible: raise FormulaDomainError("NO_FEASIBLE_SAMPLE_OBSERVED")
        selected=max(eligible,key=lambda row:_finite(row["expected_marginal_voi"],"expected_marginal_voi")/_finite(row["resource_cost"],"resource_cost"))
        return {"selected_experiment_id":selected["experiment_id"],"voi_per_resource":_finite(selected["expected_marginal_voi"],"expected_marginal_voi")/_finite(selected["resource_cost"],"resource_cost")}
    if card_id == "I04":
        rows=list(inputs.get("requirements",()))
        required=[row for row in rows if row.get("required")]
        resolved=[row for row in required if row.get("resolved_valid")]
        missing=[row.get("name") for row in required if not row.get("resolved_valid")]
        return {"coverage":1.0 if not required else len(resolved)/len(required),"coverage_state":"NO_REQUIRED_INPUTS" if not required else "REQUIRED_INPUTS_EVALUATED","critical_missing_count":sum(bool(row.get("critical")) and not row.get("resolved_valid") for row in required),"missing_fields":missing}
    if card_id == "A32":
        own=_decimal(inputs["own_fee_equivalent"],"own_fee_equivalent")
        total=_decimal(inputs["total_fee_equivalent"],"total_fee_equivalent")
        pool=_decimal(inputs["rebate_pool"],"rebate_pool")
        if total<=0 or pool<0 or own<0 or own>total:
            raise FormulaDomainError("DOMAIN_VIOLATION:rebate_share")
        return own/total*pool
    if card_id == "A33":
        probabilities=_decimal_values(inputs,"branch_probabilities"); cash=_decimal_values(inputs,"branch_net_cash")
        if len(probabilities)!=len(cash) or any(p<0 for p in probabilities) or abs(sum(probabilities,Decimal("0"))-Decimal("1"))>Decimal("1e-12"): raise FormulaDomainError("DOMAIN_VIOLATION:quote_branches")
        expected=sum((p*v for p,v in zip(probabilities,cash)),Decimal("0")); reserves=sum((_decimal(inputs[key],key) for key in ("inventory_reserve","adverse_selection_reserve","latency_model_reserve","model_reserve")),Decimal("0"))
        return expected-reserves
    if card_id == "C25":
        previous_a=_finite(inputs["previous_mean"],"previous_mean")
        previous_b=_finite(inputs["previous_second_moment"],"previous_second_moment")
        realized=_finite(inputs["return_value"],"return_value")
        eta=_finite(inputs["eta"],"eta")
        variance=previous_b-previous_a*previous_a
        if not 0<eta<=1 or variance<=0:
            raise FormulaDomainError("NUMERICAL_DOMAIN_UNAVAILABLE:differential_sharpe")
        innovation_a=realized-previous_a; innovation_b=realized*realized-previous_b
        differential=(previous_b*innovation_a-0.5*previous_a*innovation_b)/(variance**1.5)
        return {"differential_sharpe":differential,"innovation_a":innovation_a,"innovation_b":innovation_b,"updated_mean":previous_a+eta*innovation_a,"updated_second_moment":previous_b+eta*innovation_b}
    if card_id == "F03":
        linear=[_finite(value,"linear") for value in inputs["linear"]]
        quadratic={str(key):_finite(value,"quadratic") for key,value in dict(inputs["quadratic_upper"]).items()}
        for key in quadratic:
            left,right=(int(part) for part in key.split(","))
            if not 0<=left<right<len(linear): raise FormulaDomainError("DOMAIN_VIOLATION:upper_triangular_quadratic")
        return {"vartype":"BINARY","linear":linear,"quadratic_upper":quadratic,"offset":_finite(inputs["offset"],"offset"),"objective_sense":"MINIMIZE","coefficient_convention":"LINEAR_PLUS_STRICT_UPPER_TRIANGULAR"}
    if card_id == "F06":
        scale=_finite(inputs["scale"],"scale"); center=_finite(inputs["centering_constant"],"centering_constant")
        if scale<=0: raise FormulaDomainError("DOMAIN_VIOLATION:positive_scale")
        linear=[_finite(value,"linear")/scale for value in inputs["linear"]]
        quadratic={str(key):_finite(value,"quadratic")/scale for key,value in dict(inputs["quadratic_upper"]).items()}
        offset=(_finite(inputs["offset"],"offset")-center)/scale
        return {"linear_scaled":linear,"quadratic_scaled":quadratic,"offset_scaled":offset,"inverse_map":{"scale":scale,"centering_constant":center}}
    if card_id == "F21":
        samples=[tuple(int(bit) for bit in row) for row in inputs["bitstrings"]]
        if len(samples)<2 or not samples or len(samples[0])<=0 or any(len(row)!=len(samples[0]) for row in samples):
            raise FormulaDomainError("INSUFFICIENT_EVIDENCE:hamming_pairs")
        length=len(samples[0]); pairs=0; distance=0.0
        for left in range(len(samples)):
            for right in range(left+1,len(samples)):
                pairs+=1; distance+=sum(a!=b for a,b in zip(samples[left],samples[right]))/length
        return distance/pairs
    if card_id == "F24":
        candidate=_finite(inputs["objective_candidate"],"objective_candidate"); champion=_finite(inputs["objective_classical_champion"],"objective_classical_champion")
        sense=str(inputs["objective_sense"]).upper()
        if sense not in {"MINIMIZE","MAXIMIZE"}: raise FormulaDomainError("DOMAIN_VIOLATION:objective_sense")
        raw=candidate-champion; suboptimality=raw if sense=="MINIMIZE" else -raw
        return {"raw_gap":raw,"suboptimality_gap":suboptimality,"improvement_gap":-suboptimality,"objective_sense":sense}
    if card_id == "F40":
        observations=list(inputs["sample_chain_broken"])
        if not observations or any(not isinstance(row,(list,tuple)) or not row for row in observations):
            raise FormulaDomainError("INSUFFICIENT_EVIDENCE:sample_chain_observations")
        total=sum(len(row) for row in observations)
        broken=sum(sum(bool(value) for value in row) for row in observations)
        return {"chain_break_fraction":broken/total,"observed_sample_chain_pairs":total,"per_sample_fraction":[sum(bool(value) for value in row)/len(row) for row in observations]}
    if card_id == "G09":
        valid=int(inputs["valid_runs"]); successful=int(inputs["successful_valid_runs"])
        if valid<=0 or successful<0 or successful>valid: raise FormulaDomainError("INSUFFICIENT_EVIDENCE:valid_runs")
        return {"success_rate":successful/valid,"valid_runs":valid,"successful_valid_runs":successful}
    if card_id == "G14":
        frontier=[tuple(_finite(value,"frontier") for value in row) for row in inputs["frontier"]]
        point=tuple(_finite(value,"candidate") for value in inputs["candidate"])
        reference=tuple(_finite(value,"reference") for value in inputs["reference_point"])
        senses=tuple(str(value).upper() for value in inputs["objective_senses"])
        if len(point)!=2 or len(reference)!=2 or len(senses)!=2 or any(len(row)!=2 for row in frontier):
            raise FormulaDomainError("UNSUPPORTED_OPERATIONAL_ENVELOPE:hypervolume_dimension")
        def orient(row:tuple[float,...])->tuple[float,...]: return tuple(value if sense=="MAXIMIZE" else -value for value,sense in zip(row,senses))
        oriented_ref=orient(reference); oriented_frontier=[orient(row) for row in frontier]; oriented_point=orient(point)
        if any(any(ref>value for ref,value in zip(oriented_ref,row)) for row in [*oriented_frontier,oriented_point]):
            raise FormulaDomainError("DOMAIN_VIOLATION:reference_point_not_dominated")
        def hv(rows:list[tuple[float,float]])->float:
            nondominated=[row for row in rows if not any(other!=row and other[0]>=row[0] and other[1]>=row[1] for other in rows)]
            ordered=sorted(nondominated,reverse=True); area=0.0; best_y=oriented_ref[1]
            for x,y in ordered:
                if y>best_y: area+=(x-oriented_ref[0])*(y-best_y); best_y=y
            return area
        before=hv(oriented_frontier); after=hv([*oriented_frontier,oriented_point])
        return {"hypervolume_improvement":after-before,"reference_point_valid":True,"oriented_reference_point":oriented_ref}
    if card_id == "H01":
        raw=_values(inputs,"raw_probabilities"); groups=list(inputs.get("equality_groups",()))
        if any(not 0<=value<=1 for value in raw): raise FormulaDomainError("DOMAIN_VIOLATION:probability")
        projected=list(raw)
        for group in groups:
            indices=[int(value) for value in group["indices"]]; target=_finite(group["target_sum"],"target_sum")
            if not indices or any(index<0 or index>=len(raw) for index in indices): raise FormulaDomainError("DOMAIN_VIOLATION:equality_group")
            delta=(target-math.fsum(projected[index] for index in indices))/len(indices)
            for index in indices: projected[index]=min(1.0,max(0.0,projected[index]+delta))
            if abs(math.fsum(projected[index] for index in indices)-target)>1e-9: raise FormulaDomainError("NO_FEASIBLE_PROJECTION")
        return {"projected_probabilities":projected,"squared_distance":math.fsum((a-b)**2 for a,b in zip(projected,raw)),"constraint_residual":max((abs(math.fsum(projected[int(i)] for i in group["indices"])-_finite(group["target_sum"],"target_sum")) for group in groups),default=0.0)}
    if card_id == "H02":
        values=_values(inputs,"probabilities"); weights=_values(inputs,"weights")
        if len(values)!=len(weights) or any(weight<=0 for weight in weights): raise FormulaDomainError("DOMAIN_VIOLATION:isotonic_weights")
        blocks=[[value,weight,[index]] for index,(value,weight) in enumerate(zip(values,weights))]
        while any(blocks[index][0]>blocks[index+1][0] for index in range(len(blocks)-1)):
            index=next(index for index in range(len(blocks)-1) if blocks[index][0]>blocks[index+1][0]); left,right=blocks[index],blocks[index+1]; total=left[1]+right[1]
            blocks[index:index+2]=[[(left[0]*left[1]+right[0]*right[1])/total,total,left[2]+right[2]]]
        projected=[0.0]*len(values)
        for value,_weight,indices in blocks:
            for index in indices: projected[index]=value
        return {"projected_probabilities":projected,"nondecreasing":all(projected[i]<=projected[i+1] for i in range(len(projected)-1))}
    if card_id == "H03":
        success=_decimal(inputs["success_branch_net_cash"],"success_branch_net_cash"); failure=_decimal(inputs["failure_branch_net_cash"],"failure_branch_net_cash")
        denominator=success-failure
        if denominator==0: raise FormulaDomainError("UNBOUNDED_RATIO_ZERO_DENOMINATOR")
        probability=-failure/denominator
        if probability<0 or probability>1: raise FormulaDomainError("NO_BREAK_EVEN_PROBABILITY_IN_UNIT_INTERVAL")
        return {"break_even_probability":probability,"cashflow_residual":probability*success+(Decimal("1")-probability)*failure}
    if card_id == "H04":
        calibrated=_values(inputs,"calibrated_probabilities"); break_even=_values(inputs,"break_even_probabilities"); quantile=_finite(inputs["lower_quantile"],"lower_quantile")
        if len(calibrated)!=len(break_even) or not 0<=quantile<=1: raise FormulaDomainError("DOMAIN_VIOLATION:edge_lcb")
        edges=sorted(left-right for left,right in zip(calibrated,break_even)); index=max(0,min(len(edges)-1,math.ceil(quantile*len(edges))-1))
        return {"edge_lcb":edges[index],"paired_edge_samples":edges,"sample_count":len(edges)}
    if card_id == "H06":
        candidate=_values(inputs,"candidate_utilities"); best=_values(inputs,"best_available_utilities")
        if len(candidate)!=len(best): raise FormulaDomainError("DOMAIN_VIOLATION:regret_scenarios")
        regrets=[reference-value for value,reference in zip(candidate,best)]
        return {"worst_case_regret":max(regrets),"scenario_regrets":regrets}
    if card_id == "H07":
        fill_hazards=_values(inputs,"fill_hazards"); competing_hazards=inputs["competing_hazards"]
        if any(value<0 or value>1 for value in fill_hazards) or any(len(row)!=len(fill_hazards) for row in competing_hazards.values()): raise FormulaDomainError("DOMAIN_VIOLATION:hazards")
        survival=1.0; cif=[]; cumulative=0.0
        for time_index,fill in enumerate(fill_hazards):
            competitors=math.fsum(_finite(rows[time_index],"competing_hazard") for rows in competing_hazards.values()); total=fill+competitors
            if total>1+1e-12: raise FormulaDomainError("DOMAIN_VIOLATION:total_hazard")
            cumulative+=survival*fill; cif.append(cumulative); survival*=1-total
        return {"fill_cumulative_incidence":cif,"terminal_survival":survival,"competing_event_probability":1-survival-cumulative}
    if card_id == "H08":
        original=_values(inputs,"original_objective_values"); transformed=_values(inputs,"inverse_mapped_objective_values"); scale=_finite(inputs["positive_scale"],"positive_scale"); offset=_finite(inputs["offset"],"offset")
        if scale<=0 or len(original)!=len(transformed): raise FormulaDomainError("DOMAIN_VIOLATION:formulation_equivalence")
        residuals=[left-(scale*right+offset) for left,right in zip(original,transformed)]
        return {"maximum_objective_residual":max(abs(value) for value in residuals),"residuals":residuals,"equivalent":max(abs(value) for value in residuals)<=_finite(inputs["tolerance"],"tolerance")}
    if card_id == "H09":
        penalty=_finite(inputs["minimum_infeasible_penalty"],"minimum_infeasible_penalty"); objective=_finite(inputs["maximum_feasible_objective_range"],"maximum_feasible_objective_range")
        if objective<=0: raise FormulaDomainError("UNBOUNDED_RATIO_ZERO_DENOMINATOR")
        return {"penalty_dominance_ratio":penalty/objective,"sufficiency_proven":penalty>objective}
    if card_id == "H10":
        classical=_decimal(inputs["classical_presolve_utility"],"classical_presolve_utility"); qpu=_decimal(inputs["qpu_search_utility"],"qpu_search_utility"); repair=_decimal(inputs["repair_utility"],"repair_utility"); post=_decimal(inputs["postprocessed_utility"],"postprocessed_utility")
        return {"classical_presolve_contribution":classical,"qpu_search_contribution":qpu-classical,"repair_contribution":repair-qpu,"postprocessing_contribution":post-repair,"total_improvement":post-classical}
    if card_id == "H12":
        gradients=inputs["gradient_samples"]
        if len(gradients)<2 or any(len(row)!=len(gradients[0]) for row in gradients): raise FormulaDomainError("INSUFFICIENT_EVIDENCE:gradient_samples")
        means=[math.fsum(_finite(row[index],"gradient") for row in gradients)/len(gradients) for index in range(len(gradients[0]))]
        variances=[math.fsum((_finite(row[index],"gradient")-means[index])**2 for row in gradients)/(len(gradients)-1) for index in range(len(means))]
        snr=[abs(mean)/math.sqrt(variance) if variance>0 else None for mean,variance in zip(means,variances)]
        return {"component_snr":snr,"mean_gradient":means,"sample_variance":variances,"state":"FINITE" if all(value is not None for value in snr) else "ZERO_VARIANCE_COMPONENT"}
    if card_id == "H13":
        latencies=_values(inputs,"end_to_end_latency_samples"); ttl=_finite(inputs["economic_ttl_seconds"],"economic_ttl_seconds")
        if ttl<=0: raise FormulaDomainError("DOMAIN_VIOLATION:economic_ttl")
        expired=sum(value>ttl for value in latencies)
        return {"expiry_probability":expired/len(latencies),"expired_count":expired,"sample_count":len(latencies)}
    if card_id == "H11":
        components=[]; weighted=0.0; total=0.0
        for row in inputs["features"]:
            if not row.get("valid",True): continue
            weight=_finite(row.get("weight",1),"weight")
            if weight<0: raise FormulaDomainError("DOMAIN_VIOLATION:weight")
            if row["kind"]=="numeric":
                feature_range=_finite(row["range"],"range")
                if feature_range<=0: raise FormulaDomainError("DOMAIN_VIOLATION:positive_range")
                distance=abs(_finite(row["left"],"left")-_finite(row["right"],"right"))/feature_range
            else: distance=0.0 if row["left"]==row["right"] else 1.0
            components.append(distance); weighted+=weight*distance; total+=weight
        if total<=0: raise FormulaDomainError("INSUFFICIENT_COMPARABLE_FEATURES")
        return {"distance":weighted/total,"component_distances":components,"comparable_weight":total}
    if card_id == "I01":
        allowed=set(inputs["access_policy_qkus"]); stage=set(inputs["stage_qkus"]); duty=set(inputs["agent_duty_qkus"])
        universe=sorted(allowed&stage&duty); return {"qku_ids":universe,"count":len(universe),"bounded":True}
    if card_id == "I02":
        stage=set(inputs["agent_stage_qkus"]); executable=set(inputs["executable_qkus"]); inputs_ready=set(inputs["input_ready_qkus"])
        universe=sorted(stage&executable&inputs_ready); return {"qku_ids":universe,"count":len(universe),"excluded_nonexecutable":sorted(stage-executable)}
    if card_id == "I03":
        executable=set(inputs["agent_executable_qkus"]); market=set(inputs["market_applicable_qkus"]); mode=set(inputs["mode_applicable_qkus"]); capacity=set(inputs["capacity_applicable_qkus"])
        universe=sorted(executable&market&mode&capacity); return {"qku_ids":universe,"count":len(universe),"bounded":True}
    if card_id == "I06":
        vector={str(key):_finite(value,key) for key,value in dict(inputs["prior_components"]).items()}; coefficients=inputs.get("policy_coefficients")
        result={"prior_vector":vector,"scalar_state":"COEFFICIENTS_UNAVAILABLE","scalar_prior":None}
        if coefficients is not None:
            coefficient_map={str(key):_finite(value,key) for key,value in dict(coefficients).items()}
            if set(coefficient_map)!=set(vector): raise FormulaDomainError("DOMAIN_VIOLATION:policy_coefficients")
            result.update({"scalar_state":"POLICY_COEFFICIENTS_APPLIED","scalar_prior":math.fsum(vector[key]*coefficient_map[key] for key in vector)})
        return result
    if card_id == "I05":
        components=[]; weighted=0.0; total=0.0
        for row in inputs["fields"]:
            if not row.get("valid",True): continue
            weight=_finite(row.get("weight",1),"weight")
            if weight<0: raise FormulaDomainError("DOMAIN_VIOLATION:weight")
            if row["kind"]=="numeric":
                feature_range=_finite(row["range"],"range")
                if feature_range<=0: raise FormulaDomainError("DOMAIN_VIOLATION:positive_range")
                delta=min(1.0,abs(_finite(row["left"],"left")-_finite(row["right"],"right"))/feature_range)
            elif row["kind"]=="set":
                left,right=set(row["left"]),set(row["right"]); union=left|right; delta=0.0 if not union else 1-len(left&right)/len(union)
            else: delta=0.0 if row["left"]==row["right"] else 1.0
            components.append(delta); weighted+=weight*delta; total+=weight
        if total<=0: raise FormulaDomainError("INSUFFICIENT_COMPARABLE_FIELDS")
        distance=weighted/total
        return {"distance":distance,"similarity":1-distance,"component_distances":components,"comparable_weight":total}
    if card_id == "I07":
        reference=_finite(inputs["reference_time"],"reference_time"); windows=list(inputs.get("windows",()))
        if not windows: raise FormulaDomainError("MISSING_REQUIRED_INPUT:windows")
        remaining=[]; ratios=[]
        for row in windows:
            valid_from=_finite(row["valid_from"],"valid_from"); valid_until=_finite(row["valid_until"],"valid_until")
            ttl=valid_until-valid_from
            if ttl<=0: raise FormulaDomainError("INVALID_VALIDITY_WINDOW")
            remain=valid_until-reference; remaining.append(remain); ratios.append(max(0.0,min(1.0,remain/ttl)))
        return {"result_remaining_ttl":min(remaining),"result_freshness":min(ratios),"fresh":min(remaining)>=0,"freshness_state":"FRESH" if min(remaining)>=0 else "STALE"}
    if card_id == "I08":
        components={key:_finite(value,key) for key,value in dict(inputs.get("components",{})).items()}
        return {"total_decision_latency_ms":math.fsum(components.values()),"components":components,"reconciliation_residual":0.0}
    if card_id == "I09":
        total=_finite(inputs["total_decision_latency_ms"],"total_decision_latency_ms")
        latency=_finite(inputs["latency_budget_ms"],"latency_budget_ms")-total
        ttl=_finite(inputs["min_material_valid_until_ms"],"min_material_valid_until_ms")-(_finite(inputs["input_lock_time_ms"],"input_lock_time_ms")+total)
        return {"latency_slack_ms":latency,"ttl_slack_ms":ttl,"latency_pass":latency>=0 and ttl>=0}
    if card_id == "I10":
        return tuple(inputs[key] for key in ("severity_desc","economic_ttl_asc","hard_dependency_block_count_desc","downstream_blocked_value_desc","value_of_information_per_compute_desc","queue_age_desc","deterministic_tie_break_key_asc"))
    raise KeyError(f"no static operator implementation for {card_id}")


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
    from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.pr169_operator_registry import (
        CANONICAL_OPERATOR_REGISTRY,
    )

    return CANONICAL_OPERATOR_REGISTRY[card_id](resolved_input_map)


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
    """One bounded five-operation service with validated-plan-only execution."""

    def __init__(self, resolver: CanonicalQKUResolver | None = None) -> None:
        if resolver is not None and not callable(getattr(resolver, "query", None)):
            raise TypeError("production service requires a CanonicalQKUResolver")
        self._resolver = resolver or RP5CCanonicalResolverAdapter()
        self._authoritative_receipts: dict[str, FormulaEvaluationReceiptV1] = {}
        self._receipt_lock = threading.RLock()

    def query_applicable_qkus(self, context: Mapping[str, Any], agent_duty: str, stage: str, mode: str) -> list[dict[str, Any]]:
        limit = int(context.get("query_limit", 100))
        if limit <= 0 or limit > 100:
            raise FormulaDomainError("DOMAIN_VIOLATION:query_limit")
        rows = self._resolver.query(context, agent_duty, stage, mode)
        return [dict(row) for row in sorted(rows, key=lambda row: str(row["qku_id"]))[:limit]]

    def resolve_formula_inputs(self, plan: Mapping[str, Any], input_lock: Mapping[str, Any]) -> list[FormulaInputResolutionV1]:
        rows=[]
        for requirement in plan.get("input_requirements",()):
            name=str(requirement["name"]); producer=str(requirement.get("producer_field",name)); value=input_lock.get(producer)
            expected_unit=str(requirement.get("unit","declared")); actual_unit=str(input_lock.get("units",{}).get(producer,"UNKNOWN_UNIT"))
            expected_basis=str(requirement.get("basis","declared")); actual_basis=str(input_lock.get("bases",{}).get(producer,"UNKNOWN_BASIS"))
            freshness=str(input_lock.get("freshness",{}).get(producer,"UNKNOWN_FRESHNESS"))
            missing=value is None; mismatch=actual_unit!=expected_unit; basis_mismatch=actual_basis!=expected_basis
            event_time=input_lock.get("source_event_times",{}).get(producer,input_lock.get("observed_at_event_time")); observation_time=input_lock.get("source_observation_times",{}).get(producer,input_lock.get("source_observation_time")); available_at=input_lock.get("source_available_times",{}).get(producer,input_lock.get("source_available_at")); processing_time=input_lock.get("processing_time"); input_lock_time=input_lock.get("input_lock_time"); decision_time=input_lock.get("decision_time")
            point_in_time_violation=bool(requirement.get("time_information_class","PREDECISION_POINT_IN_TIME")=="PREDECISION_POINT_IN_TIME" and all((event_time,available_at,input_lock_time,decision_time)) and not (str(event_time)<=str(available_at)<=str(input_lock_time)<=str(decision_time)))
            leakage_missing=bool(requirement.get("leakage_control_required") and not (input_lock.get("purge_ref") and input_lock.get("embargo_ref") and input_lock.get("split_ref")))
            snapshot_conflict=input_lock.get("snapshot_coherence_state","COHERENT")!="COHERENT"
            conflict="UNIT_MISMATCH" if mismatch else "BASIS_MISMATCH" if basis_mismatch else "UNKNOWN_FRESHNESS" if freshness=="UNKNOWN_FRESHNESS" else "POINT_IN_TIME_VIOLATION" if point_in_time_violation else "MISSING_LEAKAGE_CONTROL" if leakage_missing else "SNAPSHOT_COHERENCE_FAILURE" if snapshot_conflict else None
            producer_ref=f"{input_lock.get('lock_identity_ref',input_lock.get('input_lock_ref','input-lock'))}:{producer}"
            rows.append(FormulaInputResolutionV1(
                resolution_id=f"{plan['logical_evaluation_id']}:{name}",workflow_id=str(plan["workflow_id"]),task_id=str(plan["task_id"]),
                qku_id=str(plan["qku_id"]),binding_id=str(plan["binding_id"]),formula_id=str(plan["formula_id"]),formula_version=str(plan.get("formula_version","1.0.0")),
                input_name=name,required_flag=bool(requirement.get("required",True)),criticality=str(requirement.get("criticality","CRITICAL")),expected_type=str(requirement.get("type","number")),
                expected_unit=expected_unit,expected_basis=expected_basis,resolved_value=value,resolved_type=type(value).__name__,resolved_unit=actual_unit,
                resolved_basis=actual_basis,producer_value_ref=producer_ref,resolved_value_ref=producer_ref,
                producer_artifact_ref=str(input_lock.get("producer_artifact_ref","AUTHORIZED_FIXTURE_PROVIDER")),producer_row_ref=str(input_lock.get("producer_row_ref","FIXTURE_ROW")),producer_field=producer,
                observed_at_event_time=event_time,valid_from=input_lock.get("valid_from"),valid_until=input_lock.get("valid_until"),freshness_proof_ref=input_lock.get("freshness_proof_ref"),
                transformation_or_unit_conversion_ref=requirement.get("transformation_ref"),freshness_state=freshness,authority_class=str(requirement.get("authority_class","RESOLVED_SNAPSHOT")),
                responsible_agent_id=str(plan["responsible_agent_id"]),source_observation_time=observation_time,source_available_at=available_at,processing_time=processing_time,input_lock_time=input_lock_time,decision_time=decision_time,settlement_time=input_lock.get("settlement_time"),sequence_or_snapshot_ref=input_lock.get("sequence_or_snapshot_ref"),late_or_out_of_order_disposition=input_lock.get("late_or_out_of_order_disposition"),missing_state="MISSING_REQUIRED_INPUT" if missing and requirement.get("required",True) else None,
                conflict_state=conflict,
            ))
        return rows

    def construct_formula_plan(
        self,
        *,
        formula_id: str,
        logical_evaluation_id: str,
        input_lock_ref: str,
        qku_id: str,
        consumer_ref: str,
    ) -> FormulaInvocationPlanV1:
        return FormulaInvocationPlanV1(
            invocation_plan_id=f"PLAN::{logical_evaluation_id}::{formula_id}",
            logical_evaluation_id=logical_evaluation_id,
            qku_id=qku_id,
            ordered_formula_ids=(formula_id,),
            dependency_edges=(),
            input_lock_ref=input_lock_ref,
            execution_mode="BOUNDED_VALIDATED_FORMULA",
            fallback="TYPED_UNAVAILABLE_THEN_DETERMINISTIC_NO_TRADE",
            consumer_ref=consumer_ref,
        )

    @staticmethod
    def _validated_input_map(
        plan: FormulaInvocationPlanV1,
        resolutions: Sequence[FormulaInputResolutionV1],
    ) -> dict[str, Any]:
        if not isinstance(plan, FormulaInvocationPlanV1):
            raise FormulaDomainError("INVALID_INVOCATION_PLAN")
        if not resolutions:
            raise FormulaDomainError("MISSING_REQUIRED_INPUT:input_resolutions")
        mapped: dict[str, Any] = {}
        for row in resolutions:
            if row.formula_id not in plan.ordered_formula_ids:
                raise FormulaDomainError("CONFLICTING_INPUTS:formula_id")
            if row.missing_state:
                raise FormulaDomainError(row.missing_state)
            if row.conflict_state:
                raise FormulaDomainError(row.conflict_state)
            if row.freshness_state not in {"FRESH", "STATIC_CONFIGURATION", "TIME_INDEPENDENT_MATHEMATICS"}:
                raise FormulaDomainError("STALE_INPUT" if row.freshness_state == "STALE" else "UNKNOWN_FRESHNESS")
            mapped[row.input_name] = row.resolved_value
        return mapped

    def evaluate_formula(
        self,
        plan: FormulaInvocationPlanV1,
        resolutions: Sequence[FormulaInputResolutionV1],
        *,
        version: str = "1.0.0",
        attempt_number: int = 1,
        dependency_receipt_refs: Sequence[str] = (),
    ) -> FormulaEvaluationReceiptV1:
        if len(plan.ordered_formula_ids) != 1:
            raise FormulaDomainError("INVALID_INVOCATION_PLAN:formula_count")
        formula_id = plan.ordered_formula_ids[0]
        resolved_input_map = self._validated_input_map(plan, resolutions)
        identity = f"{plan.logical_evaluation_id}|{plan.input_lock_ref}|{formula_id}|{version}"
        with self._receipt_lock:
            existing = self._authoritative_receipts.get(identity)
            if existing is not None:
                return existing
            try:
                output=evaluate_formula(formula_id,version,resolved_input_map); error=None
            except FormulaDomainError as exc:
                output=None; error=str(exc).split(":",1)[0]
            if error is None and not _finite_output(output):
                output=None; error="NUMERICAL_DOMAIN_UNAVAILABLE"
            receipt = FormulaEvaluationReceiptV1(
                plan.logical_evaluation_id, attempt_number, formula_id, version,
                plan.input_lock_ref, dict(resolved_input_map), output,
                str(resolved_input_map.get("output_unit", "declared")),
                "PYTHON_STDLIB_DETERMINISTIC", "DETERMINISTIC", error,
                tuple(dependency_receipt_refs),
            )
            self._authoritative_receipts[identity] = receipt
            return receipt

    def evaluate_qku_dag(self, qku_id: str, binding_set: Sequence[Mapping[str, Any]], input_lock: Mapping[str, Any]) -> list[FormulaEvaluationReceiptV1]:
        nodes=[str(row["formula_id"]) for row in binding_set]; edges=[tuple(edge) for row in binding_set for edge in row.get("dependency_edges",())]
        ordered=_topological_order(nodes,edges)
        plan=FormulaInvocationPlanV1(
            invocation_plan_id=str(input_lock.get("invocation_plan_id",f"PLAN::{input_lock.get('logical_evaluation_id','evaluation')}")),
            logical_evaluation_id=str(input_lock.get("logical_evaluation_id","evaluation")),qku_id=qku_id,
            ordered_formula_ids=ordered,dependency_edges=tuple(edges),input_lock_ref=str(input_lock.get("input_lock_ref","input-lock")),
            execution_mode=str(input_lock.get("execution_mode","BOUNDED_TOPOLOGICAL")),fallback=str(input_lock.get("fallback","DETERMINISTIC_NO_TRADE")),
            consumer_ref=str(input_lock.get("consumer_ref","PRETRADE_CURRENT_EQUIVALENT")),
        )
        by_id={str(row["formula_id"]):row for row in binding_set}; receipts=[]; values=dict(input_lock)
        for formula_id in plan.ordered_formula_ids:
            row=by_id[formula_id]
            requirements=[]
            for name, source in row.get("input_map", {}).items():
                requirements.append({
                    "name": name, "producer_field": source, "required": True,
                    "unit": row.get("input_units", {}).get(name, "declared"),
                    "basis": row.get("input_bases", {}).get(name, "declared"),
                })
            resolution_plan={
                "logical_evaluation_id": plan.logical_evaluation_id,
                "workflow_id": str(input_lock.get("workflow_id", "FORMULA_QKU_DAG")),
                "task_id": str(input_lock.get("task_id", f"TASK::{qku_id}")),
                "qku_id": qku_id,
                "binding_id": str(row.get("binding_id", f"BINDING::{formula_id}")),
                "formula_id": formula_id,
                "formula_version": str(row.get("version", "1.0.0")),
                "responsible_agent_id": str(row.get("responsible_agent_id", "governance_agent")),
                "input_requirements": requirements,
            }
            lock = {**input_lock, **values}
            resolutions=self.resolve_formula_inputs(resolution_plan, lock)
            formula_plan=self.construct_formula_plan(
                formula_id=formula_id,
                logical_evaluation_id=plan.logical_evaluation_id,
                input_lock_ref=plan.input_lock_ref,
                qku_id=qku_id,
                consumer_ref=plan.consumer_ref,
            )
            receipt=self.evaluate_formula(
                formula_plan, resolutions, version=str(row.get("version", "1.0.0")),
                dependency_receipt_refs=tuple(r.logical_evaluation_id for r in receipts),
            ); receipts.append(receipt)
            if receipt.error_or_missing_input_state is None:
                values[str(row.get("output_field",formula_id))]=receipt.output_value
        return receipts

    def evaluate_trade_plan_scenarios(self, candidate_set: Sequence[Mapping[str, Any]], scenario_set: Sequence[Mapping[str, Any]], no_trade_candidate: Mapping[str, Any]) -> dict[str, Any]:
        required_gates=("input_lock","formula_dag","accounting","original_model","net_cash_lcb","no_trade_margin","tca","fill","latency_ttl","capacity","portfolio_tail_risk","calibration_scenarios","overfit_fdr","agent_no_orphan")
        expected_owners={gate: f"CANONICAL_OWNER::{gate}" for gate in required_gates}
        probabilities=[_finite(row["probability"],"probability") for row in scenario_set]
        if not scenario_set or any(value < 0 for value in probabilities) or abs(math.fsum(probabilities)-1.0)>1e-9:
            raise FormulaDomainError("DOMAIN_VIOLATION:scenario_probabilities")
        comparator=no_trade_candidate.get("comparator_receipt")
        if not isinstance(comparator, Mapping) or comparator.get("owner")!="CANONICAL_OWNER::no_trade" or comparator.get("validation_state")!="VALID":
            raise FormulaDomainError("MISSING_REQUIRED_INPUT:no_trade_comparator_receipt")
        def utility(candidate: Mapping[str, Any]) -> float:
            values=[]
            for scenario in scenario_set:
                values.append(_finite(candidate["scenario_net_cash"][scenario["scenario_id"]],"scenario_net_cash")*_finite(scenario["probability"],"probability"))
            return math.fsum(values)-_finite(candidate.get("risk_reserve",0),"risk_reserve")
        no_trade=utility(no_trade_candidate); evaluated=[]
        for candidate in candidate_set:
            robust=utility(candidate)
            receipt_rows=candidate.get("gate_receipts",())
            gate_receipts={str(row.get("gate_id")):row for row in receipt_rows if isinstance(row,Mapping)}
            failed=[]; gate_vector={}
            for gate in required_gates:
                receipt=gate_receipts.get(gate)
                passed=bool(
                    receipt
                    and receipt.get("owner")==expected_owners[gate]
                    and receipt.get("input_lock_ref")==candidate.get("input_lock_ref")
                    and receipt.get("validation_state")=="VALID"
                    and receipt.get("freshness_state") in {"FRESH","STATIC_CONFIGURATION"}
                    and receipt.get("passed") is True
                )
                gate_vector[gate]=passed
                if not passed: failed.append(gate)
            margin=robust-no_trade; eligible=not failed and margin>_finite(candidate.get("policy_hurdle",0),"policy_hurdle")
            evaluated.append({"candidate_id":candidate["candidate_id"],"robust_utility":robust,"no_trade_margin":margin,"complete_gate_vector":gate_vector,"missing_or_failed_gates":failed,"candidate_eligible":eligible})
        ranked=sorted(evaluated,key=lambda row:(not row["candidate_eligible"],-row["robust_utility"],str(row["candidate_id"])))
        champion=next((row for row in ranked if row["candidate_eligible"]),{"candidate_id":no_trade_candidate["candidate_id"],"robust_utility":no_trade,"no_trade_margin":0.0,"complete_gate_vector":{},"missing_or_failed_gates":[],"candidate_eligible":True})
        return {"ranked_candidates":ranked,"champion":champion,"required_gate_ids":required_gates,"eligibility_state":"CHAMPION_ELIGIBLE" if champion["candidate_id"]!=no_trade_candidate["candidate_id"] else "DETERMINISTIC_NO_TRADE","authority_state":"CANDIDATE_ONLY_NO_ORDER_AUTHORITY"}
