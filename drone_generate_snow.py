import pickle
import random
import csv
import os
import networkx as nx

input_graph = "resources/eulerized_montreal_graph.pkl"
output_csv = "resources/snow_map.csv"

# Load Eulerized Graph
with open(input_graph, "rb") as f:
    G = pickle.load(f)

# Create output directory if needed
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

# Simulate snow detection
snow_data = []
for u, v in G.edges():
    # Simulate snow coverage: 30% of edges affected by snow
    snow = int(random.random() < 0.3)
    snow_data.append((u, v, snow))

# Save to CSV
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["u", "v", "snow"])
    writer.writerows(snow_data)

print(f"Simulated snow detection saved to: {output_csv}")

