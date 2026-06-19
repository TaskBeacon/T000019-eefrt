# Task Plot Review

## Evidence Match

- Pass: title and construct match the EEfRT effort-based decision task.
- Pass: rows represent the configured probability levels: 12%, 50%, and 88%.
- Pass: phase order matches README and `src/run_trial.py`: Cue -> Choice -> Ready -> Effort -> Effort feedback -> Reward feedback -> ITI.
- Pass: timing labels match config: 1000 ms cue, 5000 ms choice, 1000 ms ready, 7000 ms low-effort or 21000 ms high-effort execution, 1000 ms feedback, 1000 ms reward feedback, 1000 ms ITI.
- Pass: choice key mapping shows F for low effort and J for high effort.
- Pass: effort stage shows repeated SPACE presses and variable target count after choice.
- Pass: reward feedback shows win, no win, and incomplete/no reward alternatives.

## Visual Quality

- Pass: labels and timings are readable.
- Pass: generated timeline content stays below the header band.
- Pass: fixed title and Construct subtitle are centered.
- Pass: top-right TaskBeacon logo lockup is borderless and non-overlapping.
- Pass: no generated title, logo, watermark, people, devices, or decorative scene is present.

## README Embed

- Pass: `README.md` contains `## 2. Task Flow`.
- Pass: the section embeds `![Task Flow](task_flow.png)`.
- Pass: final image is saved as `task_flow.png`; raw timeline is saved as `references/task_plot_timeline_raw.png`.
