import random
from classes.ship import default_attack_type, hull_types
from classes.fleet import Fleet
import classes.battle_event as battle_event
from util import weighted_shuffle

side_a = 'A'
side_b = 'B'

ranges = [3, 2, 1, 0, 0, 0, 1, 2, 3]


def find_target(target_list: list, targeting_order: list):
    selected_target = None
    for target_type in targeting_order:
        potential_targets = target_list[target_type]
        if len(potential_targets):
            selected_target = \
                random.choices(potential_targets, weights=[t['ship'].target_weight for t in potential_targets],
                               k=1)[0]
            break
    return selected_target


class Battle:
    sides = {
        side_a: [],
        side_b: []
    }

    fleets = []

    ships_by_side = {}
    all_ships = []

    destroyed_ships = {rnd: [] for rnd in range(0, len(ranges))}
    events = {rnd: [] for rnd in range(0, len(ranges))}

    current_round = 0

    # Only supports Side A and Side B for now
    def load_fleet(self, side, fleet_filename):
        fleet = Fleet(side=side, fleet_filename=fleet_filename)
        self.sides[side].append(fleet)
        self.fleets.append(fleet)

    def initialise_battle(self):
        self.ships_by_side = {}
        self.all_ships = []

        for side in self.sides:
            self.ships_by_side[side] = {hull_type: [] for hull_type in hull_types}
            for fleet in self.sides[side]:
                ships_by_type = fleet.generate_combat_list()
                for ship_type in ships_by_type:
                    ship_list = ships_by_type[ship_type]
                    self.all_ships.extend(ship_list)
                    self.ships_by_side[side][ship_type].extend(ship_list)

    def attack(self, attacker, defender, enemies):
        current_round = self.current_round
        current_range = ranges[current_round]

        # Get attack value
        defender_type = defender['ship'].hull_type
        attack_lines = attacker['ship'].stats['attack']
        if defender_type in attack_lines:
            attack_value = attack_lines[defender_type][current_range]
        else:
            attack_value = attack_lines[default_attack_type][current_range]

        if attack_value == 0: return  # 0 attack means 0 impact

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
        self.add_combat_event(
            battle_event.AttackEvent(attacker['name'], defender['name'], attack_value, defence_value, damage, roll))

        # print('Dealt ' + str(damage) + ' damage to target')

        # Calculate saturation
        defender['saturation'] -= 1
        if defender['saturation'] <= 0:
            self.add_combat_event(battle_event.SaturationEvent(defender['name']))
            defender['current_hull'] -= 1
            defender['saturation'] = defender['ship'].stats['saturation']  # Reset saturation after hit
            # print(defender['name'] + ' suffers 1 damage from saturation overload')

        if defender['current_hull'] <= 0:
            # print(defender['name'] + ' is destroyed!')
            self.add_combat_event(battle_event.DestroyedEvent(defender['name']))
            target_hull_type = defender['ship'].hull_type
            enemies[target_hull_type].remove(defender)
            self.all_ships.remove(defender)
            self.destroyed_ships[current_round].append(defender)

    def simulate_battle(self):
        for current_round in range(0, len(ranges)):
            self.current_round = current_round

            initiative_list = weighted_shuffle(self.all_ships, [ship['ship'].initiative for ship in self.all_ships])

            for active_ship in initiative_list:
                if active_ship['current_hull'] <= 0: continue  # Dead ships don't act
                ship = active_ship['ship']

                if active_ship['ship'].fleet.side == side_a:
                    enemies = self.ships_by_side[side_b]
                else:
                    enemies = self.ships_by_side[side_a]

                # Primary attack
                defender = find_target(enemies, ship.stats['targeting order'])
                if defender:
                    # print(active_ship['name'] + ' attacking target ' + defender['name'])
                    self.attack(attacker=active_ship, defender=defender, enemies=enemies)

                # AEGIS attacks
                for a in range(0, active_ship['ship'].stats['aegis']):
                    defender = find_target(enemies, ['Drone'])
                    if defender:
                        # print(active_ship['name'] + ' attacking AEGIS target ' + defender['name'])
                        self.attack(attacker=active_ship, defender=defender, enemies=enemies)
        # Remaining
        for fleet in self.fleets:
            print('Battle Results: ' + fleet.fleet_name + ' - Side ' + fleet.side)
            print(fleet.generate_fleet_summary())
            print('\n')

    def add_combat_event(self, event):
        self.events[self.current_round].append(event)


if __name__ == '__main__':
    fleet1_filename = 'unifiedfleet.txt'
    fleet2_filename = 'gorn.txt'

    battle = Battle()
    battle.load_fleet(side=side_a, fleet_filename=fleet1_filename)
    battle.load_fleet(side=side_b, fleet_filename=fleet2_filename)

    battle.initialise_battle()
    battle.simulate_battle()
