import os
import pickle
import json
import csv
import plotly.graph_objects as go
from plotly.colors import qualitative, sample_colorscale

NEIGHBORHOOD_DIR = "resources/neighborhoods"
OUTPUT_PATH = "resources/unified/snow_overlay_map.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def render_plotly_mapbox_with_snow():
    from collections import defaultdict

    secteur_paths = defaultdict(lambda: {"lat": [], "lon": []})
    snow_segments = {"lat": [], "lon": []}
    all_coords = set()

    for name in sorted(os.listdir(NEIGHBORHOOD_DIR)):
        path = os.path.join(NEIGHBORHOOD_DIR, name)
        if not os.path.isdir(path):
            continue

        try:
            # === Chargement du graphe ===
            with open(os.path.join(path, "eulerized_graph.pkl"), "rb") as f:
                G = pickle.load(f)

            # === Chargement du chemin eulérien ===
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

            # === Chargement du snow_map.csv ===
            snow_csv_path = os.path.join(path, "snow_map.csv")
            if os.path.isfile(snow_csv_path):
                with open(snow_csv_path, newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["snow"] == "1":
                            u, v = int(row["u"]), int(row["v"])
                            if u in G.nodes and v in G.nodes:
                                lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
                                lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
                                snow_segments["lat"].extend([lat1, lat2, None])
                                snow_segments["lon"].extend([lon1, lon2, None])
                                all_coords.update([(lat1, lon1), (lat2, lon2)])
            else:
                print(f"⚠️ No snow map found for {name}")

        except Exception as e:
            print(f"⚠️ Skipping {name} due to error: {e}")

    if not all_coords:
        print("❌ Aucun segment valide.")
        return

    lats, lons = zip(*all_coords)
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)

    fig = go.Figure()

    # === Couleurs des secteurs ===
    secteur_names = list(secteur_paths.keys())
    # === Couleurs personnalisées à fort contraste (exclut les bleus)
    custom_palette = [
        "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
        "#FF6692", "#B6E880", "#FF97FF", "#FECB52", "#636EFA"
    ]
    color_map = {
        secteur: custom_palette[i % len(custom_palette)]
        for i, secteur in enumerate(secteur_names)
    }

    # === Tracés des trajets drone ===
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

    # === Tracé des segments enneigés en BLEU (après pour éviter qu'ils soient couverts) ===
    if snow_segments["lat"]:
        fig.add_trace(go.Scattermapbox(
            lat=snow_segments["lat"],
            lon=snow_segments["lon"],
            mode="lines",
            line=dict(width=4, color="blue"),
            name="Segments enneigés",
            hoverinfo="text",
            text=["Enneigé"] * len(snow_segments["lat"]),
        ))

    # === Mise en forme finale ===
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",  # Fond clair
            center={"lat": avg_lat, "lon": avg_lon},
            zoom=11,
            uirevision="zoom"
        ),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        title="🧊 Segments enneigés et trajets du drone – Montréal",
        autosize=True,
        hovermode="closest",
        dragmode="pan"
    )

    fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True)
    print(f"✅ Carte finale générée : {OUTPUT_PATH}")

if __name__ == "__main__":
    render_plotly_mapbox_with_snow()

