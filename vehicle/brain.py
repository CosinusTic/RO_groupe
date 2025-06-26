import random
import json

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

        self.memory = []
        self.path = [start_node]

        # Stats
        self.steps_taken = 0
        self.snow_cleared = 0
        self.fuel_used = 0.0

    def observe(self, G):
        return list(G[self.current_node])

    def choose_next(self, G):
        neighbors = self.observe(G)
        random.shuffle(neighbors)

        for neighbor in neighbors:
            edge = (self.current_node, neighbor)
            if G.has_edge(*edge) and G[self.current_node][neighbor].get("snow", False):
                if edge not in self.memory and (neighbor, self.current_node) not in self.memory:
                    return neighbor

        for neighbor in neighbors:
            edge = (self.current_node, neighbor)
            if edge not in self.memory:
                return neighbor

        return neighbors[0] if neighbors else None

    def move_to(self, next_node, edge_length):
        edge = (self.current_node, next_node)
        self.memory.append(edge)
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)

        self.path.append(next_node)
        self.current_node = next_node
        self.steps_taken += 1
        self.fuel_used += edge_length * self.fuel_per_meter

    def can_continue(self):
        if self.fuel_used >= self.fuel_capacity:
            return False
        if self.snow_cleared >= self.snow_capacity:
            return False
        return True

    def log_stats(self):
        return {
            "steps_taken": self.steps_taken,
            "snow_cleared": self.snow_cleared,
            "fuel_used": round(self.fuel_used, 2),
            "fuel_capacity": self.fuel_capacity,
            "path_length": len(self.path),
            "ended_at": self.current_node
        }

