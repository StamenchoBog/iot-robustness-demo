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
    return [n for n, d in graph.nodes(data=True) if d.get('online', True)]

def is_edge_up(u: int, v: int, graph: nx.Graph) -> bool:
    return graph.edges[u, v].get('up', True)

def build_operational_graph(graph: nx.Graph) -> nx.Graph:
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
    if len(nodes) < 2:
        return None
    a, b = random.sample(nodes, 2)
    return a, b

def attempt_packet(graph: nx.Graph) -> Tuple[bool, Optional[List[int]]]:
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
    for n, d in graph.nodes(data=True):
        if not d.get('online', True) and not d.get('dead', False):
            t = d.get('recover_timer', 0)
            if t > 0:
                graph.nodes[n]['recover_timer'] = t - 1
                if t - 1 == 0:
                    graph.nodes[n]['online'] = True


def step_link_instability(graph: nx.Graph, flip_prob: float, down_steps: int):
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

