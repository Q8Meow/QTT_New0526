from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from ..stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
if TYPE_CHECKING:
    from ..stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
        ST12GOwnerProjectionResolutionV2,
        ST12GProjectionResolutionV2,
    )


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_svc1")

JSONL_FILES = frozenset(
    {
        "service_registry.jsonl",
        "read_model_snapshots.generated.jsonl",
        "read_model_snapshot_index.generated.jsonl",
        "read_model_store_contracts.generated.jsonl",
        "event_stream_contracts.generated.jsonl",
        "owner_action_requests.generated.jsonl",
        "owner_action_receipts.generated.jsonl",
        "action_eligibility.generated.jsonl",
        "action_denied_reasons.generated.jsonl",
        "provider_pending_routes.generated.jsonl",
        "pretrade_view_routes.generated.jsonl",
        "no_trade_explanation_views.generated.jsonl",
        "tca_decomposition_views.generated.jsonl",
        "execution_adjusted_ranking_views.generated.jsonl",
        "qku_formula_compute_route_views.generated.jsonl",
        "agent_workflow_queue_views.generated.jsonl",
        "llm_grounding_route_views.generated.jsonl",
        "quantum_structural_readiness_views.generated.jsonl",
        "owner_ux_semantic_routes.generated.jsonl",
        "owner_chart_manifest.generated.jsonl",
        "owner_widget_manifest.generated.jsonl",
        "agent_operations_views.generated.jsonl",
        "team_workflow_queue_views.generated.jsonl",
        "owner_audit_trail_views.generated.jsonl",
        "execution_live_status_preview_views.generated.jsonl",
        "owner_next_step_routes.generated.jsonl",
        "surface_parity_routes.generated.jsonl",
        "artifact_value_route_map.generated.jsonl",
        "market_venue_expansion_socket_routes.generated.jsonl",
        "downstream_dag_route_views.generated.jsonl",
        "owner_conversation_views.generated.jsonl",
        "owner_plain_english_intent_routes.generated.jsonl",
        "owner_chat_route_previews.generated.jsonl",
        "owner_research_intake_routes.generated.jsonl",
        "owner_trade_intent_routes.generated.jsonl",
        "owner_search_index_routes.generated.jsonl",
        "owner_layout_profile_routes.generated.jsonl",
        "owner_notification_tier_policy.generated.jsonl",
        "owner_stale_data_banner_views.generated.jsonl",
        "mobile_app_shell_contract_views.generated.jsonl",
        "mobile_navigation_contract_views.generated.jsonl",
        "trade_workbench_route_views.generated.jsonl",
        "execution_ladder_stage_views.generated.jsonl",
        "ui_visual_qa_handoff_views.generated.jsonl",
    }
)


@dataclass(frozen=True)
class OwnerDashboardReadModelV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class OwnerSessionBoundaryV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class OwnerActionRequestQueueV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class OwnerAuditReceiptStreamV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class DashboardEventStreamV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class DashboardAuthBoundary:
    row: dict[str, Any]


@dataclass(frozen=True)
class DashboardSessionPolicy:
    row: dict[str, Any]


@dataclass(frozen=True)
class DashboardReadModelStore:
    rows: tuple[dict[str, Any], ...]


class DashboardSnapshotProvider(DashboardReadModelStore):
    pass


class DashboardEventStreamProvider(DashboardReadModelStore):
    pass


class DashboardActionRequestQueue(DashboardReadModelStore):
    pass


class DashboardAuditReceiptStream(DashboardReadModelStore):
    pass


class OwnerDashboardReadModelSnapshotV1(OwnerDashboardReadModelV1):
    pass


class OwnerActionRequestEnvelopeV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionReceiptEnvelopeV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionEligibilityViewV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionDeniedReasonV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionProviderPendingReasonV1(OwnerActionRequestQueueV1):
    pass


class OwnerSessionPolicyV1(OwnerSessionBoundaryV1):
    pass


class OwnerEventStreamCursorV1(DashboardEventStreamV1):
    pass


class OwnerAuditReceiptCursorV1(OwnerAuditReceiptStreamV1):
    pass


class OwnerDecisionQueueReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerAgentActivityReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerWorkflowQueueReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerReceiptPreviewReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerWorkflowQueuePreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerAgentActivityPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerPreTradeDecisionPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerNoTradeExplanationPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerTCADecompositionPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerExecutionAdjustedRankingPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerQKUFormulaRoutePreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerExecutionLadderPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerQuantumReadinessPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerUXSemanticBundleViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerWidgetManifestViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerChartManifestViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerAgentOperationsViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerTeamWorkflowQueueViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerAuditTrailViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerExecutionStatusPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerNextStepRouteViewV1(OwnerDashboardReadModelV1):
    pass


class ArtifactValueRouteMapViewV1(OwnerDashboardReadModelV1):
    pass


class MarketVenueExpansionSocketViewV1(OwnerDashboardReadModelV1):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return tuple(rows)


class _WindowsEvidenceProcessV1:
    """Lazy original-handle adapter; the SVC owner must settle every launch."""

    def __init__(self, supervisor, attempt):
        import os
        import threading
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceAttemptOperationV1
        _native_require(os.name == "nt", "UNAVAILABLE_PLATFORM")
        _native_require(type(supervisor) is EvidenceProcessSupervisorV1 and type(attempt) is _EvidenceAttemptOperationV1
                        and attempt.supervisor is supervisor and attempt.phase == "COMMITTED_AND_READBACK",
                        "LP03_NATIVE_ORIGINAL_ATTEMPT_REQUIRED")
        EvidenceProcessSupervisorV1._assert_original_v1(supervisor)
        # Construction allocates no native job, process or pipe. SVC retains
        # this exact object before any effectful preparation can begin.
        self.supervisor, self.attempt = supervisor, attempt
        self.original = (supervisor, attempt, attempt.grant_record, attempt.limits, attempt.deadline, attempt.handle)
        self.job = self.process = self.thread = self.pid = None
        self.stdin = self.stdout = self.stderr = None
        self.identity = self.launch_observation = None
        self.assigned = self.resumed = False
        self.kernel = self.api = self.ctypes = None
        self.extended_type = self.accounting_type = None
        self.argv = self.environment = None
        self._native_custody = (None, None, None, None, None)
        self._api_original = None
        self.process_information = self.startup_type = self.process_information_type = None
        self._process_information_original = None
        self._image_objects = []
        self._image_original = None
        self.cleanup_errors = []
        self._io = None
        self._drain_original = None
        self._terminal_original = None
        self._pipe_original = None
        self._partial_pipe_original = []
        self._no_child_original = None
        self._controller = self._controller_done = self._stop_signal = None
        self._stop_at = None
        self._reasons, self._controller_errors = [], []
        self._failed_trigger_capture = None
        self._last_native = None
        self._parent_output_ordinal = 0
        self._events_dispatched = self._computations_dispatched = 0
        self._callbacks_dispatched = self._coordinates_observed = 0
        self._write_lock, self._cancel_thread = threading.Lock(), None
        self._control_lock = threading.RLock()
        self._settlement_bounds = None
        self._stop_attempted = False
        self._stop_claims = ()
        self._image_owned = ()
        self._resource_failure_native = self._suspended_native = None
        self._associated_images, self._diagnostic_handles = (), ()
        self._observation_originals, self._exchange_original = (), None
        self.phase = "NOT_PREPARED"

    def __copy__(self):
        raise TypeError("LP03 native process custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 native process custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 native process custody cannot be serialized")

    def _assert_owner_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        EvidenceProcessSupervisorV1._assert_custody_v1(self.supervisor)
        _native_require(type(self) is _WindowsEvidenceProcessV1 and self.supervisor._active is self
                        and self.supervisor is self.original[0] and self.attempt is self.original[1]
                        and self.attempt.grant_record is self.original[2] and self.attempt.limits is self.original[3]
                        and self.attempt.deadline is self.original[4] and self.attempt.handle is self.original[5],
                        "LP03_NATIVE_PROCESS_NOT_ORIGINAL")

    def _assert_native_handles_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _WindowsEvidenceProcessV1._assert_owner_v1(self)
        original = self._native_custody
        _native_require((self.job, self.process, self.thread, self.pid) == original[:4] and self.identity is original[4],
                        "LP03_NATIVE_ORIGINAL_HANDLES_CHANGED")
        if self._api_original is not None:
            _native_require(all(left is right for left, right in zip(
                (self.ctypes, self.api, self.kernel, self.extended_type, self.accounting_type,
                 self.startup_type, self.process_information_type), self._api_original)),
                "LP03_NATIVE_ORIGINAL_API_CHANGED")
        _native_require(self.process_information is self._process_information_original,
                        "LP03_NATIVE_ORIGINAL_PROCESS_INFORMATION_CHANGED")
        if self._pipe_original is not None:
            _native_require(all(getattr(self, name) is stream for name, stream, _fd, _handle in self._pipe_original),
                            "LP03_NATIVE_ORIGINAL_PIPES_CHANGED")

    def _load_api_v1(self):
        import ctypes
        import _winapi
        from ctypes import wintypes
        self.ctypes, self.api = ctypes, _winapi
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)

        class BasicLimits(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        class Accounting(ctypes.Structure):
            _fields_ = [("TotalUserTime", ctypes.c_longlong), ("TotalKernelTime", ctypes.c_longlong),
                ("ThisPeriodTotalUserTime", ctypes.c_longlong), ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
                ("TotalPageFaultCount", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
                ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD)]

        class StartupInfo(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                *((name, wintypes.DWORD) for name in ("dwX", "dwY", "dwXSize", "dwYSize",
                    "dwXCountChars", "dwYCountChars", "dwFillAttribute", "dwFlags")),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]

        class StartupInfoEx(ctypes.Structure):
            _fields_ = [("StartupInfo", StartupInfo), ("lpAttributeList", ctypes.c_void_p)]

        class ProcessInformation(ctypes.Structure):
            _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                        ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]

        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "IsProcessInJob": ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "GetProcessId": ([wintypes.HANDLE], wintypes.DWORD),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "GetProcessTimes": ([wintypes.HANDLE, *(ctypes.POINTER(ctypes.c_ulonglong),) * 4], wintypes.BOOL),
            "QueryFullProcessImageNameW": ([wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "CreateFileW": ([wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                             wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE], wintypes.HANDLE),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "GetFileType": ([wintypes.HANDLE], wintypes.DWORD),
            "GetFileInformationByHandleEx": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "GetFinalPathNameByHandleW": ([wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD], wintypes.DWORD),
            "InitializeProcThreadAttributeList": ([ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_size_t)], wintypes.BOOL),
            "UpdateProcThreadAttribute": ([ctypes.c_void_p, wintypes.DWORD, ctypes.c_size_t, ctypes.c_void_p,
                                           ctypes.c_size_t, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)], wintypes.BOOL),
            "DeleteProcThreadAttributeList": ([ctypes.c_void_p], None),
            "CreateProcessW": ([wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
                ctypes.POINTER(StartupInfoEx), ctypes.POINTER(ProcessInformation)], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(kernel, name)
            function.argtypes, function.restype = arguments, result
        self.kernel, self.extended_type, self.accounting_type = kernel, ExtendedLimits, Accounting
        self.startup_type, self.process_information_type = StartupInfoEx, ProcessInformation
        self._api_original = (ctypes, _winapi, kernel, ExtendedLimits, Accounting, StartupInfoEx, ProcessInformation)

    def _retain_image_objects_v1(self, logical, engine):
        """Retain the original executable files and ancestors without source authority."""
        from .owner_source_use_windows import _object_state_v1
        paths = tuple(dict.fromkeys(path for file in (logical, engine) for path in (*reversed(file.parents), file)))
        for path in paths:
            directory = path not in (logical, engine)
            handle = self.kernel.CreateFileW(str(path), 0x81, 3 if directory else 1, None, 3,
                0x200000 | (0x2000000 if directory else 0), None)
            if handle in (None, self.ctypes.c_void_p(-1).value):
                raise self.ctypes.WinError(self.ctypes.get_last_error())
            self._image_owned = (*self._image_owned, (handle, path, directory))
            self._image_objects.append((handle, path, directory, None))
            observed = _object_state_v1(self, handle, path, directory)
            self._image_objects[-1] = (handle, path, directory, observed)
        return tuple(self._image_objects)

    def _check_image_objects_v1(self, original):
        from .owner_source_use_windows import _object_state_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _native_require(tuple(self._image_objects) == original, "LP03_NATIVE_IMAGE_HANDLE_ROSTER_CHANGED")
        for handle, path, directory, observed in original:
            _native_require(_object_state_v1(self, handle, path, directory) == observed,
                            "LP03_NATIVE_IMAGE_FILE_CHANGED")

    def _process_identity_v1(self, handle):
        from ctypes import wintypes
        ctypes, _api, kernel = self._api_original[:3]
        pid = kernel.GetProcessId(handle)
        times = tuple(ctypes.c_ulonglong() for _ in range(4))
        image, count = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
        if not pid or not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(count)):
            raise ctypes.WinError(ctypes.get_last_error())
        return (int(pid), int(times[0].value), str(Path(image.value).resolve()))

    def prepare_suspended_v1(self):
        import os
        import sys
        import msvcrt
        import subprocess
        from ctypes import wintypes
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1, _EvidenceAttemptOperationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        _WindowsEvidenceProcessV1._assert_owner_v1(self)
        _native_require(self.phase == "NOT_PREPARED" and self.job is None and self.process is None, "LP03_NATIVE_LAUNCH_ALREADY_ATTEMPTED")
        self.phase = "PREPARING"
        _WindowsEvidenceProcessV1._load_api_v1(self)
        operation = self.attempt.registration
        _EvidenceRegistrationOperationV1._check_current_v1(operation)
        consumed = _EvidenceAttemptOperationV1._consumption_v1(self.attempt)
        limits = self.attempt.limits
        remaining_cpu = limits.max_cpu_ns - limits.reserved_failure_cpu_ns - consumed.cpu_ns
        _native_require(remaining_cpu >= 100 and limits.max_process_memory_bytes > 0 and limits.max_job_memory_bytes > 0
                        and limits.max_concurrency == 1, "LP03_NATIVE_NECESSARY_RESOURCE_LIMIT_UNAVAILABLE")
        # Approved current engine is observed natively. The logical fixed P
        # command keeps its venv identity without launching an extra shim child.
        logical, engine = Path(os.path.abspath(sys.executable)), Path(os.path.abspath(sys._base_executable))
        capacity = tuple(entry for entry in self.supervisor._capacity_originals if entry[0] is self)
        _native_require(len(capacity) == 1 and capacity[0][1] is self.original and capacity[0][2] is self.attempt.payload
                        and str(engine.resolve()) == capacity[0][3]["launch_image_path"],
                        "LP03_NATIVE_ORIGINAL_CAPACITY_IMAGE_CHANGED")
        current = _WindowsEvidenceProcessV1._process_identity_v1(self, self.api.GetCurrentProcess())
        _native_require(Path(current[2]) == engine, "LP03_NATIVE_ENGINE_IDENTITY_MISMATCH")
        image_objects = _WindowsEvidenceProcessV1._retain_image_objects_v1(self, logical, engine)
        self._image_original = image_objects
        argv = (str(logical), "-B", "-m", "src.qtt.stage1_prediction_markets.qku_computation_control_plane.evidence_execution", "--worker-v1")
        environment = {name: os.environ[name] for name in ("SystemRoot", "WINDIR") if name in os.environ}
        environment.update(__PYVENV_LAUNCHER__=str(logical), PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONUTF8="1")
        self.argv, self.environment = argv, tuple(sorted(environment.items()))
        # Fixed local buffers cannot be redirected by a later member mutation.
        command_line = self.ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        environment_block = self.ctypes.create_unicode_buffer("\0".join(f"{key}={value}" for key, value in self.environment) + "\0")
        cwd = str(Path(__file__).resolve().parents[3])
        self.job = self.kernel.CreateJobObjectW(None, None)
        self._native_custody = (self.job, None, None, None, None)
        if not self.job:
            raise self.ctypes.WinError(self.ctypes.get_last_error())
        job_limits = self.extended_type()
        # Documented Windows JOB_TIME|ACTIVE_PROCESS|PROCESS_MEMORY|JOB_MEMORY|
        # KILL_ON_JOB_CLOSE flags. Both breakaway flags remain absent.
        job_limits.BasicLimitInformation.LimitFlags = 0x0000230C
        job_limits.BasicLimitInformation.ActiveProcessLimit = 1
        job_limits.BasicLimitInformation.PerJobUserTimeLimit = remaining_cpu // 100
        job_limits.ProcessMemoryLimit, job_limits.JobMemoryLimit = limits.max_process_memory_bytes, limits.max_job_memory_bytes
        if not self.kernel.SetInformationJobObject(self.job, 9, self.ctypes.byref(job_limits), self.ctypes.sizeof(job_limits)):
            raise self.ctypes.WinError(self.ctypes.get_last_error())
        child_fds, attributes = [], None
        attributes_initialized = False
        def owned_pipe_stream(fd, mode):
            try:
                return os.fdopen(fd, mode, buffering=0)
            except BaseException:
                os.close(fd)
                raise
        try:
            input_read, input_write = os.pipe()
            child_fds.append(input_read)
            self.stdin = owned_pipe_stream(input_write, "wb")
            self._partial_pipe_original.append(("stdin", self.stdin))
            output_read, output_write = os.pipe()
            child_fds.append(output_write)
            self.stdout = owned_pipe_stream(output_read, "rb")
            self._partial_pipe_original.append(("stdout", self.stdout))
            error_read, error_write = os.pipe()
            child_fds.append(error_write)
            self.stderr = owned_pipe_stream(error_read, "rb")
            self._partial_pipe_original.append(("stderr", self.stderr))
            self._pipe_original = tuple((name, getattr(self, name), getattr(self, name).fileno(),
                msvcrt.get_osfhandle(getattr(self, name).fileno())) for name in ("stdin", "stdout", "stderr"))
            inherited = [msvcrt.get_osfhandle(fd) for fd in child_fds]
            for handle in inherited:
                os.set_handle_inheritable(handle, True)
            startup = self.startup_type()
            startup.StartupInfo.cb = self.ctypes.sizeof(startup)
            startup.StartupInfo.dwFlags = subprocess.STARTF_USESTDHANDLES | subprocess.STARTF_USESHOWWINDOW
            startup.StartupInfo.wShowWindow = subprocess.SW_HIDE
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = inherited
            attribute_size = self.ctypes.c_size_t()
            self.ctypes.set_last_error(0)
            sized = self.kernel.InitializeProcThreadAttributeList(None, 1, 0, self.ctypes.byref(attribute_size))
            _native_require(not sized and self.ctypes.get_last_error() == 122 and 0 < attribute_size.value <= 65536,
                            "LP03_NATIVE_ATTRIBUTE_LIST_SIZE")
            attributes = self.ctypes.create_string_buffer(attribute_size.value)
            if not self.kernel.InitializeProcThreadAttributeList(attributes, 1, 0, self.ctypes.byref(attribute_size)):
                raise self.ctypes.WinError(self.ctypes.get_last_error())
            attributes_initialized = True
            startup.lpAttributeList = self.ctypes.cast(attributes, self.ctypes.c_void_p)
            handles = (wintypes.HANDLE * 3)(*inherited)
            if not self.kernel.UpdateProcThreadAttribute(attributes, 0, 0x00020002, handles,
                self.ctypes.sizeof(handles), None, None):
                raise self.ctypes.WinError(self.ctypes.get_last_error())
            # Retain native output storage BEFORE calling Windows. Even if a
            # Python conversion raises after native success, custody survives.
            information = self.process_information_type()
            self.process_information = self._process_information_original = information
            self.supervisor._creation_originals = (*self.supervisor._creation_originals,
                (self, "OUTPUT_ALLOCATED", information, None))
            original_job, ctypes, kernel = self.job, self.ctypes, self.kernel
            _WindowsEvidenceProcessV1._check_image_objects_v1(self, image_objects)
            _EvidenceRegistrationOperationV1._check_current_v1(operation)
            _WindowsEvidenceProcessV1._assert_native_handles_v1(self)
            _native_require(tuple(self._image_objects) == image_objects, "LP03_NATIVE_IMAGE_HANDLE_ROSTER_CHANGED")
            _native_require(self._stop_signal is not None and not self._stop_signal.is_set(), "LP03_NATIVE_LAUNCH_STOPPED")
            self.phase = "CREATE_PROCESS_ENTERED"
            self.supervisor._creation_originals = (*self.supervisor._creation_originals,
                (self, "ENTERED", information, None))
            try:
                created = kernel.CreateProcessW(str(engine), command_line, None, None, True,
                    # Detach the console so Windows does not add conhost.exe.
                    # This does not break away from the enclosing Job chain.
                    subprocess.DETACHED_PROCESS | 0x00000004 | 0x00080000 | 0x00000400,
                    environment_block, cwd, ctypes.byref(startup), ctypes.byref(information))
                self.supervisor._creation_originals = (*self.supervisor._creation_originals,
                    (self, "RETURNED_SUCCESS" if created else "RETURNED_FAILURE", information, bool(created)))
                launch_error = ctypes.get_last_error()
            finally:
                self.process, self.thread, self.pid = information.hProcess, information.hThread, information.dwProcessId or None
                self._native_custody = (original_job, self.process, self.thread, self.pid, None)
            if not created:
                self.phase = "CREATE_PROCESS_RETURNED_FAILURE"
                raise ctypes.WinError(launch_error)
            process, thread, pid = self.process, self.thread, self.pid
            _native_require(bool(process) and bool(thread) and bool(pid), "LP03_NATIVE_CREATE_OUTPUT_UNPROVEN")
            identity = _WindowsEvidenceProcessV1._process_identity_v1(self, process)
            with self._control_lock:
                self.identity = identity
                self._native_custody = (original_job, process, thread, pid, identity)
            _native_require(self.identity[0] == pid and self.identity[2] == capacity[0][3]["launch_image_path"],
                            "LP03_NATIVE_CHILD_IDENTITY_MISMATCH")
            if not kernel.AssignProcessToJobObject(original_job, process):
                raise ctypes.WinError(ctypes.get_last_error())
            self.assigned = True
            member = wintypes.BOOL()
            if not kernel.IsProcessInJob(process, original_job, ctypes.byref(member)) or not member.value:
                raise OSError("LP03_NATIVE_JOB_MEMBERSHIP_UNPROVEN")
            self._suspended_native = _WindowsEvidenceProcessV1.observe_v1(self)
            _native_require(self._suspended_native["active_processes"] == self._suspended_native["total_processes"] == 1
                            and self._suspended_native["assigned_process_ids"] == (pid,)
                            and self._suspended_native["effective_limit_flags"] == 0x0000230C
                            and self._suspended_native["effective_active_process_limit"] == 1,
                            "LP03_NATIVE_SUSPENDED_JOB_CONFIGURATION")
            self.launch_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            self.phase = "SUSPENDED_AND_ASSIGNED"
        finally:
            if attributes_initialized:
                try:
                    self.kernel.DeleteProcThreadAttributeList(attributes)
                except BaseException as exc:
                    self.cleanup_errors.append(("DELETE_PROCESS_ATTRIBUTES", type(exc).__name__))
            for fd in child_fds:
                try:
                    os.close(fd)
                except BaseException as exc:
                    self.cleanup_errors.append(("CLOSE_CHILD_PIPE", fd, type(exc).__name__))
            if self.cleanup_errors:
                self.supervisor._unresolved = True

    def resume_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1, _EvidenceAttemptObservationAppendV1
        _WindowsEvidenceProcessV1._assert_native_handles_v1(self)
        appends = self.attempt.observation_appends
        _native_require(len(appends) == 1 and appends[0].stage == "SUSPENDED" and appends[0].native is self
                        and appends[0].phase == "COMMITTED_AND_READBACK" and appends[0].commit_observation is not None
                        and appends[0].readback_observation is not None, "LP03_NATIVE_RESUME_REQUIRES_DURABLE_IDENTITY")
        _EvidenceAttemptObservationAppendV1._assert_original_v1(appends[0])
        _native_require(self.phase == "SUSPENDED_AND_ASSIGNED" and not self.resumed and self.assigned
                        and self.identity == _WindowsEvidenceProcessV1._process_identity_v1(self, self.process), "LP03_NATIVE_RESUME_CUSTODY")
        _WindowsEvidenceProcessV1._check_image_objects_v1(self, self._image_original)
        with self._control_lock:
            _EvidenceRegistrationOperationV1._check_current_v1(self.attempt.registration)
            _native_require(self.attempt.observation_appends is appends, "LP03_NATIVE_RESUME_OBSERVATION_CHANGED")
            _EvidenceAttemptObservationAppendV1._assert_original_v1(appends[0], canonical=False)
            _WindowsEvidenceProcessV1._assert_native_handles_v1(self)
            _native_require(tuple(self._image_objects) == self._image_original, "LP03_NATIVE_IMAGE_HANDLE_ROSTER_CHANGED")
            _native_require(self._stop_signal is not None and not self._stop_signal.is_set(), "LP03_NATIVE_RESUME_STOPPED")
            job, process, thread, pid, identity = self._native_custody
            if self.kernel.ResumeThread(thread) != 1:
                raise OSError("LP03_NATIVE_PRIMARY_THREAD_RESUME_FAILED")
            self.resumed, self.phase = True, "RESUMED"
            self.api.CloseHandle(thread)
            self.thread = None
            self._native_custody = (job, process, None, pid, identity)

    def observe_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ctypes import wintypes
        ctypes, api, kernel, extended_type, accounting_type, job, process, _thread, pid, identity = self._settlement_custody_v1()
        _native_require(process is not None and job is not None, "LP03_NATIVE_PROCESS_OBSERVATION_UNAVAILABLE")
        observed_pid = kernel.GetProcessId(process)
        times = tuple(ctypes.c_ulonglong() for _ in range(4))
        if not kernel.GetProcessTimes(process, *(ctypes.byref(value) for value in times)):
            raise ctypes.WinError(ctypes.get_last_error())
        _native_require(observed_pid == pid and (identity is None or times[0].value == identity[1]),
                        "LP03_NATIVE_ORIGINAL_PROCESS_CHANGED")
        wait = api.WaitForSingleObject(process, 0)
        _native_require(wait in (api.WAIT_OBJECT_0, api.WAIT_TIMEOUT), "LP03_NATIVE_WAIT_UNPROVEN")
        accounting, extended = accounting_type(), extended_type()
        for info_class, record in ((1, accounting), (9, extended)):
            returned = wintypes.DWORD()
            if not kernel.QueryInformationJobObject(job, info_class, ctypes.byref(record), ctypes.sizeof(record), ctypes.byref(returned)):
                raise ctypes.WinError(ctypes.get_last_error())
            _native_require(returned.value == ctypes.sizeof(record), "LP03_NATIVE_JOB_OBSERVATION_SIZE")
        class ProcessIds(ctypes.Structure):
            _fields_ = [("assigned", wintypes.DWORD), ("listed", wintypes.DWORD), ("ids", ctypes.c_size_t * 4)]
        processes, returned = ProcessIds(), wintypes.DWORD()
        complete_ids = bool(kernel.QueryInformationJobObject(job, 3, ctypes.byref(processes), ctypes.sizeof(processes), ctypes.byref(returned)))
        _native_require(complete_ids and processes.listed == processes.assigned and processes.listed <= 4,
                        "LP03_NATIVE_JOB_PROCESS_ROSTER_UNPROVEN")
        result = dict(process_identity=identity or (int(observed_pid), int(times[0].value)),
            exit_code=(int(api.GetExitCodeProcess(process)) if wait == api.WAIT_OBJECT_0 else None),
            active_processes=int(accounting.ActiveProcesses), total_processes=int(accounting.TotalProcesses),
            terminated_processes=int(accounting.TotalTerminatedProcesses), assigned_process_ids=tuple(processes.ids[:processes.listed]),
            effective_limit_flags=int(extended.BasicLimitInformation.LimitFlags),
            effective_active_process_limit=int(extended.BasicLimitInformation.ActiveProcessLimit),
            cpu_ns=max(int(accounting.TotalUserTime + accounting.TotalKernelTime), int(times[2].value + times[3].value)) * 100,
            process_memory_high_water_bytes=int(extended.PeakProcessMemoryUsed), job_memory_high_water_bytes=int(extended.PeakJobMemoryUsed))
        if self._resource_failure_native is None and (result["active_processes"] > 1 or result["total_processes"] > 1
                or result["process_memory_high_water_bytes"] > self.original[3].max_process_memory_bytes
                or result["job_memory_high_water_bytes"] > self.original[3].max_job_memory_bytes):
            from types import MappingProxyType
            with self._control_lock:
                if self._resource_failure_native is None:
                    self._resource_failure_native = MappingProxyType(result)
                    observations = []
                    for associated_pid in result["assigned_process_ids"]:
                        if associated_pid == pid:
                            continue
                        handle = kernel.OpenProcess(0x00101000, False, associated_pid)
                        if not handle:
                            observations.append((associated_pid, "OPEN_UNAVAILABLE", int(ctypes.get_last_error())))
                            continue
                        self._diagnostic_handles = (*self._diagnostic_handles, handle)
                        try:
                            member = wintypes.BOOL()
                            if not kernel.IsProcessInJob(handle, job, ctypes.byref(member)) or not member.value:
                                observations.append((associated_pid, "ORIGINAL_JOB_MEMBERSHIP_UNPROVEN"))
                            else:
                                observations.append((associated_pid, "ORIGINAL_JOB_MEMBER",
                                    _WindowsEvidenceProcessV1._process_identity_v1(self, handle)))
                        except BaseException as exc:
                            observations.append((associated_pid, "OBSERVATION_UNAVAILABLE", type(exc).__name__))
                        finally:
                            try:
                                if not kernel.CloseHandle(handle):
                                    raise ctypes.WinError(ctypes.get_last_error())
                                self._diagnostic_handles = tuple(value for value in self._diagnostic_handles if value != handle)
                            except BaseException as exc:
                                self.cleanup_errors.append(("CLOSE_JOB_MEMBER_OBSERVATION", type(exc).__name__))
                    self._associated_images = tuple(observations)
        return result

    def _settlement_custody_v1(self):
        """A nonpositive mirror cannot revoke custody of the retained original handles."""
        with self._control_lock:
            return _WindowsEvidenceProcessV1._settlement_custody_locked_v1(self)

    def _settlement_custody_locked_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        supervisor = self.original[0]
        owner = supervisor._issuer.supervisor_original
        _native_require(owner is not None and owner[0] is supervisor and owner[1]._evidence_supervisor_v1 is supervisor
                        and supervisor._issuer.supervisor is supervisor and supervisor._active is self
                        and any(value is self for value in supervisor._retained), "LP03_NATIVE_SETTLEMENT_OWNER_LOST")
        ctypes, api, kernel, extended, accounting, _startup, _information = self._api_original
        job, process, thread, pid, identity = self._native_custody
        information = self._process_information_original
        if process is None and self._terminal_original is None and self._no_child_original is None and information is not None and information.hProcess:
            process, thread, pid = information.hProcess, information.hThread, information.dwProcessId
        try:
            _WindowsEvidenceProcessV1._assert_native_handles_v1(self)
        except BaseException:
            supervisor._unresolved = True
            marker = ("ORIGINAL_CUSTODY_MIRROR_CHANGED",)
            if marker not in self.cleanup_errors:
                self.cleanup_errors.append(marker)
        return ctypes, api, kernel, extended, accounting, job, process, thread, pid, identity

    def request_native_stop_v1(self):
        """Exact owned handles only. A stop request never constitutes terminal proof."""
        with self._control_lock:
            return _WindowsEvidenceProcessV1._request_native_stop_locked_v1(self)

    def _request_native_stop_locked_v1(self):
        if self._terminal_original is not None or self._no_child_original is not None:
            return ()
        ctypes, api, kernel, _extended, _accounting, job, process, _thread, _pid, _identity = self._settlement_custody_v1()
        claim = (job, process)
        if claim in self._stop_claims:
            return ()
        self._stop_claims = (*self._stop_claims, claim)
        errors = []
        job_stopped = False
        if job is not None:
            try:
                job_stopped = bool(kernel.TerminateJobObject(job, 1))
                if not job_stopped:
                    errors.append(("TERMINATE_JOB", int(ctypes.get_last_error())))
            except BaseException as exc:
                errors.append(("TERMINATE_JOB", type(exc).__name__))
        if process is not None and (not self.assigned or not job_stopped):
            try:
                api.TerminateProcess(process, 1)
            except BaseException as exc:
                errors.append(("TERMINATE_ORIGINAL_PROCESS", type(exc).__name__, getattr(exc, "winerror", None)))
        return tuple(errors)

    def _start_drains_v1(self):
        import threading
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence_execution import decode_evidence_worker_frame_v1
        _native_require(self._io is None and all(value is not None for value in (self.stdin, self.stdout, self.stderr)),
                        "LP03_NATIVE_DRAINS_ALREADY_STARTED_OR_UNAVAILABLE")
        condition = threading.Condition()
        io = dict(condition=condition, frames=[], diagnostics=bytearray(), stdout_bytes=bytearray(), output_bytes=0,
                  stdout_observed_bytes=0, stderr_observed_bytes=0,
                  stdout_eof=False, stderr_eof=False, reasons=[], errors=[], threads=())
        self._io = io
        _WindowsEvidenceProcessV1._assert_native_handles_v1(self)
        grant, stdout, stderr = self.original[1].payload, self._pipe_original[1][1], self._pipe_original[2][1]
        causal_scope = grant.causal_timeline_v1()
        frame_count_limit = (5 if causal_scope is None else
            3 + len(causal_scope.event_pins) * (1 + len(causal_scope.callbacks)) + grant.budgets.max_computations)

        def drain(stream, structured):
            pending, ordinal, invalid = bytearray(), 0, False
            try:
                while True:
                    chunk = stream.read(min(4096, grant.budgets.frame_byte_limit + 4))
                    if chunk == b"":
                        with condition:
                            if structured and pending:
                                io["reasons"].append("WORKER_PROTOCOL_INVALID")
                            io["stdout_eof" if structured else "stderr_eof"] = True
                            condition.notify_all()
                        return
                    _native_require(type(chunk) is bytes and bool(chunk), "LP03_NATIVE_PIPE_READ_UNPROVEN")
                    with condition:
                        # Capture original stream bytes before decoding. A
                        # malformed frame cannot erase its own evidence. The
                        # two streams share the existing output-byte ceiling;
                        # retain the within-budget portion of a crossing chunk.
                        capacity = max(0, grant.budgets.max_output_bytes - io["output_bytes"])
                        io["stdout_observed_bytes" if structured else "stderr_observed_bytes"] += len(chunk)
                        io["output_bytes"] += len(chunk)
                        captured = chunk[:capacity]
                        io["stdout_bytes" if structured else "diagnostics"].extend(captured)
                        if io["output_bytes"] > grant.budgets.max_output_bytes:
                            if "RESOURCE_EXHAUSTED" not in io["reasons"]:
                                io["reasons"].append("RESOURCE_EXHAUSTED")
                            invalid = True
                            pending.clear()
                        if structured and not invalid:
                            pending.extend(chunk)
                            try:
                                while len(pending) >= 4:
                                    size = int.from_bytes(pending[:4], "big")
                                    _native_require(0 < size <= grant.budgets.frame_byte_limit, "LP03_WORKER_FRAME_SIZE")
                                    if len(pending) < size + 4:
                                        break
                                    _native_require(ordinal < frame_count_limit, "LP03_WORKER_EXCESS_FRAMES")
                                    raw = bytes(pending[:size + 4])
                                    del pending[:size + 4]
                                    frame = decode_evidence_worker_frame_v1(raw, direction="WORKER_TO_PARENT",
                                        attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref, ordinal=ordinal,
                                        frame_byte_limit=grant.budgets.frame_byte_limit)
                                    io["frames"].append(frame)
                                    ordinal += 1
                            except Exception as exc:
                                invalid = True
                                pending.clear()
                                io["reasons"].append("WORKER_PROTOCOL_INVALID")
                                io["errors"].append(("FRAME_DECODE", type(exc).__name__))
                        condition.notify_all()
            except BaseException as exc:
                with condition:
                    io["reasons"].append("SUPERVISION_FAILURE")
                    io["errors"].append(("STDOUT_DRAIN" if structured else "STDERR_DRAIN", type(exc).__name__))
                    condition.notify_all()

        threads = tuple(threading.Thread(target=drain, args=(stream, structured),
            name="LP03-owned-stdout" if structured else "LP03-owned-stderr", daemon=True)
            for stream, structured in ((stdout, True), (stderr, False)))
        io["threads"] = threads
        self._drain_original = (io, condition, threads, stdout, stderr)
        for thread in threads:
            thread.start()

    def _start_controller_v1(self):
        import threading
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        _native_require(self._controller is None, "LP03_NATIVE_CONTROLLER_ALREADY_STARTED")
        done, stop = threading.Event(), threading.Event()
        self._controller_done, self._stop_signal = done, stop
        clock, attempt = self.supervisor._clock, self.original[1]
        grant, limits = attempt.payload, self.original[3]
        deadline = min(self.original[4].exclusive_deadline_monotonic_ns,
                       attempt.registration.deadline.exclusive_deadline_monotonic_ns)
        expiry = min(attempt.grant_record.exclusive_expiry,
                     attempt.registration.envelope_entry[3].exclusive_expiry_wall_ns)
        _native_require(attempt.failure_bounds is attempt.original[9]
                        and attempt.failure_bounds[0] == deadline
                        and attempt.failure_bounds[1] - attempt.failure_bounds[0] == limits.stop_grace_ns
                        and attempt.failure_bounds[2] - attempt.failure_bounds[1] == limits.reserved_failure_wall_ns
                        and attempt.failure_bounds[2] <= attempt.started[1] + limits.max_wall_ns,
                        "LP03_NATIVE_ORIGINAL_FAILURE_WINDOWS_REQUIRED")
        # All three endpoints were fixed before admission effects. Stop grace
        # belongs only to native settlement, never the later integrity append.
        self._settlement_bounds = attempt.failure_bounds[:2]

        def control():
            stopped = False
            try:
                while not done.is_set():
                    wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(clock)
                    if mono >= deadline or wall >= expiry:
                        self._note_stop_v1("EXPIRED", mono, immediate=True)
                    io = self._io
                    if io is not None:
                        with io["condition"]:
                            for reason in tuple(io["reasons"]):
                                self._note_stop_v1(reason, mono, immediate=False)
                    if self._native_custody[1] is not None and self.identity is not None:
                        native = _WindowsEvidenceProcessV1.observe_v1(self)
                        with self._control_lock:
                            self._last_native = native
                        if (native["cpu_ns"] + cpu - attempt.started[2] > limits.max_cpu_ns - limits.reserved_failure_cpu_ns
                                or native["process_memory_high_water_bytes"] > limits.max_process_memory_bytes
                                or native["job_memory_high_water_bytes"] > limits.max_job_memory_bytes
                                or native["active_processes"] > 1 or native["total_processes"] > 1):
                            self._note_stop_v1("RESOURCE_EXHAUSTED", mono, immediate=False)
                    if stop.is_set() and self._stop_at is not None and mono >= self._stop_at and not stopped and self._api_original is not None:
                        self._stop_attempted = True
                        self._controller_errors.extend(_WindowsEvidenceProcessV1.request_native_stop_v1(self))
                        stopped = True
                    if mono >= self._settlement_bounds[1]:
                        if not self._stop_attempted and self._api_original is not None:
                            self._stop_attempted = True
                            self._controller_errors.extend(_WindowsEvidenceProcessV1.request_native_stop_v1(self))
                        return
                    done.wait(0.01)
            except BaseException as exc:
                EvidenceProcessSupervisorV1._record_failure_secondary_v1(self.supervisor, self, exc, stage="CONTROLLER")
                self._reasons.append("SUPERVISION_FAILURE")
                stop.set()
                if self._api_original is not None:
                    try:
                        self._stop_attempted = True
                        self._controller_errors.extend(_WindowsEvidenceProcessV1.request_native_stop_v1(self))
                    except BaseException as stop_exc:
                        EvidenceProcessSupervisorV1._record_failure_secondary_v1(self.supervisor, self, stop_exc, stage="CONTROLLER_STOP")
                self.supervisor._unresolved = True

        self._controller = threading.Thread(target=control, name="LP03-owned-controller", daemon=True)
        self.supervisor._controller_originals = (*self.supervisor._controller_originals,
            (self, "ALLOCATED", self._controller), (self, "START_ENTERED", self._controller))
        self._controller.start()
        self.supervisor._controller_originals = (*self.supervisor._controller_originals,
            (self, "START_RETURNED", self._controller))

    def _note_stop_v1(self, reason, mono, *, immediate):
        with self._control_lock:
            _WindowsEvidenceProcessV1._note_stop_locked_v1(self, reason, mono, immediate=immediate)

    def _note_stop_locked_v1(self, reason, mono, *, immediate):
        if reason not in self._reasons:
            self._reasons.append(reason)
        deadline = self._settlement_bounds[0]
        stop_at = mono if immediate else min(deadline, mono + self.original[3].stop_grace_ns)
        self._stop_at = stop_at if self._stop_at is None else min(self._stop_at, stop_at)
        if self._stop_signal is not None:
            self._stop_signal.set()
        if not immediate and self.resumed and self._cancel_thread is None and stop_at > mono:
            _WindowsEvidenceProcessV1._start_cancel_v1(self)

    def _start_cancel_v1(self):
        import threading
        from ..stage1_prediction_markets.qku_computation_control_plane import evidence_execution as worker
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        def cancel():
            acquired = False
            try:
                _wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(self.original[0]._clock)
                remaining = max(0.0, min(self._remaining_v1(), (self._stop_at - mono) / 1_000_000_000))
                acquired = self._write_lock.acquire(timeout=remaining)
                if not acquired:
                    return
                _wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(self.original[0]._clock)
                if mono >= self._stop_at or self._pipe_original is None or self._pipe_original[0][1].closed:
                    return
                grant, ordinal = self.original[1].payload, self._parent_output_ordinal
                raw = worker.encode_evidence_worker_frame_v1(dict(protocol=worker.WORKER_PROTOCOL_V1, kind="CANCEL",
                    attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref, ordinal=ordinal,
                    payload=dict(reason_ref=grant.grant_ref + "::SUPERVISOR_STOP")), direction="PARENT_TO_WORKER",
                    attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref, ordinal=ordinal,
                    frame_byte_limit=self.original[3].frame_byte_limit)
                worker._write_worker_bytes_v1(self._pipe_original[0][1], raw)
                self._parent_output_ordinal += 1
            except BaseException as exc:
                self._controller_errors.append(("COOPERATIVE_STOP", type(exc).__name__))
            finally:
                if acquired:
                    self._write_lock.release()
        self._cancel_thread = threading.Thread(target=cancel, name="LP03-owned-cooperative-stop", daemon=True)
        self._cancel_thread.start()

    def _remaining_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(self.original[0]._clock)
        remaining = min(self._settlement_bounds[0] - mono, self.original[2].exclusive_expiry - wall)
        return max(0.0, remaining / 1_000_000_000)

    def _settlement_remaining_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        _wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(self.original[0]._clock)
        return max(0.0, (self._settlement_bounds[1] - mono) / 1_000_000_000)

    def _require_invocation_measurement_v1(self, measurement, *, positive):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import (
            _EvidenceLocalClockV1, _evidence_invocation_measurement_v1)
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
        measured = _evidence_invocation_measurement_v1(measurement)
        supervisor, attempt = self.original[:2]
        observed = _EvidenceLocalClockV1.observe_v1(supervisor._clock)
        _native_require(measured["clock_domain_id"] == supervisor._clock.clock_domain_id
                        and measured["boot_identity_ref"] == supervisor._clock.boot_identity_ref
                        and measured["process_identity_ref"] == "LP03-PROCESS::" + str(self.identity[0]) + ":"
                            + str(self.identity[1]) + ":" + supervisor._clock.boot_identity_ref.split("::", 1)[1]
                        and deterministic_json(measured["clock_declarations"])
                            == deterministic_json(_EvidenceLocalClockV1.declaration_v1(supervisor._clock))
                        and attempt.deadline.admitted_monotonic_ns <= measured["started"][1]
                            <= measured["completed"][1] <= observed[1]
                        and (not positive or measured["completed"][1] < attempt.deadline.exclusive_deadline_monotonic_ns),
                        "LP03_WORKER_INVOCATION_CLOCK_JOIN")

    def _require_probability_edge_failure_v1(self, payload):
        """Require pair failure diagnostics without promoting them to results."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.evidence_execution import (
            _worker_probability_edge_failure_v1, _worker_probability_edge_clock_limits_v1)
        from ..stage1_prediction_markets.qku_computation_control_plane.implementation_registry import resolve_evidence_invocation_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceAuthorizationMessageV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import (
            deterministic_json, _evidence_canonical_object_v1)
        supervisor, attempt = self.original[:2]
        grant = attempt.payload
        _native_require(grant.component_closure == ("MATH-01", "MATH-02")
            and {"producer_invocation_contract", "invocation_contract", "aggregate_observation_prefix",
                 "chain_prefix_or_absence"}.issubset(payload), "LP03_NATIVE_EDGE_FAILURE_FIELDS_REQUIRED")
        contracts = tuple(resolve_evidence_invocation_v1(row[0], implementation_pin=row[1], specification_pin=row[2],
            resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
            for row in grant.component_and_callback_pins["components"])
        _native_require(all(deterministic_json(payload[name]) == deterministic_json(row)
            for name,row in zip(("producer_invocation_contract","invocation_contract"),contracts,strict=True)),
            "LP03_NATIVE_EDGE_FAILURE_GRANT_CONTRACT_JOIN")
        prefix = _worker_probability_edge_failure_v1(payload, attempt_ref=grant.grant_ref)
        aggregate = payload["aggregate_observation_prefix"]
        identity = aggregate["clock_identity"]
        _native_require(identity["clock_domain_id"] == supervisor._clock.clock_domain_id
            and identity["boot_identity_ref"] == supervisor._clock.boot_identity_ref
            and identity["process_identity_ref"] == "LP03-PROCESS::" + str(self.identity[0]) + ":"
                + str(self.identity[1]) + ":" + supervisor._clock.boot_identity_ref.split("::",1)[1]
            and deterministic_json(aggregate["clock_declarations"])
                == deterministic_json(_EvidenceLocalClockV1.declaration_v1(supervisor._clock)),
            "LP03_NATIVE_EDGE_FAILURE_ORIGINAL_CLOCK_IDENTITY")
        if prefix is not None:
            from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_probability_edge_worker_payload_v1
            refs = tuple(dict(store_id=selection.original_store_id,record_id=ref)
                for selection in grant.allowed_reads for ref in selection.selection.record_refs)
            _expected, event = _evidence_probability_edge_worker_payload_v1(attempt.invocations, attempt, contracts,
                original_record_refs=refs,frame_byte_limit=grant.budgets.frame_byte_limit)
            horizon = event["payload"]["source_slices"][0]["reconstructed_canonical_events"][0]["values"]["contract_context"]["horizon_end_wall_ns"]
            message = EvidenceAuthorizationMessageV1.from_canonical_mapping(_evidence_canonical_object_v1(
                attempt.grant_record.signed_grant.canonical_message.encode("utf-8")))
            _native_require(message.exclusive_expiry_wall_ns <= horizon and "execution_clock_limits" in prefix
                and _worker_probability_edge_clock_limits_v1(prefix["execution_clock_limits"]) == (
                    message.valid_from_wall_ns,min(message.exclusive_expiry_wall_ns,horizon),
                    grant.deadline.admitted_monotonic_ns,grant.deadline.exclusive_deadline_monotonic_ns),
                "LP03_NATIVE_EDGE_FAILURE_ORIGINAL_GRANT_CLOCK_LIMITS")
        return prefix

    def _require_probability_edge_frame_v1(self, frame):
        """Repeat original pair joins before any terminal timing promotion."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.implementation_registry import resolve_evidence_invocation_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _require_evidence_probability_edge_result_v1
        attempt = self.original[1]
        grant = attempt.payload
        _native_require(grant.component_closure == ("MATH-01", "MATH-02")
            and frame["kind"] in ("FAILED","COMPUTATION_RESULT"),"LP03_NATIVE_EDGE_FRAME_SCOPE")
        if frame["kind"] == "FAILED":
            return _WindowsEvidenceProcessV1._require_probability_edge_failure_v1(self,frame["payload"])
        contracts = tuple(resolve_evidence_invocation_v1(row[0],implementation_pin=row[1],specification_pin=row[2],
            resource_policy_ref=grant.protocol_ref,origin=attempt.grant_record.origin)
            for row in grant.component_and_callback_pins["components"])
        refs = tuple(dict(store_id=selection.original_store_id,record_id=ref)
            for selection in grant.allowed_reads for ref in selection.selection.record_refs)
        result = _require_evidence_probability_edge_result_v1(attempt.invocations,attempt,contracts,frame["payload"],
            original_record_refs=refs,frame_byte_limit=grant.budgets.frame_byte_limit)
        _WindowsEvidenceProcessV1._require_invocation_measurement_v1(self,frame["payload"]["invocation_measurement"],positive=True)
        return result

    def _receive_v1(self, ordinal, kind):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        io = self._io
        with io["condition"]:
            while len(io["frames"]) <= ordinal and not self._reasons and not io["reasons"] and not io["stdout_eof"]:
                remaining = self._remaining_v1()
                if remaining <= 0:
                    break
                io["condition"].wait(min(0.05, remaining))
            _native_require(not self._reasons and not io["reasons"] and len(io["frames"]) > ordinal,
                            "LP03_NATIVE_WORKER_FRAME_UNAVAILABLE")
            frame = io["frames"][ordinal]
            if self.original[1].payload.component_closure == ("MATH-01", "MATH-02") and frame["kind"] in ("FAILED","COMPUTATION_RESULT"):
                _WindowsEvidenceProcessV1._require_probability_edge_frame_v1(self, frame)
            if frame["kind"] == "FAILED" and "state" not in frame["payload"]["measurement_or_absence"]:
                _WindowsEvidenceProcessV1._require_invocation_measurement_v1(
                    self, frame["payload"]["measurement_or_absence"], positive=False)
            _native_require(frame["kind"] == kind, "LP03_WORKER_CAUSAL_FRAME_ORDER")
            return frame["payload"]

    def _exchange_evidence_timeline_v1(self, scope, send, contract):
        """Broker only the original registered callbacks and admitted source slices."""
        from ..agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        from ..agents.pr169_agent_orch1_resolvers import _BoundEvidenceCallbackV1
        from ..stage1_prediction_markets.qku_computation_control_plane import evidence_execution as worker
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.implementation_registry import LP03_DECIMAL_CONTEXT_POLICY_REF_V1
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
            EvidenceInvocationInputsV1, FormulaInputResolverV1, _evidence_original_timeline_inputs_v1,
        )
        from ..stage1_prediction_markets.qku_computation_control_plane.models import _evidence_normalized_event_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import (
            deterministic_json, _evidence_canonical_object_v1, _evidence_frozen_data_v1,
        )

        supervisor, attempt = self.original[:2]
        grant, operation = attempt.payload, attempt.registration
        limits = grant.budgets
        profile = worker._CAUSAL_TIMELINE_WORKER_PROFILE_V1
        ordinal = 1

        def receive(kind):
            nonlocal ordinal
            payload = _WindowsEvidenceProcessV1._receive_v1(self, ordinal, kind)
            if kind == "SEGMENT":
                frame = self._io["frames"][ordinal]
                _native_require(4 + len(deterministic_json(frame).encode("utf-8")) <= limits.segment_max_bytes,
                                "LP03_TIMELINE_OUTPUT_SEGMENT_BYTE_LIMIT")
            ordinal += 1
            return payload

        def send_causal(kind, **payload):
            return send(kind, dict(profile=profile, **payload))

        def same(actual, expected, reason):
            _native_require(deterministic_json(actual) == deterministic_json(expected), reason)

        refs = tuple(dict.fromkeys(pin.source_record_ref for pin in scope.event_pins))
        same(receive("READ_REQUEST"), dict(profile=profile, record_refs=refs, event_ordinal_or_none=None,
            role_or_none=None, scenario_values=()), "LP03_TIMELINE_INITIAL_READ_ROSTER")
        packet = FormulaInputResolverV1.resolve_evidence_v1(contract.math_id, attempt_grant=attempt.handle,
            invocation_ordinal=0, requester_context=supervisor)
        inputs = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
        events = _evidence_original_timeline_inputs_v1(scope, packet._source_slices)
        callback_regs = _EvidenceIssuerStateV1._require_original_callbacks_v1(operation.issuer,
            operation.envelope_entry, scope.callbacks)
        buffer = worker._EvidenceTimelineBufferV1(limits=limits, origin=scope.scenario_plan.origin, allowed_refs=refs)
        domain = worker._EvidenceTimelineLaneStateV1(grant, scope)
        for index, event in enumerate(events):
            final = index == len(events) - 1
            size = send_causal("INPUT_SEGMENT", segment_ordinal=index, final_segment=final, events=(event,))
            buffer.admit_segment_v1(segment_ordinal=index, events=(event,), final=final, original_wire_bytes=size)
        component_refs = tuple(pin.source_record_ref for pin in scope.component_input_pins)
        state_ref = grant.grant_ref
        draws = {}
        segments = []
        durable_events = []
        result = None
        for decision, instant in enumerate(scope.decision_wall_ns):
            send_causal("CONTINUE", command="STEP", decision_ordinal=decision, decision_wall_ns=instant)
            available = buffer.available_v1(decision_wall_ns=instant)
            source_refs = buffer.available_refs_v1(instant) | frozenset(pin.source_record_ref
                for pin in scope.component_input_pins if pin.availability_wall_ns <= instant)
            for event in available:
                domain.begin_v1(event, decision_wall_ns=instant)
                outcomes = []
                for pin, registration in zip(scope.callbacks, callback_regs, strict=True):
                    requested = receive("READ_REQUEST")
                    values = requested.get("scenario_values", ())
                    coordinates = tuple(row for row in scope.coordinates if row[4] == event.local_ordinal
                                        and row[7] in (0, pin.namespace_ordinal))
                    same(requested, dict(profile=profile, event_ordinal_or_none=event.local_ordinal,
                        role_or_none=pin.role.value, record_refs=(event.source_record_ref,), scenario_values=values),
                        "LP03_TIMELINE_CALLBACK_READ_JOIN")
                    _native_require(tuple(worker._evidence_timeline_coordinate_receipt_v1(row) for row in values)
                                    == coordinates, "LP03_TIMELINE_ORIGINAL_SCENARIO_ROSTER")
                    with EvidenceProcessSupervisorV1._operation_v1(supervisor, attempt) as current:
                        _EvidenceRegistrationOperationV1._check_current_v1(current)
                        _native_require(self._callbacks_dispatched < limits.max_callbacks, "LP03_TIMELINE_CALLBACK_LIMIT")
                        if pin is scope.callbacks[0]:
                            _native_require(self._events_dispatched < limits.max_events, "LP03_TIMELINE_EVENT_LIMIT")
                            self._events_dispatched += 1
                        for coordinate, receipt in zip(coordinates, values, strict=True):
                            _native_require(coordinate not in draws or draws[coordinate] == receipt,
                                            "LP03_TIMELINE_COORDINATE_REUSE_CHANGED")
                            draws[coordinate] = receipt
                        _native_require(len(draws) <= limits.max_coordinates, "LP03_TIMELINE_COORDINATE_LIMIT")
                        self._coordinates_observed = len(draws)
                        EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
                        lane_state = _evidence_frozen_data_v1(dict(lane=grant.lane.value, attempt_ref=grant.grant_ref,
                            state_ref=state_ref, domain=domain.view_v1()))
                        visible = dict(event=event.payload, decision_wall_ns=instant,
                            original_owner_envelope_ref=grant.original_owner_envelope_ref,
                            selected_component_id=contract.math_id, available_component_input_refs=tuple(
                                dict(store_id=ref.store_id, record_id=ref.record_id) for ref in component_refs if ref in source_refs))
                        if all(ref in source_refs for ref in component_refs):
                            visible["component_inputs"] = _evidence_canonical_object_v1(
                                deterministic_json(inputs.authoritative_values).encode("utf-8"))
                        self._callbacks_dispatched += 1
                        outcome = _BoundEvidenceCallbackV1.on_event_v1(registration, event,
                            _evidence_frozen_data_v1(visible), lane_state, values)
                        _EvidenceRegistrationOperationV1._check_current_v1(current)
                    worker._require_evidence_timeline_outcome_v1(outcome, grant=grant, event=event, pin=pin,
                        source_refs=source_refs, final_event=self._events_dispatched == len(events))
                    _native_require(outcome.next_lane_state_ref != state_ref, "LP03_TIMELINE_REUSED_LANE_STATE")
                    send_causal("CONTINUE", command="APPLY_CALLBACK_RESULT", event_ordinal=event.local_ordinal,
                                role=pin.role.value, outcome=outcome)
                    outcomes.append(outcome)
                    if outcome.disposition == "REJECTED":
                        failed = receive("FAILED")
                        _native_require(failed.get("profile") == profile and failed["event_ordinal_or_none"] == event.local_ordinal
                                        and failed["callbacks_started"] == self._callbacks_dispatched
                                        and failed["coordinates_sampled"] == len(draws)
                                        and deterministic_json(failed["outcomes"]) == deterministic_json(tuple(outcomes)),
                                        "LP03_TIMELINE_ORIGINAL_REJECTED_PREFIX")
                        raise ContractValidationError(ReasonCode.EVIDENCE_INPUT_UNAVAILABLE,
                            "LP03_TIMELINE_CALLBACK_REJECTED: " + ", ".join(outcome.reasons))
                    domain.apply_v1(event, outcome, decision_wall_ns=instant)
                    for index, request in enumerate(outcome.component_requests):
                        domain.require_component_v1(event)
                        _native_require(result is None and request.math_id == contract.math_id
                                        and request.original_input_refs == component_refs,
                                        "LP03_TIMELINE_UNADMITTED_COMPONENT_INVOCATION")
                        with EvidenceProcessSupervisorV1._operation_v1(supervisor, attempt) as current:
                            _EvidenceRegistrationOperationV1._check_current_v1(current)
                            _native_require(self._computations_dispatched < limits.max_computations,
                                            "LP03_TIMELINE_COMPUTATION_LIMIT")
                            self._computations_dispatched += 1
                        send_causal("CONTINUE", command="INVOKE_COMPONENT", event_ordinal=event.local_ordinal,
                            request_ordinal=index, request=request, inputs=inputs.authoritative_values)
                        result = receive("COMPUTATION_RESULT")
                        same(result["invocation_contract"], contract, "LP03_TIMELINE_ORIGINAL_COMPUTATION_CONTRACT")
                        same(result["original_record_refs"], component_refs, "LP03_TIMELINE_ORIGINAL_COMPUTATION_READS")
                        _native_require(result["event_ordinal"] == event.local_ordinal
                                        and result["numeric_context_policy_ref"] == LP03_DECIMAL_CONTEXT_POLICY_REF_V1,
                                        "LP03_TIMELINE_ORIGINAL_COMPUTATION_RESULT")
                        _WindowsEvidenceProcessV1._require_invocation_measurement_v1(self,
                            result["invocation_measurement"], positive=True)
                    state_ref = outcome.next_lane_state_ref
                segment = receive("SEGMENT")
                same(segment, dict(profile=profile, segment_ordinal=len(segments), decision_ordinal=decision,
                    event_ids=(event.event_id,), outcomes=tuple(outcomes), lane_state_ref=state_ref,
                    callbacks_started=self._callbacks_dispatched, coordinates_sampled=len(draws), domain_state=domain.view_v1()),
                    "LP03_TIMELINE_ORIGINAL_SEGMENT_JOIN")
                durable_events.append(dict(profile=profile, dispatch_ordinal=len(durable_events), event=event,
                    decision_ordinal=decision, decision_wall_ns=instant, outcomes=tuple(outcomes),
                    component_event_or_none=None, domain_state=segment["domain_state"],
                    scenario_values=tuple(draws[row] for row in scope.coordinates if row[4] == event.local_ordinal)))
                segments.append(segment)
        _native_require(result is not None and len(segments) == len(events), "LP03_TIMELINE_ORIGINAL_COMPLETION_REQUIRED")
        send_causal("CONTINUE", command="FINISH", decision_count=len(scope.decision_wall_ns))
        self._pipe_original[0][1].close()
        complete = receive("COMPLETE")
        same(complete, dict(profile=profile, events=len(events), segments=len(segments),
            callbacks_started=self._callbacks_dispatched, coordinates_sampled=len(draws),
            computations=self._computations_dispatched, lane_state_ref=state_ref), "LP03_TIMELINE_ORIGINAL_COMPLETE_JOIN")
        formula_source = component_refs[0]
        sources = tuple(row for part in packet._source_slices for row in part.reconstructed_canonical_events
                        if row["record_ref"] == formula_source.record_id)
        _native_require(len(sources) == 1, "LP03_TIMELINE_ORIGINAL_FORMULA_EVENT")
        source = sources[0]
        normalized = _evidence_normalized_event_v1(dict(event_id="LP03-EVENT::" + source["record_ref"],
            kind="SYNTHETIC_BOOK_SNAPSHOT", origin=scope.scenario_plan.origin.value,
            source_record_ref=dict(store_id=formula_source.store_id, record_id=formula_source.record_id),
            availability_wall_ns=source["native_clocks"]["available_time"], effective_wall_ns=source["native_clocks"]["effective_time"],
            provider_order_or_absence=source["provider_sequence"], source_revision=source["revision"],
            connection_epoch=source["source_epoch_id"], local_ordinal=0, payload=source["values"]))
        original_dispatch = next(row for row in durable_events if row["event"].local_ordinal == result["event_ordinal"])
        original_dispatch["component_event_or_none"] = normalized
        records = _evidence_canonical_object_v1(deterministic_json(dict(events=tuple(durable_events))).encode("utf-8"),
            max_bytes=min(1048576, limits.max_output_bytes))
        self._exchange_original = (packet, contract, result, _evidence_frozen_data_v1(records["events"]), complete, normalized)

    def _close_settled_v1(self, terminal):
        """Only original, independently observed terminal custody permits release."""
        with self._control_lock:
            _WindowsEvidenceProcessV1._close_settled_locked_v1(self, terminal)

    def _close_settled_locked_v1(self, terminal):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _native_require(self.phase not in ("TERMINAL_RETAINED_AND_CLOSED", "TERMINAL_RETAINED_CLEANUP_FAILED"),
                        "LP03_NATIVE_RELEASE_ALREADY_ATTEMPTED")
        ctypes, api, kernel, _extended, _accounting, job, process, thread, _pid, _identity = self._settlement_custody_v1()
        _native_require(terminal is self._terminal_original and terminal is not None
                        and terminal[0]["exit_code"] is not None and terminal[0]["active_processes"] == 0
                        and terminal[1] is True and terminal[2] is True
                        and self._io is not None and all(not thread.is_alive() for thread in self._io["threads"]),
                        "LP03_NATIVE_RELEASE_REQUIRES_ORIGINAL_TERMINAL_PROOF")
        for name, stream, _fd, _handle in self._pipe_original:
            if stream is not None:
                try:
                    stream.close()
                except BaseException as exc:
                    EvidenceProcessSupervisorV1._record_failure_cleanup_v1(self.supervisor, self, exc, stage="CLOSE_" + name.upper())
        remaining_native = dict(thread=thread, process=process, job=job)
        for name, handle in tuple(remaining_native.items()):
            if handle is not None:
                try:
                    api.CloseHandle(handle)
                    setattr(self, name, None)
                    remaining_native[name] = None
                except BaseException as exc:
                    EvidenceProcessSupervisorV1._record_failure_cleanup_v1(self.supervisor, self, exc, stage="CLOSE_" + name.upper())
        remaining = []
        for handle in self._diagnostic_handles:
            try:
                if not kernel.CloseHandle(handle):
                    raise ctypes.WinError(ctypes.get_last_error())
                self._diagnostic_handles = tuple(value for value in self._diagnostic_handles if value != handle)
            except BaseException as exc:
                EvidenceProcessSupervisorV1._record_failure_cleanup_v1(self.supervisor, self, exc, stage="CLOSE_JOB_MEMBER_OBSERVATION")
        image_original = self._image_original
        if tuple(self._image_objects) != image_original:
            self.cleanup_errors.append(("IMAGE_CUSTODY_MIRROR_CHANGED",))
        for item in reversed(image_original):
            try:
                if not kernel.CloseHandle(item[0]):
                    raise ctypes.WinError(ctypes.get_last_error())
            except BaseException as exc:
                EvidenceProcessSupervisorV1._record_failure_cleanup_v1(self.supervisor, self, exc, stage="CLOSE_IMAGE_OBJECT")
                remaining.append(item)
        self._image_objects = list(reversed(remaining))
        self._native_custody = (remaining_native["job"], remaining_native["process"], remaining_native["thread"], _pid, _identity)
        self.phase = ("TERMINAL_RETAINED_CLEANUP_FAILED" if self.cleanup_errors or self._failed_trigger_capture is not None
                      else "TERMINAL_RETAINED_AND_CLOSED")
        self.supervisor._cleanup_originals = (*self.supervisor._cleanup_originals,
            (self, self.original, terminal, tuple(self.cleanup_errors), self._native_custody, self.phase))
        if self.cleanup_errors:
            self.supervisor._unresolved = True

    def _settle_no_child_v1(self):
        """No-child proof is a native-return/never-entered fact, never an exception."""
        from ctypes import wintypes
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        information = self._process_information_original
        creation = tuple(entry for entry in self.supervisor._creation_originals if entry[0] is self)
        stages = tuple(entry[1] for entry in creation)
        _native_require(stages in (("NOT_ENTERED",), ("NOT_ENTERED", "OUTPUT_ALLOCATED"),
                            ("NOT_ENTERED", "OUTPUT_ALLOCATED", "ENTERED", "RETURNED_FAILURE"))
                        and creation[0][2:] == (None, None)
                        and all(entry[2] is information for entry in creation[1:])
                        and (stages[-1] != "RETURNED_FAILURE" or creation[-1][3] is False)
                        and self._native_custody[1] is None
                        and (information is None or not any((information.hProcess, information.hThread,
                                                            information.dwProcessId, information.dwThreadId))),
                        "LP03_NATIVE_NO_CHILD_UNPROVEN")
        controller_history = tuple(entry for entry in self.supervisor._controller_originals if entry[0] is self)
        if self._controller is None:
            _native_require(len(controller_history) == 1 and controller_history[0][1:] == ("NOT_CREATED", None)
                            and stages == ("NOT_ENTERED",) and self._api_original is None
                            and self._native_custody == (None, None, None, None, None)
                            and not self._image_owned and not self._partial_pipe_original,
                            "LP03_NATIVE_CONTROLLER_NEVER_CREATED_UNPROVEN")
        else:
            _native_require(tuple(entry[1] for entry in controller_history) in
                            (("NOT_CREATED", "ALLOCATED", "START_ENTERED"),
                             ("NOT_CREATED", "ALLOCATED", "START_ENTERED", "START_RETURNED"))
                            and controller_history[0][2] is None
                            and all(entry[2] is self._controller for entry in controller_history[1:]),
                            "LP03_NATIVE_CONTROLLER_CREATION_UNPROVEN")
            self._controller_done.set()
            self._controller.join(self._settlement_remaining_v1())
            _native_require(not self._controller.is_alive(), "LP03_NATIVE_CONTROLLER_UNJOINED")
        job = self._native_custody[0]
        accounting = None
        if job is not None:
            accounting, returned = self.accounting_type(), wintypes.DWORD()
            _native_require(self.kernel.QueryInformationJobObject(job, 1, self.ctypes.byref(accounting),
                self.ctypes.sizeof(accounting), self.ctypes.byref(returned))
                and returned.value == self.ctypes.sizeof(accounting)
                and accounting.TotalProcesses == accounting.ActiveProcesses == 0, "LP03_NATIVE_NO_CHILD_JOB_UNPROVEN")
        self._no_child_original = (self.phase, information, job, 0 if accounting is None else accounting.TotalProcesses)
        self.supervisor._no_child_originals = (*self.supervisor._no_child_originals,
            (self, self.original, self._no_child_original, information, self._controller, self._api_original, creation, controller_history))
        for name, stream in self._partial_pipe_original:
            try:
                stream.close()
            except BaseException as exc:
                self.cleanup_errors.append(("NO_CHILD_CLOSE_" + name.upper(), type(exc).__name__))
        for handle, _path, _directory in tuple(reversed(self._image_owned)):
            try:
                if not self.kernel.CloseHandle(handle):
                    raise self.ctypes.WinError(self.ctypes.get_last_error())
                self._image_objects = [item for item in self._image_objects if item[0] != handle]
            except BaseException as exc:
                self.cleanup_errors.append(("NO_CHILD_CLOSE_IMAGE", type(exc).__name__))
        if job is not None:
            try:
                self.api.CloseHandle(job)
                self.job = None
                self._native_custody = (None, None, None, None, None)
            except BaseException as exc:
                self.cleanup_errors.append(("NO_CHILD_CLOSE_JOB", type(exc).__name__))
        self.phase = "FAILED_TO_START_NO_CHILD" if not self.cleanup_errors else "NO_CHILD_CLEANUP_UNRESOLVED"
        self.supervisor._cleanup_originals = (*self.supervisor._cleanup_originals,
            (self, self.original, self._no_child_original, tuple(self.cleanup_errors), self._native_custody, self.phase))
        if self.cleanup_errors:
            self.supervisor._unresolved = True


class EvidenceProcessSupervisorV1:
    """Original SVC-owned process custody; serialized binding names grant nothing."""

    __slots__ = ("_service", "_host", "_issuer", "_clock", "_binding_ref", "_instance_ref",
                 "_active", "_unresolved", "_bound_observation", "_retained", "_lane_platforms", "_capture_originals",
                 "_unknown_capture_originals", "_no_child_originals", "_creation_originals",
                 "_cleanup_originals", "_failure_observation_originals", "_controller_originals", "_capacity_originals",
                 "_lane_operation_originals", "_failure_trigger_originals")

    def __init__(self):
        raise TypeError("use the explicit original SVC supervisor binding")

    def __copy__(self):
        raise TypeError("LP03 supervisor custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 supervisor custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 supervisor custody cannot be serialized")

    @property
    def binding_ref(self):
        return self._binding_ref

    @property
    def instance_ref(self):
        return self._instance_ref

    def _assert_original_v1(self):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(not self._unresolved, "LP03_SUPERVISOR_NOT_ORIGINAL_OR_UNRESOLVED")

    def _assert_custody_v1(self):
        """Original ownership remains inspectable when positive use is quarantined."""
        from ..agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1, _EvidenceIssuerStateV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _native_require(type(self) is EvidenceProcessSupervisorV1 and type(self._service) is DashboardReadModelService
                        and type(self._issuer) is _EvidenceIssuerStateV1 and self._issuer.supervisor is self
                        and getattr(self._service, "_evidence_supervisor_v1", None) is self
                        and self._clock is self._issuer.clock,
                        "LP03_SUPERVISOR_NOT_ORIGINAL_OR_UNRESOLVED")
        lifecycle = _EvidenceIssuerStateV1._require_lifecycle_original_v1(self._issuer)
        _native_require(self._instance_ref == lifecycle[0][4], "LP03_SUPERVISOR_LIFECYCLE_INSTANCE_CHANGED")
        original = self._issuer.supervisor_original
        _native_require(type(original) is tuple and len(original) == 7
                        and self is original[0] and self._service is original[1] and self._host is original[2]
                        and self._clock is original[3] and self._binding_ref == original[4]
                        and self._instance_ref == original[5] and self._bound_observation is original[6],
                        "LP03_SUPERVISOR_ORIGINAL_BINDING_CHANGED")
        EvidenceHostBindingV1._assert_local_binding_v1(self._host)

    def _operation_v1(self, attempt):
        from contextlib import contextmanager, ExitStack
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1
        @contextmanager
        def entered():
            issuer, operation = self._issuer, attempt.registration
            with issuer.lock, ExitStack() as locks:
                _native_require(issuer.operation is None and operation.active_attempt is None
                                and attempt.supervisor is self, "LP03_SUPERVISOR_OPERATION_REENTRY")
                issuer.operation, operation.active_attempt = operation, attempt
                try:
                    issuer._lock_original_source_custodies_v1(locks)
                    _EvidenceRegistrationOperationV1._check_current_v1(operation)
                    yield operation
                finally:
                    operation.active_attempt, issuer.operation = None, None
        return entered()

    def _execution_usage_v1(self, operation, *, selected_attempt=None, refresh=False):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        values = dict(cpu_ns=0, process_memory_high_water_bytes=0, job_memory_high_water_bytes=0,
                      events=0, computations=0, callbacks=0, coordinates=0, output_bytes=0, active_workers=0)
        _native_require(operation.issuer is self._issuer, "LP03_NATIVE_ACCOUNT_ORIGINAL_REGISTRATION")
        for native in self._retained:
            attempt = native.original[1]
            if attempt.registration is not operation or (selected_attempt is not None and attempt is not selected_attempt):
                continue
            _native_require(native.original[0] is self and operation.attempts.get(
                (attempt.request.lane, attempt.request.attempt_ordinal)) is attempt, "LP03_NATIVE_ACCOUNT_CUSTODY")
            terminal = native._terminal_original
            if terminal is not None:
                observed, output_bytes = terminal[0], terminal[6]
            elif native._native_custody[1] is not None:
                if refresh:
                    observed = _WindowsEvidenceProcessV1.observe_v1(native)
                    with native._control_lock:
                        native._last_native = observed
                else:
                    observed = native._last_native
                output_bytes = 0 if native._io is None else native._io["output_bytes"]
            else:
                observed, output_bytes = None, 0
            if observed is not None:
                values["cpu_ns"] += observed["cpu_ns"]
                values["active_workers"] += observed["active_processes"]
                for name in ("process_memory_high_water_bytes", "job_memory_high_water_bytes"):
                    values[name] = max(values[name], observed[name])
            values["output_bytes"] += output_bytes
            values["events"] += native._events_dispatched
            values["computations"] += native._computations_dispatched
            values["callbacks"] += native._callbacks_dispatched
            values["coordinates"] += native._coordinates_observed
        return values

    def _require_no_child_v1(self, native):
        """Original no-child facts, independent of mutable phase or PID text."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(type(native) is _WindowsEvidenceProcessV1 and any(item is native for item in self._retained)
                        and native.original[0] is self, "LP03_NO_CHILD_ORIGINAL_NATIVE_REQUIRED")
        witnesses = tuple(entry for entry in self._no_child_originals if entry[0] is native)
        _native_require(len(witnesses) == 1, "LP03_NO_CHILD_ORIGINAL_WITNESS_REQUIRED")
        original = witnesses[0]
        creation = tuple(entry for entry in self._creation_originals if entry[0] is native)
        controller = tuple(entry for entry in self._controller_originals if entry[0] is native)
        _native_require(native.original is original[1] and native._no_child_original is original[2]
                        and native._process_information_original is original[3]
                        and native._controller is original[4] and native._api_original is original[5]
                        and len(creation) == len(original[6])
                        and all(actual is retained for actual, retained in zip(creation, original[6]))
                        and len(controller) == len(original[7])
                        and all(actual is retained for actual, retained in zip(controller, original[7]))
                        and ((original[4] is None and len(controller) == 1 and controller[0][1:] == ("NOT_CREATED", None))
                             or (original[4] is not None and not original[4].is_alive()))
                        and original[2][1] is original[3] and original[2][3] == 0,
                        "LP03_NO_CHILD_ORIGINAL_WITNESS_CHANGED")
        information = original[3]
        _native_require(native._native_custody[1] is None
                        and (information is None or not any((information.hProcess, information.hThread,
                                                            information.dwProcessId, information.dwThreadId))),
                        "LP03_NO_CHILD_NATIVE_OUTPUT_CHANGED")
        return original

    def _require_original_capture_v1(self, native):
        """Read-only original stream custody, independent of decoded frame data."""
        from types import MappingProxyType
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(type(native) is _WindowsEvidenceProcessV1 and any(value is native for value in self._retained)
                        and native.original[0] is self,
                        "LP03_CAPTURE_ORIGINAL_NATIVE_REQUIRED")
        matches = tuple(entry for entry in self._capture_originals if entry[0] is native)
        _native_require(len(matches) == 1, "LP03_CAPTURE_ORIGINAL_WITNESS_REQUIRED")
        original = matches[0]
        _native_require(native.original is original[3] and native.original[1].payload is original[4]
                        and native._terminal_original is original[1] and original[1][9] is original[2]
                        and type(original[2]) is MappingProxyType and original[1][1:3] == (True, True)
                        and original[1][0]["exit_code"] is not None and original[1][0]["active_processes"] == 0,
                        "LP03_CAPTURE_ORIGINAL_WITNESS_CHANGED")
        return original

    def _snapshot_unknown_capture_v1(self, native):
        """Freeze original drain buffers only; this cannot prove process exit."""
        from types import MappingProxyType
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceAttemptFailureAuditV1
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(type(native) is _WindowsEvidenceProcessV1 and any(item is native for item in self._retained)
                        and native.original[0] is self and native.phase == "TERMINATION_UNKNOWN"
                        and not any(item[0] is native for item in self._unknown_capture_originals),
                        "LP03_UNKNOWN_CAPTURE_ORIGINAL_REQUIRED")
        attempt, drain = native.original[1], native._drain_original
        audit = attempt.failure_audit
        _native_require(drain is not None and native._io is drain[0] and attempt.failure_bounds is attempt.original[9],
                        "LP03_UNKNOWN_CAPTURE_DRAIN_UNAVAILABLE")
        _native_require(type(audit) is _EvidenceAttemptFailureAuditV1 and audit.attempt is attempt,
                        "LP03_UNKNOWN_CAPTURE_ORIGINAL_AUDIT_REQUIRED")
        _EvidenceAttemptFailureAuditV1._check_current_v1(audit)
        before = _EvidenceLocalClockV1.observe_v1(self._clock)
        remaining = (min(attempt.failure_bounds[2], audit.started[1] + attempt.limits.reserved_failure_wall_ns) - before[1]) / 1_000_000_000
        _native_require(remaining > 0 and drain[1].acquire(timeout=remaining), "LP03_UNKNOWN_CAPTURE_LOCK_UNAVAILABLE")
        try:
            io = native._io
            _native_require(native._drain_original is drain and io is drain[0] and io["condition"] is drain[1]
                            and io["threads"] is drain[2] and type(io["stdout_bytes"]) is bytearray
                            and type(io["diagnostics"]) is bytearray
                            and len(io["stdout_bytes"]) + len(io["diagnostics"]) <= native.original[3].max_output_bytes,
                            "LP03_UNKNOWN_CAPTURE_DRAIN_CHANGED")
            stdout, stderr = bytes(io["stdout_bytes"]), bytes(io["diagnostics"])
            captured = MappingProxyType(dict(stdout=stdout, stderr=stderr,
                stdout_observed_bytes=io["stdout_observed_bytes"], stderr_observed_bytes=io["stderr_observed_bytes"],
                stdout_discarded_bytes=io["stdout_observed_bytes"] - len(stdout),
                stderr_discarded_bytes=io["stderr_observed_bytes"] - len(stderr),
                stdout_eof=io["stdout_eof"], stderr_eof=io["stderr_eof"],
                complete=io["stdout_eof"] and io["stderr_eof"] and len(stdout) + len(stderr) == io["output_bytes"]))
        finally:
            drain[1].release()
        # This interval describes only the buffer snapshot. Native process
        # observations and resource-accounting samples have separate clocks.
        after = _EvidenceLocalClockV1.observe_v1(self._clock)
        snapshot = (native, None, captured, native.original, attempt.payload, (before, after), drain, "TERMINATION_UNKNOWN")
        self._unknown_capture_originals = (*self._unknown_capture_originals, snapshot)
        _native_require(after[1] < attempt.failure_bounds[2], "LP03_UNKNOWN_CAPTURE_AUDIT_DEADLINE")
        _EvidenceAttemptFailureAuditV1._check_current_v1(audit)
        return snapshot

    def _require_capture_snapshot_v1(self, native, snapshot):
        from types import MappingProxyType
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        if snapshot is None:
            return EvidenceProcessSupervisorV1._require_original_capture_v1(self, native)
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(type(snapshot) is tuple and len(snapshot) == 8
                        and any(item is snapshot for item in self._unknown_capture_originals)
                        and type(native) is _WindowsEvidenceProcessV1 and snapshot[0] is native
                        and any(item is native for item in self._retained) and snapshot[1] is None
                        and snapshot[3] is native.original and native.original[0] is self
                        and snapshot[4] is native.original[1].payload and type(snapshot[2]) is MappingProxyType
                        and snapshot[7] == "TERMINATION_UNKNOWN", "LP03_UNKNOWN_CAPTURE_WITNESS_CHANGED")
        return snapshot

    def _capture_plan_v1(self, native, *, maximum_total_bytes=None, maximum_segment_bytes=None, capture_snapshot=None):
        """Plan the complete bounded manifest before allocating base64 data."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_ident, _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import (
            deterministic_json, _encode_evidence_projection_json_v1, _evidence_process_capture_metadata_v1)
        original = EvidenceProcessSupervisorV1._require_capture_snapshot_v1(self, native, capture_snapshot)
        capture, attempt = original[2], native.original[1]
        grant = attempt.payload
        _native_require(grant is attempt.record_original[0] and attempt.grant_record is native.original[2]
                        and grant.budgets is native.original[3] and 0 < grant.budgets.max_output_bytes <= 1048576,
                        "LP03_CAPTURE_ORIGINAL_GRANT_REQUIRED")
        limit = min(grant.budgets.segment_max_bytes, grant.budgets.frame_byte_limit)
        byte_limit = grant.budgets.max_persistent_bytes
        if maximum_segment_bytes is not None:
            _native_require(type(maximum_segment_bytes) is int and 0 < maximum_segment_bytes <= limit,
                            "LP03_CAPTURE_SEGMENT_NARROWING")
            limit = maximum_segment_bytes
        if maximum_total_bytes is not None:
            _native_require(type(maximum_total_bytes) is int and 0 <= maximum_total_bytes <= byte_limit,
                            "LP03_CAPTURE_BYTE_NARROWING")
            byte_limit = maximum_total_bytes
        _native_require(0 < limit <= 65536, "LP03_CAPTURE_SEGMENT_BUDGET")
        observation_ref = grant.grant_ref + "::PROCESS:FAILURE"
        _native_ident(observation_ref)
        maximum_counter = 2**63 - 1

        def body(stream, ordinal, count, first, size, encoded):
            value = capture[stream.lower()]
            result = _evidence_process_capture_metadata_v1(grant_ref=grant.grant_ref, fence_ref=grant.fence_ref,
                supervisor_instance_ref=self.instance_ref, stream=stream, ordinal=ordinal, count=count, first=first,
                size=size, captured=len(value), observed=capture[stream.lower() + "_observed_bytes"],
                discarded=capture[stream.lower() + "_discarded_bytes"], eof=capture[stream.lower() + "_eof"],
                complete=capture["complete"])
            result["data_base64"] = encoded
            return result

        # Bound every header with the largest admitted counter representation;
        # base64 length is then known before slicing or allocating its output.
        template = body("STDOUT", maximum_counter, maximum_counter, maximum_counter, maximum_counter, "")
        template["stream_captured_byte_count"] = template["stream_observed_byte_count"] = maximum_counter
        template["stream_discarded_byte_count"] = maximum_counter
        template["capture_complete"] = template["stream_eof"] = False
        header_size = len(deterministic_json(template).encode("utf-8"))
        maximum_chunk = ((limit - header_size) // 4) * 3
        _native_require(maximum_chunk > 0, "LP03_CAPTURE_SEGMENT_HEADER_EXHAUSTS_BUDGET")
        counts = tuple((len(capture[stream.lower()]) + maximum_chunk - 1) // maximum_chunk
                       for stream in ("STDOUT", "STDERR"))
        total = sum(counts)
        _native_require(total <= grant.budgets.max_persistent_operations, "LP03_CAPTURE_SEGMENT_ROSTER_BUDGET")
        # Bound the complete reference list before allocating any roster or
        # base64 payload. The enclosing observation and duplicate SQL columns
        # still need a separate exact audit-owner preflight.
        manifest_bound = 2 + max(0, total - 1)
        for stream, count in zip(("STDOUT", "STDERR"), counts, strict=True):
            if count:
                last_ref = observation_ref + "::CAPTURE:" + stream + ":" + str(count - 1)
                _native_ident(last_ref)
                manifest_bound += count * len(deterministic_json(last_ref).encode("utf-8"))
        _native_require(manifest_bound <= 16384, "LP03_CAPTURE_MANIFEST_BYTES")
        plan, total_bytes = [], 0
        for stream in ("STDOUT", "STDERR"):
            value = capture[stream.lower()]
            count = (len(value) + maximum_chunk - 1) // maximum_chunk
            for ordinal in range(count):
                first = ordinal * maximum_chunk
                size = min(maximum_chunk, len(value) - first)
                _native_require(4 * ((size + 2) // 3) + header_size <= limit, "LP03_CAPTURE_ENCODING_PREFLIGHT")
                segment = body(stream, ordinal, count, first, size, "")
                encoded_size = len(deterministic_json(segment).encode("utf-8")) + 4 * ((size + 2) // 3)
                total_bytes += encoded_size
                _native_require(total_bytes <= byte_limit, "LP03_CAPTURE_BODY_BYTES_BUDGET")
                plan.append((stream, first, size, segment, encoded_size))
        refs = {stream: [] for stream in ("STDOUT", "STDERR")}
        for stream, _first, _size, segment, _encoded_size in plan:
            refs[stream].append(segment["capture_segment_ref"])
        manifest = dict(schema_version="1.0", operation="SVC_PROCESS_CAPTURE_MANIFEST_V1",
            observation_ref=grant.grant_ref + "::PROCESS:FAILURE", grant_ref=grant.grant_ref,
            fence_ref=grant.fence_ref, supervisor_instance_ref=self.instance_ref, capture_complete=capture["complete"],
            streams=tuple(dict(stream=stream, observed_byte_count=capture[stream.lower() + "_observed_bytes"],
                captured_byte_count=len(capture[stream.lower()]), discarded_byte_count=capture[stream.lower() + "_discarded_bytes"],
                eof=capture[stream.lower() + "_eof"], segment_refs=refs[stream]) for stream in ("STDOUT", "STDERR")))
        # The existing native-data encoder bounds each token and accumulated
        # output before allocation, including the complete manifest overhead.
        raw = _encode_evidence_projection_json_v1(manifest, maximum_bytes=16384, maximum_nodes=4096)
        _native_require(len(raw) + total_bytes <= byte_limit, "LP03_CAPTURE_MANIFEST_TOTAL_BYTES")
        _native_require(EvidenceProcessSupervisorV1._require_capture_snapshot_v1(self, native, capture_snapshot) is original,
                        "LP03_CAPTURE_ORIGINAL_WITNESS_CHANGED")
        return original, limit, byte_limit, tuple(plan), raw

    def _capture_segment_bodies_v1(self, native):
        """Original opaque bytes only; includes the full manifest preflight."""
        return EvidenceProcessSupervisorV1._capture_manifest_v1(self, native)[1]

    def _capture_manifest_v1(self, native, *, maximum_total_bytes=None, maximum_segment_bytes=None, capture_snapshot=None):
        """Original terminal data; optional limits only narrow signed budgets.

        A failure operation must still reserve and charge the enclosing
        observation, every SQL column copy, and the actual processing work.
        """
        import base64
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import (
            deterministic_json, _evidence_process_capture_manifest_v1)
        original, limit, byte_limit, plan, raw = EvidenceProcessSupervisorV1._capture_plan_v1(self, native,
            maximum_total_bytes=maximum_total_bytes, maximum_segment_bytes=maximum_segment_bytes, capture_snapshot=capture_snapshot)
        capture, grant, bodies = original[2], original[4], []
        for stream, first, size, segment, encoded_size in plan:
            segment["data_base64"] = base64.b64encode(capture[stream.lower()][first:first + size]).decode("ascii")
            encoded = deterministic_json(segment).encode("utf-8")
            _native_require(len(encoded) == encoded_size, "LP03_CAPTURE_ENCODING_SIZE_CHANGED")
            bodies.append(encoded)
        bodies = tuple(bodies)
        _decoded, binary = _evidence_process_capture_manifest_v1(raw, segment_bodies=bodies,
            maximum_capture_bytes=grant.budgets.max_output_bytes, maximum_segment_bytes=limit,
            maximum_segments=grant.budgets.max_persistent_operations, maximum_total_bytes=byte_limit)
        _native_require(binary == (capture["stdout"], capture["stderr"])
                        and EvidenceProcessSupervisorV1._require_capture_snapshot_v1(self, native, capture_snapshot) is original,
                        "LP03_CAPTURE_MANIFEST_ORIGINAL_CHANGED")
        return raw, bodies

    def _capture_failure_trigger_v1(self, audit):
        """Observe one original root; unretained chains remain incomplete."""
        from types import TracebackType, FrameType, CodeType
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError, ContractValidationError, ReasonCode
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        root = audit.trigger_original
        before = _EvidenceLocalClockV1.observe_v1(self._clock)
        error, args, traceback = root[3:6]
        cls, names, original_code, control_plane_error, original_native, os_error, ancestry_available = root[9]
        supported = any(cls is kind for kind in (RuntimeError, ValueError, TypeError, AssertionError, MemoryError,
            EOFError, KeyboardInterrupt, SystemExit, OSError, FileNotFoundError, PermissionError, TimeoutError,
            InterruptedError, BrokenPipeError, ConnectionError, ConnectionAbortedError, ConnectionRefusedError,
            ConnectionResetError, NotADirectoryError, IsADirectoryError, ProcessLookupError, ChildProcessError,
            ComputationControlPlaneError, ContractValidationError))
        reason = dict(state="ABSENT_WITH_REASON", reason="NOT_CONTROL_PLANE_ERROR")
        if control_plane_error or not ancestry_available:
            reason = original_code.value if type(original_code) is ReasonCode else dict(state="ABSENT_WITH_REASON", reason="REASON_CODE_UNREPRESENTABLE")
        native_error = dict(state="ABSENT_WITH_REASON", reason="NOT_OS_ERROR")
        if os_error:
            native_error = original_native
        elif not ancestry_available:
            native_error = dict(state="ABSENT_WITH_REASON", reason="NATIVE_ERROR_UNREPRESENTABLE")
        frames, location_error, remainder = [], None, "NONE"
        try:
            while traceback is not None and len(frames) < 64:
                # These native descriptors may invoke CPython audit hooks.
                # A rejected read is explicit unavailability; a blocked hook
                # is not claimed to be preemptible by this observer.
                frame = TracebackType.tb_frame.__get__(traceback)
                code = FrameType.f_code.__get__(frame)
                frames.append((CodeType.co_filename.__get__(code), CodeType.co_name.__get__(code),
                               TracebackType.tb_lineno.__get__(traceback)))
                traceback = TracebackType.tb_next.__get__(traceback)
            if traceback is not None:
                remainder = "PRESENT_NOT_RETAINED"
        except BaseException as unavailable:
            location_error, remainder = unavailable, "LOCATION_UNAVAILABLE"
        after = _EvidenceLocalClockV1.observe_v1(self._clock)
        snapshot = (root, names, reason, native_error, args[:128], len(args), tuple(frames), remainder,
                    (before, after), location_error, audit.trigger_roster, supported)
        audit.trigger_snapshot = snapshot
        return snapshot

    def _capture_failure_observation_v1(self, audit):
        """Original observations with distinct native, stream and audit times."""
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.lifecycle import evidence_attempt_primary_reason_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceAttemptFailureAuditV1, _EvidenceAttemptOperationV1)
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import (
            _evidence_canonical_object_v1, _encode_evidence_projection_json_v1)
        _native_require(type(audit) is _EvidenceAttemptFailureAuditV1 and audit.attempt.supervisor is self
                        and audit.snapshot is None and audit.phase == "RESERVED", "LP03_FAILURE_SNAPSHOT_ORIGINAL_AUDIT")
        _EvidenceAttemptFailureAuditV1._check_current_v1(audit)
        native, attempt = audit.native, audit.attempt
        _native_require(not any(entry[1] is audit or entry[0] is native for entry in self._failure_observation_originals),
                        "LP03_FAILURE_SNAPSHOT_ALREADY_RETAINED")
        terminal, no_child, capture_snapshot, plan = native._terminal_original, None, None, None
        cleanup = tuple(entry for entry in self._cleanup_originals if entry[0] is native)
        _native_require(len(cleanup) <= 1, "LP03_FAILURE_CLEANUP_WITNESS_ROSTER")
        cleanup = cleanup[0] if cleanup else None
        if cleanup is not None:
            _native_require(cleanup[1] is native.original and cleanup[4] is native._native_custody
                            and cleanup[2] is (terminal if terminal is not None else native._no_child_original),
                            "LP03_FAILURE_CLEANUP_WITNESS_CHANGED")
        cleanup_complete = cleanup is not None and not cleanup[3] and not native.cleanup_errors
        measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_MEASUREMENT_NOT_FROZEN")
        capture_absence = dict(state="ABSENT_WITH_REASON", reason="DRAIN_SNAPSHOT_UNAVAILABLE")
        capture, capture_time = capture_absence, capture_absence
        reasons = [audit.failure_reason]
        if terminal is not None:
            EvidenceProcessSupervisorV1._require_original_capture_v1(self, native)
            _native_require(len(terminal) == 12, "LP03_FAILURE_TERMINAL_TIMES_REQUIRED")
            custody = dict(kind="TERMINAL", native_observation_or_absence=dict(terminal[0]),
                native_observed_between_or_absence=terminal[10], stdout_eof=True, stderr_eof=True,
                controller_joined=True, drains_joined=True, cleanup_complete=cleanup_complete)
            plan = EvidenceProcessSupervisorV1._capture_plan_v1(self, native)
            capture_time = terminal[11]
            measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_MEASUREMENT_UNAVAILABLE")
            if native._exchange_original is not None:
                measurement = native._exchange_original[2]["invocation_measurement"]
            else:
                try:
                    for frame in terminal[4]:
                        if attempt.payload.component_closure == ("MATH-01","MATH-02") and frame["kind"] in ("FAILED","COMPUTATION_RESULT"):
                            _WindowsEvidenceProcessV1._require_probability_edge_frame_v1(native,frame)
                        if frame["kind"] == "FAILED":
                            measurement = frame["payload"]["measurement_or_absence"]
                        elif frame["kind"] == "COMPUTATION_RESULT":
                            measurement = frame["payload"]["invocation_measurement"]
                except ComputationControlPlaneError:
                    measurement = dict(state="ABSENT_WITH_REASON",reason="INVOCATION_MEASUREMENT_UNQUALIFIED")
                    reasons.append("PROTOCOL_INVALIDATED")
            if "state" not in measurement:
                try:
                    _WindowsEvidenceProcessV1._require_invocation_measurement_v1(native, measurement,
                        positive=native._exchange_original is not None)
                except ComputationControlPlaneError:
                    measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_MEASUREMENT_UNQUALIFIED")
                    reasons.append("PROTOCOL_INVALIDATED")
            reasons.extend(terminal[3])
        elif native._no_child_original is not None:
            no_child = EvidenceProcessSupervisorV1._require_no_child_v1(self, native)
            custody = dict(kind="NO_CHILD", creation_stage=no_child[6][-1][1], controller_joined=no_child[4] is not None,
                controller_status="NOT_CREATED" if no_child[4] is None else "JOINED",
                cleanup_complete=cleanup_complete, job_total_processes=no_child[2][3], output_storage_present=no_child[3] is not None)
            capture = capture_time = dict(state="ABSENT_WITH_REASON", reason="NO_CHILD_NO_STREAMS")
            measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_NOT_STARTED")
            if custody["creation_stage"] == "RETURNED_FAILURE" or audit.failure_reason in (
                    "FAILED_TO_START", "SUPERVISION_FAILURE", "INTEGRITY_FAILURE", "ACCOUNTING_FAILURE"):
                reasons.append("FAILED_TO_START")
        else:
            reasons.append("TERMINATION_UNKNOWN")
            native_data = native_time = dict(state="ABSENT_WITH_REASON", reason="NATIVE_OBSERVATION_UNAVAILABLE")
            before = _EvidenceLocalClockV1.observe_v1(self._clock)
            try:
                native_data = _WindowsEvidenceProcessV1.observe_v1(native)
            except (ComputationControlPlaneError, OSError):
                pass
            else:
                native_time = (before, _EvidenceLocalClockV1.observe_v1(self._clock))
            try:
                capture_snapshot = EvidenceProcessSupervisorV1._snapshot_unknown_capture_v1(self, native)
                plan = EvidenceProcessSupervisorV1._capture_plan_v1(self, native, capture_snapshot=capture_snapshot)
                capture_time = capture_snapshot[5]
            except ComputationControlPlaneError:
                # Failure to observe is an explicit absence. The later audit
                # accounting/budget check still has to succeed before writing.
                capture_snapshot = None
            stream_data = None if plan is None else plan[0][2]
            custody = dict(kind="TERMINATION_UNKNOWN", native_observation_or_absence=native_data,
                native_observed_between_or_absence=native_time,
                stdout_eof=False if stream_data is None else stream_data["stdout_eof"],
                stderr_eof=False if stream_data is None else stream_data["stderr_eof"],
                controller_joined=native._controller is not None and not native._controller.is_alive(),
                drains_joined=native._drain_original is not None and all(not item.is_alive() for item in native._drain_original[2]),
                cleanup_complete=False)
        if plan is not None:
            capture = _evidence_canonical_object_v1(plan[4], max_bytes=16384)
        diagnostic_before = _EvidenceLocalClockV1.observe_v1(self._clock)
        def error_prefix(values):
            _native_require(type(values) in (list, tuple) and len(values) < 2**63, "LP03_FAILURE_DIAGNOSTIC_ROSTER_BOUND")
            return len(values), tuple(values[:128])
        controller_count, controller_errors = error_prefix(native._controller_errors)
        cleanup_count, cleanup_errors = error_prefix(native.cleanup_errors)
        drain_count, drain_errors = 0, (() if native._drain_original is None else None)
        if terminal is not None:
            drain_count, drain_errors = error_prefix(terminal[8])
        elif drain_errors is None:
            drain = native._drain_original
            remaining = min(attempt.failure_bounds[2], audit.started[1] + attempt.limits.reserved_failure_wall_ns) - diagnostic_before[1]
            _native_require(remaining > 0 and drain[1].acquire(timeout=remaining / 1_000_000_000),
                            "LP03_FAILURE_DIAGNOSTIC_SNAPSHOT_UNAVAILABLE")
            try:
                _native_require(native._drain_original is drain and native._io is drain[0], "LP03_FAILURE_DIAGNOSTIC_CUSTODY_CHANGED")
                drain_count, drain_errors = error_prefix(drain[0]["errors"])
                reasons.extend(drain[0]["reasons"])
            finally:
                drain[1].release()
        reasons.extend(native._reasons)
        diagnostic_after = _EvidenceLocalClockV1.observe_v1(self._clock)
        if controller_count or drain_count or cleanup_count or not custody["cleanup_complete"]:
            reasons.append("SUPERVISION_FAILURE")
        reasons = tuple(dict.fromkeys("PROTOCOL_INVALIDATED" if reason == "WORKER_PROTOCOL_INVALID" else reason for reason in reasons))
        trigger_snapshot = EvidenceProcessSupervisorV1._capture_failure_trigger_v1(self, audit)
        observed = _EvidenceAttemptFailureAuditV1._check_current_v1(audit)
        if observed[1] >= attempt.deadline.exclusive_deadline_monotonic_ns:
            reasons = tuple(dict.fromkeys((*reasons, "EXPIRED")))
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import _evidence_failure_trigger_header_v1
        trigger = _evidence_failure_trigger_header_v1(trigger_snapshot[5],
            cause_present=audit.trigger_original[6] is not None, context_present=audit.trigger_original[7] is not None,
            suppress_context=audit.trigger_original[8], observed_between=trigger_snapshot[8],
            secondary_error_count=len(audit.trigger_roster) - 1)
        body = dict(schema_version="1.0", operation="SVC_PROCESS_FAILURE_AUDIT_V1",
            observation_ref=attempt.payload.grant_ref + "::PROCESS:FAILURE", grant_ref=attempt.payload.grant_ref,
            fence_ref=attempt.payload.fence_ref, supervisor_instance_ref=self.instance_ref,
            predecessor_state_ref=audit.predecessor.record_id, clock_domain_id=self._clock.clock_domain_id,
            boot_identity_ref=self._clock.boot_identity_ref, accounting_observed_at=observed,
            consumed_prefix=_EvidenceAttemptOperationV1._consumption_v1(attempt),
            final_accounting_tail="UNRECONCILED_FULL_RESERVATION_RETAINED",
            lifecycle_disposition=("ORIGINAL_PREDECESSOR_RETAINED" if _EvidenceAttemptFailureAuditV1._state_gap_v1(audit, custody["kind"])
                                   else "NONPOSITIVE_SUCCESSOR_REQUESTED"),
            reservation_ref=attempt.payload.grant_ref + "::RESERVATION", failure_bounds=attempt.failure_bounds,
            reason_codes=reasons, primary_reason=evidence_attempt_primary_reason_v1(reasons), custody=custody,
            capture_manifest_or_absence=capture, capture_observed_between_or_absence=capture_time,
            controller_error_count=controller_count, drain_error_count=drain_count, cleanup_error_count=cleanup_count,
            diagnostic_errors={domain: dict(retained_entries=[], omitted_entry_count=count, complete=count == 0)
                               for domain, count in (("controller", controller_count), ("drain", drain_count), ("cleanup", cleanup_count))},
            diagnostic_observed_between=(diagnostic_before, diagnostic_after), invocation_measurement_or_absence=measurement,
            trigger_error=trigger)
        # The bounded encoder accepts native JSON data, so consumption crosses
        # through its already-closed canonical data mapping explicitly.
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
        body["consumed_prefix"] = _evidence_canonical_object_v1(deterministic_json(body["consumed_prefix"]).encode("utf-8"))
        body["invocation_measurement_or_absence"] = _evidence_canonical_object_v1(
            deterministic_json(measurement).encode("utf-8"), max_bytes=16384)
        baseline = _encode_evidence_projection_json_v1(body, maximum_bytes=16384, maximum_nodes=4096)
        remaining = 16384 - len(baseline)
        def node_count(value):
            # Only the already-encoded finite native body, or closed scalar
            # prefixes below, reaches this count. Dictionary keys are nodes.
            if type(value) is dict:
                return 1 + len(value) + sum(node_count(item) for item in value.values())
            if type(value) in (list, tuple):
                return 1 + sum(node_count(item) for item in value)
            return 1
        remaining_nodes = 4096 - node_count(body)
        def retain_trigger_field(name, value):
            nonlocal remaining, remaining_nodes
            previous = _encode_evidence_projection_json_v1(trigger[name], maximum_bytes=16384, maximum_nodes=4096)
            previous_nodes = node_count(trigger[name])
            try:
                encoded = _encode_evidence_projection_json_v1(value, maximum_bytes=remaining + len(previous),
                    maximum_nodes=min(4096, remaining_nodes + previous_nodes))
            except ComputationControlPlaneError:
                return False
            trigger[name] = value
            remaining -= len(encoded) - len(previous)
            remaining_nodes -= node_count(value) - previous_nodes
            return True

        names, code, native_error = trigger_snapshot[1:4]
        if trigger_snapshot[11]:
            retain_trigger_field("exception_shape", "SELECTED_NATIVE_FIELDS")
        if all(type(item) is str and 0 < len(item) <= 512 for item in names):
            retain_trigger_field("exception_type_or_absence", names)
        retain_trigger_field("reason_code_or_absence", code)
        if type(native_error) is dict or (all(item is None or (type(item) is int and -2**63 < item < 2**63) for item in native_error[:2])
                and all(item is None or (type(item) is str and len(item) <= 16384) for item in native_error[2:])):
            retain_trigger_field("native_error_or_absence", native_error)
        for name, entries in (("argument_prefix", trigger_snapshot[4]), ("traceback_prefix", trigger_snapshot[6])):
            for entry in entries:
                if name == "argument_prefix":
                    valid = (entry is None or type(entry) is bool or (type(entry) is str and len(entry) <= 16384)
                             or (type(entry) is int and -2**63 < entry < 2**63))
                else:
                    valid = (type(entry[0]) is str and len(entry[0]) <= 4096 and type(entry[1]) is str and len(entry[1]) <= 512
                             and type(entry[2]) is int and 0 <= entry[2] < 2**63)
                comma = bool(trigger[name])
                if not valid or remaining <= comma or remaining_nodes < node_count(entry):
                    break
                try:
                    encoded = _encode_evidence_projection_json_v1(entry, maximum_bytes=remaining - comma, maximum_nodes=remaining_nodes)
                except ComputationControlPlaneError:
                    break
                trigger[name].append(entry)
                remaining -= len(encoded) + comma
                remaining_nodes -= node_count(entry)
        trigger["arguments_complete"] = len(trigger["argument_prefix"]) == trigger["argument_count"]
        tail = (trigger_snapshot[7] if len(trigger["traceback_prefix"]) == len(trigger_snapshot[6]) else "PRESENT_NOT_RETAINED")
        # The remainder token can grow, so it shares the same remaining bytes.
        if retain_trigger_field("traceback_remainder", tail):
            trigger["traceback_complete"] = tail == "NONE"
        kind, code, native_error = (trigger[key] for key in ("exception_type_or_absence", "reason_code_or_absence", "native_error_or_absence"))
        trigger["complete"] = (trigger["exception_shape"] == "SELECTED_NATIVE_FIELDS" and type(kind) is tuple
            and (type(code) is str or code["reason"] == "NOT_CONTROL_PLANE_ERROR")
            and (type(native_error) is tuple or native_error["reason"] == "NOT_OS_ERROR")
            and trigger["arguments_complete"] and trigger["traceback_complete"]
            and trigger["cause_retention"] == trigger["context_retention"] == "ABSENT" and trigger["secondary_error_count"] == 0)
        for domain, entries in (("cleanup", cleanup_errors), ("controller", controller_errors), ("drain", drain_errors)):
            summary = body["diagnostic_errors"][domain]
            for entry in entries:
                comma = bool(summary["retained_entries"])
                if remaining <= comma or type(entry) not in (tuple, list) or not 1 <= len(entry) <= 3 or not all(
                        item is None or type(item) is str or (type(item) is int and 0 <= item < 2**63) for item in entry):
                    break
                if remaining_nodes < 1 + len(entry):
                    break
                try:
                    encoded = _encode_evidence_projection_json_v1(entry, maximum_bytes=remaining - comma, maximum_nodes=remaining_nodes)
                except ComputationControlPlaneError:
                    break
                summary["retained_entries"].append(entry)
                summary["omitted_entry_count"] -= 1
                summary["complete"] = summary["omitted_entry_count"] == 0
                # The decreasing omitted-count width and false->true change
                # only shrink the body. This charge is a conservative bound.
                remaining -= len(encoded) + comma
                remaining_nodes -= 1 + len(entry)
        raw = _encode_evidence_projection_json_v1(body, maximum_bytes=16384, maximum_nodes=4096)
        _EvidenceAttemptFailureAuditV1._check_current_v1(audit)
        snapshot = (native, audit, native.original, attempt.payload, raw, plan, capture_snapshot, terminal, no_child, cleanup, trigger_snapshot)
        self._failure_observation_originals = (*self._failure_observation_originals, snapshot)
        return snapshot

    def _require_failure_observation_v1(self, audit, snapshot):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(type(snapshot) is tuple and len(snapshot) == 11
                        and any(entry is snapshot for entry in self._failure_observation_originals)
                        and snapshot[0] is audit.native and snapshot[1] is audit and snapshot[2] is audit.native.original
                        and snapshot[3] is audit.attempt.payload and audit.attempt.supervisor is self
                        and audit.native._terminal_original is snapshot[7] and audit.trigger_snapshot is snapshot[10]
                        and snapshot[10][0] is audit.trigger_original and snapshot[10][10] is audit.trigger_roster,
                        "LP03_FAILURE_SNAPSHOT_ORIGINAL_CHANGED")
        if snapshot[8] is not None:
            _native_require(EvidenceProcessSupervisorV1._require_no_child_v1(self, audit.native) is snapshot[8],
                            "LP03_FAILURE_NO_CHILD_WITNESS_CHANGED")
        if snapshot[5] is not None:
            _native_require(EvidenceProcessSupervisorV1._require_capture_snapshot_v1(self, audit.native, snapshot[6]) is snapshot[5][0],
                            "LP03_FAILURE_CAPTURE_WITNESS_CHANGED")
        if snapshot[9] is not None:
            _native_require(any(entry is snapshot[9] for entry in self._cleanup_originals),
                            "LP03_FAILURE_CLEANUP_WITNESS_CHANGED")
        return snapshot

    @staticmethod
    def _failure_reason_v1(native, original_error, *, fallback="SUPERVISION_FAILURE", trigger_original=None,
                           prelaunch_capacity_error=None):
        try:
            return EvidenceProcessSupervisorV1._classify_failure_reason_v1(native, original_error,
                fallback=fallback, trigger_original=trigger_original, prelaunch_capacity_error=prelaunch_capacity_error)
        except BaseException as classification_error:
            supervisor = native.original[0]
            EvidenceProcessSupervisorV1._record_failure_secondary_v1(supervisor, native, classification_error, stage="CLASSIFICATION")
            return fallback

    @staticmethod
    def _classify_failure_reason_v1(native, original_error, *, fallback="SUPERVISION_FAILURE", trigger_original=None,
                                    prelaunch_capacity_error=None):
        """Exact selected-owner equivalences, never exception-text guessing."""
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, ReasonCode
        from ..stage1_prediction_markets.qku_computation_control_plane.lifecycle import evidence_attempt_primary_reason_v1
        # Only native scalar arguments may reach the existing equivalence
        # helper. Tuple comparison must not call a foreign argument's __eq__.
        if type(original_error) is not ContractValidationError:
            mro = type.__dict__["__mro__"].__get__(type(original_error))
            if (len(mro) <= 64 and any(kind is OSError for kind in mro)
                    and native.phase == "CREATE_PROCESS_RETURNED_FAILURE"):
                creation = tuple(entry for entry in native.original[0]._creation_originals if entry[0] is native)
                if (creation and creation[-1][1] == "RETURNED_FAILURE" and creation[-1][3] is False
                        and creation[-1][2] is native._process_information_original):
                    return "FAILED_TO_START"
            return fallback
        if trigger_original is not None:
            from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
            _native_require(trigger_original[0] is native and trigger_original[3] is original_error,
                            "LP03_FAILURE_CLASSIFICATION_ORIGINAL_TRIGGER")
            args, original_code = trigger_original[4], trigger_original[9][2]
        else:
            args = BaseException.args.__get__(original_error)
            attributes = BaseException.__dict__["__dict__"].__get__(original_error)
            original_code = (attributes.get("reason_code") if type(attributes) is dict and len(attributes) <= 16
                             and all(type(key) is str for key in attributes) else None)
        if (type(args) is not tuple or len(args) != 1 or type(args[0]) is not str or len(args[0]) > 256
                or type(original_code) is not ReasonCode):
            return fallback
        # Explicit equivalent category at the existing selected owner.
        if original_code is ReasonCode.BUDGET_EXCEEDED:
            return "RESOURCE_EXHAUSTED"
        if original_code is ReasonCode.EVIDENCE_SOURCE_PURPOSE_DENIED:
            # Lifecycle disposition stays separate from the exact retained trigger code.
            return "SOURCE_INVALIDATED"
        if original_code is not ReasonCode.INVALID_CONTRACT:
            return fallback
        aliases = {
            "LP03_ATTEMPT_EXPIRED": "EXPIRED", "LP03_REGISTRATION_EXPIRED": "EXPIRED",
            "LP03_ATTEMPT_CLOCK_REGRESSED": "INTEGRITY_FAILURE",
            "LP03_REGISTRATION_CLOCK_CHANGED_OR_REGRESSED": "INTEGRITY_FAILURE",
            "LP03_ENVELOPE_WITHDRAWN_OR_STALE": "AUTHORITY_INVALIDATED",
            "LP03_REGISTRATION_KEY_NOT_CURRENT": "AUTHORITY_INVALIDATED",
            "LP03_ATTEMPT_ROLE_KEY_NOT_CURRENT": "AUTHORITY_INVALIDATED",
            "LP03_ORIGINAL_RIGHTS_WITHDRAWN_OR_STALE": "SOURCE_INVALIDATED",
            "LP03_PARAMETER_PROTOCOL_EXPIRED": "PROTOCOL_INVALIDATED",
            "LP03_ATTEMPT_RESOURCE_EXHAUSTED": "RESOURCE_EXHAUSTED",
            "LP03_REGISTRATION_RESOURCE_EXHAUSTED": "RESOURCE_EXHAUSTED",
        }
        # The reference layer's exact native error equivalence is applied to
        # retained scalar args. Reading live error attributes again could
        # replace an earlier original failure at an accounting callback.
        def exact_detail(allowed):
            return next((detail for detail in allowed if args == (f"{ReasonCode.INVALID_CONTRACT}: {detail}",)), None)
        # Only the error caught around the actual prelaunch capacity call may
        # use these equivalences. In particular, a generic JSON size failure
        # elsewhere is not evidence of an admitted storage-capacity denial.
        if trigger_original is not None and prelaunch_capacity_error is original_error:
            capacity_aliases = {
                "LP03_FAILURE_AUDIT_RESERVE_INSUFFICIENT:input_reads": "RESOURCE_EXHAUSTED",
                "LP03_FAILURE_AUDIT_RESERVE_INSUFFICIENT:input_bytes": "RESOURCE_EXHAUSTED",
                "LP03_FAILURE_AUDIT_RESERVE_INSUFFICIENT:persistent_operations": "RESOURCE_EXHAUSTED",
                "LP03_FAILURE_AUDIT_RESERVE_INSUFFICIENT:persistent_bytes": "RESOURCE_EXHAUSTED",
                "LP03_FAILURE_CAPTURE_HEADER_CAPACITY": "CAPACITY_EXHAUSTED",
                "LP03_FAILURE_CAPTURE_ROSTER_CAPACITY": "CAPACITY_EXHAUSTED",
                "LP03_FAILURE_MAXIMUM_MANIFEST_UNREPRESENTABLE": "CAPACITY_EXHAUSTED",
                "LP03_PROJECTION_JSON_BYTES": "CAPACITY_EXHAUSTED",
            }
            detail = exact_detail(capacity_aliases)
            if detail is not None:
                return capacity_aliases[detail]
        reason = exact_detail(aliases)
        if reason is not None:
            return aliases[reason]
        stopped = exact_detail((
            "LP03_NATIVE_WORKER_FRAME_UNAVAILABLE", "LP03_NATIVE_DISPATCH_STOPPED",
            "LP03_NATIVE_LAUNCH_STOPPED", "LP03_NATIVE_RESUME_STOPPED"))
        if stopped is not None:
            from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
            from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
            def acquire(lock):
                now = _EvidenceLocalClockV1.observe_v1(native.original[0]._clock)
                remaining = native.original[1].failure_bounds[1] - now[1]
                _native_require(remaining > 0 and lock.acquire(timeout=remaining / 1_000_000_000),
                                "LP03_FAILURE_STOP_REASON_SNAPSHOT_UNAVAILABLE")
            def copy_reasons(values):
                _native_require(type(values) in (tuple, list) and len(values) <= 32
                    and all(type(value) is str and len(value) <= 64 for value in values), "LP03_FAILURE_STOP_REASON_ROSTER")
                return tuple(values)
            acquire(native._control_lock)
            try:
                reasons = copy_reasons(native._reasons)
            finally:
                native._control_lock.release()
            drain = native._drain_original
            if drain is not None:
                acquire(drain[1])
                try:
                    _native_require(native._drain_original is drain and native._io is drain[0],
                                    "LP03_FAILURE_STOP_REASON_CUSTODY_CHANGED")
                    reasons += copy_reasons(drain[0]["reasons"])
                finally:
                    drain[1].release()
            if reasons:
                return evidence_attempt_primary_reason_v1(tuple(dict.fromkeys(
                    "PROTOCOL_INVALIDATED" if value == "WORKER_PROTOCOL_INVALID" else value for value in reasons)))
        return fallback

    def _retain_failure_trigger_v1(self, native, original_error, *, stage="TRIGGER"):
        """Retain constant-size native descriptor roots before settlement."""
        try:
            from ..stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
            cls = type(original_error)
            mro = type.__dict__["__mro__"].__get__(cls)
            ancestry_available = len(mro) <= 64
            control_plane_error = ancestry_available and any(kind is ComputationControlPlaneError for kind in mro)
            os_error = ancestry_available and any(kind is OSError for kind in mro)
            attributes = BaseException.__dict__["__dict__"].__get__(original_error)
            code = (attributes.get("reason_code") if control_plane_error and type(attributes) is dict and len(attributes) <= 16
                    and all(type(key) is str for key in attributes) else None)
            native_fields = ((OSError.errno.__get__(original_error), OSError.winerror.__get__(original_error),
                OSError.strerror.__get__(original_error), OSError.filename.__get__(original_error),
                OSError.filename2.__get__(original_error)) if os_error else None)
            metadata = (cls, (type.__dict__["__module__"].__get__(cls), type.__dict__["__qualname__"].__get__(cls)),
                        code, control_plane_error, native_fields, os_error, ancestry_available)
            retained = (native, native.original, stage, original_error,
                BaseException.args.__get__(original_error), BaseException.__traceback__.__get__(original_error),
                BaseException.__cause__.__get__(original_error), BaseException.__context__.__get__(original_error),
                BaseException.__suppress_context__.__get__(original_error), metadata)
            # Dispatch and the original controller can fail concurrently.
            # Publish both original roots under the same retained native lock.
            with native._control_lock:
                self._failure_trigger_originals = (*self._failure_trigger_originals, retained)
            return retained
        except BaseException as capture_error:
            self._unresolved = True
            native._failed_trigger_capture = capture_error
            return None

    def _record_failure_secondary_v1(self, native, error, *, stage):
        self._unresolved = True
        EvidenceProcessSupervisorV1._retain_failure_trigger_v1(self, native, error, stage=stage)
        try:
            list.append(native._controller_errors, (stage, type.__dict__["__name__"].__get__(type(error))))
        except BaseException as capture_error:
            native._failed_trigger_capture = capture_error

    def _record_failure_cleanup_v1(self, native, error, *, stage):
        # Cleanup must continue even when recording its failure cannot finish.
        # Keep quarantine independently of an allocated diagnostic list entry.
        self._unresolved = True
        EvidenceProcessSupervisorV1._retain_failure_trigger_v1(self, native, error, stage=stage)
        try:
            list.append(native.cleanup_errors, (stage, type.__dict__["__name__"].__get__(type(error))))
        except BaseException as capture_error:
            native._failed_trigger_capture = capture_error

    def _audit_failure_v1(self, native, *, reason, original_error, trigger_original):
        from ..agents.pr169_agent_orch1_resolvers import AgentOrchService
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1
        try:
            reason = EvidenceProcessSupervisorV1._failure_reason_v1(native, original_error,
                fallback=reason, trigger_original=trigger_original)
            prior = tuple(entry for entry in self._failure_trigger_originals if entry[0] is native)
            _native_require(trigger_original is not None and any(entry is trigger_original for entry in prior)
                            and trigger_original[3] is original_error and native._failed_trigger_capture is None,
                            "LP03_FAILURE_ORIGINAL_TRIGGER_REQUIRED")
            try:
                _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(native.original[1].registration),
                                "LP03_FAILURE_PRE_AUDIT_ACCOUNTING_UNAVAILABLE")
            except BaseException as accounting_error:
                EvidenceProcessSupervisorV1._record_failure_secondary_v1(self, native, accounting_error, stage="PRE_AUDIT_ACCOUNTING")
                native._reasons.append("ACCOUNTING_FAILURE")
            roster = tuple(entry for entry in self._failure_trigger_originals if entry[0] is native)
            _native_require(len(roster) >= len(prior) and all(left is right for left, right in zip(prior, roster)),
                            "LP03_FAILURE_TRIGGER_ACCOUNTING_CUSTODY_CHANGED")
            return AgentOrchService._audit_evidence_attempt_failure_v1(self._issuer.service, native.original[5],
                requester_context=self, native=native, reason=reason, original_error=original_error,
                trigger_original=trigger_original, trigger_roster=roster)
        except BaseException as audit_error:
            EvidenceProcessSupervisorV1._record_failure_secondary_v1(self, native, audit_error, stage="FAILURE_AUDIT")
            return None

    def start_v1(self, attempt_grant):
        from ..agents.pr169_agent_orch1_resolvers import AgentOrchService, EvidenceAttemptGrantV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import (
            _EvidenceAttemptFailureAuditV1, _EvidenceAttemptOperationV1)
        EvidenceProcessSupervisorV1._assert_original_v1(self)
        _native_require(type(attempt_grant) is EvidenceAttemptGrantV1 and attempt_grant._owner is self._issuer,
                        "LP03_NATIVE_ORIGINAL_GRANT_REQUIRED")
        attempt = attempt_grant._attempt
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.handle is attempt_grant
                        and attempt.registration.issuer is self._issuer and attempt.supervisor is self
                        and attempt.registration.attempts.get((attempt.request.lane, attempt.request.attempt_ordinal)) is attempt,
                        "LP03_NATIVE_ORIGINAL_ATTEMPT_REQUIRED")
        _EvidenceAttemptOperationV1._assert_original_members_v1(attempt, canonical=True)
        _native_require(self._active is None and all(value.original[1] is not attempt for value in self._retained),
                        "LP03_NATIVE_ATTEMPT_ALREADY_STARTED_OR_UNRESOLVED")
        native = _WindowsEvidenceProcessV1(self, attempt)
        self._active, self._retained = native, (*self._retained, native)
        self._creation_originals = (*self._creation_originals, (native, "NOT_ENTERED", None, None))
        self._controller_originals = (*self._controller_originals, (native, "NOT_CREATED", None))
        prelaunch_capacity_error = None
        try:
            AgentOrchService.resolve_evidence_attempt_v1(self._issuer.service, attempt_grant,
                purpose="EVIDENCE_LANE_EXECUTION_V1", requester_context=self)
            with EvidenceProcessSupervisorV1._operation_v1(self, attempt):
                try:
                    capacity = _EvidenceAttemptFailureAuditV1._storage_capacity_v1(attempt)
                except BaseException as capacity_error:
                    prelaunch_capacity_error = capacity_error
                    raise
                self._capacity_originals = (*self._capacity_originals, (native, native.original, attempt.payload, capacity))
            _WindowsEvidenceProcessV1._start_controller_v1(native)
            with EvidenceProcessSupervisorV1._operation_v1(self, attempt):
                _WindowsEvidenceProcessV1.prepare_suspended_v1(native)
            AgentOrchService._append_evidence_process_observation_v1(self._issuer.service, attempt_grant,
                requester_context=self, native=native, stage="SUSPENDED")
            _WindowsEvidenceProcessV1._start_drains_v1(native)
            with EvidenceProcessSupervisorV1._operation_v1(self, attempt):
                _WindowsEvidenceProcessV1.resume_v1(native)
            AgentOrchService._append_evidence_process_observation_v1(self._issuer.service, attempt_grant,
                requester_context=self, native=native, stage="RUNNING")
            return native
        except BaseException as original_error:
            trigger_original = EvidenceProcessSupervisorV1._retain_failure_trigger_v1(self, native, original_error)
            failure_reason = EvidenceProcessSupervisorV1._failure_reason_v1(native, original_error,
                trigger_original=trigger_original, prelaunch_capacity_error=prelaunch_capacity_error)
            try:
                if native._native_custody[1] is None and (native._process_information_original is None
                        or not native._process_information_original.hProcess):
                    _WindowsEvidenceProcessV1._settle_no_child_v1(native)
                else:
                    EvidenceProcessSupervisorV1.request_stop_v1(self, attempt_grant, reason=failure_reason)
                    if native._io is None and native._pipe_original is not None:
                        _WindowsEvidenceProcessV1._start_drains_v1(native)
                    EvidenceProcessSupervisorV1.observe_terminal_v1(self, attempt_grant)
            except BaseException as exc:
                EvidenceProcessSupervisorV1._record_failure_secondary_v1(self, native, exc, stage="FAILED_START_SETTLEMENT")
                if native._terminal_original is None:
                    native.phase = "TERMINATION_UNKNOWN"
            EvidenceProcessSupervisorV1._audit_failure_v1(self, native, reason=failure_reason,
                original_error=original_error, trigger_original=trigger_original)
            raise

    def _capture_process_observation_v1(self, native, stage):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json
        EvidenceProcessSupervisorV1._assert_custody_v1(self)
        _native_require(type(native) is _WindowsEvidenceProcessV1 and native is self._active
                        and any(entry is native for entry in self._retained) and native.original[0] is self
                        and stage in ("SUSPENDED", "RUNNING", "TERMINAL")
                        and not any(entry[0] == stage for entry in native._observation_originals),
                        "LP03_PROCESS_OBSERVATION_ORIGINAL_NATIVE")
        attempt = native.original[1]
        if stage == "TERMINAL":
            terminal = native._terminal_original
            _native_require(terminal is not None and native.phase == "TERMINAL_RETAINED_AND_CLOSED",
                            "LP03_PROCESS_TERMINAL_CUSTODY_UNAVAILABLE")
            observed, stdout_eof, stderr_eof = terminal[:3]
            joined_controller = native._controller is not None and not native._controller.is_alive()
            joined_drains = all(not thread.is_alive() for thread in native._drain_original[2])
            reasons = tuple("PROTOCOL_INVALIDATED" if reason == "WORKER_PROTOCOL_INVALID" else reason for reason in terminal[3])
            output_bytes, diagnostic_bytes = terminal[6], len(terminal[5])
            controller_errors, drain_errors = len(terminal[7]), len(terminal[8])
        else:
            _WindowsEvidenceProcessV1._assert_native_handles_v1(native)
            _native_require((stage == "SUSPENDED" and native.phase == "SUSPENDED_AND_ASSIGNED" and not native.resumed)
                            or (stage == "RUNNING" and native.resumed), "LP03_PROCESS_OBSERVATION_STAGE")
            observed = _WindowsEvidenceProcessV1.observe_v1(native)
            terminal, stdout_eof, stderr_eof, joined_controller, joined_drains = None, False, False, False, False
            reasons = tuple(native._reasons)
            output_bytes = 0 if native._io is None else native._io["output_bytes"]
            diagnostic_bytes = 0 if native._io is None else len(native._io["diagnostics"])
            controller_errors = len(native._controller_errors)
            drain_errors = 0 if native._io is None else len(native._io["errors"])
        from ..stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
        measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_NOT_STARTED")
        if stage == "TERMINAL":
            measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_MEASUREMENT_UNAVAILABLE")
            if native._exchange_original is not None:
                measurement = native._exchange_original[2]["invocation_measurement"]
            else:
                try:
                    for frame in terminal[4]:
                        if attempt.payload.component_closure == ("MATH-01","MATH-02") and frame["kind"] in ("FAILED","COMPUTATION_RESULT"):
                            _WindowsEvidenceProcessV1._require_probability_edge_frame_v1(native,frame)
                        if frame["kind"] == "FAILED":
                            measurement = frame["payload"]["measurement_or_absence"]
                        elif frame["kind"] == "COMPUTATION_RESULT":
                            measurement = frame["payload"]["invocation_measurement"]
                except ComputationControlPlaneError:
                    measurement = dict(state="ABSENT_WITH_REASON",reason="INVOCATION_MEASUREMENT_UNQUALIFIED")
                    reasons = tuple(dict.fromkeys((*reasons,"PROTOCOL_INVALIDATED")))
            if "state" not in measurement:
                from ..stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
                try:
                    _WindowsEvidenceProcessV1._require_invocation_measurement_v1(
                        native, measurement, positive=native._exchange_original is not None)
                except ComputationControlPlaneError:
                    if native._exchange_original is not None:
                        raise
                    # Raw frames/diagnostics stay in the original terminal
                    # tuple, but an unjoined clock is never promoted to timing.
                    measurement = dict(state="ABSENT_WITH_REASON", reason="INVOCATION_MEASUREMENT_UNQUALIFIED")
                    reasons = tuple(dict.fromkeys((*reasons, "PROTOCOL_INVALIDATED")))
        when = _EvidenceLocalClockV1.observe_v1(self._clock)
        body = dict(schema_version="1.1", operation="SVC_PROCESS_OBSERVATION_APPEND_V1",
            observation_ref=attempt.grant_record.record_id + "::PROCESS:" + stage, grant_ref=attempt.grant_record.record_id,
            fence_ref=attempt.payload.fence_ref, supervisor_instance_ref=self.instance_ref,
            predecessor_state_ref=attempt.current_state.record_id, stage=stage, clock_domain_id=self._clock.clock_domain_id,
            boot_identity_ref=self._clock.boot_identity_ref, observed_at=when, native_observation=observed,
            resumed=native.resumed, stdout_eof=stdout_eof, stderr_eof=stderr_eof,
            controller_joined=joined_controller, drains_joined=joined_drains, output_bytes=output_bytes,
            diagnostic_bytes=diagnostic_bytes, controller_error_count=controller_errors, drain_error_count=drain_errors,
            cleanup_error_count=len(native.cleanup_errors), reason_codes=reasons,
            exchange_complete=native._exchange_original is not None, events=native._events_dispatched,
            computations=native._computations_dispatched, invocation_measurement_or_absence=measurement)
        snapshot = (stage, deterministic_json(body), native.original, native._native_custody[4], terminal, native._exchange_original)
        native._observation_originals = (*native._observation_originals, snapshot)
        return snapshot

    def _require_process_observation_v1(self, native, snapshot):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        _native_require(type(native) is _WindowsEvidenceProcessV1 and any(entry is native for entry in self._retained)
                        and native.original is snapshot[2] and native.original[0] is self
                        and any(entry is snapshot for entry in native._observation_originals)
                        and (snapshot[0] != "TERMINAL" or (native._terminal_original is snapshot[4]
                            and native._exchange_original is snapshot[5])), "LP03_PROCESS_OBSERVATION_CUSTODY_CHANGED")

    def _finish_dispatch_v1(self, native, attempt_grant):
        from ..agents.pr169_agent_orch1_resolvers import AgentOrchService
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1

        terminal = EvidenceProcessSupervisorV1.observe_terminal_v1(self, attempt_grant)
        if (terminal is None and native._terminal_original is None
                and native.phase == "TERMINATION_UNKNOWN" and self._unresolved):
            raise ContractValidationError(ReasonCode.EVIDENCE_TERMINATION_UNKNOWN, "LP03_NATIVE_TERMINATION_UNKNOWN")
        _native_require(terminal is not None and terminal[0]["exit_code"] == 0 and terminal[0]["total_processes"] == 1
                        and not terminal[3] and not terminal[5] and not terminal[7] and not terminal[8]
                        and terminal[9]["complete"] and not native.cleanup_errors and not self._unresolved,
                        "LP03_NATIVE_WORKER_TERMINAL_NONPOSITIVE")
        _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(native.original[1].registration),
                        "LP03_EXECUTION_ACCOUNTING_UNPROVEN")
        AgentOrchService._append_evidence_process_observation_v1(self._issuer.service, attempt_grant,
            requester_context=self, native=native, stage="TERMINAL")
        return terminal

    def request_stop_v1(self, attempt_grant, *, reason):
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        native = self._active
        _native_require(native is not None and any(value is native for value in self._retained)
                        and native.original[5] is attempt_grant
                        and reason in ("SUPERVISION_FAILURE", "INTEGRITY_FAILURE", "ACCOUNTING_FAILURE", "WORKER_PROTOCOL_INVALID",
                            "PROTOCOL_INVALIDATED", "RESOURCE_EXHAUSTED", "EXPIRED", "AUTHORITY_INVALIDATED", "SOURCE_INVALIDATED",
                            "MODEL_INVALIDATED", "AUTHENTICATED_CANCEL"),
                        "LP03_NATIVE_STOP_ORIGINAL_ATTEMPT_REQUIRED")
        _wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(self._clock)
        immediate = not native.resumed or native.original[3].stop_grace_ns == 0 or native._remaining_v1() <= 0
        _WindowsEvidenceProcessV1._note_stop_v1(native, reason, mono, immediate=immediate)
        if immediate and native._api_original is not None:
            native._stop_attempted = True
            native._controller_errors.extend(_WindowsEvidenceProcessV1.request_native_stop_v1(native))

    def observe_terminal_v1(self, attempt_grant):
        from types import MappingProxyType
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        native = self._active
        _native_require(native is not None and any(value is native for value in self._retained)
                        and native.original[5] is attempt_grant, "LP03_NATIVE_TERMINAL_ORIGINAL_ATTEMPT_REQUIRED")
        if native._terminal_original is not None:
            return native._terminal_original
        io = native._io
        try:
            original = native._drain_original
            _native_require(original is not None and io is original[0] and io["condition"] is original[1]
                            and io["threads"] is original[2], "LP03_NATIVE_DRAIN_CUSTODY_UNAVAILABLE")
            while True:
                observed = _WindowsEvidenceProcessV1.observe_v1(native)
                with io["condition"]:
                    if observed["exit_code"] is not None and observed["active_processes"] == 0 and io["stdout_eof"] and io["stderr_eof"]:
                        break
                    remaining = _WindowsEvidenceProcessV1._settlement_remaining_v1(native)
                    if remaining <= 0:
                        raise ContractValidationError(ReasonCode.EVIDENCE_TERMINATION_UNKNOWN,
                            "LP03_NATIVE_TERMINATION_UNKNOWN")
                    io["condition"].wait(min(0.01, remaining))
            for thread in io["threads"]:
                thread.join(_WindowsEvidenceProcessV1._settlement_remaining_v1(native))
            if native._cancel_thread is not None:
                native._cancel_thread.join(_WindowsEvidenceProcessV1._settlement_remaining_v1(native))
            native._controller_done.set()
            native._controller.join(_WindowsEvidenceProcessV1._settlement_remaining_v1(native))
            if any(thread.is_alive() for thread in (*io["threads"], native._controller,
                    *((native._cancel_thread,) if native._cancel_thread is not None else ()))):
                raise ContractValidationError(ReasonCode.EVIDENCE_TERMINATION_UNKNOWN,
                    "LP03_NATIVE_TERMINATION_UNKNOWN")
            native_before = _EvidenceLocalClockV1.observe_v1(self._clock)
            final = _WindowsEvidenceProcessV1.observe_v1(native)
            native_after = _EvidenceLocalClockV1.observe_v1(self._clock)
            if final["exit_code"] != observed["exit_code"] or final["active_processes"] != 0:
                raise ContractValidationError(ReasonCode.EVIDENCE_TERMINATION_UNKNOWN,
                    "LP03_NATIVE_TERMINATION_UNKNOWN")
            capture_before = _EvidenceLocalClockV1.observe_v1(self._clock)
            with original[1]:
                _native_require(native._drain_original is original and native._io is original[0]
                                and io["threads"] is original[2] and io["stdout_eof"] and io["stderr_eof"],
                                "LP03_NATIVE_DRAIN_CUSTODY_CHANGED")
                reasons = tuple(dict.fromkeys((*native._reasons, *io["reasons"])))
                stdout_bytes, stderr_bytes = bytes(io["stdout_bytes"]), bytes(io["diagnostics"])
                capture = MappingProxyType(dict(stdout=stdout_bytes, stderr=stderr_bytes,
                    stdout_observed_bytes=io["stdout_observed_bytes"], stderr_observed_bytes=io["stderr_observed_bytes"],
                    stdout_discarded_bytes=io["stdout_observed_bytes"] - len(stdout_bytes),
                    stderr_discarded_bytes=io["stderr_observed_bytes"] - len(stderr_bytes),
                    stdout_eof=True, stderr_eof=True,
                    complete=len(stdout_bytes) + len(stderr_bytes) == io["output_bytes"]))
                _native_require(capture["stdout_observed_bytes"] + capture["stderr_observed_bytes"] == io["output_bytes"]
                                and len(stdout_bytes) + len(stderr_bytes) <= native.original[3].max_output_bytes,
                                "LP03_NATIVE_CAPTURE_ACCOUNTING_UNPROVEN")
                terminal = (MappingProxyType(final), True, True, reasons, tuple(io["frames"]),
                            stderr_bytes, io["output_bytes"], tuple(native._controller_errors), tuple(io["errors"]), capture)
            capture_after = _EvidenceLocalClockV1.observe_v1(self._clock)
            terminal = (*terminal, (native_before, native_after), (capture_before, capture_after))
            native._terminal_original = terminal
            _native_require(not any(entry[0] is native for entry in self._capture_originals),
                            "LP03_CAPTURE_WITNESS_ALREADY_RETAINED")
            self._capture_originals = (*self._capture_originals,
                (native, terminal, capture, native.original, native.original[1].payload))
            _WindowsEvidenceProcessV1._close_settled_v1(native, terminal)
            return terminal
        except BaseException as exc:
            self._unresolved = True
            native.phase = "TERMINATION_UNKNOWN"
            EvidenceProcessSupervisorV1._record_failure_secondary_v1(self, native, exc, stage="TERMINAL_OBSERVATION")
            if native._controller is not None:
                # UNKNOWN keeps custody. Do not cancel the only stop owner.
                try:
                    from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
                    _wall, mono, _cpu = _EvidenceLocalClockV1.observe_v1(self._clock)
                    native._note_stop_v1("SUPERVISION_FAILURE", mono, immediate=True)
                    if not native._stop_attempted and native._api_original is not None:
                        native._stop_attempted = True
                        native._controller_errors.extend(native.request_native_stop_v1())
                    native._controller.join(native._settlement_remaining_v1())
                except BaseException as stop_exc:
                    native._controller_errors.append(("UNKNOWN_CUSTODY_STOP", type(stop_exc).__name__))
            return None


class DashboardReadModelService:
    def __init__(self, base_dir: Path | str | None = None) -> None:
        root = _repo_root()
        self.base_dir = (Path(base_dir) if base_dir is not None else root / GENERATED_PREFIX).resolve()
        self._cache: dict[str, tuple[dict[str, Any], ...]] = {}

    def bind_evidence_receiver_v1(self, *, parent_resolver, host_binding, persistence_adapter):
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceReceiverContextV1
        return _EvidenceReceiverContextV1._bind_v1(owner_service=self, receiving_owner="SVC1",
            parent_resolver=parent_resolver, host_binding=host_binding, persistence_adapter=persistence_adapter)

    def receive_evidence_delivery_v1(self, delivery_ref, *, receiver_context):
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceReceiverContextV1
        return _EvidenceReceiverContextV1._receive_v1(receiver_context, delivery_ref, owner_service=self)

    def dispatch_evidence_attempt_v1(self, attempt_grant):
        """Closed original exchange; terminal data does not publish evidence."""
        import sys
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane import evidence_execution as worker
        from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import FormulaInputResolverV1, EvidenceInvocationInputsV1
        from ..stage1_prediction_markets.qku_computation_control_plane.implementation_registry import resolve_evidence_invocation_v1, LP03_DECIMAL_CONTEXT_POLICY_REF_V1
        from ..stage1_prediction_markets.qku_computation_control_plane.serialization import deterministic_json, _evidence_frozen_data_v1
        from ..stage1_prediction_markets.qku_computation_control_plane.persistence import _EvidenceRegistrationOperationV1
        supervisor = getattr(self, "_evidence_supervisor_v1", None)
        _native_require(type(supervisor) is EvidenceProcessSupervisorV1 and supervisor._service is self,
                        "LP03_DISPATCH_ORIGINAL_SUPERVISOR_REQUIRED")
        native = EvidenceProcessSupervisorV1.start_v1(supervisor, attempt_grant)
        attempt, grant = native.original[1], native.original[1].payload
        envelope = attempt.registration.envelope_entry[3]
        causal_scope = grant.causal_timeline_v1()
        packet = None
        producer_packet = None
        edge = grant.component_closure == ("MATH-01", "MATH-02")
        computations = 2 if edge else 1
        math_id = None

        def send(kind, payload, *, compute=False):
            ordinal = native._parent_output_ordinal
            raw = worker.encode_evidence_worker_frame_v1(dict(protocol=worker.WORKER_PROTOCOL_V1, kind=kind,
                attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref, ordinal=ordinal, payload=payload),
                direction="PARENT_TO_WORKER", attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref,
                ordinal=ordinal, frame_byte_limit=grant.budgets.frame_byte_limit)
            if causal_scope is not None and kind == "INPUT_SEGMENT":
                _native_require(len(raw) <= grant.budgets.segment_max_bytes, "LP03_TIMELINE_INPUT_SEGMENT_BYTE_LIMIT")
            with native._write_lock, EvidenceProcessSupervisorV1._operation_v1(supervisor, attempt) as operation:
                _WindowsEvidenceProcessV1._assert_native_handles_v1(native)
                _native_require(not native._reasons and not native._stop_signal.is_set(), "LP03_NATIVE_DISPATCH_STOPPED")
                if compute:
                    _native_require(native._events_dispatched == native._computations_dispatched == 0,
                                    "LP03_NATIVE_COMPUTATION_ALREADY_DISPATCHED")
                    _native_require(grant.budgets.max_events >= 1 and grant.budgets.max_computations >= computations,
                                    "LP03_NATIVE_EDGE_DISPATCH_BUDGET")
                    native._events_dispatched, native._computations_dispatched = 1, computations
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                _WindowsEvidenceProcessV1._assert_native_handles_v1(native)
                if math_id in ("MATH-06", "MATH-07", "MATH-02", "MATH-01", "MATH-04", "MATH-05", "MATH-08", "MATH-09", "MATH-10", "MATH-11", "MATH-14", "MATH-15", "MATH-16", "MATH-17", "MATH-18", "MATH-19", "MATH-20", "MATH-21", "MATH-22", "MATH-23", "MATH-24", "MATH-25", "MATH-12", "MATH-13", "MATH-26", "MATH-27", "MATH-28", "MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52") and packet is not None:
                    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
                    if edge:
                        EvidenceInvocationInputsV1._require_original_v1(producer_packet, attempt)
                worker._write_worker_bytes_v1(native._pipe_original[0][1], raw)
                native._parent_output_ordinal += 1
                return len(raw)

        try:
            _native_require(grant.component_closure in (("MATH-06",), ("MATH-07",), ("MATH-01",), ("MATH-03",), ("MATH-04",), ("MATH-05",), ("MATH-08",), ("MATH-09",), ("MATH-10",), ("MATH-11",), ("MATH-14",), ("MATH-15",), ("MATH-16",), ("MATH-17",), ("MATH-18",), ("MATH-19",), ("MATH-20",), ("MATH-21",), ("MATH-22",), ("MATH-23",), ("MATH-24",), ("MATH-25",), ("MATH-12",), ("MATH-13",), ("MATH-26",), ("MATH-27",), ("MATH-28",), ("MATH-29",), ("MATH-30",), ("MATH-31",), ("MATH-37",), ("MATH-32",), ("MATH-33",), ("MATH-35",), ("MATH-36",), ("MATH-38",), ("MATH-39",), ("MATH-40",), ("MATH-41",), ("MATH-42",), ("MATH-43",), ("MATH-44",), ("MATH-45",), ("MATH-50",), ("MATH-51",), ("MATH-52",), ("MATH-01", "MATH-02"))
                            and (not grant.callback_pins or causal_scope is not None),
                            "LP03_NATIVE_SELECTED_PROFILE_UNAVAILABLE")
            math_id = grant.component_closure[-1] if edge else grant.component_closure[0]
            pin = grant.component_and_callback_pins["components"][-1] if edge else grant.component_and_callback_pins["components"][0]
            _native_require(pin[0] == math_id, "LP03_NATIVE_COMPONENT_PIN_JOIN")
            contract = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
                resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
            if edge:
                producer_pin = grant.component_and_callback_pins["components"][0]
                producer_contract = resolve_evidence_invocation_v1(producer_pin[0], implementation_pin=producer_pin[1],
                    specification_pin=producer_pin[2], resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
                contracts = (producer_contract, contract)
                _native_require(tuple(row.math_id for row in contracts) == ("MATH-01", "MATH-02"),
                                "LP03_NATIVE_EDGE_COMPONENT_PIN_JOIN")
            send("START", dict(signed_grant=attempt.grant_record.signed_grant,
                environment_identity=envelope.environment_identity, package_identity_ref=envelope.package_identity_ref))
            started = _WindowsEvidenceProcessV1._receive_v1(native, 0, "STARTED")
            expected = dict(environment_identity=envelope.environment_identity,
                executable=str(Path(sys.executable).resolve()), base_executable=str(Path(sys._base_executable).resolve()),
                prefix=str(Path(sys.prefix).resolve()), base_prefix=str(Path(sys.base_prefix).resolve()),
                module_file=str(Path(worker.__file__).resolve()), process_id=native.identity[0],
                clock_domain_id=supervisor._clock.clock_domain_id, boot_identity_ref=supervisor._clock.boot_identity_ref)
            _native_require(deterministic_json(started) == deterministic_json(expected), "LP03_NATIVE_WORKER_RUNTIME_MISMATCH")
            if causal_scope is not None:
                _WindowsEvidenceProcessV1._exchange_evidence_timeline_v1(native, causal_scope, send, contract)
                return EvidenceProcessSupervisorV1._finish_dispatch_v1(supervisor, native, attempt_grant)
            refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                for selection in grant.allowed_reads for ref in selection.selection.record_refs)
            requested = _WindowsEvidenceProcessV1._receive_v1(native, 1, "READ_REQUEST")
            _native_require(requested["record_refs"] == _evidence_frozen_data_v1(refs), "LP03_WORKER_READ_SCOPE")
            if edge:
                producer_packet = FormulaInputResolverV1.resolve_evidence_v1("MATH-01", attempt_grant=attempt_grant,
                    invocation_ordinal=0, requester_context=supervisor)
            packet = FormulaInputResolverV1.resolve_evidence_v1(math_id, attempt_grant=attempt_grant,
                invocation_ordinal=1 if edge else 0, requester_context=supervisor)
            inputs = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
            from ..stage1_prediction_markets.qku_computation_control_plane.models import _evidence_normalized_event_v1
            if edge:
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
                    _evidence_probability_edge_worker_payload_v1, _require_evidence_probability_edge_result_v1)
                input_payload, normalized_event = _evidence_probability_edge_worker_payload_v1(
                    (producer_packet,packet), attempt, contracts, original_record_refs=refs,
                    frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id in ("MATH-06","MATH-07"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_cashflow_worker_payload_v1
                input_payload, normalized_event = _evidence_cashflow_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id in ("MATH-01", "MATH-04", "MATH-05"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_market_worker_payload_v1
                input_payload, normalized_event = _evidence_market_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-39":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_math39_queue_worker_payload_v1
                input_payload, normalized_event = _evidence_math39_queue_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-27":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_kelly27_worker_payload_v1
                input_payload, normalized_event = _evidence_kelly27_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_original_private_worker_payload_v1
                input_payload, normalized_event = _evidence_original_private_worker_payload_v1(
                    packet, attempt, contract, original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-28":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_kelly28_worker_payload_v1
                input_payload, normalized_event = _evidence_kelly28_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-26":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_research_worker_payload_v1
                input_payload, normalized_event = _evidence_research_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-08":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_forecast_worker_payload_v1
                input_payload, normalized_event = _evidence_forecast_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-09":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_log_loss_worker_payload_v1
                input_payload, normalized_event = _evidence_log_loss_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id in ("MATH-23", "MATH-24", "MATH-25"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_recorded_ope_point_worker_payload_v1
                input_payload, normalized_event = _evidence_recorded_ope_point_worker_payload_v1(
                    packet, attempt, contract, original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-22":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_recorded_dr_worker_payload_v1
                input_payload, normalized_event = _evidence_recorded_dr_worker_payload_v1(
                    packet, attempt, contract, original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
                computations = 2
            elif math_id in ("MATH-20", "MATH-21"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_heldout_worker_payload_v1
                input_payload, normalized_event, scorer_contract = _evidence_heldout_worker_payload_v1(
                    packet, attempt, contract, original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
                computations = worker._heldout_computation_count_v1(math_id, input_payload["inputs"])
            elif math_id == "MATH-19":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_cscv_worker_payload_v1
                input_payload, normalized_event = _evidence_cscv_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id in ("MATH-17", "MATH-18"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_sharpe_worker_payload_v1
                input_payload, normalized_event = _evidence_sharpe_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-16":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_spa_worker_payload_v1
                input_payload, normalized_event = _evidence_spa_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-15":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_reality_check_worker_payload_v1
                input_payload, normalized_event = _evidence_reality_check_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-14":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_bootstrap_worker_payload_v1
                input_payload, normalized_event = _evidence_bootstrap_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-11":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_wilson_worker_payload_v1
                input_payload, normalized_event = _evidence_wilson_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id == "MATH-10":
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_calibration_worker_payload_v1
                input_payload, normalized_event = _evidence_calibration_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            elif math_id in ("MATH-12", "MATH-13"):
                from ..stage1_prediction_markets.qku_computation_control_plane.input_resolver import _evidence_multiple_testing_worker_payload_v1
                input_payload, normalized_event = _evidence_multiple_testing_worker_payload_v1(packet, attempt, contract,
                    original_record_refs=refs, frame_byte_limit=grant.budgets.frame_byte_limit)
            else:
                first_ref = next(value.packet_id for value in inputs.inputs if value.input_name == "best_bid")
                candidates = tuple((part, event) for part in packet._source_slices for event in part.reconstructed_canonical_events
                                   if event["record_ref"] == first_ref)
                _native_require(len(candidates) == 1, "LP03_ORIGINAL_CAUSAL_BOOK_EVENT_REQUIRED")
                part, event = candidates[0]
                source_ref = next(ref for ref in refs if ref["record_id"] == first_ref)
                normalized_event = _evidence_normalized_event_v1(dict(event_id="LP03-EVENT::" + first_ref,
                    kind="SYNTHETIC_BOOK_SNAPSHOT", origin=attempt.grant_record.origin.value, source_record_ref=source_ref,
                    availability_wall_ns=event["native_clocks"]["available_time"], effective_wall_ns=event["native_clocks"]["effective_time"],
                    provider_order_or_absence=event["provider_sequence"], source_revision=event["revision"],
                    connection_epoch=event["source_epoch_id"], local_ordinal=0, payload=event["values"]))
                input_payload = dict(segment_ordinal=0, final_segment=True, inputs=inputs.authoritative_values,
                    original_record_refs=refs, event=normalized_event)
            send("INPUT_SEGMENT", input_payload)
            send("CONTINUE", dict(command="COMPUTE", event_ordinal=0), compute=True)
            result = _WindowsEvidenceProcessV1._receive_v1(native, 2, "COMPUTATION_RESULT")
            _native_require(deterministic_json(result["invocation_contract"]) == deterministic_json(contract)
                            and result["numeric_context_policy_ref"] == LP03_DECIMAL_CONTEXT_POLICY_REF_V1
                            and result["original_record_refs"] == _evidence_frozen_data_v1(refs) and result["event_ordinal"] == 0,
                            "LP03_WORKER_ORIGINAL_INVOCATION_JOIN")
            _WindowsEvidenceProcessV1._require_invocation_measurement_v1(native, result["invocation_measurement"], positive=True)
            if edge:
                _require_evidence_probability_edge_result_v1((producer_packet,packet), attempt, contracts, result,
                    original_record_refs=refs,frame_byte_limit=grant.budgets.frame_byte_limit)
            if math_id in ("MATH-20", "MATH-21"):
                _native_require(deterministic_json(result["scorer_invocation_contract"]) == deterministic_json(scorer_contract),
                    "LP03_NATIVE_HELD_OUT_ORIGINAL_SIGNED_SCORER")
                topology_raw = result["raw_output_json"].encode("utf-8", "strict")
                artifact = worker._evidence_decode_heldout_worker_artifact_v1(
                    result["held_out_score_artifact_json"].encode("utf-8", "strict"),
                    topology_math_id=math_id, topology_raw_json=topology_raw, scorer_contract=scorer_contract,
                    maximum_bytes=grant.budgets.frame_byte_limit, maximum_nodes=4096)
                _, scored_trace = worker._worker_heldout_inputs_v1(input_payload, normalized_event)
                expected = worker._prepare_evidence_heldout_scorer_inputs_v1(topology_math_id=math_id,
                    topology_raw_json=topology_raw, scored_trace=scored_trace, scorer_contract=scorer_contract,
                    maximum_input_bytes=min(grant.budgets.max_input_bytes, grant.budgets.segment_max_bytes),
                    maximum_nodes=4096)
                _native_require(len(expected) == len(artifact["folds"]) == computations - 1,
                    "LP03_NATIVE_HELD_OUT_COMPLETE_RESULT")
                for source, measured_fold in zip(expected, artifact["folds"], strict=True):
                    ordinal, training_ref, sample_refs, _typed_input = source
                    _native_require(measured_fold["ordinal"] == ordinal
                        and measured_fold["training_receipt_ref"] == training_ref
                        and deterministic_json(measured_fold["sample_receipts"]) == deterministic_json(sample_refs),
                        "LP03_NATIVE_HELD_OUT_SCORER_ORIGINAL_INPUT_JOIN")
                    _WindowsEvidenceProcessV1._require_invocation_measurement_v1(
                        native, measured_fold["invocation_measurement"], positive=True)
                EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
            if math_id == "MATH-22":
                artifact, certificate = worker._evidence_decode_recorded_dr_worker_artifact_v1(
                    result["dr_uncertainty_artifact_json"], raw_output_json=result["raw_output_json"],
                    attempt_ref=grant.grant_ref, topology_measurement=result["invocation_measurement"],
                    maximum_bytes=grant.budgets.frame_byte_limit)
                from ..stage1_prediction_markets.qku_computation_control_plane.models import _evidence_dr_original_source_data_v1
                _, typed_input, original_policy, _, original_fit_after_first_label = _evidence_dr_original_source_data_v1(normalized_event["payload"],
                    original_raw_ref=grant.grant_ref+"::DATA::RAW")
                _native_require(deterministic_json(certificate["original_input"]) == deterministic_json(typed_input)
                    and deterministic_json(certificate["original_policy"]) == deterministic_json(original_policy)
                    and (not original_fit_after_first_label or "OUTCOME_LEAKING_NUISANCE_FIT" in certificate["reasons"]),
                    "LP03_NATIVE_DR_ORIGINAL_SOURCE_AND_POLICY_JOIN")
                _WindowsEvidenceProcessV1._require_invocation_measurement_v1(
                    native, artifact["invocation_measurement"], positive=True)
                EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
            segment = _WindowsEvidenceProcessV1._receive_v1(native, 3, "SEGMENT")
            _native_require(dict(segment) == dict(segment_ordinal=0, first_event_ordinal=0, last_event_ordinal=0, computations=computations, complete=True),
                            "LP03_WORKER_SEGMENT_SCOPE")
            send("CONTINUE", dict(command="FINISH", event_ordinal=1))
            native._pipe_original[0][1].close()
            complete = _WindowsEvidenceProcessV1._receive_v1(native, 4, "COMPLETE")
            _native_require(dict(complete) == dict(events=1, computations=computations, segments=1), "LP03_WORKER_COMPLETION_SCOPE")
            native._exchange_original = (packet, contract, result, segment, complete, normalized_event)
            return EvidenceProcessSupervisorV1._finish_dispatch_v1(supervisor, native, attempt_grant)
        except BaseException as original_error:
            trigger_original = EvidenceProcessSupervisorV1._retain_failure_trigger_v1(supervisor, native, original_error)
            failure_reason = EvidenceProcessSupervisorV1._failure_reason_v1(native, original_error, trigger_original=trigger_original)
            if native._terminal_original is None:
                try:
                    EvidenceProcessSupervisorV1.request_stop_v1(supervisor, attempt_grant, reason=failure_reason)
                    EvidenceProcessSupervisorV1.observe_terminal_v1(supervisor, attempt_grant)
                except BaseException as settlement_error:
                    EvidenceProcessSupervisorV1._record_failure_secondary_v1(supervisor, native, settlement_error, stage="DISPATCH_SETTLEMENT")
                    native.phase = "TERMINATION_UNKNOWN"
            EvidenceProcessSupervisorV1._audit_failure_v1(supervisor, native, reason=failure_reason,
                original_error=original_error, trigger_original=trigger_original)
            raise

    def bind_evidence_supervisor_v1(self, *, host_binding, issuer_context):
        """Explicit local conformance composition; creates no process or grant."""
        from ..agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1, EvidenceIssuerContextV1, _EvidenceIssuerStateV1
        from ..stage1_prediction_markets.qku_computation_control_plane.context import _native_require
        from ..stage1_prediction_markets.qku_computation_control_plane.latency_policy import _EvidenceLocalClockV1
        from ..stage1_prediction_markets.qku_computation_control_plane.models import EvidenceOriginV1, EvidenceStoreRoleV1, EvidenceKeyPurposeV1

        _native_require(type(self) is DashboardReadModelService and type(host_binding) is EvidenceHostBindingV1
                        and type(issuer_context) is EvidenceIssuerContextV1, "LP03_SUPERVISOR_ORIGINAL_COMPOSITION")
        state = issuer_context._EvidenceIssuerContextV1__owner
        _native_require(type(state) is _EvidenceIssuerStateV1, "LP03_SUPERVISOR_ORIGINAL_ISSUER")
        EvidenceIssuerContextV1._state_for_owner_v1(issuer_context, state.service)
        with state.lock:
            _native_require(state.operation is None and state.supervisor is None
                            and getattr(self, "_evidence_supervisor_v1", None) is None
                            and type(state.clock) is _EvidenceLocalClockV1, "LP03_SUPERVISOR_ALREADY_BOUND_OR_UNAVAILABLE")
            lifecycle = _EvidenceIssuerStateV1._require_lifecycle_original_v1(state)
            EvidenceHostBindingV1._assert_local_binding_v1(host_binding)
            config, original = host_binding.public_configuration, state.host.public_configuration
            _native_require(config.service_owner == "SVC1" and config.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                            and host_binding.signing_purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER
                            and all(binding.allowed_writer_principal != config.service_principal
                                    for binding in config.store_bindings if binding.role in (
                                        EvidenceStoreRoleV1.READINESS_ACK, EvidenceStoreRoleV1.PRETRADE_ACK,
                                        EvidenceStoreRoleV1.AGENT_ACK, EvidenceStoreRoleV1.SVC_ACK)),
                            "LP03_SUPERVISOR_HOST_ROLE_UNAVAILABLE")
            _native_require((config.deployment_id, config.host_identity, config.package_identity_ref, config.environment_identity,
                             config.generation, config.store_bindings, config.verification_keys)
                            == (original.deployment_id, original.host_identity, original.package_identity_ref,
                                original.environment_identity, original.generation, original.store_bindings, original.verification_keys),
                            "LP03_SUPERVISOR_ORIGINAL_HOST_JOIN")
            result = object.__new__(EvidenceProcessSupervisorV1)
            result._service, result._host, result._issuer, result._clock = self, host_binding, state, state.clock
            result._binding_ref = EvidenceHostBindingV1._nonce_ref_v1(host_binding, "LP03-SUPERVISOR")
            result._instance_ref = lifecycle[0][4]
            result._active, result._unresolved = None, False
            result._retained = ()
            result._capture_originals = ()
            result._unknown_capture_originals = result._no_child_originals = result._creation_originals = ()
            result._cleanup_originals = result._failure_observation_originals = ()
            result._controller_originals = ()
            result._capacity_originals = ()
            result._lane_operation_originals = ()
            result._failure_trigger_originals = ()
            result._lane_platforms = ()
            result._bound_observation = _EvidenceLocalClockV1.observe_v1(state.clock)
            _native_require(_EvidenceIssuerStateV1._require_lifecycle_original_v1(state) is lifecycle,
                            "LP03_SUPERVISOR_LIFECYCLE_CURRENTNESS_CHANGED")
            self._evidence_supervisor_v1 = result
            state.supervisor = result
            state.supervisor_original = (result, self, host_binding, state.clock,
                                         result._binding_ref, result._instance_ref, result._bound_observation)
            return result

    def _path(self, file_name: str) -> Path:
        if file_name not in JSONL_FILES:
            raise KeyError(file_name)
        path = (self.base_dir / file_name).resolve()
        if self.base_dir not in (path, *path.parents):
            raise ValueError(f"SVC1 artifact escapes base directory: {file_name}")
        return path

    def _rows(self, file_name: str) -> tuple[dict[str, Any], ...]:
        if file_name not in self._cache:
            self._cache[file_name] = _read_jsonl(self._path(file_name))
        return self._cache[file_name]

    def _first(self, file_name: str, predicate: Any) -> dict[str, Any]:
        for row in self._rows(file_name):
            if predicate(row):
                return dict(row)
        raise KeyError(file_name)

    def _by_candidate(self, file_name: str, candidate_id: str) -> dict[str, Any]:
        return self._first(file_name, lambda row: row.get("candidate_id") == candidate_id)

    def load_service_manifest(self) -> dict[str, Any]:
        return _read_json((self.base_dir / "service_manifest.json").resolve())

    def list_read_model_snapshots(self) -> tuple[dict[str, Any], ...]:
        return self._rows("read_model_snapshots.generated.jsonl")

    def get_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        return self._first(
            "read_model_snapshots.generated.jsonl",
            lambda row: row.get("snapshot_id") == snapshot_id,
        )

    def list_snapshot_index(self) -> tuple[dict[str, Any], ...]:
        return self._rows("read_model_snapshot_index.generated.jsonl")

    def list_event_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("event_stream_contracts.generated.jsonl")

    def list_action_requests(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_action_requests.generated.jsonl")

    def get_action_eligibility(self, action_code: str, candidate_id: str | None = None) -> dict[str, Any]:
        return self._first(
            "action_eligibility.generated.jsonl",
            lambda row: row.get("action_code") == action_code
            and (candidate_id is None or row.get("candidate_id") == candidate_id),
        )

    def get_action_denied_reason(self, action_code: str, candidate_id: str | None = None) -> dict[str, Any]:
        return self._first(
            "action_denied_reasons.generated.jsonl",
            lambda row: row.get("action_code") == action_code
            and (candidate_id is None or row.get("candidate_id") == candidate_id),
        )

    def get_provider_pending_reason(self, action_code: str, candidate_id: str | None = None) -> dict[str, Any]:
        return self._first(
            "provider_pending_routes.generated.jsonl",
            lambda row: row.get("owner_action_ref_or_gap") == action_code
            or (candidate_id is not None and row.get("candidate_id") == candidate_id),
        )

    def list_action_receipt_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_action_receipts.generated.jsonl")

    def get_pretrade_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("pretrade_view_routes.generated.jsonl", candidate_id)

    def get_no_trade_explanation(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("no_trade_explanation_views.generated.jsonl", candidate_id)

    def get_tca_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("tca_decomposition_views.generated.jsonl", candidate_id)

    def get_execution_adjusted_ranking_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("execution_adjusted_ranking_views.generated.jsonl", candidate_id)

    def get_qku_formula_route_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("qku_formula_compute_route_views.generated.jsonl", candidate_id)

    def get_agent_workflow_preview(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("agent_workflow_queue_views.generated.jsonl", candidate_id)

    def get_llm_grounding_route(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("llm_grounding_route_views.generated.jsonl", candidate_id)

    def get_quantum_readiness_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("quantum_structural_readiness_views.generated.jsonl", candidate_id)

    def get_owner_ux_semantic_route(self, surface_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("owner_ux_semantic_routes.generated.jsonl")
        if surface_id is None:
            return rows
        return tuple(row for row in rows if row.get("owner_read_model_section") == surface_id)

    def get_owner_chart_manifest(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_chart_manifest.generated.jsonl")

    def get_owner_widget_manifest(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_widget_manifest.generated.jsonl")

    def get_agent_operations_view(self, agent_role_or_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("agent_operations_views.generated.jsonl")
        if agent_role_or_id is None:
            return rows
        return tuple(
            row
            for row in rows
            if agent_role_or_id in {str(role) for role in row.get("responsible_agent_role_refs", [])}
        )

    def get_team_workflow_queue(self, stage: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("team_workflow_queue_views.generated.jsonl")
        if stage is None:
            return rows
        return tuple(row for row in rows if row.get("current_stage") == stage)

    def get_owner_audit_trail_preview(
        self,
        candidate_id: str | None = None,
        workflow_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        rows = self._rows("owner_audit_trail_views.generated.jsonl")
        return tuple(
            row
            for row in rows
            if (candidate_id is None or row.get("candidate_id") == candidate_id)
            and (workflow_id is None or row.get("workflow_id_or_gap") == workflow_id)
        )

    def get_execution_status_preview(self, candidate_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("execution_live_status_preview_views.generated.jsonl")
        if candidate_id is None:
            return rows
        return tuple(row for row in rows if row.get("candidate_id") == candidate_id)

    def get_owner_next_step_route(
        self,
        action_id: str,
        current_surface_id: str | None = None,
    ) -> dict[str, Any]:
        return self._first(
            "owner_next_step_routes.generated.jsonl",
            lambda row: row.get("action_id") == action_id
            and (current_surface_id is None or row.get("current_surface_id") == current_surface_id),
        )

    def get_surface_parity_routes(self, surface_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("surface_parity_routes.generated.jsonl")
        if surface_id is None:
            return rows
        return tuple(row for row in rows if row.get("target_surface_id_or_gap") == surface_id)

    def get_artifact_value_route_map(self, artifact_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("artifact_value_route_map.generated.jsonl")
        if artifact_id is None:
            return rows
        return tuple(row for row in rows if artifact_id in str(row.get("projection_ref", "")))

    def get_market_venue_expansion_socket(
        self,
        market_family: str | None = None,
        venue_or_platform_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        rows = self._rows("market_venue_expansion_socket_routes.generated.jsonl")
        return tuple(
            row
            for row in rows
            if (market_family is None or row.get("market_family") == market_family)
            and (
                venue_or_platform_id is None
                or row.get("venue_or_platform_id_or_gap") == venue_or_platform_id
            )
        )

    def get_downstream_routes(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(
            row
            for row in self._rows("downstream_dag_route_views.generated.jsonl")
            if row.get("candidate_id") == candidate_id
        )

    def list_owner_conversation_views(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_conversation_views.generated.jsonl")

    def parse_owner_plain_english_intent_preview(self, text: str) -> dict[str, Any]:
        lowered = text.lower()
        if "why" in lowered and "no-trade" in lowered:
            intent = "NO_TRADE_EXPLANATION_REQUEST"
        elif "formula" in lowered or "qku" in lowered:
            intent = "FORMULA_EXTRACTION_REQUEST"
        elif "quantum" in lowered:
            intent = "QUANTUM_MAPPING_REQUEST"
        elif "replay" in lowered or "paper" in lowered:
            intent = "REPLAY_PAPER_REQUEST"
        elif "article" in lowered or "research" in lowered or "source" in lowered:
            intent = "RESEARCH_ANALYSIS_REQUEST"
        elif "rank" in lowered or "edge" in lowered or "alpha" in lowered:
            intent = "EDGE_ALPHA_RANKING_REQUEST"
        elif "variable" in lowered or "parameter" in lowered:
            intent = "PARAMETER_TUNING_REQUEST"
        else:
            intent = "TRADE_CHECK_REQUEST"
        row = self._first(
            "owner_plain_english_intent_routes.generated.jsonl",
            lambda candidate: candidate.get("intent_class") == intent,
        )
        preview = dict(row)
        preview["plain_english_text_or_ref"] = text
        preview["parser_runtime"] = "DETERMINISTIC_ROUTE_PREVIEW_NO_LLM_CALL"
        return preview

    def list_owner_chat_route_previews(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_chat_route_previews.generated.jsonl")

    def list_owner_research_intake_routes(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_research_intake_routes.generated.jsonl")

    def list_owner_trade_intent_routes(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_trade_intent_routes.generated.jsonl")

    def list_owner_search_index_routes(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_search_index_routes.generated.jsonl")

    def list_owner_layout_profiles(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_layout_profile_routes.generated.jsonl")

    def list_owner_notification_tier_policy(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_notification_tier_policy.generated.jsonl")

    def list_owner_stale_data_banners(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_stale_data_banner_views.generated.jsonl")

    def list_mobile_app_shell_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("mobile_app_shell_contract_views.generated.jsonl")

    def list_mobile_navigation_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("mobile_navigation_contract_views.generated.jsonl")

    def get_trade_workbench_route(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("trade_workbench_route_views.generated.jsonl", candidate_id)

    def get_execution_ladder(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("execution_ladder_stage_views.generated.jsonl", candidate_id)

    def list_ui_visual_qa_handoffs(self) -> tuple[dict[str, Any], ...]:
        return self._rows("ui_visual_qa_handoff_views.generated.jsonl")


class OwnerDashboardAPI(DashboardReadModelService):
    pass


def load_service_manifest(*, base_dir: Path | str | None = None) -> dict[str, Any]:
    return DashboardReadModelService(base_dir).load_service_manifest()


def list_read_model_snapshots(*, base_dir: Path | str | None = None) -> tuple[dict[str, Any], ...]:
    return DashboardReadModelService(base_dir).list_read_model_snapshots()


def resolve_st12g_projection_v2(
    resolution: "ST12GProjectionResolutionV2",
) -> "ST12GOwnerProjectionResolutionV2":
    """Select SVC1 without I/O, core copying, or recomputation."""

    from ..stage1_prediction_markets.qku_computation_control_plane import (
        existing_owner_projection as st12g,
    )

    if type(resolution) is not st12g.ST12GProjectionResolutionV2:
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "SVC1 requires the exact central ST12-G resolution",
        )
    if (
        resolution.resolution_state
        is st12g.ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY
    ):
        bundle = resolution.projection_bundle
        if type(bundle) is not st12g.ST12GProjectionBundleV2 or type(
            bundle.svc
        ) is not st12g.ST12GServiceEvidenceViewV2:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "SVC1 projection is missing from the central bundle",
            )
        payload = bundle.svc
    else:
        payload = resolution.absence
        if type(payload) is not st12g.ST12GProjectionAbsenceV2:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "SVC1 noncurrent resolution must preserve central absence",
            )
    return st12g.ST12GOwnerProjectionResolutionV2(
        consumer_id="SVC1",
        source_request_id=resolution.request_id,
        resolution_state=resolution.resolution_state,
        payload=payload,
    )
