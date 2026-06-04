from __future__ import annotations


def test_pr162r_a_executable_replay_ready_requires_formula_inputs_outputs_units_dataset_route(records):
    io = {row["candidate_id"]: row for row in records("PR162R_A_InputOutputUnitCompatibilityMatrix.report.json")}
    dataset = {row["candidate_id"]: row for row in records("PR162R_A_DatasetBindingCompatibilityMatrix.report.json")}
    executable = [
        row
        for row in records("PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json")
        if row["primary_executability_state"].startswith("EXECUTABLE")
    ]
    assert executable
    for row in executable:
        assert row["candidate_type"] in {"FORMULA", "ALGORITHM"}
        assert io[row["candidate_id"]]["input_fields_present_flag"]
        assert io[row["candidate_id"]]["output_fields_present_flag"]
        assert io[row["candidate_id"]]["units_present_flag"]
        assert dataset[row["candidate_id"]]["replay_dataset_binding_flag"]
