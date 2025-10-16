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
    'num_nodes': 300,
    'num_runs_per_setting': 150,
    'models': models(),
    'strategies': ['random', 'targeted_degree', 'targeted_centrality'],
    'results_filename': 'static_analysis_300n_150r.csv',
    'random_seed_base': 1000,
    'flush_every': 0,
}

DYNAMIC_SIMULATION_CONFIG = {
    'num_nodes': 300,
    'num_runs_per_setting': 150,
    'models': models(),
    'steps': 1000,
    'packet_rate': 2,
    'node_failure_period': 40,
    'node_recovery_steps': 25,
    'base_energy_drain': 0.12,
    'tx_energy_cost': 0.05,
    'rx_energy_cost': 0.02,
    'initial_energy': 50.0,
    'link_flip_prob': 0.005,
    'link_down_steps': 10,
    'ttr_epsilon': 0.01,
    'ddr_smoothing_window': 20,
    'timeseries_filename': 'dynamic_analysis_timeseries_300n_150r.csv',
    'summary_filename': 'dynamic_analysis_summary_300n_150r.csv',
    'random_seed_base': 2000,
    'flush_every': 0,
}
