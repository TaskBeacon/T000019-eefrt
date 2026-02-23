from __future__ import annotations

from dataclasses import dataclass
import math
import random as _py_random
from typing import Any

from psyflow.sim.contracts import Action, Feedback, Observation, SessionInfo


@dataclass
class TaskSamplerResponder:
    """Task-specific EEfRT sampler responder.

    - `offer_choice` phase: choose easy/hard option from utility model.
    - `effort_execution_window` phase: provide effort key with press-rate metadata.
    - Other phases: provide quick continue key if valid.
    """

    easy_key: str = "f"
    hard_key: str = "j"
    effort_key: str = "space"

    lapse_rate: float = 0.03
    choice_rt_mean_s: float = 0.45
    choice_rt_sd_s: float = 0.08

    hard_choice_bias: float = -0.3
    hard_choice_reward_weight: float = 0.45
    hard_choice_prob_weight: float = 1.8
    hard_choice_effort_weight: float = 0.05

    base_press_rate_hz: float = 8.5
    hard_press_rate_penalty_hz: float = 1.2
    press_rate_sd_hz: float = 0.8

    min_rt_s: float = 0.08
    continue_rt_s: float = 0.2

    def __post_init__(self) -> None:
        self._rng: Any = None
        self.lapse_rate = max(0.0, min(1.0, float(self.lapse_rate)))
        self.choice_rt_mean_s = float(self.choice_rt_mean_s)
        self.choice_rt_sd_s = max(1e-6, float(self.choice_rt_sd_s))
        self.base_press_rate_hz = max(0.1, float(self.base_press_rate_hz))
        self.hard_press_rate_penalty_hz = max(0.0, float(self.hard_press_rate_penalty_hz))
        self.press_rate_sd_hz = max(1e-6, float(self.press_rate_sd_hz))
        self.min_rt_s = max(0.01, float(self.min_rt_s))
        self.continue_rt_s = max(self.min_rt_s, float(self.continue_rt_s))

    def start_session(self, session: SessionInfo, rng: Any) -> None:
        self._rng = rng

    def on_feedback(self, fb: Feedback) -> None:
        return None

    def end_session(self) -> None:
        self._rng = None

    def _random(self) -> float:
        rng = self._rng
        if hasattr(rng, "random"):
            return float(rng.random())
        return float(_py_random.random())

    def _normal(self, mean: float, sd: float) -> float:
        rng = self._rng
        if hasattr(rng, "normal"):
            return float(rng.normal(mean, sd))
        return float(_py_random.gauss(mean, sd))

    @staticmethod
    def _sigmoid(x: float) -> float:
        # numerically stable sigmoid
        if x >= 0:
            z = math.exp(-x)
            return 1.0 / (1.0 + z)
        z = math.exp(x)
        return z / (1.0 + z)

    def _choice_action(self, obs: Observation) -> Action:
        factors = dict(obs.task_factors or {})
        valid = list(obs.valid_keys or [])
        phase = str(obs.phase or factors.get("stage") or "").strip().lower() or "offer_choice"
        easy_key = self.easy_key if self.easy_key in valid else (valid[0] if valid else None)
        hard_key = self.hard_key if self.hard_key in valid else (valid[-1] if valid else None)
        if not valid or easy_key is None or hard_key is None:
            return Action(key=None, rt_s=None, meta={"source": "eefrt_sampler", "reason": "no_valid_choice_keys"})

        if self._random() < self.lapse_rate:
            return Action(key=None, rt_s=None, meta={"source": "eefrt_sampler", "phase": phase, "outcome": "lapse"})

        prob = float(factors.get("offer_probability", 0.5))
        hard_reward = float(factors.get("offer_hard_reward", 2.0))
        easy_reward = float(factors.get("offer_easy_reward", 1.0))
        easy_req = float(factors.get("easy_required_presses", 30.0))
        hard_req = float(factors.get("hard_required_presses", 100.0))

        utility_hard = (
            self.hard_choice_bias
            + self.hard_choice_reward_weight * (hard_reward - easy_reward)
            + self.hard_choice_prob_weight * (prob - 0.5)
            - self.hard_choice_effort_weight * max(0.0, hard_req - easy_req)
        )
        p_hard = self._sigmoid(utility_hard)
        choose_hard = self._random() < p_hard
        key = hard_key if choose_hard else easy_key
        rt = max(self.min_rt_s, self._normal(self.choice_rt_mean_s, self.choice_rt_sd_s))
        return Action(
            key=key,
            rt_s=rt,
            meta={
                "source": "eefrt_sampler",
                "phase": phase,
                "p_hard": p_hard,
                "utility_hard": utility_hard,
                "choice_option": "hard" if choose_hard else "easy",
            },
        )

    def _effort_action(self, obs: Observation) -> Action:
        factors = dict(obs.task_factors or {})
        valid = list(obs.valid_keys or [])
        phase = str(obs.phase or factors.get("stage") or "").strip().lower() or "effort_execution_window"
        effort_key = self.effort_key if self.effort_key in valid else (valid[0] if valid else None)
        if effort_key is None:
            return Action(key=None, rt_s=None, meta={"source": "eefrt_sampler", "reason": "no_valid_effort_key"})

        if self._random() < self.lapse_rate:
            return Action(key=None, rt_s=None, meta={"source": "eefrt_sampler", "phase": phase, "outcome": "lapse"})

        choice_option = str(factors.get("choice_option", "easy"))
        base_rate = self.base_press_rate_hz
        if choice_option == "hard":
            base_rate -= self.hard_press_rate_penalty_hz
        sampled_rate = max(0.3, self._normal(base_rate, self.press_rate_sd_hz))
        rt = max(self.min_rt_s, 1.0 / sampled_rate)

        return Action(
            key=effort_key,
            rt_s=rt,
            meta={
                "source": "eefrt_sampler",
                "phase": phase,
                "press_rate_hz": sampled_rate,
                "choice_option": choice_option,
            },
        )

    def act(self, obs: Observation) -> Action:
        factors = dict(obs.task_factors or {})
        phase = str(obs.phase or factors.get("stage") or "").strip().lower()
        valid = list(obs.valid_keys or [])

        if phase in {"offer_choice", "anticipation"}:
            return self._choice_action(obs)
        if phase in {"effort_execution_window", "target"}:
            return self._effort_action(obs)

        if valid:
            return Action(
                key=valid[0],
                rt_s=self.continue_rt_s,
                meta={"source": "eefrt_sampler", "phase": phase, "outcome": "continue"},
            )
        return Action(key=None, rt_s=None, meta={"source": "eefrt_sampler", "phase": phase, "outcome": "no_response"})
