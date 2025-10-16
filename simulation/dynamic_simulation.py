import argparse
import os
from typing import Dict, Any, List

import pandas as pd
from tqdm import tqdm

from analysis.dynamic_graph_models_analysis import (
    DynamicParams,
    simulate_dynamic,
)
from config import DYNAMIC_SIMULATION_CONFIG
from models.model_generator import generate_network


def build_params(config: Dict[str, Any], compute_ac: bool) -> DynamicParams:
    return DynamicParams(
        steps=config.get('steps', 1000),
        packet_rate=config.get('packet_rate', 1),
        node_failure_period=config.get('node_failure_period', 100),
        node_recovery_steps=config.get('node_recovery_steps', 20),
        base_energy_drain=config.get('base_energy_drain', 0.05),
        tx_energy_cost=config.get('tx_energy_cost', 0.05),
        rx_energy_cost=config.get('rx_energy_cost', 0.02),
        initial_energy=config.get('initial_energy', 100.0),
        link_flip_prob=config.get('link_flip_prob', 0.0),
        link_down_steps=config.get('link_down_steps', 10),
        ttr_epsilon=config.get('ttr_epsilon', 0.02),
        compute_algebraic_connectivity=compute_ac,
    )


def rolling_mean(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series
    return series.rolling(window, min_periods=1).mean()


def maybe_flush(ts_buffer: List[pd.DataFrame], sm_buffer: List[Dict[str, Any]], ts_path: str, sm_path: str, force: bool, wrote_any: Dict[str, bool]):
    if not force and not ts_buffer and not sm_buffer:
        return
    if ts_buffer:
        df = pd.concat(ts_buffer, ignore_index=True)
        mode = 'a' if wrote_any.get('ts') else 'w'
        header = not wrote_any.get('ts')
        df.to_csv(ts_path, index=False, mode=mode, header=header)
        ts_buffer.clear()
        wrote_any['ts'] = True
    if sm_buffer:
        df = pd.DataFrame(sm_buffer)
        mode = 'a' if wrote_any.get('sm') else 'w'
        header = not wrote_any.get('sm')
        df.to_csv(sm_path, index=False, mode=mode, header=header)
        sm_buffer.clear()
        wrote_any['sm'] = True


def main():
    parser = argparse.ArgumentParser(description="Run dynamic network simulations and export results.")
    parser.add_argument('--runs', type=int, default=None, help='Override number of runs per model.')
    parser.add_argument('--steps', type=int, default=None, help='Override number of time steps.')
    parser.add_argument('--compute-ac', action='store_true', help='Compute algebraic connectivity per step (slower).')
    parser.add_argument('--timeseries', type=str, default=None, help='Override timeseries output filename.')
    parser.add_argument('--summary', type=str, default=None, help='Override summary output filename.')
    args = parser.parse_args()

    cfg = dict(DYNAMIC_SIMULATION_CONFIG)

    if args.runs is not None:
        cfg['num_runs_per_setting'] = args.runs
    if args.steps is not None:
        cfg['steps'] = args.steps

    timeseries_path = args.timeseries or cfg.get('timeseries_filename', 'dynamic_timeseries.csv')
    summary_path = args.summary or cfg.get('summary_filename', 'dynamic_summary.csv')

    params = build_params(cfg, compute_ac=args.compute_ac)
    smoothing_window = int(cfg.get('ddr_smoothing_window', 1))

    random_seed_base = cfg.get('random_seed_base')
    flush_every = int(cfg.get('flush_every', 0))

    ts_buffer: List[pd.DataFrame] = []
    sm_buffer: List[Dict[str, Any]] = []
    wrote_any = {'ts': False, 'sm': False}

    total_runs = len(cfg['models']) * cfg['num_runs_per_setting']

    if os.path.exists(timeseries_path):
        os.remove(timeseries_path)
    if os.path.exists(summary_path):
        os.remove(summary_path)

    run_counter = 0
    with tqdm(total=total_runs, desc="Dynamic Simulations", unit="run") as pbar:
        for model_name, model_params in cfg['models'].items():
            gen_params = {k: v for k, v in model_params.items() if k != 'model_type'}
            for run_id in range(cfg['num_runs_per_setting']):
                # Deterministic seed incorporating model & run
                seed = None
                if random_seed_base is not None:
                    seed = random_seed_base + run_id + (hash(model_name) & 0xFFFF)
                gp = gen_params.copy()
                model_type = model_params['model_type']
                G = generate_network(model_type=model_type, num_nodes=cfg['num_nodes'], **gp)

                df, summary = simulate_dynamic(G, params=params, seed=seed)
                df['model_name'] = model_name
                df['run_id'] = run_id
                df['seed'] = seed
                for pk, pv in gp.items():
                    df[f'gen_{pk}'] = pv
                if 'ddr_step' in df.columns and smoothing_window > 1:
                    df['ddr_step_smoothed'] = rolling_mean(df['ddr_step'], smoothing_window)
                ts_buffer.append(df)

                summary_row = {'model_name': model_name, 'run_id': run_id, 'seed': seed}
                for pk, pv in gp.items():
                    summary_row[f'gen_{pk}'] = pv
                summary_row.update(summary)
                sm_buffer.append(summary_row)

                run_counter += 1
                if flush_every and (run_counter % flush_every == 0):
                    maybe_flush(ts_buffer, sm_buffer, timeseries_path, summary_path, force=False, wrote_any=wrote_any)

                pbar.set_postfix(model=model_name, run=run_id + 1)
                pbar.update(1)

    maybe_flush(ts_buffer, sm_buffer, timeseries_path, summary_path, force=True, wrote_any=wrote_any)

    if not wrote_any['ts']:
        pd.concat(ts_buffer, ignore_index=True).to_csv(timeseries_path, index=False)
    if not wrote_any['sm']:
        pd.DataFrame(sm_buffer).to_csv(summary_path, index=False)

    print(f"Time series written to {timeseries_path}")
    print(f"Summary written to {summary_path}")


if __name__ == '__main__':
    main()
