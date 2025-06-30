#!/usr/bin/env python3
"""
Interactive Mapbox:
  • coloured lines – oriented Eulerian drone walk (one colour / borough)
  • black   lines – global snow overlay, auto-generated if absent
"""

import os, csv, json, pickle
from collections import defaultdict
import plotly.graph_objects as go
from plotly.colors import qualitative

ROOT         = "resources"                    # root containing borough dirs
GLOBAL_SNOW  = os.path.join(ROOT, "snow_map_global.csv")
OUT_HTML     = os.path.join(ROOT, "oriented_snow.html")
PALETTE      = qualitative.Dark24
os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)

# ────────────────────────────────────────────────────────────────────────────
def add_seg(store, lat1, lon1, lat2, lon2):
    store["lat"] += [lat1, lat2, None]
    store["lon"] += [lon1, lon2, None]

# ---------------------------------------------------------------------------
def merge_snow_csvs(force=True):
    """Create/overwrite resources/snow_map_global.csv."""
    if force and os.path.isfile(GLOBAL_SNOW):
        print(f"Removing existing {GLOBAL_SNOW}")
        os.remove(GLOBAL_SNOW)          # ← erase stale file
    else:
        print(f"Cannot find the {GLOBAL_SNOW} file")

    rows, seen = [], set()
    for slug in os.listdir(ROOT):
        s_csv = os.path.join(ROOT, slug, "snow_map.csv")
        if not os.path.isfile(s_csv):
            continue
        with open(s_csv, newline="") as f:
            for r in csv.reader(f):
                if r and r[0].isdigit():          # skip header
                    key = (r[0], r[1])
                    if key not in seen:
                        seen.add(key)
                        rows.append(r)

    if rows:
        with open(GLOBAL_SNOW, "w", newline="") as f:
            csv.writer(f).writerows([["u", "v", "snow"], *rows])
        print(f"📝 Global snow file rebuilt with {len(rows):,} edges")
    else:
        print("⚠ No borough snow CSVs found — global file not written")

# ---------------------------------------------------------------------------
def load_borough_paths():
    paths, allpts = defaultdict(lambda: {"lat": [], "lon": []}), set()
    for slug in os.listdir(ROOT):
        folder = os.path.join(ROOT, slug)
        g_pkl  = os.path.join(folder, "eulerized_graph_oriented.pkl")
        p_json = os.path.join(folder, "eulerian_path_oriented.json")
        if not (os.path.isfile(g_pkl) and os.path.isfile(p_json)):
            continue
        G    = pickle.load(open(g_pkl, "rb"))
        walk = json.load(open(p_json))
        for e in walk:
            u, v = e["u"], e["v"]
            if u in G.nodes and v in G.nodes:
                lat1, lon1 = G.nodes[u]["y"], G.nodes[u]["x"]
                lat2, lon2 = G.nodes[v]["y"], G.nodes[v]["x"]
                add_seg(paths[slug], lat1, lon1, lat2, lon2)
                allpts.update([(lat1, lon1), (lat2, lon2)])
    return paths, allpts

# ---------------------------------------------------------------------------
def build_node_lookup():
    node_xy = {}
    for slug in os.listdir(ROOT):
        pkl = os.path.join(ROOT, slug, "eulerized_graph_oriented.pkl")
        if not os.path.isfile(pkl):
            continue
        G = pickle.load(open(pkl, "rb"))
        node_xy.update({n: (d["y"], d["x"]) for n, d in G.nodes(data=True)})
    return node_xy

# ---------------------------------------------------------------------------
def main():
    # 1. ensure global snow file
    merge_snow_csvs(True)

    # 2. load borough paths
    paths, allpts = load_borough_paths()
    if not allpts:
        print("❌ No borough data found — abort.")
        return

    # 3. node lookup & snow overlay
    node_xy = build_node_lookup()
    snow = {"lat": [], "lon": []}
    snow_edges = 0
    if os.path.isfile(GLOBAL_SNOW):
        with open(GLOBAL_SNOW, newline="") as f:
            for r in csv.reader(f):
                if r and r[0].isdigit() and r[2] == "1":
                    u, v = int(r[0]), int(r[1])
                    if u in node_xy and v in node_xy:
                        lat1, lon1 = node_xy[u]
                        lat2, lon2 = node_xy[v]
                        add_seg(snow, lat1, lon1, lat2, lon2)
                        allpts.update([(lat1, lon1), (lat2, lon2)])
                        snow_edges += 1
    print(f"✔ Using global snow file with {snow_edges:,} snowy edges")

    # 4. centre of map
    cen_lat = sum(p[0] for p in allpts)/len(allpts)
    cen_lon = sum(p[1] for p in allpts)/len(allpts)
    colours = {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(paths)}

    fig = go.Figure()

    # coloured borough paths (below)
    for slug, d in paths.items():
        fig.add_trace(go.Scattermapbox(
            lat=d["lat"], lon=d["lon"],
            mode="lines", line=dict(width=2, color=colours[slug]),
            name=slug))

    # snow overlay (above)
    if snow["lat"]:
        fig.add_trace(go.Scattermapbox(
            lat=snow["lat"], lon=snow["lon"],
            mode="lines", line=dict(width=4, color="black"),
            name="snow", hoverinfo="skip"))

    fig.update_layout(
        mapbox=dict(style="carto-positron",
                    center=dict(lat=cen_lat, lon=cen_lon), zoom=11),
        margin=dict(r=0, t=40, l=0, b=0),
        title="🚀 Oriented Drone Paths with Global Snow Overlay",
        hovermode="closest")

    fig.write_html(OUT_HTML, include_plotlyjs="cdn", full_html=True)
    print(f"✅ Map saved → {OUT_HTML}")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()

