#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass
from fnmatch import fnmatchcase
import re
from pathlib import Path, PurePosixPath
import sys
from typing import Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import run_validation_gates as runner
from tools.repo_path_refs import normalize_repo_ref


FAST_UNIVERSAL_PREFLIGHT = "FAST_UNIVERSAL_PREFLIGHT"
CHANGED_AREA_VALIDATOR = "CHANGED_AREA_VALIDATOR"
TOUCHED_GENERATED_ARTIFACT_VALIDATOR = "TOUCHED_GENERATED_ARTIFACT_VALIDATOR"
DETERMINISTIC_GENERATED_ARTIFACT_VALIDATOR = (
    "DETERMINISTIC_GENERATED_ARTIFACT_VALIDATOR"
)
NIGHTLY_DEEP_VALIDATOR = "NIGHTLY_DEEP_VALIDATOR"
RELEASE_LIVE_READINESS_VALIDATOR = "RELEASE_LIVE_READINESS_VALIDATOR"

VALIDATOR_CLASSES = frozenset(
    {
        FAST_UNIVERSAL_PREFLIGHT,
        CHANGED_AREA_VALIDATOR,
        TOUCHED_GENERATED_ARTIFACT_VALIDATOR,
        DETERMINISTIC_GENERATED_ARTIFACT_VALIDATOR,
        NIGHTLY_DEEP_VALIDATOR,
        RELEASE_LIVE_READINESS_VALIDATOR,
    }
)
COST_TIERS = frozenset({"FAST", "MEDIUM", "SLOW", "DEEP"})

VALIDATION_INFRASTRUCTURE_GLOBS = (
    ".github/workflows/**",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tools/validation_scope_registry.py",
    "tools/validate_validation_scope_registry.py",
    "tools/qtt_authority_reason_code_registry.py",
    "tools/validate_qtt_authority_reason_code_registry.py",
    "tools/validation_inventory.py",
    "tools/validate_validation_inventory.py",
    "tools/validate_idempotence_runtime_containment.py",
    "tools/changed_area_validation_router.py",
    "tools/cross_platform_path_invariant.py",
    "tools/repo_path_refs.py",
    "src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/report.py",
    "src/qtt/stage1_prediction_markets/"
    "qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py",
    "tests/tools/test_validation_inventory.py",
    "tests/tools/test_validate_idempotence_runtime_containment.py",
    "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
    "tests/tools/test_changed_area_validation_router.py",
    "tests/tools/test_cross_platform_path_invariant.py",
    "tests/tools/test_ci_branch_context.py",
    "tests/tools/test_validation_scope_registry.py",
    "tests/tools/test_qtt_authority_reason_code_registry.py",
    "tests/fail_closed/test_run_validation_gates.py",
    "docs/master_plan/generated/PR208_*.report.json",
)
PR152_TRACKED_GLOBS = (
    "tools/currentize_pr152_after_generated_artifacts.py",
    "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
    "docs/master_plan/generated/PR152_*.report.json",
)
GENERATED_REPORT_GLOBS = (
    "docs/master_plan/generated/*.json",
    "docs/master_plan/generated/**/*.json",
    "docs/master_plan/source_evidence/generated/*.json",
    "docs/master_plan/source_evidence/generated/**/*.json",
    "docs/roadmap/generated/*.json",
    "docs/roadmap/generated/**/*.json",
)
VALIDATION_MATRIX_JOB_ID = "validation_shards"
PHASE_JOB_IDS = {phase: VALIDATION_MATRIX_JOB_ID for phase in runner.ORDERED_PHASES}


@dataclass(frozen=True)
class ValidatorInventoryEntry:
    validator_id: str
    command: tuple[str, ...]
    phase: str
    validator_class: tuple[str, ...]
    owner_domain: str
    owner_pr_or_feature: str
    input_globs: tuple[str, ...]
    output_globs: tuple[str, ...]
    generated_report_globs: tuple[str, ...]
    schema_globs: tuple[str, ...]
    tool_globs: tuple[str, ...]
    test_globs: tuple[str, ...]
    workflow_globs: tuple[str, ...]
    cost_tier: str
    typical_runtime_seconds_if_known: float | None
    runs_on_pull_request_default: bool
    runs_on_pull_request_when_touched: bool
    runs_on_main_push: bool
    runs_on_nightly: bool
    runs_on_manual_full: bool
    runs_on_release_live_readiness: bool
    fail_closed_if_touched: bool
    fail_closed_if_unknown_change: bool
    required_when_files_match: tuple[str, ...]
    cross_platform_sensitive: bool
    linux_required: bool
    windows_required: bool
    pr152_tracked: bool
    full_validation_required_when_changed: bool
    rationale: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


def _dedupe_sorted(values: Iterable[str]) -> tuple[str, ...]:
    normalized = [normalize_repo_ref(value) for value in values if str(value).strip()]
    return tuple(sorted(dict.fromkeys(normalized)))


def _matches_any(path: str, globs: Iterable[str]) -> bool:
    normalized = normalize_repo_ref(path)
    return any(fnmatchcase(normalized, glob) for glob in globs)


def _canonical_arg(arg: object) -> str:
    value = str(arg)
    if "\n" in value:
        if "atomicrows_semantic_contract" in value:
            return "PR138_NON_MUTATING_VALIDATION_SCRIPT"
        if "AtomicRows bundle is missing" in value:
            return "ATOMICROWS_BUNDLE_CHECK_SCRIPT"
        return "INLINE_PYTHON_SCRIPT"
    normalized = value.replace("\\", "/")
    if normalized.endswith("/python.exe") or normalized.endswith("/python"):
        return "python"
    return normalized


def canonical_command(command: Sequence[str]) -> tuple[str, ...]:
    return tuple(_canonical_arg(part) for part in command)


def _script_name_from_canonical(command: Sequence[str]) -> str:
    if len(command) <= 1:
        return ""
    return PurePosixPath(command[1].replace("\\", "/")).name


def _pytest_validator_id(command: Sequence[str], phase: str) -> str:
    path_args = [
        part
        for part in command[2:]
        if not part.startswith("-")
        and part not in {"--ignore", "--basetemp"}
        and not part.endswith("pytest-basetemp")
    ]
    joined = "_".join(
        PurePosixPath(path).name.replace(".py", "") for path in path_args[:2]
    )
    suffix = re.sub(r"[^a-zA-Z0-9]+", "_", joined).strip("_").lower()
    return f"{phase}_{suffix or 'pytest'}".replace("-", "_")


def validator_id_for_command(command: Sequence[str], phase: str) -> str:
    canonical = canonical_command(command)
    if not canonical:
        return f"{phase}_empty_command".replace("-", "_")
    if canonical[0] == "git":
        if canonical[:3] == ("git", "diff", "--check"):
            return "post_git_diff_check"
        if len(canonical) >= 5 and canonical[:3] == ("git", "diff", "--exit-code"):
            return "post_master_plan_unchanged"
        return "post_git_command"
    if len(canonical) > 2 and canonical[1:3] == ("-m", "compileall"):
        return "post_compileall"
    if len(canonical) > 1 and canonical[1] == "-c":
        if len(canonical) > 2 and canonical[2] == "ATOMICROWS_BUNDLE_CHECK_SCRIPT":
            return "post_atomicrows_bundle_presence_no_sidecar"
        return "inline_atomicrows_semantic_contract"

    script_name = _script_name_from_canonical(canonical)
    if script_name == runner.PYTEST_FRESH_BASETEMP_SCRIPT:
        return _pytest_validator_id(canonical, phase)
    return PurePosixPath(script_name).stem


def _pr_token(stem: str) -> str | None:
    if "pr169_pretrade1" in stem:
        return "pr169_pretrade1"
    if "pr169_readiness1" in stem:
        return "pr169_readiness1"
    if "pr169_dash1" in stem:
        return "pr169_dash1"
    if (
        "pr162e_plugin_framework" in stem
        or "pr162e_negative_repair_factory" in stem
        or "pr162e_no_orphan_lineage" in stem
    ):
        return "pr162e"
    if "pr167_open_trade_simulator" in stem:
        return "pr167"
    if "pr165_d3" in stem:
        return "pr165_d3"
    if "pr168_gfp2r" in stem:
        return "pr168_gfp2r"
    if "pr168_rp3" in stem:
        return "pr168_rp3"
    if "pr168_qopt1" in stem:
        return "pr168_qopt1"
    if "pr168_vs2" in stem:
        return "pr168_vs2"
    if "pr168_mem1" in stem:
        return "pr168_mem1"
    if "pr168_rank4" in stem:
        return "pr168_rank4"
    if "pr168_rank3" in stem:
        return "pr168_rank3"
    if "pr168_rp5a" in stem:
        return "pr168_rp5a"
    if "pr168_rp5b" in stem:
        return "pr168_rp5b"
    if "pr168_rp5c" in stem:
        return "pr168_rp5c"
    if "pr168_rp5d_r1" in stem:
        return "pr168_rp5d_r1"
    if "pr168_rp5g" in stem:
        return "pr168_rp5g"
    if "pr168_rp5f" in stem:
        return "pr168_rp5f"
    if "pr168_rp5d" in stem:
        return "pr168_rp5d"
    if "pr168_rp5e" in stem:
        return "pr168_rp5e"
    if "pr168_vs1" in stem:
        return "pr168_vs1"
    if "pr168_map3" in stem:
        return "pr168_map3"
    if "pr168_rp2" in stem:
        return "pr168_rp2"
    if "pr168_data1a" in stem:
        return "pr168_data1a"
    if "pr168_data1" in stem:
        return "pr168_data1"
    match = re.search(r"(pr\d+[a-z]?(?:_[a-z]+)?)", stem)
    if match is None:
        return None
    return match.group(1)


def _pr_tag_from_token(token: str) -> str:
    return token.upper().replace("PR", "PR", 1)


def _owner_pr_or_feature(stem: str) -> str:
    token = _pr_token(stem)
    if token is not None:
        return _pr_tag_from_token(token)
    if "qtt_authority_reason_code_registry" in stem:
        return "PR168-RP"
    if "atomicrows" in stem:
        return "AtomicRows"
    if "source_evidence" in stem:
        return "source_evidence"
    if "ci_branch_context" in stem:
        return "ci_branch_context"
    if "validation_inventory" in stem:
        return "PR208"
    if "idempotence_runtime_containment" in stem:
        return "CI runtime containment"
    if "changed_area_validation_router" in stem:
        return "PR208"
    if "cross_platform_path_invariant" in stem:
        return "PR208"
    return stem or "repository"


def _owner_domain(stem: str, command: Sequence[str]) -> str:
    haystack = " ".join(command).lower()
    if (
        "qtt_authority_reason_code_registry" in stem
        or "qtt_authority_reason_code_registry" in haystack
    ):
        return "QTT authority reason code registry"
    if (
        "validation_inventory" in stem
        or "changed_area" in stem
        or "idempotence_runtime_containment" in stem
    ):
        return "CI validation infrastructure"
    if "cross_platform_path" in stem or "repo_path_refs" in haystack:
        return "cross-platform path invariant"
    if "branch_context" in stem:
        return "branch context"
    if "atomicrows" in haystack:
        return "AtomicRows"
    if "source_evidence" in haystack:
        return "source evidence"
    if "connector" in haystack:
        return "connector static gates"
    if "runtime_cash" in haystack:
        return "runtime cash static gates"
    if "private_state" in haystack:
        return "private-state static gates"
    if "live" in haystack or "launch" in haystack or "canary" in haystack:
        return "release/live readiness static gates"
    token = _pr_token(stem)
    if token is not None:
        return _pr_tag_from_token(token)
    return "repository validation"


def _script_path_glob(script_name: str) -> tuple[str, ...]:
    if not script_name:
        return ()
    return (f"tools/{script_name}",)


def _pr_globs(stem: str) -> tuple[str, ...]:
    token = _pr_token(stem)
    if token is None:
        return ()
    tag = _pr_tag_from_token(token)
    lower = token.lower()
    globs = [
        f"docs/master_plan/generated/{tag}*.json",
        f"docs/master_plan/generated/{tag}_*.report.json",
        f"docs/master_plan/generated/{lower}*/**",
        f"src/qtt/stage1_prediction_markets/{lower}*/**",
        f"tests/{lower}/**",
        f"tests/stage1_prediction_markets/{lower}*/**",
        f"tools/*{lower}*.py",
    ]
    if token == "pr162e":
        globs.extend(
            [
                "src/qtt/plugins/**",
                "tests/pr162e/**",
            ]
        )
    if token == "pr168_rank4":
        globs.extend(
            [
                "src/qtt/ranking/__init__.py",
                "src/qtt/ranking/pr168_rank4/**",
            ]
        )
    if token == "pr168_qopt1":
        globs.extend(
            [
                "src/qtt/optimization/__init__.py",
                "src/qtt/optimization/pr168_qopt1/**",
                "tests/pr168_qopt1/**",
            ]
        )
    if token == "pr168_vs2":
        globs.extend(
            [
                "src/qtt/paper/__init__.py",
                "src/qtt/paper/pr168_vs2/**",
                "tests/pr168_vs2/**",
            ]
        )
    if token == "pr168_mem1":
        globs.extend(
            [
                "src/qtt/memory/__init__.py",
                "src/qtt/memory/pr168_mem1/**",
                "tests/pr168_mem1/**",
            ]
        )
    if token == "pr169_readiness1":
        globs.extend(
            [
                "docs/master_plan/generated/pr169_readiness1/**",
                "src/qtt/readiness/**",
                "tests/pr169_readiness1/**",
            ]
        )
    if token == "pr169_pretrade1":
        globs.extend(
            [
                "docs/master_plan/generated/pr169_pretrade1/**",
                "src/qtt/pretrade/**",
                "tests/pr169_pretrade1/**",
            ]
        )
    if token == "pr169_dash1":
        globs.extend(
            [
                "docs/master_plan/generated/pr169_dash1/**",
                "src/qtt/dashboard/**",
                "tests/pr169_dash1/**",
                "tests/pr169_dash1_ui1/**",
            ]
        )
    return tuple(globs)


def _domain_globs(stem: str, command: Sequence[str]) -> tuple[str, ...]:
    haystack = " ".join(command).lower()
    globs: list[str] = []
    if "atomicrows" in haystack:
        globs.extend(
            [
                "docs/master_plan/atomic_rows/**",
                "docs/master_plan/generated/AtomicRows*.json",
                "src/qtt/stage1_prediction_markets/atomicrows*/**",
                "tests/atomicrows/**",
                "tools/*atomicrows*.py",
            ]
        )
    if "source_evidence" in haystack:
        globs.extend(
            [
                "docs/master_plan/source_evidence/**",
                "docs/master_plan/source_evidence/generated/**",
                "schemas/source_evidence/**",
                "tests/source_evidence/**",
                "tests/fixtures/source_evidence/**",
                "tools/*source_evidence*.py",
            ]
        )
    if "master_plan" in haystack:
        globs.extend(
            [
                "docs/master_plan/generated/MasterPlan*.json",
                "tests/master_plan/**",
                "tools/master_plan*.py",
            ]
        )
    if "ci_branch_context" in haystack:
        globs.extend(("tools/ci_branch_context.py", "tests/tools/test_ci_branch_context.py"))
    if "validation_scope_registry" in haystack:
        globs.extend(
            (
                "tools/validation_scope_registry.py",
                "tools/validate_validation_scope_registry.py",
                "tests/tools/test_validation_scope_registry.py",
            )
        )
    if "qtt_authority_reason_code_registry" in haystack:
        globs.extend(
            (
                "tools/qtt_authority_reason_code_registry.py",
                "tools/validate_qtt_authority_reason_code_registry.py",
                "tests/tools/test_qtt_authority_reason_code_registry.py",
            )
        )
    if "grand_global_debug_logical_consistency_audit" in stem:
        globs.extend(
            (
                "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
                "tools/currentize_pr152_after_generated_artifacts.py",
                "tests/tools/test_currentize_pr152_after_generated_artifacts.py",
            )
        )
    if "validation_inventory" in stem:
        globs.extend(
            (
                *VALIDATION_INFRASTRUCTURE_GLOBS,
                "tools/validation_inventory.py",
                "tools/validate_validation_inventory.py",
                "tests/tools/test_validation_inventory.py",
                "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
                "docs/master_plan/generated/PR208_CIRuntimeRationalizationSummary.report.json",
                "docs/master_plan/generated/PR208_FinalSummary.report.json",
            )
        )
    if "idempotence_runtime_containment" in stem:
        globs.extend(
            (
                *VALIDATION_INFRASTRUCTURE_GLOBS,
                "tools/validate_idempotence_runtime_containment.py",
                "tests/tools/test_validate_idempotence_runtime_containment.py",
                "tests/tools/fixtures/idempotence_runtime_containment_inventory.json",
            )
        )
    if "changed_area_validation_router" in stem:
        globs.extend(
            (
                *VALIDATION_INFRASTRUCTURE_GLOBS,
                "tools/changed_area_validation_router.py",
                "tests/tools/test_changed_area_validation_router.py",
                "docs/master_plan/generated/PR208_ChangedAreaRoutingPolicy.report.json",
            )
        )
    if "cross_platform_path_invariant" in stem:
        globs.extend(
            (
                *VALIDATION_INFRASTRUCTURE_GLOBS,
                "tools/cross_platform_path_invariant.py",
                "tools/repo_path_refs.py",
                "tests/tools/test_cross_platform_path_invariant.py",
                "docs/master_plan/generated/PR208_CrossPlatformPathInvariant.report.json",
            )
        )
    return tuple(globs)


def _output_globs(script_name: str, stem: str) -> tuple[str, ...]:
    globs: list[str] = []
    generated_args = runner.DEFAULT_GENERATED_OUTPUT_ARGS.get(script_name)
    if generated_args is not None:
        globs.append(generated_args[1])
    token = _pr_token(stem)
    if token is not None:
        tag = _pr_tag_from_token(token)
        lower = token.lower()
        globs.extend(
            [
                f"docs/master_plan/generated/{tag}*.json",
                f"docs/master_plan/generated/{tag}_*.report.json",
                f"docs/master_plan/generated/{lower}*/**",
            ]
        )
        if token == "pr168_rp2":
            globs.append("docs/master_plan/generated/rp2p/**")
        if token == "pr168_map3":
            globs.append("docs/master_plan/generated/map3/**")
        if token == "pr168_rp3":
            globs.append("docs/master_plan/generated/rp3/**")
        if token == "pr168_rank3":
            globs.append("docs/master_plan/generated/rank3/**")
        if token == "pr168_rank4":
            globs.append("docs/master_plan/generated/pr168_rank4/**")
        if token == "pr168_qopt1":
            globs.append("docs/master_plan/generated/pr168_qopt1/**")
        if token == "pr168_vs2":
            globs.append("docs/master_plan/generated/pr168_vs2/**")
        if token == "pr168_mem1":
            globs.append("docs/master_plan/generated/pr168_mem1/**")
        if token == "pr168_rp5a":
            globs.append("docs/master_plan/generated/rp5a/**")
        if token == "pr168_rp5b":
            globs.append("docs/master_plan/generated/rp5b/**")
        if token == "pr168_rp5c":
            globs.append("docs/master_plan/generated/rp5c/**")
        if token == "pr168_vs1":
            globs.append("docs/master_plan/generated/pr168_vs1/**")
        if token == "pr168_rp5d":
            globs.append("docs/master_plan/generated/pr168_rp5d/**")
        if token == "pr168_rp5d_r1":
            globs.append("docs/master_plan/generated/pr168_rp5d_r1/**")
        if token == "pr168_rp5f":
            globs.append("docs/master_plan/generated/pr168_rp5f/**")
        if token == "pr168_rp5g":
            globs.append("docs/master_plan/generated/pr168_rp5g/**")
        if token == "pr168_rp5e":
            globs.append("docs/master_plan/generated/pr168_rp5e/**")
        if token == "pr169_readiness1":
            globs.append("docs/master_plan/generated/pr169_readiness1/**")
        if token == "pr169_pretrade1":
            globs.append("docs/master_plan/generated/pr169_pretrade1/**")
    return tuple(globs)


def _schema_globs(stem: str) -> tuple[str, ...]:
    token = _pr_token(stem)
    if token is None:
        return ()
    lower = token.lower()
    return (f"src/qtt/stage1_prediction_markets/{lower}*/schemas/**",)


def _test_globs(stem: str, command: Sequence[str], phase: str) -> tuple[str, ...]:
    if phase.startswith("pytest-shard"):
        canonical = canonical_command(command)
        globs: list[str] = []
        ignore_next = False
        for part in canonical[2:]:
            if ignore_next:
                ignore_next = False
                continue
            if part in {"--ignore", "--basetemp"}:
                ignore_next = True
                continue
            if part.startswith("-") or part.endswith("pytest-basetemp"):
                continue
            if part.startswith("tests/"):
                globs.append(part if part.endswith(".py") else f"{part}/**")
        for split_test_root in (
            runner.PR166_SM2_TEST_ROOT,
            runner.PR166_SF_R2_TEST_ROOT,
        ):
            split_prefix = f"{split_test_root}/"
            globs = [
                f"{split_test_root}/**" if glob.startswith(split_prefix) else glob
                for glob in globs
            ]
        return _dedupe_sorted(globs)
    token = _pr_token(stem)
    globs = []
    if token is not None:
        globs.append(f"tests/{token.lower()}/**")
        globs.append(f"tests/stage1_prediction_markets/{token.lower()}*/**")
        if token == "pr162e":
            globs.append("tests/pr162e/**")
    if "atomicrows" in " ".join(command).lower():
        globs.append("tests/atomicrows/**")
    return tuple(globs)


def _workflow_globs(stem: str) -> tuple[str, ...]:
    if stem in {
        "validate_ci_branch_context_matrix",
        "validate_validation_inventory",
        "validate_validation_scope_registry",
        "validate_idempotence_runtime_containment",
        "changed_area_validation_router",
    }:
        return (".github/workflows/**",)
    return ()


def _classes_for(stem: str, command: Sequence[str], phase: str) -> tuple[str, ...]:
    if phase == runner.FAST_PREFLIGHT_PHASE or phase == runner.POST_VALIDATION_PHASE:
        return (FAST_UNIVERSAL_PREFLIGHT,)
    if phase.startswith("pytest-shard"):
        return (CHANGED_AREA_VALIDATOR,)

    classes = [
        CHANGED_AREA_VALIDATOR,
        TOUCHED_GENERATED_ARTIFACT_VALIDATOR,
        DETERMINISTIC_GENERATED_ARTIFACT_VALIDATOR,
    ]
    haystack = " ".join(command).lower()
    if _pr_token(stem) is not None or "atomicrows" in haystack:
        classes.append(NIGHTLY_DEEP_VALIDATOR)
    if any(
        marker in haystack
        for marker in (
            "live",
            "launch",
            "canary",
            "runtime",
            "connector_semantic",
            "private_state",
        )
    ):
        classes.append(RELEASE_LIVE_READINESS_VALIDATOR)
    return tuple(dict.fromkeys(classes))


def _cost_tier(classes: Sequence[str], phase: str) -> str:
    if FAST_UNIVERSAL_PREFLIGHT in classes:
        return "FAST"
    if phase.startswith("pytest-shard"):
        return "SLOW"
    if NIGHTLY_DEEP_VALIDATOR in classes or RELEASE_LIVE_READINESS_VALIDATOR in classes:
        return "DEEP"
    return "MEDIUM"


def _entry_for_command(command: Sequence[str], phase: str) -> ValidatorInventoryEntry:
    canonical = canonical_command(command)
    validator_id = validator_id_for_command(command, phase)
    script_name = _script_name_from_canonical(canonical)
    stem = PurePosixPath(script_name).stem if script_name else validator_id
    classes = _classes_for(stem, canonical, phase)
    output_globs = _dedupe_sorted(_output_globs(script_name, stem))
    tool_globs = _dedupe_sorted(
        [*_script_path_glob(script_name), *_domain_globs(stem, canonical)]
    )
    test_globs = _test_globs(stem, canonical, phase)
    workflow_globs = _workflow_globs(stem)
    generated_report_globs = tuple(
        glob for glob in output_globs if glob.startswith("docs/")
    )
    schema_globs = _dedupe_sorted(_schema_globs(stem))
    input_globs = _dedupe_sorted(
        [
            *_pr_globs(stem),
            *_domain_globs(stem, canonical),
            *schema_globs,
            *test_globs,
            *workflow_globs,
        ]
    )
    required_globs = _dedupe_sorted(
        [
            *input_globs,
            *output_globs,
            *generated_report_globs,
            *schema_globs,
            *tool_globs,
            *test_globs,
            *workflow_globs,
        ]
    )
    infra_sensitive = any(
        _matches_any(glob.rstrip("/**"), VALIDATION_INFRASTRUCTURE_GLOBS)
        for glob in required_globs
    ) or validator_id in {
        "validate_validation_inventory",
        "validate_validation_scope_registry",
        "validate_idempotence_runtime_containment",
        "changed_area_validation_router",
        "cross_platform_path_invariant",
    }
    cross_platform_sensitive = bool(
        generated_report_globs
        or any("path" in part.lower() for part in canonical)
        or validator_id in {
            "cross_platform_path_invariant",
            "changed_area_validation_router",
            "validate_validation_inventory",
            "validate_validation_scope_registry",
            "validate_idempotence_runtime_containment",
        }
    )
    pr152_tracked = any(_matches_any(glob.rstrip("/**"), PR152_TRACKED_GLOBS) for glob in required_globs)
    runs_default = FAST_UNIVERSAL_PREFLIGHT in classes
    rationale = (
        "Runs on every pull request because it is cheap and universal."
        if runs_default
        else "Runs on pull requests only when owned inputs, tools, tests, "
        "schemas, or generated artifacts are touched; otherwise it remains "
        "covered by main, nightly, and manual full validation."
    )
    return ValidatorInventoryEntry(
        validator_id=validator_id,
        command=canonical,
        phase=phase,
        validator_class=classes,
        owner_domain=_owner_domain(stem, canonical),
        owner_pr_or_feature=_owner_pr_or_feature(stem),
        input_globs=input_globs,
        output_globs=output_globs,
        generated_report_globs=generated_report_globs,
        schema_globs=schema_globs,
        tool_globs=tool_globs,
        test_globs=test_globs,
        workflow_globs=workflow_globs,
        cost_tier=_cost_tier(classes, phase),
        typical_runtime_seconds_if_known=None,
        runs_on_pull_request_default=runs_default,
        runs_on_pull_request_when_touched=True,
        runs_on_main_push=True,
        runs_on_nightly=True,
        runs_on_manual_full=True,
        runs_on_release_live_readiness=(
            RELEASE_LIVE_READINESS_VALIDATOR in classes
            or NIGHTLY_DEEP_VALIDATOR in classes
        ),
        fail_closed_if_touched=True,
        fail_closed_if_unknown_change=True,
        required_when_files_match=required_globs,
        cross_platform_sensitive=cross_platform_sensitive,
        linux_required=True,
        windows_required=cross_platform_sensitive,
        pr152_tracked=pr152_tracked,
        full_validation_required_when_changed=infra_sensitive,
        rationale=rationale,
    )


def validation_inventory() -> tuple[ValidatorInventoryEntry, ...]:
    validation_dir = Path(".tmp/qtt_validation_inventory")
    pytest_basetemp = validation_dir / "pytest"
    entries: list[ValidatorInventoryEntry] = []
    for phase_record in runner.build_phase_manifest(validation_dir, pytest_basetemp):
        phase = str(phase_record["phase"])
        for command in phase_record["commands"]:
            entries.append(_entry_for_command(command, phase))
    return tuple(sorted(entries, key=lambda entry: entry.validator_id))


def inventory_by_id() -> dict[str, ValidatorInventoryEntry]:
    return {entry.validator_id: entry for entry in validation_inventory()}


def command_inventory_ids_for_phase(phase: str) -> tuple[str, ...]:
    validation_dir = Path(".tmp/qtt_validation_inventory")
    pytest_basetemp = validation_dir / "pytest"
    return tuple(
        validator_id_for_command(command, phase)
        for command in runner.build_phase_commands(phase, validation_dir, pytest_basetemp)
    )


def entries_matching_path(path: str) -> tuple[ValidatorInventoryEntry, ...]:
    normalized = normalize_repo_ref(path)
    matches = [
        entry
        for entry in validation_inventory()
        if _matches_any(normalized, entry.required_when_files_match)
    ]
    specific_token = _specific_pr_token_for_path(normalized)
    if specific_token is not None:
        matches = [
            entry
            for entry in matches
            if _entry_matches_specific_token(entry, specific_token)
        ]
    return tuple(sorted(matches, key=lambda entry: entry.validator_id))


def _specific_pr_token_for_path(path: str) -> str | None:
    if (
        path.startswith("docs/master_plan/generated/pr169_pretrade1/")
        or path.startswith("src/qtt/pretrade/")
        or path.startswith("tests/pr169_pretrade1/")
        or "pr169_pretrade1" in PurePosixPath(path).name.lower()
    ):
        return "pr169_pretrade1"
    if (
        path.startswith("docs/master_plan/generated/pr169_readiness1/")
        or path.startswith("src/qtt/readiness/")
        or path.startswith("tests/pr169_readiness1/")
        or "pr169_readiness1" in PurePosixPath(path).name.lower()
    ):
        return "pr169_readiness1"
    if (
        path.startswith("docs/master_plan/generated/pr169_dash1/")
        or path.startswith("src/qtt/dashboard/")
        or path.startswith("tests/pr169_dash1/")
        or path.startswith("tests/pr169_dash1_ui1/")
        or "pr169_dash1" in PurePosixPath(path).name.lower()
    ):
        return "pr169_dash1"
    if (
        path.startswith("docs/master_plan/generated/pr168_mem1/")
        or path == "src/qtt/memory/__init__.py"
        or path.startswith("src/qtt/memory/pr168_mem1/")
        or path.startswith("tests/pr168_mem1/")
        or "pr168_mem1" in PurePosixPath(path).name.lower()
    ):
        return "pr168_mem1"
    if (
        path.startswith("docs/master_plan/generated/pr168_vs2/")
        or path == "src/qtt/paper/__init__.py"
        or path.startswith("src/qtt/paper/pr168_vs2/")
        or path.startswith("tests/pr168_vs2/")
        or "pr168_vs2" in PurePosixPath(path).name.lower()
    ):
        return "pr168_vs2"
    if (
        path.startswith("docs/master_plan/generated/pr168_qopt1/")
        or path == "src/qtt/optimization/__init__.py"
        or path.startswith("src/qtt/optimization/pr168_qopt1/")
        or path.startswith("tests/pr168_qopt1/")
        or "pr168_qopt1" in PurePosixPath(path).name.lower()
    ):
        return "pr168_qopt1"
    if (
        path.startswith("docs/master_plan/generated/pr168_rank4/")
        or path == "src/qtt/ranking/__init__.py"
        or path.startswith("src/qtt/ranking/pr168_rank4/")
        or path.startswith("tests/pr168_rank4/")
        or "pr168_rank4" in PurePosixPath(path).name.lower()
    ):
        return "pr168_rank4"
    if (
        path.startswith("docs/master_plan/generated/pr168_rp5d_r1/")
        or path.startswith(
            "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/"
        )
        or path.startswith("tests/pr168_rp5d_r1/")
        or "pr168_rp5d_r1" in PurePosixPath(path).name.lower()
    ):
        return "pr168_rp5d_r1"
    if (
        path.startswith("docs/master_plan/generated/pr168_rp5g/")
        or path.startswith(
            "src/qtt/stage1_prediction_markets/pr168_rp5g_trade_plan_sim/"
        )
        or path.startswith("tests/pr168_rp5g/")
        or "pr168_rp5g" in PurePosixPath(path).name.lower()
    ):
        return "pr168_rp5g"
    if (
        path.startswith("docs/master_plan/generated/pr168_rp5f/")
        or path.startswith(
            "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/"
        )
        or path.startswith("tests/pr168_rp5f/")
        or "pr168_rp5f" in PurePosixPath(path).name.lower()
    ):
        return "pr168_rp5f"
    return None


def _entry_matches_specific_token(
    entry: ValidatorInventoryEntry,
    token: str,
) -> bool:
    token = token.lower()
    tag = _pr_tag_from_token(token)
    haystack = " ".join(
        (
            entry.validator_id,
            entry.owner_pr_or_feature,
            *entry.input_globs,
            *entry.output_globs,
            *entry.generated_report_globs,
            *entry.schema_globs,
            *entry.tool_globs,
            *entry.test_globs,
            *entry.required_when_files_match,
        )
    ).lower()
    return entry.owner_pr_or_feature == tag or token in haystack


def inventory_counts(
    entries: Sequence[ValidatorInventoryEntry] | None = None,
) -> dict[str, int]:
    rows = tuple(validation_inventory() if entries is None else entries)
    counts = {
        "current_validator_count": len(rows),
        "classified_validator_count": len(
            [entry for entry in rows if entry.validator_class]
        ),
        "fast_universal_preflight_count": 0,
        "changed_area_validator_count": 0,
        "touched_generated_artifact_validator_count": 0,
        "deterministic_generated_artifact_validator_count": 0,
        "nightly_deep_validator_count": 0,
        "release_live_readiness_validator_count": 0,
        "validators_moved_out_of_default_pr_path_count": len(
            [entry for entry in rows if not entry.runs_on_pull_request_default]
        ),
        "validators_still_running_on_main_count": len(
            [entry for entry in rows if entry.runs_on_main_push]
        ),
        "validators_deleted_count": 0,
        "tests_deleted_count": 0,
    }
    class_to_key = {
        FAST_UNIVERSAL_PREFLIGHT: "fast_universal_preflight_count",
        CHANGED_AREA_VALIDATOR: "changed_area_validator_count",
        TOUCHED_GENERATED_ARTIFACT_VALIDATOR: (
            "touched_generated_artifact_validator_count"
        ),
        DETERMINISTIC_GENERATED_ARTIFACT_VALIDATOR: (
            "deterministic_generated_artifact_validator_count"
        ),
        NIGHTLY_DEEP_VALIDATOR: "nightly_deep_validator_count",
        RELEASE_LIVE_READINESS_VALIDATOR: "release_live_readiness_validator_count",
    }
    for entry in rows:
        for validator_class in entry.validator_class:
            counts[class_to_key[validator_class]] += 1
    return counts


def inventory_report_rows(
    entries: Sequence[ValidatorInventoryEntry] | None = None,
) -> list[dict[str, object]]:
    rows = tuple(validation_inventory() if entries is None else entries)
    report_rows: list[dict[str, object]] = []
    for entry in rows:
        report_rows.append(
            {
                "validator_id": entry.validator_id,
                "command": list(entry.command),
                "phase": entry.phase,
                "validator_class": list(entry.validator_class),
                "owner_domain": entry.owner_domain,
                "owner_pr_or_feature": entry.owner_pr_or_feature,
                "input_globs": list(entry.input_globs),
                "output_globs": list(entry.output_globs),
                "generated_report_globs": list(entry.generated_report_globs),
                "tool_globs": list(entry.tool_globs),
                "test_globs": list(entry.test_globs),
                "workflow_globs": list(entry.workflow_globs),
                "cost_tier": entry.cost_tier,
                "pull_request_default_behavior": (
                    "run" if entry.runs_on_pull_request_default else "run_when_touched"
                ),
                "main_behavior": "run" if entry.runs_on_main_push else "skip",
                "nightly_behavior": "run" if entry.runs_on_nightly else "skip",
                "manual_full_behavior": (
                    "run" if entry.runs_on_manual_full else "skip"
                ),
                "release_live_readiness_behavior": (
                    "run" if entry.runs_on_release_live_readiness else "skip"
                ),
                "fail_closed_if_touched": entry.fail_closed_if_touched,
                "fail_closed_if_unknown_change": entry.fail_closed_if_unknown_change,
                "cross_platform_sensitive": entry.cross_platform_sensitive,
                "linux_required": entry.linux_required,
                "windows_required": entry.windows_required,
                "pr152_tracked": entry.pr152_tracked,
                "full_validation_required_when_changed": (
                    entry.full_validation_required_when_changed
                ),
                "rationale": entry.rationale,
            }
        )
    return report_rows


def validate_inventory(entries: Sequence[ValidatorInventoryEntry] | None = None) -> tuple[str, ...]:
    rows = tuple(validation_inventory() if entries is None else entries)
    failures: list[str] = []
    ids = [entry.validator_id for entry in rows]
    duplicates = sorted({validator_id for validator_id in ids if ids.count(validator_id) > 1})
    for duplicate in duplicates:
        failures.append(f"VALIDATION_INVENTORY_DUPLICATE_ID: {duplicate}")

    expected_ids: set[str] = set()
    validation_dir = Path(".tmp/qtt_validation_inventory")
    pytest_basetemp = validation_dir / "pytest"
    for phase_record in runner.build_phase_manifest(validation_dir, pytest_basetemp):
        phase = str(phase_record["phase"])
        for command in phase_record["commands"]:
            expected_ids.add(validator_id_for_command(command, phase))
    missing = sorted(expected_ids - set(ids))
    extra = sorted(set(ids) - expected_ids)
    for validator_id in missing:
        failures.append(f"VALIDATION_INVENTORY_MISSING_RUNNER_COMMAND: {validator_id}")
    for validator_id in extra:
        failures.append(f"VALIDATION_INVENTORY_UNKNOWN_EXTRA_COMMAND: {validator_id}")

    repo_root = Path(__file__).resolve().parents[1]
    for entry in rows:
        if not entry.validator_id:
            failures.append("VALIDATION_INVENTORY_EMPTY_VALIDATOR_ID")
        if not entry.command:
            failures.append(f"VALIDATION_INVENTORY_EMPTY_COMMAND: {entry.validator_id}")
        if entry.cost_tier not in COST_TIERS:
            failures.append(f"VALIDATION_INVENTORY_BAD_COST_TIER: {entry.validator_id}")
        if not set(entry.validator_class).issubset(VALIDATOR_CLASSES):
            failures.append(f"VALIDATION_INVENTORY_BAD_CLASS: {entry.validator_id}")
        for field_name in (
            "input_globs",
            "output_globs",
            "generated_report_globs",
            "schema_globs",
            "tool_globs",
            "test_globs",
            "workflow_globs",
            "required_when_files_match",
        ):
            for glob in getattr(entry, field_name):
                if "\\" in glob:
                    failures.append(
                        "VALIDATION_INVENTORY_BACKSLASH_GLOB: "
                        f"{entry.validator_id} {field_name} {glob}"
                    )
                try:
                    normalize_repo_ref(glob.replace("/**", "/sentinel"))
                except ValueError as exc:
                    failures.append(
                        "VALIDATION_INVENTORY_BAD_GLOB: "
                        f"{entry.validator_id} {field_name} {glob} {exc}"
                    )
        for glob in entry.tool_globs:
            if "*" not in glob and glob.endswith(".py") and not (repo_root / glob).is_file():
                failures.append(
                    f"VALIDATION_INVENTORY_MISSING_TOOL: {entry.validator_id} {glob}"
                )
        if entry.owner_domain == "UNKNOWN" and not entry.full_validation_required_when_changed:
            failures.append(
                f"VALIDATION_INVENTORY_UNKNOWN_OWNER_NOT_FULL: {entry.validator_id}"
            )
        if not entry.rationale:
            failures.append(f"VALIDATION_INVENTORY_MISSING_RATIONALE: {entry.validator_id}")
        if not entry.required_when_files_match:
            failures.append(
                f"VALIDATION_INVENTORY_EMPTY_MATCH_GLOBS: {entry.validator_id}"
            )
    return tuple(failures)


def phase_job_id(phase: str) -> str:
    return PHASE_JOB_IDS[phase]


def phase_job_ids_for_validators(
    validator_ids: Iterable[str],
    entries_by_id: Mapping[str, ValidatorInventoryEntry] | None = None,
) -> tuple[str, ...]:
    by_id = inventory_by_id() if entries_by_id is None else dict(entries_by_id)
    return tuple(
        sorted(
            {
                PHASE_JOB_IDS[by_id[validator_id].phase]
                for validator_id in validator_ids
                if validator_id in by_id and by_id[validator_id].phase in PHASE_JOB_IDS
            }
        )
    )
