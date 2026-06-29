from ._helpers import ensure_built, report


def test_rank4_builder_and_validator_pass() -> None:
    out_dir = ensure_built()
    assert (out_dir / "art_reg.json").is_file()
    assert report("run_receipt.report.json")["RP5G_outputs_consumed"] is True

