# iot-robustness-demo

Demonstrating various algorithms and their robustness in the IoT sector.

## Models

To cover a broad set of structures and networks, several graph models are included. Details are here:

- [Graph Models](MODELS_README.md/#static-graph-models)

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

This will generate the results CSV at the path set in config.py (default: static_analysis_Xn_Yr.csv).

### Plot results

Available metrics in the results CSV: lcc, algebraic_connectivity, smoothness.

```shell
# Show plot interactively (default metric: lcc)
python -m plots.plot_results

# Save plots to the plots/ directory (pass only a filename, not a path)
python -m plots.plot_results --save --output static_analysis_lcc_comparison.png
python -m plots.plot_results --metric algebraic_connectivity --save --output static_analysis_algebraic_connectivity_comparison.png
python -m plots.plot_results --metric smoothness --save --output static_analysis_smoothness_comparison.png
```

Notes:
- The plotting script reads the CSV path from config.STATIC_SIMULATION_CONFIG['results_filename'].
- When using --save, files are written into the plots/ directory automatically.

### Generate graph visualizations

```shell
# (Re-)generate graph pictures
python -m models.model_visualizations.visualize_models

# (Re-)generate interactive visualizations using pyvis
python -m models.model_visualizations.interactive_visualizer
```
