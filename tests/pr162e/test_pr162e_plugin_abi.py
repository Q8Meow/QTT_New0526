from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass, replace
from enum import Enum
from types import MappingProxyType

import pytest

import src.qtt.plugins as plugin_package
from src.qtt.plugins.contracts import (
    ALLOWED_RUNTIME_LANE_VALUES,
    FORBIDDEN_RUNTIME_LANE_VALUES,
    MATERIALIZATION_STATUSES,
    PLUGIN_FAMILIES,
    PackageAdmissionStateV1,
    PackageSupersessionStateV1,
    PackageValidationTerminalStateV1,
    PackageVersionV1,
    PluginAuthorityEnvelope,
    PluginPackageContractError,
    PluginPackageReasonCodeV1,
    _normalize_package_serialization_value,
    adapter_smoke_vector,
)
from src.qtt.plugins.registry import (
    build_selected_component_package_manifest_v1,
    derive_rollback_and_supersession_receipt_v1,
    rebuild_selected_component_package_v1,
    selected_component_package_projection_v1,
    validate_package_supersession_v1,
    validate_selected_component_package_v1,
)
from src.qtt.stage1_prediction_markets.pr162e_plugin_framework import (
    constants as stage_constants,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    stage1_launch_graph_projection_v2,
)


def test_plugin_abi_smoke_vector_is_computable():
    request, context, response = adapter_smoke_vector()
    assert request.plugin_id == response.plugin_id
    assert context.authority_envelope.no_live_order_authority
    assert response.plugin_materialization_status == "COMPUTABLE_PLUGIN_READY"
    assert "execution_adjusted_edge" in response.score_components

    assert stage_constants.MATERIALIZATION_STATUSES is MATERIALIZATION_STATUSES
    assert stage_constants.ALLOWED_RUNTIME_LANES is ALLOWED_RUNTIME_LANE_VALUES
    assert stage_constants.FORBIDDEN_RUNTIME_LANES is FORBIDDEN_RUNTIME_LANE_VALUES
    assert stage_constants.PLUGIN_FAMILIES is PLUGIN_FAMILIES
    assert len(PLUGIN_FAMILIES) == 95

    assert PackageVersionV1.parse("0.0.0").canonical == "0.0.0"
    version = PackageVersionV1.parse("1.0.0")
    assert version.canonical == "1.0.0"
    assert version.compare(PackageVersionV1(1, 0, 0)) == 0
    assert version.compare(PackageVersionV1(1, 0, 1)) == -1
    assert PackageVersionV1(1, 0, 1).compare(version) == 1
    for malformed_version in (
        "1.0",
        "01.0.0",
        "1.0.0 ",
        " 1.0.0",
        "1.0.0-alpha",
        "1.0.0+build",
        ">=1.0.0",
        "1.*.0",
        "https://example.invalid/package",
    ):
        with pytest.raises(PluginPackageContractError) as error:
            PackageVersionV1.parse(malformed_version)
        assert error.value.reason_code is PluginPackageReasonCodeV1.VERSION_INVALID

    launch_projection = stage1_launch_graph_projection_v2()
    canonical_launch_projection = stage1_launch_graph_projection_v2()
    manifest = build_selected_component_package_manifest_v1(
        launch_projection,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    receipt = validate_selected_component_package_v1(
        manifest,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert manifest.package_version == version
    assert {entry.package_version for entry in manifest.entries} == {version}
    assert len(manifest.entries) == 28
    assert tuple(entry.package_component_id for entry in manifest.entries) == tuple(
        f"S1PKG::ROLE-{index:02d}" for index in range(1, 29)
    )
    admission_counts = {
        state: sum(entry.admission_state is state for entry in manifest.entries)
        for state in PackageAdmissionStateV1
    }
    assert admission_counts == {
        PackageAdmissionStateV1.ADMITTED_CONTRACT_ONLY_NO_EFFECT: 11,
        PackageAdmissionStateV1.HELD_EVIDENCE_INSUFFICIENT_NO_ADMISSION: 5,
        PackageAdmissionStateV1.HELD_IMPLEMENTATION_MISSING_NO_ADMISSION: 12,
    }
    family_refs = tuple(
        family
        for entry in manifest.entries
        for family in (
            *((entry.primary_plugin_family_or_none,)
              if entry.primary_plugin_family_or_none is not None
              else ()),
            *entry.supporting_plugin_families,
        )
    )
    assert len(family_refs) == 66
    assert len(set(family_refs)) == 58
    assert set(family_refs) <= set(PLUGIN_FAMILIES)
    assert sum(
        entry.primary_plugin_family_or_none is None
        and not entry.supporting_plugin_families
        for entry in manifest.entries
    ) == 6
    assert receipt.terminal_state is (
        PackageValidationTerminalStateV1.VALIDATED_NO_EFFECT_WITH_HELD_DEPENDENCIES
    )
    assert receipt.reason_codes == ()
    assert manifest.active_live_profile_ids == ()
    assert manifest.selected_profile_ids == (
        "GEMINI_TITAN_DIRECT",
        "POLYMARKET_US_RETAIL_DIRECT",
        "KALSHI_US_DCM_DIRECT",
    )
    assert manifest.excluded_profile_ids == (
        "FORECASTEX_IBKR",
        "FORECASTEX_DIRECT_MEMBER",
    )

    role_27 = manifest.entries[26]
    assert role_27.fallback_component_id_or_none == "S1PKG::ROLE-26"
    assert all(
        entry.fallback_component_id_or_none is None
        for entry in (*manifest.entries[:26], manifest.entries[27])
    )
    initial_rollback = derive_rollback_and_supersession_receipt_v1(
        manifest,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert initial_rollback.predecessor_package_version_or_none is None
    assert initial_rollback.superseded_package_versions == ()
    assert initial_rollback.retained_predecessor_versions == ()
    assert initial_rollback.supersession_state is (
        PackageSupersessionStateV1.INITIAL_CURRENT_NO_PREDECESSOR
    )
    disabled = derive_rollback_and_supersession_receipt_v1(
        manifest,
        canonical_launch_graph_projection=canonical_launch_projection,
        disabled_component_ids=("S1PKG::ROLE-01", "S1PKG::ROLE-27"),
    )
    assert disabled.disabled_component_ids == (
        "S1PKG::ROLE-01",
        "S1PKG::ROLE-27",
    )
    assert "S1PKG::ROLE-01" in disabled.operation_eligibility_rows[0].blocking_component_ids
    assert disabled.operation_eligibility_rows[0].blocking_component_ids.count(
        "S1PKG::ROLE-27"
    ) == 0
    assert disabled.operation_eligibility_rows[3].blocking_component_ids.count(
        "S1PKG::ROLE-27"
    ) == 0
    with pytest.raises(PluginPackageContractError) as unknown_disable:
        derive_rollback_and_supersession_receipt_v1(
            manifest,
            canonical_launch_graph_projection=canonical_launch_projection,
            disabled_component_ids=("S1PKG::ROLE-99",),
        )
    assert unknown_disable.value.reason_code is PluginPackageReasonCodeV1.ROLLBACK_INVALID

    next_version = PackageVersionV1(1, 0, 1)
    successor = replace(
        manifest,
        package_version=next_version,
        entries=tuple(
            replace(entry, package_version=next_version)
            for entry in manifest.entries
        ),
    )
    successor_receipt = validate_package_supersession_v1(
        manifest,
        successor,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert successor_receipt.supersession_state is (
        PackageSupersessionStateV1.VALIDATED_MONOTONE_SUPERSESSION
    )
    assert successor_receipt.predecessor_package_version_or_none == version
    nonmonotone = validate_package_supersession_v1(
        manifest,
        manifest,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert nonmonotone.supersession_state is (
        PackageSupersessionStateV1.REJECTED_NON_MONOTONE_OR_INCOMPATIBLE
    )
    assert nonmonotone.reason_codes == (
        PluginPackageReasonCodeV1.SUPERSESSION_INVALID,
    )

    identity_mutation = replace(manifest, package_id=f"{manifest.package_id}-COPY")
    identity_receipt = validate_selected_component_package_v1(
        identity_mutation,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert identity_receipt.terminal_state is (
        PackageValidationTerminalStateV1.REJECTED_INVALID
    )
    assert PluginPackageReasonCodeV1.IDENTITY_INVALID in identity_receipt.reason_codes
    family_mutation_entry = replace(
        manifest.entries[3],
        primary_plugin_family_or_none="UNKNOWN_PLUGIN_FAMILY",
    )
    family_mutation = replace(
        manifest,
        entries=(
            *manifest.entries[:3],
            family_mutation_entry,
            *manifest.entries[4:],
        ),
    )
    family_receipt = validate_selected_component_package_v1(
        family_mutation,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert family_receipt.terminal_state is (
        PackageValidationTerminalStateV1.REJECTED_INVALID
    )
    assert PluginPackageReasonCodeV1.FAMILY_UNKNOWN in family_receipt.reason_codes

    future_index = next(
        index
        for index, entry in enumerate(manifest.entries)
        if entry.future_owner_paths
    )
    future_entry = manifest.entries[future_index]
    source_field_mutations = (
        (
            0,
            replace(
                manifest.entries[0],
                canonical_output_contract="WRONG_NONEMPTY_OUTPUT_CONTRACT",
            ),
        ),
        (
            26,
            replace(
                manifest.entries[26],
                latency_class="WRONG_NONEMPTY_LATENCY_CLASS",
            ),
        ),
        (
            24,
            replace(
                manifest.entries[24],
                default_failure_route="WRONG_NONEMPTY_FAILURE_ROUTE",
            ),
        ),
        (
            future_index,
            replace(
                future_entry,
                existing_owner_paths=(
                    *future_entry.existing_owner_paths,
                    future_entry.future_owner_paths[0],
                ),
                future_owner_paths=future_entry.future_owner_paths[1:],
            ),
        ),
    )
    for entry_index, mutated_entry in source_field_mutations:
        mutated_entries = list(manifest.entries)
        mutated_entries[entry_index] = mutated_entry
        mutation_receipt = validate_selected_component_package_v1(
            replace(manifest, entries=tuple(mutated_entries)),
            canonical_launch_graph_projection=canonical_launch_projection,
        )
        assert mutation_receipt.terminal_state is (
            PackageValidationTerminalStateV1.REJECTED_INVALID
        )
        assert PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID in (
            mutation_receipt.reason_codes
        )

    with pytest.raises(PluginPackageContractError) as numeric_authority:
        PluginAuthorityEnvelope(
            authority_envelope_id=(
                manifest.authority_envelope.authority_envelope_id
            ),
            no_live_order_authority=1,
        )
    assert numeric_authority.value.reason_code is (
        PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN
    )
    false_authority = replace(
        manifest.authority_envelope,
        no_live_order_authority=False,
    )
    false_authority_receipt = validate_selected_component_package_v1(
        replace(manifest, authority_envelope=false_authority),
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert false_authority_receipt.terminal_state is (
        PackageValidationTerminalStateV1.REJECTED_INVALID
    )
    assert PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN in (
        false_authority_receipt.reason_codes
    )

    reordered_mapping_projection = dict(
        reversed(tuple(launch_projection.items()))
    )
    assert build_selected_component_package_manifest_v1(
        reordered_mapping_projection,
        canonical_launch_graph_projection=canonical_launch_projection,
    ) == manifest

    altered_latency_projection = deepcopy(launch_projection)
    altered_latency_projection["graph"]["roles"][26]["latency_class"] = (
        "WRONG_NONEMPTY_LATENCY_CLASS"
    )
    boolean_ordinal_projection = deepcopy(launch_projection)
    boolean_ordinal_projection["graph"]["scope"]["profiles"][0][
        "serialization_ordinal_or_none"
    ] = True
    reordered_role_projection = deepcopy(launch_projection)
    reordered_role_projection["graph"]["roles"][0:2] = reversed(
        reordered_role_projection["graph"]["roles"][0:2]
    )
    for mutated_launch_projection in (
        altered_latency_projection,
        boolean_ordinal_projection,
        reordered_role_projection,
    ):
        with pytest.raises(PluginPackageContractError) as launch_error:
            build_selected_component_package_manifest_v1(
                mutated_launch_projection,
                canonical_launch_graph_projection=canonical_launch_projection,
            )
        assert launch_error.value.reason_code is (
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID
        )

    floating_count_projection = deepcopy(launch_projection)
    floating_count_projection["validation"]["checked_role_count"] = 28.0
    with pytest.raises(PluginPackageContractError) as floating_count:
        build_selected_component_package_manifest_v1(
            floating_count_projection,
            canonical_launch_graph_projection=canonical_launch_projection,
        )
    assert floating_count.value.reason_code is (
        PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID
    )

    @dataclass
    class MutablePackageValue:
        value: int

    class FloatPayloadEnum(Enum):
        VALUE = 1.25

    class ListPayloadEnum(Enum):
        VALUE = ["mutable"]

    class CustomText(str):
        pass

    class CustomMapping(dict):
        pass

    cyclic_value: dict[str, object] = {}
    cyclic_value["cycle"] = cyclic_value
    invalid_package_values = (
        MutablePackageValue(1),
        FloatPayloadEnum.VALUE,
        ListPayloadEnum.VALUE,
        1.25,
        ["mutable"],
        CustomText("custom"),
        CustomMapping({"value": 1}),
        cyclic_value,
    )
    for invalid_package_value in invalid_package_values:
        with pytest.raises(PluginPackageContractError) as normalization_error:
            _normalize_package_serialization_value(invalid_package_value)
        assert normalization_error.value.reason_code is (
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID
        )
    assert _normalize_package_serialization_value(
        MappingProxyType({"value": (1, "canonical")})
    ) == {"value": [1, "canonical"]}
    assert _normalize_package_serialization_value(
        {"alpha": 1, "beta": 2}
    ) == _normalize_package_serialization_value(
        {"beta": 2, "alpha": 1}
    )

    with pytest.raises(PluginPackageContractError) as oversized_version:
        PackageVersionV1.parse(f"{'9' * 5000}.0.0")
    assert oversized_version.value.reason_code is (
        PluginPackageReasonCodeV1.VERSION_INVALID
    )

    missing_reference_calls = (
        lambda: build_selected_component_package_manifest_v1(launch_projection),
        lambda: validate_selected_component_package_v1(manifest),
        lambda: derive_rollback_and_supersession_receipt_v1(manifest),
        lambda: validate_package_supersession_v1(manifest, successor),
        lambda: rebuild_selected_component_package_v1(launch_projection),
        lambda: selected_component_package_projection_v1(launch_projection),
    )
    for missing_reference_call in missing_reference_calls:
        with pytest.raises(TypeError):
            missing_reference_call()

    reproducibility = rebuild_selected_component_package_v1(
        launch_projection,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert reproducibility.second_build_byte_equal is True
    assert reproducibility.pure_build_effect_count == 0
    projection = selected_component_package_projection_v1(
        launch_projection,
        canonical_launch_graph_projection=canonical_launch_projection,
    )
    assert tuple(projection) == (
        "manifest",
        "compatibility_and_dependency",
        "rollback_and_supersession",
        "reproducibility",
    )
    with pytest.raises(TypeError):
        projection["manifest"] = manifest
    with pytest.raises(FrozenInstanceError):
        manifest.package_id = "MUTATED"

    new_exports = (
        "PluginPackageReasonCodeV1",
        "PluginPackageContractError",
        "PackageVersionV1",
        "PackageAdmissionStateV1",
        "PackageCompatibilityStateV1",
        "PackageRollbackTargetKindV1",
        "PackageOperationEligibilityStateV1",
        "PackageValidationTerminalStateV1",
        "PackageSupersessionStateV1",
        "PackageOperationEligibilityV1",
        "SelectedComponentPackageEntryV1",
        "SelectedComponentPackageManifestV1",
        "CompatibilityAndDependencyReceiptV1",
        "RollbackAndSupersessionReceiptV1",
        "PackageReproducibilityReceiptV1",
        "compile_selected_package_dependency_order_v1",
        "build_selected_component_package_manifest_v1",
        "validate_selected_component_package_v1",
        "derive_rollback_and_supersession_receipt_v1",
        "validate_package_supersession_v1",
        "rebuild_selected_component_package_v1",
        "selected_component_package_projection_v1",
    )
    assert tuple(plugin_package.__all__[-22:]) == new_exports
    assert all(plugin_package.__all__.count(name) == 1 for name in new_exports)
