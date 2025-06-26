import os
import pickle
import json
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from slugify import slugify

NEIGHBORHOOD_DIR = "resources/neighborhoods"
OUTPUT_PATH = "resources/unified/graph_without_snow.png"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def render_unified_without_snow():
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

            # Plot drone path in red
            coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_nodes if n in G.nodes]
            if coords:
                lats, lons = zip(*coords)
                ax.plot(lons, lats, color='red', linewidth=1.5, alpha=0.7)

        except Exception as e:
            print(f"⚠️ Skipping {name} due to error: {e}")

    ax.set_title("Unified Drone Path – No Snow Overlay")
    ax.axis("off")
    plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    render_unified_without_snow()

