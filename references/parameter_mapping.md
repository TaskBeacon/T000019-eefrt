# Parameter Mapping

| Literature Parameter | Implemented Config Value | Source Paper ID | Confidence | Rationale |
|---|---|---|---|---|
| Easy effort requirement | `task.easy_required_presses = 30` | `R1_TREADWAY_2009` | `exact` | Canonical EEfRT easy option. |
| Hard effort requirement | `task.hard_required_presses = 100` | `R1_TREADWAY_2009` | `exact` | Canonical EEfRT hard option. |
| Easy effort deadline | `task.easy_time_limit_s = 7.0` | `R1_TREADWAY_2009` | `exact` | Canonical EEfRT easy trial deadline. |
| Hard effort deadline | `task.hard_time_limit_s = 21.0` | `R1_TREADWAY_2009` | `exact` | Canonical EEfRT hard trial deadline. |
| Probability cues | `controller.probability_levels = [0.12, 0.50, 0.88]` | `R1_TREADWAY_2009`, `R2_OHMANN_2022` | `exact` | Canonical probability levels. |
| Easy reward amount | `task.easy_reward = 1.00` | `R1_TREADWAY_2009` | `exact` | Canonical easy-option reward. |
| Hard reward range | `controller.hard_reward_levels = [1.24 ... 4.30]` | `R1_TREADWAY_2009` | `exact` | Canonical hard-option reward range. |
| Choice response mapping | `task.choice_keys = ["f","j"]` | `R1_TREADWAY_2009` | `inferred` | Keyboard side mapping adapted to Chinese local setup while preserving binary choice. |
| Effort action key | `task.effort_key = "space"` | `R1_TREADWAY_2009` | `inferred` | Single-key repeated tapping operationalizes the required effort counts in desktop PsychoPy. |
| Trial count (human profile) | `task.total_trials = 48` | `R1_TREADWAY_2009`, `R2_OHMANN_2022` | `inferred` | Balanced probability × hard-reward offer grid for reproducible lab deployment. |
| Primary outcomes | `choice_option`, `effort_completed`, `reward_amount` outputs | `R1_TREADWAY_2009`, `R3_TREADWAY_2012` | `exact` | Matches core EEfRT behavioral endpoints. |

