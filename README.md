# iot-robustness-demo

Demonstrating various algorithms and their robustness in the IoT sector.

## Models

To cover a broad set of structures and networks, several graph models are included. Details can be found here:

- [Graph Models](MODELS_README.md/#graph-models)

## Local Development

### Current Configuration (config.py)

**Simulation Parameters:**
- Nodes: 300 per network
- Runs: 150 per model/strategy
- Dynamic steps: 3500 (captures energy depletion)
- Energy: 100 initial, 0.03 base drain (~3333 step lifetime)

**Network Models:** Erdős-Rényi, Barabási-Albert, Watts-Strogatz, Random Geometric, Hierarchical

**Attack Strategies (Static):** Random, Targeted Degree, Targeted Centrality

### Install Requirements

```shell
# Install the Python version from .tool-versions
asdf install

# Install required packages
pip install -r requirements.txt
```

Configure parameters in config.py as needed (node count, models, strategies, output filename).

### Run simulations

Static analysis (recommended entry points):

```shell
# Run the static simulation module directly
python -m simulation.static_simulation

# Run the dynamic simulation module directly
python -m simulation.dynamic_simulation
```

Note: CSV results are saved to the `csv/` folder (configured in config.py):

- Attack simulation: `csv/attack_simulation_results.csv`
- Operational simulation: `csv/operational_simulation_timeseries.csv` and `csv/operational_simulation_summary.csv`

### Plot results

Available metrics in the results CSV: `lcc`, `algebraic_connectivity`.

```shell
# Save plots from static analysis to the plots/ directory (pass only a filename, not a path)
## Metrics (LCC, Algebraic Connectivity)
python -m plots.static_plot_results --save --output static_analysis_lcc_comparison.png
python -m plots.static_plot_results --metric algebraic_connectivity --save --output static_analysis_algebraic_connectivity_comparison.png

# Dynamic analysis plots
## Overlay plots (all models on one chart for comparison)
python -m plots.dynamic_plot_results --plot timeseries-overlay --metric lcc --save
python -m plots.dynamic_plot_results --plot timeseries-overlay --metric ddr_cumulative --save
python -m plots.dynamic_plot_results --plot timeseries-overlay --metric online_fraction --save

## Summary plots (bar charts with color-coded performance)
python -m plots.dynamic_plot_results --plot summary --summary-metric ddr_final --save
python -m plots.dynamic_plot_results --plot summary --summary-metric ttr_mean --save
python -m plots.dynamic_plot_results --plot summary --summary-metric time_to_first_death --save
python -m plots.dynamic_plot_results --plot summary --summary-metric time_to_lcc_collapse --save
```

Notes:

- Simulation runs for 3500 steps to capture energy depletion effects
- When using `--save`, files are written into `plots/dynamic_analysis_results/` automatically
- Overlay plots show all models on one chart for easy comparison
- Summary plots use color coding: green (good), orange (moderate), red (poor)

### Generate graph visualizations

```shell
# (Re-)generate graph pictures
python -m models.model_visualizations.visualize_models

# (Re-)generate interactive visualizations using pyvis
python -m models.model_visualizations.interactive_visualizer
```
