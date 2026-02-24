# EEfRT Task

![Maturity: draft](https://img.shields.io/badge/Maturity-draft-64748b?style=flat-square&labelColor=111827)

| Field | Value |
|---|---|
| Name | EEfRT Task |
| Version | v0.2.1-dev |
| URL / Repository | https://github.com/TaskBeacon/T000019-eefrt |
| Short Description | Effort Expenditure for Rewards Task with probabilistic reward outcomes. |
| Created By | TaskBeacon |
| Date Updated | 2026-02-24 |
| PsyFlow Version | 0.1.9 |
| PsychoPy Version | 2025.1.1 |
| Modality | Behavior |
| Language | Chinese |
| Voice Name | zh-CN-YunyangNeural |

## 1. Task Overview

This task implements an EEfRT-style paradigm in which participants choose between low-effort/low-reward and high-effort/high-reward options under varying reward probabilities. After choosing, participants perform an effort execution stage and then receive completion and reward feedback. The task captures effort allocation, completion rate, and reward-sensitive decision behavior.

## 2. Task Flow

### Block-Level Flow

| Step | Description |
|---|---|
| 1. Parse mode and config | `main.py` loads `human`, `qa`, or `sim` runtime mode and the selected YAML config. |
| 2. Initialize runtime | Window, keyboard, trigger runtime, and stimulus bank are initialized. |
| 3. Prepare offers | For each block, a custom condition generator builds deterministic `(probability, hard_reward, fallback, reward-draw)` trial specs. |
| 4. Execute trials | Trials run through `src/run_trial.py` with full context logging. |
| 5. Block summary | Block metrics are shown (high-effort rate, completion rate, block reward). |
| 6. Final summary | Final task metrics are shown and trial data are saved. |

### Trial-Level Flow

| Step | Description |
|---|---|
| Offer fixation | Central fixation before offer display. |
| Offer choice | Participant chooses low vs high effort option with response deadline. |
| Ready stage | The chosen effort requirement and deadline are shown. |
| Effort execution | Participant presses effort key repeatedly within the deadline. |
| Effort feedback | Completion or failure message is presented. |
| Reward feedback | Probabilistic reward outcome is presented (or no reward if not completed). |
| Inter-trial interval | Fixation interval before the next trial. |

### Controller Logic

| Component | Description |
|---|---|
| Adaptive controller | Not used. EEfRT does not require dynamic RT-window adjustment. |
| Offer condition generation | `src/utils.py` generates deterministic block trial specs (offer grid + fallback choice + reward draw sample). |
| Runtime scoring | Trial outcomes and rewards are computed in `src/run_trial.py`; summaries are aggregated from trial data in `main.py`. |

### Runtime Context Phases

| Phase Label | Meaning |
|---|---|
| `offer_fixation` | Fixation before the choice screen. |
| `offer_choice` | Choice screen for low vs high effort options. |
| `effort_execution_window` | Effort performance response window. |
| `effort_feedback` | Effort completion feedback stage. |
| `inter_trial_interval` | ITI fixation stage. |

## 3. Configuration Summary

### a. Subject Info

| Field | Meaning |
|---|---|
| `subject_id` | Participant identifier. |

### b. Window Settings

| Parameter | Value |
|---|---|
| `size` | `[1280, 720]` |
| `units` | `pix` |
| `screen` | `0` |
| `bg_color` | `black` |
| `fullscreen` | `false` |
| `monitor_width_cm` | `35.5` |
| `monitor_distance_cm` | `60` |

### c. Stimuli

| Name | Type | Description |
|---|---|---|
| `fixation` | text | Central fixation cross. |
| `choice_header` / `choice_left` / `choice_right` | text | Offer and choice information panel. |
| `ready_text` | text | Pre-effort confirmation prompt. |
| `effort_prompt` / `effort_counter` | text | Effort instruction and live progress display. |
| `effort_success_feedback` / `effort_fail_feedback` | text | Completion feedback. |
| `reward_win_feedback` / `reward_nowin_feedback` / `reward_incomplete_feedback` | text | Reward outcome feedback. |
| `block_break` / `good_bye` | text | Block and final summaries. |

### d. Timing

| Phase | Duration |
|---|---|
| cue | 1.0 s |
| choice | 5.0 s |
| ready | 1.0 s |
| effort deadline (easy) | 7.0 s |
| effort deadline (hard) | 21.0 s |
| feedback | 1.0 s |
| reward_feedback | 1.0 s |
| iti | 1.0 s |

## 4. Methods (for academic publication)

Participants complete an EEfRT-style effort-based choice task. On each trial, reward probability and low/high effort options are presented. Participants choose an option and then perform the selected effort requirement using repeated keypresses within a time limit.

If the effort criterion is met, reward outcome is sampled according to trial probability. If the criterion is not met, reward is set to zero. Trial-level records include offer parameters, selected option, effort completion status, reaction timing, and reward outcome.

The implementation supports `human`, `qa`, and `sim` modes with consistent trial logic and responder-context instrumentation for reproducibility and auditability.

This refactor removes the generic task controller object and replaces it with explicit condition-generation utilities so the EEfRT offer logic and stochastic outcomes are easier to audit.
