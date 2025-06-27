import os
import json
import pickle
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

CITY_NAME = "Montréal, Québec, Canada"
OUTPUT_DIR = "resources/whole_city"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def shortest_path_length_safe(G, source, target):
    try:
        return nx.shortest_path_length(G, source, target, weight="length")
    except nx.NetworkXNoPath:
        return float("inf")

def compute_pair_distance(args):
    u, v, G = args
    dist = shortest_path_length_safe(G, u, v)
    return (u, v, dist)

def generate_city_eulerian_path():
    print(f"📡 Chargement du graphe de Montréal...")
    G = ox.graph_from_place(CITY_NAME, network_type='drive', simplify=True, retain_all=False)
    G_un = G.to_undirected()
    with open(os.path.join(OUTPUT_DIR, "raw_graph.pkl"), "wb") as f:
        pickle.dump(G_un, f)

    odd_nodes = [n for n, d in G_un.degree if d % 2 == 1]
    print(f"🔎 {len(odd_nodes)} nœuds de degré impair")

    print("🧮 Calcul des distances entre paires de nœuds impairs (multithread)...")
    pairs = list(combinations(odd_nodes, 2))
    args_list = [(u, v, G_un) for u, v in pairs]

    distances = {}
    with ThreadPoolExecutor() as executor:
        for u, v, dist in tqdm(executor.map(compute_pair_distance, args_list), total=len(args_list), desc="⏳ Progression"):
            if dist != float("inf"):
                distances[(u, v)] = dist

    print("⚖️ Résolution du couplage minimum parfait (matching)...")
    G_match = nx.Graph()
    for (u, v), dist in distances.items():
        G_match.add_edge(u, v, weight=dist)

    matching = nx.algorithms.matching.min_weight_matching(G_match, maxcardinality=True)
    print(f"✅ {len(matching)} paires appariées")

    # Création du graphe eulérien
    G_euler = G_un.copy()
    for u, v in matching:
        try:
            path = nx.shortest_path(G_un, source=u, target=v, weight="length")
            nx.add_path(G_euler, path)
        except nx.NetworkXNoPath:
            print(f"⚠️ Aucun chemin entre {u} et {v}, ignoré")

    with open(os.path.join(OUTPUT_DIR, "eulerized_graph.pkl"), "wb") as f:
        pickle.dump(G_euler, f)

    print("🧩 Calcul du circuit eulérien...")
    circuit = list(nx.eulerian_circuit(G_euler))
    path_json = [{"u": u, "v": v} for u, v in circuit]
    with open(os.path.join(OUTPUT_DIR, "eulerian_path.json"), "w") as f:
        json.dump(path_json, f, indent=2)

    path_nodes = [u for u, v in circuit] + [circuit[-1][1]]
    print("🎨 Génération du tracé PNG...")

    fig, ax = ox.plot_graph(
        G_un,
        show=False, close=False,
        edge_color='lightgray',
        node_size=0,
        bgcolor='white'
    )

    coords = [(G_un.nodes[n]['y'], G_un.nodes[n]['x']) for n in path_nodes if n in G_un.nodes and 'x' in G_un.nodes[n] and 'y' in G_un.nodes[n]]
    if coords:
        lats, lons = zip(*coords)
        ax.plot(lons, lats, color='red', linewidth=1.2, alpha=0.7)
        ax.set_title(f"Chemin eulérien – {CITY_NAME}", fontsize=10)
        plt.savefig(os.path.join(OUTPUT_DIR, "path_visualization.png"), dpi=300)
        plt.close()
        print("✅ Tracé enregistré")
    else:
        print("❌ Aucun point valide pour le tracé")

if __name__ == "__main__":
    generate_city_eulerian_path()
    print("✅ Traitement complet de la ville de Montréal.")
