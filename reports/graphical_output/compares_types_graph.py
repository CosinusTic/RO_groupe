import json
from collections import defaultdict
from statistics import mean
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

REFERENCE_SNOW_CLEARED = 500

UNITS = {
    'vehicles_used': '',
    'snow_cleared': 'units',
    'visited_nodes': 'nodes',
    'distance_km': 'km',
    'time_h': 'min',
    'cost_total': '€'
}

EXCLUDED_KEYS = {'snow_cleared'}

def load_data(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def average_by_strategy(data):
    grouped = defaultdict(list)
    for entry in data:
        strategy = entry['strategy']
        grouped[strategy].append(entry)

    averages = {}
    for strategy, entries in grouped.items():
        averages[strategy] = {}
        keys = entries[0].keys()
        for key in keys:
            if key in EXCLUDED_KEYS or not isinstance(entries[0][key], (int, float)):
                continue
            values = [e[key] for e in entries]
            averages[strategy][key] = mean(values)
        averages[strategy]['snow_cleared'] = mean([e['snow_cleared'] for e in entries])
    return averages

def normalize_by_snow(averages, reference):
    normalized = {}
    for strategy, stats in averages.items():
        factor = reference / stats['snow_cleared'] if stats['snow_cleared'] != 0 else 0

        normalized_stats = {}
        for key, val in stats.items():
            if key == 'snow_cleared':
                normalized_stats[key] = reference
            elif key == 'time_h':
                normalized_stats[key] = val * 60 * factor
            else:
                normalized_stats[key] = val * factor

        normalized[strategy] = normalized_stats
    return normalized

def create_dataframe_for_plot(normalized):
    rows = []
    for strategy, stats in normalized.items():
        for key, val in stats.items():
            if key in EXCLUDED_KEYS:
                continue
            label = f"{key} ({UNITS.get(key, '')})".strip()
            rows.append({
                "Metric": label,
                "Strategy": strategy,
                "Value": val
            })
    return pd.DataFrame(rows)

def plot_histogram(df):
    plt.figure(figsize=(12, 6))
    sns.set(style="whitegrid")

    ax = sns.barplot(
        data=df,
        x="Metric",
        y="Value",
        hue="Strategy",
        palette="Set2"
    )

    ax.set_title("Normalized Metrics by Strategy (Snow Cleared = 500 units)", fontsize=14)
    ax.set_ylabel("Normalized Value")
    ax.set_xlabel("Metric")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.legend(title="Strategy")
    plt.show()

def main():
    json_file = 'reports/all_runs.json'
    data = load_data(json_file)

    averages = average_by_strategy(data)
    normalized = normalize_by_snow(averages, REFERENCE_SNOW_CLEARED)

    df = create_dataframe_for_plot(normalized)
    plot_histogram(df)

if __name__ == "__main__":
    main()
