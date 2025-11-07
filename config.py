def models():
    return {
        'Erdos-Renyi': {'model_type': 'ER'},
        'Barabasi-Albert': {'model_type': 'BA', 'm': 2},
        'Watts-Strogatz': {'model_type': 'WS', 'k': 6, 'p': 0.1},  # Increased k from 4 to 6 for better connectivity
        'Random Geometric': {'model_type': 'RGG', 'radius': 0.125},  # Increased from 0.10 for better connectivity
        'Hierarchical': {
            'model_type': 'HIER',
            'num_gateways': 20,
            'sensors_per_gateway': 14  # Adjusted from 9 to get ~300 nodes (1+20+280=301)
        },
    }

STATIC_SIMULATION_CONFIG = {
    'num_nodes': 300,
    'num_runs_per_setting': 150,
    'models': models(),
    'strategies': ['random', 'targeted_degree', 'targeted_centrality'],
    'results_filename': 'csv/attack_simulation_results.csv',
    'random_seed_base': 1000,
    'flush_every': 0,
}

DYNAMIC_SIMULATION_CONFIG = {
    'num_nodes': 300,
    'num_runs_per_setting': 150,
    'models': models(),
    'steps': 3500,
    'packet_rate': 2,
    'node_failure_period': 40,
    'node_recovery_steps': 25,
    'base_energy_drain': 0.03,  # Reduced from 0.12 for longer-lived networks
    'tx_energy_cost': 0.05,
    'rx_energy_cost': 0.02,
    'initial_energy': 100.0,  # Increased from 50.0 for more realistic lifetime
    'link_flip_prob': 0.005,
    'link_down_steps': 10,
    'ttr_epsilon': 0.05,  # Increased from 0.01 to capture meaningful disruptions
    'ddr_smoothing_window': 20,
    'timeseries_filename': 'csv/operational_simulation_timeseries.csv',
    'summary_filename': 'csv/operational_simulation_summary.csv',
    'random_seed_base': 2000,
    'flush_every': 0,
}
