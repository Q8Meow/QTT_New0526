from pathlib import Path


def test_resolver_does_not_glob_raw_generated_jsonl_files() -> None:
    source = Path("src/qtt/dashboard/owner_surface_resolver.py").read_text(encoding="utf-8")
    forbidden = (".glob(", ".rglob(", "os.walk", "glob.glob")
    assert not any(token in source for token in forbidden)
    assert "owner_dashboard_surface_registry.jsonl" not in source
