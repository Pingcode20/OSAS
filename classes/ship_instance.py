# Represents a single instance of a ship
import definitions.ship_properties as sp
import uuid


class ShipInstance:
    # Reference to parent
    ship = None
    name: str = ''
    ship_id: uuid = None
    current_hull: int = 0
    saturation: int = 0

    def __init__(self, ship, name: str, current_hull: int):
        self.ship = ship
        self.current_hull = current_hull
        self.name = name
        self.ship_id = uuid.uuid4()
        self.reset_saturation()

    def reset_saturation(self):
        self.saturation = self.ship.get_stat(sp.stat_saturation)

    def get_id(self):
        return self.ship_id

    def get_ship(self):
        return self.ship

    def get_hull_type(self):
        return self.ship.hull_type

    def get_initiative(self):
        return self.ship.initiative

    def get_target_weight(self):
        return self.ship.target_weight

    def get_side(self):
        return self.ship.get_side()

    def get_name(self):
        return self.name

    def get_stat(self, stat_name: str):
        return self.ship.get_stat(stat_name)

    def get_attack_for_hull_type(self, hull_type: str, current_range: int):
        attack_lines = self.get_stat(sp.stat_attack)
        if hull_type in attack_lines:
            return attack_lines[hull_type][current_range]
        else:
            return attack_lines[sp.attack_type_any][current_range]

    def get_hull(self):
        return self.current_hull

    def damage(self, damage: int):
        self.current_hull -= damage

    def saturate(self, saturation_damage: int):
        self.saturation -= saturation_damage
        return self.saturation
