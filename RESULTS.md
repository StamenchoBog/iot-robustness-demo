# Static Resilience Analysis: Results

## Plots

![LCC](plots/static_analysis_results/static_analysis_lcc_comparison.png)
![Algebraic Connectivity](plots/static_analysis_results/static_analysis_algebraic_connectivity_comparison.png)

---

### Quantitative Resilience Metrics

**Time to 50% LCC Loss (Targeted Degree Attack):**

| Network Model | Nodes to 50% Loss | % of Total Nodes |
| :--- | :--- | :--- |
| Hierarchical | 10 | 3.3% |
| Barabási-Albert | 18 | 6% |
| Watts-Strogatz | 52 | 17% |
| Random Geometric | 48 | 16% |
| Erdős-Rényi | 95 | 32% |

**Vulnerability Index** (lower = more resilient):

| Network Model | Vulnerability Index |
| :--- | :--- |
| Hierarchical | 0.033 |
| Barabási-Albert | 0.060 |
| Watts-Strogatz | 0.173 |
| Random Geometric | 0.160 |
| Erdős-Rényi | 0.317 |
---

## Findings

### Barabási-Albert & Hierarchical Networks

- Observation: Targeted Degree and Targeted Centrality attacks are nearly identical and cause rapid collapse.
- Interpretation: Hubs/gateways are also key bridges; both strategies target the same critical nodes.

### Erdős-Rényi Network

- Observation: All three strategies behave similarly.
- Interpretation: The network is homogeneous; intelligent targeting offers little advantage.

### Watts-Strogatz & Random Geometric Networks

- Observation: Centrality-based attacks are most damaging, then degree-based, then random.
- Interpretation: High-centrality nodes form shortcuts/bridges across clusters or geographic regions.

---

> [!NOTE]
>
> Below we can view the summary table as a conclusion to the static analysis experiment.
>
> ### Summary Table
>
> | Network Model | Resilience to Random Failures | Most Effective Targeted Attack | Key Structural Reason |
> | :--- | :--- | :--- | :--- |
> | Hierarchical | Very High | Degree / Centrality (Identical) | Centralized single points of failure. |
> | Barabási-Albert | High | Degree / Centrality (Identical) | Hubs are also the main bridges. |
> | Watts-Strogatz | Moderate | Centrality | Attacks the critical "shortcut" nodes between clusters. |
> | Random Geometric | Moderate | Centrality | Attacks the critical "bridge" nodes between geographic regions. |
> | Erdős-Rényi | Moderate | (Similar) | Lacks exploitable structure. |
>

# Dynamic Resilience Analysis: Results
