# simulate_vehicle.py
import os
import csv
import json
import pickle
import networkx as nx
from brain import VehicleAgent
from vehicles import VehicleTypeI, VehicleTypeII


def prompt_for_neighborhood():
    root_dir = "resources/"
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

def estimate_total_snow_edges(G):
    """Estime le nombre total d'arêtes avec de la neige"""
    snow_edges = 0
    for u, v, key in G.edges(keys=True):
        if G[u][v][key].get('snow', False):
            snow_edges += 1
    return snow_edges

def has_snow_remaining(G):
    """Vérifie s'il reste de la neige dans le graphe"""
    for u, v, key in G.edges(keys=True):
        if G[u][v][key].get('snow', False):
            return True
    return False

def calculate_vehicle_distribution(strategy, budget=None, total_snow_edges=0):
    """Calcule la distribution optimale des véhicules selon la stratégie"""
    if strategy == "economie_argent":
        # Un seul véhicule Type I (le moins cher) pour minimiser les coûts
        return 1, 0

    elif strategy == "economie_temps":
        # Optimiser le temps en respectant strictement le budget
        return optimize_for_time_with_budget(budget, total_snow_edges)

def optimize_for_time_with_budget(budget, total_snow_edges):
    """Optimise le nombre de véhicules pour minimiser le temps en respectant le budget"""
    # Coûts fixes des véhicules
    type1_fixed_cost = 500
    type2_fixed_cost = 800

    # Estimation grossière : 1 véhicule peut traiter ~50 arêtes, ~100km, ~10h
    edges_per_vehicle = 50
    km_per_vehicle = 100

    # Coût estimé par véhicule (fixe + variable)
    type1_estimated_cost = type1_fixed_cost + (1.1 * km_per_vehicle) + (1.1 * 8 + 1.3 * 2)  # ~8h + 2h sup
    type2_estimated_cost = type2_fixed_cost + (1.3 * km_per_vehicle) + (1.3 * 5)  # 5h (plus rapide)

    best_time = float('inf')
    best_config = (1, 0)  # Au minimum 1 véhicule Type I

    max_vehicles = min(10, int(budget // type1_estimated_cost))

    for num_type1 in range(0, max_vehicles + 1):
        for num_type2 in range(0, max_vehicles + 1):
            if num_type1 + num_type2 == 0:
                continue

            # Estimation du coût total
            estimated_cost = (num_type1 * type1_estimated_cost +
                              num_type2 * type2_estimated_cost)

            if estimated_cost > budget:
                continue

            # Estimation du temps (limité par le véhicule le plus lent)
            # Répartition du travail entre les véhicules
            total_vehicles = num_type1 + num_type2
            edges_per_this_config = total_snow_edges / total_vehicles
            km_per_this_config = edges_per_this_config * 2  # Estimation

            time_type1 = km_per_this_config / 10 if num_type1 > 0 else 0  # 10 km/h
            time_type2 = km_per_this_config / 20 if num_type2 > 0 else 0  # 20 km/h

            max_time = max(time_type1, time_type2)

            if max_time < best_time:
                best_time = max_time
                best_config = (num_type1, num_type2)

    return best_config

def prompt_for_strategy():
    """Demande à l'utilisateur de choisir une stratégie d'optimisation"""
    print("\n🎯 Choose optimization strategy:")
    print("1. Économie d'argent (priorité au coût minimal)")
    print("2. Économie de temps (avec budget maximal)")

    while True:
        try:
            choice = int(input("Enter choice (1-2): "))
            if choice == 1:
                return "economie_argent", None
            elif choice == 2:
                while True:
                    try:
                        budget = float(input("💰 Quel est le budget maximal ? : "))
                        if budget > 0:
                            return "economie_temps", budget
                        else:
                            print("❌ Le budget doit être positif.")
                    except ValueError:
                        print("❌ Veuillez entrer un nombre valide.")
        except ValueError:
            pass
        print("❌ Invalid input. Please enter 1 or 2.")

def simulate_vehicle(vehicle_class, start_node, config_path, G_shared, vehicle_id):
    """Simule un véhicule individuel sur le graphe partagé"""
    agent = vehicle_class(start_node, config_path)
    cleared_edges = set()

    while agent.can_continue():
        # Vérifier s'il reste de la neige dans le graphe
        if not has_snow_remaining(G_shared):
            print(f"      ❄️ Plus de neige détectée - Arrêt du véhicule {vehicle_id}")
            break

        next_node = agent.choose_next(G_shared)
        if not next_node:
            break

        u, v = agent.current_node, next_node
        edge_data = G_shared[u][v][0] if isinstance(G_shared[u][v], dict) else G_shared[u][v]
        length = edge_data.get("length", 1.0)

        # Vérifier et déneiger les arêtes (sur le graphe partagé)
        if any(G_shared[u][v][key].get("snow", False) for key in G_shared[u][v]):
            for key in G_shared[u][v]:
                if G_shared[u][v][key].get("snow", False):
                    cleared_edges.add((u, v))
                    # Déneiger sur le graphe partagé - tous les véhicules verront ce changement
                    G_shared[u][v][key]["snow"] = False
                    agent.snow_cleared += 1

        agent.move_to(next_node, length)

    return agent, cleared_edges

def simulate():
    neighborhood = prompt_for_neighborhood()
    input_dir = os.path.join("resources/", neighborhood)
    config_path = "vehicle/config.json"

    # Chemins de sortie
    cleared_csv = os.path.join(input_dir, "vehicle_cleared.csv")
    path_json = os.path.join(input_dir, "vehicle_path.json")
    stats_json = os.path.join(input_dir, "vehicle_stats.json")

    # Charger le graphe
    G = load_graph_with_snow(input_dir)
    start_node = list(G.nodes())[0]

    # Estimer le travail total
    total_snow_edges = estimate_total_snow_edges(G)

    # Choisir la stratégie
    strategy, budget = prompt_for_strategy()

    # Calculer la distribution des véhicules
    num_type1, num_type2 = calculate_vehicle_distribution(strategy, budget, total_snow_edges)

    print(f"\n🚗 Distribution optimale des véhicules:")
    if strategy == "economie_argent":
        print(f"   💰 Stratégie économie d'argent: 1 seul véhicule Type I (optimal)")
    else:
        print(f"   ⏱️  Stratégie économie de temps avec budget {budget}€:")
    print(f"   - Véhicules Type I: {num_type1}")
    print(f"   - Véhicules Type II: {num_type2}")

    # Simulation des véhicules sur le graphe partagé
    all_agents = []
    all_cleared_edges = set()
    all_paths = {}

    print(f"\n🚧 Début de la simulation...")

    # Simuler les véhicules Type I
    for i in range(num_type1):
        if not has_snow_remaining(G):
            print(f"   ❄️ Plus de neige - Arrêt des véhicules restants")
            break

        print(f"   🚗 Véhicule Type I #{i+1} en cours...")
        agent, cleared_edges = simulate_vehicle(VehicleTypeI, start_node, config_path, G, f"TypeI_{i+1}")
        all_agents.append(agent)
        all_cleared_edges.update(cleared_edges)
        all_paths[f"vehicle_typeI_{i+1}"] = agent.path
        print(f"      ✅ Terminé - {agent.snow_cleared} arêtes déneigées")

    # Simuler les véhicules Type II
    for i in range(num_type2):
        if not has_snow_remaining(G):
            print(f"   ❄️ Plus de neige - Arrêt des véhicules restants")
            break

        print(f"   🚛 Véhicule Type II #{i+1} en cours...")
        agent, cleared_edges = simulate_vehicle(VehicleTypeII, start_node, config_path, G, f"TypeII_{i+1}")
        all_agents.append(agent)
        all_cleared_edges.update(cleared_edges)
        all_paths[f"vehicle_typeII_{i+1}"] = agent.path
        print(f"      ✅ Terminé - {agent.snow_cleared} arêtes déneigées")

    # Vérifier s'il reste de la neige
    remaining_snow = estimate_total_snow_edges(G)
    if remaining_snow == 0:
        print(f"\n🎉 DÉNEIGEMENT TERMINÉ ! Toute la neige a été enlevée.")
    else:
        print(f"\n❄️  Neige restante: {remaining_snow} arêtes")

    # Calculs des statistiques globales
    total_cost = sum(agent.compute_cost() for agent in all_agents)
    total_snow_cleared = sum(agent.snow_cleared for agent in all_agents)
    total_distance = sum(agent.distance_traveled for agent in all_agents)
    total_fuel_used = sum(agent.fuel_used for agent in all_agents)

    # Le temps final est celui du véhicule le plus lent
    max_time = 0
    slowest_vehicle = None
    for agent in all_agents:
        vehicle_time = agent.distance_traveled / agent.speed_kmph
        if vehicle_time > max_time:
            max_time = vehicle_time
            slowest_vehicle = type(agent).__name__

    # Vérification stricte du budget si stratégie économie de temps
    budget_respected = True
    if strategy == "economie_temps" and budget:
        if total_cost > budget:
            budget_respected = False
            print(f"\n⚠️  ERREUR: Budget dépassé ! ({total_cost:.2f}€ > {budget}€)")
            print("La configuration n'est pas valide. Réessayez avec un budget plus élevé.")
        else:
            budget_respected = True

    # Sauvegarde des résultats
    with open(cleared_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["u", "v"])
        writer.writerows(all_cleared_edges)

    with open(path_json, "w") as f:
        json.dump(all_paths, f)

    # Statistiques détaillées
    detailed_stats = {
        "strategy": strategy,
        "budget": budget,
        "budget_respected": budget_respected,
        "snow_clearing_completed": remaining_snow == 0,
        "vehicle_distribution": {
            "type_I": num_type1,
            "type_II": num_type2
        },
        "global_stats": {
            "total_cost": round(total_cost, 2),
            "total_snow_cleared": total_snow_cleared,
            "remaining_snow": remaining_snow,
            "total_distance": round(total_distance, 2),
            "total_fuel_used": round(total_fuel_used, 2),
            "max_time_hours": round(max_time, 2),
            "slowest_vehicle_type": slowest_vehicle
        },
        "individual_vehicles": []
    }

    for i, agent in enumerate(all_agents):
        vehicle_stats = agent.log_stats()
        vehicle_stats["cost"] = agent.compute_cost()
        vehicle_stats["time_hours"] = round(agent.distance_traveled / agent.speed_kmph, 2)
        vehicle_stats["vehicle_type"] = type(agent).__name__
        detailed_stats["individual_vehicles"].append(vehicle_stats)

    with open(stats_json, "w") as f:
        json.dump(detailed_stats, f, indent=2)

    # Affichage des résultats
    print(f"\n✅ Simulation completed for: {neighborhood}")
    print(f"🎯 Stratégie: {strategy}")
    if strategy == "economie_temps" and budget:
        if budget_respected:
            print(f"💰 Budget: {budget}€ ✅ Respecté (coût réel: {total_cost:.2f}€)")
        else:
            print(f"💰 Budget: {budget}€ ❌ DÉPASSÉ (coût réel: {total_cost:.2f}€)")

    print(f"\n📊 RÉSULTATS GLOBAUX:")
    print(f"🧹 Neige nettoyée: {total_snow_cleared} arêtes")
    if remaining_snow == 0:
        print(f"🎉 Neige restante: {remaining_snow} arêtes - DÉNEIGEMENT COMPLET !")
    else:
        print(f"❄️  Neige restante: {remaining_snow} arêtes")
    print(f"💸 Coût total: {total_cost:.2f} €")
    print(f"📏 Distance totale: {total_distance:.2f} km")
    print(f"⛽ Carburant total: {total_fuel_used:.2f}")
    print(f"⏱️  Temps total: {max_time:.2f} heures (limité par {slowest_vehicle})")

    if strategy == "economie_argent":
        print(f"\n💡 Économie d'argent: Solution optimale avec 1 seul véhicule!")
    elif strategy == "economie_temps":
        print(f"\n💡 Économie de temps: {num_type1 + num_type2} véhicules pour minimiser le temps")

    print(f"\n🚗 DÉTAIL PAR VÉHICULE:")
    for i, agent in enumerate(all_agents):
        vehicle_time = agent.distance_traveled / agent.speed_kmph
        print(f"   {type(agent).__name__} #{i+1}:")
        print(f"      - Coût: {agent.compute_cost():.2f} €")
        print(f"      - Distance: {agent.distance_traveled:.2f} km")
        print(f"      - Temps: {vehicle_time:.2f} heures")
        print(f"      - Neige nettoyée: {agent.snow_cleared} arêtes")

    # -----------------------------------------------------------------
    # 🔄  AJOUT D’UN RÉSUMÉ DANS runs_summary.json
    # -----------------------------------------------------------------
    summary_obj = {
        "vehicles_used": len(all_agents),
        "snow_cleared": total_snow_cleared,
        "visited_nodes": len({n for p in all_paths.values() for n in p}),
        "distance_km": round(total_distance, 2),
        "time_h": round(max_time, 2),
        "cost_total": round(total_cost, 2),
        "strategy": "eco" if strategy == "economie_argent" else "time",
        "neighborhood": neighborhood
    }

    summary_file = "reports/all_runs.json"
    try:
        with open(summary_file, "r") as f:
            runs = json.load(f)
            if not isinstance(runs, list):
                raise ValueError
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        runs = []

    runs.append(summary_obj)

    with open(summary_file, "w") as f:
        json.dump(runs, f, indent=2)

    print(f"\n📝 Résumé ajouté dans {summary_file}")



if __name__ == "__main__":
    simulate()
