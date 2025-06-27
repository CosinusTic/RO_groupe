import json
from collections import defaultdict
from statistics import mean
from tabulate import tabulate

REFERENCE_SNOW_CLEARED = 500

UNITS = {
    'steps_taken': 'steps',
    'snow_cleared': 'edges',
    'fuel_used': 'L',
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
        # Ajustement du fuel_used
        if 'fuel_used' in stats and stats['fuel_used'] > 50000:
            stats['fuel_used'] -= 50000

        # Normalisation
        factor = reference / stats['snow_cleared'] if stats['snow_cleared'] != 0 else 0
        normalized[vehicle_type] = {
            key: (val * factor if key != 'snow_cleared' else reference)
            for key, val in stats.items()
            if isinstance(val, (int, float))
        }
    return normalized

def format_with_units(key, value):
    unit = UNITS.get(key, '')
    return f"{value:.2f} {unit}" if unit else f"{value:.2f}"

def main():
    json_file = '../../reports/all_runs.json'
    data = load_data(json_file)

    averages = average_by_vehicle_type(data)
    normalized = normalize_by_snow(averages, REFERENCE_SNOW_CLEARED)

    keys_to_display = sorted(
        {k for stats in normalized.values() for k in stats if k not in EXCLUDED_KEYS}
    )

    table = []
    for key in keys_to_display:
        row = [key]
        for vehicle_type in sorted(normalized.keys()):
            val = normalized[vehicle_type].get(key)
            row.append(format_with_units(key, val) if val is not None else '-')
        table.append(row)

    headers = ['Metric'] + sorted(normalized.keys())
    print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

if __name__ == "__main__":
    main()
