from src.qtt.plugins.contracts import adapter_smoke_vector


def test_plugin_abi_smoke_vector_is_computable():
    request, context, response = adapter_smoke_vector()
    assert request.plugin_id == response.plugin_id
    assert context.authority_envelope.no_live_order_authority
    assert response.plugin_materialization_status == "COMPUTABLE_PLUGIN_READY"
    assert "execution_adjusted_edge" in response.score_components
