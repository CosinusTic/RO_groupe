#!/usr/bin/env python3
# simulation_drone.py
# ------------------------------------------------------------
# Évaluation “coût drone” : un seul engin, pas de carburant,
# juste coût fixe + coût par kilomètre parcouru.
# ------------------------------------------------------------
import os
import json
import pickle
import csv
import networkx as nx

# ---------------------  PARAMÈTRES DRONE  --------------------
DRONE_FIXED_COST = 1_000        # € par mission
DRONE_COST_PER_KM = 0.50        # € / km

# ------------------  UTILITAIRES GÉNÉRIQUES  -----------------
def prompt_for_neighborhood() -> str:
    root_dir = "resources/"
    hoods = [n for n in os.listdir(root_dir)
             if os.path.isdir(os.path.join(root_dir, n))]
    print("\n📍 Available neighborhoods:")
    for i, h in enumerate(hoods, 1):
        print(f"{i}. {h}")
    while True:
        try:
            c = int(input("Choose a neighborhood (number): "))
            if 1 <= c <= len(hoods):
                return hoods[c-1]
        except ValueError:
            pass
        print("❌ Invalid input. Please enter a valid number.")

def load_graph(path: str) -> nx.MultiGraph:
    with open(path, "rb") as f:
        return pickle.load(f)

# ------------------  CALCUL POSTIER CHINOIS  -----------------
def chinese_postman_distance(G: nx.MultiGraph, start) -> tuple[list[int], float]:
    """
    G est déjà eulérisé.  On renvoie la séquence des nœuds visités
    et la distance totale en kilomètres.
    """
    circuit = list(nx.eulerian_circuit(G, source=start))
    path_nodes = [start] + [v for _, v in circuit]          # liste ordonnée de nœuds

    dist_m = 0.0
    for u, v in circuit:
        # MultiGraph : on prend la première clé
        data = G[u][v][0] if isinstance(G[u][v], dict) else G[u][v]
        dist_m += data.get("length", 1.0)

    dist_km = dist_m / 1_000          # conversion (OSM → mètres)
    return path_nodes, dist_km

# ---------------------------  MAIN  --------------------------
def main():
    hood = prompt_for_neighborhood()
    hood_dir = os.path.join("resources", hood)
    graph_path = os.path.join(hood_dir, "eulerized_graph.pkl")

    print("📡 Chargement du graphe…")
    G = load_graph(graph_path)
    start_node = list(G.nodes())[0]

    print("🔄 Calcul du circuit eulérien…")
    path_nodes, dist_km = chinese_postman_distance(G, start_node)

    cost_total = DRONE_FIXED_COST + DRONE_COST_PER_KM * dist_km

    print("\n✅  Résultats drone")
    print(f"   ↳ Distance       : {dist_km:.2f} km")
    print(f"   ↳ Arêtes visitées: {len(G.edges())}")
    print(f"   ↳ Coût total     : {cost_total:.2f} €")

    # -----------  fichiers de sortie  -----------
    path_json = os.path.join(hood_dir, "drone_path.json")
    stats_json = os.path.join(hood_dir, "drone_stats.json")

    with open(path_json, "w") as f:
        json.dump(path_nodes, f)
    with open(stats_json, "w") as f:
        json.dump({
            "distance_km": round(dist_km, 2),
            "edges_traversed": len(G.edges()),
            "cost_total": round(cost_total, 2),
            "fixed_cost": DRONE_FIXED_COST,
            "variable_cost_per_km": DRONE_COST_PER_KM
        }, f, indent=2)

    print(f"\n📝  Fichiers écrits : {path_json}, {stats_json}")

if __name__ == "__main__":
    main()

