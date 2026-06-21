from __future__ import annotations

from functools import partial
from typing import Any

from psyflow import StimUnit, set_trial_context, next_trial_id
from psyflow.sim import get_context
from .utils import choose_fallback_key, parse_offer_condition, reward_draw_win, run_effort_execution

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
    probability, hard_reward, cond_id, planned_trial_index, fallback_choice, reward_draw_u = parse_offer_condition(condition)
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
    easy_choice_label = str(getattr(settings, "easy_choice_label"))
    hard_choice_label = str(getattr(settings, "hard_choice_label"))

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
    choice_label = hard_choice_label if choice_option == "hard" else easy_choice_label

    choice.set_state(
        choice_key=choice_key,
        choice_option=choice_option,
        choice_forced=choice_forced,
        required_presses=required_presses,
        effort_deadline_s=effort_deadline,
        chosen_reward=chosen_reward,
    ).to_dict(trial_data)

    # --- Ready ---
    ready = make_unit(unit_label="ready").add_stim(
        stim_bank.get_and_format(
            "ready_text",
            choice_label=choice_label,
            required_presses=required_presses,
            effort_key=effort_key.upper(),
            time_limit_s=f"{effort_deadline:.1f}",
        )
    )
    set_trial_context(
        ready,
        trial_id=trial_id,
        phase="ready",
        deadline_s=_qa_scale_duration(float(settings.ready_duration), win),
        valid_keys=[],
        block_id=block_id,
        condition_id=cond_id,
        task_factors={
            "stage": "ready",
            "choice_option": choice_option,
            "required_presses": required_presses,
            "effort_deadline_s": effort_deadline,
            "block_idx": block_idx,
        },
        stim_id="ready_text",
    )
    ready.show(
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

    effort_result = run_effort_execution(
        win=win,
        kb=kb,
        stim_bank=stim_bank,
        trigger_runtime=trigger_runtime,
        target=target,
        trial_data=trial_data,
        trial_id=trial_id,
        block_id=block_id,
        condition_id=cond_id,
        task_factors={
            **target_factors,
            "target_onset_trigger": settings.triggers.get("target_onset"),
            "target_key_press_trigger": settings.triggers.get("target_key_press"),
            "target_complete_trigger": settings.triggers.get("target_complete"),
            "target_fail_trigger": settings.triggers.get("target_fail"),
        },
        choice_label=choice_label,
        required_presses=required_presses,
        effort_key=effort_key,
        effort_deadline=effort_deadline,
    )
    press_count = int(effort_result["press_count"])
    first_rt = effort_result["first_rt"]
    close_time = float(effort_result["close_time"])
    effort_completed = bool(effort_result["effort_completed"])

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
    set_trial_context(
        reward_fb,
        trial_id=trial_id,
        phase="reward_feedback",
        deadline_s=_qa_scale_duration(float(settings.reward_feedback_duration), win),
        valid_keys=[],
        block_id=block_id,
        condition_id=cond_id,
        task_factors={
            "stage": "reward_feedback",
            "choice_option": choice_option,
            "effort_completed": effort_completed,
            "reward_win": reward_win,
            "reward_probability": probability,
            "block_idx": block_idx,
        },
        stim_id=(
            "reward_incomplete_feedback"
            if not effort_completed
            else "reward_win_feedback"
            if reward_win
            else "reward_nowin_feedback"
        ),
    )
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

