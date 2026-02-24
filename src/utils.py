from __future__ import annotations

import itertools
import random
from typing import Any

from psychopy import logging


EEFRTOfferCondition = tuple[float, float, str, int, str, float]


def build_eefrt_offer_conditions(
    n_trials: int,
    condition_labels: list[Any] | None = None,
    *,
    seed: int | None = None,
    probability_levels: list[float] | None = None,
    hard_reward_levels: list[float] | None = None,
    randomize_order: bool = True,
    no_choice_hard_prob: float = 0.5,
    enable_logging: bool = True,
    **_: Any,
) -> list[EEFRTOfferCondition]:
    """Generate hashable EEfRT trial specs for one block.

    Each tuple stores:
    `(offer_probability, hard_reward, condition_id, trial_index, fallback_choice, reward_draw_u)`
    """
    n = max(0, int(n_trials))
    if n == 0:
        return []

    probs = [float(p) for p in (probability_levels or [0.12, 0.50, 0.88])]
    rewards = [round(float(r), 2) for r in (hard_reward_levels or [1.24, 1.68, 2.11, 2.55, 2.99, 3.43, 3.86, 4.30])]
    if not probs or not rewards:
        raise ValueError("EEfRT condition generation requires non-empty probability_levels and hard_reward_levels")

    p_hard = max(0.0, min(1.0, float(no_choice_hard_prob)))
    rng = random.Random(seed if seed is not None else 0)

    combos = [(float(p), float(r)) for p, r in itertools.product(probs, rewards)]
    reps = n // len(combos)
    rem = n % len(combos)
    offers: list[tuple[float, float]] = combos * reps
    if rem > 0:
        offers.extend(rng.sample(combos, k=rem) if rem <= len(combos) else rng.choices(combos, k=rem))
    if randomize_order:
        rng.shuffle(offers)

    out: list[EEFRTOfferCondition] = []
    for trial_index, (prob, hard_reward) in enumerate(offers, start=1):
        cond_id = f"p{int(round(prob * 100)):02d}_h{hard_reward:.2f}_t{trial_index:03d}"
        fallback_choice = "hard" if rng.random() < p_hard else "easy"
        reward_draw_u = float(rng.random())
        out.append((float(prob), float(hard_reward), cond_id, int(trial_index), fallback_choice, reward_draw_u))

    if enable_logging:
        prob_dist: dict[int, int] = {}
        for prob, *_rest in out:
            key = int(round(float(prob) * 100))
            prob_dist[key] = prob_dist.get(key, 0) + 1
        logging.data(f"[EEfRTConditionGen] n_trials={n} seed={seed} prob_dist={prob_dist}")

    return out


def choose_fallback_key(*, fallback_choice: str, easy_key: str, hard_key: str) -> str:
    return hard_key if str(fallback_choice).strip().lower() == "hard" else easy_key


def reward_draw_win(*, probability: float, reward_draw_u: float) -> bool:
    p = max(0.0, min(1.0, float(probability)))
    u = max(0.0, min(1.0, float(reward_draw_u)))
    return bool(u < p)
