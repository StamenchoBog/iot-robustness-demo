import networkx as nx
import math

def generate_network(model_type, num_nodes, **params):
    """
    Generate a network based on the specified model type.
    """
    if model_type == 'ER':
        p = params.get('p', math.log(num_nodes) / num_nodes)
        return nx.erdos_renyi_graph(num_nodes, p)

    elif model_type == 'BA':
        m = params.get('m', 3)
        return nx.barabasi_albert_graph(num_nodes, m)

    elif model_type == 'WS':
        k = params.get('k', 6)
        p = params.get('p', 0.1)
        return nx.watts_strogatz_graph(num_nodes, k, p)

    elif model_type == 'RGG':
        radius = params.get('radius', 0.075)
        return nx.random_geometric_graph(num_nodes, radius)

    elif model_type == 'HIER':
        num_gateways = params.get('num_gateways', 10)
        sensors_per_gateway = params.get('sensors_per_gateway', 49)
        return _generate_hierarchical_network(num_gateways, sensors_per_gateway)

    else:
        raise ValueError(f"Unsupported model type: {model_type}")


def _generate_hierarchical_network(num_gateways=10, sensors_per_gateway=49):
    """
    Generates a two-level hierarchical network with a single sink.
    - Level 0: Sink node
    - Level 1: Gateway nodes connected to the sink
    - Level 2: Sensor nodes connected to their respective gateways
    """
    G = nx.Graph()

    # 1. Add the central sink node
    sink_node = 0
    G.add_node(sink_node, level=0, label='Sink')

    # 2. Add gateway nodes and connect them to the sink
    gateway_nodes = range(1, num_gateways + 1)
    G.add_nodes_from(gateway_nodes, level=1, label='Gateway')
    for gw_node in gateway_nodes:
        G.add_edge(sink_node, gw_node)

    # Optional: Connect gateways to each other in a chain for redundancy
    for i in range(len(gateway_nodes) - 1):
        G.add_edge(gateway_nodes[i], gateway_nodes[i+1])

    # 3. Add sensor nodes and connect them to their parent gateway
    current_node_id = num_gateways + 1
    for gw_node in gateway_nodes:
        for i in range(sensors_per_gateway):
            sensor_node = current_node_id
            G.add_node(sensor_node, level=2, label='Sensor')
            G.add_edge(gw_node, sensor_node)
            current_node_id += 1

    return G
