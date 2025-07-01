import os
import pickle
import json
import urllib.parse
from math import radians, cos, sin, sqrt, atan2

BASE_DIR = "../resources"
CARTIERS = {
    "1": "anjou",
    "2": "plateau-mont-royal",
    "3": "outremont",
    "4": "riviere-des-prairies-pointe-aux-trembles",
    "5": "verdun"
}

MAX_WAYPOINTS = 23  # Google Maps limit
DIST_THRESHOLD = 0.0005  # En degrés approx (~50m)

def choisir_cartier():
    print("Choisissez un quartier :")
    for key, name in CARTIERS.items():
        print(f"{key}. {name.replace('-', ' ').title()}")
    while True:
        choix = input("Votre choix (1-5) : ").strip()
        if choix in CARTIERS:
            return CARTIERS[choix]
        print("❌ Entrée invalide. Veuillez choisir un numéro entre 1 et 5.")

def charger_coordonnees(path_dir):
    pkl_path = os.path.join(path_dir, "eulerized_graph.pkl")
    json_path = os.path.join(path_dir, "eulerian_path.json")

    with open(pkl_path, "rb") as f:
        G = pickle.load(f)
    with open(json_path, "r") as f:
        path_data = json.load(f)

    path_nodes = [edge["u"] for edge in path_data] + [path_data[-1]["v"]]
    coords = [
        (G.nodes[n]["y"], G.nodes[n]["x"])
        for n in path_nodes if n in G.nodes and "x" in G.nodes[n] and "y" in G.nodes[n]
    ]
    return coords

def distance(c1, c2):
    """Retourne la distance approx entre deux coordonnées (lat/lon) en degrés"""
    return sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

def filtrer_coords(coords, max_points=MAX_WAYPOINTS + 2):
    """Filtrage spatial pour réduire les points trop proches + échantillonnage"""
    if not coords:
        return []

    filtered = [coords[0]]
    for pt in coords[1:]:
        if distance(pt, filtered[-1]) >= DIST_THRESHOLD:
            filtered.append(pt)

    # Si encore trop de points, on sous-échantillonne uniformément
    if len(filtered) > max_points:
        step = len(filtered) / max_points
        sampled = [filtered[int(i * step)] for i in range(max_points)]
        return sampled
    return filtered

def generer_url_google_maps(coords):
    if len(coords) < 2:
        print("❌ Pas assez de points pour créer un trajet.")
        return None

    coords = filtrer_coords(coords)

    origin = coords[0]
    destination = coords[-1]
    waypoints = coords[1:-1][:MAX_WAYPOINTS]

    base_url = "https://www.google.com/maps/dir/?api=1"
    origin_str = f"{origin[0]},{origin[1]}"
    dest_str = f"{destination[0]},{destination[1]}"
    waypoints_str = "|".join(f"{lat},{lon}" for lat, lon in waypoints)

    params = {
        "origin": origin_str,
        "destination": dest_str,
        "travelmode": "driving",
        "waypoints": waypoints_str
    }
    return f"{base_url}&{urllib.parse.urlencode(params)}"

if __name__ == "__main__":
    cartier = choisir_cartier()
    full_path = os.path.join(BASE_DIR, cartier)
    coords = charger_coordonnees(full_path)
    url = generer_url_google_maps(coords)

    if url:
        print("\n🗺️ Lien Google Maps optimisé généré :")
        print(url)
