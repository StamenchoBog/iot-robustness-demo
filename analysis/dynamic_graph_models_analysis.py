import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
import pandas as pd

# -----------------------
# Data structures
# -----------------------

@dataclass
class DynamicParams:
    steps: int = 2000
    packet_rate: int = 1  # packets per step
    node_failure_period: int = 100  # introduce a failure every N steps (0 disables)
    node_recovery_steps: int = 20
    base_energy_drain: float = 0.05  # per step drain for online nodes
    tx_energy_cost: float = 0.05     # per hop on path (sender + relays)
    rx_energy_cost: float = 0.02     # per hop on path (receiver)
    initial_energy: float = 100.0
    link_flip_prob: float = 0.0      # probability an edge toggles down per step
    link_down_steps: int = 10
    ttr_epsilon: float = 0.02        # recovery threshold as fraction of baseline LCC
    compute_algebraic_connectivity: bool = False

@dataclass
class TtrEvent:
    start_step: int
    baseline_lcc: float
    recovered_at: Optional[int] = None

# -----------------------
# Helpers for operational graph
# -----------------------

def operational_nodes(graph: nx.Graph) -> List[int]:
    """
    Returns list of currently operational (online) nodes.
    
    Args:
        graph (nx.Graph): Network with node attribute 'online'
    
    Returns:
        List[int]: Node IDs that are currently online
    """
    return [n for n, d in graph.nodes(data=True) if d.get('online', True)]

def is_edge_up(u: int, v: int, graph: nx.Graph) -> bool:
    """
    Check if an edge is currently operational (not experiencing failure).
    
    Args:
        u, v (int): Node IDs of the edge endpoints
        graph (nx.Graph): Network with edge attribute 'up'
    
    Returns:
        bool: True if edge is up, False if down
    """
    return graph.edges[u, v].get('up', True)

def build_operational_graph(graph: nx.Graph) -> nx.Graph:
    """
    Constructs subgraph containing only operational nodes and functional edges.
    
    This represents the 'current state' of the network for routing purposes,
    excluding failed nodes and unstable links.
    
    Args:
        graph (nx.Graph): Full network with node/edge status attributes
    
    Returns:
        nx.Graph: Subgraph with only online nodes and up edges
    """
    nodes = operational_nodes(graph)
    sub = graph.subgraph(nodes).copy()
    # Remove edges that are down
    down_edges = [(u, v) for u, v in sub.edges() if not is_edge_up(u, v, graph)]
    sub.remove_edges_from(down_edges)
    return sub

# -----------------------
# Metrics
# -----------------------

def lcc_fraction(sub: nx.Graph, total_nodes: int) -> float:
    """
    Calculates Largest Connected Component as fraction of total network.
    
    LCC represents the size of the biggest group of nodes that can still
    communicate with each other. Used to measure network fragmentation.
    
    Args:
        sub (nx.Graph): Current operational subgraph
        total_nodes (int): Original total number of nodes in network
    
    Returns:
        float: Fraction (0-1) of nodes in largest connected component
    """
    if sub.number_of_nodes() == 0:
        return 0.0
    if sub.number_of_edges() == 0 and sub.number_of_nodes() > 0:
        # LCC is 1 node if isolated
        return 1.0 / float(total_nodes)
    comps = list(nx.connected_components(sub))
    if not comps:
        return 0.0
    largest = max((len(c) for c in comps), default=0)
    return largest / float(total_nodes)

# -----------------------
# Packet delivery and energy model
# -----------------------

def pick_two_distinct(nodes: List[int]) -> Optional[Tuple[int, int]]:
    """
    Randomly selects two different nodes for packet transmission.
    
    Args:
        nodes (List[int]): Available node IDs
    
    Returns:
        Optional[Tuple[int, int]]: (source, destination) or None if < 2 nodes
    """
    if len(nodes) < 2:
        return None
    a, b = random.sample(nodes, 2)
    return a, b

def attempt_packet(graph: nx.Graph) -> Tuple[bool, Optional[List[int]]]:
    """
    Attempts to deliver a packet between two random nodes.
    
    Process:
        1. Build current operational network
        2. Select random source and destination
        3. Find shortest path (if exists)
        4. Return success status and routing path
    
    Args:
        graph (nx.Graph): Full network state
    
    Returns:
        Tuple[bool, Optional[List[int]]]: 
            - success: True if path exists
            - path: List of node IDs in routing path, or None if failed
    """
    sub = build_operational_graph(graph)
    nodes = list(sub.nodes())
    pair = pick_two_distinct(nodes)
    if pair is None:
        return False, None
    s, t = pair
    try:
        path = nx.shortest_path(sub, s, t)
        return True, path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return False, None

def apply_energy_drain(graph: nx.Graph, path: Optional[List[int]], params: DynamicParams) -> List[int]:
    """
    Drains energy from nodes based on base consumption and packet routing.
    
    Energy model:
        - All online nodes: base_energy_drain per step
        - Sender + relays on path: additional tx_energy_cost
        - Receiver on path: additional rx_energy_cost
        - Node dies when energy <= 0 (permanent death)
    
    Args:
        graph (nx.Graph): Network with node energy attributes
        path (Optional[List[int]]): Routing path from last packet, or None
        params (DynamicParams): Energy cost parameters
    
    Returns:
        List[int]: Node IDs that died this step from energy depletion
    """
    died_now: List[int] = []
    # Base drain for all online nodes
    for n in operational_nodes(graph):
        graph.nodes[n]['energy'] -= params.base_energy_drain
        if graph.nodes[n]['energy'] <= 0 and not graph.nodes[n].get('dead', False):
            graph.nodes[n]['online'] = False
            graph.nodes[n]['dead'] = True
            graph.nodes[n]['recover_timer'] = 0
            died_now.append(n)

    if path is None:
        return died_now

    # Additional drain along the path
    if len(path) >= 2:
        sender = path[0]
        receiver = path[-1]
        intermediates = path[1:-1]

        # Sender + intermediates pay tx per hop
        for n in [sender] + intermediates:
            if graph.nodes[n].get('online', False):
                graph.nodes[n]['energy'] -= params.tx_energy_cost
                if graph.nodes[n]['energy'] <= 0 and not graph.nodes[n].get('dead', False):
                    graph.nodes[n]['online'] = False
                    graph.nodes[n]['dead'] = True
                    graph.nodes[n]['recover_timer'] = 0
                    died_now.append(n)

        # Receiver pays rx cost
        if graph.nodes[receiver].get('online', False):
            graph.nodes[receiver]['energy'] -= params.rx_energy_cost
            if graph.nodes[receiver]['energy'] <= 0 and not graph.nodes[receiver].get('dead', False):
                graph.nodes[receiver]['online'] = False
                graph.nodes[receiver]['dead'] = True
                graph.nodes[receiver]['recover_timer'] = 0
                died_now.append(receiver)

    return died_now

# -----------------------
# Failure and recovery dynamics
# -----------------------

def schedule_random_node_failure(graph: nx.Graph, recover_steps: int) -> Optional[int]:
    """
    Schedules a random node failure to simulate hardware/environmental issues.
    
    Selects random online node (not already dead from energy) and marks it as
    temporarily offline with scheduled recovery time.
    
    Args:
        graph (nx.Graph): Network to modify
        recover_steps (int): Steps until automatic recovery
    
    Returns:
        Optional[int]: ID of failed node, or None if no candidates available
    """
    candidates = [n for n in operational_nodes(graph) if not graph.nodes[n].get('dead', False)]
    if not candidates:
        return None
    victim = random.choice(candidates)
    graph.nodes[victim]['online'] = False
    # Only schedule recovery if not dead due to energy
    if not graph.nodes[victim].get('dead', False):
        graph.nodes[victim]['recover_timer'] = recover_steps
    return victim


def step_recoveries(graph: nx.Graph):
    """
    Processes node recovery timers and brings recovered nodes back online.
    
    Decrements recovery timer for each offline (but not dead) node.
    When timer reaches 0, node comes back online.
    
    Args:
        graph (nx.Graph): Network with node recovery_timer attributes
    """
    for n, d in graph.nodes(data=True):
        if not d.get('online', True) and not d.get('dead', False):
            t = d.get('recover_timer', 0)
            if t > 0:
                graph.nodes[n]['recover_timer'] = t - 1
                if t - 1 == 0:
                    graph.nodes[n]['online'] = True


def step_link_instability(graph: nx.Graph, flip_prob: float, down_steps: int):
    """
    Simulates wireless link instability (interference, obstruction).
    
    Each edge has flip_prob chance to go down for down_steps time.
    Already-down edges count down to recovery.
    
    Args:
        graph (nx.Graph): Network with edge 'up' and 'down_timer' attributes
        flip_prob (float): Probability (0-1) of link failure per step
        down_steps (int): Duration of link outage when it occurs
    """
    if flip_prob <= 0:
        return
    for u, v, ed in graph.edges(data=True):
        if random.random() < flip_prob:
            # toggle down
            ed['up'] = False
            ed['down_timer'] = down_steps
        elif not ed.get('up', True):
            # count down if already down
            t = ed.get('down_timer', 0)
            if t > 0:
                ed['down_timer'] = t - 1
                if t - 1 == 0:
                    ed['up'] = True

# -----------------------
# Initialization
# -----------------------

def initialize_state(graph: nx.Graph, params: DynamicParams):
    """
    Initializes all node and edge attributes for simulation start.
    
    Node attributes:
        - online: True (all nodes start operational)
        - dead: False (no energy deaths yet)
        - recover_timer: 0 (no pending recoveries)
        - energy: initial_energy value
    
    Edge attributes:
        - up: True (all links start functional)
        - down_timer: 0 (no pending link recoveries)
    
    Args:
        graph (nx.Graph): Network to initialize
        params (DynamicParams): Simulation parameters with initial_energy
    """
    for n in graph.nodes():
        graph.nodes[n]['online'] = True
        graph.nodes[n]['dead'] = False
        graph.nodes[n]['recover_timer'] = 0
        graph.nodes[n]['energy'] = float(params.initial_energy)
    for u, v in graph.edges():
        graph.edges[u, v]['up'] = True
        graph.edges[u, v]['down_timer'] = 0

# -----------------------
# Main simulation
# -----------------------

def simulate_dynamic(graph: nx.Graph, params: Optional[DynamicParams] = None, seed: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Main dynamic simulation: models realistic IoT network operation over time.
    
    Simulates:
        - Energy consumption (base + TX/RX costs from packet routing)
        - Random node failures with recovery
        - Link instability (wireless interference)
        - Packet delivery attempts via shortest-path routing
        - Node death from energy depletion (permanent)
    
    Tracked metrics per time step:
        - LCC (largest connected component fraction)
        - Online fraction (active nodes)
        - DDR cumulative (data delivery ratio)
        - Successful/total packets
    
    Summary metrics:
        - Time to first node death
        - Time to LCC collapse (< 50%)
        - Time to Recovery (TTR) statistics
        - Final DDR
    
    Args:
        graph (nx.Graph): Network topology to simulate
        params (Optional[DynamicParams]): Simulation parameters, uses defaults if None
        seed (Optional[int]): Random seed for reproducibility
    
    Returns:
        Tuple[pd.DataFrame, Dict[str, float]]:
            - Time-series DataFrame with metrics per step
            - Summary dictionary with aggregate statistics
    """
    if params is None:
        params = DynamicParams()

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    initialize_state(graph, params)

    total_nodes = graph.number_of_nodes()
    total_packets = 0
    successful_packets = 0

    first_death_time: Optional[int] = None
    lcc_collapse_time: Optional[int] = None  # when LCC fraction drops below 0.5

    ttr_events: List[TtrEvent] = []

    # Initial baseline LCC (kept for reference; per-event baseline is captured on failure)
    sub0 = build_operational_graph(graph)
    _baseline_lcc = lcc_fraction(sub0, total_nodes)

    records: List[Dict] = []

    for t in range(params.steps):
        # Failure event schedule
        if params.node_failure_period and t > 0 and t % params.node_failure_period == 0:
            # capture baseline before failure
            sub_pre = build_operational_graph(graph)
            baseline = lcc_fraction(sub_pre, total_nodes)
            scheduled = schedule_random_node_failure(graph, params.node_recovery_steps)
            if scheduled is not None:
                ttr_events.append(TtrEvent(start_step=t, baseline_lcc=baseline))

        # Link instability and recoveries
        step_link_instability(graph, params.link_flip_prob, params.link_down_steps)
        step_recoveries(graph)

        # Packet attempts
        delivered_this_step = 0
        path_used: Optional[List[int]] = None
        for _ in range(params.packet_rate):
            success, path = attempt_packet(graph)
            total_packets += 1
            if success:
                successful_packets += 1
                delivered_this_step += 1
                path_used = path

        # Energy drain (base + any path cost)
        died_now = apply_energy_drain(graph, path_used, params)
        if died_now and first_death_time is None:
            first_death_time = t

        # Metrics at this step
        sub = build_operational_graph(graph)
        lcc = lcc_fraction(sub, total_nodes)
        online_frac = len(operational_nodes(graph)) / float(total_nodes) if total_nodes else 0.0

        if lcc_collapse_time is None and lcc < 0.5:
            lcc_collapse_time = t

        # Resolve TTR events if recovered
        for ev in ttr_events:
            if ev.recovered_at is None and lcc >= max(0.0, ev.baseline_lcc * (1 - params.ttr_epsilon)):
                ev.recovered_at = t

        rec: Dict[str, float] = {
            'time': t,
            'lcc': lcc,
            'online_fraction': online_frac,
            'successful_packets': successful_packets,
            'total_packets': total_packets,
            'ddr_cumulative': (successful_packets / total_packets) if total_packets else 0.0,
            'delivered_this_step': delivered_this_step,
            'ddr_step': (delivered_this_step / float(params.packet_rate)) if params.packet_rate > 0 else np.nan,
        }

        if params.compute_algebraic_connectivity:
            # Compute on LCC subgraph only
            if sub.number_of_nodes() > 0:
                comps = list(nx.connected_components(sub))
                if comps:
                    largest_nodes_iter = max(comps, key=len)
                    largest_nodes = list(largest_nodes_iter)
                    lcc_subgraph = sub.subgraph(largest_nodes)
                    try:
                        rec['algebraic_connectivity'] = float(nx.algebraic_connectivity(lcc_subgraph))
                    except nx.NetworkXError:
                        rec['algebraic_connectivity'] = 0.0
                else:
                    rec['algebraic_connectivity'] = 0.0
            else:
                rec['algebraic_connectivity'] = 0.0

        records.append(rec)

    # Summaries
    ttrs = [ev.recovered_at - ev.start_step for ev in ttr_events if ev.recovered_at is not None]
    summary = {
        'ddr_final': (successful_packets / total_packets) if total_packets else 0.0,
        'time_to_first_death': first_death_time if first_death_time is not None else float('inf'),
        'time_to_lcc_collapse': lcc_collapse_time if lcc_collapse_time is not None else float('inf'),
        'ttr_events_count': len(ttr_events),
        'ttr_mean': float(np.mean(ttrs)) if ttrs else float('inf'),
        'ttr_median': float(np.median(ttrs)) if ttrs else float('inf'),
    }

    df = pd.DataFrame.from_records(records)
    return df, summary

