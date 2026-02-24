# CHANGELOG

All notable development changes for `T000019-eefrt` are documented here.

## [0.1.0] - 2026-02-17

### Added
- Added initial PsyFlow/TAPS task scaffold for EEfRT Task.
- Added mode-aware runtime (`human|qa|sim`) in `main.py`.
- Added split configs (`config.yaml`, `config_qa.yaml`, `config_scripted_sim.yaml`, `config_sampler_sim.yaml`).
- Added responder trial-context plumbing via `set_trial_context(...)` in `src/run_trial.py`.
- Added generated cue/target image stimuli under `assets/generated/`.

### Verified
- `python -m psyflow.validate <task_path>`
- `psyflow-qa <task_path> --config config/config_qa.yaml --no-maturity-update`
- `python main.py sim --config config/config_scripted_sim.yaml`
- `python main.py sim --config config/config_sampler_sim.yaml`

## [Unreleased]

### Added
- Added `references/task_logic_audit.md` documenting the literature-first EEfRT state machine and condition-generation architecture.

### Changed
- Refactored `main.py` to a PsyFlow-first flow using `BlockUnit.generate_conditions(func=...)` and `condition_generation` config (no task controller object).
- Replaced `src/utils.py` `Controller` class with deterministic EEfRT offer condition generation utilities and helper functions.
- Refactored `src/run_trial.py` to consume explicit generated trial specs (fallback choice + reward draw) and removed controller dependencies.
- Renamed legacy internal unit labels to task-specific names (`offer_choice`, `effort_execution`, `effort_feedback`) for clearer QA traces.
- Updated `responders/task_sampler.py` to use canonical phases only (`offer_choice`, `effort_execution_window`).
- Updated `references/parameter_mapping.md` and `README.md` to reflect `condition_generation` instead of a generic controller.

### Fixed
- Fixed task-build standard failure caused by missing `references/task_logic_audit.md`.
- Fixed QA acceptance criteria columns to match the refactored unit labels.

### Verified
- `python -m py_compile main.py src/run_trial.py src/utils.py responders/task_sampler.py`
- `python e:\\Taskbeacon\\psyflow\\skills\\task-build\\scripts\\check_task_standard.py --task-path e:\\Taskbeacon\\T000019-eefrt`
- `python -m psyflow.validate e:\\Taskbeacon\\T000019-eefrt`
- `python main.py qa --config config/config_qa.yaml`
- `python main.py sim --config config/config_scripted_sim.yaml`
- `python main.py sim --config config/config_sampler_sim.yaml`

## [0.2.0] - 2026-02-17

### Changed
- Replaced MID-like placeholder trial logic with EEfRT-specific flow:
  cue -> choice (`anticipation`) -> ready -> effort (`target`) -> completion feedback -> reward feedback -> ITI.
- Replaced adaptive-duration controller with offer-based EEfRT controller (probability × hard-reward grid, randomized per block).
- Updated block summaries to report high-effort choice rate, effort completion rate, and earned reward.
- Reworked all config profiles to Chinese participant-facing text with `font: SimHei`, human-auditable sections, and mode-specific content separation.
- Replaced generic sampler with task-specific EEfRT sampler (utility-based hard-choice + effort press-rate simulation).
- Rewrote `README.md` to full reproducibility structure and updated reference mapping artifacts.

### Fixed
- Fixed protocol validity issues where previous implementation used unrelated condition labels and non-EEfRT feedback logic.
- Fixed simulation/runtime mismatch in effort stage by adding explicit responder-aware effort-count simulation path.

### Verified
- `python -m psyflow.validate e:\Taskbeacon\T000019-eefrt`
- `python main.py qa --config config/config_qa.yaml`
- `python main.py sim --config config/config_scripted_sim.yaml`
- `python main.py sim --config config/config_sampler_sim.yaml`
