import os
import random
from typing import Dict, Any, List
import pandas as pd
from tqdm import tqdm

from config import STATIC_SIMULATION_CONFIG
from models.model_generator import generate_network
from analysis.static_graph_models_analysis import simulate_attack


class SimulationRunner:
    """
    Orchestrates static attack simulations across multiple network models.
    
    Runs experiments for all combinations of:
        - Network models (ER, BA, WS, RGG, Hierarchical)
        - Attack strategies (random, targeted_degree, targeted_centrality)
        - Multiple runs for statistical validity
    
    Results are incrementally flushed to CSV to handle large datasets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config (Dict): Configuration with keys:
                - models: Dict of model definitions
                - strategies: List of attack strategies
                - num_runs_per_setting: Runs per model/strategy combo
                - num_nodes: Network size
                - results_filename: Output CSV path
                - flush_every: Rows to buffer before flushing (0 = flush at end)
                - random_seed_base: Base for reproducible seeds
        """
        self.config = config
        self.flush_every = int(config.get('flush_every', 0))
        self.random_seed_base = config.get('random_seed_base')
        self.results_filename = config['results_filename']
        self._rows: List[Dict[str, Any]] = []

    def _seed(self, model_name: str, strategy: str, run_id: int) -> int | None:
        """
        Generates deterministic seed for reproducible experiments.
        
        Combines base seed with run_id and hash of (model, strategy) to ensure
        different experiments get different but reproducible random sequences.
        
        Args:
            model_name: Network model name
            strategy: Attack strategy name
            run_id: Run number (0 to num_runs-1)
        
        Returns:
            int or None: Seed value, or None if random_seed_base not configured
        """
        if self.random_seed_base is None:
            return None
        seed = (self.random_seed_base
                + run_id
                + (hash((model_name, strategy)) & 0xFFFF))
        random.seed(seed)
        return seed

    def _flush(self, force: bool = False):
        """
        Writes buffered results to CSV file.
        
        Implements incremental flushing to avoid memory overflow with large datasets.
        Appends to existing file if present, creates new file otherwise.
        
        Args:
            force: If True, flush regardless of buffer size
        """
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
        """
        Executes all static attack simulations.
        
        For each (model, strategy, run) combination:
            1. Generate network with reproducible seed
            2. Run attack simulation (sequential node removal)
            3. Record metrics at each step (LCC, algebraic connectivity)
            4. Flush results incrementally to CSV
        
        Returns:
            pd.DataFrame: Complete results with columns:
                - model_name, attack_strategy, run_id, seed
                - step_index, nodes_removed, nodes_removed_fraction
                - lcc, algebraic_connectivity
                - model generation parameters (gen_*)
        """
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
