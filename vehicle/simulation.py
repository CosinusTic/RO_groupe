from __future__ import annotations
import argparse, csv, datetime as _dt, json, os, pickle
from pathlib import Path
import math

import networkx as nx
from vehicles import VehicleTypeI, VehicleTypeII, SuperDrone

# ----------------------------------------------------------------- constantes
ROOT   = "resources/neighborhoods"
REPORT = Path("reports/all_runs.json"); REPORT.parent.mkdir(exist_ok=True)

VEH = {
    "type_I":  VehicleTypeI,
    "type_II": VehicleTypeII,
    "drone":   SuperDrone,
}

# ----------------------------------------------------------------- utilitaires
def load_graph(folder: str) -> nx.Graph:
    with open(os.path.join(folder, "eulerized_graph_oriented.pkl"), "rb") as f:
        G = pickle.load(f)
    nx.set_node_attributes(G, False, "snow")
    with open(os.path.join(folder, "snow_map.csv"), newline="") as f:
        for r in csv.DictReader(f):
            if int(r["snow"]) == 1:
                for nid in (r["u"], r["v"]):
                    if nid and G.has_node(int(nid)):
                        G.nodes[int(nid)]["snow"] = True
    return G


def snowy_nodes(G):               # set[int]
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

# ----------------------------------------------------------------- stratégie
def pick_vehicle(n_veh: int, mode: str) -> str:
    """Décide quel type envoyer à la position n_veh (déjà envoyés)."""
    if mode == "single":                 # toujours le même camion
        return "type_I"
    if mode == "eco":                    # I I I I II …
        return "type_II" if n_veh % 5 == 4 else "type_I"
    # mode == "speed"                    # II II I I …
    return "type_II" if n_veh < 2 else "type_I"

# ----------------------------------------------------------------- simulation
def simulate(neigh: str, cfg: str | None):
    folder = os.path.join(ROOT, neigh)
    G      = load_graph(folder)
    snowy  = snowy_nodes(G)
    init_snow = set(snowy)

    # ----------- choix de la stratégie ----------------------------------
    print("\nChoisir la stratégie :")
    print("1. Moins chère possible (un seul véhicule type I, boucle)")
    print("2. Économie d’argent (flotte majoritairement type I)")
    print("3. Rapidité d’intervention (démarrage en type II)")
    while True:
        sel = input("Choix (1-3) ? ").strip()
        if sel in {"1", "2", "3"}:
            mode = {"1": "single", "2": "eco", "3": "speed"}[sel]
            break
        print("Entrée invalide.")

    cfg_file = cfg if cfg and os.path.exists(cfg) else None
    start    = next(iter(G.nodes))

    # ---------------- accumulateurs globaux -----------------------------
    n_total = n_I = n_II = 0
    dist_total = dur_total = cost_total = 0.0
    cleared, visited = set(), set()

    # ---------------- boucle flotte ------------------------------------
    while snowy:
        veh_key = pick_vehicle(n_total, mode)
        VehCls  = VEH[veh_key]

        # décompte des véhicules
        if mode == "single":
            if n_total == 0:            # premier et unique enregistrement
                n_total = n_I = 1
        else:
            n_total += 1
            if veh_key == "type_I":  n_I  += 1
            if veh_key == "type_II": n_II += 1

        agent = VehCls(start, config_path=cfg_file)

        # lever toutes les limites si mode "single" (le camion tourne tant qu'il reste de la neige)
        if mode == "single":
            agent.max_hours     = math.inf
            agent.fuel_capacity = math.inf
            agent.snow_capacity = math.inf
            agent.max_steps     = math.inf

        # ---------------- tournée du camion ----------------------------
        while agent.can_continue():
            nxt = agent.choose_next(G, snowy)
            if nxt is None:
                break
            ed = G[agent.current][nxt]
            length_m = (ed if isinstance(ed, dict) else next(iter(ed.values()))).get("length", 1.0)
            agent.move_to(nxt, length_m)
            visited.add(nxt)
            if G.nodes[nxt].get("snow", False):
                G.nodes[nxt]["snow"] = False
                snowy.discard(nxt); cleared.add(nxt)
                agent.snow_cleared += 1

        # ---------------- agrégation -----------------------------------
        st = agent.log_stats()
        dist_total += st["distance_km"]
        dur_total  += st["time_h"]
        cost_total += agent.compute_cost()

        if mode == "single" and not snowy:
            # boucle terminée : aucune neige restante
            break

    # ---------------- statistiques finales -----------------------------
    stats = {
        "vehicles_used": n_total,
        "type_I_used":   n_I,
        "type_II_used":  n_II,
        "snow_cleared":  len(cleared),
        "coverage_pct":  round(100*len(cleared)/len(init_snow), 2) if init_snow else 0,
        "visited_nodes": len(visited),
        "visit_pct":     round(100*len(visited)/G.number_of_nodes(), 2),
        "distance_km":   round(dist_total, 2),
        "time_h":        round(dur_total, 2),
        "cost_total":    round(cost_total, 2),
        "strategy":      mode,
    }

    # ---------------- rapport cumulatif ---------------------------------
    rec = {"timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
           "neighborhood": neigh, "stats": stats}
    try:
        data = json.loads(REPORT.read_text()) if REPORT.exists() else []
    except json.JSONDecodeError:
        data = []
    data.append(rec)
    REPORT.write_text(json.dumps(data, indent=2))

    # ---------------- sortie console -----------------------------------
    print(
        f"{neigh} | neige {stats['snow_cleared']} nœuds | cover {stats['coverage_pct']} % | "
        f"visit {stats['visit_pct']} % ({stats['visited_nodes']} nœuds) | "
        f"véh {n_total} (I:{n_I} / II:{n_II}) | dist {stats['distance_km']} km | "
        f"durée {stats['time_h']} h | coût {stats['cost_total']} €"
    )


# ------------------------------------------------------------------- CLI
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", default="vehicle/config.json",
                    help="fichier JSON de configuration")
    simulate(prompt(os.listdir(ROOT), "Quartier ? "), ap.parse_args().config)
