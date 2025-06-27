"""Concrete vehicle classes built on top of VehicleAgent.
Each class hard‑codes its own economic parameters while re‑using the
navigation / state logic already implemented in VehicleAgent.
"""
from brain import VehicleAgent


class _BaseVehicle(VehicleAgent):
    """Shared helpers for concrete vehicle types."""

    @property
    def distance_m(self) -> float:
        """Alias pour compatibilité avec vehicles.py"""
        return self.dist_m

    @property
    def distance_km(self) -> float:
        """Alias équivalent à dist_km pour les sous-classes custom."""
        return self.dist_m / 1000


class VehicleTypeI(_BaseVehicle):
    """Slow and cheap vehicle (type I)."""

    def __init__(self, start_node, config_path="config.json"):
        super().__init__(start_node, config_path)
        self.fixed_cost = 500
        self.km_cost = 1.1
        self.fuel_capacity = 6_000
        self.snow_capacity = 400     
        self.hour_cost_first_8 = 1.1
        self.hour_cost_after_8 = 1.3
        self.speed_kmph = 10  # override parent speed if config differs

    # ------------------------------------------------------------------ cost
    def compute_cost(self) -> float:
        hours = self.distance_km / self.speed_kmph
        if hours <= 8:
            hourly_cost = self.hour_cost_first_8 * hours
        else:
            hourly_cost = (
                self.hour_cost_first_8 * 8 + self.hour_cost_after_8 * (hours - 8)
            )
        return round(self.fixed_cost + self.km_cost * self.distance_km + hourly_cost, 2)


class VehicleTypeII(_BaseVehicle):
    """Faster but more expensive vehicle (type II)."""

    def __init__(self, start_node, config_path="config.json"):
        super().__init__(start_node, config_path)
        self.fixed_cost = 800
        self.km_cost = 1.3
        self.hour_cost_first_8 = 1.3
        self.hour_cost_after_8 = 1.5
        self.speed_kmph = 20
        self.fuel_capacity = 4_000
        self.snow_capacity = 250  

    # ------------------------------------------------------------------ cost
    def compute_cost(self) -> float:
        hours = self.distance_km / self.speed_kmph
        if hours <= 8:
            hourly_cost = self.hour_cost_first_8 * hours
        else:
            hourly_cost = (
                self.hour_cost_first_8 * 8 + self.hour_cost_after_8 * (hours - 8)
            )
        return round(self.fixed_cost + self.km_cost * self.distance_km + hourly_cost, 2)


class SuperDrone(_BaseVehicle):
    """Experimental ultra‑cheap airborne drone."""

    def __init__(self, start_node, config_path="config.json"):
        super().__init__(start_node, config_path)
        self.fixed_cost = 100
        self.km_cost = 0.01
        # Keep parent speed_kmph (comes from config) – could be overridden here.

    # ------------------------------------------------------------------ cost
    def compute_cost(self) -> float:
        return round(self.fixed_cost + self.km_cost * self.distance_km, 2)

