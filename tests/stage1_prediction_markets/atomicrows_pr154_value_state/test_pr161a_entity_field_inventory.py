from .pr161a_test_support import records, summary


def test_pr161a_entity_and_field_inventory():
    assert len(records("atomicrows_entity")) == 4183
    assert len(records("pr154_entity")) == 342
    assert summary()["field_value_record_count"] >= 4525
    field_entities = {record.get("row_id") or record.get("target_id") for record in records("field_inventory")}
    assert len(field_entities) == 4525

