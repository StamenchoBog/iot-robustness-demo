# Static Resilience Analysis: Results
## Plots

- LCC comparison: static_analysis_lcc_comparison.png
- Algebraic connectivity comparison: static_analysis_algebraic_connectivity_comparison.png
- Smoothness comparison: static_analysis_smoothness_comparison.png

![LCC](static_analysis_results/static_analysis_lcc_comparison.png)
![Algebraic Connectivity](static_analysis_results/static_analysis_algebraic_connectivity_comparison.png)
![Smoothness](static_analysis_results/static_analysis_smoothness_comparison.png)

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

### Summary Table

| Network Model | Resilience to Random Failures | Most Effective Targeted Attack | Key Structural Reason |
| :--- | :--- | :--- | :--- |
| Hierarchical | Very High | Degree / Centrality (Identical) | Centralized single points of failure. |
| Barabási-Albert | High | Degree / Centrality (Identical) | Hubs are also the main bridges. |
| Watts-Strogatz | Moderate | Centrality | Attacks the critical "shortcut" nodes between clusters. |
| Random Geometric | Moderate | Centrality | Attacks the critical "bridge" nodes between geographic regions. |
| Erdős-Rényi | Moderate | (Similar) | Lacks exploitable structure. |

# Dynamic Resilience Analysis: Results
