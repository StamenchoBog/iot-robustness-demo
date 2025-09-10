import argparse
from typing import Dict, Any

import pandas as pd
from tqdm import tqdm

from config import DYNAMIC_SIMULATION_CONFIG
from models.model_generator import generate_network
from analysis.dynamic_graph_models_analysis import (
    DynamicParams,
    simulate_dynamic,
)


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

    ts_rows = []
    summary_rows = []

    total_runs = len(cfg['models']) * cfg['num_runs_per_setting']
    with tqdm(total=total_runs, desc="Dynamic Simulations", unit="run") as pbar:
        for model_name, model_params in cfg['models'].items():
            for run_id in range(cfg['num_runs_per_setting']):
                gen_params = model_params.copy()
                model_type = gen_params.pop('model_type')
                G = generate_network(model_type=model_type, num_nodes=cfg['num_nodes'], **gen_params)

                df, summary = simulate_dynamic(G, params=params, seed=42 + run_id)

                df['model_name'] = model_name
                df['run_id'] = run_id
                ts_rows.append(df)

                summary_row = {'model_name': model_name, 'run_id': run_id}
                summary_row.update(summary)
                summary_rows.append(summary_row)

                pbar.set_postfix(model=model_name, run=run_id + 1)
                pbar.update(1)

    ts_df = pd.concat(ts_rows, ignore_index=True) if ts_rows else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows)

    ts_df.to_csv(timeseries_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Time series written to {timeseries_path}")
    print(f"Summary written to {summary_path}")


if __name__ == '__main__':
    main()
