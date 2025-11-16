import networkx as nx
import random
import numpy as np
from typing import List, Dict

def calculate_algebraic_connectivity(graph: nx.Graph) -> float:
    """
    Calculates the algebraic connectivity (Fiedler value) of the graph.
    
    Algebraic connectivity is the second smallest eigenvalue of the graph's
    Laplacian matrix. It measures how well-connected the graph is:
    - Higher values = better connectivity and robustness
    - Value of 0 = disconnected graph
    
    Args:
        graph (nx.Graph): Input graph to analyze
    
    Returns:
        float: Algebraic connectivity value, or 0.0 if disconnected
    """
    if not nx.is_connected(graph):
        return 0.0
    # This function can be computationally intensive on very large graphs
    try:
        # Use a faster, approximate method if needed for large graphs
        # For now, the exact method is fine.
        return nx.algebraic_connectivity(graph)
    except nx.NetworkXError:
        return 0.0

def calculate_signal_smoothness(graph: nx.Graph, signal: Dict) -> float:
    """
    Calculates the signal smoothness using the Laplacian quadratic form (x'Lx).
    A lower value means the signal is smoother across the graph.
    """
    # Ensure the graph is not empty
    if not graph.nodes():
        return 0.0

    # Get the Laplacian matrix and the node order
    L = nx.laplacian_matrix(graph)
    node_order = list(graph.nodes())

    # Create the signal vector in the correct order
    signal_vector = np.array([signal[n] for n in node_order])

    # Calculate the quadratic form: x' * L * x
    smoothness = signal_vector.T @ L @ signal_vector
    return smoothness


def simulate_attack(graph: nx.Graph, strategy: str) -> Dict[str, List[float]]:
    """
    Simulates sequential node removal attack on network, tracking degradation metrics.
    
    Process:
        1. Determine removal order based on strategy
        2. Record initial metrics
        3. Remove nodes one by one
        4. After each removal, measure LCC and algebraic connectivity
    
    Args:
        graph (nx.Graph): Network to attack
        strategy (str): Attack strategy - 'random', 'targeted_degree', or 'targeted_centrality'
            - random: Random node removal order
            - targeted_degree: Remove highest-degree nodes first
            - targeted_centrality: Remove highest-betweenness nodes first
    
    Returns:
        Dict[str, List[float]]: Dictionary with keys:
            - 'lcc': List of LCC fractions (0-1) after each removal
            - 'algebraic_connectivity': List of connectivity values after each removal
    """
    g = graph.copy()
    n_initial = len(g.nodes())

    if strategy == 'random':
        nodes_to_remove = list(g.nodes())
        random.shuffle(nodes_to_remove)
    elif strategy == 'targeted_degree':
        nodes_to_remove = sorted(g.nodes(), key=lambda n: g.degree(n), reverse=True)
    elif strategy == 'targeted_centrality':
        centrality = nx.betweenness_centrality(g)
        nodes_to_remove = sorted(centrality, key=centrality.get, reverse=True)
    else:
        raise ValueError(f"Unknown attack strategy: {strategy}")

    # --- Initialize lists to store the history of each metric ---
    results = {
        'lcc': [],
        'algebraic_connectivity': []
    }

    # --- Measure initial state before any nodes are removed ---
    if g.nodes():
        initial_lcc_graph = g.subgraph(max(nx.connected_components(g), key=len)).copy()
        results['lcc'].append(len(initial_lcc_graph) / n_initial)
        results['algebraic_connectivity'].append(calculate_algebraic_connectivity(initial_lcc_graph))
    else: # Handle case of empty graph
        results['lcc'].append(0)
        results['algebraic_connectivity'].append(0)

    # --- Sequentially remove nodes and record metrics ---
    for node in nodes_to_remove:
        g.remove_node(node)

        if not g.nodes():
            results['lcc'].append(0)
            results['algebraic_connectivity'].append(0)
            continue

        lcc_subgraph = g.subgraph(max(nx.connected_components(g), key=len, default=set())).copy()

        results['lcc'].append(len(lcc_subgraph) / n_initial)
        results['algebraic_connectivity'].append(calculate_algebraic_connectivity(lcc_subgraph))

    return results
