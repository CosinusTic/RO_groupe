import json, os, tempfile, networkx as nx
from brain import VehicleAgent

MINI_CFG = {
    "vehicle_types": {
        "T": {"memory_size": 2, "fuel_capacity": 10, "fuel_per_meter": 1,
              "snow_capacity": 3, "speed_kmph": 10,
              "cost_fixed": 0, "cost_km": 0, "cost_hour_first": 0,
              "cost_hour_after": 0, "hour_breakpoint": 8}
    },
    "selected_vehicle": "T"
}

def build_graph():
    G = nx.MultiGraph()
    G.add_edge(0, 1, snow=True, length=100)
    G.add_edge(1, 2, snow=False, length=100)
    return G

def test_choose_next_prefers_snow():
    with tempfile.NamedTemporaryFile("w+", delete=False) as fp:
        json.dump(MINI_CFG, fp); fp.flush()
        G = build_graph()
        agent = VehicleAgent(0, fp.name)
        nxt = agent.choose_next(G)
        assert nxt == 1, "Doit choisir l’arête enneigée en priorité"
