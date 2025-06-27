#!/usr/bin/env python3
"""
Render oriented Eulerian drone paths for the 5 boroughs
as an interactive Mapbox HTML (one color per borough).
"""
import os
import pickle
import json
import plotly.graph_objects as go
from plotly.colors import qualitative

NEIGHBORHOOD_DIR = "resources/neighborhoods"
OUTPUT_PATH      = "resources/unified/drone_oriented_plotly_map.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

def render_plotly_mapbox_oriented():
    from collections import defaultdict

    paths   = defaultdict(lambda: {"lat": [], "lon": []})
    all_pts = set()

    for slug in sorted(os.listdir(NEIGHBORHOOD_DIR)):
        n_dir = os.path.join(NEIGHBORHOOD_DIR, slug)
        if not os.path.isdir(n_dir):
            continue

        g_pkl = os.path.join(n_dir, "eulerized_graph_oriented.pkl")
        p_json= os.path.join(n_dir, "eulerian_path_oriented.json")
        if not (os.path.isfile(g_pkl) and os.path.isfile(p_json)):
            print(f"⚠️  Skipping {slug}: missing oriented files")
            continue

        # --- Load directed graph and oriented walk
        with open(g_pkl, "rb") as f:
            G = pickle.load(f)
        with open(p_json) as f:
            walk = json.load(f)

        coords = [
            (G.nodes[u]["y"], G.nodes[u]["x"])
            for edge in walk
            for u in (edge["u"], edge["v"])
            if edge["u"] in G.nodes and edge["v"] in G.nodes
        ]

        for i in range(0, len(coords)-1, 2):
            lat1, lon1 = coords[i]
            lat2, lon2 = coords[i+1]
            paths[slug]["lat"].extend([lat1, lat2, None])
            paths[slug]["lon"].extend([lon1, lon2, None])
            all_pts.update([(lat1, lon1), (lat2, lon2)])

    if not all_pts:
        print("❌ No valid segments; nothing rendered.")
        return

    # --- Map centre
    lats, lons = zip(*all_pts)
    center = {"lat": sum(lats)/len(lats), "lon": sum(lons)/len(lons)}

    # --- Choose a palette with distinct line colours
    palette = qualitative.Dark24  # 24 visually distinct colours
    colour = {slug: palette[i % len(palette)]
              for i, slug in enumerate(paths)}

    # --- Build figure
    fig = go.Figure()
    for slug, data in paths.items():
        fig.add_trace(go.Scattermapbox(
            lat=data["lat"],
            lon=data["lon"],
            mode="lines",
            line=dict(width=3, color=colour[slug]),
            name=slug,
            hoverinfo="text",
            text=[slug]*len(data["lat"])
        ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=center,
            zoom=11,
            uirevision="zoom"
        ),
        margin=dict(r=0, t=40, l=0, b=0),
        title="🚀 Oriented Eulerian Drone Paths – Montréal",
        hovermode="closest",
        dragmode="pan"
    )

    fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True)
    print(f"✅ Oriented map written to {OUTPUT_PATH}")

if __name__ == "__main__":
    render_plotly_mapbox_oriented()
