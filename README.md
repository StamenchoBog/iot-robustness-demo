# iot-robustness-demo

Demonstrating various algorithms and their robustness in the IoT sector.

## Models

To cover a broad set of structures and networks, several graph models are included. Details can be found here:

- [Graph Models](MODELS_README.md/#graph-models)

## Local Development

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

Note: This will generate the results CSV at the path set in config.py (default: static_analysis_Xn_Yr.csv).

### Plot results

Available metrics in the results CSV: `lcc`, `algebraic_connectivity`.

```shell
# Save plots from static analysis to the plots/ directory (pass only a filename, not a path)
## Metrics (LCC, Algebraic Connectivity)
python -m plots.static_plot_results --save --output static_analysis_lcc_comparison.png
python -m plots.static_plot_results --metric algebraic_connectivity --save --output static_analysis_algebraic_connectivity_comparison.png

# Dynamic analysis plots
## Overlay plots (all models on one chart for comparison)
python -m plots.dynamic_plot_results --plot timeseries-overlay --metric lcc --save --output dynamic_lcc_overlay.png
python -m plots.dynamic_plot_results --plot timeseries-overlay --metric ddr_cumulative --save --output dynamic_ddr_overlay.png
python -m plots.dynamic_plot_results --plot timeseries-overlay --metric online_fraction --save --output dynamic_online_overlay.png

## Summary plots (bar charts with color-coded performance)
python -m plots.dynamic_plot_results --plot summary --summary-metric ddr_final --save --output dynamic_ddr_summary.png
python -m plots.dynamic_plot_results --plot summary --summary-metric ttr_mean --save --output dynamic_ttr_summary.png
python -m plots.dynamic_plot_results --plot summary --summary-metric time_to_lcc_collapse --save --output dynamic_lcc_collapse_summary.png
```

Notes:
- When using `--save`, files are written into the plots/ directory automatically.
- Overlay plots show all models on one chart for easy comparison

### Generate graph visualizations

```shell
# (Re-)generate graph pictures
python -m models.model_visualizations.visualize_models

# (Re-)generate interactive visualizations using pyvis
python -m models.model_visualizations.interactive_visualizer
```
