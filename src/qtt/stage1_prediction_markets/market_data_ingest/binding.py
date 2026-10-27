from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    _native_ident, _native_require, _native_retail_decimal_string_v1, _public_counter_v1,
    _public_nanoseconds_v1, _public_price_bands_v1, _public_refs_v1, _public_scalar_tree_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITEventKindV2,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    PITRightsAdmissionReceiptV1,
    PITSourceCurrentizationReceiptV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1SelectedScopeV2,
    Stage1VenueProfileIdV1,
)


PUBLIC_FIELD_TRANSFORMS_V1 = frozenset({
    "EXACT_IDENTITY", "EXACT_DECIMAL_NUMBER_TO_TEXT", "EXACT_DECIMAL_TEXT",
    "LOWERCASE_OUTCOME_TO_CANONICAL_SIDE", "SOURCE_PRICE_BAND", "SOURCE_SCALAR_GRID",
    "DECLARED_SECONDS_TO_NS", "DECLARED_MILLISECONDS_TO_NS", "DECLARED_NANOSECONDS",
    "EXACT_RFC3339", "METADATA_IDENTITY_JOIN", "EXISTING_COMPLEMENT_PAYOUT",
    "EXISTING_REGISTERED_DERIVATION",
})


def _public_field_lineage_v1(rows):
    _native_require(type(rows) is tuple and 0 < len(rows) <= 4096, "missing field lineage")
    identities = set()
    for row in rows:
        _native_require(type(row) is tuple and len(row) == 4, "invalid field lineage row")
        original, pointer, field_name, transform = row
        for value in row:
            _native_ident(value)
        _native_require(pointer.startswith("/") and transform in PUBLIC_FIELD_TRANSFORMS_V1
                        and row not in identities, "unbound or duplicate field lineage")
        identities.add(row)
    return rows


@dataclass(frozen=True, slots=True)
class PublicMetadataSnapshotV1:
    metadata_id: str
    profile_id: Stage1VenueProfileIdV1
    market_id: str
    instrument_id: str
    event_id_or_none: str | None
    series_id_or_none: str | None
    product_class: str
    price_orientation: str
    payout_amount_or_none: str | None
    payout_basis_or_none: str | None
    price_bands: tuple[tuple[str, str, str], ...]
    price_origin_or_none: str | None
    price_increment_or_none: str | None
    quantity_increment_or_none: str | None
    quantity_minimum_or_none: str | None
    quantity_origin_or_none: str | None
    lifecycle: Mapping[str, object]
    resolution: Mapping[str, object]
    field_lineage: tuple[tuple[str, str, str, str], ...]
    known_at_ns: int
    effective_from_ns: int
    effective_until_ns_or_none: int | None
    expires_at_ns: int
    generation: int
    unavailable_fields: tuple[str, ...]

    def __post_init__(self):
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import _public_profile_v1

        _public_profile_v1(self.profile_id)
        for name in ("metadata_id", "market_id", "instrument_id", "product_class", "price_orientation"):
            _native_ident(getattr(self, name))
        for name in ("event_id_or_none", "series_id_or_none", "payout_basis_or_none"):
            if getattr(self, name) is not None:
                _native_ident(getattr(self, name))
        for name in ("payout_amount_or_none", "price_origin_or_none", "price_increment_or_none",
                     "quantity_increment_or_none", "quantity_minimum_or_none", "quantity_origin_or_none"):
            value = getattr(self, name)
            if value is not None:
                number = Fraction(_native_retail_decimal_string_v1(value))
                _native_require(number >= 0 and (number > 0 if name in {
                    "payout_amount_or_none", "price_increment_or_none", "quantity_increment_or_none"} else True),
                    "invalid source metadata numeric domain")
        _native_require((self.payout_amount_or_none is None) == (self.payout_basis_or_none is None),
                        "incomplete payout basis")
        _native_require(type(self.price_bands) is tuple, "invalid source bands")
        if self.price_bands:
            _public_price_bands_v1(self.price_bands)
            _native_require(self.price_origin_or_none is self.price_increment_or_none is None,
                            "ambiguous source price grid")
        else:
            _native_require(self.price_origin_or_none is not None and self.price_increment_or_none is not None,
                            "source scalar price grid unavailable")
        for name, allowed in (
            ("lifecycle", {"state", "native_state", "observation_ref", "effective_at_ns", "unavailable_reason"}),
            ("resolution", {"state", "outcome", "value", "final", "revision", "effective_at_ns",
                            "known_at_ns", "observation_ref", "unavailable_reason"}),
        ):
            value = getattr(self, name)
            _native_require(type(value) in (dict, MappingProxyType) and set(value) <= allowed
                            and "state" in value and type(value["state"]) is str, "invalid lifecycle/resolution fields")
            for key, item in value.items():
                _native_require(item is None or type(item) in (str, bool, int), "non-scalar lifecycle/resolution fact")
                if key.endswith("_ns"):
                    _public_nanoseconds_v1(item)
                if key == "final":
                    _native_require(type(item) is bool, "finality must be an exact Boolean")
            object.__setattr__(self, name, _public_scalar_tree_v1(value))
        _public_field_lineage_v1(self.field_lineage)
        _public_refs_v1(self.unavailable_fields, allow_empty=True)
        if self.quantity_origin_or_none is None:
            _native_require("UNAVAILABLE_QUANTITY_ORIGIN" in self.unavailable_fields,
                            "quantity minimum is not a source grid origin")
        for name in ("known_at_ns", "effective_from_ns", "expires_at_ns"):
            _public_nanoseconds_v1(getattr(self, name))
        if self.effective_until_ns_or_none is not None:
            _public_nanoseconds_v1(self.effective_until_ns_or_none)
            _native_require(self.effective_from_ns < self.effective_until_ns_or_none, "empty metadata interval")
        _native_require(self.known_at_ns < self.expires_at_ns, "metadata expires before known time")
        _public_counter_v1(self.generation, allow_zero=True)


def _validate_public_contract_terms_v1(*, facts, field_bindings, original_ref):
    """Validate accepted documentary payoff/resolution facts without custody."""
    required = {"instrument_id", "market_id", "event_id_or_none", "series_id_or_none", "product_class",
        "price_orientation", "payout_amount_or_none", "payout_basis_or_none", "effective_from_ns",
        "effective_until_ns", "generation", "resolution_or_none"}
    _native_require(type(facts) in (list, tuple) and 0 < len(facts) <= 4096, "accepted contract terms are absent")
    identities = set()
    for index, row in enumerate(facts):
        _native_require(type(row) in (dict, MappingProxyType) and required <= set(row)
                        <= required | {"grid_rules_or_none"},
                        "accepted contract terms have missing or extra fields")
        for name in ("instrument_id", "market_id", "product_class", "price_orientation"):
            _native_ident(row[name])
        for name in ("event_id_or_none", "series_id_or_none", "payout_basis_or_none"):
            if row[name] is not None:
                _native_ident(row[name])
        _native_require(row["instrument_id"] not in identities, "duplicate accepted contract terms")
        identities.add(row["instrument_id"])
        _native_require(("contract_terms."+row["instrument_id"], "OBJECT", "EVIDENCE_USE_CONTRACT_TERMS",
            original_ref, "/contract_terms/"+str(index), "EXACT_IDENTITY") in field_bindings,
            "contract terms lack their exact accepted field")
        _public_counter_v1(row["generation"], allow_zero=True)
        for name in ("effective_from_ns", "effective_until_ns"):
            _public_nanoseconds_v1(row[name])
        _native_require(row["effective_from_ns"] < row["effective_until_ns"], "empty accepted contract interval")
        _native_require((row["payout_amount_or_none"] is None) == (row["payout_basis_or_none"] is None),
                        "accepted payout basis is incomplete")
        if row["payout_amount_or_none"] is not None:
            _native_require(Fraction(_native_retail_decimal_string_v1(row["payout_amount_or_none"])) > 0,
                            "accepted contractual payout must be positive")
        grid = row.get("grid_rules_or_none")
        if grid is not None:
            _native_require(type(grid) in (dict, MappingProxyType) and set(grid) == {
                "price_origin_or_none", "quantity_origin_or_none", "quantity_increment_or_none"},
                "accepted documentary grid rules have missing or extra fields")
            for name, value in grid.items():
                if value is not None:
                    number = Fraction(_native_retail_decimal_string_v1(value))
                    _native_require(number > 0 if name == "quantity_increment_or_none" else number >= 0,
                                    "invalid accepted documentary grid rule")
        resolution = row["resolution_or_none"]
        if resolution is not None:
            _native_require(type(resolution) in (dict, MappingProxyType)
                and set(resolution) == {"state", "outcome", "final", "revision", "effective_at_ns"}
                and resolution["state"] in {"RESOLVED", "SETTLED", "UNDER_REVIEW", "VOID", "UNAVAILABLE"}
                and resolution["outcome"] in {"YES", "NO", "UNAVAILABLE"}
                and type(resolution["final"]) is bool, "invalid accepted resolution facts")
            _native_ident(resolution["revision"])
            _public_nanoseconds_v1(resolution["effective_at_ns"])
    return tuple(_public_scalar_tree_v1(row) for row in facts)


def _public_contract_terms_values_v1(*, terms, source_binding, original_ref):
    values = {name: terms[name] for name in ("product_class", "price_orientation")}
    values.update(payout_amount=terms["payout_amount_or_none"], payout_basis=terms["payout_basis_or_none"])
    if terms.get("grid_rules_or_none") is not None:
        values.update((name, value) for name,value in terms["grid_rules_or_none"].items() if value is not None)
    if terms["resolution_or_none"] is not None:
        values.update(("resolution."+key, value) for key, value in terms["resolution_or_none"].items())
        values.update({"resolution.known_at_ns": source_binding.known_at_ns,
                       "resolution.observation_ref": original_ref})
    return values


def _public_contract_term_path_v1(name):
    if name in {"price_origin_or_none", "quantity_origin_or_none", "quantity_increment_or_none"}:
        return "grid_rules_or_none/"+name
    return {"payout_amount":"payout_amount_or_none", "payout_basis":"payout_basis_or_none"}.get(
        name,name.replace("resolution.","resolution_or_none/"))


def compile_accepted_public_contract_terms_v1(*, metadata, source_binding, acceptance_results, originals, review_facts):
    """Attach accepted terms to a metadata candidate; publication grants no cash."""
    from dataclasses import replace
    from .source_dependency import project_accepted_public_field_bindings_v1
    from ..qku_computation_control_plane.receipts import _public_identity_v1

    _native_require(type(metadata) is PublicMetadataSnapshotV1, "accepted terms require exact selected metadata")
    projection = project_accepted_public_field_bindings_v1(source_binding=source_binding,
        acceptance_results=acceptance_results, originals=originals, review_facts=review_facts)
    selected = []
    for bundle in projection[2]:
        packet = bundle["accepted_packet"]
        facts = packet["extracted_fact_payload"].get("contract_terms")
        if facts is None:
            continue
        original = packet["accepted_source_evidence_packet_id"]
        for index, terms in enumerate(_validate_public_contract_terms_v1(facts=facts,
                field_bindings=source_binding.field_bindings, original_ref=original)):
            if terms["instrument_id"] == metadata.instrument_id:
                selected.append((index, terms, original))
    _native_require(len(selected) == 1, "selected accepted contract terms are missing or conflicting")
    index, terms, original = selected[0]
    _native_require(source_binding.profile_id is metadata.profile_id and all(terms[key] == getattr(metadata,key)
        for key in ("market_id", "event_id_or_none", "series_id_or_none")), "accepted contract parent scope differs")
    values = _public_contract_terms_values_v1(terms=terms, source_binding=source_binding, original_ref=original)
    lineage = tuple(row for row in metadata.field_lineage if row[2] not in values) + tuple(
        (original, "/contract_terms/"+str(index)+"/"+_public_contract_term_path_v1(name),
         name, "EXACT_IDENTITY") for name in values if name not in {"resolution.known_at_ns", "resolution.observation_ref"})
    known = max(metadata.known_at_ns,source_binding.known_at_ns)
    end = min(terms["effective_until_ns"],source_binding.expires_at_ns,metadata.expires_at_ns,
        *(value for value in (metadata.effective_until_ns_or_none,source_binding.effective_until_ns_or_none) if value is not None))
    start = max(metadata.effective_from_ns,source_binding.effective_from_ns,terms["effective_from_ns"])
    _native_require(start <= known < end, "accepted contract terms unavailable at metadata knowledge time")
    changes = dict(product_class=terms["product_class"],price_orientation=terms["price_orientation"],
        payout_amount_or_none=terms["payout_amount_or_none"],payout_basis_or_none=terms["payout_basis_or_none"])
    changes.update((name,value) for name,value in values.items() if name.endswith("_or_none"))
    if changes.get("quantity_origin_or_none") is not None:
        changes["unavailable_fields"] = tuple(row for row in metadata.unavailable_fields if row != "UNAVAILABLE_QUANTITY_ORIGIN")
    if terms["resolution_or_none"] is not None:
        _native_require(metadata.resolution["state"] in {"UNRESOLVED", "UNAVAILABLE"},
                        "accepted resolution needs explicit successor custody")
        changes.update(resolution={key.removeprefix("resolution."):value for key,value in values.items() if key.startswith("resolution.")},
            lifecycle=dict(state=terms["resolution_or_none"]["state"],observation_ref=original,
                effective_at_ns=terms["resolution_or_none"]["effective_at_ns"]))
    return replace(metadata,metadata_id=_public_identity_v1("PUBLIC_ACCEPTED_TERMS_V1",original,metadata.metadata_id,
        metadata.instrument_id,metadata.generation+1,terms["generation"],known,start,end),
        field_lineage=lineage,known_at_ns=known,effective_from_ns=start,
        effective_until_ns_or_none=end,expires_at_ns=end,generation=metadata.generation+1,**changes)


def _public_metadata_lineage_sources_v1(*, metadata, inputs, originals, native_only, known_as_of_ns, translations=()):
    """Join non-capture terms to the exact retained acceptance proof and values."""
    captured = {row.observation_id for row in originals}
    accepted, result = [], []
    for projection in inputs.get("qualified_source_bindings", ()):
        _native_require(type(projection) is tuple and len(projection) == 5, "malformed retained metadata terms proof")
        source = projection[0]
        if (native_only and projection[4] is not True
                or not any(source is row for row in inputs["source_bindings"]) or source.known_at_ns > known_as_of_ns):
            continue
        for bundle in projection[2]:
            packet = bundle["accepted_packet"]
            facts = packet["extracted_fact_payload"].get("contract_terms")
            if facts is not None:
                original = packet["accepted_source_evidence_packet_id"]
                accepted.extend((source,index,terms,original) for index,terms in enumerate(
                    _validate_public_contract_terms_v1(facts=facts,field_bindings=source.field_bindings,original_ref=original)))
    for item in metadata:
        scoped = tuple(row for row in accepted if row[0].profile_id is item.profile_id
                       and row[2]["instrument_id"] == item.instrument_id)
        if not native_only and not scoped and not any(row[1].startswith("/contract_terms/") for row in item.field_lineage):
            continue
        active = tuple(row for row in scoped if row[2]["effective_from_ns"] <= known_as_of_ns < row[2]["effective_until_ns"]
            and row[0].effective_from_ns <= known_as_of_ns < row[0].expires_at_ns
            and (row[0].effective_until_ns_or_none is None or known_as_of_ns < row[0].effective_until_ns_or_none))
        _native_require(len(active) == 1, "metadata documentary original lacks unique accepted custody")
        source,index,terms,original = active[0]
        _native_require(all(terms[key] == getattr(item,key) for key in ("market_id","event_id_or_none","series_id_or_none")),
                        "accepted contract parent scope differs")
        future = tuple(row for row in scoped if row[2]["effective_from_ns"] > known_as_of_ns)
        end = min(terms["effective_until_ns"],source.expires_at_ns,
            *(value for value in (source.effective_until_ns_or_none,) if value is not None),
            *(row[2]["effective_from_ns"] for row in future))
        _native_require(source.known_at_ns <= item.known_at_ns <= known_as_of_ns
            and item.effective_from_ns >= max(terms["effective_from_ns"],source.effective_from_ns)
            and item.effective_until_ns_or_none is not None and item.effective_until_ns_or_none <= end
            and item.expires_at_ns <= end, "metadata interval exceeds accepted documentary terms")
        values = _public_contract_terms_values_v1(terms=terms,source_binding=source,original_ref=original)
        required = {"product_class","price_orientation","payout_amount","payout_basis"}
        required.update(name for name in values if name.endswith("_or_none"))
        if terms["resolution_or_none"] is not None or item.resolution["state"] not in {"UNRESOLVED","UNAVAILABLE"}:
            required.update("resolution."+name for name in ("state","outcome","final","revision","effective_at_ns"))
            _native_require(item.resolution.get("known_at_ns") == source.known_at_ns
                and item.resolution.get("observation_ref") == original, "resolution knowledge/original differs from accepted terms")
            _native_require(not (item.resolution.get("final") is True and item.lifecycle["state"] == "OPEN"),
                            "catalog reopening conflicts with accepted final resolution")
        expected = []
        for name in required:
            path = _public_contract_term_path_v1(name)
            actual = (item.resolution.get(name.removeprefix("resolution.")) if name.startswith("resolution.") else
                getattr(item,{"payout_amount":"payout_amount_or_none","payout_basis":"payout_basis_or_none"}.get(name,name),None))
            row = (original,"/contract_terms/"+str(index)+"/"+path,name,"EXACT_IDENTITY")
            _native_require(name in values and actual == values[name]
                and tuple(line for line in item.field_lineage if line[2] == name
                    and (not name.endswith("_or_none") or line[1].startswith("/contract_terms/"))) == (row,),
                "accepted metadata term differs from its original field or interval")
            expected.append(row)
        _native_require(not native_only or all(row[0] in captured or row in expected for row in item.field_lineage),
                        "metadata documentary original lacks unique accepted custody")
        if native_only:
            _validate_public_metadata_grid_lineage_v1(metadata=item,originals=originals,
                translations=translations,documentary_values=values,documentary_lineage=tuple(expected))
        for dependency in (source,*(row[0] for row in future)):
            if not any(dependency is row for row in result):
                result.append(dependency)
    return tuple(result)


def _validate_public_metadata_grid_lineage_v1(*, metadata, originals, translations,
                                             documentary_values, documentary_lineage):
    """Check material grids against reconstructed catalogs, never seed labels.

    The publication owner supplies translations already reproduced from committed
    bytes. Documentary origins remain separate from observable minima and steps.
    This validation function grants no capture or publication authority.
    """
    import base64
    from .adapter import _public_native_tree_v1

    original_by_id = {row.observation_id: row for row in originals}
    values = {name:value for name,value in documentary_values.items() if name.endswith("_or_none")}
    lineage = {name:tuple(row for row in documentary_lineage if row[2] == name) for name in values}
    for translation in translations:
        if translation.stream_disposition["kind"] != "METADATA":
            continue
        original = original_by_id.get(translation.observation_ref)
        _native_require(original is not None, "metadata catalog lacks its committed original")
        body = translation.normalized_frame.parsed_source_scalar_tree_or_none
        material = tuple(row for row in translation.field_lineage if row[0] == original.observation_id)
        projected = {}
        pointers = {}
        if original.operation_id == "K_MARKET" and body["market"]["ticker"] == metadata.instrument_id:
            projected["price_bands"] = tuple((row["start"],row["end"],row["step"]) for row in body["market"]["price_ranges"])
            pointers["price_bands"] = {"/market/price_ranges",*(f"/market/price_ranges/{i}/{name}"
                for i in range(len(projected["price_bands"])) for name in ("start","end","step"))}
        elif original.operation_id == "P_MARKET" and body["marketId"] == metadata.market_id:
            for name,native in (("price_increment_or_none","orderPriceMinTickSize"),
                                ("quantity_minimum_or_none","minimumTradeQty")):
                projected[name],pointers[name] = body[native],{"/market/"+native}
        elif original.operation_id in {"G_EVENT","G_EVENTS"}:
            selected = tuple(row for row in body["contracts"] if row["instrumentSymbol"] == metadata.instrument_id)
            if not selected:
                continue
            _native_require(len(selected) == 1, "metadata catalog instrument is ambiguous")
            raw = _public_native_tree_v1(base64.urlsafe_b64decode(original.raw_body_b64
                + "="*(-len(original.raw_body_b64)%4)),maximum_bytes=1048576)
            events = (("",raw),) if original.operation_id == "G_EVENT" else tuple(
                (f"/data/{index}",event) for index,event in enumerate(raw["data"]))
            prefixes = tuple(base+f"/contracts/{index}/" for base,event in events
                if event["ticker"] == metadata.event_id_or_none for index,row in enumerate(event["contracts"])
                if row["instrumentSymbol"] == metadata.instrument_id)
            _native_require(len(prefixes) == 1, "metadata grid contract pointer is ambiguous")
            for name,native in (("price_origin_or_none","priceMinimum"),("price_increment_or_none","priceIncrement"),
                    ("quantity_increment_or_none","quantityIncrement"),("quantity_minimum_or_none","quantityMinimum")):
                projected[name],pointers[name] = selected[0][native],{prefixes[0]+native}
        for name,value in projected.items():
            proof = tuple(row for row in material if row[1] in pointers[name])
            _native_require(len(proof) == len(pointers[name]) and {row[1] for row in proof} == pointers[name],
                            "metadata grid lacks complete catalog field coverage")
            if name in documentary_values:
                _native_require(value == documentary_values[name], "catalog grid conflicts with accepted documentary rule")
            values[name],lineage[name] = value,proof
    names = ("price_bands",) if metadata.price_bands else ("price_origin_or_none","price_increment_or_none")
    names += tuple(name for name in ("quantity_increment_or_none","quantity_minimum_or_none","quantity_origin_or_none")
                   if getattr(metadata,name) is not None)
    for name in names:
        _native_require(name in values and getattr(metadata,name) == values[name] and lineage[name]
            and all(row in metadata.field_lineage for row in lineage[name]),
            "metadata grid value lacks its exact accepted original field: "+name)
    if metadata.quantity_origin_or_none is None:
        _native_require("UNAVAILABLE_QUANTITY_ORIGIN" in metadata.unavailable_fields,
                        "unavailable quantity origin was inferred from a minimum")


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref_from_value(scope_value: str) -> policy.ScopeRef:
    scope_kind = "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope"
    return policy.ScopeRef(scope_kind, scope_value)


def build_adapter_bindings(
    adapter_inputs: list[Mapping[str, object]],
    canonical_events: list[Mapping[str, object]],
    source_dependencies: list[Mapping[str, object]],
    credential_handoff_ref: str,
) -> list[dict[str, object]]:
    inputs_by_scope: dict[str, list[str]] = {}
    events_by_scope: dict[str, list[str]] = {}
    deps_by_scope: dict[str, list[str]] = {}
    connector_refs_by_scope: dict[str, list[str]] = {}
    for record in adapter_inputs:
        inputs_by_scope.setdefault(_scope_value(record), []).append(str(record["input_id"]))
    for record in canonical_events:
        events_by_scope.setdefault(_scope_value(record), []).append(str(record["event_id"]))
    for record in source_dependencies:
        scope_value = _scope_value(record)
        deps_by_scope.setdefault(scope_value, []).append(str(record["dependency_id"]))
        connector_ref = record.get("connector_semantic_binding_ref")
        if connector_ref:
            connector_refs_by_scope.setdefault(scope_value, []).append(str(connector_ref))

    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        records.append(
            {
                **policy.common_record_fields("VENUE_MARKET_DATA_ADAPTER_BINDING"),
                **policy.scope_field(_scope_ref_from_value(scope_value)),
                "binding_id": f"PR132_{scope_value}_MARKET_DATA_ADAPTER_BINDING_V1",
                "adapter_name": f"PR132_{scope_value}_FIXTURE_MARKET_DATA_INGEST_ADAPTER",
                "adapter_version": "v1",
                "adapter_scope": "FIXTURE_BACKED_CONTRACT_ONLY",
                "input_refs": inputs_by_scope[scope_value],
                "output_event_refs": events_by_scope[scope_value],
                "credential_readiness_handoff_ref": credential_handoff_ref,
                "source_dependency_refs": deps_by_scope[scope_value],
                "connector_semantic_dependency_refs": sorted(
                    connector_refs_by_scope.get(scope_value, [])
                ),
                "allowed_use": "FIXTURE_BACKED_MARKET_DATA_INGEST_CONTRACT_ONLY",
                "disallowed_use": list(policy.DISALLOWED_USE),
                "future_live_use_requires_owner_approval": True,
                "future_live_use_requires_accepted_source_packet": True,
                "future_live_use_requires_fresh_revalidation_state": True,
                "future_live_use_requires_connector_semantic_binding": True,
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed": True,
                "future_quantum_use_requires_pr115_pr116_pr117_data_chain": True,
                "future_quantum_use_requires_replay_paper_validation": True,
                "future_quantum_use_requires_owner_approval": True,
            }
        )
    return records


def _pit_binding_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_binding_text_tuple(
    value: object,
    name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple or (not allow_empty and not value):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact tuple",
        )
    result = tuple(_pit_binding_text(item, name) for item in value)
    if len(result) != len(set(result)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            f"{name} contains duplicate values",
        )
    return result


def _pit_binding_boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact boolean",
        )
    return value


@dataclass(frozen=True, slots=True)
class SelectedPITPublicDataContractV2:
    contract_id: str
    contract_version: str
    profile_id: Stage1VenueProfileIdV1
    scope_receipt_ref: str
    operating_legal_entity: str
    product_profile: str
    jurisdiction: str
    production_rest_base: str
    websocket_url: str
    allowed_access_classes: tuple[policy.PITAccessClassV1, ...]
    allowed_methods: tuple[policy.PITReadActionV1, ...]
    allowed_paths: tuple[str, ...]
    allowed_channels: tuple[str, ...]
    wire_dialect_policy: str
    subscription_form: str
    sequence_model: str
    snapshot_model: str
    recovery_model: str
    heartbeat_model: str
    admitted_event_kinds: tuple[PITEventKindV2, ...]
    event_identity_fields: tuple[str, ...]
    market_identity_fields: tuple[str, ...]
    instrument_identity_fields: tuple[str, ...]
    outcome_and_side_fields: tuple[str, ...]
    depth_class: PITDepthClassV2
    price_quantity_tick_model: str
    lifecycle_and_finality_fields: tuple[str, ...]
    source_currentization_receipt_ref: str
    source_contract_version: str
    rights_receipt_ref: str
    agreement_version: str
    credential_alias_required: bool
    no_private_state_authority: bool
    no_order_authority: bool
    default_failure_reason: PITReasonCodeV1
    unavailable_capabilities: tuple[str, ...]
    recovery_preconditions: tuple[str, ...]
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "contract profile is outside the selected Stage-1 scope",
            )
        for name in (
            "contract_id",
            "contract_version",
            "scope_receipt_ref",
            "operating_legal_entity",
            "product_profile",
            "jurisdiction",
            "production_rest_base",
            "websocket_url",
            "wire_dialect_policy",
            "subscription_form",
            "sequence_model",
            "snapshot_model",
            "recovery_model",
            "heartbeat_model",
            "price_quantity_tick_model",
            "source_currentization_receipt_ref",
            "source_contract_version",
            "rights_receipt_ref",
            "agreement_version",
        ):
            _pit_binding_text(getattr(self, name), name)
        if self.contract_version != "S1_PIT_PUBLIC_DATA_CONTRACT_V2":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "selected public-data contract version is not exact V2",
            )
        for name in (
            "allowed_paths",
            "allowed_channels",
            "event_identity_fields",
            "market_identity_fields",
            "instrument_identity_fields",
            "outcome_and_side_fields",
            "lifecycle_and_finality_fields",
            "unavailable_capabilities",
            "recovery_preconditions",
        ):
            _pit_binding_text_tuple(
                getattr(self, name),
                name,
                allow_empty=name == "unavailable_capabilities",
            )
        if type(self.allowed_access_classes) is not tuple or not self.allowed_access_classes or any(
            type(value) is not policy.PITAccessClassV1
            for value in self.allowed_access_classes
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "allowed access classes must be exact typed values",
            )
        if type(self.allowed_methods) is not tuple or not self.allowed_methods or any(
            type(value) is not policy.PITReadActionV1 for value in self.allowed_methods
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "allowed methods must be exact typed values",
            )
        if type(self.admitted_event_kinds) is not tuple or not self.admitted_event_kinds or any(
            type(value) is not PITEventKindV2 for value in self.admitted_event_kinds
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "admitted event kinds must be exact PITEventKindV2 values",
            )
        if len(self.admitted_event_kinds) != len(set(self.admitted_event_kinds)):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "admitted event kinds must be unique",
            )
        if type(self.depth_class) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "depth class has the wrong exact type",
            )
        for name in (
            "credential_alias_required",
            "no_private_state_authority",
            "no_order_authority",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if not self.no_private_state_authority or not self.no_order_authority:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "selected public-data contracts have no private/order authority",
            )
        if type(self.default_failure_reason) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "default failure reason has the wrong exact type",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "selected contract must use exact NO_EFFECTS_V1",
            )
        _pit_validate_exact_profile_contract_v2(self)


_PIT_EVENT_KINDS_BY_PROFILE = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.SOURCE_STATUS,
    ),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_REPLACEMENT,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    ),
})


_PIT_UNAVAILABLE_BY_PROFILE = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: (
        "PROVIDER_PUBLICATION_TIME",
        "PROVIDER_HISTORICAL_ORDERBOOK_CHANGE_STREAM",
        "PROVIDER_REVISION_HISTORY",
    ),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: (
        "PROVIDER_NUMERIC_SEQUENCE",
        "WEBSOCKET_COMPLETE_PROVIDER_DEPTH",
        "EXACT_CHANGE_LEVEL_HISTORY",
        "EXACT_IMMUTABLE_TRADE_IDENTITY",
        "PROVIDER_PUBLICATION_TIME",
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: (
        "PROVIDER_PUBLICATION_TIME",
        "PROVIDER_HISTORICAL_ORDERBOOK_CHANGE_STREAM",
        "PROVIDER_REVISION_HISTORY",
    ),
})


def _pit_validate_exact_profile_contract_v2(
    contract: SelectedPITPublicDataContractV2,
) -> None:
    """Prevent a typed contract copy from widening the frozen profile policy."""

    profile_row = next(
        row
        for row in policy.PIT_SELECTED_SCOPE_V2.profiles
        if row.profile_id is contract.profile_id
    )
    protocol = policy._pit_profile_protocol_policy_v2(contract.profile_id)
    expected_fields: dict[str, object] = {
        "contract_id": f"S1-PIT-PUBLIC-DATA::{contract.profile_id.value}::V2",
        "scope_receipt_ref": policy.PIT_SELECTED_SCOPE_V2.source_decision_ref,
        "operating_legal_entity": profile_row.operating_legal_entity,
        "product_profile": profile_row.api_profile,
        "jurisdiction": profile_row.jurisdiction,
        "production_rest_base": protocol["production_rest_base"],
        "websocket_url": protocol["websocket_url"],
        "allowed_access_classes": protocol["allowed_access_classes"],
        "allowed_methods": protocol["allowed_methods"],
        "allowed_paths": protocol["allowed_paths"],
        "allowed_channels": protocol["allowed_channels"],
        "wire_dialect_policy": protocol["wire_dialect_policy"],
        "subscription_form": (
            "use_yes_price=true"
            if contract.profile_id
            is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
            else "EXACT_PROFILE_ALLOWLISTED_SUBSCRIPTION"
        ),
        "sequence_model": protocol["sequence_model"],
        "snapshot_model": protocol["snapshot_model"],
        "recovery_model": protocol["recovery_model"],
        "heartbeat_model": protocol["heartbeat_model"],
        "admitted_event_kinds": _PIT_EVENT_KINDS_BY_PROFILE[contract.profile_id],
        "event_identity_fields": ("event_id", "event_kind", "source_version"),
        "market_identity_fields": ("market_id", "market_slug_or_ticker"),
        "instrument_identity_fields": ("instrument_id", "source_symbol"),
        "outcome_and_side_fields": (
            "source_outcome_id",
            "source_side",
            "canonical_side",
        ),
        "depth_class": protocol["depth_class"],
        "price_quantity_tick_model": (
            "CANONICAL_DECIMAL_TEXT_SCALE_ORIGIN_INCREMENT"
        ),
        "lifecycle_and_finality_fields": (
            "lifecycle_state",
            "lifecycle_version",
            "settlement_finality_time_or_none",
        ),
        "credential_alias_required": protocol["credential_alias_required"],
        "default_failure_reason": PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
        "unavailable_capabilities": _PIT_UNAVAILABLE_BY_PROFILE[
            contract.profile_id
        ],
        "recovery_preconditions": (
            "NEW_CONNECTION_EPOCH",
            "FRESH_VALID_ANCHOR_OR_CURRENT_STATE_FRAME",
            "INDEPENDENT_RECONSTRUCTION_VALID",
            "CURRENT_SOURCE_AND_RIGHTS",
        ),
    }
    mismatched = tuple(
        name
        for name, expected in expected_fields.items()
        if getattr(contract, name) != expected
    )
    if mismatched:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
            "selected contract differs from its exact frozen profile policy: "
            + ", ".join(mismatched),
        )


def build_selected_pit_public_data_contracts_v2(
    selected_scope: Stage1SelectedScopeV2,
    source_currentization_receipts: tuple[PITSourceCurrentizationReceiptV1, ...],
    rights_receipts: tuple[PITRightsAdmissionReceiptV1, ...],
    *,
    evaluated_at_utc: datetime,
) -> tuple[SelectedPITPublicDataContractV2, ...]:
    """Build the three selected contracts in the sole scope serialization order."""

    if type(selected_scope) is not Stage1SelectedScopeV2 or selected_scope != (
        policy.PIT_SELECTED_SCOPE_V2
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "selected_scope must equal the sole Stage1SelectedScopeV2 authority",
        )
    if type(source_currentization_receipts) is not tuple or any(
        type(value) is not PITSourceCurrentizationReceiptV1
        for value in source_currentization_receipts
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
            "source receipts must be exact typed values",
        )
    if type(rights_receipts) is not tuple or any(
        type(value) is not PITRightsAdmissionReceiptV1 for value in rights_receipts
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
            "rights receipts must be exact typed values",
        )
    source_by_profile = {value.profile_id: value for value in source_currentization_receipts}
    rights_by_profile = {value.profile_id: value for value in rights_receipts}
    expected = set(selected_scope.serialization)
    if (
        len(source_by_profile) != len(source_currentization_receipts)
        or len(rights_by_profile) != len(rights_receipts)
        or set(source_by_profile) != expected
        or set(rights_by_profile) != expected
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "source and rights receipt profile sets must equal selected scope",
        )
    if (
        type(evaluated_at_utc) is not datetime
        or evaluated_at_utc.tzinfo is None
        or evaluated_at_utc.utcoffset() is None
        or evaluated_at_utc.utcoffset().total_seconds() != 0
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            "evaluated_at_utc must be an aware UTC datetime",
        )
    else:
        evaluated = evaluated_at_utc.astimezone(UTC)
    profile_by_id = {value.profile_id: value for value in selected_scope.profiles}
    contracts: list[SelectedPITPublicDataContractV2] = []
    for profile_id in selected_scope.serialization:
        source = source_by_profile[profile_id]
        rights = rights_by_profile[profile_id]
        if (
            evaluated < source.effective_at_utc
            or evaluated < source.checked_at_utc
            or evaluated - source.checked_at_utc > timedelta(hours=24)
            or evaluated < rights.checked_at_utc
            or evaluated >= source.expires_at_utc
            or evaluated >= rights.expires_at_utc
            or source.source_id != rights.source_id
            or source.invalidating_change_detected
            or rights.revoked
        ):
            raise PITDataContractErrorV1(
                (
                    PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE
                    if evaluated < source.effective_at_utc
                    or evaluated < source.checked_at_utc
                    or evaluated - source.checked_at_utc > timedelta(hours=24)
                    or evaluated >= source.expires_at_utc
                    or source.invalidating_change_detected
                    else PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED
                ),
                "source or rights receipt is stale, revoked, or cross-source",
            )
        row = profile_by_id[profile_id]
        protocol = policy._pit_profile_protocol_policy_v2(profile_id)
        contracts.append(
            SelectedPITPublicDataContractV2(
                contract_id=f"S1-PIT-PUBLIC-DATA::{profile_id.value}::V2",
                contract_version="S1_PIT_PUBLIC_DATA_CONTRACT_V2",
                profile_id=profile_id,
                scope_receipt_ref=selected_scope.source_decision_ref,
                operating_legal_entity=row.operating_legal_entity,
                product_profile=row.api_profile,
                jurisdiction=row.jurisdiction,
                production_rest_base=_pit_binding_text(
                    protocol["production_rest_base"], "production_rest_base"
                ),
                websocket_url=_pit_binding_text(
                    protocol["websocket_url"], "websocket_url"
                ),
                allowed_access_classes=protocol["allowed_access_classes"],
                allowed_methods=protocol["allowed_methods"],
                allowed_paths=protocol["allowed_paths"],
                allowed_channels=protocol["allowed_channels"],
                wire_dialect_policy=_pit_binding_text(
                    protocol["wire_dialect_policy"], "wire_dialect_policy"
                ),
                subscription_form=(
                    "use_yes_price=true"
                    if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
                    else "EXACT_PROFILE_ALLOWLISTED_SUBSCRIPTION"
                ),
                sequence_model=_pit_binding_text(
                    protocol["sequence_model"], "sequence_model"
                ),
                snapshot_model=_pit_binding_text(
                    protocol["snapshot_model"], "snapshot_model"
                ),
                recovery_model=_pit_binding_text(
                    protocol["recovery_model"], "recovery_model"
                ),
                heartbeat_model=_pit_binding_text(
                    protocol["heartbeat_model"], "heartbeat_model"
                ),
                admitted_event_kinds=_PIT_EVENT_KINDS_BY_PROFILE[profile_id],
                event_identity_fields=("event_id", "event_kind", "source_version"),
                market_identity_fields=("market_id", "market_slug_or_ticker"),
                instrument_identity_fields=("instrument_id", "source_symbol"),
                outcome_and_side_fields=("source_outcome_id", "source_side", "canonical_side"),
                depth_class=protocol["depth_class"],
                price_quantity_tick_model="CANONICAL_DECIMAL_TEXT_SCALE_ORIGIN_INCREMENT",
                lifecycle_and_finality_fields=(
                    "lifecycle_state",
                    "lifecycle_version",
                    "settlement_finality_time_or_none",
                ),
                source_currentization_receipt_ref=source.receipt_id,
                source_contract_version=source.source_contract_version,
                rights_receipt_ref=rights.receipt_id,
                agreement_version=rights.agreement_version,
                credential_alias_required=_pit_binding_boolean(
                    protocol["credential_alias_required"],
                    "credential_alias_required",
                ),
                no_private_state_authority=True,
                no_order_authority=True,
                default_failure_reason=PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                unavailable_capabilities=_PIT_UNAVAILABLE_BY_PROFILE[profile_id],
                recovery_preconditions=(
                    "NEW_CONNECTION_EPOCH",
                    "FRESH_VALID_ANCHOR_OR_CURRENT_STATE_FRAME",
                    "INDEPENDENT_RECONSTRUCTION_VALID",
                    "CURRENT_SOURCE_AND_RIGHTS",
                ),
            )
        )
    return tuple(contracts)
