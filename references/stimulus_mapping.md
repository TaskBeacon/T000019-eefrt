# Stimulus Mapping

Task: `EEfRT Task`

| Trial Component | Implemented Stimulus IDs | Source Paper ID | Evidence Basis | Implementation Mode | Notes |
|---|---|---|---|---|---|
| Fixation | `fixation` | `R1_TREADWAY_2009` | Canonical trial-start fixation before offer evaluation | `psychopy_builtin` | Central `+` text stimulus. |
| Offer/choice display | `choice_offer` | `R1_TREADWAY_2009`, `R2_OHMANN_2022` | Probability cue + easy/hard option reward display before choice | `psychopy_builtin` | Uses Chinese text; no hidden condition labels shown. |
| Ready cue before effort | `ready_text` | `R1_TREADWAY_2009` | Choice confirmation before motor execution | `psychopy_builtin` | Provides selected option and effort requirement. |
| Effort execution display | `effort_prompt`, `effort_counter` | `R1_TREADWAY_2009` | Repeated button-press execution under time limit | `psychopy_builtin` | Live progress and remaining-time feedback during effort window. |
| Completion feedback | `effort_success_feedback`, `effort_fail_feedback` | `R1_TREADWAY_2009` | Completion status before reward outcome | `psychopy_builtin` | Separates effort completion from reward lottery outcome. |
| Reward outcome feedback | `reward_win_feedback`, `reward_nowin_feedback`, `reward_incomplete_feedback` | `R1_TREADWAY_2009` | Probabilistic reward given completion | `psychopy_builtin` | Win/loss/incomplete outcomes explicitly distinguished. |
| Block and task summary | `block_break`, `good_bye` | `R2_OHMANN_2022`, `R3_TREADWAY_2012` | Behavioral summary metrics for QC and interpretation | `psychopy_builtin` | Displays hard-choice rate, completion rate, and total reward. |

Implementation mode legend:
- `psychopy_builtin`: generated at runtime using PsychoPy text primitives.
- `generated_reference_asset`: generated media aligned to reference-defined stimulus rules.
- `licensed_external_asset`: externally sourced licensed media with protocol linkage.

