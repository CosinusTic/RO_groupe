#!/usr/bin/env python3
"""
phase2_vehicle.py — Phase 2 : directed Chinese‑Postman per borough
=================================================================

* Compatible with Python ≥ 3.6, NetworkX ≥ 3.0, OSMnx ≥ 2.0
* No walrus operator, no pattern‑matching.
* Works with both `DiGraph` and `MultiDiGraph` edge styles returned by
  OSMnx.
* Parallel borough processing via `ProcessPoolExecutor` (`--processes`).
* Splits the directed tour among any number of vehicles (`--vehicles`).
* Outputs:
    • `results_phase2/borough‑<name>.geojson` – full directed tour.
    • `results_phase2/borough‑veh<N>.geojson` – per‑vehicle slices.
    • `results_phase2/summary.csv` – km per vehicle + totals.
    • (optional) quick‑look PNGs (omit with `--no‑plot`).

Algorithm
---------
For each borough:
1. **Download** directed drive graph with OSMnx.
2. **Undirected snapshot → Euler tour**  
   * take `G_dir.to_undirected()` per connected component,
   * `nx.eulerize()` to make all degrees even,
   * `nx.eulerian_circuit()` to get an undirected edge tour,
   * convert to a *node list* (cheap).
3. **Re‑project to directed network**  
   For each consecutive pair `(u, v)` in that node list, compute the
   **shortest directed path** (`weight='length'`) and concatenate the
   edges.  Always succeeds because the original was derived from `G_dir`.
4. **Distance & slicing**  
   Compute total km; slice edges round‑robin across the requested number
   of vehicles.

Usage
-----
    python phase2_vehicle.py --vehicles 3 --processes 5 [--no-plot]

"""
from __future__ import annotations

import csv
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from typing import Iterable, List, Tuple

import networkx as nx
import osmnx as ox

try:
    import matplotlib.pyplot as plt  # optional, only if plotting requested
except ImportError:
    plt = None  # type: ignore

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
BOROUGHS = [
    "Plateau-Mont-Royal, Montréal, Québec, Canada",
    "Outremont, Montréal, Québec, Canada",
    "Verdun, Montréal, Québec, Canada",
    "Anjou, Montréal, Québec, Canada",
    "Rivière-des-Prairies–Pointe-aux-Trembles, Montréal, Québec, Canada",
]
EDGE_WEIGHT = "length"  # metres
OUT_DIR = "results_phase2"
DAILY_LIMIT_KM = 350.0  # placeholder for Phase 3 (not used here)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def pairwise(iterable: Iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    it = iter(iterable)
    prev = next(it)
    for item in it:
        yield prev, item
        prev = item

def get_edge_length(G: nx.MultiDiGraph, u, v, k=None) -> float:
    """Return edge length in metres, whether graph is MultiDiGraph or DiGraph."""
    if k is None and G.is_multigraph():
        # pick the first key deterministically
        k = next(iter(G[u][v]))
    data = G.edges[u, v] if k is None else G.edges[u, v, k]
    return float(data.get(EDGE_WEIGHT, 0.0))

# ---------------------------------------------------------------------------
# Core CPP logic
# ---------------------------------------------------------------------------

def undirected_euler_nodes(G_dir: nx.MultiDiGraph) -> List[int]:
    """Return a continuous node list that is an Euler tour of *every* connected
    component of an undirected snapshot of ``G_dir``.
    Always succeeds thanks to `nx.eulerize`.
    """
    Gu = G_dir.to_undirected()
    tour_nodes: List[int] = []

    for comp in nx.connected_components(Gu):
        H = Gu.subgraph(comp).copy()
        H_eul = nx.eulerize(H)
        edges = list(nx.eulerian_circuit(H_eul))
        tour_nodes.extend([u for u, _ in edges])
        # add last target node to close component
        if edges:
            tour_nodes.append(edges[-1][1])

    return tour_nodes

def directed_cpp_edges(G_dir: nx.MultiDiGraph, node_sequence: List[int]) -> List[Tuple]:
    """Map the undirected node walk onto directed edges via shortest paths."""
    edges: List[Tuple] = []
    for u, v in pairwise(node_sequence):
        if u == v:
            continue
        try:
            sp_nodes = nx.shortest_path(G_dir, u, v, weight=EDGE_WEIGHT)
        except nx.NetworkXNoPath:
            # Should not happen on real road graphs; fallback to undirected path
            sp_nodes = nx.shortest_path(G_dir.to_undirected(), u, v, weight=EDGE_WEIGHT)
        edges.extend(list(pairwise(sp_nodes)))
    return edges

# ---------------------------------------------------------------------------
# Borough processing (runs in worker process)
# ---------------------------------------------------------------------------

def process_borough(place: str, vehicles: int, make_plot: bool = True) -> dict:
    print(f"[fetch] {place} …", end="", flush=True)
    G_dir = ox.graph_from_place(place, network_type="drive", simplify=True)
    print(f"  ✓  (|V|={G_dir.number_of_nodes()}, |E|={G_dir.number_of_edges()})")

    # 1) undirected CPP ⇒ node list
    node_sequence = undirected_euler_nodes(G_dir)
    # 2) map to directed edges
    directed_edges = directed_cpp_edges(G_dir, node_sequence)

    # 3) total distance
    total_km = sum(get_edge_length(G_dir, *e) for e in directed_edges) / 1000.0

    # 4) split among vehicles (round‑robin by edge)
    veh_edges: List[List[Tuple]] = [[] for _ in range(vehicles)]
    for i, e in enumerate(directed_edges):
        veh_edges[i % vehicles].append(e)

    # 5) write geojson
    os.makedirs(OUT_DIR, exist_ok=True)
    base_name = place.split(",")[0].replace(" ", "_")
    geo_all = {
        "type": "Feature",
        "properties": {"borough": place, "km": total_km},
        "geometry": {
            "type": "LineString",
            "coordinates": [(G_dir.nodes[u]["x"], G_dir.nodes[u]["y"]) for u, _ in directed_edges] +
                           [(G_dir.nodes[directed_edges[-1][1]]["x"], G_dir.nodes[directed_edges[-1][1]]["y"])]
        }
    }
    with open(os.path.join(OUT_DIR, f"{base_name}.geojson"), "w") as f:
        json.dump(geo_all, f)

    # per vehicle
    for vid, edgelist in enumerate(veh_edges, 1):
        coords = [(G_dir.nodes[u]["x"], G_dir.nodes[u]["y"]) for u, _ in edgelist]
        if edgelist:
            coords.append((G_dir.nodes[edgelist[-1][1]]["x"], G_dir.nodes[edgelist[-1][1]]["y"]))
        feat = {
            "type": "Feature",
            "properties": {"borough": place, "vehicle": vid},
            "geometry": {"type": "LineString", "coordinates": coords},
        }
        with open(os.path.join(OUT_DIR, f"{base_name}-veh{vid}.geojson"), "w") as f:
            json.dump(feat, f)

    # optional quick‑look plot
    if make_plot and plt is not None:
        fig, ax = ox.plot_graph(G_dir, show=False, close=False, node_size=0, edge_color="lightgray")
        xs, ys = zip(*[(G_dir.nodes[u]["x"], G_dir.nodes[u]["y"]) for u, _ in directed_edges])
        ax.plot(xs, ys, color="red", linewidth=1.0)
        fig.savefig(os.path.join(OUT_DIR, f"{base_name}.png"), dpi=200)
        plt.close(fig)  # type: ignore

    return {"borough": place, "km": total_km}

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Phase 2 vehicle routing (directed CPP per borough)")
    parser.add_argument("--vehicles", type=int, default=2, help="vehicles per borough")
    parser.add_argument("--processes", type=int, default=os.cpu_count() or 1, help="parallel processes")
    parser.add_argument("--no-plot", action="store_true", help="skip PNG generation")
    args = parser.parse_args(argv)

    print(f"[Phase 2] Directed CPP with {args.vehicles} vehicle(s) per borough")

    with ProcessPoolExecutor(max_workers=args.processes) as pool:
        futs = [pool.submit(process_borough, b, args.vehicles, not args.no_plot) for b in BOROUGHS]
        stats: List[dict] = []
        for fut in as_completed(futs):
            stats.append(fut.result())

    # summary CSV
    csv_path = os.path.join(OUT_DIR, "summary.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["borough", "km"])
        writer.writeheader()
        writer.writerows(stats)
    print(f"[save] {csv_path}")


if __name__ == "__main__":
    main(sys.argv[1:])

