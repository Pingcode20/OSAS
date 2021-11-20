# Targeting functions
import random
import definitions.ship_properties as sp


def find_random_target(target_list: iter, target_weights: iter, targeting_order: iter):
    selected_target = None
    for target_type in targeting_order:
        potential_targets = target_list[target_type]
        potential_target_weights = target_weights[target_type]
        if len(potential_targets):
            selected_target = random.choices(potential_targets, weights=potential_target_weights, k=1)[0]
            break
    return selected_target


def find_bully_target(target_list: iter, target_weights: iter):
    selected_target = None
    if len(target_list):
        return random.choices(target_list, weights=target_weights, k=1)[0]

    return None
