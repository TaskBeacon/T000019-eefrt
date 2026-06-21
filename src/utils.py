from __future__ import annotations

import itertools
import random
from typing import Any

from psychopy import core, logging
from psyflow.sim import Observation, ResponderAdapter, get_context


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


def parse_offer_condition(condition: Any) -> tuple[float, float, str, int | None, str, float]:
    """Decode a scheduled EEfRT offer condition."""
    if isinstance(condition, (tuple, list)) and len(condition) >= 6:
        probability = float(condition[0])
        hard_reward = float(condition[1])
        condition_id = str(condition[2])
        trial_index = int(condition[3]) if condition[3] is not None else None
        fallback_choice = str(condition[4]).strip().lower()
        reward_draw_u = float(condition[5])
        return probability, hard_reward, condition_id, trial_index, fallback_choice, reward_draw_u
    raise ValueError(f"Unsupported EEfRT condition format: {condition!r}")


def formatted_stim_text(stim_bank: Any, stim_id: str, **kwargs: Any) -> str:
    return str(getattr(stim_bank.get_and_format(stim_id, **kwargs), "text"))


def simulate_effort_via_responder(
    *,
    trial_id: int,
    block_id: str | None,
    condition_id: str,
    task_factors: dict[str, Any],
    effort_key: str,
    deadline_s: float,
) -> tuple[int, float | None]:
    ctx = get_context()
    if ctx is None or ctx.responder is None or ctx.mode not in ("qa", "sim"):
        return 0, None

    obs = Observation(
        mode=ctx.mode,
        trial_id=trial_id,
        block_id=block_id,
        phase="effort_execution_window",
        valid_keys=[effort_key],
        deadline_s=deadline_s,
        response_window_open=True,
        response_window_s=deadline_s,
        condition_id=condition_id,
        task_factors=task_factors,
        stim_id="effort_stage",
    )
    adapter = ResponderAdapter(
        policy=str(ctx.config.sim_policy),
        default_rt_s=float(ctx.config.default_rt_s),
        clamp_rt=bool(ctx.config.clamp_rt),
        logger=ctx.sim_logger,
        session=ctx.session,
    )
    handled = adapter.handle_response(obs, ctx.responder)
    action = handled.used_action
    if action.key is None:
        return 0, None

    meta = dict(action.meta or {})
    rt = float(action.rt_s) if action.rt_s is not None else float(ctx.config.default_rt_s)
    if "press_count" in meta:
        try:
            return max(0, int(meta["press_count"])), rt
        except Exception:
            pass
    if "press_rate_hz" in meta:
        try:
            rate = max(0.0, float(meta["press_rate_hz"]))
            return max(0, int(rate * deadline_s)), rt
        except Exception:
            pass

    interval = max(0.05, rt)
    return max(1, int(deadline_s / interval)), rt


def run_effort_execution(
    *,
    win: Any,
    kb: Any,
    stim_bank: Any,
    trigger_runtime: Any,
    target: Any,
    trial_data: dict[str, Any],
    trial_id: int,
    block_id: str | None,
    condition_id: str,
    task_factors: dict[str, Any],
    choice_label: str,
    required_presses: int,
    effort_key: str,
    effort_deadline: float,
) -> dict[str, Any]:
    """Run the repeated-key effort execution phase outside run_trial orchestration."""
    prompt = stim_bank.get_and_format(
        "effort_prompt",
        choice_label=choice_label,
        required_presses=required_presses,
        effort_key=effort_key.upper(),
        time_limit_s=f"{effort_deadline:.1f}",
    )
    counter = stim_bank.get_and_format(
        "effort_counter",
        current_presses=0,
        required_presses=required_presses,
        time_left_s=f"{effort_deadline:.1f}",
    )

    onset_global = core.getAbsTime()
    trigger_runtime.send(task_factors.get("target_onset_trigger"))
    target.set_state(onset_time=0.0, onset_time_global=onset_global)

    ctx = get_context()
    responder_active = bool(ctx is not None and ctx.mode in ("qa", "sim") and ctx.responder is not None)
    press_count = 0
    first_rt = None
    close_time = effort_deadline

    if responder_active:
        prompt.draw()
        counter.draw()
        flip_time = win.flip()
        target.set_state(flip_time=flip_time)

        press_count, first_rt = simulate_effort_via_responder(
            trial_id=trial_id,
            block_id=block_id,
            condition_id=condition_id,
            task_factors=task_factors,
            effort_key=effort_key,
            deadline_s=effort_deadline,
        )
        if press_count > 0:
            trigger_runtime.send(task_factors.get("target_key_press_trigger"))
            close_time = min(effort_deadline, max(first_rt or 0.0, 0.01))
    else:
        kb.clearEvents()
        kb.clock.reset()
        stage_clock = core.Clock()
        first_flip = None

        while stage_clock.getTime() < effort_deadline and press_count < required_presses:
            elapsed = stage_clock.getTime()
            remain = max(0.0, effort_deadline - elapsed)
            counter.text = formatted_stim_text(
                stim_bank,
                "effort_counter",
                current_presses=press_count,
                required_presses=required_presses,
                time_left_s=f"{remain:.1f}",
            )
            prompt.draw()
            counter.draw()
            flip_time = win.flip()
            if first_flip is None:
                first_flip = flip_time
                target.set_state(flip_time=flip_time)

            keys = kb.getKeys(keyList=[effort_key], waitRelease=False)
            if keys:
                press_count += len(keys)
                if first_rt is None:
                    try:
                        first_rt = float(keys[0].rt)
                    except Exception:
                        first_rt = float(stage_clock.getTime())
                    trigger_runtime.send(task_factors.get("target_key_press_trigger"))

        close_time = min(effort_deadline, float(stage_clock.getTime()))

    effort_completed = press_count >= required_presses
    trigger_runtime.send(task_factors.get("target_complete_trigger" if effort_completed else "target_fail_trigger"))
    close_global = onset_global + close_time
    response_global = onset_global + float(first_rt) if first_rt is not None else None

    target.set_state(
        response=effort_key if press_count > 0 else None,
        key_press=press_count > 0,
        rt=first_rt,
        response_time=first_rt,
        response_time_global=response_global,
        hit=effort_completed,
        required_presses=required_presses,
        press_count=press_count,
        effort_deadline_s=effort_deadline,
        choice_option=task_factors.get("choice_option"),
        close_time=close_time,
        close_time_global=close_global,
    ).to_dict(trial_data)

    return {
        "press_count": press_count,
        "first_rt": first_rt,
        "close_time": close_time,
        "effort_completed": effort_completed,
    }
