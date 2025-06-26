## import pickle
## import random
## import csv
## import os
## import networkx as nx
## 
## input_graph = "resources/eulerized_montreal_graph.pkl"
## output_csv = "resources/snow_map.csv"
## 
## # Load Eulerized Graph
## with open(input_graph, "rb") as f:
##     G = pickle.load(f)
## 
## # Create output directory if needed
## os.makedirs(os.path.dirname(output_csv), exist_ok=True)
## 
## # Simulate snow detection
## snow_data = []
## for u, v in G.edges():
##     # Simulate snow coverage: 30% of edges affected by snow
##     snow = int(random.random() < 0.3)
##     snow_data.append((u, v, snow))
## 
## # Save to CSV
## with open(output_csv, "w", newline="") as csvfile:
##     writer = csv.writer(csvfile)
##     writer.writerow(["u", "v", "snow"])
##     writer.writerows(snow_data)
## 
## print(f"Simulated snow detection saved to: {output_csv}")
## 

import pickle
import random
import csv
import os
import networkx as nx

NEIGHBORHOOD_DIR = "resources/neighborhoods"
SNOW_PROBABILITY = 0.3  # 30% chance an edge has snow

def simulate_snow_for_neighborhood(neigh_path):
    graph_path = os.path.join(neigh_path, "eulerized_graph.pkl")
    snow_map_path = os.path.join(neigh_path, "snow_map.csv")

    if not os.path.isfile(graph_path):
        print(f"❌ Missing graph: {graph_path}")
        return

    # Load graph
    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    # Simulate snow
    snow_data = []
    for u, v in G.edges():
        snow = int(random.random() < SNOW_PROBABILITY)
        snow_data.append((u, v, snow))

    # Save CSV
    with open(snow_map_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["u", "v", "snow"])
        writer.writerows(snow_data)

    print(f"✅ Snow map saved: {snow_map_path}")


if __name__ == "__main__":
    for name in os.listdir(NEIGHBORHOOD_DIR):
        full_path = os.path.join(NEIGHBORHOOD_DIR, name)
        if os.path.isdir(full_path):
            simulate_snow_for_neighborhood(full_path)

    print("🎯 Snow simulation completed for all neighborhoods.")

