# Targeting functions
import random
import definitions.ship_properties as sp
from classes.ship_manager import ShipManager
from classes.ship_instance import ShipInstance


def find_target_priority_list(sm: ShipManager, instance: ShipInstance):
    targeting_order = instance.get_stat(sp.stat_targeting)

    for hull_type in targeting_order:
        selected_target = find_target_hull_type(sm, instance, hull_type)
        if selected_target:
            return selected_target

    return None


def find_target_hull_type(sm: ShipManager, instance: ShipInstance, hull_type: str):
    potential_targets, potential_target_weights = sm.get_ship_enemies_by_type(instance, hull_type)
    if len(potential_targets):
        return random.choices(potential_targets, weights=potential_target_weights, k=1)[0]
    else:
        return None


def find_target_bully(sm: ShipManager, instance: ShipInstance):
    # Get targets
    ship = instance.get_ship()
    target_list = ship.get_targets()

    if len(target_list):
        return random.choices(list(target_list.keys()), weights=list(target_list.values()), k=1)[0]
    else:
        return find_target_priority_list(sm, instance)  # Default behaviour if there's no bully targets
