# Responsible for managing ship instances in a battle
from classes.ship_instance import ShipInstance
import definitions.battle_properties as bp
import definitions.ship_properties as sp

class ShipManager:

    all_ships: dict

    ships_by_side: dict = {}
    target_weight_by_side: dict = {}

    def __init__(self):
        self.all_ships = {}
        self.ships_by_side = {}
        self.target_weight_by_side = {}
        for side in bp.sides:
            self.ships_by_side[side] = {}
            self.target_weight_by_side[side] = {}
            self.ships_by_side[side][sp.size_any] = {}
            self.target_weight_by_side[side][sp.size_any] = {}
            for hull_type in sp.hull_types:
                self.ships_by_side[side][hull_type] = {}
                self.target_weight_by_side[side][hull_type] = {}

    def add(self, instance: ShipInstance):
        id = instance.get_id()
        side = instance.get_side()
        hull_type = instance.get_hull_type()
        self.all_ships[id] = instance
        self.ships_by_side[side][sp.size_any][id] = instance
        self.ships_by_side[side][hull_type][id] = instance
        self.target_weight_by_side[side][sp.size_any][id] = instance.get_target_weight()
        self.target_weight_by_side[side][hull_type][id] = instance.get_target_weight()
