from tests.pr168_gfp2.pr168_gfp2_test_support import validate_agent_and_dag


def test_dag_has_no_orphan_nodes() -> None:
    validate_agent_and_dag()
