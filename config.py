STATIC_SIMULATION_CONFIG = {
    'num_nodes': 200,
    'num_runs_per_setting': 100,
    'models': {
        'Erdos-Renyi': {'model_type': 'ER'},
        'Barabasi-Albert': {'model_type': 'BA', 'm': 2},
        'Watts-Strogatz': {'model_type': 'WS', 'k': 4, 'p': 0.1},
        'Random Geometric': {'model_type': 'RGG', 'radius': 0.075},
        'Hierarchical': {
            'model_type': 'HIER',
            'num_gateways': 20,
            'sensors_per_gateway': 9
        },
    },
    'strategies': ['random', 'targeted_degree', 'targeted_centrality'],
    'results_filename': 'static_analysis_200n_100r.csv'
}