from tests.pr168_gfp2.pr168_gfp2_test_support import validate_agent_and_dag


def test_every_generated_file_and_numeric_value_has_upstream_downstream_or_terminal_exception() -> None:
    validate_agent_and_dag()
