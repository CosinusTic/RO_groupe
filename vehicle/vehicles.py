from brain import VehicleAgent

class VehicleTypeI(VehicleAgent):
    def __init__(self, start_node, config_path):
        super().__init__(start_node, config_path)
        self.fixed_cost = 500
        self.km_cost = 1.1
        self.hour_cost_first_8 = 1.1
        self.hour_cost_after_8 = 1.3
        self.speed_kmph = 10

    def compute_cost(self):
        distance_km = self.distance_traveled
        hours = distance_km / self.speed_kmph
        if hours <= 8:
            hourly_cost = self.hour_cost_first_8 * hours
        else:
            hourly_cost = self.hour_cost_first_8 * 8 + self.hour_cost_after_8 * (hours - 8)
        return round(self.fixed_cost + self.km_cost * distance_km + hourly_cost, 2)


class VehicleTypeII(VehicleAgent):
    def __init__(self, start_node, config_path):
        super().__init__(start_node, config_path)
        self.fixed_cost = 800
        self.km_cost = 1.3
        self.hour_cost_first_8 = 1.3
        self.hour_cost_after_8 = 1.5
        self.speed_kmph = 20

    def compute_cost(self):
        distance_km = self.distance_traveled
        hours = distance_km / self.speed_kmph
        if hours <= 8:
            hourly_cost = self.hour_cost_first_8 * hours
        else:
            hourly_cost = self.hour_cost_first_8 * 8 + self.hour_cost_after_8 * (hours - 8)
        return round(self.fixed_cost + self.km_cost * distance_km + hourly_cost, 2)


class SuperDrone(VehicleAgent):
    def __init__(self, start_node, config_path):
        super().__init__(start_node, config_path)
        self.fixed_cost = 100
        self.km_cost = 0.01

    def compute_cost(self):
        distance_km = self.distance_traveled
        return round(self.fixed_cost + self.km_cost * distance_km, 2)
