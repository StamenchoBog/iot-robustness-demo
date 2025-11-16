# Review of IoT Network Robustness Simulations

## 1. Introduction

This project investigates the robustness of different network topologies in the context of IoT systems. The analysis is divided into two parts: static simulations that test network behavior under structural attacks, and dynamic simulations that model real operational scenarios with energy consumption and data transmission.

The simulations cover five network models, each with 300 nodes:

- `Erdős-Rényi (ER)` - A model representing a random network without structural preferences.
- `Barabási-Albert (BA)` - A model creating a centralized network with "hub nodes" that have many connections.
- `Watts-Strogatz (WS)` - A model built from a network with local clusters connected through several "bridge" nodes.
- `Random Geometric (RGG)` - A model simulating the spatial nature of wireless networks where connectivity depends on physical proximity.
- `Hierarchical` - A network model representing a three-tier architecture with a central hub, several "gateway nodes", and sensors.

The project's goal is to demonstrate and prove network weaknesses under structural attacks and operational conditions, focusing on identifying topologies that offer the best balance between efficiency and resilience.

Note: The focus of processing and analysis is solely on the logical connectivity of nodes, not their physical (geographical) placement and distance.

---

## 2. Metrics

### Static Analysis

Static analysis represents testing each network model with 150 steps/iterations of executions for each of the three attack strategies (Random, Targeted Degree, Targeted Centrality).

Two metrics are processed in static analysis:

- Largest Connected Component (LCC) measures the percentage of nodes in the largest connected component, where reduction indicates network fragmentation.
- Algebraic Connectivity, also known as Fiedler Value, represents the second smallest eigenvalue of the Laplacian matrix and displays the degree of network cohesion. Higher values indicate better connectivity and greater resilience.

### Dynamic Analysis

Dynamic simulations run for 3500 steps/iterations, where each node starts with 100 energy units and consumes 0.03 units per step/iteration, allowing approximately 3333 steps/iterations of lifetime for a given node. During the simulation, random node failures occur with a probability of 2.5% every 40 steps/iterations, with a recovery time of 25 steps/iterations - these random failures simulate real hardware defects, battery problems, or unpredictable environmental conditions (temperature changes, humidity, physical damage). Links between nodes can also temporarily fail with a probability of 0.5% for a period of 10 steps/iterations - this models physical obstructions, electromagnetic interference, or temporary signal loss. Each node attempts to send 2 packets per step/iteration using shortest paths in the network, where each packet is sent to another randomly selected node (not every node communicates with every other node, but only with randomly selected destinations).

The metrics used in dynamic analysis/simulation are:

- `"Data Delivery Ratio (DDR)"` represents the percentage of successfully delivered packets. In each step/iteration of the simulation, each node attempts to send two packets to another randomly selected node. A packet is considered successfully delivered if there is connectivity between the source and destination through active nodes and functional links. DDR is calculated cumulatively. From the beginning of the simulation to the current moment, all successful deliveries are counted and divided by the total number of attempts. For example, if 6500 out of 7000 delivery attempts are successful, DDR is 92.9%.
- `"Time to Recovery (TTR)"` measures the time required for the network to return to at least 95% of its baseline LCC value after a failure. When a planned node failure occurs, the baseline LCC value before the failure is recorded, and then it is tracked how many steps/iterations are needed to achieve recovery.
- `"Time to First Death"` indicates at which step/iteration the first node runs out of energy and dies.
- `"Time to LCC Collapse"` indicates the moment when the LCC value falls below 50% of the initial network size.
- `"Online Fraction"` represents the percentage of active nodes at each step/iteration of the simulation.

---

## 3. Attacks and Strategies

### Static Attacks

In the static simulation, the attack strategies used are:

- `Random Removal` represents a strategy of random node removal.
- `Targeted Degree Attack` removes nodes with the highest degree (Degree Centrality), i.e., those with the most connections.
- `Targeted Centrality Attack` identifies and removes nodes with the highest centrality (Betweenness Centrality), which function as critical bridges between different parts of the network.

### Dynamic Attacks

In the dynamic simulation, the attack strategies used are:

- `Energy Consumption` which is modeled with base consumption of 0.03 units per step for all active nodes. Additionally, each transmission (TX) costs 0.05 units, and each reception (RX) 0.02 units. This mechanism naturally creates an effect similar to a "targeted attack" because hub nodes, which participate in routing more packets, consume energy significantly faster.
- `Random Failures` which simulate hardware defects or unpredictable conditions. With a probability of 2.5% every 40 steps/iterations, a node may fail and automatically recover after 25 steps/iterations. In parallel, link instability is modeled with a probability of 0.5% for temporary failure lasting 10 steps/iterations, simulating the effects of physical obstruction.

---

## 4. Results and Visualizations

### Static Analysis

#### LCC (Largest Connected Component)

![LCC](plots/static_analysis_results/static_analysis_lcc_comparison.png)

**Key Findings:**

| Model | Nodes for 50% LCC Loss | % of Total | Ranking |
|-------|------------------------|------------|---------|
| Hierarchical | 10 | 3.3% | Most Vulnerable |
| Barabási-Albert | 18 | 6.0% | Very Vulnerable |
| Watts-Strogatz | 52 | 17.0% | Moderate |
| Random Geometric | 48 | 16.0% | Moderate |
| Erdős-Rényi | 95 | 31.7% | Most Resilient |

Centralized architectures (`Hierarchical` and `BA`) prove to be extremely vulnerable, where the removal of only `3-6%` of nodes with targeted attacks causes the collapse of half the network connectivity. The `ER` network proves to be the most resilient thanks to its homogeneous structure without clear weak points. The `WS` and `RGG` topologies offer a balance between efficiency and resilience, withstanding up to `16-17%` of targeted attacks before losing half of the baseline LCC.

#### Algebraic Connectivity

![Algebraic Connectivity under attacks](plots/static_analysis_results/static_analysis_algebraic_connectivity_comparison.png)

The algebraic connectivity metric confirms this picture, showing how centralized networks rapidly lose cohesion under targeted attacks. This metric measures the "tightness" of connectivity through the second smallest eigenvalue of the Laplacian matrix - a value of 0 indicates a disconnected network, while higher values indicate better integration. The graphs show that Hierarchical and BA topologies experience a dramatic drop in algebraic connectivity immediately after removing a few key nodes, confirming that their connectivity depends on a small number of critical points. In contrast, the ER model maintains relatively high algebraic connectivity even when a significant percentage of nodes are removed.

---

### Dynamic Analysis

#### LCC (Over Time)

![LCC dynamic](plots/dynamic_analysis_results/dynamic_lcc_overlay.png)

The graph shows how the LCC metric changes over time under the influence of energy consumption, random failures, and unstable links. Distributed topologies (`ER`, `WS`, `RGG`) maintain stable connectivity above 80% of the initial value throughout the entire simulation of 3500 steps/iterations. In contrast, the `Hierarchical` topology begins to fragment around step/iteration 1500 when "gateway nodes" start dying from energy depletion, resulting in LCC dropping below 40%. The `BA` model shows moderate decline, maintaining around 60-70% thanks to some "hub nodes" still surviving and providing minimal connectivity.

#### Online Fraction

![Online Fraction](plots/dynamic_analysis_results/dynamic_online_fraction_overlay.png)

The "Online fraction" metric graph shows the percentage of active nodes over time. Distributed topologies (`ER`, `WS`, `RGG`) maintain over 90% active nodes until the end of the simulation, with the first dead nodes around step/iteration 2000-2500 thanks to balanced energy consumption. In contrast, the `Hierarchical` topology shows decline starting from step/iteration ~1200, dropping to 60-70% active nodes at the end due to intensive energy consumption by "gateway nodes" that route a large portion of the traffic. The `BA` model also declines faster than distributed topologies, but not as dramatically as Hierarchical, maintaining 75-80% active nodes because some "hub nodes" die early while peripheral ones survive longer.

#### Data Delivery Ratio (Cumulative)

![DDR cumulative](plots/dynamic_analysis_results/dynamic_ddr_cumulative_overlay.png)

**Performance:**

| Model | Final DDR | Rating |
|-------|-----------|--------|
| Random Geometric | 92.9% | Excellent |
| Erdős-Rényi | 92.4% | Excellent |
| Watts-Strogatz | 92.2% | Excellent |
| Barabási-Albert | 88.8% | Good |
| Hierarchical | 56.9% | Poor |

The graph shows that distributed topologies (`ER`, `WS`, `RGG`) maintain consistently high DDR values above 92% throughout the entire simulation, indicating that connectivity remains strong enough for successful packet routing even when some nodes die. These networks start with DDR around 95-96% in early phases and gradually decline by 3-4% at the end due to accumulated energy failures. The `BA` model shows moderate decline, finishing at 88.8% DDR, which is still acceptable for most applications. In contrast, the `Hierarchical` topology experiences dramatic collapse: DDR drops from ~80% in early phases to 56.9% at the end of the simulation, which occurs when central "gateway nodes" die and leave isolated clusters of sensors that cannot communicate with each other.

#### Summary Comparison

![Time to First Death](plots/dynamic_analysis_results/dynamic_time_to_first_death_summary.png)

Distributed topologies (`ER`, `WS`, `RGG`) show significantly longer time to first death (around 2000-2500 steps/iterations) due to balanced distribution of traffic and energy consumption. In contrast, the `Hierarchical` network loses nodes much faster - first death occurs around step/iteration 800-1000 due to intensive overloading of "gateway nodes" that must route a portion of the traffic. The `BA` model shows moderate values, with first death around step/iteration 1200-1500, when one of the central "hub nodes" exhausts its energy.

![Time to LCC Collapse](plots/dynamic_analysis_results/dynamic_time_to_lcc_collapse_summary.png)

`ER` and `WS` topologies maintain LCC above 50% the longest (often until the end of the simulation or around step/iteration 3000+) thanks to the balanced structure where there are no critical failure points. The `RGG` model also shows good resilience. The `Hierarchical` topology collapses very early (around step/iteration 1500-1800) when critical "gateway nodes" die and fragment the network. The `BA` model shows moderate resilience, with collapse around step/iteration 2000-2500.

![Mean Time to Recovery](plots/dynamic_analysis_results/dynamic_ttr_mean_summary.png)

Distributed topologies (`ER`, `WS`, `RGG`) show significantly shorter recovery time (around 10-20 steps/iterations) because the loss of one node does not create critical fragmentation, i.e., alternative paths are readily available. In contrast, centralized topologies (`Hierarchical`, `BA`) require longer recovery time (30-50+ steps/iterations) or fail to recover at all if a critical "hub" or "gateway" node fails, because there are not enough alternative paths to compensate for the loss.

![Final DDR](plots/dynamic_analysis_results/dynamic_ddr_final_summary.png)

The final DDR value summarizes the overall success of packet delivery. A clear difference is visible between distributed topologies (green/orange: `ER`, `WS`, `RGG` with DDR >92%) and centralized topologies (`BA` with orange 88.8%, `Hierarchical` with red 56.9%). This difference directly reflects the impact of topology on operational robustness. Distributed networks maintain high performance even under stress, while centralized ones depend on a few critical nodes whose failure dramatically reduces performance.

---

## 5. Conclusion

Centralized topologies (Hierarchical and Barabási-Albert) proved efficient for data distribution in stable conditions, but extremely vulnerable to attacks and energy collapse of "hub nodes". This characteristic makes them unsuitable for scenarios where energy is a limited resource.

Distributed topologies (Erdős-Rényi, Watts-Strogatz, and Random Geometric) showed the best resilience to attacks thanks to balanced distribution of energy consumption across the network. This characteristic enables longer operational life and higher DDR compared to centralized variants.

For IoT system design, the recommendations are clear: critical systems requiring maximum robustness should use ER or WS topologies. For spatial deployments where geographical proximity plays a role, RGG offers an excellent compromise between natural structure and resilience. The Hierarchical model remains most efficient for non-critical systems with physical protection where attacks are unlikely.

### How are the Simulations Executed?

**Static simulation** (`simulation/static_simulation.py`):

```python
for model in models:
    for strategy in ['random', 'targeted_degree', 'targeted_centrality']:
        for run in range(150):
            G = generate_graph(model, 300)
            results = simulate_attack(G, strategy)  # Sequential node removal
            # Measures LCC and Algebraic Connectivity after each removal
```

To invoke it, execute `python -m simulation.static_simulation` in the command terminal.

**Dynamic simulation** (`simulation/dynamic_simulation.py`):

```python
for model in models:
    for run in range(150):
        G = generate_graph(model, 300)
        initialize_energy(G, initial=100.0)
        for step in range(3500):
            # 1. Simulate node failures (2.5% every 40 steps)
            # 2. Simulate link failures (0.5% probability)
            # 3. Attempt packet delivery (shortest path routing)
            # 4. Drain energy (base + TX/RX costs)
            # 5. Check for node deaths (energy <= 0)
            # 6. Record metrics (LCC, DDR, online fraction)
```

To invoke it, execute `python -m simulation.dynamic_simulation` in the command terminal.

Note: Results are saved in CSV format and visualized using matplotlib.
