"""Explicit installed Windows entry. Import does not load DLLs or inspect the host.

Native installation/enrollment/device behavior is UNQUALIFIED_NOT_EXECUTED by
synthetic development tests. A protected administrative installation is an
external prerequisite; these checks cannot prove a compromised interpreter honest.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import sys
from types import SimpleNamespace


_ROOTS = {}


def _require(ok):
    if not ok:
        raise RuntimeError("OWNER_SOURCE_USE_NATIVE_BOUNDARY_REJECTED")


class _FileAttributeTag(ctypes.Structure):
    _fields_ = [("attributes", ctypes.c_uint32), ("tag", ctypes.c_uint32)]


class _FileStandard(ctypes.Structure):
    _fields_ = [("allocation", ctypes.c_int64), ("size", ctypes.c_int64), ("links", ctypes.c_uint32),
                ("delete_pending", ctypes.c_ubyte), ("directory", ctypes.c_ubyte)]


class _FileId(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_uint64), ("file_id", ctypes.c_ubyte * 16)]


class _Acl(ctypes.Structure):
    _fields_ = [("revision", ctypes.c_ubyte), ("reserved", ctypes.c_ubyte), ("size", ctypes.c_uint16),
                ("count", ctypes.c_uint16), ("reserved2", ctypes.c_uint16)]


class _SidAttributes(ctypes.Structure):
    _fields_ = [("sid", ctypes.c_void_p), ("attributes", ctypes.c_uint32)]


def _native_system_v1():
    """Fixed System32 libraries and explicit prototypes; no generic native caller."""
    _require(sys.platform == "win32" and ctypes.sizeof(ctypes.c_void_p) == 8)
    k = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
    a = ctypes.WinDLL("advapi32.dll", use_last_error=True, winmode=0x800)
    s = ctypes.WinDLL("shell32.dll", use_last_error=True, winmode=0x800)
    o = ctypes.WinDLL("ole32.dll", use_last_error=True, winmode=0x800)
    h, p, d, b = ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32
    k.GetCurrentProcess.argtypes, k.GetCurrentProcess.restype = [], h
    k.GetCurrentThread.argtypes, k.GetCurrentThread.restype = [], h
    k.GetCurrentProcessId.argtypes, k.GetCurrentProcessId.restype = [], d
    k.CloseHandle.argtypes, k.CloseHandle.restype = [h], b
    k.LocalFree.argtypes, k.LocalFree.restype = [h], h
    k.CreateFileW.argtypes = [ctypes.c_wchar_p, d, d, p, d, d, h]
    k.CreateFileW.restype = h
    k.GetFileType.argtypes, k.GetFileType.restype = [h], d
    k.GetFileInformationByHandleEx.argtypes, k.GetFileInformationByHandleEx.restype = [h, ctypes.c_int32, p, d], b
    k.GetFinalPathNameByHandleW.argtypes, k.GetFinalPathNameByHandleW.restype = [h, ctypes.c_wchar_p, d, d], d
    k.GetDriveTypeW.argtypes, k.GetDriveTypeW.restype = [ctypes.c_wchar_p], d
    k.GetVolumeInformationW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, d, p, p, p, ctypes.c_wchar_p, d]
    k.GetVolumeInformationW.restype = b
    k.ReadFile.argtypes, k.ReadFile.restype = [h, p, d, ctypes.POINTER(d), p], b
    a.OpenProcessToken.argtypes, a.OpenProcessToken.restype = [h, d, ctypes.POINTER(h)], b
    a.OpenThreadToken.argtypes, a.OpenThreadToken.restype = [h, d, b, ctypes.POINTER(h)], b
    a.GetTokenInformation.argtypes, a.GetTokenInformation.restype = [h, ctypes.c_int32, p, d, ctypes.POINTER(d)], b
    a.IsValidSid.argtypes, a.IsValidSid.restype = [p], b
    a.GetLengthSid.argtypes, a.GetLengthSid.restype = [p], d
    a.ConvertSidToStringSidW.argtypes, a.ConvertSidToStringSidW.restype = [p, ctypes.POINTER(p)], b
    a.GetSecurityInfo.argtypes = [h, ctypes.c_int32, d, ctypes.POINTER(p), p, ctypes.POINTER(p), p, ctypes.POINTER(p)]
    a.GetSecurityInfo.restype = d
    a.GetSecurityDescriptorControl.argtypes, a.GetSecurityDescriptorControl.restype = [p, ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(d)], b
    a.GetSecurityDescriptorLength.argtypes, a.GetSecurityDescriptorLength.restype = [p], d
    a.GetSecurityDescriptorDacl.argtypes = [p, ctypes.POINTER(b), ctypes.POINTER(p), ctypes.POINTER(b)]
    a.GetSecurityDescriptorDacl.restype = b
    a.GetAce.argtypes, a.GetAce.restype = [p, d, ctypes.POINTER(p)], b
    s.SHGetKnownFolderPath.argtypes, s.SHGetKnownFolderPath.restype = [p, d, h, ctypes.POINTER(p)], ctypes.c_int32
    o.CoTaskMemFree.argtypes, o.CoTaskMemFree.restype = [p], None
    return SimpleNamespace(kernel=k, security=a, shell=s, ole=o)


def _native_utf16_v1(pointer, units):
    _require(type(units) is int and units > 0 and pointer)
    values = []
    for offset in range(units):
        unit = ctypes.c_uint16.from_address(pointer + offset * 2).value
        values.append(unit)
        if unit == 0:
            raw = b"".join(value.to_bytes(2, "little") for value in values[:-1])
            return raw.decode("utf-16-le", errors="strict"), len(values) * 2
    _require(False)


def _bounded_sid_v1(pointer, start, end):
    # Read no SID byte until the fixed header fits. In particular, a pointer
    # merely inside a TOKEN_USER buffer does not establish a complete SID.
    _require(type(pointer) is int and type(start) is int and type(end) is int
             and start <= pointer and pointer + 8 <= end)
    revision = ctypes.c_ubyte.from_address(pointer).value
    count = ctypes.c_ubyte.from_address(pointer + 1).value
    _require(revision == 1 and count <= 15 and pointer + 8 + count * 4 <= end)
    return 8 + count * 4


def _sid_string_v1(api, pointer):
    _require(pointer and api.security.IsValidSid(pointer))
    length = api.security.GetLengthSid(pointer)
    _require(8 <= length <= 68)
    text = ctypes.c_void_p()
    _require(api.security.ConvertSidToStringSidW(pointer, ctypes.byref(text)))
    try:
        return _native_utf16_v1(text.value, 192)[0]
    finally:
        _require(not api.kernel.LocalFree(text))


def _observe_principal_v1(api):
    handle, thread = ctypes.c_void_p(), ctypes.c_void_p()
    if api.security.OpenThreadToken(api.kernel.GetCurrentThread(), 8, True, ctypes.byref(thread)):
        _require(api.kernel.CloseHandle(thread))
        _require(False)
    _require(ctypes.get_last_error() == 1008)
    _require(api.security.OpenProcessToken(api.kernel.GetCurrentProcess(), 8, ctypes.byref(handle)))
    try:
        observed = {}
        for name, information in (("sid", 1), ("type", 8), ("elevation_type", 18),
                                  ("elevated", 20), ("integrity", 25), ("app_container", 29)):
            length = ctypes.c_uint32()
            first = api.security.GetTokenInformation(handle, information, None, 0, ctypes.byref(length))
            _require(not first and ctypes.get_last_error() == 122 and 4 <= length.value <= 65536)
            data = ctypes.create_string_buffer(length.value)
            capacity = length.value
            _require(api.security.GetTokenInformation(handle, information, data, capacity, ctypes.byref(length))
                     and 4 <= length.value <= capacity)
            if name in {"sid", "integrity"}:
                _require(length.value >= ctypes.sizeof(_SidAttributes))
                sid = _SidAttributes.from_buffer(data).sid
                _bounded_sid_v1(sid, ctypes.addressof(data), ctypes.addressof(data) + length.value)
                observed[name] = _sid_string_v1(api, sid)
            else:
                _require(length.value == 4)
                observed[name] = ctypes.c_uint32.from_buffer(data).value
        return observed
    finally:
        _require(api.kernel.CloseHandle(handle))


def _check_principal_v1(observed):
    _require(type(observed) is dict and set(observed) == {"sid", "type", "elevation_type", "elevated", "integrity", "app_container"})
    _require(type(observed["sid"]) is str and observed["sid"].startswith("S-1-5-21-")
             and type(observed["integrity"]) is str and observed["integrity"] == "S-1-16-8192"
             and all(type(observed[name]) is int for name in ("type", "elevation_type", "elevated", "app_container"))
             and (observed["type"], observed["elevation_type"], observed["elevated"], observed["app_container"]) == (1, 1, 0, 0))
    return observed["sid"]


def _known_folders_v1(api):
    from uuid import UUID

    paths = []
    for fixed in ("905e63b6-c1bf-494e-b29c-65b732d3d21a", "62ab5d82-fdc1-4dc3-a9dd-070d1d495d97"):
        guid = (ctypes.c_ubyte * 16).from_buffer_copy(UUID(fixed).bytes_le)
        pointer = ctypes.c_void_p()
        _require(api.shell.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(pointer)) == 0 and pointer.value)
        try:
            value = _native_utf16_v1(pointer.value, 32768)[0]
        finally:
            api.ole.CoTaskMemFree(pointer)
        _require(len(value) >= 3 and value[1:3] == ":\\" and value[0].isascii() and value[0].isalpha()
                 and not value.startswith("\\") and ":" not in value[2:])
        volume = value[:3]
        filesystem = ctypes.create_unicode_buffer(32)
        _require(api.kernel.GetDriveTypeW(volume) == 3
                 and api.kernel.GetVolumeInformationW(volume, None, 0, None, None, None, filesystem, len(filesystem))
                 and filesystem.value == "NTFS")
        paths.append(Path(value))
    return tuple(paths)


def _observe_acl_v1(api, handle):
    owner, dacl, descriptor = ctypes.c_void_p(), ctypes.c_void_p(), ctypes.c_void_p()
    _require(api.security.GetSecurityInfo(handle, 1, 5, ctypes.byref(owner), None, ctypes.byref(dacl),
                                          None, ctypes.byref(descriptor)) == 0 and descriptor.value)
    try:
        control, revision = ctypes.c_uint16(), ctypes.c_uint32()
        present, defaulted, verified_dacl = ctypes.c_int32(), ctypes.c_int32(), ctypes.c_void_p()
        _require(api.security.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision))
                 and api.security.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(verified_dacl), ctypes.byref(defaulted)))
        descriptor_size = api.security.GetSecurityDescriptorLength(descriptor)
        _require(revision.value == 1 and control.value & 0x8000 and 20 <= descriptor_size <= 65536)
        descriptor_end = descriptor.value + descriptor_size
        _bounded_sid_v1(owner.value, descriptor.value, descriptor_end)
        _require(present.value == 1 and dacl.value and verified_dacl.value == dacl.value)
        _require(descriptor.value <= dacl.value and dacl.value + 8 <= descriptor_end)
        header = _Acl.from_address(dacl.value)
        _require(header.revision == 2 and header.size >= 8 and header.count == 3
                 and dacl.value + header.size <= descriptor_end
                 and header.reserved == header.reserved2 == 0)
        aces = []
        for index in range(header.count):
            pointer = ctypes.c_void_p()
            _require(api.security.GetAce(dacl, index, ctypes.byref(pointer)) and pointer.value)
            _require(dacl.value + 8 <= pointer.value <= dacl.value + header.size - 8)
            ace_type = ctypes.c_ubyte.from_address(pointer.value).value
            flags = ctypes.c_ubyte.from_address(pointer.value + 1).value
            size = ctypes.c_uint16.from_address(pointer.value + 2).value
            _require(16 <= size <= header.size and pointer.value + size <= dacl.value + header.size
                     and ace_type == 0)
            _require(_bounded_sid_v1(pointer.value + 8, pointer.value + 8, pointer.value + size) + 8 == size
                     and api.security.IsValidSid(pointer.value + 8)
                     and api.security.GetLengthSid(pointer.value + 8) + 8 == size)
            mask = ctypes.c_uint32.from_address(pointer.value + 4).value
            aces.append((_sid_string_v1(api, pointer.value + 8), mask, flags, ace_type))
        return {"owner": _sid_string_v1(api, owner.value), "protected": bool(control.value & 0x1000),
                "present": present.value, "defaulted": defaulted.value, "aces": tuple(aces)}
    finally:
        _require(not api.kernel.LocalFree(descriptor))


def _check_acl_v1(acl, sid, directory):
    _require(type(acl) is dict and set(acl) == {"owner", "protected", "present", "defaulted", "aces"}
             and acl["owner"] in {"S-1-5-18", "S-1-5-32-544"} and acl["protected"] is True
             and type(acl["present"]) is int and acl["present"] == 1
             and type(acl["defaulted"]) is int and acl["defaulted"] == 0
             and type(acl["aces"]) is tuple and len(acl["aces"]) == 3)
    expected = {"S-1-5-18": 0x1F01FF, "S-1-5-32-544": 0x1F01FF, sid: 0x1200A9}
    _require(len(expected) == 3)
    seen = set()
    for ace in acl["aces"]:
        _require(type(ace) is tuple and len(ace) == 4)
        principal, mask, flags, kind = ace
        _require(type(principal) is str and principal in expected and principal not in seen
                 and all(type(value) is int for value in (mask, flags, kind))
                 and mask == expected[principal] and kind == 0
                 and flags in ({0, 1, 2, 3} if directory else {0}))
        seen.add(principal)


def _object_state_v1(api, handle, path, directory):
    _require(api.kernel.GetFileType(handle) == 1)
    tag, standard, identity = _FileAttributeTag(), _FileStandard(), _FileId()
    for kind, value in ((9, tag), (1, standard), (18, identity)):
        _require(api.kernel.GetFileInformationByHandleEx(handle, kind, ctypes.byref(value), ctypes.sizeof(value)))
    _require(not tag.attributes & 0x400 and tag.tag == 0 and standard.delete_pending == 0
             and standard.directory in (0, 1) and bool(standard.directory) is directory
             and bool(tag.attributes & 0x10) is directory and standard.size >= 0
             and (directory or standard.links == 1) and any(identity.file_id))
    text = ctypes.create_unicode_buffer(32768)
    count = api.kernel.GetFinalPathNameByHandleW(handle, text, len(text), 0)
    _require(0 < count < len(text) and text.value.startswith("\\\\?\\") and not text.value.startswith("\\\\?\\UNC\\")
             and os.path.normcase(text.value[4:]) == os.path.normcase(str(path)))
    return (identity.volume, bytes(identity.file_id), tag.attributes, standard.size, standard.links, directory)


def _open_control_object_v1(api, path, directory, sid, retained):
    text = str(path)
    _require(path.is_absolute() and len(text) < 32760 and ":" not in text[2:] and not text.startswith("\\"))
    handle = api.kernel.CreateFileW(text, 0x20000 | 0x80 | 1, 1, None, 3,
                                    0x200000 | (0x2000000 if directory else 0), None)
    _require(handle not in (None, ctypes.c_void_p(-1).value))
    retained.append(handle)
    state = _object_state_v1(api, handle, path, directory)
    _check_acl_v1(_observe_acl_v1(api, handle), sid, directory)
    _require(_object_state_v1(api, handle, path, directory) == state)
    return handle, state


def _read_control_bytes_v1(api, handle, size, maximum):
    _require(type(size) is int and 0 < size <= maximum)
    buffer = ctypes.create_string_buffer(size + 1)
    count = ctypes.c_uint32()
    _require(api.kernel.ReadFile(handle, buffer, size + 1, ctypes.byref(count), None) and count.value == size)
    return buffer.raw[:size]


def _check_interpreter_v1(installation):
    runtime = installation / "runtime"
    expected = (runtime / "python314.zip", runtime, installation / "app", installation / "deps")
    _require(sys.version_info[:3] == (3, 14, 6) and sys.platform == "win32" and os.name == "nt"
             and ctypes.sizeof(ctypes.c_void_p) == 8 and getattr(sys.implementation, "_multiarch", None) == "win-amd64"
             and all(getattr(sys.flags, name) == 1 for name in ("isolated", "no_site", "ignore_environment", "safe_path", "dont_write_bytecode"))
             and sys.prefix == sys.base_prefix and sys.exec_prefix == sys.base_exec_prefix
             and os.path.normcase(sys.executable) == os.path.normcase(str(runtime / "pythonw.exe"))
             and tuple(os.path.normcase(str(Path(value))) for value in sys.path)
             == tuple(os.path.normcase(str(value)) for value in expected)
             and os.path.normcase(os.getcwd()) == os.path.normcase(str(runtime))
             and not {"site", "sitecustomize", "usercustomize"}.intersection(sys.modules)
             and len(sys.argv) == 1 and os.path.normcase(sys.argv[0])
             == os.path.normcase(str(installation / "app" / "qtt" / "service" / "owner_source_use_windows.py"))
             and os.path.normcase(__file__) == os.path.normcase(sys.argv[0]))


def _bind_native_module_identity_v1():
    global __package__

    if __name__ == "__main__":
        current = sys.modules["__main__"]
        canonical = "qtt.service.owner_source_use_windows"
        _require(sys.modules.get(canonical) in (None, current))
        sys.modules[canonical] = current
        __package__ = "qtt.service"


class _SourceUseNativeRootV1:
    def __init__(self):
        raise TypeError("native root requires the fixed installed bootstrap")

    def __reduce__(self):
        raise TypeError("native root cannot be serialized")


def _require_native_root_v1(root):
    _require(type(root) is _SourceUseNativeRootV1 and _ROOTS.get(id(root)) is root and not root.closed)


def _bootstrap_owner_source_use_v1():
    api = _native_system_v1()
    retained = []
    try:
        # The independently observed process SID precedes every enrollment/ACL read.
        sid = _check_principal_v1(_observe_principal_v1(api))
        program_files, program_data = _known_folders_v1(api)
        installation = program_files / "QTT" / "OwnerControl"
        _check_interpreter_v1(installation)
        for anchor in (program_files, program_data):
            _open_control_object_v1(api, anchor / "QTT", True, sid, retained)
            _open_control_object_v1(api, anchor / "QTT" / "OwnerControl", True, sid, retained)
        opened = {}
        seen_ids = set()
        stack = [installation]
        while stack:
            directory = stack.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    _require(len(opened) < 65536 and entry.name not in {".", ".."} and ":" not in entry.name)
                    path = directory / entry.name
                    is_directory = entry.is_dir(follow_symlinks=False)
                    handle, state = _open_control_object_v1(api, path, is_directory, sid, retained)
                    _require(state[:2] not in seen_ids)
                    seen_ids.add(state[:2])
                    opened[os.path.normcase(str(path))] = (handle, state)
                    if is_directory:
                        stack.append(path)
        for relative, directory in (("runtime", True), ("app", True), ("deps", True),
            ("runtime/pythonw.exe", False), ("runtime/python314.zip", False),
            ("runtime/python314._pth", False), ("app/qtt/service/owner_source_use_windows.py", False)):
            required = opened.get(os.path.normcase(str(installation / relative)))
            _require(required is not None and required[1][5] is directory)
        pth = installation / "runtime" / "python314._pth"
        handle, state = opened[os.path.normcase(str(pth))]
        pth_raw = _read_control_bytes_v1(api, handle, state[3], 256)
        _require(pth_raw in (b"python314.zip\n.\n../app\n../deps\n", b"python314.zip\r\n.\r\n../app\r\n../deps\r\n")
                 and _object_state_v1(api, handle, pth, False) == state)
        config = program_data / "QTT" / "OwnerControl" / "enrollment.json"
        handle, state = _open_control_object_v1(api, config, False, sid, retained)
        raw = _read_control_bytes_v1(api, handle, state[3], 65536)
        _require(_object_state_v1(api, handle, config, False) == state)
        _bind_native_module_identity_v1()
        # Only now are protected QTT and third-party imports reachable.
        from .owner_source_use import _read_public_enrollment_v1

        enrollment = _read_public_enrollment_v1(raw)
        _require(enrollment.approval_sid == sid and enrollment.root_state != "DISABLED")
        root = object.__new__(_SourceUseNativeRootV1)
        root.api, root.handles, root.enrollment, root.sid = api, retained, enrollment, sid
        root.closed, root.operation = False, None
        from threading import RLock

        root.operation_lock = RLock()
        root.window = None
        root.completion_worker = None
        root.completed = {}
        _ROOTS[id(root)] = root
        return root
    except BaseException:
        for handle in reversed(retained):
            api.kernel.CloseHandle(handle)
        raise


def _close_native_root_v1(root):
    _require_native_root_v1(root)
    _require(root.operation is None or not root.operation.worker.is_alive())
    _require(root.completion_worker is None or not root.completion_worker.is_alive())
    failures = []
    for handle in reversed(root.handles):
        if not root.api.kernel.CloseHandle(handle):
            failures.append(handle)
    root.closed = True
    root.handles = list(reversed(failures))
    if not failures:
        _ROOTS.pop(id(root), None)
    _require(not failures)


def _require_completed_operation_v1(root, pending_ref, raw):
    _require_native_root_v1(root)
    with root.operation_lock:
        result = root.completed.pop(pending_ref, None)
    _require(result is not None and result[0] is raw and result[1] == root.sid and result[2] == root.sid)


# Non-owning ABI views only. Win32 DWORD/BOOL/LONG stay 32 bits on every
# synthetic host; no library output class, descriptor or destructor is used.
class _RawCredential(ctypes.Structure):
    _fields_ = [("dwVersion", ctypes.c_uint32), ("cbId", ctypes.c_uint32),
                ("pbId", ctypes.c_void_p), ("pwszCredentialType", ctypes.c_void_p)]


class _RawExtensions(ctypes.Structure):
    _fields_ = [("cExtensions", ctypes.c_uint32), ("pExtensions", ctypes.c_void_p)]


_D, _B, _P = ctypes.c_uint32, ctypes.c_int32, ctypes.c_void_p
_ASSERTION_FIELDS = (
    (1, "dwVersion", _D), (1, "cbAuthenticatorData", _D), (1, "pbAuthenticatorData", _P),
    (1, "cbSignature", _D), (1, "pbSignature", _P), (1, "Credential", _RawCredential),
    (1, "cbUserId", _D), (1, "pbUserId", _P), (2, "Extensions", _RawExtensions),
    (2, "cbCredLargeBlob", _D), (2, "pbCredLargeBlob", _P), (2, "dwCredLargeBlobStatus", _D),
    (3, "pHmacSecret", _P), (4, "dwUsedTransports", _D),
    (5, "cbUnsignedExtensionOutputs", _D), (5, "pbUnsignedExtensionOutputs", _P),
    (6, "cbClientDataJSON", _D), (6, "pbClientDataJSON", _P),
    (6, "cbAuthenticationResponseJSON", _D), (6, "pbAuthenticationResponseJSON", _P),
)
_ATTESTATION_FIELDS = (
    (1, "dwVersion", _D), (1, "pwszFormatType", _P),
    (1, "cbAuthenticatorData", _D), (1, "pbAuthenticatorData", _P),
    (1, "cbAttestation", _D), (1, "pbAttestation", _P),
    (1, "dwAttestationDecodeType", _D), (1, "pvAttestationDecode", _P),
    (1, "cbAttestationObject", _D), (1, "pbAttestationObject", _P),
    (1, "cbCredentialId", _D), (1, "pbCredentialId", _P),
    (2, "Extensions", _RawExtensions), (3, "dwUsedTransport", _D),
    (4, "bEpAtt", _B), (4, "bLargeBlobSupported", _B), (4, "bResidentKey", _B),
    (5, "bPrfEnabled", _B), (6, "cbUnsignedExtensionOutputs", _D), (6, "pbUnsignedExtensionOutputs", _P),
    (7, "pHmacSecret", _P), (7, "bThirdPartyPayment", _B), (8, "dwTransports", _D),
    (8, "cbClientDataJSON", _D), (8, "pbClientDataJSON", _P),
    (8, "cbRegistrationResponseJSON", _D), (8, "pbRegistrationResponseJSON", _P),
)
_ASSERTION_VIEWS = {version: type(f"_RawAssertion{version}", (ctypes.Structure,), {
    "_fields_": [(name, kind) for minimum, name, kind in _ASSERTION_FIELDS if minimum <= version]
}) for version in range(1, 7)}
_ATTESTATION_VIEWS = {version: type(f"_RawAttestation{version}", (ctypes.Structure,), {
    "_fields_": [(name, kind) for minimum, name, kind in _ATTESTATION_FIELDS if minimum <= version]
}) for version in range(1, 9)}


def _check_output_layouts_v1(library=None):
    # Independent Windows-x64 ABI expectations, not values derived from either
    # implementation under test. Synthetic comparisons do not qualify Windows.
    assertion_offsets = (0, 4, 8, 16, 24, 32, 56, 64, 72, 88, 96, 104, 112, 120, 124, 128, 136, 144, 152, 160)
    attestation_offsets = (0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 112, 116, 120, 124, 128,
                           132, 136, 144, 152, 156, 160, 168, 176, 184)
    for views, fields, sizes, offsets in (
        (_ASSERTION_VIEWS, _ASSERTION_FIELDS, (72, 112, 120, 128, 136, 168), assertion_offsets),
        (_ATTESTATION_VIEWS, _ATTESTATION_FIELDS, (96, 112, 120, 128, 136, 144, 160, 192), attestation_offsets),
    ):
        for version, view in views.items():
            _require(ctypes.sizeof(view) == sizes[version - 1])
            for (minimum, name, _), offset in zip(fields, offsets, strict=True):
                if minimum <= version:
                    _require(getattr(view, name).offset == offset)
    if library is not None:
        for original, view in ((library.WebAuthNAssertion, _ASSERTION_VIEWS[6]),
                               (library.WebAuthNCredentialAttestation, _ATTESTATION_VIEWS[8])):
            _require(ctypes.sizeof(original) == ctypes.sizeof(view)
                     and [name for name, _ in original._fields_] == [name for name, _ in view._fields_])
            for name, kind in original._fields_:
                field = getattr(original, name)
                _require(field.offset == getattr(view, name).offset and field.size == getattr(view, name).size)


def _scan_response_string_v1(pointer):
    _require(pointer)
    for offset in range(64):
        if ctypes.c_uint16.from_address(pointer + 2 * offset).value == 0:
            return 2 * (offset + 1)
    _require(False)


def _copy_native_response_v1(pointer, operation, client_data):
    """Called only with the original OS-returned output, never proposal pointers.

    The cap bounds QTT application copies/parsing, not the OS's own allocations
    or parsing before the native operation returns. All buffers are budgeted
    before copying or constructing any FIDO/CBOR/JSON response object.
    """
    _require(type(pointer) is int and pointer != 0 and operation in {"GET", "CREATE"}
             and type(client_data) is bytes and 0 < len(client_data) <= 65536)
    version = ctypes.c_uint32.from_address(pointer).value
    views = _ASSERTION_VIEWS if operation == "GET" else _ATTESTATION_VIEWS
    _require(version in views)
    response = views[version].from_address(pointer)
    fields = [("auth", response.cbAuthenticatorData, response.pbAuthenticatorData)]
    string_pointer = None
    if operation == "GET":
        _require(response.Credential.dwVersion == 1 and response.cbAuthenticatorData == 37)
        fields.extend((("signature", response.cbSignature, response.pbSignature),
                       ("id", response.Credential.cbId, response.Credential.pbId),
                       ("user", response.cbUserId, response.pbUserId)))
        string_pointer = response.Credential.pwszCredentialType
        if version >= 2:
            _require(response.Extensions.cExtensions == 0 and not response.Extensions.pExtensions
                     and response.cbCredLargeBlob == 0 and not response.pbCredLargeBlob
                     and response.dwCredLargeBlobStatus == 0)
        if version >= 3:
            _require(not response.pHmacSecret)
        if version >= 4:
            _require(response.dwUsedTransports == 0x10)
        if version >= 5:
            _require(response.cbUnsignedExtensionOutputs == 0 and not response.pbUnsignedExtensionOutputs)
        if version >= 6:
            fields.extend((("client", response.cbClientDataJSON, response.pbClientDataJSON),
                           ("json", response.cbAuthenticationResponseJSON, response.pbAuthenticationResponseJSON)))
    else:
        fields.extend((("attestation", response.cbAttestation, response.pbAttestation),
                       ("object", response.cbAttestationObject, response.pbAttestationObject),
                       ("id", response.cbCredentialId, response.pbCredentialId)))
        string_pointer = response.pwszFormatType
        _require(response.dwAttestationDecodeType == 0 and not response.pvAttestationDecode)
        if version >= 2:
            _require(response.Extensions.cExtensions == 0 and not response.Extensions.pExtensions)
        if version >= 3:
            _require(response.dwUsedTransport == 0x10)
        if version >= 4:
            _require(response.bEpAtt == 0 and response.bLargeBlobSupported in (0, 1) and response.bResidentKey in (0, 1))
        if version >= 5:
            _require(response.bPrfEnabled == 0)
        if version >= 6:
            _require(response.cbUnsignedExtensionOutputs == 0 and not response.pbUnsignedExtensionOutputs)
        if version >= 7:
            _require(not response.pHmacSecret and response.bThirdPartyPayment == 0)
        if version >= 8:
            _require(response.dwTransports == 0x10)
            fields.extend((("client", response.cbClientDataJSON, response.pbClientDataJSON),
                           ("json", response.cbRegistrationResponseJSON, response.pbRegistrationResponseJSON)))
    total = len(client_data)
    for _, size, address in fields:
        _require(type(size) is int and 0 <= size <= 65536 and (size == 0 or address))
        total += size
    _require(total <= 65536)
    string_size = _scan_response_string_v1(string_pointer)
    _require(total + string_size <= 65536)
    text = ctypes.string_at(string_pointer, string_size - 2).decode("utf-16-le", errors="strict")
    _require(text == ("public-key" if operation == "GET" else "none"))
    copied = {name: ctypes.string_at(address, size) if size else b"" for name, size, address in fields}
    _require(copied.get("client", client_data) in (b"", client_data))
    from .owner_source_use import _RawSourceUseResponseV1, _closed_json_v1, _b64_v1

    if operation == "CREATE":
        from fido2 import cbor

        if copied["attestation"]:
            decoded = cbor.decode(copied["attestation"])
            _require(type(decoded) is dict and not decoded and cbor.encode(decoded) == copied["attestation"])
    if copied.get("json"):
        redundant = _closed_json_v1(copied["json"], 65536)
        _require(set(redundant) <= {"id", "rawId", "type", "response", "clientExtensionResults", "authenticatorAttachment"}
                 and {"id", "rawId", "type", "response"} <= set(redundant)
                 and redundant["id"] == redundant["rawId"] == _b64_v1(copied["id"])
                 and redundant["type"] == "public-key"
                 and redundant.get("authenticatorAttachment", "platform") == "platform"
                 and type(redundant.get("clientExtensionResults", {})) is dict and not redundant.get("clientExtensionResults", {}))
        nested = redundant["response"]
        expected = {"clientDataJSON": _b64_v1(client_data)}
        if operation == "GET":
            expected.update(authenticatorData=_b64_v1(copied["auth"]), signature=_b64_v1(copied["signature"]))
            _require(type(nested) is dict and set(nested) in (set(expected), set(expected) | {"userHandle"}))
            if "userHandle" in nested:
                expected["userHandle"] = _b64_v1(copied["user"]) if copied["user"] else None
        else:
            expected["attestationObject"] = _b64_v1(copied["object"])
        _require(type(nested) is dict and nested == expected)
    return _RawSourceUseResponseV1(operation, copied["id"], client_data, copied["auth"],
        copied["signature"] if operation == "GET" else None,
        copied["user"] or None if operation == "GET" else None,
        copied["object"] if operation == "CREATE" else None)


def _webauthn_table_v1(root):
    _require_native_root_v1(root)
    w = ctypes.WinDLL("webauthn.dll", use_last_error=True, winmode=0x800)
    w.WebAuthNGetApiVersionNumber.argtypes, w.WebAuthNGetApiVersionNumber.restype = [], ctypes.c_uint32
    version = w.WebAuthNGetApiVersionNumber()
    _require(type(version) is int and 1 <= version <= 9)
    # The pinned module itself loads System32 WebAuthn and observes API version.
    # It is imported only here, after bootstrap; its global prototypes stay intact.
    from fido2.client import win_api

    _require(win_api.WEBAUTHN_API_VERSION == version)
    _check_output_layouts_v1(win_api)
    h, p, hr = ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32
    w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable.argtypes = [ctypes.POINTER(ctypes.c_int32)]
    w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable.restype = hr
    w.WebAuthNGetCancellationId.argtypes, w.WebAuthNGetCancellationId.restype = [ctypes.POINTER(win_api.GUID)], hr
    w.WebAuthNCancelCurrentOperation.argtypes, w.WebAuthNCancelCurrentOperation.restype = [ctypes.POINTER(win_api.GUID)], hr
    w.WebAuthNAuthenticatorMakeCredential.argtypes = [h, ctypes.POINTER(win_api.WebAuthNRpEntityInformation),
        ctypes.POINTER(win_api.WebAuthNUserEntityInformation), ctypes.POINTER(win_api.WebAuthNCoseCredentialParameters),
        ctypes.POINTER(win_api.WebAuthNClientData), ctypes.POINTER(win_api.WebAuthNMakeCredentialOptions), ctypes.POINTER(p)]
    w.WebAuthNAuthenticatorMakeCredential.restype = hr
    w.WebAuthNAuthenticatorGetAssertion.argtypes = [h, ctypes.c_wchar_p,
        ctypes.POINTER(win_api.WebAuthNClientData), ctypes.POINTER(win_api.WebAuthNGetAssertionOptions), ctypes.POINTER(p)]
    w.WebAuthNAuthenticatorGetAssertion.restype = hr
    w.WebAuthNFreeCredentialAttestation.argtypes, w.WebAuthNFreeCredentialAttestation.restype = [p], None
    w.WebAuthNFreeAssertion.argtypes, w.WebAuthNFreeAssertion.restype = [p], None
    available = ctypes.c_int32()
    _require(w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable(ctypes.byref(available)) == 0 and available.value == 1)
    return w, win_api


def _check_owned_window_v1(root):
    _require_native_root_v1(root)
    window = root.window
    _require(window is not None and window.root is root and window.hwnd
             and window.user.IsWindow(window.hwnd))
    process = ctypes.c_uint32()
    thread = window.user.GetWindowThreadProcessId(window.hwnd, ctypes.byref(process))
    _require(thread != 0 and process.value == root.api.kernel.GetCurrentProcessId())
    return window


def _acquire_native_response_v1(root, operation):
    import time
    from .owner_source_use import _source_use_b64_v1

    _require_native_root_v1(root)
    window = _check_owned_window_v1(root)
    before = _check_principal_v1(_observe_principal_v1(root.api))
    _require(before == root.sid)
    library, table = operation.library, operation.table
    authentication = operation.authentication
    remaining_ms = (operation.deadline - time.monotonic_ns()) // 1_000_000
    _require(1 <= remaining_ms <= 120000)
    client = library.WebAuthNClientData(authentication.client_data)
    pointer = ctypes.c_void_p()
    operation.keepalive = [window, operation.guid, client]
    try:
        if authentication.operation == "GET":
            options = library.WebAuthNGetAssertionOptions(timeout=remaining_ms,
                attachment=library.WebAuthNAuthenticatorAttachment.PLATFORM,
                uv_requirement=library.WebAuthNUserVerificationRequirement.REQUIRED,
                credentials=[{"id": _source_use_b64_v1(authentication.enrollment.key_id_b64, maximum=1024),
                              "type": "public-key", "transport": "INTERNAL"}],
                cancellationId=operation.guid, extensions=[], flags=0,
                cred_large_blob_operation=library.WebAuthNLargeBlobOperation.NONE)
            operation.keepalive.append(options)
            result = table.WebAuthNAuthenticatorGetAssertion(window.hwnd, "localhost", ctypes.byref(client),
                ctypes.byref(options), ctypes.byref(pointer))
        else:
            options = library.WebAuthNMakeCredentialOptions(timeout=remaining_ms,
                require_resident_key=False, prefer_resident_key=False,
                attachment=library.WebAuthNAuthenticatorAttachment.PLATFORM,
                uv_requirement=library.WebAuthNUserVerificationRequirement.REQUIRED,
                attestation_convoyence=library.WebAuthNAttestationConveyancePreference.NONE,
                credentials=[], cancellationId=operation.guid, extensions=[],
                enterprise_attestation=library.WebAuthNEnterpriseAttestation.NONE,
                large_blob_support=library.WebAuthNLargeBlobSupport.NONE, enable_prf=False)
            rp = library.WebAuthNRpEntityInformation({"id": "localhost", "name": "QTT Owner Source Use"})
            user = library.WebAuthNUserEntityInformation({"id": _source_use_b64_v1(
                authentication.enrollment.user_handle_b64, minimum=32, maximum=32),
                "name": authentication.enrollment.owner_ref, "displayName": authentication.enrollment.owner_ref})
            algorithms = library.WebAuthNCoseCredentialParameters([{"type": "public-key", "alg": -7}])
            operation.keepalive.extend((options, rp, user, algorithms))
            result = table.WebAuthNAuthenticatorMakeCredential(window.hwnd, ctypes.byref(rp), ctypes.byref(user),
                ctypes.byref(algorithms), ctypes.byref(client), ctypes.byref(options), ctypes.byref(pointer))
        _require(result == 0 and pointer.value)
        after = _check_principal_v1(_observe_principal_v1(root.api))
        _require(after == before == root.sid)
        raw = _copy_native_response_v1(pointer.value, authentication.operation, authentication.client_data)
        return raw, before, after
    finally:
        if pointer.value:
            if authentication.operation == "GET":
                table.WebAuthNFreeAssertion(pointer)
            else:
                table.WebAuthNFreeCredentialAttestation(pointer)


def _start_native_operation_v1(root, pending_ref, authentication, deadline):
    from threading import Thread

    _require_native_root_v1(root)
    _check_owned_window_v1(root)
    with root.operation_lock:
        _require(root.operation is None)
    table, library = _webauthn_table_v1(root)
    guid = library.GUID()
    _require(table.WebAuthNGetCancellationId(ctypes.byref(guid)) == 0)
    operation = SimpleNamespace(root=root, pending_ref=pending_ref, authentication=authentication,
        deadline=deadline, table=table, library=library, guid=guid, keepalive=[], result=None,
        error=None, cancelled=False, terminal=False)

    def worker():
        try:
            result = _acquire_native_response_v1(root, operation)
            with root.operation_lock:
                operation.result = result
        except BaseException:
            with root.operation_lock:
                operation.error = "NATIVE_AUTHENTICATION_REJECTED"
        finally:
            with root.operation_lock:
                operation.terminal = True

    operation.worker = Thread(target=worker, name="QTT-owner-authentication", daemon=False)
    with root.operation_lock:
        _require(root.operation is None)
        root.operation = operation
    try:
        operation.worker.start()
    except BaseException:
        with root.operation_lock:
            root.operation = None
        raise


def _cancel_native_operation_v1(root):
    _require_native_root_v1(root)
    with root.operation_lock:
        operation = root.operation
        if operation is None:
            return
        if operation.cancelled:
            return
        operation.cancelled = True
        terminal = operation.terminal
    if not terminal:
        # Cancellation is a request, never proof of termination. The window and
        # inputs stay owned until the worker has actually returned and joined.
        result = operation.table.WebAuthNCancelCurrentOperation(ctypes.byref(operation.guid))
        _require(result == 0)


def _take_native_completion_v1(root):
    _require_native_root_v1(root)
    with root.operation_lock:
        operation = root.operation
        if operation is None or not operation.terminal:
            return None
    operation.worker.join(timeout=0)
    if operation.worker.is_alive():
        return None
    with root.operation_lock:
        _require(root.operation is operation)
        root.operation = None
        if operation.error is not None or operation.cancelled:
            return operation.pending_ref, None, "CANCELLED" if operation.cancelled else operation.error
        _require(operation.result is not None)
        root.completed[operation.pending_ref] = operation.result
        return operation.pending_ref, operation.result[0], None


def _user_table_v1():
    user = ctypes.WinDLL("user32.dll", use_last_error=True, winmode=0x800)
    h, p, b, d, word = ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32, ctypes.c_uint32, ctypes.c_size_t
    result = ctypes.c_ssize_t
    user.IsWindow.argtypes, user.IsWindow.restype = [h], b
    user.GetWindowThreadProcessId.argtypes, user.GetWindowThreadProcessId.restype = [h, ctypes.POINTER(d)], d
    user.RegisterClassExW.argtypes, user.RegisterClassExW.restype = [p], ctypes.c_uint16
    user.UnregisterClassW.argtypes, user.UnregisterClassW.restype = [ctypes.c_wchar_p, h], b
    user.CreateWindowExW.argtypes = [d, ctypes.c_wchar_p, ctypes.c_wchar_p, d, b, b, b, b, h, h, h, p]
    user.CreateWindowExW.restype = h
    user.DefWindowProcW.argtypes, user.DefWindowProcW.restype = [h, d, word, result], result
    user.DestroyWindow.argtypes, user.DestroyWindow.restype = [h], b
    user.ShowWindow.argtypes, user.ShowWindow.restype = [h, b], b
    user.UpdateWindow.argtypes, user.UpdateWindow.restype = [h], b
    user.GetMessageW.argtypes, user.GetMessageW.restype = [p, h, d, d], b
    user.TranslateMessage.argtypes, user.TranslateMessage.restype = [p], b
    user.DispatchMessageW.argtypes, user.DispatchMessageW.restype = [p], result
    user.PostQuitMessage.argtypes, user.PostQuitMessage.restype = [b], None
    user.SetWindowTextW.argtypes, user.SetWindowTextW.restype = [h, ctypes.c_wchar_p], b
    user.GetWindowTextLengthW.argtypes, user.GetWindowTextLengthW.restype = [h], b
    user.GetWindowTextW.argtypes, user.GetWindowTextW.restype = [h, ctypes.c_wchar_p, b], b
    user.EnableWindow.argtypes, user.EnableWindow.restype = [h, b], b
    user.SendMessageW.argtypes, user.SendMessageW.restype = [h, d, word, result], result
    user.SetTimer.argtypes, user.SetTimer.restype = [h, word, d, p], word
    user.KillTimer.argtypes, user.KillTimer.restype = [h, word], b
    user.MessageBoxW.argtypes, user.MessageBoxW.restype = [h, ctypes.c_wchar_p, ctypes.c_wchar_p, d], b
    user.SetWindowLongPtrW.argtypes, user.SetWindowLongPtrW.restype = [h, b, result], result
    user.CallWindowProcW.argtypes, user.CallWindowProcW.restype = [p, h, d, word, result], result
    return user


def _display_text_v1(text):
    import unicodedata

    _require(type(text) is str)
    return "".join(f"\\u{ord(character):04x}" if (unicodedata.category(character) == "Cf"
                    or (ord(character) < 32 and character not in "\r\n\t") or 127 <= ord(character) < 160)
                   else character for character in text)


def _run_local_window_v1(root, controller):
    import json
    import time
    from threading import Thread

    _require_native_root_v1(root)
    user = _user_table_v1()
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_size_t, ctypes.c_ssize_t)

    class WindowClass(ctypes.Structure):
        _fields_ = [("size", ctypes.c_uint32), ("style", ctypes.c_uint32), ("procedure", callback_type),
                    ("class_extra", ctypes.c_int32), ("window_extra", ctypes.c_int32), ("instance", ctypes.c_void_p),
                    ("icon", ctypes.c_void_p), ("cursor", ctypes.c_void_p), ("background", ctypes.c_void_p),
                    ("menu", ctypes.c_wchar_p), ("name", ctypes.c_wchar_p), ("small_icon", ctypes.c_void_p)]

    class Message(ctypes.Structure):
        _fields_ = [("window", ctypes.c_void_p), ("message", ctypes.c_uint32), ("wparam", ctypes.c_size_t),
                    ("lparam", ctypes.c_ssize_t), ("time", ctypes.c_uint32), ("x", ctypes.c_int32),
                    ("y", ctypes.c_int32), ("private", ctypes.c_uint32)]

    window = SimpleNamespace(root=root, user=user, hwnd=None, controls={}, closing=False, failed=False,
                             completion=None, completion_error=None, result_procedure=None)
    root.window = window

    def set_text(control, text):
        _require(user.SetWindowTextW(window.controls[control], _display_text_v1(text)))

    def busy():
        return root.operation is not None or root.completion_worker is not None

    def enable_inputs():
        enabled = not busy() and not window.closing and not controller._closed
        for control in (10, 11, 12, 16):
            user.EnableWindow(window.controls[control], enabled)
        user.EnableWindow(window.controls[12], enabled and controller._pending_ref is not None)
        user.EnableWindow(window.controls[16], enabled and controller._authority is None and controller._enrollment_stage is None)

    def stop(closing):
        window.closing = window.closing or closing
        try:
            controller.stop_v1()
        except BaseException:
            window.failed = True
        enable_inputs()
        if window.closing and not busy():
            _require(user.DestroyWindow(window.hwnd))

    def completion_worker(reference, raw):
        try:
            completed = controller.complete_action_v1(reference, raw)
            with root.operation_lock:
                window.completion = completed
        except BaseException:
            with root.operation_lock:
                window.completion_error = "ACTION_REJECTED"

    def timer():
        if root.operation is not None and time.monotonic_ns() >= root.operation.deadline:
            try:
                controller.cancel_v1()
            except BaseException:
                window.failed = True
        completed = _take_native_completion_v1(root)
        if completed is not None:
            reference, raw, error = completed
            if error is not None:
                controller.cancel_v1()
                set_text(15, error)
            elif controller._authority is None:
                candidate = controller._complete_enrollment_v1(reference, raw)
                if candidate is not None:
                    set_text(13, "PUBLIC ENROLLMENT CANDIDATE — ADMINISTRATIVE INSTALLATION REQUIRED\r\n" + candidate)
            else:
                window.completion = window.completion_error = None
                root.completion_worker = Thread(target=completion_worker, args=(reference, raw),
                                                 name="QTT-owner-action", daemon=False)
                root.completion_worker.start()
        worker = root.completion_worker
        if worker is not None and not worker.is_alive():
            worker.join(timeout=0)
            _require(not worker.is_alive())
            root.completion_worker = None
            with root.operation_lock:
                failed = window.completion_error is not None
            if failed:
                set_text(15, "ACTION_REJECTED; prior published results remain historical")
            elif controller._result is not None:
                try:
                    model = controller._display_result_v1()
                    set_text(14, json.dumps(dict(model), ensure_ascii=False, indent=2))
                except BaseException:
                    set_text(15, "RESULT_NOT_CURRENT; no new result display authorized")
        set_text(15, json.dumps(dict(controller.read_status_v1()), ensure_ascii=True))
        enable_inputs()
        if window.closing and not busy():
            _require(user.DestroyWindow(window.hwnd))

    def command(control):
        if control == 17:
            stop(True)
        elif control == 18:
            stop(False)
        elif control == 19:
            controller.cancel_v1()
            enable_inputs()
        elif control == 11:
            _require(not busy())
            length = user.GetWindowTextLengthW(window.controls[10])
            _require(0 < length <= 262144)
            buffer = ctypes.create_unicode_buffer(length + 1)
            _require(user.GetWindowTextW(window.controls[10], buffer, len(buffer)) == length)
            raw = buffer.value.encode("utf-8", errors="strict")
            _require(len(raw) <= 262144)
            _, preview = controller.prepare_action_v1(raw)
            set_text(13, preview)
            enable_inputs()
        elif control == 12:
            _require(not busy() and controller._preview is not None)
            if user.MessageBoxW(window.hwnd, "Confirm the complete displayed action and its explicit effects?",
                                "QTT Owner Source Use", 0x24) == 6:
                controller._confirm_prepared_v1()
                enable_inputs()
        elif control == 16:
            _require(not busy())
            if user.MessageBoxW(window.hwnd,
                "Create a platform public key with user verification, then prove possession. This only produces a public enrollment candidate; it grants no source use.",
                "QTT Owner Source Use", 0x24) == 6:
                controller._begin_enrollment_v1()
                enable_inputs()

    @callback_type
    def procedure(hwnd, message, wparam, lparam):
        try:
            if message == 0x111:  # WM_COMMAND; no data-bearing custom messages.
                if (wparam & 0xFFFF) == 10 and (wparam >> 16) == 0x300:  # EN_CHANGE
                    if controller._pending_ref is not None:
                        controller.cancel_v1()
                        set_text(13, "Input changed; prepare and confirm the complete new action.")
                        enable_inputs()
                    return 0
                command(wparam & 0xFFFF)
                return 0
            if message == 0x113:
                timer()
                return 0
            if message == 0x10:
                stop(True)
                return 0
            if message == 2:
                user.KillTimer(hwnd, 1)
                user.PostQuitMessage(0)
                return 0
        except BaseException:
            window.failed = True
            try:
                controller.cancel_v1()
                if window.controls:
                    set_text(15, "LOCAL_ACTION_REJECTED")
                    enable_inputs()
            except BaseException:
                try:
                    controller.stop_v1()
                except BaseException:
                    pass
            return 0
        return user.DefWindowProcW(hwnd, message, wparam, lparam)

    specification = WindowClass()
    specification.size, specification.procedure = ctypes.sizeof(specification), procedure
    specification.name, specification.background = "QTT.OwnerSourceUse.V1", 6
    _require(user.RegisterClassExW(ctypes.byref(specification)))
    try:
        window.hwnd = user.CreateWindowExW(0, specification.name, "QTT Owner Source Use", 0x00CA0000,
            80, 60, 1000, 840, None, None, None, None)
        _require(window.hwnd)
        for control, kind, title, x, y, width, height, extra in (
            (10, "EDIT", "", 15, 15, 950, 155, 0x003010C4),
            (11, "BUTTON", "Prepare action", 15, 180, 145, 30, 0),
            (12, "BUTTON", "Confirm with verification", 170, 180, 220, 30, 0),
            (16, "BUTTON", "Enroll public key", 400, 180, 160, 30, 0),
            (19, "BUTTON", "Cancel", 570, 180, 100, 30, 0),
            (18, "BUTTON", "Stop", 680, 180, 100, 30, 0),
            (17, "BUTTON", "Close", 790, 180, 100, 30, 0),
            (13, "EDIT", "Review all displayed source facts, scope, times and financial inputs before confirmation.", 15, 220, 950, 245, 0x003018C4),
            (14, "EDIT", "No observation result.", 15, 475, 950, 240, 0x003018C4),
            (15, "STATIC", "DENIED — no current source-use admission", 15, 725, 950, 60, 0),
        ):
            handle = user.CreateWindowExW(0, kind, title, 0x50000000 | extra, x, y, width, height,
                                         window.hwnd, control, None, None)
            _require(handle)
            window.controls[control] = handle
        user.SendMessageW(window.controls[10], 0xC5, 262144, 0)
        for control in (13, 14):
            user.SendMessageW(window.controls[control], 0xC5, 0x7FFFFFFE, 0)

        @callback_type
        def result_procedure(hwnd, message, wparam, lparam):
            if message in (0x300, 0x301, 0x7B):  # No result cut/copy/context-menu export.
                return 0
            return user.CallWindowProcW(window.result_procedure, hwnd, message, wparam, lparam)

        window.result_procedure = user.SetWindowLongPtrW(window.controls[14], -4,
                                                       ctypes.cast(result_procedure, ctypes.c_void_p).value)
        _require(window.result_procedure)
        window.callbacks = (procedure, result_procedure)
        _require(user.SetTimer(window.hwnd, 1, 100, None) == 1)
        enable_inputs()
        user.ShowWindow(window.hwnd, 5)
        _require(user.UpdateWindow(window.hwnd))
        message = Message()
        while True:
            result = user.GetMessageW(ctypes.byref(message), None, 0, 0)
            _require(result != -1)
            if result == 0:
                break
            user.TranslateMessage(ctypes.byref(message))
            user.DispatchMessageW(ctypes.byref(message))
        _require(not busy())
        return 1 if window.failed else 0
    finally:
        # Never free a live call's window or buffers to make cleanup look complete.
        if not busy():
            if window.hwnd and user.IsWindow(window.hwnd):
                _require(user.DestroyWindow(window.hwnd))
            _require(user.UnregisterClassW(specification.name, None))


def run_owner_source_use_local_v1() -> int:
    root = None
    controller = None
    outcome = 1
    try:
        root = _bootstrap_owner_source_use_v1()
        from .owner_source_use import _create_owner_source_use_controller_v1

        controller = _create_owner_source_use_controller_v1(root)
        outcome = _run_local_window_v1(root, controller)
    except BaseException:
        # Fixed exit only: no exception, key, proposal, response or original output.
        outcome = 1
    finally:
        if controller is not None:
            try:
                controller.stop_v1()
            except BaseException:
                outcome = 1
        if root is not None:
            try:
                _close_native_root_v1(root)
            except BaseException:
                # Non-daemon worker/root references stay retained if terminal
                # custody is unestablished. No successful cleanup is advertised.
                outcome = 1
    return outcome


if __name__ == "__main__":
    raise SystemExit(run_owner_source_use_local_v1())
