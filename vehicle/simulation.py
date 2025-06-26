# simulate_vehicle.py
import os
import csv
import json
import pickle
import networkx as nx
from brain import VehicleAgent
from vehicles import VehicleTypeI, VehicleTypeII, SuperDrone


def prompt_for_neighborhood():
    root_dir = "resources/neighborhoods"
    neighborhoods = [n for n in os.listdir(root_dir)
                     if os.path.isdir(os.path.join(root_dir, n))]

    print("\n📍 Available neighborhoods:")
    for idx, name in enumerate(neighborhoods):
        print(f"{idx + 1}. {name}")

    while True:
        try:
            choice = int(input("Choose a neighborhood (number): "))
            if 1 <= choice <= len(neighborhoods):
                return neighborhoods[choice - 1]
        except ValueError:
            pass
        print("❌ Invalid input. Please enter a valid number.")

def load_graph_with_snow(input_dir):
    graph_path = os.path.join(input_dir, "eulerized_graph.pkl")
    snow_path = os.path.join(input_dir, "snow_map.csv")

    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    for u, v, key in G.edges(keys=True):
        G[u][v][key]['snow'] = False

    with open(snow_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            u, v, snow = int(row['u']), int(row['v']), int(row['snow'])
            if snow == 1:
                if G.has_edge(u, v):
                    for key in G[u][v]:
                        G[u][v][key]['snow'] = True
                elif G.has_edge(v, u):
                    for key in G[v][u]:
                        G[v][u][key]['snow'] = True

    return G

def simulate():
    neighborhood = prompt_for_neighborhood()
    input_dir = os.path.join("resources/neighborhoods", neighborhood)
    config_path = "vehicle/config.json"

    cleared_csv = os.path.join(input_dir, "vehicle_cleared.csv")
    path_json = os.path.join(input_dir, "vehicle_path.json")
    stats_json = os.path.join(input_dir, "vehicle_stats.json")

    G = load_graph_with_snow(input_dir)
    start_node = list(G.nodes())[0]

    AgentClass = prompt_for_agent_type()
    agent = AgentClass(start_node, config_path)

    cleared_edges = set()

    while agent.can_continue():
        next_node = agent.choose_next(G)
        if not next_node:
            break

        u, v = agent.current_node, next_node
        edge_data = G[u][v][0] if isinstance(G[u][v], dict) else G[u][v]
        length = edge_data.get("length", 1.0)

        if any(G[u][v][key].get("snow", False) for key in G[u][v]):
            for key in G[u][v]:
                if G[u][v][key].get("snow", False):
                    cleared_edges.add((u, v))
                    G[u][v][key]["snow"] = False
                    agent.snow_cleared += 1

        agent.move_to(next_node, length)

    with open(cleared_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["u", "v"])
        writer.writerows(cleared_edges)

    with open(path_json, "w") as f:
        json.dump(agent.path, f)

    with open(stats_json, "w") as f:
        json.dump(agent.log_stats(), f, indent=2)

    print(f"\n✅ Simulation completed for: {neighborhood}")
    print(f"🧹 Cleared snow on {agent.snow_cleared} edges in {agent.steps_taken} steps")
    print(f"⛽ Fuel used: {agent.fuel_used:.2f}/{agent.fuel_capacity}")
    print(f"\n cost : {agent.compute_cost()}")
    print(f"\n distance traveled : {agent.distance_traveled}")

def prompt_for_agent_type():
    print("\n🚗 Choose vehicle type:")
    print("1. Vehicle Type I")
    print("2. Vehicle Type II")
    print("3. Super Drone")

    while True:
        try:
            choice = int(input("Enter choice (1-3): "))
            if choice == 1:
                return VehicleTypeI
            elif choice == 2:
                return VehicleTypeII
            elif choice == 3:
                return SuperDrone
        except ValueError:
            pass
        print("❌ Invalid input. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    simulate()

