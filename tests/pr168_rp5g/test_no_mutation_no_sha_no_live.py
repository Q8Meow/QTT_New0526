from ._helpers import all_jsonl_rows


def test_no_mutation_no_sha_no_live() -> None:
    for filename, row in all_jsonl_rows():
        for field in ("formula_mutation_flag", "qku_mutation_flag", "qtt_sha_authority_flag", "atomicrows_sha_ref_flag", "live_authority_flag"):
            if field in row:
                assert row[field] is False, (filename, row["row_id"], field)

