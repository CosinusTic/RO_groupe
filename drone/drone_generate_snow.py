import os
import pickle
import csv
from noise import snoise2
import networkx as nx

GRAPH_PATH = "resources/whole_city/eulerized_graph.pkl"
SNOW_MAP_PATH = "resources/whole_city/snow_map.csv"

# Configuration
FREQ = 0.01       # fréquence du bruit : plus petit = zones plus grandes
THRESHOLD = 0.15  # seuil d’intensité du bruit pour dire "il neige"
SEED = 42         # pour reproductibilité

def simulate_snow_city():
    if not os.path.isfile(GRAPH_PATH):
        print(f"❌ Missing graph: {GRAPH_PATH}")
        return

    with open(GRAPH_PATH, "rb") as f:
        G = pickle.load(f)

    print(f"📡 Chargement du graphe global ({len(G.edges())} arêtes)...")

    # Obtenir les bornes pour normalisation
    lats = [G.nodes[n]['y'] for n in G.nodes if 'y' in G.nodes[n]]
    lons = [G.nodes[n]['x'] for n in G.nodes if 'x' in G.nodes[n]]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    def normalize(val, min_val, max_val):
        return (val - min_val) / (max_val - min_val)

    snow_data = []

    print("❄️ Calcul du bruit de neige pour chaque segment...")

    for u, v in G.edges():
        try:
            x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
            x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
            mx = normalize((x1 + x2) / 2, min_lon, max_lon)
            my = normalize((y1 + y2) / 2, min_lat, max_lat)
            intensity = snoise2(mx / FREQ, my / FREQ, octaves=3, base=SEED)
            snow = int(intensity > THRESHOLD)
            snow_data.append((u, v, snow))
        except KeyError:
            print(f"⚠️ Coordonnées manquantes pour arête ({u},{v}), ignorée.")

    print(f"✅ {sum(s == 1 for _, _, s in snow_data)} segments enneigés sur {len(snow_data)}")

    os.makedirs(os.path.dirname(SNOW_MAP_PATH), exist_ok=True)
    with open(SNOW_MAP_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["u", "v", "snow"])
        writer.writerows(snow_data)

    print(f"📦 Fichier enregistré : {SNOW_MAP_PATH}")

if __name__ == "__main__":
    simulate_snow_city()
