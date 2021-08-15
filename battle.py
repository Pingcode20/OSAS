import random
from classes.ship import Fleet, default_attack_type
from util import weighted_shuffle

fleet1_filename = 'fleet_a.txt'
fleet2_filename = 'fleet_b.txt'

ranges = [3, 2, 1, 0, 0, 0, 1, 2, 3]


def find_target(target_list: list, targeting_order: list, k:int=1):
    selected_target = None
    for target_type in targeting_order:
        potential_targets = [t for t in target_list if t['hull_type'] == target_type and t['current_hull'] > 0]
        if len(potential_targets):
            selected_target = \
                random.choices(potential_targets, weights=[t['target_weight'] for t in potential_targets], k=1)[0]
            break
    return selected_target


def attack(attacker, defender, current_range, current_round):
    # Get attack value
    defender_type = defender['ship'].hull_type
    attack_lines = attacker['ship'].stats['attack']
    if defender_type in attack_lines:
        attack_value = attack_lines[defender_type][current_range]
    else:
        attack_value = attack_lines[default_attack_type][current_range]

    if attack_value == 0: return # 0 attack means 0 impact

    # Get defence value
    defence_value = defender['ship'].stats['defense']

    # Roll 1d20+attack vs defence+10
    roll = random.randint(1, 20)
    result = roll + attack_value - defence_value - 10
    if result >= 20:
        damage = 3
    elif result >= 6:
        damage = 2
    elif result >= 1:
        damage = 1
    else:
        damage = 1

    # Inflict damage
    combat_score = min(damage, max(defender['current_hull'],0)) * defender['ship'].combat_value
    try:
        attacker['combat_score'][current_round] += combat_score
    except KeyError:
        attacker['combat_score'][current_round] = combat_score
    defender['current_hull'] -= damage

    # Calculate saturation
    defender['saturation'] -= 1
    if defender['saturation'] <= 0:
        defender['current_hull'] -= 1
        defender['saturation'] = defender['ship'].stats['saturation']


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

    # Round starts here
    current_round = 0
    initiative_list = weighted_shuffle(all_ships, [ship['initiative'] for ship in all_ships])

    # for range in ranges:
    for active_ship in initiative_list:
        if active_ship['current_hull'] <= 0: continue  # Dead ships don't act

        ship = active_ship['ship']
        enemies = [t for t in all_ships if t['side'] != active_ship['side']]

        # Find target
        target = find_target(enemies, ship.stats['targeting order'])

        print(active_ship['name'] + ' found target ' + target['name'])

        # Primary attack
        attack(attacker=active_ship, defender=target, current_range=ranges[current_round], current_round=current_round)

        # AEGIS attacks


    a = 1