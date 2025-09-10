def models():
    return {
        'Erdos-Renyi': {'model_type': 'ER'},
        'Barabasi-Albert': {'model_type': 'BA', 'm': 2},
        'Watts-Strogatz': {'model_type': 'WS', 'k': 4, 'p': 0.1},
        'Random Geometric': {'model_type': 'RGG', 'radius': 0.10},
        'Hierarchical': {
            'model_type': 'HIER',
            'num_gateways': 20,
            'sensors_per_gateway': 9
        },
    }

STATIC_SIMULATION_CONFIG = {
    'num_nodes': 200,
    'num_runs_per_setting': 100,
    'models': models(),
    'strategies': ['random', 'targeted_degree', 'targeted_centrality'],
    'results_filename': 'static_analysis_200n_100r.csv'
}

DYNAMIC_SIMULATION_CONFIG = {
    'num_nodes': 200,
    'num_runs_per_setting': 20,
    'models': models(),
    # Dynamic parameters
    'steps': 1000,
    'packet_rate': 2,
    'node_failure_period': 100,
    'node_recovery_steps': 20,
    'base_energy_drain': 0.05,
    'tx_energy_cost': 0.05,
    'rx_energy_cost': 0.02,
    'initial_energy': 100.0,
    'link_flip_prob': 0.0,
    'link_down_steps': 10,
    'ttr_epsilon': 0.02,
    # Outputs
    'timeseries_filename': 'dynamic_timeseries.csv',
    'summary_filename': 'dynamic_summary.csv',
}
