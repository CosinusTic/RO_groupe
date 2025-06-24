#!/usr/bin/env python3
"""
phase1_drone.py — Phase 1 (Drone reconnaissance)
===============================================
Implements **tasks 1, 2, 3, 4, 5, 8, 9** of the roadmap.

Highlights
----------
* **Parallel** download & preprocessing of the five main Montréal boroughs
  using `ProcessPoolExecutor` (see `--processes`).
* **Merged** graph is Eulerised **per connected component** so we never hit
  the “G is not connected” error.
* Distance is measured directly on the Euler circuit; when a duplicated edge
  (added by `nx.eulerize`) has no `length` attribute, a haversine fallback is
  used.
* **Cost model**: €100 per drone‑day + €0.01 per km. A day is assumed to
  cover ≤ 500 km (parameter).
* Outputs: `summary.csv`, `tour.geojson`, and `tour.png` (unless `--no-plot`).

Changelog
---------
* **v0.4** *(current)* — Fix `NameError: plt` (missing import) and clarify why
  CPU usage looks mostly single‑core after the download stage.
* v0.3 — Robust distance accounting (haversine fallback).
* v0.2 — Handle disconnected components.
* v0.1 — Initial proof‑of‑concept.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt  # ← FIXED: needed for plot_tour()
import networkx as nx
import osmnx as ox

# ---------------------------------------------------------------------------
# OSMnx logging / cache – version‑agnostic
# ---------------------------------------------------------------------------
try:  # OSMnx ≤1.4 style
    ox.config(use_cache=True, log_console=False)
except AttributeError:  # OSMnx ≥2.0 style
    ox.settings.use_cache = True
    ox.settings.log_console = False

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
BOROUGHS = [
    "Plateau-Mont-Royal, Montréal, Québec, Canada",
    "Outremont, Montréal, Québec, Canada",
    "Verdun, Montréal, Québec, Canada",
    "Anjou, Montréal, Québec, Canada",
    "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada",
]

DRONE_DAILY_COST = 100.0  # € / day
DRONE_COST_PER_KM = 0.01  # € / km
DRONE_MAX_KM_PER_DAY = 500.0  # km a drone can cover in a shift (assumed)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great‑circle distance (approx.) between two (lat, lon) points in km."""
    R = 6371.0  # Earth radius km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(
        dlambda / 2
    ) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def edge_length_from_lookup(G: nx.MultiGraph, u: int, v: int) -> float:
    """Return edge length (metres); fallback to haversine if missing."""
    for data in G.get_edge_data(u, v, default={}).values():
        length = data.get("length")
        if length is not None:
            return float(length)
    lat1, lon1 = G.nodes[u]["y"], G.nodes[u]["x"]
    lat2, lon2 = G.nodes[v]["y"], G.nodes[v]["x"]
    return haversine_km(lat1, lon1, lat2, lon2) * 1000.0


# ---------------------------------------------------------------------------
# Per‑borough worker
# ---------------------------------------------------------------------------

def fetch_and_prepare(place: str) -> nx.MultiGraph:
    print(f"[fetch] {place} …", flush=True)
    G = ox.graph_from_place(place, network_type="drive", simplify=True)
    G_u = G.to_undirected()
    print(
        f"[fetch] {place} ✓  (|V|={G_u.number_of_nodes()}, |E|={G_u.number_of_edges()})",
        flush=True,
    )
    return G_u


# ---------------------------------------------------------------------------
# Euler computation
# ---------------------------------------------------------------------------

def euler_tour_for_component(
    comp: nx.MultiGraph, original: nx.MultiGraph
) -> Tuple[List[Tuple[int, int]], float]:
    """Euler tour & km for one connected component."""
    comp_eul = nx.eulerize(comp)
    circuit = list(nx.eulerian_circuit(comp_eul))
    metres = sum(edge_length_from_lookup(original, u, v) for u, v in circuit)
    return circuit, metres / 1000.0  # km


def compute_euler_tours(
    merged: nx.MultiGraph,
) -> Tuple[List[Tuple[int, int] | None], float]:
    print("[euler] Computing Euler tours component‑wise…", flush=True)
    tour: List[Tuple[int, int] | None] = []
    total_km = 0.0
    for i, nodes in enumerate(nx.connected_components(merged)):
        comp = merged.subgraph(nodes).copy()
        circuit, km = euler_tour_for_component(comp, merged)
        if i > 0:
            tour.append(None)  # teleport sentinel
        tour.extend(circuit)
        total_km += km
    return tour, total_km


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_tour(G: nx.MultiGraph, tour: List[Tuple[int, int] | None], out_png: Path):
    coords_lat, coords_lon = [], []
    for edge in tour:
        if edge is None:
            continue
        u, _ = edge
        coords_lat.append(G.nodes[u]["y"])
        coords_lon.append(G.nodes[u]["x"])
    last_edge = next(e for e in reversed(tour) if e is not None)
    coords_lat.append(G.nodes[last_edge[1]]["y"])
    coords_lon.append(G.nodes[last_edge[1]]["x"])

    fig, ax = ox.plot_graph(
        G,
        show=False,
        close=False,
        edge_color="lightgray",
        node_size=0,
        bgcolor="white",
    )
    ax.plot(coords_lon, coords_lat, color="red", linewidth=1.4, alpha=0.7)
    ax.set_title("Euler tour – main Montréal boroughs", fontsize=12)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser("phase1_drone.py — Drone reconnaissance phase 1")
    ap.add_argument("--processes", type=int, default=min(8, os.cpu_count() or 2))
    ap.add_argument("--output-dir", type=Path, default=Path("results_phase1"))
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parallel fetch -------------------------------------------------------
    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] Starting parallel fetch of boroughs…",
        flush=True,
    )
    with ProcessPoolExecutor(max_workers=args.processes) as pool:
        borough_graphs = list(pool.map(fetch_and_prepare, BOROUGHS))

    # Merge ---------------------------------------------------------------
    print("[merge] Merging borough graphs…", flush=True)
    merged = nx.compose_all(borough_graphs)
    print(
        f"[merge] Unified graph: |V|={merged.number_of_nodes():,}  |E|={merged.number_of_edges():,}",
        flush=True,
    )

    # Euler ---------------------------------------------------------------
    tour, km = compute_euler_tours(merged)
    print(f"[euler] Total distance = {km:.1f} km", flush=True)

    # Cost ---------------------------------------------------------------
    days = math.ceil(km / DRONE_MAX_KM_PER_DAY)
    cost = days * DRONE_DAILY_COST + km * DRONE_COST_PER_KM
    print(
        f"[cost] Days = {days},  Cost = €{cost:,.2f} (100€/day + 0.01€/km)",
        flush=True,
    )

    # Persist outputs -----------------------------------------------------
    summary_csv = out_dir / "summary.csv"
    with summary_csv.open("w", newline="") as f:
        f.write("km,days,cost\n")
        f.write(f"{km:.2f},{days},{cost:.2f}\n")
    print(f"[save] Wrote {summary_csv}")

    # GeoJSON -------------------------------------------------------------
    import shapely.geometry as geom
    import geopandas as gpd

    features = []
    coords_accum: List[Tuple[float, float]] = []
    for edge in tour:
        if edge is None:
            if coords_accum:
                features.append(geom.LineString(coords_accum))
                coords_accum = []
            continue
        u, _ = edge
        coords_accum.append((merged.nodes[u]["x"], merged.nodes[u]["y"]))
    if coords_accum:
        features.append(geom.LineString(coords_accum))

    gdf = gpd.GeoDataFrame(geometry=features, crs="EPSG:4326")
    geojson_path = out_dir / "tour.geojson"
    gdf.to_file(geojson_path, driver="GeoJSON")
    print(f"[save] Wrote {geojson_path}")

    # PNG -----------------------------------------------------------------
    if not args.no_plot:
        out_png = out_dir / "tour.png"
        plot_tour(merged, tour, out_png)
        print(f"[save] Wrote {out_png}")

    # --------------------------------------------------------------------
    print("\nDone. Note on CPU usage: the download & simplification of borough graphs\n"
          "runs concurrently across the specified processes; afterwards,"
          " Eulerisation and plotting are single‑process steps (they are"
          " mostly CPU‑bound but quick at this graph size). If you need to",
          " push full parallelism further, consider splitting Eulerisation",
          " per component into separate processes as well — but for <10k",
          " edges the wall‑time benefit is negligible.")


if __name__ == "__main__":
    main()

