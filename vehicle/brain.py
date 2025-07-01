import random
import json
import networkx as nx
from itertools import combinations

class VehicleAgent:
    def __init__(self, start_node, config_path):
        with open(config_path) as f:
            config = json.load(f)

        self.current_node = start_node
        self.start_node = start_node
        self.memory_size = config["memory_size"]
        self.fuel_capacity = config["fuel_capacity"]
        self.fuel_per_meter = config["fuel_per_meter"]
        self.snow_capacity = config["snow_capacity"]
        self.return_to_base = config.get("return_to_base", False)

        self.distance_traveled = 0.0

        self.memory = []
        self.path = [start_node]
        self.planned_route = []  # Route calculée par le postier chinois
        self.route_index = 0     # Index actuel dans la route

        # Stats
        self.steps_taken = 0
        self.snow_cleared = 0
        self.fuel_used = 0.0

    def chinese_postman_route(self, G):
        """
        Calcule la route optimale du postier chinois pour parcourir toutes les arêtes
        """
        # Créer une copie du graphe pour les calculs
        graph_copy = G.copy()

        # Étape 1: Vérifier si le graphe est eulérien
        odd_degree_nodes = [node for node in graph_copy.nodes()
                            if graph_copy.degree(node) % 2 == 1]

        if not odd_degree_nodes:
            # Le graphe est déjà eulérien, on peut faire un circuit eulérien
            try:
                return list(nx.eulerian_circuit(graph_copy, source=self.current_node))
            except nx.NetworkXError:
                # Fallback si le circuit eulérien échoue
                return self._fallback_route(graph_copy)

        # Étape 2: Trouver les paires de nœuds de degré impair avec distance minimale
        min_weight_pairs = self._find_minimum_weight_matching(graph_copy, odd_degree_nodes)

        # Étape 3: Ajouter les arêtes nécessaires pour rendre le graphe eulérien
        for node1, node2 in min_weight_pairs:
            # Trouver le plus court chemin entre les nœuds
            try:
                shortest_path = nx.shortest_path(graph_copy, node1, node2, weight='length')
                # Ajouter les arêtes du plus court chemin
                for i in range(len(shortest_path) - 1):
                    u, v = shortest_path[i], shortest_path[i + 1]
                    if graph_copy.has_edge(u, v):
                        # Dupliquer l'arête existante
                        edge_data = graph_copy[u][v][0].copy() if isinstance(graph_copy[u][v], dict) else {}
                        graph_copy.add_edge(u, v, **edge_data)
                    else:
                        # Ajouter une nouvelle arête (ne devrait pas arriver dans un graphe connexe)
                        graph_copy.add_edge(u, v, length=1.0, snow=False)
            except nx.NetworkXNoPath:
                continue

        # Étape 4: Calculer le circuit eulérien
        try:
            return list(nx.eulerian_circuit(graph_copy, source=self.current_node))
        except nx.NetworkXError:
            return self._fallback_route(graph_copy)

    def _find_minimum_weight_matching(self, G, odd_nodes):
        """
        Trouve l'appariement de poids minimum entre les nœuds de degré impair
        """
        if len(odd_nodes) % 2 != 0:
            # Ne devrait pas arriver dans un graphe eulérisé, mais au cas où
            odd_nodes = odd_nodes[:-1]

        if len(odd_nodes) == 0:
            return []

        # Calculer toutes les distances entre paires de nœuds impairs
        distances = {}
        for i, node1 in enumerate(odd_nodes):
            for j, node2 in enumerate(odd_nodes):
                if i < j:
                    try:
                        dist = nx.shortest_path_length(G, node1, node2, weight='length')
                        distances[(node1, node2)] = dist
                    except nx.NetworkXNoPath:
                        distances[(node1, node2)] = float('inf')

        # Trouver l'appariement de poids minimum (algorithme simple pour petits graphes)
        return self._minimum_weight_perfect_matching(odd_nodes, distances)

    def _minimum_weight_perfect_matching(self, nodes, distances):
        """
        Algorithme simple pour trouver l'appariement parfait de poids minimum
        """
        n = len(nodes)
        if n == 0:
            return []
        if n == 2:
            return [(nodes[0], nodes[1])]

        min_cost = float('inf')
        best_matching = []

        # Générer tous les appariements parfaits possibles
        def generate_matchings(remaining_nodes):
            if len(remaining_nodes) == 0:
                return [[]]
            if len(remaining_nodes) == 2:
                return [[(remaining_nodes[0], remaining_nodes[1])]]

            matchings = []
            first = remaining_nodes[0]
            for i in range(1, len(remaining_nodes)):
                partner = remaining_nodes[i]
                rest = remaining_nodes[1:i] + remaining_nodes[i+1:]
                for sub_matching in generate_matchings(rest):
                    matchings.append([(first, partner)] + sub_matching)
            return matchings

        # Évaluer tous les appariements
        for matching in generate_matchings(nodes):
            cost = sum(distances.get((min(pair), max(pair)), float('inf')) for pair in matching)
            if cost < min_cost:
                min_cost = cost
                best_matching = matching

        return best_matching

    def _fallback_route(self, G):
        """
        Route de secours si l'algorithme du postier chinois échoue
        """
        edges = list(G.edges())
        if not edges:
            return []

        # Créer une route simple qui visite toutes les arêtes
        route = []
        current = self.current_node
        visited_edges = set()

        while len(visited_edges) < len(edges):
            # Trouver une arête non visitée depuis le nœud actuel
            found = False
            for neighbor in G[current]:
                edge_key = (min(current, neighbor), max(current, neighbor))
                if edge_key not in visited_edges:
                    route.append((current, neighbor))
                    visited_edges.add(edge_key)
                    current = neighbor
                    found = True
                    break

            if not found:
                # Se déplacer vers un nœud avec des arêtes non visitées
                for edge in edges:
                    edge_key = (min(edge[0], edge[1]), max(edge[0], edge[1]))
                    if edge_key not in visited_edges:
                        # Aller vers ce nœud (chemin le plus court)
                        try:
                            path_to_edge = nx.shortest_path(G, current, edge[0])
                            for i in range(len(path_to_edge) - 1):
                                route.append((path_to_edge[i], path_to_edge[i + 1]))
                            current = edge[0]
                            break
                        except nx.NetworkXNoPath:
                            continue
                else:
                    break

        return route

    def plan_route(self, G):
        """
        Planifie la route complète en utilisant l'algorithme du postier chinois
        """
        print(f"🧭 Planification de la route avec l'algorithme du postier chinois...")
        self.planned_route = self.chinese_postman_route(G)
        self.route_index = 0
        print(f"✅ Route planifiée: {len(self.planned_route)} segments")
        return len(self.planned_route) > 0

    def observe(self, G):
        return list(G[self.current_node])

    def choose_next(self, G):
        """
        Choisit le prochain nœud selon la route planifiée du postier chinois
        """
        # Si pas de route planifiée, la planifier
        if not self.planned_route:
            if not self.plan_route(G):
                # Fallback vers l'ancien comportement
                return self._choose_next_fallback(G)

        # Suivre la route planifiée
        if self.route_index < len(self.planned_route):
            current_edge = self.planned_route[self.route_index]
            expected_current = current_edge[0]
            next_node = current_edge[1]

            # Vérifier si on est au bon nœud
            if self.current_node == expected_current:
                self.route_index += 1
                return next_node
            else:
                # Essayer de se repositionner
                if self.current_node == next_node and self.route_index > 0:
                    # On est peut-être sur l'arête précédente dans l'autre sens
                    prev_edge = self.planned_route[self.route_index - 1]
                    if prev_edge[1] == next_node and prev_edge[0] == expected_current:
                        self.route_index += 1
                        if self.route_index < len(self.planned_route):
                            return self.planned_route[self.route_index][1]

                # Chercher dans la route où on devrait être
                for i in range(self.route_index, len(self.planned_route)):
                    if self.planned_route[i][0] == self.current_node:
                        self.route_index = i + 1
                        return self.planned_route[i][1]

        # Si on a terminé la route ou si il y a un problème, fallback
        return self._choose_next_fallback(G)

    def _choose_next_fallback(self, G):
        """
        Comportement de fallback (ancien algorithme)
        """
        neighbors = self.observe(G)
        if not neighbors:
            return None

        random.shuffle(neighbors)

        # Priorité aux arêtes avec de la neige non visitées
        for neighbor in neighbors:
            if G.has_edge(self.current_node, neighbor):
                edge_data = G[self.current_node][neighbor]
                if isinstance(edge_data, dict):
                    # Multigraphe
                    for key in edge_data:
                        if edge_data[key].get("snow", False):
                            edge = (self.current_node, neighbor)
                            if edge not in self.memory and (neighbor, self.current_node) not in self.memory:
                                return neighbor
                else:
                    # Graphe simple
                    if edge_data.get("snow", False):
                        edge = (self.current_node, neighbor)
                        if edge not in self.memory and (neighbor, self.current_node) not in self.memory:
                            return neighbor

        # Arêtes non visitées
        for neighbor in neighbors:
            edge = (self.current_node, neighbor)
            if edge not in self.memory and (neighbor, self.current_node) not in self.memory:
                return neighbor

        # Dernier recours
        return neighbors[0]

    def has_snow_remaining(self, G):
        """
        Vérifie s'il reste encore de la neige à déneiger dans le graphe
        """
        for u, v, key in G.edges(keys=True):
            if G[u][v][key].get('snow', False):
                return True
        return False

    def move_to(self, next_node, edge_length):
        edge = (self.current_node, next_node)
        self.memory.append(edge)
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)

        self.path.append(next_node)
        self.current_node = next_node
        self.steps_taken += 1
        self.fuel_used += edge_length * self.fuel_per_meter
        self.distance_traveled += edge_length

    def can_continue(self, G=None):
        if self.fuel_used >= self.fuel_capacity:
            return False
        if self.snow_cleared >= self.snow_capacity:
            return False

        # Si le graphe est fourni, vérifier s'il reste de la neige
        if G is not None and not self.has_snow_remaining(G):
            return False

        return True

    def log_stats(self):
        return {
            "steps_taken": self.steps_taken,
            "snow_cleared": self.snow_cleared,
            "fuel_used": round(self.fuel_used, 2),
            "fuel_capacity": self.fuel_capacity,
            "path_length": len(self.path),
            "ended_at": self.current_node,
            "planned_route_length": len(self.planned_route),
            "route_completion": round((self.route_index / len(self.planned_route)) * 100, 2) if self.planned_route else 0
        }