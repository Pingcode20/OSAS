# Responsible for managing ship instances in a battle
from classes.ship_instance import ShipInstance
from classes.fleet import Fleet
import definitions.battle_properties as bp
import definitions.ship_properties as sp
import uuid
import util


class ShipManager:
    all_ships: dict

    allies_by_side: dict
    allies_target_weight_by_side: dict

    enemies_by_side: dict
    enemies_target_weight_by_side: dict

    def __init__(self):
        self.all_ships = {}
        self.allies_by_side = {}
        self.allies_target_weight_by_side = {}
        self.enemies_by_side = {}
        self.enemies_target_weight_by_side = {}

    def initialise_side(self, side: str):
        # Check if side exists and cancel if it exists
        if side in self.allies_by_side:
            return

        # Initialise per-side tables
        self.allies_by_side[side] = {}
        self.allies_target_weight_by_side[side] = {}
        self.allies_by_side[side][sp.size_any] = {}
        self.allies_target_weight_by_side[side][sp.size_any] = {}

        self.enemies_by_side[side] = {}
        self.enemies_target_weight_by_side[side] = {}
        self.enemies_by_side[side][sp.size_any] = {}
        self.enemies_target_weight_by_side[side][sp.size_any] = {}

        for hull_type in sp.hull_types:
            self.allies_by_side[side][hull_type] = {}
            self.allies_target_weight_by_side[side][hull_type] = {}
            self.enemies_by_side[side][hull_type] = {}
            self.enemies_target_weight_by_side[side][hull_type] = {}

        # Populate enemies based on existing tables
        for opponent in [opponent for opponent in self.allies_by_side if opponent != side]:
            self.enemies_by_side[side][sp.size_any] |= self.allies_by_side[opponent][sp.size_any]
            self.enemies_target_weight_by_side[side][sp.size_any] |= \
                self.allies_target_weight_by_side[opponent][sp.size_any]
            for hull_type in sp.hull_types:
                self.enemies_by_side[side][hull_type] |= self.allies_by_side[opponent][hull_type]
                self.enemies_target_weight_by_side[side][hull_type] |= \
                    self.allies_target_weight_by_side[opponent][hull_type]

    def add(self, instance: ShipInstance) -> None:
        ship_id = instance.get_id()
        side = instance.get_side()
        hull_type = instance.get_hull_type()

        # Ensure side is initialised
        self.initialise_side(side)

        # Add ship to ally lists
        self.all_ships[ship_id] = instance
        self.allies_by_side[side][sp.size_any][ship_id] = instance
        self.allies_by_side[side][hull_type][ship_id] = instance
        self.allies_target_weight_by_side[side][sp.size_any][ship_id] = instance.get_target_weight()
        self.allies_target_weight_by_side[side][hull_type][ship_id] = instance.get_target_weight()

        # Add ship to enemy lists
        for opponent in [opponent for opponent in self.allies_by_side if opponent != side]:
            self.enemies_by_side[opponent][sp.size_any][ship_id] = instance
            self.enemies_target_weight_by_side[opponent][sp.size_any][ship_id] = instance

    def add_fleet(self, fleet: Fleet):
        combat_list = fleet.generate_combat_list()
        for hull_type in combat_list:
            for instance in combat_list[hull_type]:
                self.add(instance)

    def destroy(self, instance: ShipInstance) -> None:
        ship_id = instance.get_id()
        side = instance.get_side()
        hull_type = instance.get_hull_type()

        del self.all_ships[ship_id]
        del self.allies_by_side[side][sp.size_any][ship_id]
        del self.allies_by_side[side][hull_type][ship_id]

        del self.allies_target_weight_by_side[side][sp.size_any][ship_id]
        del self.allies_target_weight_by_side[side][hull_type][ship_id]

        for opponent in [opponent for opponent in self.enemies_by_side if opponent != side]:
            # Delete from generic target list
            del self.enemies_by_side[opponent][sp.size_any][ship_id]
            del self.enemies_target_weight_by_side[opponent][sp.size_any][ship_id]

            # Delete from hull type specific target list
            del self.enemies_by_side[opponent][hull_type][ship_id]
            del self.enemies_target_weight_by_side[opponent][hull_type][ship_id]

    def exists(self, ship_id: uuid) -> bool:
        return ship_id in self.all_ships

    def get_all_ships(self) -> dict:
        return self.all_ships.values()

    def get_ship_by_id(self, ship_id: uuid) -> ShipInstance:
        return self.all_ships[ship_id]

    def get_ship_allies_by_type(self, instance: ShipInstance, hull_type: str) \
            -> tuple[list[ShipInstance], list[ShipInstance]]:
        side = instance.get_side()
        return list(self.allies_by_side[side][hull_type].values()), \
               list(self.allies_target_weight_by_side[side][hull_type].values())

    def get_ship_enemies_by_type(self, instance: ShipInstance, hull_type: str) \
            -> tuple[list[ShipInstance], list[ShipInstance]]:
        side = instance.get_side()
        return list(self.enemies_by_side[side][hull_type].values()), \
               list(self.enemies_target_weight_by_side[side][hull_type].values())

    def generate_initiative_list(self) -> list:
        instances = [instance for instance in self.all_ships]
        initiatives = [instance.get_initiative() for instance in instances]

        return util.weighted_shuffle(instances, initiatives)

    def get_ship_counts(self) -> dict:
        counts = {}
        for side in self.allies_by_side:
            counts[side] = len(self.allies_by_side[side][sp.size_any])
        return counts

    def get_survivor_counts(self) -> dict:
        counts = self.get_ship_counts()
        return {side: counts[side] for side in counts if counts[side] > 0}
