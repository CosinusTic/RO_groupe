# import os
# import pickle
# import csv
# from noise import snoise2
# import networkx as nx
# import random
# import time
# 
# # Chemins spécifiques au quartier d'Anjou
# GRAPH_PATH = "resources/neighborhoods/anjou/eulerized_graph.pkl"
# SNOW_MAP_PATH = "resources/neighborhoods/snow_map.csv"
# 
# # Configuration réaliste aléatoire
# FREQ = 0.75        # Zones de neige plus grandes
# THRESHOLD = 0.075    # Seuil : + haut = neige plus rare mais plus nette
# OCTAVES = 4         # Complexité du bruit
# BASE = random.randint(0, 10000)  # seed aléatoire pour chaque exécution
# 
# def simulate_snow_city():
#     if not os.path.isfile(GRAPH_PATH):
#         print(f"❌ Graphe introuvable : {GRAPH_PATH}")
#         return
# 
#     with open(GRAPH_PATH, "rb") as f:
#         G = pickle.load(f)
# 
#     print(f"✔ Chargement du graphe ({len(G.edges())} arêtes)")
# 
#     # Extraire les coordonnées
#     lats = [G.nodes[n]['y'] for n in G.nodes if 'y' in G.nodes[n]]
#     lons = [G.nodes[n]['x'] for n in G.nodes if 'x' in G.nodes[n]]
#     min_lat, max_lat = min(lats), max(lats)
#     min_lon, max_lon = min(lons), max(lons)
# 
#     def normalize(val, min_val, max_val):
#         return (val - min_val) / (max_val - min_val)
# 
#     snow_data = []
#     print(f"🌨️ Simulation aléatoire des zones de neige (base={BASE})...")
# 
#     for u, v in G.edges():
#         try:
#             x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
#             x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
# 
#             # Calcul du point central (milieu de l’arête)
#             mx = normalize((x1 + x2) / 2, min_lon, max_lon)
#             my = normalize((y1 + y2) / 2, min_lat, max_lat)
# 
#             intensity = snoise2(mx / FREQ, my / FREQ, octaves=OCTAVES, base=BASE)
#             snow = int(intensity > THRESHOLD)
# 
#             snow_data.append((u, v, snow))
# 
#         except KeyError:
#             print(f"⚠️ Coordonnées manquantes pour arête ({u},{v}), ignorée")
# 
#     total = len(snow_data)
#     covered = sum(1 for _, _, s in snow_data if s == 1)
#     print(f"🧊 {covered} segments enneigés sur {total} ({(covered/total)*100:.1f} %)")
# 
#     os.makedirs(os.path.dirname(SNOW_MAP_PATH), exist_ok=True)
#     with open(SNOW_MAP_PATH, "w", newline="") as f:
#         writer = csv.writer(f)
#         writer.writerow(["u", "v", "snow"])
#         writer.writerows(snow_data)
# 
#     print(f"💾 Fichier exporté : {SNOW_MAP_PATH}")
# 
# if __name__ == "__main__":
#     simulate_snow_city()

#!/usr/bin/env python3
"""
Generate a Perlin-noise “snow_map.csv” for **each** neighborhood folder
under resources/.

For every edge (u,v) we write a line:  u,v,snow   where snow ∈ {0,1}
"""
import os, csv, pickle, random
from noise import snoise2

ROOT = "resources"                     # root that holds the borough dirs
FREQ = 0.75                            # ↑  bigger  → larger snow patches
THRESHOLD = 0.075                      # ↑  higher → rarer snow
OCTAVES   = 4

def normalise(val, lo, hi):
    return (val - lo) / (hi - lo) if hi > lo else 0.0

def simulate_for_folder(folder):
    g_pkl = os.path.join(folder, "eulerized_graph.pkl")
    if not os.path.isfile(g_pkl):
        return False

    G = pickle.load(open(g_pkl, "rb"))
    if not G.edges:
        return False

    lats = [d["y"] for _, d in G.nodes(data=True) if "y" in d]
    lons = [d["x"] for _, d in G.nodes(data=True) if "x" in d]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    base = random.randint(0, 9999)     # new seed per run / folder
    snow_rows, snowy = [], 0

    for u, v in G.edges():
        try:
            lat = (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2
            lon = (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2
        except KeyError:
            continue

        mx = normalise(lon, min_lon, max_lon) / FREQ
        my = normalise(lat, min_lat, max_lat) / FREQ
        intensity = snoise2(mx, my, octaves=OCTAVES, base=base)
        snow = int(intensity > THRESHOLD)
        if snow:
            snowy += 1
        snow_rows.append((u, v, snow))

    out_csv = os.path.join(folder, "snow_map.csv")
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["u", "v", "snow"])
        writer.writerows(snow_rows)

    pct = snowy / len(snow_rows) * 100
    print(f"✔ {os.path.basename(folder):30} : {snowy}/{len(snow_rows)} "
          f"edges snowy ({pct:.1f} %)  -> snow_map.csv")
    return True

def main():
    processed = 0
    for slug in os.listdir(ROOT):
        folder = os.path.join(ROOT, slug)
        if os.path.isdir(folder):
            if simulate_for_folder(folder):
                processed += 1
    if processed:
        print(f"🎯 Snow maps generated for {processed} neighborhoods.")
    else:
        print("⚠ No neighborhood graphs found – nothing done.")

if __name__ == "__main__":
    main()

