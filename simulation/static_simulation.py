import pandas as pd
from tqdm import tqdm
from typing import Dict, Any

from config import STATIC_SIMULATION_CONFIG
from model_generator.model import generate_network
from analysis.static_graph_models_analysis import simulate_attack

class SimulationRunner:
    """Encapsulates the logic for running the simulation suite."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []

    def run(self) -> pd.DataFrame:
        """Executes the simulation based on the provided configuration."""
        num_total_runs = (
                len(self.config['models']) * len(self.config['strategies']) * self.config['num_runs_per_setting']
        )
        print(f"Starting simulations... Total experiments to run: {num_total_runs}")

        with tqdm(total=num_total_runs, desc="Overall Progress") as pbar:
            for model_name, model_params in self.config['models'].items():
                for strategy in self.config['strategies']:
                    for i in range(self.config['num_runs_per_setting']):

                        # --- 1. Generate network (corrected call) ---
                        params_for_func = model_params.copy()
                        params_for_func.pop('model_type')
                        G = generate_network(
                            model_type=model_params['model_type'],
                            num_nodes=self.config['num_nodes'],
                            **params_for_func
                        )

                        # --- 2. Run attack simulation to get the dictionary of results ---
                        attack_results = simulate_attack(G, strategy)

                        # --- 3. Process the dictionary of results ---
                        # The number of steps is the length of any of the metric lists
                        num_steps = len(attack_results['lcc'])
                        num_graph_nodes = len(G.nodes()) # Use actual graph size for accuracy

                        for step in range(num_steps):
                            # Start with the base info for this row
                            row_data = {
                                'model_name': model_name,
                                'attack_strategy': strategy,
                                'run_id': i,
                                'nodes_removed_fraction': step / num_graph_nodes if num_graph_nodes > 0 else 0
                            }

                            # Add the value of each metric at the current step to the row
                            for metric_name, values_list in attack_results.items():
                                # This will create columns like 'lcc' and 'smoothness'
                                row_data[metric_name] = values_list[step]

                            self.results.append(row_data)

                        pbar.update(1)

        print("Simulations complete.")
        return pd.DataFrame(self.results)

def main():
    """Main function to execute the simulation and save the results."""
    runner = SimulationRunner(config=STATIC_SIMULATION_CONFIG)
    results_dataframe = runner.run()

    output_file = STATIC_SIMULATION_CONFIG['results_filename']
    results_dataframe.to_csv(output_file, index=False)
    print(f"\nResults successfully saved to '{output_file}'")

if __name__ == '__main__':
    main()
