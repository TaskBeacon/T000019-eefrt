# Parameter Mapping

## Mapping Table

| Parameter ID | Config Path | Implemented Value | Source Paper ID | Evidence (quote/figure/table) | Decision Type | Notes |
|---|---|---|---|---|---|---|
| easy_required_presses | `task.easy_required_presses` | `30` | R1_TREADWAY_2009 | Canonical easy option press count | exact | Easy effort option |
| hard_required_presses | `task.hard_required_presses` | `100` | R1_TREADWAY_2009 | Canonical hard option press count | exact | Hard effort option |
| easy_time_limit | `task.easy_time_limit_s` | `7.0` | R1_TREADWAY_2009 | Easy trial completion window | exact | Easy effort deadline |
| hard_time_limit | `task.hard_time_limit_s` | `21.0` | R1_TREADWAY_2009 | Hard trial completion window | exact | Hard effort deadline |
| easy_reward | `task.easy_reward` | `1.00` | R1_TREADWAY_2009 | Fixed easy-option reward | exact | Reward baseline |
| probability_levels | `condition_generation.probability_levels` | `[0.12, 0.50, 0.88]` | R1_TREADWAY_2009; R2_OHMANN_2022 | Canonical EEfRT probability cue levels | exact | Offer-level probability |
| hard_reward_levels | `condition_generation.hard_reward_levels` | `[1.24..4.30]` | R1_TREADWAY_2009 | Hard-option reward range in EEfRT | exact | Discrete level list in config |
| total_trials_human | `task.total_trials` | `48` | R1_TREADWAY_2009; R2_OHMANN_2022 | Short-form balanced grid adaptation | inferred | Practical profile for this task package |
| choice_keys | `task.choice_keys` | `['f','j']` | R1_TREADWAY_2009 | Binary easy vs hard choice mapping | inferred | Side-key adaptation for local keyboard |
| effort_key | `task.effort_key` | `'space'` | R1_TREADWAY_2009 | Repeated key pressing operationalizes effort | inferred | Desktop implementation detail |
| no_choice_policy | `condition_generation.no_choice_hard_prob` | `0.50` | R1_TREADWAY_2009 | Timeout policy not explicitly specified | inferred | Deterministic fallback for QA/sim |
| primary_outputs | `outputs/log columns` | `choice_option, effort_completed, reward_amount` | R1_TREADWAY_2009; R3_TREADWAY_2012 | Core behavioral outcomes in EEfRT literature | exact | Also includes RT and press counts |
