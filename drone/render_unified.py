import os
import pickle
import json
import plotly.graph_objects as go
from plotly.colors import qualitative

NEIGHBORHOOD_DIR = "resources/neighborhoods"
OUTPUT_PATH = "resources/unified/drone_plotly_map.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def render_plotly_mapbox():
    from collections import defaultdict

    secteur_paths = defaultdict(lambda: {"lat": [], "lon": []})
    all_coords = set()

    for name in sorted(os.listdir(NEIGHBORHOOD_DIR)):
        path = os.path.join(NEIGHBORHOOD_DIR, name)
        if not os.path.isdir(path):
            continue

        try:
            with open(os.path.join(path, "eulerized_graph.pkl"), "rb") as f:
                G = pickle.load(f)

            with open(os.path.join(path, "eulerian_path.json")) as f:
                path_data = json.load(f)
            path_nodes = [edge["u"] for edge in path_data] + [path_data[-1]["v"]]

            coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path_nodes if n in G.nodes]

            for i in range(len(coords) - 1):
                lat1, lon1 = coords[i]
                lat2, lon2 = coords[i + 1]
                secteur_paths[name]["lat"].extend([lat1, lat2, None])
                secteur_paths[name]["lon"].extend([lon1, lon2, None])
                all_coords.update([(lat1, lon1), (lat2, lon2)])

        except Exception as e:
            print(f"⚠️ Skipping {name} due to error: {e}")

    if not all_coords:
        print("❌ Aucun segment valide.")
        return

    lats, lons = zip(*all_coords)
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)

    fig = go.Figure()

    secteur_names = list(secteur_paths.keys())
    palette = qualitative.Plotly
    color_map = {
        secteur: palette[i % len(palette)]
        for i, secteur in enumerate(secteur_names)
    }

    for secteur, data in secteur_paths.items():
        fig.add_trace(go.Scattermapbox(
            lat=data["lat"],
            lon=data["lon"],
            mode="lines",
            line=dict(width=3, color=color_map[secteur]),
            name=secteur,
            hoverinfo="text",
            text=[secteur] * len(data["lat"]),
        ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": avg_lat, "lon": avg_lon},
            zoom=11,
            uirevision="zoom"
        ),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title="🛰️ Drone reconnaissance paths – Montréal",
        autosize=True,
        hovermode="closest",
        dragmode="pan"
    )

    fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True)
    print(f"✅ Carte interactive avec couleurs restaurées générée : {OUTPUT_PATH}")

if __name__ == "__main__":
    render_plotly_mapbox()
