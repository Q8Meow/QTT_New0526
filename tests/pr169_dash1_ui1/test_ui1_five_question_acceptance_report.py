from tests.pr169_dash1_ui1.conftest import ui_doc


def test_ui1_five_question_acceptance_report() -> None:
    report = ui_doc("owner_dashboard_ui1_five_question_acceptance.report.json")
    answers = report["answers"]
    assert len(answers) == 5
    for answer in answers:
        assert answer["answer_status"] == "PASS"
        assert answer["visible_widget_refs"]
        assert answer["generated_artifact_refs"]
        assert answer["provider_stage_refs"]
        assert answer["missing_items"] == []
