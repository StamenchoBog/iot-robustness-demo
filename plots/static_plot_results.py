import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
import numpy as np

from config import STATIC_SIMULATION_CONFIG

class ResultsPlotter:
    """Handles the visualization of simulation results from a DataFrame."""

    def __init__(self, results_df: pd.DataFrame, metric_to_plot: str, show_ci: bool = False, smooth_window: int = 1):
        self.df = results_df.copy()
        self.metric = metric_to_plot
        self.show_ci = show_ci
        self.smooth_window = max(1, smooth_window)
        grp = self.df.groupby(['model_name', 'attack_strategy', 'nodes_removed_fraction'])[self.metric]
        summary = grp.agg(['mean', 'count', 'std']).reset_index()
        summary['ci95'] = 1.96 * (summary['std'] / np.sqrt(summary['count'].clip(lower=1)))
        if self.smooth_window > 1:
            summary = summary.sort_values('nodes_removed_fraction')
            summary['mean'] = summary.groupby(['model_name', 'attack_strategy'])['mean'].transform(
                lambda s: s.rolling(self.smooth_window, min_periods=1).mean()
            )
            if self.show_ci:
                summary['ci95'] = summary.groupby(['model_name', 'attack_strategy'])['ci95'].transform(
                    lambda s: s.rolling(self.smooth_window, min_periods=1).mean()
                )
        self.summary = summary

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
                sd = model_data[model_data['attack_strategy'] == strategy].sort_values('nodes_removed_fraction')
                x = sd['nodes_removed_fraction']
                y = sd['mean']
                ax.plot(x, y, label=strategy.replace('_', ' ').title(), linestyle=line_styles.get(strategy, ':'))
                if self.show_ci:
                    ax.fill_between(x, y - sd['ci95'], y + sd['ci95'], alpha=0.18, linewidth=0)

            ax.set_title(f"{model_name}")
            ax.set_xlabel("Fraction Removed")
            ax.legend()

        y_label = self.metric.replace('_', ' ').title()
        if self.metric == 'lcc':
            y_label = 'Fractional Size of LCC' # Make it more descriptive

        axes[0].set_ylabel(y_label)
        fig.suptitle(f"Network Robustness: {y_label}")
        fig.tight_layout(rect=(0, 0.03, 1, 0.95))

        if save_plot:
            output_dir = "plots/static_analysis_results"
            os.makedirs(output_dir, exist_ok=True)

            filepath = os.path.join(output_dir, output_filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Plot saved to '{filepath}'")
            plt.close()
        else:
            plt.show()


def safe_read_static_results(results_file: str) -> pd.DataFrame:
    """Try to read a static results CSV. If it lacks a header, try to assign reasonable column names.

    Expected layout (when header present):
      model_name, attack_strategy, run_id, seed, step_index, nodes_removed,
      nodes_removed_fraction, original_nodes, gen_<...>..., lcc, smoothness, algebraic_connectivity

    If header is missing, the function will assign the first 8 columns to the base names and
    treat the trailing 3 columns as metrics, inserting generic gen_x names for middle columns.
    """
    try:
        df = pd.read_csv(results_file)
        if 'model_name' in df.columns:
            return df
    except Exception:
        pass

    df = pd.read_csv(results_file, header=None)
    ncols = df.shape[1]
    base = ['model_name', 'attack_strategy', 'run_id', 'seed', 'step_index', 'nodes_removed', 'nodes_removed_fraction', 'original_nodes']
    metrics = ['lcc', 'smoothness', 'algebraic_connectivity']
    if ncols >= len(base) + len(metrics):
        gen_count = ncols - len(base) - len(metrics)
        gen_cols = [f'gen_{i}' for i in range(gen_count)]
        cols = base + gen_cols + metrics
    else:
        cols = base[:min(len(base), ncols)]
        while len(cols) < ncols:
            cols.append(f'col_{len(cols)}')
    df.columns = cols
    return df


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
        default="lcc",
        help="The metric to plot from the results file (one of: 'lcc', 'algebraic_connectivity', 'smoothness')."
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help='Show mean ± 95% CI shading.'
    )
    parser.add_argument(
        '--smooth-window',
        type=int,
        default=1,
        help='Rolling window (steps) to smooth mean (and CI).'
    )
    args = parser.parse_args()

    results_file = STATIC_SIMULATION_CONFIG['results_filename']

    if not os.path.exists(results_file):
        print(f"Error: Results file '{results_file}' not found.")
        print("Please run the simulation script first.")
        return

    print(f"Loading results from '{results_file}'...")
    results_dataframe = safe_read_static_results(results_file)

    if args.metric not in results_dataframe.columns:
        available = ', '.join(c for c in results_dataframe.columns if c not in ['model_name','attack_strategy','run_id','nodes_removed_fraction','nodes_removed','seed','step_index','original_nodes'])
        print(f"Metric '{args.metric}' not found. Available metrics: {available}")
        return

    plotter = ResultsPlotter(results_dataframe, metric_to_plot=args.metric, show_ci=args.ci, smooth_window=args.smooth_window)
    print(f"Generating plots for metric: '{args.metric}'...")

    plotter.plot_comparison(save_plot=args.save, output_filename=args.output)

if __name__ == '__main__':
    main()
