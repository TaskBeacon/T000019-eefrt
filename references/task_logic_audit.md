# Task Logic Audit

## 1. Paradigm Intent

- Task: Effort Expenditure for Rewards Task (EEfRT).
- Primary construct: effort-based choice under reward probability and reward magnitude uncertainty.
- Manipulated factors:
  - reward probability cue (`12%`, `50%`, `88%`)
  - hard-option reward magnitude
  - effort cost (easy vs hard press requirement and deadline)
- Dependent measures:
  - hard-choice rate
  - effort completion rate
  - earned reward
  - choice RT and effort RT trace
- Key citations: `R1_TREADWAY_2009`, `R2_OHMANN_2022`, `R3_TREADWAY_2012`.

## 2. Block/Trial Workflow

### Block Structure

- Total blocks: `1` (human, qa, sim profiles differ mainly by trial count/timing scale).
- Trials per block: `48` human, `12` qa/sim.
- Randomization/counterbalancing: custom generated offer tuples with deterministic seed use.
- Condition weight policy:
  - `task.condition_weights` is not used for this task.
  - Runtime resolution via `TaskSettings.resolve_condition_weights()` is not used because conditions are tuple-valued offers.
  - Generation is handled by custom function `build_eefrt_offer_conditions(...)`.
- Condition generation method:
  - Custom generator is used because simple condition labels cannot represent `(probability, hard_reward, fallback_choice, reward_draw_u)` tuple semantics.
  - Generated trial shape:
    - `offer_probability`
    - `offer_hard_reward`
    - `condition_id`
    - `trial_index`
    - `fallback_choice`
    - `reward_draw_u`
- Runtime-generated trial values:
  - Effort press count, completion status, and reward outcome are generated during trial execution.
  - Reproducibility:
    - Offer tuples are precomputed from deterministic seeds.
    - Reward lottery uses precomputed `reward_draw_u` passed in condition tuple.

### Trial State Machine

1. State name: `offer_fixation`
   - Onset trigger: `cue_onset`
   - Stimuli shown: fixation cross
   - Valid keys: none
   - Timeout behavior: fixed duration; advances automatically
   - Next state: `offer_choice`
2. State name: `offer_choice`
   - Onset trigger: `choice_onset`
   - Stimuli shown: probability header + easy/hard option panels
   - Valid keys: `choice_keys` (`f`, `j`)
   - Timeout behavior: fallback choice from preplanned tuple and emit `choice_forced`
   - Next state: `ready`
3. State name: `ready`
   - Onset trigger: `ready_onset`
   - Stimuli shown: selected option summary and effort requirement reminder
   - Valid keys: none
   - Timeout behavior: fixed duration
   - Next state: `effort_execution_window`
4. State name: `effort_execution_window`
   - Onset trigger: `target_onset`
   - Stimuli shown: effort prompt and live press/time counter
   - Valid keys: `effort_key` (`space`)
   - Timeout behavior: stop at selected deadline (`7s` easy or `21s` hard)
   - Next state: `effort_feedback`
5. State name: `effort_feedback`
   - Onset trigger: `feedback_onset`
   - Stimuli shown: completion success/failure message
   - Valid keys: none
   - Timeout behavior: fixed duration
   - Next state: `reward_feedback`
6. State name: `reward_feedback`
   - Onset trigger: one of `reward_win_onset`, `reward_nowin_onset`, `reward_incomplete_onset`
   - Stimuli shown: reward outcome message
   - Valid keys: none
   - Timeout behavior: fixed duration
   - Next state: `inter_trial_interval`
7. State name: `inter_trial_interval`
   - Onset trigger: `iti_onset`
   - Stimuli shown: fixation
   - Valid keys: none
   - Timeout behavior: fixed duration
   - Next state: next trial / block end

## 3. Condition Semantics

- Condition ID: `offer`
  - Participant-facing meaning: one EEfRT offer with a specific probability and hard-option reward.
  - Concrete stimulus realization:
    - probability shown in `choice_header`
    - easy option details in `choice_left`
    - hard option details in `choice_right`
  - Outcome rules:
    - participant selects easy/hard (or fallback if timeout)
    - effort completion determines reward eligibility
    - reward lottery uses offer probability and preplanned draw value

Also document where participant-facing condition text/stimuli are defined:

- Participant-facing text source (config stimuli / code formatting / generated assets):
  - base wording is config-defined in `config/*.yaml` stimuli
  - runtime formatting injects numeric values (probability, reward amount, counter values)
- Why this source is appropriate for auditability:
  - static wording is centralized in config and trial values are explicit in logged condition tuple/state.
- Localization strategy (how language variants are swapped via config without code edits):
  - localized text is stored in config stimulus entries; switching language is done by editing config text assets.

## 4. Response and Scoring Rules

- Response mapping:
  - `f` -> easy option
  - `j` -> hard option
  - `space` -> effort keypress
- Response key source (config field vs code constant):
  - config fields `task.choice_keys` and `task.effort_key`.
- If code-defined, why config-driven mapping is not sufficient:
  - not applicable.
- Missing-response policy:
  - choice timeout uses deterministic fallback (`fallback_choice`) and marks forced choice.
- Correctness logic:
  - effort success if `press_count >= required_presses` before deadline.
- Reward/penalty updates:
  - if effort incomplete, reward is `0`
  - if effort complete, reward is granted when `reward_draw_u < offer_probability`
- Running metrics:
  - hard-choice count/rate
  - effort completion count/rate
  - total earned reward

## 5. Stimulus Layout Plan

- Screen name: `offer_choice`
  - Stimulus IDs shown together: `choice_header`, `choice_left`, `choice_right`
  - Layout anchors (`pos`): `[0,250]`, `[-300,10]`, `[300,10]`
  - Size/spacing (`height`, width, wrap): separate columns with wrap width `420`
  - Readability/overlap checks: two-column layout prevents overlap across standard window settings
  - Rationale: preserve simultaneous binary choice structure from EEfRT
- Screen name: `effort_execution_window`
  - Stimulus IDs shown together: `effort_prompt`, `effort_counter`
  - Layout anchors (`pos`): `[0,195]`, `[0,-190]`
  - Size/spacing (`height`, width, wrap): vertical split for prompt and dynamic counter
  - Readability/overlap checks: counter updates remain below prompt
  - Rationale: keep effort goal and progress visible concurrently

## 6. Trigger Plan

- Experiment: `exp_onset`, `exp_end`
- Block: `block_onset`, `block_end`
- Phase onsets: `cue_onset`, `choice_onset`, `ready_onset`, `target_onset`, `feedback_onset`, reward outcome triggers, `iti_onset`
- Action events: `choice_easy_press`, `choice_hard_press`, `choice_no_response`, `choice_forced`, `target_key_press`, `target_complete`, `target_fail`

## 7. Architecture Decisions (Auditability)

- `main.py` runtime flow style (simple single flow / helper-heavy / why):
  - simple mode-aware flow (`human|qa|sim`) with direct block execution and explicit logs.
- `utils.py` used? (yes/no)
  - yes.
- If yes, exact purpose (adaptive controller / sequence generation / asset pool / other):
  - custom offer condition generation, deterministic fallback selection, deterministic reward draw decision helper.
- Custom controller used? (yes/no)
  - no.
- If yes, why PsyFlow-native path is insufficient:
  - not applicable.
- Legacy/backward-compatibility fallback logic required? (yes/no)
  - no.
- If yes, scope and removal plan:
  - not applicable.

## 8. Inference Log

- Decision:
  - use deterministic `fallback_choice` for no-choice trials.
  - Why inference was required:
    - canonical papers describe behavior but not software timeout policy for automation.
  - Citation-supported rationale:
    - preserves binary forced-choice requirement while enabling reproducible QA/sim traces.
- Decision:
  - include deterministic `reward_draw_u` in condition tuple.
  - Why inference was required:
    - literature specifies probabilistic reward, not implementation-level reproducibility details.
  - Citation-supported rationale:
    - maintains exact Bernoulli reward semantics while ensuring test reproducibility.
