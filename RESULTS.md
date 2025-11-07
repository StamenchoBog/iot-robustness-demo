# Network Robustness Analysis: Results

## 1. Static Analysis: Targeted Attack Resilience

### Overview

This analysis simulates three attack strategies on 300-node networks (150 runs each):

- **Random removal**: Baseline random failures
- **Targeted degree**: Remove highest-degree nodes first
- **Targeted centrality**: Remove highest-betweenness nodes first

### Quantitative Metrics

**Time to 50% LCC Loss (Targeted Degree Attack):**

| Network Model | Nodes to 50% Loss | % of Total Nodes |
| :--- | :--- | :--- |
| Hierarchical | 10 | 3.3% |
| Barabási-Albert | 18 | 6% |
| Watts-Strogatz | 52 | 17% |
| Random Geometric | 48 | 16% |
| Erdős-Rényi | 95 | 32% |

**Vulnerability Index** (% of nodes to remove for 50% LCC loss - lower = more vulnerable):

| Network Model | Vulnerability Index | Resilience Rank |
| :--- | :--- | :--- |
| Hierarchical | 3.3% | Extremely Vulnerable |
| Barabási-Albert | 6.0% | Very Vulnerable |
| Watts-Strogatz | 17.0% | Moderate |
| Random Geometric | 16.0% | Moderate |
| Erdős-Rényi | 31.7% | Most Resilient |

### Key Findings

**Centralized Topologies (Hierarchical, Barabási-Albert):**

- Critical vulnerability: Degree and centrality attacks are identical - hubs/gateways are also key bridges
- Rapid collapse: Only 3-6% targeted removal causes 50% connectivity loss
- **Implication:** Unsuitable for adversarial environments

**Small-World Networks (Watts-Strogatz, Random Geometric):**

- Moderate vulnerability: Centrality attacks most effective (targets shortcuts/bridges between clusters)
- Degree-based attacks less effective than centrality-based
- **Implication:** Good balance for spatial/clustered deployments

**Random Networks (Erdős-Rényi):**

- Highest resilience: All attack strategies perform similarly (homogeneous structure)
- No exploitable structural weaknesses
- **Implication:** Best for environments with sophisticated attackers

### Visualizations

![Largest Connected Component Under Attack](plots/static_analysis_results/static_analysis_lcc_comparison.png)
*Figure 1: Network connectivity degradation under different attack strategies. Steeper slopes indicate higher vulnerability.*

![Algebraic Connectivity Under Attack](plots/static_analysis_results/static_analysis_algebraic_connectivity_comparison.png)
*Figure 2: Network cohesion metric. Faster decline indicates structural brittleness.*

---

## 2. Dynamic Analysis: Operational Resilience with Energy Depletion

### Overview

This analysis simulates realistic IoT operation over 3500 steps with:

- **Random node failures**: 2.5% probability every 40 steps (25 steps recovery time)
- **Energy depletion**: Nodes die when energy reaches zero (initial: 100, drain: 0.03/step)
- **Link instability**: 0.5% probability of 10-step link failures
- **Data routing**: Shortest-path packet delivery (2 packets/step/node)

**Expected energy lifetime**: ~3333 steps (100 / 0.03)

### Performance Metrics

| Network Model | Final DDR | Energy Lifetime | Performance |
| :--- | :--- | :--- | :--- |
| Random Geometric | 92.9% | 2783 steps | Excellent |
| Erdős-Rényi | 92.4% | 3094 steps (best) | Excellent |
| Watts-Strogatz | 92.2% | 2976 steps | Excellent |
| Barabási-Albert | 88.8% | 2101 steps | Good |
| Hierarchical | 56.9% | 1388 steps | Poor |

### Key Findings

**Energy-Based "Targeted Attacks" Emerge Naturally:**

1. **Erdős-Rényi (3094 steps)**: Longest lifetime due to uniform load distribution across all nodes
2. **Watts-Strogatz (2976 steps)**: Balanced traffic via clustering + shortcuts prevents hotspots
3. **Random Geometric (2783 steps)**: Spatial routing naturally distributes energy consumption
4. **Barabási-Albert (2101 steps)**: Hub nodes die 33% earlier from excessive traffic forwarding
5. **Hierarchical (1388 steps)**: Gateways die 55% earlier - all sensor traffic creates extreme hotspots

**Distributed vs. Centralized Topologies:**

| Aspect | Distributed (ER/WS/RGG) | Centralized (BA/Hierarchical) |
|--------|-------------------------|-------------------------------|
| **Final DDR** | 92-93% | 57-89% |
| **Energy Lifetime** | 2783-3094 steps | 1388-2101 steps |
| **Degradation Pattern** | Graceful decline | Catastrophic collapse |
| **Load Balancing** | Uniform across nodes | Hotspots at hubs/gateways |
| **Lifetime Extension** | Baseline | -33% to -55% penalty |

**Critical Insight - Hub Energy Exhaustion:**

- Scale-free networks suffer from natural load concentration
- High-degree nodes exhaust energy faster, creating cascading failures
- Energy depletion creates "targeted attack" effects without explicit adversary
- **BA hubs**: 37% network degradation (88.8% DDR)
- **Hierarchical gateways**: 43% network collapse (56.9% DDR)

### Visualizations

**Timeseries Analysis:**

![Network Connectivity Over Time](plots/dynamic_analysis_results/dynamic_lcc_overlay.png)
*Figure 3: LCC evolution over 3500 steps. All networks eventually collapse due to energy depletion, but distributed topologies maintain connectivity longer.*

![Active Nodes Over Time](plots/dynamic_analysis_results/dynamic_online_fraction_overlay.png)
*Figure 4: Node survival rates. Hierarchical gateways die first (1388 steps), BA hubs at 2101 steps, distributed networks survive ~3000 steps.*

![Data Delivery Performance](plots/dynamic_analysis_results/dynamic_ddr_cumulative_overlay.png)
*Figure 5: Packet delivery ratio throughout network lifetime. Hierarchical shows catastrophic 43% failure; distributed networks maintain 92%+ performance.*

**Performance Summaries:**

![Final DDR Comparison](plots/dynamic_analysis_results/dynamic_ddr_final_summary.png)
*Figure 6: Final data delivery ratio after 3500 steps. Color coding: green (>88%), orange (75-88%), red (<75%).*

![Energy Lifetime Comparison](plots/dynamic_analysis_results/dynamic_time_to_first_death_summary.png)
*Figure 7: Time to first node death. Color coding: green (>2700 steps), orange (2000-2700), red (<2000). Shows impact of load concentration.*

![Recovery Time Analysis](plots/dynamic_analysis_results/dynamic_ttr_mean_summary.png)
*Figure 8: Time to recover from disruptions (when LCC drops >5%). Lower is better.*

![Network Collapse Timing](plots/dynamic_analysis_results/dynamic_time_to_lcc_collapse_summary.png)
*Figure 9: When LCC first drops below 50% of initial size. All networks eventually collapse from energy depletion.

---

## 3. Comparative Analysis & Recommendations

### Static vs. Dynamic Vulnerability

| Network Model | Attack Resilience | Operational Performance | Energy Lifetime | Overall Grade |
|---------------|-------------------|-------------------------|-----------------|---------------|
| **Erdős-Rényi** | Best (32% nodes) | Excellent (92.4% DDR) | Best (3094 steps) | **A+** |
| **Watts-Strogatz** | Good (17% nodes) | Excellent (92.2% DDR) | Good (2976 steps) | **A** |
| **Random Geometric** | Good (16% nodes) | Excellent (92.9% DDR) | Good (2783 steps) | **A** |
| **Barabási-Albert** | Poor (6% nodes) | Good (88.8% DDR) | Poor (2101 steps) | **C** |
| **Hierarchical** | Critical (3.3% nodes) | Poor (56.9% DDR) | Critical (1388 steps) | **F** |

### Design Recommendations

**For High-Security IoT Deployments:**

- **Erdős-Rényi**: Best all-around choice - resistant to attacks, excellent operational performance, longest energy lifetime
- **Use case**: Critical infrastructure, defense systems, financial networks

**For High-Reliability IoT with Spatial Constraints:**

- **Watts-Strogatz**: Excellent clustering + shortcuts, moderate attack resistance, good energy efficiency
- **Random Geometric**: Natural for geographic deployment, strong operational performance
- **Use case**: Smart cities, environmental monitoring, logistics

**Avoid for Critical Systems:**

- **Barabási-Albert**: Vulnerable to targeted attacks AND hub energy exhaustion - dual failure modes
- **Hierarchical**: Catastrophic on all metrics - only use if strict manageability requirements override resilience

**Mitigation Strategies for Centralized Topologies:**

If Hierarchical/BA required for management simplicity:

1. **Gateway redundancy**: Multiple gateways per sensor cluster (2-3× redundancy)
2. **Multi-parent connections**: Sensors connect to 2-3 gateways for failover
3. **Inter-gateway mesh**: Connect gateways in distributed topology (ER/WS)
4. **Energy balancing**: Rotate gateway roles or provide differential battery capacity
5. **Hybrid topology**: Core mesh (ER/WS) with hierarchical edge clusters
