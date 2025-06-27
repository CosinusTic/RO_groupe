from __future__ import annotations
import argparse, csv, datetime as _dt, json, os, pickle
from pathlib import Path

import networkx as nx
from vehicles import VehicleTypeI, VehicleTypeII, SuperDrone

ROOT = "resources/neighborhoods"
REPORT = Path("reports/all_runs.json")
REPORT.parent.mkdir(exist_ok=True)

VEH = {
    "type_I (economie d essence)": VehicleTypeI,
    "type_II (rapidite)":          VehicleTypeII,
    "drone":                       SuperDrone,
}

# ---------------------------------------------------------------- helpers
def load_graph(dir_path: str) -> nx.Graph:
    with open(os.path.join(dir_path, "eulerized_graph.pkl"), "rb") as f:
        G = pickle.load(f)
    nx.set_node_attributes(G, False, "snow")
    with open(os.path.join(dir_path, "snow_map.csv"), newline="") as f:
        for r in csv.DictReader(f):
            if int(r["snow"]) == 1:
                for nid in (r["u"], r["v"]):
                    if nid and G.has_node(int(nid)):
                        G.nodes[int(nid)]["snow"] = True
    return G


def snowy_nodes(G):                         # set[int]
    return {n for n, d in G.nodes(data=True) if d.get("snow", False)}


def prompt(lst, msg):
    for i, x in enumerate(lst, 1):
        print(f"{i}. {x}")
    while True:
        try:
            i = int(input(msg)) - 1
        except ValueError:
            i = -1
        if 0 <= i < len(lst):
            return lst[i]

# ---------------------------------------------------------------- simulation
def simulate(neigh: str, cfg: str | None):
    folder = os.path.join(ROOT, neigh)
    G = load_graph(folder)
    snowy      = snowy_nodes(G)
    init_snow  = set(snowy)

    veh_key = prompt(list(VEH), "Véhicule ? ")
    VehCls  = VEH[veh_key]

    cfg_file = cfg if cfg and os.path.exists(cfg) else None

    start = next(iter(G.nodes))
    Nveh = 0
    dist_total = dur = cost_total = 0.0
    cleared, visited = set(), set()

    while snowy:
        Nveh += 1
        agent = VehCls(start, config_path=cfg_file)

        while agent.can_continue():
            nxt = agent.choose_next(G, snowy)
            if nxt is None:
                break
            ed = G[agent.current][nxt]
            length_m = (
                ed if isinstance(ed, dict) else next(iter(ed.values()))
            ).get("length", 1.0)
            agent.move_to(nxt, length_m)
            visited.add(nxt)
            if G.nodes[nxt].get("snow", False):
                G.nodes[nxt]["snow"] = False
                snowy.discard(nxt)
                cleared.add(nxt)
                agent.snow_cleared += 1

        st = agent.log_stats()
        dist_total += st["distance_km"]
        dur        += st["time_h"]
        cost_total += agent.compute_cost()

    stats = {
        "vehicles_used": Nveh,
        "snow_cleared":  len(cleared),
        "coverage_pct":  round(100 * len(cleared) / len(init_snow), 2) if init_snow else 0,
        "visited_nodes": len(visited),
        "visit_pct":     round(100 * len(visited) / G.number_of_nodes(), 2),
        "distance_km":   round(dist_total, 2),
        "time_h":        round(dur, 2),
        "cost_total":    round(cost_total, 2),
    }

    # ------------------ rapport cumulatif -------------------------------
    rec = {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "neighborhood": neigh,
        "vehicle": veh_key,
        "stats": stats,
    }
    try:
        data = json.loads(REPORT.read_text()) if REPORT.exists() else []
    except json.JSONDecodeError:
        data = []
    data.append(rec)
    REPORT.write_text(json.dumps(data, indent=2))

    # ------------------ console -----------------------------------------
    print(
        f"{neigh} | neige {stats['snow_cleared']} nœuds | "
        f"cover {stats['coverage_pct']} % | "
        f"visit {stats['visit_pct']} % ({stats['visited_nodes']} nœuds) | "
        f"véh {stats['vehicles_used']} | dist {stats['distance_km']} km | "
        f"durée {stats['time_h']} h | coût {stats['cost_total']} €"
    )

# ---------------------------------------------------------------- CLI
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c", "--config",
        default="vehicle/config.json",
        help="fichier JSON de configuration"
    )
    simulate(prompt(os.listdir(ROOT), "Quartier ? "), ap.parse_args().config)
