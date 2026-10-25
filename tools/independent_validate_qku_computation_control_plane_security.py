#!/usr/bin/env python3
"""Independent static security validation without importing production."""

from __future__ import annotations

import ast
import ntpath
from pathlib import Path
import sys
import unicodedata

from independent_validate_qku_computation_control_plane_e import (
    validate_domain as validate_st12e_domain,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
FORBIDDEN_IMPORT_ROOTS = {
    "dill",
    "importlib",
    "marshal",
    "pickle",
    "shelve",
}
FORBIDDEN_CALLS = {"eval", "exec", "__import__", "compile"}
FORBIDDEN_ATTRIBUTE_CALLS = {
    ("importlib", "import_module"),
    ("importlib", "reload"),
    ("pickle", "load"),
    ("pickle", "loads"),
}
SUCCESS_MARKER = "QKU_SECURITY_INDEPENDENTLY_VALIDATED"
SECRET_TERMS = frozenset(
    {
        "apikey",
        "apisecret",
        "authorization",
        "bearer",
        "password",
        "passphrase",
        "accesstoken",
        "refreshtoken",
        "sessiontoken",
        "cookie",
        "credential",
        "privatekey",
        "secret",
        "seedphrase",
        "walletsecret",
    }
)
ALLOWED_SECRET_LOOKALIKES = frozenset(
    {"tokencount", "tokenbudget", "credentialstate"}
)


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _independent_secret_match(value: str) -> bool:
    normalized = _normalize_key(value)
    if normalized in ALLOWED_SECRET_LOOKALIKES:
        return False
    return (
        normalized == "token"
        or normalized.endswith("token")
        or any(term in normalized for term in SECRET_TERMS)
    )


def _function_uses_name(
    tree: ast.Module,
    function_name: str,
    consumed_name: str,
) -> bool:
    function = _find_function(tree, function_name)
    return function is not None and any(
        isinstance(node, ast.Name) and node.id == consumed_name
        for node in ast.walk(function)
    )


def _find_function(
    tree: ast.Module,
    function_name: str,
) -> ast.FunctionDef | None:
    return next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        ),
        None,
    )


def _is_certified_parameter_resource_import(
    path: Path,
    node: ast.ImportFrom,
) -> bool:
    if path.resolve() != (PACKAGE / "parameter_policy.py").resolve():
        return False
    if node.level != 0:
        return False
    signature = (
        node.module,
        tuple((alias.name, alias.asname) for alias in node.names),
    )
    return signature in {
        ("importlib", (("resources", None),)),
        ("importlib.resources.abc", (("Traversable", None),)),
    }


def _directly_imports_module(tree: ast.Module, module_name: str) -> bool:
    return any(
        isinstance(node, ast.Import)
        and any(alias.name == module_name for alias in node.names)
        for node in tree.body
    )


def _function_calls_name(
    function: ast.FunctionDef | None,
    function_name: str,
) -> bool:
    return function is not None and any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == function_name
        for node in ast.walk(function)
    )


def _helper_calls_ntpath_isreserved(
    function: ast.FunctionDef | None,
) -> bool:
    return function is not None and any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "isreserved"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "ntpath"
        for node in ast.walk(function)
    )


def _helper_enforces_colon_denial(
    function: ast.FunctionDef | None,
) -> bool:
    return function is not None and any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Constant)
        and node.left.value == ":"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.In)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Name)
        and node.comparators[0].id == "segment"
        for node in ast.walk(function)
    )


def _helper_enforces_control_characters(
    function: ast.FunctionDef | None,
) -> bool:
    if function is None:
        return False
    for generator in (
        node for node in ast.walk(function) if isinstance(node, ast.GeneratorExp)
    ):
        if len(generator.generators) != 1:
            continue
        comprehension = generator.generators[0]
        if (
            not isinstance(comprehension.target, ast.Name)
            or not isinstance(comprehension.iter, ast.Name)
            or comprehension.iter.id != "segment"
        ):
            continue
        character_name = comprehension.target.id
        comparisons = (
            node
            for node in ast.walk(generator.elt)
            if isinstance(node, ast.Compare)
        )
        comparison_pairs = []
        for comparison in comparisons:
            if (
                len(comparison.ops) != 1
                or len(comparison.comparators) != 1
                or not isinstance(comparison.left, ast.Call)
                or not isinstance(comparison.left.func, ast.Name)
                or comparison.left.func.id != "ord"
                or len(comparison.left.args) != 1
                or not isinstance(comparison.left.args[0], ast.Name)
                or comparison.left.args[0].id != character_name
                or not isinstance(comparison.comparators[0], ast.Constant)
            ):
                continue
            comparison_pairs.append(
                (
                    type(comparison.ops[0]),
                    comparison.comparators[0].value,
                )
            )
        if (ast.Lt, 32) in comparison_pairs and (ast.Eq, 127) in comparison_pairs:
            return True
    return False


def _is_clock_base_expression(node: ast.AST) -> bool:
    if (
        not isinstance(node, ast.Call)
        or node.args
        or node.keywords
        or not isinstance(node.func, ast.Attribute)
        or node.func.attr != "casefold"
        or not isinstance(node.func.value, ast.Subscript)
    ):
        return False
    base_subscript = node.func.value
    if not isinstance(base_subscript.slice, ast.Constant):
        return False
    if base_subscript.slice.value != 0:
        return False
    split_call = base_subscript.value
    if (
        not isinstance(split_call, ast.Call)
        or split_call.keywords
        or not isinstance(split_call.func, ast.Attribute)
        or split_call.func.attr != "split"
        or len(split_call.args) != 2
        or not isinstance(split_call.args[0], ast.Constant)
        or split_call.args[0].value != "."
        or not isinstance(split_call.args[1], ast.Constant)
        or split_call.args[1].value != 1
    ):
        return False
    rstrip_call = split_call.func.value
    return (
        isinstance(rstrip_call, ast.Call)
        and not rstrip_call.keywords
        and isinstance(rstrip_call.func, ast.Attribute)
        and rstrip_call.func.attr == "rstrip"
        and isinstance(rstrip_call.func.value, ast.Name)
        and rstrip_call.func.value.id == "segment"
        and len(rstrip_call.args) == 1
        and isinstance(rstrip_call.args[0], ast.Constant)
        and rstrip_call.args[0].value == " ."
    )


def _helper_enforces_exact_clock_base(
    function: ast.FunctionDef | None,
) -> bool:
    return function is not None and any(
        isinstance(node, ast.Compare)
        and _is_clock_base_expression(node.left)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value == "clock$"
        for node in ast.walk(function)
    )


def _source_use_security_failures_v1(root):
    """Separate security oracle; no production/native module is imported."""
    native_path = root / "src/qtt/service/owner_source_use_windows.py"
    service_path = root / "src/qtt/service/owner_source_use.py"
    native = ast.parse(native_path.read_text(encoding="utf-8"))
    service = ast.parse(service_path.read_text(encoding="utf-8"))
    failures = []
    native_functions = {n.name: n for n in native.body if isinstance(n, ast.FunctionDef)}
    service_functions = {n.name: n for n in service.body if isinstance(n, ast.FunctionDef)}
    def calls(node):
        return [n for n in ast.walk(node) if isinstance(n, ast.Call)]
    try:
        expected_dlls = {
            "_native_system_v1": ["advapi32.dll", "kernel32.dll", "ole32.dll", "shell32.dll"],
            "_webauthn_table_v1": ["webauthn.dll"], "_user_table_v1": ["user32.dll"],
        }
        found = []
        for name, function in native_functions.items():
            loads = [n for n in calls(function) if ast.unparse(n.func) == "ctypes.WinDLL"]
            if loads:
                observed = []
                for node in loads:
                    if len(node.args) != 1 or not isinstance(node.args[0], ast.Constant):
                        failures.append("native DLL is not fixed")
                        continue
                    observed.append(node.args[0].value)
                    if {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords} != {"use_last_error": True, "winmode": 2048}:
                        failures.append("native DLL search policy differs")
                if sorted(observed) != expected_dlls.get(name):
                    failures.append("native DLL owner/roster differs")
                found.extend(observed)
        if len(found) != 6:
            failures.append("native DLL census differs")
        allowed_entry = ast.parse('if __name__ == "__main__":\n    raise SystemExit(run_owner_source_use_local_v1())').body[0]
        top_effects = [n for n in native.body if not isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign,
                      ast.AnnAssign, ast.FunctionDef, ast.ClassDef, ast.Expr))]
        if len(top_effects) != 1 or ast.dump(top_effects[0], include_attributes=False) != ast.dump(allowed_entry, include_attributes=False):
            failures.append("native explicit entry differs")
        for node in native.body:
            if isinstance(node, ast.Expr) and not isinstance(node.value, ast.Constant):
                failures.append("native import scope executes a call")
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                if any(ast.unparse(call.func) in {"run_owner_source_use_local_v1", "_bootstrap_owner_source_use_v1", "ctypes.WinDLL"}
                       for call in calls(node)):
                    failures.append("native import scope constructs an operational root")
        entry_calls = {ast.unparse(n.func) for n in calls(native_functions["run_owner_source_use_local_v1"])}
        if not {"_bootstrap_owner_source_use_v1", "_create_owner_source_use_controller_v1",
                "_run_local_window_v1", "_close_native_root_v1", "controller.stop_v1"} <= entry_calls:
            failures.append("entry bootstrap/controller/window/cleanup chain incomplete")
        verify = service_functions["_verify_source_use_response_v1"]
        verifier_calls = {ast.unparse(n.func) for n in calls(verify)}
        if not {"Fido2Server.authenticate_complete", "Fido2Server.register_complete", "_validate_public_key_v1",
                "_closed_json_v1", "_source_use_b64_v1"} <= verifier_calls:
            failures.append("actual Fido2Server verification boundary incomplete")
        if {"pending.server.authenticate_complete", "pending.server.register_complete"} & verifier_calls:
            failures.append("verifier is replaceable through an instance callback")
        verifier_checks = {ast.unparse(n) for n in ast.walk(verify)}
        if not {"raw.client_data == pending.client_data", "pending.server._verify is _exact_source_use_origin_v1",
                "type(pending.server) is Fido2Server"} <= verifier_checks:
            failures.append("frozen response/origin/server association missing")
        table_text = ast.unparse(native_functions["_webauthn_table_v1"])
        if "w.WebAuthNIsUserVerifyingPlatformAuthenticatorAvailable.argtypes = [ctypes.POINTER(ctypes.c_int32)]" not in table_text:
            failures.append("WebAuthn availability BOOL width differs")
        acquire = native_functions["_acquire_native_response_v1"]
        finalizers = [n for n in ast.walk(acquire) if isinstance(n, ast.Try) and n.finalbody]
        if len(finalizers) != 1:
            failures.append("native response does not have one cleanup owner")
        else:
            free_calls = [ast.unparse(n.func) for stmt in finalizers[0].finalbody for n in calls(stmt)]
            if free_calls != ["table.WebAuthNFreeAssertion", "table.WebAuthNFreeCredentialAttestation"]:
                failures.append("native response free functions differ")
        for node in ast.walk(native):
            if isinstance(node, ast.ImportFrom) and node.module == "fido2.client.windows":
                failures.append("high-level native parser imported")
            if isinstance(node, ast.FunctionDef) and node.name == "__del__":
                failures.append("native response has an automatic destructor")
            if isinstance(node, ast.Assign) and any(ast.unparse(t) == "sys.path" for t in node.targets):
                failures.append("bootstrap modifies its import path")
    except (KeyError, ValueError, TypeError) as error:
        failures.append("source-use security structure invalid: " + str(error))
    return failures


def main() -> int:
    failures: list[str] = []
    failures.extend(_source_use_security_failures_v1(REPO_ROOT))
    failures.extend(validate_st12e_domain("security"))
    authority_tree: ast.Module | None = None
    certified_import_count = 0
    other_importlib_import_count = 0
    dynamic_import_call_count = 0
    cache_lock_import_count = 0
    cache_lock_assignment_count = 0
    cache_lock_publication_count = 0
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        source_use_thread_imports = set()
        if path.name == "source_policy.py":
            for cls in tree.body:
                if isinstance(cls, ast.ClassDef) and cls.name == "KalshiFeeObservationOwnerV1":
                    for method in cls.body:
                        if isinstance(method, ast.FunctionDef) and method.name in {"_prepare_read_v1", "_require_pending_v1"}:
                            source_use_thread_imports.update(id(n) for n in method.body if isinstance(n, ast.ImportFrom)
                                and n.module == "threading" and n.level == 0
                                and tuple((a.name, a.asname) for a in n.names) == (("current_thread", None),))
        if path.name == "authority.py":
            authority_tree = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path.name}: unsafe import {sorted(roots)}")
                if "importlib" in roots:
                    other_importlib_import_count += 1
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if root == "threading":
                    signature = tuple(
                        (alias.name, alias.asname) for alias in node.names
                    )
                    if path.name == "evidence.py":
                        if node.module == "threading" and signature == (("Lock", None),):
                            cache_lock_import_count += 1
                        else:
                            failures.append(
                                "evidence.py: cache publication import differs "
                                "from exact threading.Lock authority"
                            )
                    elif path.name != "parameter_policy.py" and id(node) not in source_use_thread_imports:
                        failures.append(
                            f"{path.name}: unauthorized production threading import"
                        )
                if root == "importlib" and _is_certified_parameter_resource_import(
                    path,
                    node,
                ):
                    certified_import_count += 1
                elif root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path.name}: unsafe import {root}")
                    if root == "importlib":
                        other_importlib_import_count += 1
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else ""
                if name in FORBIDDEN_CALLS:
                    failures.append(f"{path.name}: unsafe call {name}")
                if name == "__import__":
                    dynamic_import_call_count += 1
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and (
                        node.func.value.id,
                        node.func.attr,
                    )
                    in FORBIDDEN_ATTRIBUTE_CALLS
                ):
                    failures.append(
                        f"{path.name}: unsafe call "
                        f"{node.func.value.id}.{node.func.attr}"
                    )
                    if (
                        node.func.value.id,
                        node.func.attr,
                    ) == ("importlib", "import_module"):
                        dynamic_import_call_count += 1
            if path.name == "evidence.py" and isinstance(node, ast.Assign):
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Attribute)
                    and isinstance(node.targets[0].value, ast.Name)
                    and node.targets[0].value.id == "self"
                    and node.targets[0].attr == "_cache_publication_lock"
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "Lock"
                    and not node.value.args
                    and not node.value.keywords
                ):
                    cache_lock_assignment_count += 1
            if path.name == "evidence.py" and isinstance(node, ast.With):
                if (
                    len(node.items) == 1
                    and isinstance(node.items[0].context_expr, ast.Attribute)
                    and isinstance(
                        node.items[0].context_expr.value,
                        ast.Name,
                    )
                    and node.items[0].context_expr.value.id == "self"
                    and node.items[0].context_expr.attr
                    == "_cache_publication_lock"
                    and node.items[0].optional_vars is None
                ):
                    cache_lock_publication_count += 1
    if cache_lock_import_count != 1:
        failures.append(
            "evidence.py does not contain exactly one certified Lock import"
        )
    if cache_lock_assignment_count != 1:
        failures.append(
            "evidence.py does not construct exactly one cache publication Lock"
        )
    if cache_lock_publication_count != 1:
        failures.append(
            "evidence.py does not use its Lock exactly once for cache publication"
        )
    parameter_policy_tree = ast.parse(
        (PACKAGE / "parameter_policy.py").read_text(encoding="utf-8"),
        filename="parameter_policy.py",
    )
    resource_root_functions = tuple(
        node
        for node in parameter_policy_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_st12f_parameter_resource_root_v1"
    )
    resource_calls = tuple(
        node
        for node in ast.walk(parameter_policy_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "resources"
    )
    resource_root_exact = False
    if len(resource_root_functions) == 1:
        resource_root = resource_root_functions[0]
        if len(resource_root.body) == 1 and isinstance(
            resource_root.body[0],
            ast.Return,
        ):
            join_call = resource_root.body[0].value
            if (
                isinstance(join_call, ast.Call)
                and isinstance(join_call.func, ast.Attribute)
                and join_call.func.attr == "joinpath"
                and len(join_call.args) == 1
                and isinstance(join_call.args[0], ast.Constant)
                and join_call.args[0].value == "data"
                and not join_call.keywords
                and isinstance(join_call.func.value, ast.Call)
            ):
                files_call = join_call.func.value
                resource_root_exact = (
                    isinstance(files_call.func, ast.Attribute)
                    and isinstance(files_call.func.value, ast.Name)
                    and files_call.func.value.id == "resources"
                    and files_call.func.attr == "files"
                    and len(files_call.args) == 1
                    and isinstance(files_call.args[0], ast.Name)
                    and files_call.args[0].id == "__package__"
                    and not files_call.keywords
                )
    if certified_import_count != 2:
        failures.append(
            "parameter_policy.py does not contain exactly two certified "
            "package-resource imports"
        )
    if other_importlib_import_count:
        failures.append("a non-certified importlib-root import exists")
    if len(resource_root_functions) != 1:
        failures.append(
            "parameter_policy.py does not define exactly one top-level "
            "_st12f_parameter_resource_root_v1"
        )
    if not resource_root_exact:
        failures.append(
            "parameter resource root is not exactly "
            "resources.files(__package__).joinpath('data')"
        )
    if len(resource_calls) != 1:
        failures.append(
            "parameter_policy.py contains a non-certified resources call"
        )
    if dynamic_import_call_count:
        failures.append("a dynamic import call exists")
    capability_defaults: list[bool] = []
    for node in authority_tree.body if authority_tree else ():
        if isinstance(node, ast.ClassDef) and node.name == "CapabilityEnvelopeV1":
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign):
                    capability_defaults.append(
                        isinstance(statement.value, ast.Constant)
                        and statement.value.value is False
                    )
    if len(capability_defaults) != 10 or not all(capability_defaults):
        failures.append("capability envelope is not exactly ten default-false fields")
    serialization_tree = ast.parse(
        (PACKAGE / "serialization.py").read_text(encoding="utf-8")
    )
    source_rights_tree = ast.parse(
        (PACKAGE / "source_rights.py").read_text(encoding="utf-8")
    )
    function = _find_function(serialization_tree, "validate_relative_path")
    segment_helper = _find_function(
        serialization_tree,
        "_is_windows_reserved_segment",
    )
    obsolete_reserved_table_present = any(
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == "_WINDOWS_RESERVED_NAMES"
        for node in ast.walk(serialization_tree)
    )
    call_attributes = {
        node.func.attr
        for node in (ast.walk(function) if function is not None else ())
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    }
    constants = {
        node.value
        for node in (ast.walk(function) if function is not None else ())
        if isinstance(node, ast.Constant)
    }
    attribute_names = {
        node.attr
        for node in (ast.walk(function) if function is not None else ())
        if isinstance(node, ast.Attribute)
    }
    if (
        function is None
        or not {"replace", "split", "is_absolute"} <= call_attributes
        or not {"", ".", ".."} <= constants
        or "drive" not in attribute_names
        or not _function_calls_name(function, "_is_windows_reserved_segment")
    ):
        failures.append(
            "relative-path safety lacks structural traversal, drive, "
            "segment, or reserved-name checks"
        )
    if not _directly_imports_module(serialization_tree, "ntpath"):
        failures.append("serialization.py does not directly import ntpath")
    if segment_helper is None:
        failures.append(
            "serialization.py does not define _is_windows_reserved_segment"
        )
    if not _helper_calls_ntpath_isreserved(segment_helper):
        failures.append(
            "_is_windows_reserved_segment does not call ntpath.isreserved"
        )
    if not _helper_enforces_colon_denial(segment_helper):
        failures.append(
            "_is_windows_reserved_segment lacks structural colon denial"
        )
    if not _helper_enforces_control_characters(segment_helper):
        failures.append(
            "_is_windows_reserved_segment lacks structural control/DEL denial"
        )
    if not _helper_enforces_exact_clock_base(segment_helper):
        failures.append(
            "_is_windows_reserved_segment lacks exact case-insensitive CLOCK$ denial"
        )
    if obsolete_reserved_table_present:
        failures.append("obsolete manual _WINDOWS_RESERVED_NAMES table remains")
    invalid_segments = (
        "NUL.txt",
        "COM1",
        "CONIN$.txt",
        "CONOUT$.txt",
        "CLOCK$.txt",
        "clock$.txt",
        "trailing.",
        "trailing ",
        "a:b",
        "\x1fcontrol",
        "\x7fcontrol",
        *(f"name{character}.json" for character in '<>:"|?*'),
    )
    valid_segments = (
        "β–contract.json",
        "contract.json",
        "CONTEXT.json",
        "CONIN$foo.txt",
        "CONOUT$foo.txt",
        "CLOCKWORK.txt",
        "COM10.txt",
        "LPT10.txt",
    )
    independent_segment_results = {
        segment: (
            ntpath.isreserved(segment)
            or ":" in segment
            or segment.endswith((" ", "."))
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in segment
            )
            or segment.rstrip(" .").split(".", 1)[0].casefold() == "clock$"
        )
        for segment in (*invalid_segments, *valid_segments)
    }
    independently_accepted_invalid = [
        segment
        for segment in invalid_segments
        if not independent_segment_results[segment]
    ]
    independently_rejected_valid = [
        segment
        for segment in valid_segments
        if independent_segment_results[segment]
    ]
    if independently_accepted_invalid:
        failures.append(
            "independent Windows path matrix accepted invalid segments: "
            + repr(independently_accepted_invalid)
        )
    if independently_rejected_valid:
        failures.append(
            "independent Windows path matrix rejected valid segments: "
            + repr(independently_rejected_valid)
        )
    serialization_classes = {
        node.name
        for node in serialization_tree.body
        if isinstance(node, ast.ClassDef)
    }
    serialization_assignments = {
        target.id
        for node in serialization_tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    source_rights_imports = {
        alias.name
        for node in source_rights_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "serialization"
        for alias in node.names
    }
    if (
        "SecretKeyPolicyV1" not in serialization_classes
        or "SECRET_KEY_POLICY" not in serialization_assignments
        or "SECRET_KEY_POLICY" not in source_rights_imports
        or not _function_uses_name(
            serialization_tree,
            "_check_key",
            "SECRET_KEY_POLICY",
        )
        or not _function_uses_name(
            source_rights_tree,
            "reject_secret_material",
            "SECRET_KEY_POLICY",
        )
    ):
        failures.append(
            "serialization and source rights do not consume one secret policy"
        )
    secret_variants = (
        "API-KEY",
        "api.secret",
        "Authorization",
        "bearer_token",
        "password",
        "pass phrase",
        "access-token",
        "refresh_token",
        "SESSION.TOKEN",
        "cookie",
        "credential",
        "private/key",
        "seed_phrase",
        "wallet-secret",
    )
    allowed_variants = ("token_count", "token-budget", "credential.state")
    if not all(_independent_secret_match(value) for value in secret_variants):
        failures.append("independent secret-key normalization misses a class")
    if any(_independent_secret_match(value) for value in allowed_variants):
        failures.append("independent secret-key normalization has a false positive")
    serialization_text = (PACKAGE / "serialization.py").read_text(encoding="utf-8")
    for term in SECRET_TERMS | ALLOWED_SECRET_LOOKALIKES:
        if f'"{term}"' not in serialization_text:
            failures.append(f"central secret policy term is absent: {term}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} "
        f"certified_importlib_resource_import_count={certified_import_count} "
        f"other_importlib_import_count={other_importlib_import_count} "
        f"dynamic_import_call_count={dynamic_import_call_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
