import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse

from config import STATIC_SIMULATION_CONFIG

class ResultsPlotter:
    """Handles the visualization of simulation results from a DataFrame."""

    def __init__(self, results_df: pd.DataFrame, metric_to_plot: str):
        self.df = results_df
        self.metric = metric_to_plot
        self.summary = results_df.groupby(
            ['model_name', 'attack_strategy', 'nodes_removed_fraction']
        )[self.metric].mean().reset_index()

    def plot_comparison(self, save_plot=False, output_filename="resilience_comparison.png"):
        """Creates a multi-plot figure for comparison."""
        models = self.summary['model_name'].unique()
        n_models = len(models)

        plt.style.use('seaborn-v0_8-whitegrid')
        fig, axes = plt.subplots(1, n_models, figsize=(7 * n_models, 6), sharey=False)
        if n_models == 1: axes = [axes]

        line_styles = {'random': '--', 'targeted_degree': '-', 'targeted_centrality': '-.'}

        for ax, model_name in zip(axes, models):
            model_data = self.summary[self.summary['model_name'] == model_name]
            for strategy in model_data['attack_strategy'].unique():
                strategy_data = model_data[model_data['attack_strategy'] == strategy]

                ax.plot(
                    strategy_data['nodes_removed_fraction'],
                    strategy_data[self.metric],
                    label=strategy.replace("_", " ").title(),
                    linestyle=line_styles.get(strategy, ':')
                )

            ax.set_title(f"Resilience of {model_name} Network", fontsize=14)
            ax.set_xlabel("Fraction of Nodes Removed")
            ax.legend()

        y_label = self.metric.replace("_", " ").title()
        if self.metric == 'lcc':
            y_label = "Fractional Size of LCC" # Make it more descriptive

        axes[0].set_ylabel(y_label)
        fig.suptitle(f"Network Robustness Comparison: {y_label}", fontsize=16)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        if save_plot:
            output_dir = "plots"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            filepath = os.path.join(output_dir, output_filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Plot successfully saved to '{filepath}'")
            plt.close()
        else:
            plt.show()

def main():
    """Main function to load results and generate plots."""
    parser = argparse.ArgumentParser(description="Plot network resilience simulation results.")
    parser.add_argument(
        '--save',
        action='store_true',
        help="Save the plot to a file instead of displaying it."
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default="resilience_comparison.png",
        help="Name of the output file if --save is used."
    )
    parser.add_argument(
        '-m', '--metric',
        type=str,
        default="lcc", # Default to plotting LCC
        help="The metric to plot from the results file (e.g., 'lcc', 'smoothness')."
    )
    args = parser.parse_args()

    results_file = STATIC_SIMULATION_CONFIG['results_filename']

    if not os.path.exists(results_file):
        print(f"Error: Results file '{results_file}' not found.")
        print("Please run the simulation script first.")
        return

    print(f"Loading results from '{results_file}'...")
    results_dataframe = pd.read_csv(results_file)

    plotter = ResultsPlotter(results_dataframe, metric_to_plot=args.metric)
    print(f"Generating plots for metric: '{args.metric}'...")

    plotter.plot_comparison(save_plot=args.save, output_filename=args.output)

if __name__ == '__main__':
    main()
