import json
from collections import defaultdict
from statistics import mean
from tabulate import tabulate

REFERENCE_SNOW_CLEARED = 500

UNITS = {
    'vehicles_used': '',
    'snow_cleared': 'edges',
    'visited_nodes': 'nodes',
    'distance_km': 'km',
    'time_h': 'h',
    'cost_total': '€'
}

EXCLUDED_KEYS = {
    'fuel_capacity', 'vehicle_type', 'path_length',
    'ended_at', 'coverage_pct', 'node_visit_pct'
}

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
                normalized_stats[key] = (val * factor) / 100
            elif key == 'distance_km':
                normalized_stats[key] = (val * factor) / 10
            else:
                normalized_stats[key] = val * factor
        normalized[strategy] = normalized_stats
    return normalized

def format_with_units(key, value):
    unit = UNITS.get(key, '')
    return f"{value:.2f} {unit}" if unit else f"{value:.2f}"

def main():
    json_file = 'reports/all_runs.json'
    data = load_data(json_file)
    averages = average_by_strategy(data)
    normalized = normalize_by_snow(averages, REFERENCE_SNOW_CLEARED)
    keys_to_display = sorted(
        {k for stats in normalized.values() for k in stats if k not in EXCLUDED_KEYS}
    )
    table = []
    for key in keys_to_display:
        row = [key]
        for strategy in sorted(normalized.keys()):
            val = normalized[strategy].get(key)
            row.append(format_with_units(key, val) if val is not None else '-')
        table.append(row)
    headers = ['Metric'] + sorted(normalized.keys())
    print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

if __name__ == "__main__":
    main()
