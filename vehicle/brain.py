import random
import json
import networkx as nx


class VehicleAgent:
    # ------------------------------------------------------------------ #
    #  INITIALISATION                                                    #
    # ------------------------------------------------------------------ #
    def __init__(self, start_node: int, config_path: str):
        with open(config_path) as f:
            cfg = json.load(f)

        self.current_node = start_node
        self.start_node = start_node

        self.memory_size = cfg["memory_size"]
        self.fuel_capacity = cfg["fuel_capacity"]
        self.fuel_per_meter = cfg["fuel_per_meter"]
        self.snow_capacity = cfg["snow_capacity"]
        self.return_to_base = cfg.get("return_to_base", False)

        self.distance_traveled = 0.0
        self.memory = []
        self.path = [start_node]

        self.planned_route = []   # [(u,v), …]
        self.route_index = 0

        self.steps_taken = 0
        self.snow_cleared = 0
        self.fuel_used = 0.0

    # ================================================================== #
    #  1.  PLANIFICATION – circuit du postier chinois dirigé             #
    # ================================================================== #
    def chinese_postman_route(self, G):
        G_un = G.to_undirected()
        G_eu_un = nx.eulerize(G_un)

        G_eu_dir = nx.MultiDiGraph()
        G_eu_dir.add_nodes_from(G.nodes(data=True))

        for u, v in G_eu_un.edges():
            if G.has_edge(u, v):
                for k, d in G[u][v].items():
                    G_eu_dir.add_edge(u, v, **d)
            elif G.has_edge(v, u):
                for k, d in G[v][u].items():
                    G_eu_dir.add_edge(v, u, **d)
            else:
                G_eu_dir.add_edge(u, v, length=G_eu_un[u][v].get("length", 1))

        circuit = list(nx.eulerian_circuit(G_eu_un, source=self.current_node))

        walk = []
        for u, v in circuit:
            if G.has_edge(u, v):
                walk.append((u, v))
            else:
                try:
                    sp = nx.shortest_path(G, u, v, weight="length")
                    walk.extend([(sp[i], sp[i + 1]) for i in range(len(sp) - 1)])
                except nx.NetworkXNoPath:
                    walk.append((u, v))
        return walk

    def plan_route(self, G):
        if self.planned_route:
            return True
        self.planned_route = self.chinese_postman_route(G)
        self.route_index = 0
        print(f"🧭  Route planifiée : {len(self.planned_route)} segments")
        return len(self.planned_route) > 0

    # ================================================================== #
    #  2.  CHOIX DU PROCHAIN NŒUD                                        #
    # ================================================================== #
    def observe(self, G):
        return list(G[self.current_node])

    def choose_next(self, G):
        """
        1️⃣  Suivre la route planifiée,  
        2️⃣  sinon heuristique locale (priorité neige).  
        La *sécurité adjacence* en fin de méthode garantit que le nœud choisi
        est toujours un vrai voisin ; sinon on renvoie le premier pas d’un
        plus court chemin.
        """
        # --- suivre la route planifiée -------------------------------- #
        if not self.planned_route and not self.plan_route(G):
            return self._choose_next_fallback(G)

        if self.route_index < len(self.planned_route):
            u_exp, v_next = self.planned_route[self.route_index]
            if self.current_node == u_exp:
                self.route_index += 1
                candidate = v_next
            else:
                # resynchronisation
                candidate = None
                for i in range(self.route_index, len(self.planned_route)):
                    if self.planned_route[i][0] == self.current_node:
                        self.route_index = i + 1
                        candidate = self.planned_route[i][1]
                        break
                if candidate is None:
                    candidate = self._choose_next_fallback(G)
        else:
            candidate = self._choose_next_fallback(G)

        # ----------- 🔒  Sécurité : doit être adjacent ---------------- #
        if candidate is not None and not G.has_edge(self.current_node, candidate):
            # prendre le premier pas d’un plus court chemin légal
            try:
                sp = nx.shortest_path(G, self.current_node, candidate, weight="length")
                if len(sp) >= 2:
                    candidate = sp[1]
            except nx.NetworkXNoPath:
                candidate = None

        return candidate

    def _choose_next_fallback(self, G):
        neighbors = self.observe(G)
        if not neighbors:
            return None
        random.shuffle(neighbors)

        for neigh in neighbors:
            data = G[self.current_node][neigh]
            if isinstance(data, dict):
                if any(data[k].get("snow", False) for k in data):
                    return neigh
            elif data.get("snow", False):
                return neigh
        return neighbors[0]

    # ================================================================== #
    #  3.  MISE À JOUR APRÈS DÉPLACEMENT                                 #
    # ================================================================== #
    def move_to(self, next_node, edge_length):
        if self.memory_size > 0:
            self.memory.append((self.current_node, next_node))
            if len(self.memory) > self.memory_size:
                self.memory.pop(0)

        self.path.append(next_node)
        self.current_node = next_node
        self.steps_taken += 1
        self.fuel_used += edge_length * self.fuel_per_meter
        self.distance_traveled += edge_length

    # ================================================================== #
    #  4.  CONDITIONS D’ARRÊT                                            #
    # ================================================================== #
    def can_continue(self):
        return (
            self.fuel_used < self.fuel_capacity
            and self.snow_cleared < self.snow_capacity
        )

    # ================================================================== #
    #  5.  LOG STATISTIQUES                                              #
    # ================================================================== #
    def log_stats(self):
        return {
            "steps_taken": self.steps_taken,
            "snow_cleared": self.snow_cleared,
            "fuel_used": round(self.fuel_used, 2),
            "fuel_capacity": self.fuel_capacity,
            "path_length": len(self.path),
            "ended_at": self.current_node,
            "planned_route_length": len(self.planned_route),
            "route_completion": round(
                (self.route_index / len(self.planned_route)) * 100, 2
            )
            if self.planned_route
            else 0,
        }

