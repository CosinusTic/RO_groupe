import json
from collections import defaultdict
from statistics import mean
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

REFERENCE_SNOW_CLEARED = 500

UNITS = {
    'steps_taken': 'steps',
    'fuel_used': 'cl',
    'distance_km': 'km',
    'time_h': 'min',
    'cost_total': '€'
}

EXCLUDED_KEYS = {'fuel_capacity', 'vehicle_type', 'path_length', 'ended_at', 'coverage_pct', 'node_visit_pct','snow_cleared'}

def load_data(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def average_by_vehicle_type(data):
    grouped = defaultdict(list)
    for entry in data:
        vehicle_type = entry['vehicle']
        grouped[vehicle_type].append(entry['stats'])

    averages = {}
    for vehicle_type, stats_list in grouped.items():
        averages[vehicle_type] = {}
        keys = stats_list[0].keys()
        for key in keys:
            if isinstance(stats_list[0][key], (int, float)):
                values = [s[key] for s in stats_list]
                averages[vehicle_type][key] = mean(values)
    return averages

def normalize_by_snow(averages, reference):
    normalized = {}
    for vehicle_type, stats in averages.items():
        if 'fuel_used' in stats and stats['fuel_used'] > 50000:
            stats['fuel_used'] -= 50000

        if 'fuel_used' in stats:
            stats['fuel_used'] *= 100

        if 'time_h' in stats:
            stats['time_h'] *= 60

        factor = reference / stats['snow_cleared'] if stats['snow_cleared'] != 0 else 0
        normalized[vehicle_type] = {
            key: (val * factor if key != 'snow_cleared' else reference)
            for key, val in stats.items()
            if isinstance(val, (int, float))
        }
    return normalized


def create_dataframe_for_plot(normalized):
    rows = []
    for vehicle_type, stats in normalized.items():
        for key, val in stats.items():
            if key not in EXCLUDED_KEYS:
                label = f"{key} ({UNITS.get(key, '')})"
                rows.append({
                    "Metric": label,
                    "Vehicle Type": vehicle_type,
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
        hue="Vehicle Type",
        palette="Set2"
    )

    ax.set_title("Normalized Vehicle Metrics (Snow Cleared = 500 edge)", fontsize=14)
    ax.set_ylabel("Normalized Value")
    ax.set_xlabel("Metric")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.legend(title="Vehicle Type")
    plt.show()

def main():
    json_file = '../all_runs.json'
    data = load_data(json_file)

    averages = average_by_vehicle_type(data)
    normalized = normalize_by_snow(averages, REFERENCE_SNOW_CLEARED)

    df = create_dataframe_for_plot(normalized)
    plot_histogram(df)

if __name__ == "__main__":
    main()
