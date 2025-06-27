#!/usr/bin/env python3
"""
Interactive Mapbox HTML
  • coloured lines – oriented Eulerian drone paths (one colour/borough)
  • black lines    – all edges flagged in resources/whole_city/snow_map.csv
"""

import os, json, csv, pickle
from collections import defaultdict
import plotly.graph_objects as go
from plotly.colors import qualitative

NEIGH_DIR   = "resources/neighborhoods"
GLOBAL_SNOW = "resources/neighborhoods/snow_map.csv"
OUT_HTML    = "resources/unified/drone_oriented_with_snow.html"
PALETTE     = qualitative.Dark24
os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)

# ───────────── helper ──────────────────────────────────────────────────
def add_seg(store, lat1, lon1, lat2, lon2):
    store["lat"] += [lat1, lat2, None]
    store["lon"] += [lon1, lon2, None]
# ───────────── main ────────────────────────────────────────────────────
def main():
    # ---------- gather coloured borough paths ----------
    paths = defaultdict(lambda: {"lat": [], "lon": []})
    allpts = set()

    for i, slug in enumerate(sorted(os.listdir(NEIGH_DIR))):
        folder = os.path.join(NEIGH_DIR, slug)
        g_pkl = os.path.join(folder, "eulerized_graph_oriented.pkl")
        p_js  = os.path.join(folder, "eulerian_path_oriented.json")
        if not (os.path.isfile(g_pkl) and os.path.isfile(p_js)):
            continue
        G   = pickle.load(open(g_pkl, "rb"))
        walk = json.load(open(p_js))
        for e in walk:
            u, v = e["u"], e["v"]
            if u in G.nodes and v in G.nodes:
                lat1, lon1 = G.nodes[u]["y"], G.nodes[u]["x"]
                lat2, lon2 = G.nodes[v]["y"], G.nodes[v]["x"]
                add_seg(paths[slug], lat1, lon1, lat2, lon2)
                allpts.update([(lat1, lon1), (lat2, lon2)])

    if not allpts:
        print("❌ No borough data – abort.")
        return

    # ---------- build node-coordinate lookup ----------
    node_xy = {}
    for slug in paths:
        G = pickle.load(open(os.path.join(NEIGH_DIR, slug,
                              "eulerized_graph_oriented.pkl"), "rb"))
        node_xy.update({n: (d["y"], d["x"]) for n, d in G.nodes(data=True)})

    # ---------- load global snow CSV ----------
    snow = {"lat": [], "lon": []}
    snow_edges = 0
    if os.path.isfile(GLOBAL_SNOW):
        with open(GLOBAL_SNOW, newline="") as f:
            for r in csv.reader(f):
                if len(r) < 3 or r[2] != "1":
                    continue
                u, v = int(r[0]), int(r[1])
                if u in node_xy and v in node_xy:
                    lat1, lon1 = node_xy[u]
                    lat2, lon2 = node_xy[v]
                    add_seg(snow, lat1, lon1, lat2, lon2)
                    allpts.update([(lat1, lon1), (lat2, lon2)])
                    snow_edges += 1
    else:
        print(f"⚠ Global snow file not found: {GLOBAL_SNOW}")

    # ---------- map centre ----------
    cen_lat = sum(p[0] for p in allpts)/len(allpts)
    cen_lon = sum(p[1] for p in allpts)/len(allpts)
    colours = {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(paths)}

    fig = go.Figure()

    # 1️⃣  borough paths below
    for slug, d in paths.items():
        fig.add_trace(go.Scattermapbox(
            lat=d["lat"], lon=d["lon"],
            mode="lines",
            line=dict(width=2, color=colours[slug]),
            name=slug
        ))

    # 2️⃣  global snow overlay above
    if snow["lat"]:
        fig.add_trace(go.Scattermapbox(
            lat=snow["lat"], lon=snow["lon"],
            mode="lines",
            line=dict(width=4, color="black"),
            name="snow",
            hoverinfo="skip"
        ))
        print(f"✔ Added {snow_edges:,} snow edges from global CSV")
    else:
        print("⚠ No snow edges flagged in global CSV")

    fig.update_layout(
        mapbox=dict(style="carto-positron",
                    center=dict(lat=cen_lat, lon=cen_lon), zoom=11),
        margin=dict(r=0,t=40,l=0,b=0),
        title="🚀 Oriented Drone Paths with Global Snow Overlay",
        hovermode="closest"
    )
    fig.write_html(OUT_HTML, include_plotlyjs="cdn", full_html=True)
    print(f"✅ Map saved → {OUT_HTML}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()

