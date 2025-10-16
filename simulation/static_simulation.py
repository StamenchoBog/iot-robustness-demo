import os
import random
from typing import Dict, Any, List
import pandas as pd
from tqdm import tqdm

from config import STATIC_SIMULATION_CONFIG
from models.model_generator import generate_network
from analysis.static_graph_models_analysis import simulate_attack


class SimulationRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.flush_every = int(config.get('flush_every', 0))
        self.random_seed_base = config.get('random_seed_base')
        self.results_filename = config['results_filename']
        self._rows: List[Dict[str, Any]] = []

    def _seed(self, model_name: str, strategy: str, run_id: int) -> int | None:
        if self.random_seed_base is None:
            return None
        seed = (self.random_seed_base
                + run_id
                + (hash((model_name, strategy)) & 0xFFFF))
        random.seed(seed)
        return seed

    def _flush(self, force: bool = False):
        if not self._rows:
            return
        if self.flush_every <= 0 and not force:
            return
        if not force and len(self._rows) < self.flush_every:
            return
        mode = 'a' if os.path.exists(self.results_filename) else 'w'
        header = mode == 'w'
        pd.DataFrame(self._rows).to_csv(self.results_filename, index=False, mode=mode, header=header)
        self._rows.clear()

    def run(self) -> pd.DataFrame:
        total = (len(self.config['models']) * len(self.config['strategies']) * self.config['num_runs_per_setting'])
        with tqdm(total=total, desc='Static simulations') as pbar:
            for model_name, model_params in self.config['models'].items():
                base_params = {k: v for k, v in model_params.items() if k != 'model_type'}
                for strategy in self.config['strategies']:
                    for run_id in range(self.config['num_runs_per_setting']):
                        seed_used = self._seed(model_name, strategy, run_id)
                        gen_params = base_params.copy()
                        G = generate_network(model_type=model_params['model_type'], num_nodes=self.config['num_nodes'], **gen_params)
                        attack_results = simulate_attack(G, strategy)
                        steps = len(next(iter(attack_results.values())))
                        n_nodes = len(G.nodes())
                        for step in range(steps):
                            row = {
                                'model_name': model_name,
                                'attack_strategy': strategy,
                                'run_id': run_id,
                                'seed': seed_used,
                                'step_index': step,
                                'nodes_removed': step,
                                'nodes_removed_fraction': step / n_nodes if n_nodes else 0.0,
                                'original_nodes': n_nodes,
                            }
                            for pk, pv in gen_params.items():
                                row[f'gen_{pk}'] = pv
                            for metric_name, series in attack_results.items():
                                row[metric_name] = series[step]
                            self._rows.append(row)
                        self._flush()
                        pbar.update(1)
        if self.flush_every > 0:
            self._flush(force=True)
            df = pd.read_csv(self.results_filename)
        else:
            df = pd.DataFrame(self._rows)
            df.to_csv(self.results_filename, index=False)
        return df


def main():
    runner = SimulationRunner(config=STATIC_SIMULATION_CONFIG)
    df = runner.run()
    print(f"Saved results to '{runner.results_filename}' ({len(df)} rows)")


if __name__ == '__main__':
    main()
