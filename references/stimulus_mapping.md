# Stimulus Mapping

## Mapping Table

| Condition | Stage/Phase | Stimulus IDs | Participant-Facing Content | Source Paper ID | Evidence (quote/figure/table) | Implementation Mode | Asset References | Notes |
|---|---|---|---|---|---|---|---|---|
| `offer` | `offer_fixation` | `fixation` | Central fixation cross before offer/choice display | R1_TREADWAY_2009 | Canonical pre-choice fixation | psychopy_builtin | config text stimulus | Shared across trials |
| `offer` | `offer_choice` | `choice_header`, `choice_left`, `choice_right` | Probability cue and easy/hard options with reward and effort requirements | R1_TREADWAY_2009; R2_OHMANN_2022 | EEfRT choice stage presents probability and option values | psychopy_builtin | config text stimuli with formatting | Content generated from trial condition tuple |
| `offer` | `ready` | `ready_text` | Brief confirmation of selected option and required presses/time | R1_TREADWAY_2009 | Transition from choice to effort execution | psychopy_builtin | config text stimulus | Uses localized labels |
| `offer` | `effort_execution_window` | `effort_prompt`, `effort_counter` | Repeated keypress task with running press count and remaining time | R1_TREADWAY_2009 | Effort execution stage with press-count criterion | psychopy_builtin | config text template + runtime formatting | Counter updated each frame |
| `offer` | `effort_feedback` | `effort_success_feedback`, `effort_fail_feedback` | Completion status after effort window | R1_TREADWAY_2009 | Completion outcome precedes reward lottery | psychopy_builtin | config text stimuli | Binary success/fail message |
| `offer` | `reward_feedback` | `reward_win_feedback`, `reward_nowin_feedback`, `reward_incomplete_feedback` | Reward win/no-win/incomplete messages and amount | R1_TREADWAY_2009 | Reward only when effort completed and probabilistic draw wins | psychopy_builtin | config text stimuli with amount formatting | Explicitly separates completion and lottery outcome |
| `all` | `inter_trial_interval` | `fixation` | Short fixation between trials | R1_TREADWAY_2009 | ITI separation between EEfRT trials | psychopy_builtin | config text stimulus | Phase boundary marker |
| `all` | `instruction/block_break/goodbye` | `instruction_text`, `block_break`, `good_bye` | Instructions, break summary, and end-of-task message | R2_OHMANN_2022; R3_TREADWAY_2012 | Session control and summary support behavioral interpretation | psychopy_builtin | config text stimuli | Localization-ready via config |
