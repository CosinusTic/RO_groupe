import csv
import pickle
import networkx as nx
import os

GRAPH_PATH = "resources/eulerized_montreal_graph.pkl"
SNOW_MAP_CSV = "resources/snow_map.csv"
OUTPUT_SUBGRAPH = "resources/snowy_subgraph.graphml"

# Load the original graph
with open(GRAPH_PATH, "rb") as f:
    G = pickle.load(f)

# Read snow map CSV
snow_edges = set()
with open(SNOW_MAP_CSV, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["snow"] == "1":
            u, v = int(row["u"]), int(row["v"])
            if G.has_edge(u, v):
                snow_edges.add((u, v))
            elif G.has_edge(v, u):
                snow_edges.add((v, u))  # fallback if reversed

# Build plow subgraph
G_snow = nx.Graph()
for u, v in snow_edges:
    if G.has_edge(u, v):
        G_snow.add_edge(u, v, **G[u][v])

print(f"Subgraph has {G_snow.number_of_nodes()} nodes and {G_snow.number_of_edges()} edges.")
print("Is Eulerian:", nx.is_eulerian(G_snow))

# Save to GraphML
os.makedirs(os.path.dirname(OUTPUT_SUBGRAPH), exist_ok=True)
nx.write_graphml(G_snow, OUTPUT_SUBGRAPH)
print(f"Snowy subgraph saved to: {OUTPUT_SUBGRAPH}")

