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

### Changed
- Refactored `src/run_trial.py` to use `psyflow`'s native `next_trial_id()` and removed legacy internal `_next_trial_id` boilerplate.

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
