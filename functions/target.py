# Targeting functions
import random
import definitions.ship_properties as sp
from classes.ship_manager import ShipManager
from classes.ship_instance import ShipInstance


def find_random_target(sm: ShipManager, instance: ShipInstance, override_targeting_order: list = None):
    if override_targeting_order:
        targeting_order = override_targeting_order
    else:
        targeting_order = instance.get_stat(sp.stat_targeting)

    selected_target = None

    for target_type in targeting_order:
        potential_targets, potential_target_weights = sm.get_ship_enemies_by_type(instance, target_type)
        if len(potential_targets):
            selected_target = random.choices(potential_targets, weights=potential_target_weights, k=1)[0]
            break

    return selected_target


def find_bully_target(target_list: iter, target_weights: iter):
    selected_target = None
    if len(target_list):
        return random.choices(target_list, weights=target_weights, k=1)[0]

    return None
