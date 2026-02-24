from __future__ import annotations

from functools import partial
from typing import Any

from psychopy import core

from psyflow import StimUnit, set_trial_context, next_trial_id
from psyflow.sim import Observation, ResponderAdapter, get_context
from .utils import choose_fallback_key, reward_draw_win

# run_trial uses task-specific phase labels via set_trial_context(...).


def _qa_scale_duration(duration_s: float, win) -> float:
    base = max(0.0, float(duration_s))
    ctx = get_context()
    if ctx is None or not ctx.config.enable_scaling:
        return base
    frame = float(getattr(win, "monitorFramePeriod", 1.0 / 60.0) or (1.0 / 60.0))
    min_frames = int(max(1, ctx.config.min_frames))
    scaled = base * float(ctx.config.timing_scale)
    return max(scaled, frame * min_frames)


def _parse_offer_condition(condition: Any) -> tuple[float, float, str, int | None, str, float]:
    if isinstance(condition, (tuple, list)) and len(condition) >= 6:
        probability = float(condition[0])
        hard_reward = float(condition[1])
        condition_id = str(condition[2])
        trial_index = int(condition[3]) if condition[3] is not None else None
        fallback_choice = str(condition[4]).strip().lower()
        reward_draw_u = float(condition[5])
        return probability, hard_reward, condition_id, trial_index, fallback_choice, reward_draw_u
    raise ValueError(f"Unsupported EEfRT condition format: {condition!r}")


def _simulate_effort_via_responder(
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

    # Fallback: derive approximate press count from inter-press interval.
    interval = max(0.05, rt)
    return max(1, int(deadline_s / interval)), rt


def run_trial(
    win,
    kb,
    settings,
    condition,
    stim_bank,
    trigger_runtime,
    block_id=None,
    block_idx=None,
):
    """Run one EEfRT trial."""
    probability, hard_reward, cond_id, planned_trial_index, fallback_choice, reward_draw_u = _parse_offer_condition(condition)
    trial_id = next_trial_id()

    easy_reward = float(getattr(settings, "easy_reward", 1.00))
    easy_presses = int(getattr(settings, "easy_required_presses", 30))
    hard_presses = int(getattr(settings, "hard_required_presses", 100))
    easy_deadline = _qa_scale_duration(float(getattr(settings, "easy_time_limit_s", 7.0)), win)
    hard_deadline = _qa_scale_duration(float(getattr(settings, "hard_time_limit_s", 21.0)), win)
    effort_key = str(getattr(settings, "effort_key", "space"))
    choice_keys = list(getattr(settings, "choice_keys", ["f", "j"]))
    easy_key = str(choice_keys[0])
    hard_key = str(choice_keys[1] if len(choice_keys) > 1 else choice_keys[0])

    trial_data = {
        "offer_probability": probability,
        "offer_hard_reward": hard_reward,
        "offer_easy_reward": easy_reward,
        "planned_trial_index": planned_trial_index,
    }
    make_unit = partial(StimUnit, win=win, kb=kb, runtime=trigger_runtime)

    # phase: offer_fixation
    cue = make_unit(unit_label="offer_fixation").add_stim(stim_bank.get("fixation"))
    set_trial_context(
        cue,
        trial_id=trial_id,
        phase="offer_fixation",
        deadline_s=_qa_scale_duration(float(settings.cue_duration), win),
        valid_keys=[],
        block_id=block_id,
        condition_id=cond_id,
        task_factors={
            "stage": "offer_fixation",
            "offer_probability": probability,
            "offer_hard_reward": hard_reward,
            "block_idx": block_idx,
        },
        stim_id="fixation",
    )
    cue.show(
        duration=float(settings.cue_duration),
        onset_trigger=settings.triggers.get("cue_onset"),
    ).to_dict(trial_data)

    # --- Choice stage (phase label: offer_choice) ---
    choice = (
        make_unit(unit_label="offer_choice")
        .add_stim(
            stim_bank.get_and_format(
                "choice_header",
                probability_pct=int(round(probability * 100)),
            )
        )
        .add_stim(
            stim_bank.get_and_format(
                "choice_left",
                easy_reward=f"{easy_reward:.2f}",
                easy_presses=easy_presses,
                easy_deadline_s=f"{easy_deadline:.1f}",
            )
        )
        .add_stim(
            stim_bank.get_and_format(
                "choice_right",
                hard_reward=f"{hard_reward:.2f}",
                hard_presses=hard_presses,
                hard_deadline_s=f"{hard_deadline:.1f}",
            )
        )
    )
    set_trial_context(
        choice,
        trial_id=trial_id,
        phase="offer_choice",
        deadline_s=_qa_scale_duration(float(settings.anticipation_duration), win),
        valid_keys=[easy_key, hard_key],
        block_id=block_id,
        condition_id=cond_id,
        task_factors={
            "stage": "offer_choice",
            "offer_probability": probability,
            "offer_hard_reward": hard_reward,
            "offer_easy_reward": easy_reward,
            "easy_required_presses": easy_presses,
            "hard_required_presses": hard_presses,
            "easy_key": easy_key,
            "hard_key": hard_key,
            "block_idx": block_idx,
        },
        stim_id="choice_layout",
    )
    choice.capture_response(
        keys=[easy_key, hard_key],
        correct_keys=[easy_key, hard_key],
        duration=float(settings.anticipation_duration),
        onset_trigger=settings.triggers.get("choice_onset"),
        response_trigger={
            easy_key: settings.triggers.get("choice_easy_press"),
            hard_key: settings.triggers.get("choice_hard_press"),
        },
        timeout_trigger=settings.triggers.get("choice_no_response"),
    )

    choice_key = choice.get_state("response", None)
    choice_forced = False
    if choice_key not in (easy_key, hard_key):
        choice_key = choose_fallback_key(
            fallback_choice=fallback_choice,
            easy_key=easy_key,
            hard_key=hard_key,
        )
        choice_forced = True
        trigger_runtime.send(settings.triggers.get("choice_forced"))

    choice_option = "hard" if choice_key == hard_key else "easy"
    required_presses = hard_presses if choice_option == "hard" else easy_presses
    effort_deadline = hard_deadline if choice_option == "hard" else easy_deadline
    chosen_reward = hard_reward if choice_option == "hard" else easy_reward
    choice_label = "高努力" if choice_option == "hard" else "低努力"

    choice.set_state(
        choice_key=choice_key,
        choice_option=choice_option,
        choice_forced=choice_forced,
        required_presses=required_presses,
        effort_deadline_s=effort_deadline,
        chosen_reward=chosen_reward,
    ).to_dict(trial_data)

    # --- Ready ---
    make_unit(unit_label="ready").add_stim(
        stim_bank.get_and_format(
            "ready_text",
            choice_label=choice_label,
            required_presses=required_presses,
            effort_key=effort_key.upper(),
            time_limit_s=f"{effort_deadline:.1f}",
        )
    ).show(
        duration=float(settings.ready_duration),
        onset_trigger=settings.triggers.get("ready_onset"),
    ).to_dict(trial_data)

    # --- Effort stage (phase label: effort_execution_window) ---
    target = make_unit(unit_label="effort_execution")
    target_factors = {
        "stage": "effort_execution_window",
        "choice_option": choice_option,
        "required_presses": required_presses,
        "effort_deadline_s": effort_deadline,
        "offer_probability": probability,
        "offer_hard_reward": hard_reward,
        "offer_easy_reward": easy_reward,
        "chosen_reward": chosen_reward,
        "block_idx": block_idx,
    }
    set_trial_context(
        target,
        trial_id=trial_id,
        phase="effort_execution_window",
        deadline_s=effort_deadline,
        valid_keys=[effort_key],
        block_id=block_id,
        condition_id=cond_id,
        task_factors=target_factors,
        stim_id="effort_stage",
    )

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
    trigger_runtime.send(settings.triggers.get("target_onset"))
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

        press_count, first_rt = _simulate_effort_via_responder(
            trial_id=trial_id,
            block_id=block_id,
            condition_id=cond_id,
            task_factors=target_factors,
            effort_key=effort_key,
            deadline_s=effort_deadline,
        )
        if press_count > 0:
            trigger_runtime.send(settings.triggers.get("target_key_press"))
            close_time = min(effort_deadline, max(first_rt or 0.0, 0.01))
    else:
        kb.clearEvents()
        kb.clock.reset()
        stage_clock = core.Clock()
        first_flip = None

        while stage_clock.getTime() < effort_deadline and press_count < required_presses:
            elapsed = stage_clock.getTime()
            remain = max(0.0, effort_deadline - elapsed)
            counter.text = f"按键进度：{press_count}/{required_presses}\n剩余时间：{remain:.1f} 秒"
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
                    trigger_runtime.send(settings.triggers.get("target_key_press"))

        close_time = min(effort_deadline, float(stage_clock.getTime()))

    effort_completed = press_count >= required_presses
    trigger_runtime.send(
        settings.triggers.get("target_complete" if effort_completed else "target_fail")
    )
    close_global = onset_global + close_time
    if first_rt is not None:
        response_global = onset_global + float(first_rt)
    else:
        response_global = None

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
        choice_option=choice_option,
        close_time=close_time,
        close_time_global=close_global,
    ).to_dict(trial_data)

    # phase: effort_feedback
    completion_key = "effort_success_feedback" if effort_completed else "effort_fail_feedback"
    feedback = make_unit(unit_label="effort_feedback").add_stim(stim_bank.get(completion_key))
    set_trial_context(
        feedback,
        trial_id=trial_id,
        phase="effort_feedback",
        deadline_s=_qa_scale_duration(float(settings.feedback_duration), win),
        valid_keys=[],
        block_id=block_id,
        condition_id=cond_id,
        task_factors={
            "stage": "effort_feedback",
            "choice_option": choice_option,
            "effort_completed": effort_completed,
            "block_idx": block_idx,
        },
        stim_id=completion_key,
    )
    feedback.show(
        duration=float(settings.feedback_duration),
        onset_trigger=settings.triggers.get("feedback_onset"),
    ).to_dict(trial_data)

    # --- Reward outcome ---
    reward_win = bool(effort_completed and reward_draw_win(probability=probability, reward_draw_u=reward_draw_u))
    reward_amount = float(chosen_reward if reward_win else 0.0)
    if not effort_completed:
        reward_stim = stim_bank.get("reward_incomplete_feedback")
        reward_code = settings.triggers.get("reward_incomplete_onset")
    elif reward_win:
        reward_stim = stim_bank.get_and_format(
            "reward_win_feedback",
            reward_amount=f"{reward_amount:.2f}",
        )
        reward_code = settings.triggers.get("reward_win_onset")
    else:
        reward_stim = stim_bank.get("reward_nowin_feedback")
        reward_code = settings.triggers.get("reward_nowin_onset")

    reward_fb = make_unit(unit_label="reward_feedback").add_stim(reward_stim)
    reward_fb.show(
        duration=float(settings.reward_feedback_duration),
        onset_trigger=reward_code,
    ).set_state(
        reward_win=reward_win,
        reward_amount=reward_amount,
        reward_probability=probability,
    ).to_dict(trial_data)

    # phase: inter_trial_interval
    iti = make_unit(unit_label="iti").add_stim(stim_bank.get("fixation"))
    set_trial_context(
        iti,
        trial_id=trial_id,
        phase="inter_trial_interval",
        deadline_s=_qa_scale_duration(float(settings.iti_duration), win),
        valid_keys=[],
        block_id=block_id,
        condition_id=cond_id,
        task_factors={"stage": "inter_trial_interval", "block_idx": block_idx},
        stim_id="fixation",
    )
    iti.show(
        duration=float(settings.iti_duration),
        onset_trigger=settings.triggers.get("iti_onset"),
    ).to_dict(trial_data)

    trial_data.update(
        {
            "condition_label": cond_id,
            "choice_option": choice_option,
            "choice_key": choice_key,
            "choice_forced": choice_forced,
            "effort_required_presses": required_presses,
            "effort_press_count": press_count,
            "effort_completed": effort_completed,
            "reward_win": reward_win,
            "reward_amount": reward_amount,
        }
    )

    return trial_data

