import os
import pickle
import json
import csv
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from slugify import slugify

NEIGHBORHOOD_DIR = "resources/neighborhoods"
OUTPUT_PATH = "resources/unified/graph_with_snow.png"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def apply_snow_from_csv(G, snow_csv):
    if G.is_multigraph():
        for u, v, k in G.edges(keys=True):
            G[u][v][k]["snow"] = False
    else:
        for u, v in G.edges():
            G[u][v]["snow"] = False

    with open(snow_csv, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                u, v, snow = int(row["u"]), int(row["v"]), int(row["snow"])
                if snow == 1:
                    if G.has_edge(u, v):
                        if G.is_multigraph():
                            for k in G[u][v]:
                                G[u][v][k]["snow"] = True
                        else:
                            G[u][v]["snow"] = True
                    elif G.has_edge(v, u):
                        if G.is_multigraph():
                            for k in G[v][u]:
                                G[v][u][k]["snow"] = True
                        else:
                            G[v][u]["snow"] = True
            except:
                pass
    return G

def render_unified_with_snow():
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_facecolor("white")

    for name in os.listdir(NEIGHBORHOOD_DIR):
        path = os.path.join(NEIGHBORHOOD_DIR, name)
        if not os.path.isdir(path):
            continue

        try:
            # Load graph
            with open(os.path.join(path, "eulerized_graph.pkl"), "rb") as f:
                G = pickle.load(f)

            # Load snow data
            snow_csv = os.path.join(path, "snow_map.csv")
            if os.path.exists(snow_csv):
                G = apply_snow_from_csv(G, snow_csv)

            # Load path
            with open(os.path.join(path, "eulerian_path.json")) as f:
                path_data = json.load(f)
            path_nodes = [edge["u"] for edge in path_data] + [path_data[-1]["v"]]

            # Plot roads in light gray
            for u, v in G.edges():
                if u in G.nodes and v in G.nodes:
                    x = [G.nodes[u]["x"], G.nodes[v]["x"]]
                    y = [G.nodes[u]["y"], G.nodes[v]["y"]]
                    ax.plot(x, y, color='lightgray', linewidth=0.5, alpha=0.5)

            # Plot snow in black
            if G.is_multigraph():
                for u, v, k in G.edges(keys=True):
                    if G[u][v][k].get("snow"):
                        x = [G.nodes[u]["x"], G.nodes[v]["x"]]
                        y = [G.nodes[u]["y"], G.nodes[v]["y"]]
                        ax.plot(x, y, color='black', linewidth=1.2, alpha=0.8)
            else:
                for u, v in G.edges():
                    if G[u][v].get("snow"):
                        x = [G.nodes[u]["x"], G.nodes[v]["x"]]
                        y = [G.nodes[u]["y"], G.nodes[v]["y"]]
                        ax.plot(x, y, color='black', linewidth=1.2, alpha=0.8)

            # Plot drone path in red
            coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_nodes if n in G.nodes]
            if coords:
                lats, lons = zip(*coords)
                ax.plot(lons, lats, color='red', linewidth=2.0, alpha=0.7)

        except Exception as e:
            print(f"⚠️ Skipping {name} due to error: {e}")

    ax.set_title("Unified Drone Path with Snow Overlay")
    ax.axis("off")
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    render_unified_with_snow()

