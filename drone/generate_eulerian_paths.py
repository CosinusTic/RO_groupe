import os
import json
import pickle
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from slugify import slugify

# List of boroughs
BOROUGHS = [
    "Plateau-Mont-Royal, Montréal, Québec, Canada",
    "Outremont, Montréal, Québec, Canada",
    "Verdun, Montréal, Québec, Canada",
    "Anjou, Montréal, Québec, Canada",
    "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada"
]

OUTPUT_DIR = "resources/neighborhoods"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_borough(place: str):
    slug = slugify(place.split(",")[0])  # short directory name
    borough_dir = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(borough_dir, exist_ok=True)

    print(f"[{slug}] Chargement du réseau routier...")
    G = ox.graph_from_place(place, network_type='drive', simplify=True, retain_all=False)
    G_un = G.to_undirected()

    # Save raw graph
    with open(os.path.join(borough_dir, "raw_graph.pkl"), "wb") as f:
        pickle.dump(G_un, f)

    # Eulerize
    odd_nodes = [n for n, d in G_un.degree if d % 2 == 1]
    print(f"[{slug}] {len(odd_nodes)} noeuds de degré impair")
    G_euler = nx.eulerize(G_un)

    # Save eulerized graph
    with open(os.path.join(borough_dir, "eulerized_graph.pkl"), "wb") as f:
        pickle.dump(G_euler, f)

    # Eulerian path
    circuit = list(nx.eulerian_circuit(G_euler))
    path_nodes = [u for u, v in circuit] + [circuit[-1][1]]

    # Save path to JSON
    path_json = [{"u": u, "v": v} for u, v in circuit]
    with open(os.path.join(borough_dir, "eulerian_path.json"), "w") as f:
        json.dump(path_json, f, indent=2)

    # Plot
    print(f"[{slug}] Génération du tracé PNG...")
    fig, ax = ox.plot_graph(
        G_un,
        show=False, close=False,
        edge_color='lightgray',
        node_size=0,
        bgcolor='white'
    )

    # coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_nodes]
    # lats, lons = zip(*coords)
    # ax.plot(lons, lats, color='red', linewidth=1.5, alpha=0.7)

    valid_coords = []
    missing_nodes = 0

    for n in path_nodes:
        if n in G.nodes and 'x' in G.nodes[n] and 'y' in G.nodes[n]:
            valid_coords.append((G.nodes[n]['y'], G.nodes[n]['x']))
        else:
            missing_nodes += 1

    if missing_nodes > 0:
        print(f"[{slug}] ❗ {missing_nodes} path nodes missing 'x','y' or not found in G.nodes")

    if valid_coords:
        lats, lons = zip(*valid_coords)
        ax.plot(lons, lats, color='red', linewidth=1.5, alpha=0.7)
        ax.set_title(f"Chemin eulérien – {place}", fontsize=10)

        # Optional zoom diagnostics
        print(f"[{slug}] Coord bounds:")
        print(f"  Lat range: {min(lats):.6f} → {max(lats):.6f}")
        print(f"  Lon range: {min(lons):.6f} → {max(lons):.6f}")
    else:
        print(f"[{slug}] ❌ No valid coordinates found to plot!")

    ax.set_title(f"Chemin eulérien – {place}", fontsize=10)

    plt.savefig(os.path.join(borough_dir, "path_visualization.png"), dpi=300)
    plt.close()
    print(f"[{slug}] ✔ Fini")

# Main parallel execution
if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.map(process_borough, BOROUGHS)

    print("✅ Tous les quartiers traités.")

