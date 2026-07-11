from __future__ import annotations


CORE_OBJECTS = (
    "AdverseSelectionModelV1", "CampaignCapacityFrontierV1", "CampaignChildOrderV1",
    "CampaignEvidenceStopPolicyV1", "CapacityCrowdingModelV1", "CashflowModelV1",
    "ExecutableExitQuoteV1", "FastCanaryEligibilityHandoffV1", "FeeModelV1", "FillModelV1",
    "HarvestExitPolicyV1", "HotpathSnapshotRequestV1", "LatencyDecayModelV1",
    "LiveDryrunCandidateHandoffV1", "LossDispositionPolicyV1", "MemoryObservationRequestV1",
    "MemoryUpdateReceiptV1", "MemoryUpdateRequestV1", "MetricsEventHandoffV1",
    "ModeAuthorityMatrixV1", "NetCashVelocityPolicyV1", "OrderPolicyRealityModelV1",
    "OwnerTradeIntentV1", "PaperOwnerConstraintReceiptV1", "PaperOwnerOverridePreviewV1",
    "PaperPresentationProjectionV1", "PartialFillModelV1", "PluginEvidenceHandoffV1",
    "PostlaunchLearningContractV1", "PreTradeDecisionCandidateV1", "QKUFormulaBindingV1",
    "QuantumAlgorithmCatalogV1", "QuantumBackendRunReceiptV1", "QuantumCoefficientStressV1",
    "QuantumComparatorReceiptV1", "QuantumComputeAllocatorV1", "QuantumComputeBudgetV1",
    "QuantumEconomicProblemV1", "QuantumEconomicUtilityV1", "QuantumFormulationPortfolioV1",
    "QuantumHotpathEnvelopeV1", "QuantumMappingCandidateHandoffV1", "QuantumMemoryPriorV1",
    "QuantumProblemFingerprintV1", "QuantumRegimeRobustnessV1", "QuantumSampleConsensusV1",
    "QuantumSolutionFragilityV1", "QuantumSolverRouteV1", "QuantumSolverRouterV1",
    "QueuePositionModelV1", "ReentryHysteresisPolicyV1", "RoundTripCostEnvelopeV1",
    "RuntimeAllowlistCandidateHandoffV1", "SettlementResolutionModelV1", "SlippageModelV1",
    "TradeCampaignV1", "TradePlanCandidateV1", "VenueFeeModelV1", "VenueRealityModelV1",
)

INTEGRATED_OBJECTS = (
    "AgentQKUAccessPolicyRegistryV1", "FormulaAssignmentLibraryV1", "FormulaOntologyV1",
    "ImmutableFormulaComputationRunnerV1", "ImmutableFormulaLibraryV1",
    "ImmutableFormulaQKULibraryV1", "ImmutableQKULibraryV1", "LibraryQueryReceiptV1",
    "MarketStageActivationProfileRegistryV1", "QKUFormulaIdentityLineageV1",
    "QKUMarketApplicabilityMatrixV1", "ContextFormulaPoolSelectorV1", "ContextFormulaSelectorV1",
    "EphemeralStackRunContractV1", "SimpleStackGeneratorV1", "StackGeneratorBudgetPolicyV1",
    "StackGeneratorEngineV1", "StackGeneratorRunReceiptV1", "StackRoleOntologyV1",
    "StackTemplateRegistryV1", "UseAndDumpRetentionPolicyV1", "UseAndDumpSimulationGridV1",
    "AdverseSelectionModelV1", "CapacityCrowdingEngineV1", "CapacityCrowdingModelV1",
    "CashflowModelV1", "ChampionChallengerSelectionV1", "ChampionChallengerSimulationPreviewV1",
    "ExitTimingGridV1", "ExpectedCashPnLEngineV1", "FeeModelV1", "FillLatencyCapacityEngineV1",
    "FillModelV1", "ImplementationShortfallV1", "LCBAndUncertaintyEngineV1",
    "LatencyBudgetDecisionV1", "LatencyDecayModelV1", "MakerTakerSplitPolicyGridV1",
    "MarketConditionClassifierV1", "ModeAuthorityMatrixV1", "NoTradeCandidateV1",
    "NoTradeComparatorV1", "OrderPolicyCandidateSetV1", "OrderPolicyRealityModelV1",
    "OrderSizingGridV1", "OrderVariableCombinationEngineV1", "OrderVariableGridGeneratorV1",
    "OrderVariableGridV1", "OverfitFDRPenaltyEngineV1", "PartialFillModelV1",
    "PnLDecompositionEngineV1", "PortfolioMarginalUtilityEngineV1", "PreTradeDecisionCandidateV1",
    "QuantumOptimizationReadinessBridgeV1", "QueuePositionModelV1", "ReplayPaperFactualGateV1",
    "ScenarioLadderDecisionV1", "ScenarioLadderEngineV1", "SettlementResolutionModelV1",
    "SlippageModelV1", "SnapshotConditionedTradePlanSimulationEngineV1", "TCADecompositionEngineV1",
    "TCADecompositionV1", "TopKTradePlanSelectorV1", "TradePlanCandidateV1",
    "TradePlanOutcomeLedgerV1", "TradePlanSimulationEngineV1", "TradeTargetFixtureV1",
    "TradeTargetScoutV1", "TradeTargetV1", "VenueRealityModelV1",
    "ConditionedFailureMemoryRegistryV1", "ConditionedFailureMemoryV1",
    "ConditionedWinningRecipeRegistryV1", "ConditionedWinningRecipeV1", "Rank4ContextSignatureV1",
    "Rank4NegativeMemoryHintV1", "Rank4RecipeRetestPriorityV1", "Rank4RecipeSimilarityKeyV1",
    "Rank4WinnerAttributionV1", "Rank4WinningRecipeHandoffV1", "RecipeCooldownPolicyV1",
    "RecipeDemotionHistoryV1", "RecipeDriftMonitorV1", "RecipeOutcomeAttributionLedgerV1",
    "RecipePriorScoreEngineV1", "RecipePromotionHistoryV1", "RecipeRetestQueueV1",
    "RegimeConditionedMemoryHandoffV1", "TradeContextSignatureV1", "TradeContextSimilarityEngineV1",
    "WinningAttributionV1", "CapacityCrowdingInferenceEngineV1", "CleanRoomReverseEngineeringReceiptV1",
    "ExitRuleInferenceEngineV1", "HistoricalTradeRecordIngestionV1",
    "InstitutionalStyleDefaultCandidateRegistryV1", "OrderPolicyInferenceEngineV1",
    "OwnerReviewDefaultPromotionPacketV1", "ReplayPaperCandidateDefaultQueueV1",
    "RightsAndProvenanceGateV1", "SizingInferenceEngineV1", "StrategyFamilyClassifierV1",
    "TCAInferenceEngineV1", "TradeReconstructionEngineV1", "TradeRecordRightsAndProvenanceGateV1",
    "MemoryUpdateReceiptV1", "NoTradeDecisionReceiptV1", "PaperExitSimulationReceiptV1",
    "PaperFillSimulationReceiptV1", "PaperIntentCandidateV1", "PaperOrderIntentCandidateV1",
    "PaperOrderIntentV1", "PaperPnLReceiptV1", "PaperResultReceiptV1", "ReplayPaperRequestV1",
    "ReplayResultReceiptV1", "TradePlanSelectionReceiptV1", "AckTimestampReceiptV1",
    "CancelRejectReceiptV1", "DecisionTimestampReceiptV1", "KillSwitchReceiptV1",
    "LiveDryRunDecisionReceiptV1", "LivePreTradeDecisionGateV1", "MarketQuoteReceiptV1",
    "OrderBookSnapshotReceiptV1", "OrderIntentCompileReceiptV1", "RiskGateReceiptV1",
    "SubmitDisabledProofV1", "SubmitTimestampReceiptV1", "TCAMetricReceiptV1",
    "VenueAdapterContractV1", "AgentCycleReceiptV1", "AgentDAGRunReceiptV1",
    "AgentDecisionReceiptV1", "AgentRouteIdentityCrosswalkV1", "AgentTaskQueueV1",
    "RuntimeTaskReceiptV1", "UpstreamConsumptionReceiptV1", "DashboardDecisionViewV1",
    "OWNER_DASHBOARD_PACKET_V1", "OwnerActionReceiptV1", "OwnerActionRegistryV1",
    "OwnerActionRequestV1", "OwnerActionableCardV1", "OwnerAgentDirectiveEnvelopeV1",
    "OwnerAgentResponsePreviewV1", "OwnerAgentStateV1", "OwnerApprovalLadderV1",
    "OwnerAttachmentCandidateV1", "OwnerAuditTrailPanelV1", "OwnerBacklogPanelV1",
    "OwnerChangeQueuePanelV1", "OwnerChartSeriesV1", "OwnerChatActionPreviewV1",
    "OwnerChatRouteReceiptPreviewV1", "OwnerConfirmationClassV1", "OwnerConversationStateV1",
    "OwnerDashboardPacketV1", "OwnerDashboardStateV1", "OwnerDecisionQueueStateV1",
    "OwnerDecisionQueueV1", "OwnerExecutionAuthorityStateV1", "OwnerExecutionRouterSubmitRequestV1",
    "OwnerHeaderStripV1", "OwnerKillSwitchRequestV1", "OwnerKillSwitchSurfaceV1",
    "OwnerLiveCanaryReviewRequestV1", "OwnerLivePanelV1", "OwnerMessageThreadV1", "OwnerMessageV1",
    "OwnerPlainEnglishIntentV1", "OwnerPortfolioStateV1", "OwnerQuantumStateV1",
    "OwnerReplayPaperRequestV1", "OwnerResearchPanelV1", "OwnerResearchPipelineStateV1",
    "OwnerResearchSubmissionV1", "OwnerRiskPanelV1", "OwnerRollbackRequestV1",
    "OwnerSearchIndexV1", "OwnerShadowPanelV1", "OwnerSurfaceRegistrySeedV1",
    "OwnerTradeCheckRequestV1", "OwnerTradeIntentV1", "FormulaCandidateV1",
    "FormulaExtractionCandidateV1", "QKUCandidateMaterializationRequestV1",
    "QuantumStructureMappingRequestV1", "ResearchCandidateV1", "SourceCandidateV1",
)

DISTINCT_OBJECTS = tuple(sorted(set(CORE_OBJECTS) | set(INTEGRATED_OBJECTS)))


if len(CORE_OBJECTS) != 59:
    raise ValueError("core object inventory must contain 59 names")
if len(INTEGRATED_OBJECTS) != 191:
    raise ValueError("integrated object inventory must contain 191 names")
if len(set(CORE_OBJECTS) & set(INTEGRATED_OBJECTS)) != 17:
    raise ValueError("object inventories must overlap by 17 names")
if len(DISTINCT_OBJECTS) != 233:
    raise ValueError("object union must contain 233 names")
