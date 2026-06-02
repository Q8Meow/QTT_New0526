from .test_support import records


def test_pr162c_agent_routes_no_orphans():
    qku_ids = {record["qku_id"] for record in records("PR162C_QKUExecutionClassificationRegistry.report.json")}
    route_ids = {record["qku_id"] for record in records("PR162C_QTTAgentExecutableQKURoutingMatrix.report.json")}

    assert qku_ids == route_ids
    assert all(
        record["qtt_agent_consumer_routes"]
        for record in records("PR162C_QTTAgentExecutableQKURoutingMatrix.report.json")
    )
