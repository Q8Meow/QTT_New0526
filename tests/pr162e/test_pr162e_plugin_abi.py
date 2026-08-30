from dataclasses import FrozenInstanceError, replace

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
    PluginPackageContractError,
    PluginPackageReasonCodeV1,
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
    manifest = build_selected_component_package_manifest_v1(launch_projection)
    receipt = validate_selected_component_package_v1(manifest)
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
    initial_rollback = derive_rollback_and_supersession_receipt_v1(manifest)
    assert initial_rollback.predecessor_package_version_or_none is None
    assert initial_rollback.superseded_package_versions == ()
    assert initial_rollback.retained_predecessor_versions == ()
    assert initial_rollback.supersession_state is (
        PackageSupersessionStateV1.INITIAL_CURRENT_NO_PREDECESSOR
    )
    disabled = derive_rollback_and_supersession_receipt_v1(
        manifest,
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
    successor_receipt = validate_package_supersession_v1(manifest, successor)
    assert successor_receipt.supersession_state is (
        PackageSupersessionStateV1.VALIDATED_MONOTONE_SUPERSESSION
    )
    assert successor_receipt.predecessor_package_version_or_none == version
    nonmonotone = validate_package_supersession_v1(manifest, manifest)
    assert nonmonotone.supersession_state is (
        PackageSupersessionStateV1.REJECTED_NON_MONOTONE_OR_INCOMPATIBLE
    )
    assert nonmonotone.reason_codes == (
        PluginPackageReasonCodeV1.SUPERSESSION_INVALID,
    )

    identity_mutation = replace(manifest, package_id=f"{manifest.package_id}-COPY")
    identity_receipt = validate_selected_component_package_v1(identity_mutation)
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
    family_receipt = validate_selected_component_package_v1(family_mutation)
    assert family_receipt.terminal_state is (
        PackageValidationTerminalStateV1.REJECTED_INVALID
    )
    assert PluginPackageReasonCodeV1.FAMILY_UNKNOWN in family_receipt.reason_codes

    reproducibility = rebuild_selected_component_package_v1(launch_projection)
    assert reproducibility.second_build_byte_equal is True
    assert reproducibility.pure_build_effect_count == 0
    projection = selected_component_package_projection_v1(launch_projection)
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
