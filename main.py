from contextlib import nullcontext
from functools import partial
from pathlib import Path

import pandas as pd
from psychopy import core

from psyflow import (
    BlockUnit,
    StimBank,
    StimUnit,
    SubInfo,
    TaskRunOptions,
    TaskSettings,
    context_from_config,
    count_down,
    initialize_exp,
    initialize_triggers,
    load_config,
    parse_task_run_options,
    runtime_context,
)

from src import build_eefrt_offer_conditions, run_trial


MODES = ("human", "qa", "sim")
DEFAULT_CONFIG_BY_MODE = {
    "human": "config/config.yaml",
    "qa": "config/config_qa.yaml",
    "sim": "config/config_scripted_sim.yaml",
}


def run(options: TaskRunOptions):
    """Run EEfRT task in human/qa/sim mode with one auditable flow."""
    task_root = Path(__file__).resolve().parent
    cfg = load_config(str(options.config_path), extra_keys=["condition_generation"])
    print(f"[EEfRT] mode={options.mode} config={options.config_path}")

    output_dir: Path | None = None
    runtime_scope = nullcontext()
    runtime_ctx = None
    if options.mode in ("qa", "sim"):
        runtime_ctx = context_from_config(task_dir=task_root, config=cfg, mode=options.mode)
        output_dir = runtime_ctx.output_dir
        runtime_scope = runtime_context(runtime_ctx)

    with runtime_scope:
        if options.mode == "human":
            subform = SubInfo(cfg["subform_config"])
            subject_data = subform.collect()
        elif options.mode == "qa":
            subject_data = {"subject_id": "qa"}
        else:
            participant_id = "sim"
            if runtime_ctx is not None and runtime_ctx.session is not None:
                participant_id = str(runtime_ctx.session.participant_id or "sim")
            subject_data = {"subject_id": participant_id}

        settings = TaskSettings.from_dict(cfg["task_config"])
        if options.mode in ("qa", "sim") and output_dir is not None:
            settings.save_path = str(output_dir)
        settings.add_subinfo(subject_data)

        if options.mode == "qa" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "qa_trace.csv")
            settings.log_file = str(output_dir / "qa_psychopy.log")
            settings.json_file = str(output_dir / "qa_settings.json")

        settings.triggers = cfg["trigger_config"]
        settings.condition_generation = cfg.get("condition_generation_config", {})
        settings.save_to_json()
        trigger_runtime = initialize_triggers(mock=True) if options.mode in ("qa", "sim") else initialize_triggers(cfg)

        win, kb = initialize_exp(settings)

        stim_bank = StimBank(win, cfg["stim_config"])
        if options.mode not in ("qa", "sim"):
            stim_bank = stim_bank.convert_to_voice("instruction_text")
        stim_bank = stim_bank.preload_all()

        trigger_runtime.send(settings.triggers.get("exp_onset"))
        instr = StimUnit("instruction_text", win, kb, runtime=trigger_runtime).add_stim(stim_bank.get("instruction_text"))
        if options.mode not in ("qa", "sim"):
            instr.add_stim(stim_bank.get("instruction_text_voice"))
        instr.wait_and_continue()

        all_data: list[dict] = []
        cg_cfg = dict(getattr(settings, "condition_generation", {}) or {})
        for block_i in range(settings.total_blocks):
            if options.mode not in ("qa", "sim"):
                count_down(win, 3, color="black")

            block = (
                BlockUnit(
                    block_id=f"block_{block_i}",
                    block_idx=block_i,
                    settings=settings,
                    window=win,
                    keyboard=kb,
                )
                .generate_conditions(
                    func=build_eefrt_offer_conditions,
                    condition_labels=list(getattr(settings, "conditions", ["offer"])),
                    probability_levels=list(cg_cfg.get("probability_levels", [0.12, 0.50, 0.88])),
                    hard_reward_levels=list(cg_cfg.get("hard_reward_levels", [1.24, 1.68, 2.11, 2.55, 2.99, 3.43, 3.86, 4.30])),
                    randomize_order=bool(cg_cfg.get("randomize_order", True)),
                    no_choice_hard_prob=float(cg_cfg.get("no_choice_hard_prob", 0.50)),
                    enable_logging=bool(cg_cfg.get("enable_logging", True)),
                )
                .on_start(lambda b: trigger_runtime.send(settings.triggers.get("block_onset")))
                .on_end(lambda b: trigger_runtime.send(settings.triggers.get("block_end")))
                .run_trial(
                    partial(
                        run_trial,
                        stim_bank=stim_bank,
                        trigger_runtime=trigger_runtime,
                        block_id=f"block_{block_i}",
                        block_idx=block_i,
                    )
                )
                .to_dict(all_data)
            )

            block_trials = block.get_all_data()
            n_block = max(1, len(block_trials))
            hard_rate = sum(1 for trial in block_trials if trial.get("choice_option") == "hard") / n_block
            completion_rate = sum(1 for trial in block_trials if trial.get("effort_completed", False)) / n_block
            total_reward = sum(float(trial.get("reward_amount", 0.0) or 0.0) for trial in block_trials)
            StimUnit("block", win, kb, runtime=trigger_runtime).add_stim(
                stim_bank.get_and_format(
                    "block_break",
                    block_num=block_i + 1,
                    total_blocks=settings.total_blocks,
                    hard_rate=hard_rate,
                    completion_rate=completion_rate,
                    total_reward=f"{total_reward:.2f}",
                )
            ).wait_and_continue()

        final_reward = sum(float(trial.get("reward_amount", 0.0) or 0.0) for trial in all_data)
        n_all = max(1, len(all_data))
        final_hard_rate = sum(1 for trial in all_data if trial.get("choice_option") == "hard") / n_all
        final_completion_rate = sum(1 for trial in all_data if trial.get("effort_completed", False)) / n_all
        StimUnit("goodbye", win, kb, runtime=trigger_runtime).add_stim(
            stim_bank.get_and_format(
                "good_bye",
                total_reward=f"{final_reward:.2f}",
                hard_rate=f"{final_hard_rate:.1%}",
                completion_rate=f"{final_completion_rate:.1%}",
            )
        ).wait_and_continue(terminate=True)

        trigger_runtime.send(settings.triggers.get("exp_end"))
        pd.DataFrame(all_data).to_csv(settings.res_file, index=False)
        trigger_runtime.close()
        core.quit()


def main() -> None:
    task_root = Path(__file__).resolve().parent
    options = parse_task_run_options(
        task_root=task_root,
        description="Run EEfRT Task in human/qa/sim mode.",
        default_config_by_mode=DEFAULT_CONFIG_BY_MODE,
        modes=MODES,
    )
    run(options)


if __name__ == "__main__":
    main()
