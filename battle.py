import random
from classes.ship import default_attack_type, hull_types
from classes.fleet import Fleet
from util import weighted_shuffle

fleet1_filename = 'fleet_a.txt'
fleet2_filename = 'fleet_b.txt'

ranges = [3, 2, 1, 0, 0, 0, 1, 2, 3]

side_a = 'Side A'
side_b = 'Side B'


def find_target(target_list: list, targeting_order: list):
    selected_target = []
    for target_type in targeting_order:
        potential_targets = target_list[target_type]
        if len(potential_targets):
            selected_target = \
                random.choices(potential_targets, weights=[t['ship'].target_weight for t in potential_targets], k=1)[0]
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

    if attack_value == 0:
        print('No effective firepower at this range')
        return  # 0 attack means 0 impact

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
        damage = 0

    # Inflict damage
    combat_score = min(damage, max(defender['current_hull'], 0)) * defender['ship'].combat_value
    try:
        attacker['ship'].combat_score[current_round] += combat_score
    except KeyError:
        attacker['ship'].combat_score[current_round] = combat_score
    defender['current_hull'] -= damage

    print('Dealt ' + str(damage) + ' damage to target')

    # Calculate saturation
    defender['saturation'] -= 1
    if defender['saturation'] <= 0:
        defender['current_hull'] -= 1
        defender['saturation'] = defender['ship'].stats['saturation']  # Reset saturation after hit
        print(defender['name'] + ' suffers 1 damage from saturation overload')


if __name__ == '__main__':
    sides = {
        side_a: [],
        side_b: []
    }

    fleet_a = Fleet(side=side_a, fleet_filename=fleet1_filename)
    sides[side_a].append(fleet_a)

    fleet_b = Fleet(side=side_b, fleet_filename=fleet2_filename)
    sides[side_b].append(fleet_b)

    # Created weighted lists
    ships_by_side = {}
    all_ships = []

    for side in sides:
        ships_by_side[side] = {hull_type: [] for hull_type in hull_types}
        for fleet in sides[side]:
            ships_by_type = fleet.generate_combat_list()
            for ship_type in ships_by_type:
                ship_list = ships_by_type[ship_type]
                all_ships.extend(ship_list)
                ships_by_side[side][ship_type].extend(ship_list)

    # Round starts here
    current_round = 0

    initiative_list = weighted_shuffle(all_ships, [ship['ship'].initiative for ship in all_ships])

    for active_ship in initiative_list:
        if active_ship['current_hull'] <= 0: continue  # Dead ships don't act
        ship = active_ship['ship']

        if active_ship['ship'].fleet.side == side_a:
            enemies = ships_by_side[side_b]
        else:
            enemies = ships_by_side[side_a]

        # Primary attack
        target = find_target(enemies, ship.stats['targeting order'])
        if target:
            print(active_ship['name'] + ' attacking target ' + target['name'])
            attack(attacker=active_ship, defender=target, current_range=ranges[current_round],
                   current_round=current_round)

        # AEGIS attacks
        for a in range(0, active_ship['ship'].stats['aegis']):
            target = find_target(enemies, ['Drone'])
            if target:
                print(active_ship['name'] + ' attacking AEGIS target ' + target['name'])
                attack(attacker=active_ship, defender=target, current_range=ranges[current_round],
                       current_round=current_round)

    a = 1
