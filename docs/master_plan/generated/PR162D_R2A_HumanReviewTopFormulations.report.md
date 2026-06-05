# PR162D-R2A Human Review Top Formulations

This file displays executable candidate formulations only. It creates no live, order, replay, paper, result, profit, or quantum-advantage authority.

## Formula Formulations
### FORMULA::YES_EV
- expression/procedure/objective: yes_ev = p_model * payout - yes_price - fee_estimate - slippage_estimate - latency_cost_estimate
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_yes_ev`
- inputs/variables: `['p_model', 'payout', 'yes_price', 'fee_estimate', 'slippage_estimate', 'latency_cost_estimate']`
- outputs/objective meaning: `['yes_ev']`
- test_vector: `PR162D_R2A_TV_FORMULA::YES_EV`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::NO_EV
- expression/procedure/objective: no_ev = (1 - p_model) * payout - no_price - fee_estimate - slippage_estimate - latency_cost_estimate
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_no_ev`
- inputs/variables: `['p_model', 'payout', 'no_price', 'fee_estimate', 'slippage_estimate', 'latency_cost_estimate']`
- outputs/objective meaning: `['no_ev']`
- test_vector: `PR162D_R2A_TV_FORMULA::NO_EV`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::IMPLIED_PROBABILITY
- expression/procedure/objective: implied_probability = clamp(price / max(payout, epsilon), 0, 1)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_implied_probability`
- inputs/variables: `['price', 'payout']`
- outputs/objective meaning: `['implied_probability']`
- test_vector: `PR162D_R2A_TV_FORMULA::IMPLIED_PROBABILITY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::PROBABILITY_EDGE
- expression/procedure/objective: probability_edge = p_model - implied_probability
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_probability_edge`
- inputs/variables: `['p_model', 'implied_probability']`
- outputs/objective meaning: `['probability_edge']`
- test_vector: `PR162D_R2A_TV_FORMULA::PROBABILITY_EDGE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::NET_EDGE
- expression/procedure/objective: net_edge = expected_net_value / max(entry_price, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_net_edge`
- inputs/variables: `['expected_net_value', 'entry_price']`
- outputs/objective meaning: `['net_edge']`
- test_vector: `PR162D_R2A_TV_FORMULA::NET_EDGE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::MID_PRICE
- expression/procedure/objective: mid_price = (best_bid + best_ask) / 2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_mid_price`
- inputs/variables: `['best_bid', 'best_ask']`
- outputs/objective meaning: `['mid_price']`
- test_vector: `PR162D_R2A_TV_FORMULA::MID_PRICE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::SPREAD
- expression/procedure/objective: spread = best_ask - best_bid
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_spread`
- inputs/variables: `['best_bid', 'best_ask']`
- outputs/objective meaning: `['spread']`
- test_vector: `PR162D_R2A_TV_FORMULA::SPREAD`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::RELATIVE_SPREAD
- expression/procedure/objective: relative_spread = spread / max(mid_price, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_relative_spread`
- inputs/variables: `['spread', 'mid_price']`
- outputs/objective meaning: `['relative_spread']`
- test_vector: `PR162D_R2A_TV_FORMULA::RELATIVE_SPREAD`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::ORDERBOOK_IMBALANCE
- expression/procedure/objective: orderbook_imbalance = (bid_size - ask_size) / max(bid_size + ask_size, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_orderbook_imbalance`
- inputs/variables: `['bid_size', 'ask_size']`
- outputs/objective meaning: `['orderbook_imbalance']`
- test_vector: `PR162D_R2A_TV_FORMULA::ORDERBOOK_IMBALANCE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::LIQUIDITY_SCORE
- expression/procedure/objective: liquidity_score = log1p(volume) * log1p(depth) / max(spread, tick_size_or_epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_liquidity_score`
- inputs/variables: `['volume', 'depth', 'spread', 'tick_size_or_epsilon']`
- outputs/objective meaning: `['liquidity_score']`
- test_vector: `PR162D_R2A_TV_FORMULA::LIQUIDITY_SCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::LATENCY_COST
- expression/procedure/objective: latency_cost = abs(price_velocity_per_second) * expected_latency_seconds * notional_sensitivity
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_latency_cost`
- inputs/variables: `['price_velocity_per_second', 'expected_latency_seconds', 'notional_sensitivity']`
- outputs/objective meaning: `['latency_cost']`
- test_vector: `PR162D_R2A_TV_FORMULA::LATENCY_COST`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::SLIPPAGE_ESTIMATE
- expression/procedure/objective: slippage_estimate = spread_component + depth_impact_component + volatility_impact_component
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_slippage_estimate`
- inputs/variables: `['spread_component', 'depth_impact_component', 'volatility_impact_component']`
- outputs/objective meaning: `['slippage_estimate']`
- test_vector: `PR162D_R2A_TV_FORMULA::SLIPPAGE_ESTIMATE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::KELLY_CAPPED
- expression/procedure/objective: kelly_capped = clamp(((edge_probability * odds_payoff_ratio - loss_probability) / max(odds_payoff_ratio, epsilon)), 0, max_fraction_cap)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_kelly_capped`
- inputs/variables: `['edge_probability', 'odds_payoff_ratio', 'loss_probability', 'max_fraction_cap']`
- outputs/objective meaning: `['kelly_raw', 'kelly_capped']`
- test_vector: `PR162D_R2A_TV_FORMULA::KELLY_CAPPED`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::BRIER_SCORE
- expression/procedure/objective: brier_score = mean((actual_outcome - predicted_probability)^2)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_brier_score`
- inputs/variables: `['actual_outcomes', 'predicted_probabilities']`
- outputs/objective meaning: `['brier_score']`
- test_vector: `PR162D_R2A_TV_FORMULA::BRIER_SCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::LOG_LOSS
- expression/procedure/objective: log_loss = -mean(y * log(p_clipped) + (1 - y) * log(1 - p_clipped))
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_log_loss`
- inputs/variables: `['actual_outcomes', 'predicted_probabilities']`
- outputs/objective meaning: `['log_loss']`
- test_vector: `PR162D_R2A_TV_FORMULA::LOG_LOSS`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::EMA
- expression/procedure/objective: ema_t = alpha * price_t + (1 - alpha) * ema_t_minus_1
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_ema`
- inputs/variables: `['alpha', 'price_t', 'ema_t_minus_1']`
- outputs/objective meaning: `['ema_t']`
- test_vector: `PR162D_R2A_TV_FORMULA::EMA`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::SIMPLE_RETURN
- expression/procedure/objective: simple_return = price_t / max(price_t_minus_1, epsilon) - 1
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_simple_return`
- inputs/variables: `['price_t', 'price_t_minus_1']`
- outputs/objective meaning: `['simple_return']`
- test_vector: `PR162D_R2A_TV_FORMULA::SIMPLE_RETURN`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::ROLLING_VOLATILITY
- expression/procedure/objective: rolling_volatility = std(returns_window)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_rolling_volatility`
- inputs/variables: `['returns_window']`
- outputs/objective meaning: `['rolling_volatility']`
- test_vector: `PR162D_R2A_TV_FORMULA::ROLLING_VOLATILITY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::VWAP
- expression/procedure/objective: vwap = sum(price_i * volume_i) / max(sum(volume_i), epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_vwap`
- inputs/variables: `['prices', 'volumes']`
- outputs/objective meaning: `['vwap']`
- test_vector: `PR162D_R2A_TV_FORMULA::VWAP`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::BOLLINGER_Z
- expression/procedure/objective: bollinger_z = (price - rolling_mean) / max(rolling_std, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_bollinger_z`
- inputs/variables: `['price', 'rolling_mean', 'rolling_std']`
- outputs/objective meaning: `['bollinger_z']`
- test_vector: `PR162D_R2A_TV_FORMULA::BOLLINGER_Z`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::RSI
- expression/procedure/objective: rsi = 100 - 100 / (1 + mean(max(delta_i,0)) / max(mean(abs(min(delta_i,0))), epsilon))
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_rsi`
- inputs/variables: `['deltas']`
- outputs/objective meaning: `['avg_gain', 'avg_loss', 'rs', 'rsi']`
- test_vector: `PR162D_R2A_TV_FORMULA::RSI`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::MACD
- expression/procedure/objective: macd = ema_fast - ema_slow; macd_signal = ema(macd, signal_alpha); macd_histogram = macd - macd_signal
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_macd`
- inputs/variables: `['ema_fast', 'ema_slow', 'signal_alpha', 'macd_signal_t_minus_1']`
- outputs/objective meaning: `['macd', 'macd_signal', 'macd_histogram']`
- test_vector: `PR162D_R2A_TV_FORMULA::MACD`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::RISK_ADJUSTED_SCORE
- expression/procedure/objective: risk_adjusted_score = expected_net_value - drawdown_penalty_lambda*drawdown_risk - latency_penalty_lambda*latency_cost - slippage_penalty_lambda*slippage_estimate - complexity_penalty_lambda*complexity_score
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_risk_adjusted_score`
- inputs/variables: `['expected_net_value', 'drawdown_penalty_lambda', 'drawdown_risk', 'latency_penalty_lambda', 'latency_cost', 'slippage_penalty_lambda', 'slippage_estimate', 'complexity_penalty_lambda', 'complexity_score']`
- outputs/objective meaning: `['risk_adjusted_score']`
- test_vector: `PR162D_R2A_TV_FORMULA::RISK_ADJUSTED_SCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::CANDIDATE_SELECTION_SCORE
- expression/procedure/objective: candidate_selection_score = replay_value_score + paper_value_score + stability_score + cross_market_generalization_score + quantum_priority_boost - latency_penalty - drawdown_penalty - data_missing_penalty - complexity_penalty
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_candidate_selection_score`
- inputs/variables: `['replay_value_score', 'paper_value_score', 'stability_score', 'cross_market_generalization_score', 'quantum_priority_boost', 'latency_penalty', 'drawdown_penalty', 'data_missing_penalty', 'complexity_penalty']`
- outputs/objective meaning: `['candidate_selection_score']`
- test_vector: `PR162D_R2A_TV_FORMULA::CANDIDATE_SELECTION_SCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::DEPTH_IMPACT_COMPONENT
- expression/procedure/objective: depth_impact_component = order_size / max(available_depth, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_depth_impact_component`
- inputs/variables: `['order_size', 'available_depth']`
- outputs/objective meaning: `['depth_impact_component']`
- test_vector: `PR162D_R2A_TV_FORMULA::DEPTH_IMPACT_COMPONENT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::VOLATILITY_IMPACT_COMPONENT
- expression/procedure/objective: volatility_impact_component = rolling_volatility * sqrt(holding_period_seconds)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_volatility_impact_component`
- inputs/variables: `['rolling_volatility', 'holding_period_seconds']`
- outputs/objective meaning: `['volatility_impact_component']`
- test_vector: `PR162D_R2A_TV_FORMULA::VOLATILITY_IMPACT_COMPONENT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::SPREAD_COMPONENT
- expression/procedure/objective: spread_component = spread * spread_capture_fraction
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_spread_component`
- inputs/variables: `['spread', 'spread_capture_fraction']`
- outputs/objective meaning: `['spread_component']`
- test_vector: `PR162D_R2A_TV_FORMULA::SPREAD_COMPONENT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::DEPTH_WEIGHTED_MID_PRICE
- expression/procedure/objective: depth_weighted_mid_price = (best_bid*ask_size + best_ask*bid_size) / max(bid_size + ask_size, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_depth_weighted_mid_price`
- inputs/variables: `['best_bid', 'best_ask', 'bid_size', 'ask_size']`
- outputs/objective meaning: `['depth_weighted_mid_price']`
- test_vector: `PR162D_R2A_TV_FORMULA::DEPTH_WEIGHTED_MID_PRICE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::TOP_OF_BOOK_DEPTH
- expression/procedure/objective: top_of_book_depth = bid_size + ask_size
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_top_of_book_depth`
- inputs/variables: `['bid_size', 'ask_size']`
- outputs/objective meaning: `['top_of_book_depth']`
- test_vector: `PR162D_R2A_TV_FORMULA::TOP_OF_BOOK_DEPTH`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::MARKET_PRESSURE
- expression/procedure/objective: market_pressure = orderbook_imbalance * relative_spread
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_market_pressure`
- inputs/variables: `['orderbook_imbalance', 'relative_spread']`
- outputs/objective meaning: `['market_pressure']`
- test_vector: `PR162D_R2A_TV_FORMULA::MARKET_PRESSURE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::VOLUME_GROWTH_RATE
- expression/procedure/objective: volume_growth_rate = volume_t / max(volume_t_minus_1, epsilon) - 1
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_volume_growth_rate`
- inputs/variables: `['volume_t', 'volume_t_minus_1']`
- outputs/objective meaning: `['volume_growth_rate']`
- test_vector: `PR162D_R2A_TV_FORMULA::VOLUME_GROWTH_RATE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::CANDLE_RETURN
- expression/procedure/objective: candle_return = close_price / max(open_price, epsilon) - 1
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_candle_return`
- inputs/variables: `['close_price', 'open_price']`
- outputs/objective meaning: `['candle_return']`
- test_vector: `PR162D_R2A_TV_FORMULA::CANDLE_RETURN`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::HIGH_LOW_RANGE
- expression/procedure/objective: high_low_range = high_price - low_price
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_high_low_range`
- inputs/variables: `['high_price', 'low_price']`
- outputs/objective meaning: `['high_low_range']`
- test_vector: `PR162D_R2A_TV_FORMULA::HIGH_LOW_RANGE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::CANDLE_BODY
- expression/procedure/objective: candle_body = abs(close_price - open_price)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_candle_body`
- inputs/variables: `['close_price', 'open_price']`
- outputs/objective meaning: `['candle_body']`
- test_vector: `PR162D_R2A_TV_FORMULA::CANDLE_BODY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::WICK_RATIO
- expression/procedure/objective: wick_ratio = ((high_price - low_price) - abs(close_price - open_price)) / max(high_price - low_price, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_wick_ratio`
- inputs/variables: `['high_price', 'low_price', 'close_price', 'open_price']`
- outputs/objective meaning: `['wick_ratio']`
- test_vector: `PR162D_R2A_TV_FORMULA::WICK_RATIO`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::REALIZED_SPREAD_PROXY
- expression/procedure/objective: realized_spread_proxy = abs(execution_price - mid_price_after_delay)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_realized_spread_proxy`
- inputs/variables: `['execution_price', 'mid_price_after_delay']`
- outputs/objective meaning: `['realized_spread_proxy']`
- test_vector: `PR162D_R2A_TV_FORMULA::REALIZED_SPREAD_PROXY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::MOMENTUM_N_PERIOD
- expression/procedure/objective: momentum_n_period = price_t - price_t_minus_n
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_momentum_n_period`
- inputs/variables: `['price_t', 'price_t_minus_n']`
- outputs/objective meaning: `['momentum_n_period']`
- test_vector: `PR162D_R2A_TV_FORMULA::MOMENTUM_N_PERIOD`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::PRICE_ZSCORE
- expression/procedure/objective: price_zscore = (price - mean_price) / max(std_price, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_price_zscore`
- inputs/variables: `['price', 'mean_price', 'std_price']`
- outputs/objective meaning: `['price_zscore']`
- test_vector: `PR162D_R2A_TV_FORMULA::PRICE_ZSCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::SHARPE_LIKE_SCORE
- expression/procedure/objective: sharpe_like_score = mean_return / max(return_volatility, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_sharpe_like_score`
- inputs/variables: `['mean_return', 'return_volatility']`
- outputs/objective meaning: `['sharpe_like_score']`
- test_vector: `PR162D_R2A_TV_FORMULA::SHARPE_LIKE_SCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::EXPECTED_SHORTFALL_PROXY
- expression/procedure/objective: expected_shortfall_proxy = mean(losses >= var_threshold)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_expected_shortfall_proxy`
- inputs/variables: `['losses', 'var_threshold']`
- outputs/objective meaning: `['expected_shortfall_proxy']`
- test_vector: `PR162D_R2A_TV_FORMULA::EXPECTED_SHORTFALL_PROXY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::CAPITAL_UTILIZATION
- expression/procedure/objective: capital_utilization = capital_used / max(capital_budget, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_capital_utilization`
- inputs/variables: `['capital_used', 'capital_budget']`
- outputs/objective meaning: `['capital_utilization']`
- test_vector: `PR162D_R2A_TV_FORMULA::CAPITAL_UTILIZATION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::EXPOSURE_UTILIZATION
- expression/procedure/objective: exposure_utilization = exposure_used / max(max_exposure, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_exposure_utilization`
- inputs/variables: `['exposure_used', 'max_exposure']`
- outputs/objective meaning: `['exposure_utilization']`
- test_vector: `PR162D_R2A_TV_FORMULA::EXPOSURE_UTILIZATION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::COST_TO_BUDGET_RATIO
- expression/procedure/objective: cost_to_budget_ratio = candidate_cost / max(budget, epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_cost_to_budget_ratio`
- inputs/variables: `['candidate_cost', 'budget']`
- outputs/objective meaning: `['cost_to_budget_ratio']`
- test_vector: `PR162D_R2A_TV_FORMULA::COST_TO_BUDGET_RATIO`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::LOGIT
- expression/procedure/objective: logit = log(p_model / (1 - p_model))
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_logit`
- inputs/variables: `['p_model']`
- outputs/objective meaning: `['logit']`
- test_vector: `PR162D_R2A_TV_FORMULA::LOGIT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::SIGMOID_PROBABILITY
- expression/procedure/objective: sigmoid_probability = 1 / (1 + exp(-logit))
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_sigmoid_probability`
- inputs/variables: `['logit']`
- outputs/objective meaning: `['sigmoid_probability']`
- test_vector: `PR162D_R2A_TV_FORMULA::SIGMOID_PROBABILITY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::PROBABILITY_CALIBRATION_ERROR
- expression/procedure/objective: probability_calibration_error = observed_frequency - predicted_probability
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_probability_calibration_error`
- inputs/variables: `['observed_frequency', 'predicted_probability']`
- outputs/objective meaning: `['probability_calibration_error']`
- test_vector: `PR162D_R2A_TV_FORMULA::PROBABILITY_CALIBRATION_ERROR`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::BINARY_ENTROPY
- expression/procedure/objective: binary_entropy = -(p*log(p) + (1-p)*log(1-p))
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_binary_entropy`
- inputs/variables: `['probability']`
- outputs/objective meaning: `['binary_entropy']`
- test_vector: `PR162D_R2A_TV_FORMULA::BINARY_ENTROPY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::ENSEMBLE_PROBABILITY_MEAN
- expression/procedure/objective: ensemble_probability_mean = mean(probabilities)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_ensemble_probability_mean`
- inputs/variables: `['probabilities']`
- outputs/objective meaning: `['ensemble_probability_mean']`
- test_vector: `PR162D_R2A_TV_FORMULA::ENSEMBLE_PROBABILITY_MEAN`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::WEIGHTED_SIGNAL_SCORE
- expression/procedure/objective: weighted_signal_score = sum(signal_i*weight_i)/max(sum(weights), epsilon)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_weighted_signal_score`
- inputs/variables: `['signals', 'weights']`
- outputs/objective meaning: `['weighted_signal_score']`
- test_vector: `PR162D_R2A_TV_FORMULA::WEIGHTED_SIGNAL_SCORE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### FORMULA::COVARIANCE_PENALTY
- expression/procedure/objective: covariance_penalty = lambda_risk * w^T covariance w
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_covariance_penalty`
- inputs/variables: `['weights', 'covariance', 'lambda_risk']`
- outputs/objective meaning: `['covariance_penalty']`
- test_vector: `PR162D_R2A_TV_FORMULA::COVARIANCE_PENALTY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

## Algorithm Procedures
### ALGORITHM::DETERMINISTIC_CANDIDATE_RANKING
- expression/procedure/objective: Filter invalid candidates, compute final_score, sort descending, and tie-break by latency_class, risk_class, candidate_id.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- inputs/variables: `['candidates']`
- outputs/objective meaning: `['ranked_candidate_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::DETERMINISTIC_CANDIDATE_RANKING`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::GREEDY_MARKET_BUNDLE_SELECTION
- expression/procedure/objective: Sort candidates by expected_net_value/capital_required and greedily add while budget and exposure remain satisfied.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- inputs/variables: `['candidates', 'budget', 'max_exposure']`
- outputs/objective meaning: `['selected_candidate_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::GREEDY_MARKET_BUNDLE_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::REPLAY_PAPER_ELIGIBILITY_ROUTER
- expression/procedure/objective: Route materialized formulations with route records to replay/paper, create route fill actions for route gaps, and field-fill actions for unmaterialized records.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:replay_paper_eligibility_router`
- inputs/variables: `['formulation_record', 'route_record']`
- outputs/objective meaning: `['route_state', 'fill_action']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::REPLAY_PAPER_ELIGIBILITY_ROUTER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::PARAMETER_STACK_SELECTOR
- expression/procedure/objective: Reject incompatible parameter stacks, compute deterministic stack score, rank, and select the top stack.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:parameter_stack_selector`
- inputs/variables: `['stacks']`
- outputs/objective meaning: `['selected_stack_candidate']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::PARAMETER_STACK_SELECTOR`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::BUILD_PARAMETER_PACK_FROM_DEFAULTS
- expression/procedure/objective: Return a versioned parameter pack from candidate defaults and ranges.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:build_parameter_pack_from_defaults`
- inputs/variables: `['defaults', 'ranges', 'version']`
- outputs/objective meaning: `['parameter_pack']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::BUILD_PARAMETER_PACK_FROM_DEFAULTS`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::STABLE_DEDUPE_BY_FAMILY
- expression/procedure/objective: Sort records, keep first record per equivalence family, and preserve duplicate provenance externally.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:stable_dedupe_by_family`
- inputs/variables: `['records']`
- outputs/objective meaning: `['canonical_record_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::STABLE_DEDUPE_BY_FAMILY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::TOP_K_CANDIDATE_FILTER
- expression/procedure/objective: Rank candidates with deterministic ordering and return the top k candidate IDs.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:top_k_candidate_filter`
- inputs/variables: `['candidates', 'k']`
- outputs/objective meaning: `['top_candidate_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::TOP_K_CANDIDATE_FILTER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::LATENCY_BUCKET_ROUTER
- expression/procedure/objective: Group candidates by latency class for hot path and precompute planning.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:latency_bucket_router`
- inputs/variables: `['candidates']`
- outputs/objective meaning: `['latency_buckets']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::LATENCY_BUCKET_ROUTER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::SOURCE_CONFIDENCE_RANKER
- expression/procedure/objective: Rank candidate source locators by confidence while preserving candidate status.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:source_confidence_ranker`
- inputs/variables: `['sources']`
- outputs/objective meaning: `['ranked_source_locator_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::SOURCE_CONFIDENCE_RANKER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::FIELD_FILL_PRIORITY_ORDER
- expression/procedure/objective: Order exact field-fill actions by materialization priority.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:field_fill_priority_order`
- inputs/variables: `['actions']`
- outputs/objective meaning: `['ordered_fill_action_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::FIELD_FILL_PRIORITY_ORDER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::ROUTE_FILL_PRIORITY_ORDER
- expression/procedure/objective: Order route-fill actions by route-fill need score.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:route_fill_priority_order`
- inputs/variables: `['actions']`
- outputs/objective meaning: `['ordered_route_fill_action_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::ROUTE_FILL_PRIORITY_ORDER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::PORTFOLIO_EXPOSURE_CHECK
- expression/procedure/objective: Sum candidate exposures and verify whether max exposure is satisfied.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:portfolio_exposure_check`
- inputs/variables: `['positions', 'max_exposure']`
- outputs/objective meaning: `['exposure', 'within_limit_flag']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::PORTFOLIO_EXPOSURE_CHECK`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::PARAMETER_RANGE_CLIPPER
- expression/procedure/objective: Clip a candidate parameter value into a deterministic min/max range.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:parameter_range_clipper`
- inputs/variables: `['value', 'min_value', 'max_value']`
- outputs/objective meaning: `['clipped_value']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::PARAMETER_RANGE_CLIPPER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::COMPATIBILITY_THRESHOLD_FILTER
- expression/procedure/objective: Keep candidates with compatibility scores above a deterministic threshold.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:compatibility_threshold_filter`
- inputs/variables: `['candidates', 'threshold']`
- outputs/objective meaning: `['compatible_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::COMPATIBILITY_THRESHOLD_FILTER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::QUANTUM_PRIORITY_RANKER
- expression/procedure/objective: Rank candidates by quantum priority for batch optimizer materialization.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:quantum_priority_ranker`
- inputs/variables: `['candidates']`
- outputs/objective meaning: `['ranked_quantum_candidate_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::QUANTUM_PRIORITY_RANKER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::FAMILY_VARIANT_NORMALIZER
- expression/procedure/objective: Normalize a raw mention label into deterministic domain and variant keys.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:family_variant_normalizer`
- inputs/variables: `['raw_label']`
- outputs/objective meaning: `['domain_family_key', 'variant_key']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::FAMILY_VARIANT_NORMALIZER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::REPLAY_PAPER_BATCH_PARTITION
- expression/procedure/objective: Partition candidate IDs into stable replay/paper adapter batches.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:replay_paper_batch_partition`
- inputs/variables: `['candidate_ids', 'batch_size']`
- outputs/objective meaning: `['batches']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::REPLAY_PAPER_BATCH_PARTITION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::CACHEABILITY_CLASSIFIER
- expression/procedure/objective: Classify compute tiers that can be cached or precomputed.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:cacheability_classifier`
- inputs/variables: `['compute_tier']`
- outputs/objective meaning: `['cacheable']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::CACHEABILITY_CLASSIFIER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::HOT_PATH_PRECOMPUTE_SELECTOR
- expression/procedure/objective: Split formulations into future hot-path candidates and precompute-required candidates.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:hot_path_precompute_selector`
- inputs/variables: `['formulations']`
- outputs/objective meaning: `['hot_path_candidate_ids', 'precompute_required_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::HOT_PATH_PRECOMPUTE_SELECTOR`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::FORMULA_COVERAGE_CLASSIFIER
- expression/procedure/objective: Count formulation-backed and unmapped formulation attempts.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:formula_coverage_classifier`
- inputs/variables: `['mappings']`
- outputs/objective meaning: `['formulation_backed_count', 'formulation_unmapped_count']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::FORMULA_COVERAGE_CLASSIFIER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::EXACT_FILL_ACTION_BUILDER
- expression/procedure/objective: Create a deterministic exact field-fill action payload after mapping attempts fail.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:exact_fill_action_builder`
- inputs/variables: `['missing_field', 'responsible_agent', 'priority_score']`
- outputs/objective meaning: `['fill_action']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::EXACT_FILL_ACTION_BUILDER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::OWNER_REVIEW_ESCALATION_SELECTOR
- expression/procedure/objective: Select owner-review rows only after deterministic materialization attempts fail or exceed priority threshold.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:owner_review_escalation_selector`
- inputs/variables: `['records', 'threshold']`
- outputs/objective meaning: `['owner_review_record_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::OWNER_REVIEW_ESCALATION_SELECTOR`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::MARKET_BUNDLE_DIVERSIFIER
- expression/procedure/objective: Select highest-scoring candidates while limiting one candidate per family.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier`
- inputs/variables: `['candidates']`
- outputs/objective meaning: `['diversified_candidate_ids']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::MARKET_BUNDLE_DIVERSIFIER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::OBJECTIVE_CONSTRAINT_PAIRER
- expression/procedure/objective: Pair objective refs with constraint refs for objective/constraint/solver records.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:objective_constraint_pairer`
- inputs/variables: `['objective_refs', 'constraint_refs']`
- outputs/objective meaning: `['objective_constraint_pairs']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::OBJECTIVE_CONSTRAINT_PAIRER`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### ALGORITHM::COMPARATOR_ASSIGNMENT
- expression/procedure/objective: Attach a deterministic classical comparator to each quantum formulation.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:comparator_assignment`
- inputs/variables: `['quantum_records', 'default_comparator_ref']`
- outputs/objective meaning: `['classical_comparator_assignments']`
- test_vector: `PR162D_R2A_TV_ALGORITHM::COMPARATOR_ASSIGNMENT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

## Quantum Formulations
### QUANTUM::QUBO_MARKET_BUNDLE_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_MARKET_BUNDLE_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::CQM_CONSTRAINED_CAPITAL_ALLOCATION
- expression/procedure/objective: maximize sum(x_i*expected_net_value_i) - lambda_drawdown*drawdown_risk(x) - lambda_latency*latency_cost(x) - lambda_slippage*slippage_cost(x)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_cqm_constrained_capital_allocation`
- inputs/variables: `['x_A', 'x_B', 'size_A', 'size_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::CQM_CONSTRAINED_CAPITAL_ALLOCATION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_PARAMETER_STACK_SELECTION
- expression/procedure/objective: -sum(stack_score_i*x_i) + lambda_onehot*(sum(x_i)-1)^2 + lambda_incompat*sum(incompatibility_ij*x_i*x_j)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_parameter_stack_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_PARAMETER_STACK_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::LATENCY_ADJUSTED_OPPORTUNITY_SELECTION
- expression/procedure/objective: -sum(expected_net_value_i*x_i) + lambda_latency*sum(latency_cost_i*x_i) + lambda_slippage*sum(slippage_cost_i*x_i) + lambda_risk*portfolio_risk(x)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_latency_adjusted_opportunity_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::LATENCY_ADJUSTED_OPPORTUNITY_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::ISING_BINARY_SELECTION
- expression/procedure/objective: sum(h_i*s_i) + sum(J_ij*s_i*s_j), where s_i in {-1,1}
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_ising_binary_selection`
- inputs/variables: `['s_A', 's_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::ISING_BINARY_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QAOA_CANDIDATE_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qaoa_candidate_selection_shape`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QAOA_CANDIDATE_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::ANNEALING_CANDIDATE_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_annealing_candidate_selection_shape`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::ANNEALING_CANDIDATE_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::BQM_RISK_BALANCED_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_bqm_risk_balanced_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::BQM_RISK_BALANCED_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::CQM_ROUTE_FILL_ALLOCATION
- expression/procedure/objective: maximize sum(route_unlock_score_i*x_i) - lambda_complexity*sum(complexity_i*x_i)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_cqm_route_fill_allocation`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::CQM_ROUTE_FILL_ALLOCATION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_STAGE1_SIGNAL_BUNDLE
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_STAGE1_SIGNAL_BUNDLE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_LIQUIDITY_BUNDLE
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_LIQUIDITY_BUNDLE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_RISK_CAPPED_BUNDLE
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_RISK_CAPPED_BUNDLE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_CROSS_MARKET_BUNDLE
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_CROSS_MARKET_BUNDLE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_REPLAY_VALUE_BUNDLE
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_REPLAY_VALUE_BUNDLE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_PAPER_VALUE_BUNDLE
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_market_bundle_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_PAPER_VALUE_BUNDLE`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::CQM_CAPITAL_BUDGET_STRICT
- expression/procedure/objective: maximize sum(x_i*expected_net_value_i) - lambda_drawdown*drawdown_risk(x) - lambda_latency*latency_cost(x) - lambda_slippage*slippage_cost(x)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_cqm_constrained_capital_allocation`
- inputs/variables: `['x_A', 'x_B', 'size_A', 'size_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::CQM_CAPITAL_BUDGET_STRICT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::CQM_EXPOSURE_BUDGET_STRICT
- expression/procedure/objective: maximize sum(x_i*expected_net_value_i) - lambda_drawdown*drawdown_risk(x) - lambda_latency*latency_cost(x) - lambda_slippage*slippage_cost(x)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_cqm_constrained_capital_allocation`
- inputs/variables: `['x_A', 'x_B', 'size_A', 'size_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::CQM_EXPOSURE_BUDGET_STRICT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_STACK_ONEHOT
- expression/procedure/objective: -sum(stack_score_i*x_i) + lambda_onehot*(sum(x_i)-1)^2 + lambda_incompat*sum(incompatibility_ij*x_i*x_j)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_parameter_stack_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_STACK_ONEHOT`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_STACK_INCOMPATIBILITY
- expression/procedure/objective: -sum(stack_score_i*x_i) + lambda_onehot*(sum(x_i)-1)^2 + lambda_incompat*sum(incompatibility_ij*x_i*x_j)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qubo_parameter_stack_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_STACK_INCOMPATIBILITY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_LATENCY_ONLY
- expression/procedure/objective: -sum(expected_net_value_i*x_i) + lambda_latency*sum(latency_cost_i*x_i) + lambda_slippage*sum(slippage_cost_i*x_i) + lambda_risk*portfolio_risk(x)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_latency_adjusted_opportunity_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_LATENCY_ONLY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QUBO_SLIPPAGE_ONLY
- expression/procedure/objective: -sum(expected_net_value_i*x_i) + lambda_latency*sum(latency_cost_i*x_i) + lambda_slippage*sum(slippage_cost_i*x_i) + lambda_risk*portfolio_risk(x)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_latency_adjusted_opportunity_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QUBO_SLIPPAGE_ONLY`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::ISING_OPPORTUNITY_SPIN
- expression/procedure/objective: sum(h_i*s_i) + sum(J_ij*s_i*s_j), where s_i in {-1,1}
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_ising_binary_selection`
- inputs/variables: `['s_A', 's_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::ISING_OPPORTUNITY_SPIN`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::QAOA_RISK_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_qaoa_candidate_selection_shape`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::QAOA_RISK_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::ANNEALING_ROUTE_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_annealing_candidate_selection_shape`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::ANNEALING_ROUTE_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

### QUANTUM::BQM_LOW_CORRELATION_SELECTION
- expression/procedure/objective: -sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j)
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library:build_bqm_risk_balanced_selection`
- inputs/variables: `['x_A', 'x_B']`
- outputs/objective meaning: `Deterministic local optimizer-shape payload for replay/paper research candidate construction.`
- test_vector: `PR162D_R2A_TV_QUANTUM::BQM_LOW_CORRELATION_SELECTION`
- source_truth_status: `OWNER_TEMPLATE`
- live_order_authority: false

## Classical Comparator Mappings
### CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION::VARIANT_01
- procedure: Greedy EV/capital baseline for QUBO bundle selection.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- compared_quantum_family: `QUBO_MARKET_BUNDLE_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR::VARIANT_02
- procedure: MIP-style comparator placeholder using deterministic greedy local baseline until PR162R/PR163 solver wiring.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- compared_quantum_family: `CQM_CONSTRAINED_CAPITAL_ALLOCATION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::DETERMINISTIC_CANDIDATE_RANKING::VARIANT_03
- procedure: Stable ranking comparator for one-hot stack selection.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `QUBO_PARAMETER_STACK_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::RISK_ADJUSTED_SCORE_RANKING::VARIANT_04
- procedure: Risk-adjusted score baseline comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_risk_adjusted_score`
- compared_quantum_family: `LATENCY_ADJUSTED_OPPORTUNITY_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::BRUTE_FORCE_BINARY_ENUMERATION::VARIANT_05
- procedure: Local deterministic enumeration candidate baseline.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:top_k_candidate_filter`
- compared_quantum_family: `ISING_BINARY_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR::VARIANT_06
- procedure: Mean-variance-style diversified greedy comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier`
- compared_quantum_family: `QAOA_CANDIDATE_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::DIVERSIFIED_GREEDY_COMPARATOR::VARIANT_07
- procedure: Family-diversified greedy comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier`
- compared_quantum_family: `ANNEALING_CANDIDATE_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::REPLAY_VALUE_RANKING_COMPARATOR::VARIANT_08
- procedure: Replay-value deterministic ranking comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `BQM_RISK_BALANCED_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::PAPER_VALUE_RANKING_COMPARATOR::VARIANT_09
- procedure: Paper-value deterministic ranking comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `CQM_ROUTE_FILL_ALLOCATION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::PARAMETER_STACK_SELECTOR::VARIANT_10
- procedure: Parameter-stack selector comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:parameter_stack_selector`
- compared_quantum_family: `QUBO_STAGE1_SIGNAL_BUNDLE`
- live_order_authority: false

### CLASSICAL_COMPARATOR::ROUTE_FILL_PRIORITY_ORDER::VARIANT_11
- procedure: Route-fill priority comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:route_fill_priority_order`
- compared_quantum_family: `QUBO_LIQUIDITY_BUNDLE`
- live_order_authority: false

### CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION::VARIANT_12
- procedure: Greedy EV/capital baseline for QUBO bundle selection.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- compared_quantum_family: `QUBO_RISK_CAPPED_BUNDLE`
- live_order_authority: false

### CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR::VARIANT_13
- procedure: MIP-style comparator placeholder using deterministic greedy local baseline until PR162R/PR163 solver wiring.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- compared_quantum_family: `QUBO_CROSS_MARKET_BUNDLE`
- live_order_authority: false

### CLASSICAL_COMPARATOR::DETERMINISTIC_CANDIDATE_RANKING::VARIANT_14
- procedure: Stable ranking comparator for one-hot stack selection.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `QUBO_REPLAY_VALUE_BUNDLE`
- live_order_authority: false

### CLASSICAL_COMPARATOR::RISK_ADJUSTED_SCORE_RANKING::VARIANT_15
- procedure: Risk-adjusted score baseline comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_risk_adjusted_score`
- compared_quantum_family: `QUBO_PAPER_VALUE_BUNDLE`
- live_order_authority: false

### CLASSICAL_COMPARATOR::BRUTE_FORCE_BINARY_ENUMERATION::VARIANT_16
- procedure: Local deterministic enumeration candidate baseline.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:top_k_candidate_filter`
- compared_quantum_family: `CQM_CAPITAL_BUDGET_STRICT`
- live_order_authority: false

### CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR::VARIANT_17
- procedure: Mean-variance-style diversified greedy comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier`
- compared_quantum_family: `CQM_EXPOSURE_BUDGET_STRICT`
- live_order_authority: false

### CLASSICAL_COMPARATOR::DIVERSIFIED_GREEDY_COMPARATOR::VARIANT_18
- procedure: Family-diversified greedy comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier`
- compared_quantum_family: `QUBO_STACK_ONEHOT`
- live_order_authority: false

### CLASSICAL_COMPARATOR::REPLAY_VALUE_RANKING_COMPARATOR::VARIANT_19
- procedure: Replay-value deterministic ranking comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `QUBO_STACK_INCOMPATIBILITY`
- live_order_authority: false

### CLASSICAL_COMPARATOR::PAPER_VALUE_RANKING_COMPARATOR::VARIANT_20
- procedure: Paper-value deterministic ranking comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `QUBO_LATENCY_ONLY`
- live_order_authority: false

### CLASSICAL_COMPARATOR::PARAMETER_STACK_SELECTOR::VARIANT_21
- procedure: Parameter-stack selector comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:parameter_stack_selector`
- compared_quantum_family: `QUBO_SLIPPAGE_ONLY`
- live_order_authority: false

### CLASSICAL_COMPARATOR::ROUTE_FILL_PRIORITY_ORDER::VARIANT_22
- procedure: Route-fill priority comparator.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:route_fill_priority_order`
- compared_quantum_family: `ISING_OPPORTUNITY_SPIN`
- live_order_authority: false

### CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION::VARIANT_23
- procedure: Greedy EV/capital baseline for QUBO bundle selection.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- compared_quantum_family: `QAOA_RISK_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR::VARIANT_24
- procedure: MIP-style comparator placeholder using deterministic greedy local baseline until PR162R/PR163 solver wiring.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection`
- compared_quantum_family: `ANNEALING_ROUTE_SELECTION`
- live_order_authority: false

### CLASSICAL_COMPARATOR::DETERMINISTIC_CANDIDATE_RANKING::VARIANT_25
- procedure: Stable ranking comparator for one-hot stack selection.
- callable_ref: `src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking`
- compared_quantum_family: `BQM_LOW_CORRELATION_SELECTION`
- live_order_authority: false
