# Task Logic Audit

## 1. Paradigm Intent

- Task: EEfRT (Effort Expenditure for Rewards Task)
- Primary construct: Effort-based decision-making under varying reward probability and reward magnitude
- Manipulated factors:
  - reward probability cue (`12%`, `50%`, `88%`)
  - hard-option reward magnitude (grid-defined values)
  - effort cost (easy vs hard fixed effort requirements)
- Dependent measures:
  - hard-choice rate
  - effort completion rate
  - reward earned
  - choice RT and effort-stage response traces
- Key citations: `R1_TREADWAY_2009`, `R2_OHMANN_2022`, `R3_TREADWAY_2012`

## 2. Block/Trial Workflow

### Block Structure

- Human profile: 1 block x 48 trials (balanced offer grid)
- QA/sim profiles: 1 block x 12 trials (smoke coverage)
- Condition generation:
  - Custom `BlockUnit.generate_conditions(func=build_eefrt_offer_conditions, ...)`
  - Rationale: built-in label generation cannot encode `(probability, hard_reward)` offer tuples with preplanned fallback/reward draws
  - Output is a hashable tuple per trial with:
    - offer probability
    - hard reward
    - condition id
    - trial index
    - fallback choice (for timeout)
    - reward draw uniform sample (for deterministic reward outcome)

### Trial State Machine

1. `offer_fixation`
   - Stimulus: `fixation`
   - Valid keys: none
   - Trigger: `cue_onset`
2. `offer_choice`
   - Stimuli: `choice_header`, `choice_left`, `choice_right`
   - Valid keys: `task.choice_keys` (`f`, `j`)
   - Timeout: if no response, use preplanned fallback choice and emit `choice_forced`
   - Trigger(s): `choice_onset`, `choice_easy_press`, `choice_hard_press`, `choice_no_response`
3. `ready`
   - Stimulus: `ready_text` (chosen option + required presses + deadline)
   - Valid keys: none
   - Trigger: `ready_onset`
4. `effort_execution_window`
   - Stimuli: `effort_prompt`, `effort_counter`
   - Valid key: `task.effort_key` (`space`)
   - Timeout: trial ends at effort deadline
   - Completion criterion: keypress count >= required presses
   - Trigger(s): `target_onset`, `target_key_press`, `target_complete` / `target_fail`
5. `effort_feedback`
   - Stimulus: `effort_success_feedback` or `effort_fail_feedback`
   - Valid keys: none
   - Trigger: `feedback_onset`
6. reward outcome feedback
   - Stimulus:
     - `reward_incomplete_feedback` if effort not completed
     - `reward_win_feedback` if completed and reward draw < probability
     - `reward_nowin_feedback` otherwise
   - Valid keys: none
   - Trigger: `reward_incomplete_onset` / `reward_win_onset` / `reward_nowin_onset`
7. `inter_trial_interval`
   - Stimulus: `fixation`
   - Valid keys: none
   - Trigger: `iti_onset`

## 3. Condition Semantics

- Condition token in `task.conditions`: `offer` (placeholder label; actual trial content comes from `condition_generation`)
- Trial-spec semantics (generated per trial):
  - `offer_probability`: displayed as cue/header probability
  - `offer_hard_reward`: hard-option reward amount shown on choice screen
  - `fallback_choice`: deterministic timeout imputation for QA/sim reproducibility
  - `reward_draw_u`: deterministic Bernoulli draw support (reward outcome computed at runtime after effort completion)

## 4. Response and Scoring Rules

- Choice stage:
  - `f` = easy option
  - `j` = hard option
  - timeout -> preplanned fallback choice (documented as inferred implementation policy)
- Effort stage:
  - `space` repeated taps
  - completion if taps >= requirement before deadline
- Reward rule:
  - if effort incomplete: reward = `0`
  - if effort complete: reward awarded if `reward_draw_u < offer_probability`
- Running metrics:
  - hard-choice rate
  - effort completion rate
  - cumulative reward (summarized from trial outputs; no global controller object)

## 5. Stimulus Layout Plan

- `offer_choice` screen:
  - `choice_header` top center (`pos: [0,250]`)
  - `choice_left` left column (`pos: [-300,10]`)
  - `choice_right` right column (`pos: [300,10]`)
  - Separate wrap widths (`420`) prevent overlap
- `effort_execution_window` screen:
  - `effort_prompt` top (`pos: [0,195]`)
  - `effort_counter` bottom (`pos: [0,-190]`)
  - Vertical separation prevents overlap during live counter updates
- Other screens:
  - Single centered text stimulus or fixation only

## 6. Trigger Plan

- Experiment: `exp_onset`, `exp_end`
- Block: `block_onset`, `block_end`
- Trial phases: `cue_onset`, `choice_onset`, `ready_onset`, `target_onset`, `feedback_onset`, reward outcome onsets, `iti_onset`
- Choice/effort actions: condition-specific choice press triggers and effort keypress trigger

## 7. Inference Log

- Decision: Use deterministic preplanned fallback choice and reward draw values in condition specs
  - Why inference was required: literature specifies task structure but not software architecture for simulation reproducibility
  - Rationale: removes broad controller state while preserving exact EEfRT trial semantics and making QA/sim runs auditable
- Decision: Keep config timing/trigger key names (`cue`, `target`) while phase labels are EEfRT-specific
  - Why inference was required: refactor priority is paradigm logic and auditability without unnecessary config churn
  - Rationale: runtime phase/state machine is EEfRT-specific; config aliases remain functional and documented
