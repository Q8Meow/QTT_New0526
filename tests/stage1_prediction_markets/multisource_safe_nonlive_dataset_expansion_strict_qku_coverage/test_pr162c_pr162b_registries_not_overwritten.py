from .test_support import report


def test_pr162c_pr162b_registries_not_overwritten():
    for filename in (
        "PR162B_QKUFormulaRegistry.report.json",
        "PR162B_QKUAlgorithmRegistry.report.json",
        "PR162B_QKUSolverMappingRegistry.report.json",
        "PR162B_PR162CDataRequirementHandoff.report.json",
    ):
        assert report(filename)["created_by_pr"] == "PR162B"
