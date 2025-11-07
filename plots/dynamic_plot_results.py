import argparse
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from config import DYNAMIC_SIMULATION_CONFIG


def ci95(series: pd.Series) -> float:
    n = series.count()
    if n <= 1:
        return 0.0
    return 1.96 * series.std(ddof=1) / np.sqrt(n)


def plot_timeseries(df: pd.DataFrame, metric: str, save: bool, output: str):
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in time series data. Available: {
                        list(df.columns)}")

    # Coerce and sanitize metric column
    df = df.copy()
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    df.loc[~np.isfinite(df[metric]), metric] = np.nan

    sns.set_style("whitegrid")
    models = df['model_name'].unique()
    n_models = len(models)

    fig, axes = plt.subplots(
        1, n_models, figsize=(7 * n_models, 5), sharey=False)
    if n_models == 1:
        axes = [axes]

    for ax, model_name in zip(axes, models):
        sub = df[df['model_name'] == model_name]
        agg = sub.groupby('time')[metric].agg(['mean', ci95]).reset_index()
        # Clean NaNs/Infs for plotting
        agg = agg.replace([np.inf, -np.inf], np.nan)
        agg['ci95'] = np.nan_to_num(agg['ci95'].to_numpy(), nan=0.0)
        agg = agg.dropna(subset=['mean'])
        if agg.empty:
            ax.set_title(model_name + " (no data)")
            continue
        ax.plot(agg['time'], agg['mean'], label=f"Mean {metric}")
        ax.fill_between(agg['time'], agg['mean'] - agg['ci95'],
                        agg['mean'] + agg['ci95'], alpha=0.2)
        ax.set_title(model_name)
        ax.set_xlabel('Time')
        ax.set_ylabel(metric.replace('_', ' ').title())

    fig.suptitle(f"Dynamic {metric.replace(
        '_', ' ').title()} Over Time (Mean ± 95% CI)")
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))

    if save:
        out_dir = "plots/dynamic_analysis_results"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, output)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved time series plot to {path}")
        plt.close()
    else:
        plt.show()


def plot_summary(df: pd.DataFrame, metric: str, save: bool, output: str):
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in summary data. Available: {list(df.columns)}")

    sns.set_style("whitegrid")

    # Sanitize metric: coerce to numeric
    df = df.copy()
    df[metric] = pd.to_numeric(df[metric], errors='coerce')

    # Map infinite times (no event within horizon) to the simulation length for visibility
    horizon = float(DYNAMIC_SIMULATION_CONFIG.get('steps', 1000))
    if metric in ('time_to_first_death', 'time_to_lcc_collapse'):
        df.loc[np.isposinf(df[metric]), metric] = horizon
        df.loc[np.isneginf(df[metric]), metric] = np.nan

    # Drop remaining non-finite
    df.loc[~np.isfinite(df[metric]), metric] = np.nan

    # Compute mean and CI vectorized (NaNs ignored)
    grp = df.groupby('model_name')[metric]
    mean = grp.mean()
    count = grp.count().astype(float)
    std = grp.std(ddof=1)
    with np.errstate(invalid='ignore', divide='ignore'):
        ci = 1.96 * (std / np.sqrt(count))

    agg = pd.DataFrame({
        'model_name': mean.index,
        'mean': mean.values,
        'ci95': np.nan_to_num(ci.values, nan=0.0, posinf=0.0, neginf=0.0)
    })

    # Drop rows with no mean (all-NaN in that model)
    agg = agg.replace([np.inf, -np.inf], np.nan).dropna(subset=['mean'])
    
    # Sort by mean value for better visual comparison (descending for most metrics)
    if metric in ('time_to_first_death', 'time_to_lcc_collapse'):
        # Higher is better (survived longer)
        agg = agg.sort_values('mean', ascending=False)
    else:
        # For DDR, higher is better; for TTR, lower is better
        agg = agg.sort_values('mean', ascending=(metric == 'ttr_mean'))

    plt.figure(figsize=(10, 6))

    if agg.empty:
        plt.text(0.5, 0.5, 'No data available for this metric',
                ha='center', va='center', fontsize=14)
        plt.title(f"Dynamic Summary: {metric.replace('_', ' ').title()}", fontsize=16)
        plt.axis('off')
    else:
        # Create bar chart with color gradient
        x = np.arange(len(agg))
        heights = agg['mean'].to_numpy()
        yerr = agg['ci95'].to_numpy()
        
        # Color bars based on performance (green=good, orange=warning, red=poor)
        # Updated thresholds for 3500-step simulation with energy depletion
        if metric == 'ddr_final':
            # With energy depletion: 56.9% (Hierarchical) to 92.9% (RGG)
            # Red < 75%, Orange < 88%, Green ≥ 88%
            colors = ['#d62728' if h < 0.75 else '#ff7f0e' if h < 0.88 else '#2ca02c' for h in heights]
        elif metric == 'ttr_mean':
            colors = ['#2ca02c' if h < 0.1 else '#ff7f0e' if h < 0.5 else '#d62728' for h in heights]
        elif metric == 'time_to_first_death':
            # Energy lifetime: 1388 (Hierarchical) to 3094 (ER)
            # Red < 2000 steps, Orange < 2700 steps, Green ≥ 2700 steps
            colors = ['#d62728' if h < 2000 else '#ff7f0e' if h < 2700 else '#2ca02c' for h in heights]
        elif metric == 'time_to_lcc_collapse':
            # All models collapse eventually due to energy depletion
            # Use horizon-based thresholds (earlier collapse = worse)
            colors = ['#d62728' if h < horizon * 0.8 else '#ff7f0e' if h < horizon * 0.95 else '#2ca02c' for h in heights]
        else:
            colors = '#1f77b4'  # Default blue

        bars = plt.bar(x, heights, yerr=yerr, capsize=5, alpha=0.8, 
                      color=colors, edgecolor='black', linewidth=1.2)
        
        # Add value labels on top of bars
        for i, (bar, height, err) in enumerate(zip(bars, heights, yerr)):
            label_height = height + err + (max(heights) * 0.02)
            if metric == 'ddr_final':
                label = f'{height:.4f}'
            elif metric == 'ttr_mean':
                label = f'{height:.2f}'
            else:
                label = f'{int(height)}'
            plt.text(bar.get_x() + bar.get_width()/2., label_height,
                    label, ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.xticks(x, agg['model_name'], rotation=15, ha='right', fontsize=11)
        plt.xlabel('Network Model', fontsize=12, fontweight='bold')
        plt.ylabel(metric.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        
        title = f"{metric.replace('_', ' ').title()}"
        if metric in ('time_to_first_death', 'time_to_lcc_collapse'):
            title += f"\n(Horizon = {int(horizon)} steps; no event runs shown at horizon)"
        plt.title(title, fontsize=14, fontweight='bold', pad=15)
        
        # Add grid for easier reading
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.tight_layout()

    if save:
        out_dir = "plots/dynamic_analysis_results"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, output)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved summary plot to {path}")
        plt.close()
    else:
        plt.show()


# -----------------------------
# New: distribution visualization for per-run summary metrics
# -----------------------------

def plot_distribution(df: pd.DataFrame, metric: str, save: bool, output: str, style: str = 'violin', log_y: bool = False):
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not in summary data. Available: {
                        list(df.columns)}")
    sns.set_style("whitegrid")
    df = df.copy()
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    horizon = float(DYNAMIC_SIMULATION_CONFIG.get('steps', 1000))
    censored_mask = np.isposinf(df[metric])
    if metric in ('time_to_first_death', 'time_to_lcc_collapse', 'ttr_mean', 'ttr_median'):
        # Treat +inf as censored at horizon
        df.loc[censored_mask, metric] = horizon
    df = df[np.isfinite(df[metric])]
    if df.empty:
        plt.figure(figsize=(8, 4))
        plt.text(0.5, 0.5, 'No finite data', ha='center', va='center')
        plt.title(f"Distribution: {metric}")
        if save:
            out_dir = "plots/dynamic_analysis_results"
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, output)
            plt.savefig(path, dpi=300, bbox_inches='tight')
            print(f"Saved distribution plot to {path}")
            plt.close()
        else:
            plt.show()
        return
    plt.figure(figsize=(10, 5))
    order = df.groupby('model_name')[metric].median().sort_values().index
    if style == 'violin':
        sns.violinplot(data=df, x='model_name', y=metric,
                    order=order, inner=None, cut=0)
    else:
        sns.boxplot(data=df, x='model_name', y=metric, order=order)
    # jittered points
    sns.stripplot(data=df, x='model_name', y=metric,
                order=order, color='k', alpha=0.35, size=3)
    # Means with CI
    means = df.groupby('model_name')[metric].mean()
    cis = df.groupby('model_name')[metric].apply(ci95)
    x_positions = {name: i for i, name in enumerate(order)}
    for name in order:
        m = means[name]
        c = cis[name]
        plt.errorbar(x_positions[name], m, yerr=c,
                    fmt='o', color='red', capsize=3)
    plt.xlabel('Model')
    plt.ylabel(metric.replace('_', ' ').title())
    title = f"Distribution of {metric.replace('_', ' ').title()} per Run"
    if metric in ('time_to_first_death', 'time_to_lcc_collapse', 'ttr_mean', 'ttr_median'):
        censored_counts = df.groupby('model_name')[metric].apply(
            lambda s: (s >= horizon).sum())
        total_counts = df.groupby('model_name')[metric].count()
        annot = ", ".join(f"{m}: cens {censored_counts.get(
            m, 0)}/{total_counts.get(m, 0)}" for m in order)
        title += f"\n(Horizon={int(horizon)}; {annot})"
    plt.title(title)
    plt.xticks(rotation=20, ha='right')
    if log_y:
        plt.yscale('log')
    plt.tight_layout()
    if save:
        out_dir = "plots/dynamic_analysis_results"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, output)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved distribution plot to {path}")
        plt.close()
    else:
        plt.show()


# -----------------------------
# New: Kaplan-Meier survival for time metrics
# -----------------------------

def km_curve(times: np.ndarray, censored: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # times: observed (event or censor) times; censored: bool True if censored
    # Returns stepwise x (including 0) and survival probabilities
    order = np.argsort(times)
    times = times[order]
    censored = censored[order]
    unique_event_times = np.unique(times[~censored])
    if unique_event_times.size == 0:
        return np.array([0.0, times.max()]), np.array([1.0, 1.0])
    surv_times = [0.0]
    surv_probs = [1.0]
    for t in unique_event_times:
        d = ((times == t) & (~censored)).sum()
        at_risk = (times >= t).sum()
        if at_risk == 0:
            continue
        last_prob = surv_probs[-1] * (1 - d / at_risk)
        surv_times.extend([t])
        surv_probs.extend([last_prob])
    # Extend to max time
    max_t = times.max()
    if surv_times[-1] != max_t:
        surv_times.append(max_t)
        surv_probs.append(surv_probs[-1])
    return np.array(surv_times), np.array(surv_probs)


def plot_survival(df: pd.DataFrame, metric: str, save: bool, output: str):
    if metric not in ('time_to_first_death', 'time_to_lcc_collapse'):
        raise ValueError(
            "Survival plots only supported for 'time_to_first_death' or 'time_to_lcc_collapse'.")
    sns.set_style('whitegrid')
    df = df.copy()
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    horizon = float(DYNAMIC_SIMULATION_CONFIG.get('steps', 1000))
    # Identify censoring: +inf means no event
    censored = np.isposinf(df[metric])
    df.loc[censored, metric] = horizon
    models = sorted(df['model_name'].unique())
    plt.figure(figsize=(9, 5))
    for model in models:
        sub = df[df['model_name'] == model]
        times = sub[metric].to_numpy()
        cens = np.isclose(times, horizon) & (
            sub[metric].notna()) & (sub[metric] == horizon)
        # However, differentiate true horizon due to censor vs event at horizon (rare). Original censor mask may track.
        # We'll mark those originally infinite as censored.
        cens = cens | censored[sub.index]
        x, y = km_curve(times.astype(float), cens)
        plt.step(x, y, where='post', label=model)
    plt.xlabel('Time')
    plt.ylabel('Survival Probability')
    pretty = metric.replace('_', ' ').title()
    plt.title(f"Kaplan-Meier Survival: Time to {pretty.split(
        'Time To ')[-1]}\n(Horizon={int(horizon)}; Censor=No Event)")
    plt.ylim(0, 1.05)
    plt.legend(title='Model')
    plt.tight_layout()
    if save:
        out_dir = "plots/dynamic_analysis_results"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, output)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved survival plot to {path}")
        plt.close()
    else:
        plt.show()


def plot_timeseries_overlay(df: pd.DataFrame, metric: str, save: bool, output: str):
    """Create a single plot with all models overlaid for easier comparison."""
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in time series data. Available: {list(df.columns)}")

    df = df.copy()
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    df.loc[~np.isfinite(df[metric]), metric] = np.nan

    sns.set_style("whitegrid")
    models = sorted(df['model_name'].unique())
    
    plt.figure(figsize=(12, 6))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(models)))
    
    for idx, model_name in enumerate(models):
        sub = df[df['model_name'] == model_name]
        agg = sub.groupby('time')[metric].agg(['mean', ci95]).reset_index()
        agg = agg.replace([np.inf, -np.inf], np.nan)
        agg['ci95'] = np.nan_to_num(agg['ci95'].to_numpy(), nan=0.0)
        agg = agg.dropna(subset=['mean'])
        
        if not agg.empty:
            plt.plot(agg['time'], agg['mean'], label=model_name, 
                    color=colors[idx], linewidth=2, alpha=0.8)
            plt.fill_between(agg['time'], agg['mean'] - agg['ci95'],
                        agg['mean'] + agg['ci95'], alpha=0.15, color=colors[idx])
    
    plt.xlabel('Time Step', fontsize=12)
    plt.ylabel(metric.replace('_', ' ').title(), fontsize=12)
    plt.title(f"Dynamic {metric.replace('_', ' ').title()} Over Time (All Models)", fontsize=14, pad=15)
    plt.legend(loc='best', framealpha=0.9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save:
        out_dir = "plots/dynamic_analysis_results"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, output)
        plt.savefig(path, dpi=300, bbox_inches='tight')
        print(f"Saved overlay time series plot to {path}")
        plt.close()
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Plot dynamic simulation results.")
    parser.add_argument('--plot', choices=['timeseries', 'summary', 'timeseries-overlay'],
                        default='timeseries', help='Type of plot to generate.')
    parser.add_argument('--metric', type=str, default='lcc',
                        help="Timeseries metric (e.g., 'lcc', 'ddr_cumulative', 'online_fraction', 'algebraic_connectivity').")
    parser.add_argument('--summary-metric', type=str, default='ddr_final',
                        help="Summary metric (e.g., 'ddr_final', 'ttr_mean', 'time_to_first_death', 'time_to_lcc_collapse').")
    parser.add_argument('--save', action='store_true',
                        help='Save the plot instead of showing it.')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Output filename when using --save.')
    args = parser.parse_args()

    ts_file = DYNAMIC_SIMULATION_CONFIG.get(
        'timeseries_filename', 'csv/operational_simulation_timeseries.csv')
    sm_file = DYNAMIC_SIMULATION_CONFIG.get(
        'summary_filename', 'csv/operational_simulation_summary.csv')

    if args.plot == 'timeseries':
        if not os.path.exists(ts_file):
            print(f"Error: time series file '{ts_file}' not found. Run the dynamic simulation first.")
            return
        df_ts = pd.read_csv(ts_file)
        output = args.output or f"dynamic_{args.metric}_timeseries.png"
        plot_timeseries(df_ts, args.metric, args.save, output)
    elif args.plot == 'timeseries-overlay':
        if not os.path.exists(ts_file):
            print(f"Error: time series file '{ts_file}' not found. Run the dynamic simulation first.")
            return
        df_ts = pd.read_csv(ts_file)
        output = args.output or f"dynamic_{args.metric}_overlay.png"
        plot_timeseries_overlay(df_ts, args.metric, args.save, output)
    else:
        if not os.path.exists(sm_file):
            print(f"Error: summary file '{sm_file}' not found. Run the dynamic simulation first.")
            return
        df_sm = pd.read_csv(sm_file)
        output = args.output or f"dynamic_{args.summary_metric}_summary.png"
        plot_summary(df_sm, args.summary_metric, args.save, output)


if __name__ == '__main__':
    main()
