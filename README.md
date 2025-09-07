# iot-robustness-demo

Demonstrating various algorithm and their robustness in the IoT sector.

## Models

In order to include a bigger scope of structures and networks, a couple of graph models were included. Details about them,
and definition on them can be seen on the link below.

- [Graph Models](MODELS_README.md/#static-graph-models)

## 

## Local Development

### Install Requirements

```shell
# To install the Python 3.13.7 and use it later on
asdf install

# Install required packages
pip install -r requirements.txt

### Configure parameters in config.py ###

# Start the simulation
python -m simulation.simulation

# Generate plots
## Without export as images
python -m plot.plot_results

## With export as images
python -m plot.plot_results --save

## With export as images and predefined file name
python -m plot.plot_results --metric smoothness --save --output static_analysis_lcc_comparison.png
python -m plot.plot_results --metric algebraic_connectivity --save --output static_analysis_algebraic_connectivity_comparison.png
python -m plot.plot_results --metric smoothness --save --output static_analysis_smoothness_comparison.pn
```
