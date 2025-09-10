import networkx as nx
import matplotlib.pyplot as plt
import os
import numpy as np

from config import STATIC_SIMULATION_CONFIG
from models.model_generator import generate_network

def _generate_hierarchical_layout(G):
    """
    Creates a custom layout for the hierarchical graph to display layers clearly.
    """
    pos = {}
    nodes_by_level = {0: [], 1: [], 2: []}
    for n, data in G.nodes(data=True):
        nodes_by_level[data['level']].append(n)

    pos[nodes_by_level[0][0]] = (0, 0)

    num_gateways = len(nodes_by_level[1])
    gateway_ys = np.linspace(-num_gateways / 2, num_gateways / 2, num_gateways)
    for i, gw_node in enumerate(nodes_by_level[1]):
        pos[gw_node] = (1, gateway_ys[i])

    for gw_node in nodes_by_level[1]:
        parent_gateway_pos = pos[gw_node]
        child_sensors = [n for n in G.neighbors(gw_node) if G.nodes[n]['level'] == 2]
        num_sensors = len(child_sensors)
        sensor_ys = np.linspace(-0.2, 0.2, num_sensors) + parent_gateway_pos[1]
        for i, sensor_node in enumerate(child_sensors):
            pos[sensor_node] = (2, sensor_ys[i])

    return pos

def visualize_and_save_models():
    """
    Generates, visualizes, and saves an image of each network model
    defined in the configuration file with model-specific layouts.
    """
    print("Starting model visualization...")

    output_dir = "models/model_visualizations/pictures"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: '{output_dir}'")

    num_nodes_config = STATIC_SIMULATION_CONFIG['num_nodes']

    for model_name, model_params in STATIC_SIMULATION_CONFIG['models'].items():
        print(f"Generating visualization for {model_name}...")

        func_models_param = model_params.copy()
        func_models_param.pop('model_type')

        G = generate_network(
            model_type=model_params['model_type'],
            num_nodes=num_nodes_config,
            **func_models_param
        )

        plt.figure(figsize=(12, 12))

        if model_params['model_type'] == 'RGG':
            pos = {n: G.nodes[n]['pos'] for n in G.nodes}
            node_sizes, node_colors = 50, "#00B4D8"
            plt.title(f"{model_name} Topology (N={len(G.nodes())}) - Geographic Layout", fontsize=16)

        elif model_params['model_type'] == 'HIER':
            pos = _generate_hierarchical_layout(G)
            color_map = {0: 'red', 1: 'orange', 2: 'skyblue'}
            node_colors = [color_map[G.nodes[n]['level']] for n in G.nodes]
            size_map = {0: 500, 1: 200, 2: 30}
            node_sizes = [size_map[G.nodes[n]['level']] for n in G.nodes]
            plt.title(f"{model_name} Topology (N={len(G.nodes())}) - Custom Layered Layout", fontsize=16)

        elif model_params['model_type'] == 'BA':
            pos = nx.spring_layout(G, seed=42)
            node_sizes = [d * 20 for n, d in G.degree()]
            node_colors = "#FF5733"
            plt.title(f"{model_name} Topology (N={len(G.nodes())}) - Spring Layout", fontsize=16)

        else: # Default for ER, WS
            pos = nx.spring_layout(G, seed=42)
            node_sizes, node_colors = 50, "#33A1FF"
            plt.title(f"{model_name} Topology (N={len(G.nodes())}) - Spring Layout", fontsize=16)

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)
        nx.draw_networkx_edges(G, pos, width=0.5, alpha=0.5, edge_color='gray')

        plt.axis('off')
        filename = os.path.join(output_dir, f"{model_name.replace(' ', '_')}_model.png")
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

    print(f"\nVisualizations saved successfully in the '{output_dir}' folder.")

if __name__ == '__main__':
    visualize_and_save_models()