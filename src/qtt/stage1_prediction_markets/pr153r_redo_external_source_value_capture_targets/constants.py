"""Path and count constants for PR153R redo."""

from __future__ import annotations

from pathlib import Path

from . import taxonomy as tx

PR_ID = "PR153R_REDO"
CONTROLLER_VERSION = "v1.0"
REPORT_PATH = Path(
    "docs/master_plan/generated/PR153R_RedoExternalSourceValueCaptureTargets.report.json"
)
REPORT_AUTHORITY_CLASS = (
    "PR153R_REDO_EXTERNAL_SOURCE_VALUE_CAPTURE_TARGETS_ONLY_NOT_FACT_ACCEPTANCE_"
    "NOT_CONNECTOR_NOT_RUNTIME_NOT_ORDER_NOT_ATOMICROWS_NOT_QTT_SHA_AUTHORITY"
)
SUCCESS_MARKER = "QTT_PR153R_REDO_EXTERNAL_SOURCE_VALUE_CAPTURE_TARGETS_OK"

EXPECTED_TARGET_COUNT = 34
EXPECTED_PLATFORM_COUNTS = {
    "FORECASTEX_IBKR": 16,
    "KALSHI": 10,
    "POLYMARKET": 8,
}
PR151_TOTAL_TARGET_COUNT = 342
CORRECTED_PUBLIC_DENOMINATOR_COUNT = 126
PR154_ACCEPTANCE_REVIEW_ONLY_PACKET_COUNT = 92

PR153_REPORT_PATH = Path(
    "docs/master_plan/generated/PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json"
)
PR151_REPORT_PATH = Path(
    "docs/master_plan/generated/PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json"
)
OWNER_SUPPLIED_DIR = Path("docs/master_plan/source_evidence/owner_supplied_pr153r_redo")
OWNER_SEED_JSON_PATH = (
    OWNER_SUPPLIED_DIR / "PR153R_34_retry_targets_official_source_seed_map.json"
)
OWNER_SEED_CSV_PATH = (
    OWNER_SUPPLIED_DIR / "PR153R_34_retry_targets_official_source_seed_map.csv"
)
OWNER_EXTRACTED_JSON_PATH = (
    OWNER_SUPPLIED_DIR / "PR153R_extracted_external_lane_from_zip.json"
)

MANDATORY_CONTROL_PLANE_PATHS = (
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
    Path("docs/master_plan/generated/PR136RouteTriage.report.json"),
    Path("docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"),
    Path("docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    Path("docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"),
    Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"),
    Path(
        "docs/master_plan/generated/"
        "PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json"
    ),
    PR151_REPORT_PATH,
    PR153_REPORT_PATH,
    Path("docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"),
    Path("docs/master_plan/QTT_MasterPlan_Current.md"),
    OWNER_SEED_JSON_PATH,
    OWNER_SEED_CSV_PATH,
    OWNER_EXTRACTED_JSON_PATH,
)

PR136_SECTION_CROSSWALK_ALIAS = Path(
    "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
)
PR136_SECTION_CROSSWALK_CANONICAL_SUCCESSOR = Path(
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)

OWNER_SUPPLIED_INPUT_PATHS = (
    OWNER_SEED_JSON_PATH,
    OWNER_SEED_CSV_PATH,
    OWNER_EXTRACTED_JSON_PATH,
)

REQUIRED_COMMANDS = (
    "git branch --show-current",
    "git status --short",
    "git diff --check",
    ".\\.venv\\Scripts\\python.exe tools\\validate_pr153r_redo_external_source_value_capture_targets.py",
    (
        ".\\.venv\\Scripts\\python.exe -m pytest "
        "tests\\source_evidence\\test_pr153r_redo_external_source_value_capture_targets.py -q"
    ),
    ".\\.venv\\Scripts\\python.exe -m pytest tests\\source_evidence -q",
    ".\\.venv\\Scripts\\python.exe tools\\run_validation_gates.py",
    "git status --short",
    "git diff --name-only",
    "git diff --stat",
)

FORBIDDEN_RETRY_LANES = (
    tx.INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET,
    tx.TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED,
    tx.PRIVATE_DOC_OR_ATTESTATION_REQUIRED,
    tx.OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE,
)

ACCEPTED_PACKET_DIR = Path("docs/master_plan/generated/source_evidence/pr153r_redo")
