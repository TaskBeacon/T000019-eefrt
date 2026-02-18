from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import random
from typing import Any

from psychopy import logging


@dataclass
class Controller:
    """Offer generator + trial outcome helper for EEfRT."""

    probability_levels: list[float] = field(default_factory=lambda: [0.12, 0.50, 0.88])
    hard_reward_levels: list[float] = field(
        default_factory=lambda: [1.24, 1.68, 2.11, 2.55, 2.99, 3.43, 3.86, 4.30]
    )
    randomize_order: bool = True
    no_choice_hard_prob: float = 0.5
    enable_logging: bool = True

    def __post_init__(self) -> None:
        self._base_rng = random.Random(0)
        self._last_block_seed: int | None = None
        self.completed_trials: int = 0
        self._history: list[dict[str, Any]] = []

        self.probability_levels = [float(p) for p in self.probability_levels]
        self.hard_reward_levels = [round(float(r), 2) for r in self.hard_reward_levels]
        self.no_choice_hard_prob = max(0.0, min(1.0, float(self.no_choice_hard_prob)))

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "Controller":
        allowed = {
            "probability_levels",
            "hard_reward_levels",
            "randomize_order",
            "no_choice_hard_prob",
            "enable_logging",
        }
        extra = set(config.keys()) - allowed
        if extra:
            raise ValueError(f"[EEfRTController] Unsupported config keys: {sorted(extra)}")
        return cls(
            probability_levels=list(config.get("probability_levels", [0.12, 0.50, 0.88])),
            hard_reward_levels=list(
                config.get("hard_reward_levels", [1.24, 1.68, 2.11, 2.55, 2.99, 3.43, 3.86, 4.30])
            ),
            randomize_order=bool(config.get("randomize_order", True)),
            no_choice_hard_prob=float(config.get("no_choice_hard_prob", 0.5)),
            enable_logging=bool(config.get("enable_logging", True)),
        )

    def prepare_block(self, *, block_idx: int, n_trials: int, seed: int) -> list[tuple[float, float]]:
        if n_trials <= 0:
            return []

        combos = list(itertools.product(self.probability_levels, self.hard_reward_levels))
        if not combos:
            raise ValueError("[EEfRTController] No offer combinations available.")

        rng = random.Random(int(seed))
        self._base_rng = rng
        self._last_block_seed = int(seed)

        reps = n_trials // len(combos)
        rem = n_trials % len(combos)
        offers = combos * reps

        if rem > 0:
            if rem <= len(combos):
                offers.extend(rng.sample(combos, k=rem))
            else:
                offers.extend(rng.choices(combos, k=rem))

        if self.randomize_order:
            rng.shuffle(offers)

        if self.enable_logging:
            prob_dist: dict[int, int] = {}
            for p, _ in offers:
                k = int(round(p * 100))
                prob_dist[k] = prob_dist.get(k, 0) + 1
            logging.data(
                f"[EEfRTController] block={block_idx} n_trials={n_trials} seed={seed} prob_dist={prob_dist}"
            )

        return [(float(p), float(r)) for p, r in offers]

    def fallback_choice(self, *, easy_key: str, hard_key: str) -> str:
        return hard_key if self._base_rng.random() < self.no_choice_hard_prob else easy_key

    def draw_reward(self, probability: float) -> bool:
        p = max(0.0, min(1.0, float(probability)))
        return self._base_rng.random() < p

    def update(self, trial_summary: dict[str, Any]) -> None:
        self.completed_trials += 1
        self._history.append(dict(trial_summary))
        if self.enable_logging:
            choice = trial_summary.get("choice_option")
            completed = bool(trial_summary.get("effort_completed", False))
            reward = float(trial_summary.get("reward_amount", 0.0) or 0.0)
            logging.data(
                f"[EEfRTController] trial={self.completed_trials} choice={choice} completed={completed} reward={reward:.2f}"
            )

