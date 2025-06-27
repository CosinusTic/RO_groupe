import os
import pickle
import csv
from noise import snoise2
import networkx as nx
import random
import time

# Chemins spécifiques au quartier d'Anjou
GRAPH_PATH = "resources/neighborhoods/anjou/eulerized_graph.pkl"
SNOW_MAP_PATH = "resources/neighborhoods/snow_map.csv"

# Configuration réaliste aléatoire
FREQ = 0.75        # Zones de neige plus grandes
THRESHOLD = 0.075    # Seuil : + haut = neige plus rare mais plus nette
OCTAVES = 4         # Complexité du bruit
BASE = random.randint(0, 10000)  # seed aléatoire pour chaque exécution

def simulate_snow_city():
    if not os.path.isfile(GRAPH_PATH):
        print(f"❌ Graphe introuvable : {GRAPH_PATH}")
        return

    with open(GRAPH_PATH, "rb") as f:
        G = pickle.load(f)

    print(f"✔ Chargement du graphe ({len(G.edges())} arêtes)")

    # Extraire les coordonnées
    lats = [G.nodes[n]['y'] for n in G.nodes if 'y' in G.nodes[n]]
    lons = [G.nodes[n]['x'] for n in G.nodes if 'x' in G.nodes[n]]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    def normalize(val, min_val, max_val):
        return (val - min_val) / (max_val - min_val)

    snow_data = []
    print(f"🌨️ Simulation aléatoire des zones de neige (base={BASE})...")

    for u, v in G.edges():
        try:
            x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
            x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']

            # Calcul du point central (milieu de l’arête)
            mx = normalize((x1 + x2) / 2, min_lon, max_lon)
            my = normalize((y1 + y2) / 2, min_lat, max_lat)

            intensity = snoise2(mx / FREQ, my / FREQ, octaves=OCTAVES, base=BASE)
            snow = int(intensity > THRESHOLD)

            snow_data.append((u, v, snow))

        except KeyError:
            print(f"⚠️ Coordonnées manquantes pour arête ({u},{v}), ignorée")

    total = len(snow_data)
    covered = sum(1 for _, _, s in snow_data if s == 1)
    print(f"🧊 {covered} segments enneigés sur {total} ({(covered/total)*100:.1f} %)")

    os.makedirs(os.path.dirname(SNOW_MAP_PATH), exist_ok=True)
    with open(SNOW_MAP_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["u", "v", "snow"])
        writer.writerows(snow_data)

    print(f"💾 Fichier exporté : {SNOW_MAP_PATH}")

if __name__ == "__main__":
    simulate_snow_city()
