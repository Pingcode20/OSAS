import random
from classes.ship import Fleet
from util import weighted_shuffle

fleet1_filename = 'fleet_a.txt'
fleet2_filename = 'fleet_b.txt'

ranges = [3, 2, 1, 0, 0, 0, 1, 2, 3]


def find_target(target_list: list, targeting_order: list):
    selected_target = None
    for target_type in targeting_order:
        potential_targets = [t for t in target_list if t['hull_type'] == target_type]
        if len(potential_targets):
            selected_target = random.choices(potential_targets, weights=[t['target_weight'] for t in potential_targets], k=1)[0]
            break
    return selected_target


if __name__ == '__main__':
    fleets = {}

    fleet_a = Fleet(side='Side A', fleet_filename=fleet1_filename)
    fleets[fleet_a.fleet_name] = fleet_a

    fleet_b = Fleet(side='Side B', fleet_filename=fleet2_filename)
    fleets[fleet_b.fleet_name] = fleet_b

    # Created weighted lists
    all_ships = []
    for fleet in fleets:
        all_ships += fleets[fleet].generate_combat_list()

    initiative_list = weighted_shuffle(all_ships, [ship['initiative'] for ship in all_ships])

    # for range in ranges:
    for active_ship in initiative_list:
        ship = active_ship['ship']
        enemies = [t for t in all_ships if t['side'] != active_ship['side']]

        # Find target
        target = find_target(enemies, ship.stats['targeting order'])

        print(active_ship['name'] + ' found target ' + target['name'])

        # Primary attack

# print('\n')
# print(fleet_b.generate_fleet_summary())
