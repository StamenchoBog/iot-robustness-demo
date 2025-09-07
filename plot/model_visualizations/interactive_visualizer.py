import os
from pyvis.network import Network

from config import STATIC_SIMULATION_CONFIG
from model_generator.model import generate_network

def visualize_interactively():
    """
    Generates an interactive HTML visualization for each network model
    and saves it to a file.
    """
    print("Starting interactive model visualization...")

    # Define the output directory
    output_dir = "plot/model_visualizations/interactive/interactive_visualizations"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: '{output_dir}'")

    num_nodes = STATIC_SIMULATION_CONFIG['num_nodes']

    for model_name, model_params in STATIC_SIMULATION_CONFIG['models'].items():
        print(f"Generating interactive plot for {model_name}...")

        # 1. Generate the networkx graph
        # Note: We use 'num_nodes' to match the function definition
        G = generate_network(num_nodes=num_nodes, **model_params)

        # 2. Create a Pyvis network object
        # The 'notebook=True' argument is useful for generating standalone HTML files
        # with the control UI.
        nt = Network(height="800px", width="100%", notebook=True, cdn_resources='remote')

        # 3. Load the networkx graph into the Pyvis network
        nt.from_nx(G)

        # 4. Add physics controls to the UI for tweaking the layout
        nt.show_buttons(filter_=['physics'])

        # 5. Generate and save the HTML file
        filename = os.path.join(output_dir, f"{model_name.replace(' ', '_')}.html")
        try:
            nt.show(filename)
        except Exception as e:
            print(f"Could not generate plot for {model_name}. Error: {e}")

    print(f"\nInteractive visualizations saved in the '{output_dir}' folder.")
    print("Open the .html files in your web browser to view them.")


if __name__ == '__main__':
    visualize_interactively()
