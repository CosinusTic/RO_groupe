import json, heapq, networkx as nx
from typing import Dict, Optional


class VehicleAgent:
    """Navigation : toujours vers le nœud enneigé le plus proche."""

    # ---------------------------------------------------------------- init
    def __init__(self, start: int, config: Optional[str] = "config.json") -> None:
        cfg: Dict[str, float] = {}
        if config:
            try:
                with open(config, encoding="utf-8") as f:
                    cfg = json.load(f)
            except FileNotFoundError:
                pass
        p = (cfg.get("vehicle_types", {})
                .get(cfg.get("selected_vehicle"), cfg)).copy()
        p.update(cfg.get("overrides", {}))

        # paramètres opérationnels
        self.memory_size    = p.get("memory_size",    10)
        self.fuel_capacity  = p.get("fuel_capacity",  5_000)
        self.fuel_per_meter = p.get("fuel_per_meter", 0.25)
        self.snow_capacity  = p.get("snow_capacity",  300)
        self.speed_kmph     = p.get("speed_kmph",     15)
        self.max_hours      = p.get("max_hours",      12)
        self.max_steps      = p.get("max_steps",      4_000)

        # coût kilométrique (unique variable côté agent)
        self.cost_km        = p.get("cost_km", 1.2)

        # état dynamique
        self.current  = start
        self.memory   = []
        self.path     = [start]

        self.steps = self.snow_cleared = 0
        self.fuel_used = self.dist_m = self.time_h = 0.0

    # ---------------------------------------------------------- décision
    def _shortest_to_snow(self, G: nx.Graph, snowy: set[int]) -> Optional[int]:
        if not snowy:
            return None
        d, _ = nx.single_source_dijkstra(
            G, self.current, weight=lambda u, v, ed: ed.get("length", 1)
        )
        targets = [n for n in snowy if n in d]
        if not targets:
            return None
        target = min(targets, key=d.get)
        # reconstruction du premier pas
        pred = {self.current: None}
        pq, seen = [(0, self.current)], set()
        while pq:
            dist, u = heapq.heappop(pq)
            if u in seen:
                continue
            seen.add(u)
            if u == target:
                break
            for v, ed in G[u].items():
                w = ed.get("length", 1)
                if v not in pred:
                    pred[v] = u
                    heapq.heappush(pq, (dist + w, v))
        nxt = target
        while pred[nxt] != self.current:
            nxt = pred[nxt]
        return nxt

    def choose_next(self, G: nx.Graph, snowy: set[int]) -> Optional[int]:
        for n in sorted(G[self.current]):
            if G.nodes[n].get("snow", False):
                return n
        return self._shortest_to_snow(G, snowy)

    # ---------------------------------------------------------- mouvement
    def move_to(self, nxt: int, length_m: float):
        self.memory.append((self.current, nxt))
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
        self.current = nxt
        self.path.append(nxt)

        self.steps      += 1
        self.fuel_used  += length_m * self.fuel_per_meter
        self.dist_m     += length_m
        self.time_h     += (length_m / 1_000) / self.speed_kmph

    # ---------------------------------------------------------- arrêt
    def can_continue(self) -> bool:
        return (self.steps        < self.max_steps     and
                self.fuel_used    < self.fuel_capacity and
                self.snow_cleared < self.snow_capacity and
                self.time_h       < self.max_hours)

    # ---------------------------------------------------------- métriques
    @property
    def distance_km(self) -> float:        # utilisé par simulation.py
        return self.dist_m / 1_000

    # ---------------------------------------------------------- log
    def log_stats(self) -> Dict[str, float]:
        return {
            "steps":        self.steps,
            "snow_cleared": self.snow_cleared,
            "distance_km":  round(self.distance_km, 2),
            "time_h":       round(self.time_h, 2),
            "fuel_used":    round(self.fuel_used, 2),
        }
