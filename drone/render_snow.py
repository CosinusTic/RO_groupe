import os
import pickle
import json
import csv
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from slugify import slugify

NEIGHBORHOOD_DIR = "resources/neighborhoods"
OUTPUT_DIR = "resources/graphical_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def apply_snow_from_csv(G: nx.Graph, csv_path: str) -> nx.Graph:
    """Apply snow data from CSV to the graph by setting edge['snow'] = True"""
    is_multigraph = G.is_multigraph()

    # Reset snow status
    if is_multigraph:
        for u, v, k in G.edges(keys=True):
            G[u][v][k]['snow'] = False
    else:
        for u, v in G.edges():
            G[u][v]['snow'] = False

    # Parse CSV and apply snow
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                u, v, snow = int(row["u"]), int(row["v"]), int(row["snow"])
                if snow == 1:
                    if is_multigraph:
                        if G.has_edge(u, v):
                            for k in G[u][v]:
                                G[u][v][k]['snow'] = True
                        elif G.has_edge(v, u):
                            for k in G[v][u]:
                                G[v][u][k]['snow'] = True
                    else:
                        if G.has_edge(u, v):
                            G[u][v]['snow'] = True
                        elif G.has_edge(v, u):
                            G[v][u]['snow'] = True
            except Exception as e:
                print(f"⚠️ Skipping malformed row in snow CSV: {row} ({e})")
    return G

def render_neighborhood_with_snow(neigh_path):
    slug = os.path.basename(neigh_path)
    print(f"🎨 Rendering {slug}...")

    try:
        # Load Eulerized graph
        graph_path = os.path.join(neigh_path, "eulerized_graph.pkl")
        with open(graph_path, "rb") as f:
            G = pickle.load(f)

        # Load Eulerian path
        path_json = os.path.join(neigh_path, "eulerian_path.json")
        with open(path_json) as f:
            path = json.load(f)
        path_nodes = [edge["u"] for edge in path] + [path[-1]["v"]]

        # Load and apply snow CSV
        snow_path = os.path.join(neigh_path, "snow_map.csv")
        if os.path.isfile(snow_path):
            print(f"📄 Found snow map: {snow_path}")
            with open(snow_path) as f:
                print("📄 Sample snow_map.csv rows:", [next(f).strip() for _ in range(3)])
            G = apply_snow_from_csv(G, snow_path)
        else:
            print(f"⚠️ No snow_map.csv found for {slug}, skipping snow.")

        # Plot base map
        fig, ax = ox.plot_graph(
            G,
            show=False, close=False,
            edge_color='lightgray',
            edge_linewidth=0.5,
            node_size=0,
            bgcolor='white'
        )

        # Plot snowy edges in blue
        snowy_count = 0
        if G.is_multigraph():
            for u, v, k in G.edges(keys=True):
                if G[u][v][k].get('snow', False):
                    snowy_count += 1
                    x = [G.nodes[u]['x'], G.nodes[v]['x']]
                    y = [G.nodes[u]['y'], G.nodes[v]['y']]
                    ax.plot(x, y, color='blue', linewidth=1.2, alpha=0.8)
        else:
            for u, v in G.edges():
                if G[u][v].get('snow', False):
                    snowy_count += 1
                    x = [G.nodes[u]['x'], G.nodes[v]['x']]
                    y = [G.nodes[u]['y'], G.nodes[v]['y']]
                    ax.plot(x, y, color='blue', linewidth=1.2, alpha=0.8)

        print(f"🔵 {slug}: Rendered {snowy_count} snowy edges.")

        # Plot drone path in red
        valid_coords = [
            (G.nodes[n]['y'], G.nodes[n]['x'])
            for n in path_nodes
            if n in G.nodes and 'x' in G.nodes[n] and 'y' in G.nodes[n]
        ]
        if valid_coords:
            lats, lons = zip(*valid_coords)
            ax.plot(lons, lats, color='red', linewidth=1.5, alpha=0.7)

        ax.set_title(f"{slug.replace('-', ' ').title()}", fontsize=10)
        out_path = os.path.join(OUTPUT_DIR, f"{slug}.png")
        plt.savefig(out_path, dpi=300)
        plt.close()
        print(f"✅ Saved to {out_path}")

    except Exception as e:
        print(f"❌ Error rendering {slug}: {e}")

if __name__ == "__main__":
    for name in os.listdir(NEIGHBORHOOD_DIR):
        path = os.path.join(NEIGHBORHOOD_DIR, name)
        if os.path.isdir(path):
            render_neighborhood_with_snow(path)

    print("🎯 All neighborhood maps generated.")

