"""Overfit and validation controls for PR168-GFP."""

from __future__ import annotations

import math


def sample_sufficiency_check(sample_count: int, minimum_samples: int) -> bool:
    return int(sample_count) >= int(minimum_samples)


def false_discovery_penalty(trial_count: int, effective_trial_count: int) -> float:
    trials = max(int(trial_count), 1)
    effective = max(int(effective_trial_count), 1)
    return math.sqrt(math.log(effective + 1.0) / trials)


def overfit_fdr_penalty(
    raw_edge: float,
    trial_count: int,
    effective_trial_count: int,
    confidence_penalty: float,
) -> float:
    return abs(float(raw_edge)) * float(confidence_penalty) * false_discovery_penalty(trial_count, effective_trial_count)


def deflated_score_proxy(raw_score: float, trial_count: int, skew: float = 0.0, kurtosis: float = 3.0) -> float:
    multiple_test_penalty = math.sqrt(math.log(max(int(trial_count), 1) + 1.0))
    non_normal_penalty = abs(float(skew)) + abs(float(kurtosis) - 3.0) / 10.0
    return float(raw_score) - multiple_test_penalty - non_normal_penalty


def champion_challenger_score(
    mean_reward_i: float,
    risk_penalty_i: float,
    exploration_multiplier: float,
    total_trials: int,
    trials_i: int,
) -> float:
    trials = max(int(trials_i), 1)
    total = max(int(total_trials), 2)
    exploration = float(exploration_multiplier) * math.sqrt(math.log(total) / trials)
    return float(mean_reward_i) - float(risk_penalty_i) + exploration


def purged_window_overlap_check(train_window: tuple[int, int], test_window: tuple[int, int], label_horizon: int) -> bool:
    train_start, train_end = train_window
    test_start, test_end = test_window
    return not (train_start <= test_end + int(label_horizon) and test_start <= train_end + int(label_horizon))


def embargo_window_check(test_window: tuple[int, int], train_window: tuple[int, int], embargo_size: int) -> bool:
    test_start, test_end = test_window
    train_start, train_end = train_window
    return train_end + int(embargo_size) < test_start or test_end + int(embargo_size) < train_start


def lcb_from_mean_se(mean_value: float, standard_error: float, confidence_multiplier: float) -> float:
    return float(mean_value) - float(confidence_multiplier) * float(standard_error)


def shrinkage_probability(raw_probability: float, prior_probability: float, shrinkage_weight: float) -> float:
    weight = max(0.0, min(1.0, float(shrinkage_weight)))
    return weight * float(raw_probability) + (1.0 - weight) * float(prior_probability)
