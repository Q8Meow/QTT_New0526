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


def main() -> int:
    failures: list[str] = []
    failures.extend(validate_st12e_domain("security"))
    authority_tree: ast.Module | None = None
    certified_import_count = 0
    other_importlib_import_count = 0
    dynamic_import_call_count = 0
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
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
