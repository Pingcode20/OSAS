import collections
import random
from classes.ship import default_attack_type, hull_types
from classes.fleet import Fleet
import classes.battle_event as battle_event
import classes.combat_scoreboard as st
from definitions import ranges, OUTPUT_DIR
from util import weighted_shuffle
import os

side_a = 'A'
side_b = 'B'


def find_target(target_list: list, target_weights: list, targeting_order: list):
    selected_target = None
    for target_type in targeting_order:
        potential_targets = target_list[target_type]
        potential_target_weights = target_weights[target_type]
        if len(potential_targets):
            selected_target = random.choices(potential_targets, weights=potential_target_weights, k=1)[0]
            break
    return selected_target


class Battle:
    sides = {
        side_a: [],
        side_b: []
    }

    ships_by_side = {}
    target_weight_by_side = {}
    all_ships = {}

    destroyed_ships = {rnd: [] for rnd in range(0, len(ranges))}
    events = {rnd: [] for rnd in range(0, len(ranges))}

    current_round = 0
    final_round = 0

    # Only supports Side A and Side B for now
    def load_fleet(self, side, fleet_filename):
        fleet = Fleet(side=side, fleet_filename=fleet_filename)
        self.sides[side].append(fleet)

    def initialise_battle(self):
        self.ships_by_side = {}
        self.all_ships = {}

        for side in self.sides:
            self.ships_by_side[side] = {hull_type: [] for hull_type in hull_types}
            self.target_weight_by_side[side] = {hull_type: [] for hull_type in hull_types}

            for fleet in self.sides[side]:
                ships_by_type = fleet.generate_combat_list()
                for ship_type in ships_by_type:
                    ship_list = ships_by_type[ship_type]
                    self.all_ships.update({ship['ship_id']: ship for ship in ship_list})
                    self.ships_by_side[side][ship_type].extend(ship_list)
                    self.target_weight_by_side[side][ship_type].extend(
                        [ship['ship'].target_weight for ship in ship_list])

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

        if damage:
            attacker['ship'].update_scorecard(current_round, st.hits, 1)
            attacker['ship'].update_scorecard(current_round, st.damage, damage)
        else:
            attacker['ship'].update_scorecard(current_round, st.misses, 1)
            defender['ship'].update_scorecard(current_round, st.defence, attack_value ** 2)

        # Inflict damage
        attacker['ship'].update_scorecard(current_round, st.attack, damage * defence_value ** 2)
        defender['current_hull'] -= damage
        defender['ship'].update_scorecard(current_round, st.hull_loss, damage)
        self.add_combat_event(
            battle_event.AttackEvent(attacker['name'], defender['name'], attack_value, defence_value, damage, roll))

        # Calculate saturation
        defender['saturation'] -= 1
        if defender['saturation'] <= 0:
            self.add_combat_event(battle_event.SaturationEvent(defender['name']))
            defender['current_hull'] -= 1
            defender['saturation'] = defender['ship'].stats['saturation']  # Reset saturation after hit
            defender['ship'].update_scorecard(current_round, st.saturation, 1)

        if defender['current_hull'] <= 0:
            self.destroy_ship(defender)

    def simulate_battle(self):
        for current_round in range(0, len(ranges)):
            self.current_round = current_round

            all_ships = list(self.all_ships.values())
            initiative_list = weighted_shuffle(all_ships, [ship['ship'].initiative for ship in all_ships])

            for active_ship in initiative_list:
                if active_ship['current_hull'] <= 0: continue  # Dead ships don't act
                ship = active_ship['ship']

                if active_ship['ship'].fleet.side == side_a:
                    enemies = self.ships_by_side[side_b]
                    target_weights = self.target_weight_by_side[side_b]
                else:
                    enemies = self.ships_by_side[side_a]
                    target_weights = self.target_weight_by_side[side_a]

                # Primary attack
                defender = find_target(enemies, target_weights, ship.stats['targeting order'])
                if defender:
                    self.attack(attacker=active_ship, defender=defender, enemies=enemies)

                # AEGIS attacks
                for a in range(0, active_ship['ship'].stats['aegis']):
                    defender = find_target(enemies, target_weights, ['Drone'])
                    if defender:
                        self.attack(attacker=active_ship, defender=defender, enemies=enemies)

            # Post-exchange
            for side in self.sides:
                for fleet in self.sides[side]:
                    for ship_id in fleet.ships:
                        ship = fleet.ships[ship_id]
                        ship.update_scorecard(current_round, st.quantity, ship.get_quantity())

            # Test if anyone has won
            winning_side = None
            fleets_with_ships_left = 0
            for side in self.ships_by_side:
                for ship_type in self.ships_by_side[side]:
                    if len(self.ships_by_side[side][ship_type]) > 1:
                        fleets_with_ships_left += 1
                        winning_side = side
                        break

            if fleets_with_ships_left <= 1:
                self.add_combat_event(
                    battle_event.BattleEndEvent([fleet.fleet_name for fleet in self.sides[winning_side]]))
                self.final_round = current_round
                break

    def add_combat_event(self, event):
        self.events[self.current_round].append(event)

    def destroy_ship(self, ship, index=None):
        side = ship['ship'].get_side()
        hull_type = ship['ship'].hull_type
        ship_list = self.ships_by_side[side][hull_type]
        index = index or ship_list.index(ship)

        self.add_combat_event(battle_event.DestroyedEvent(ship['name']))
        del ship_list[index]
        del self.target_weight_by_side[side][hull_type][index]
        del self.all_ships[ship['ship_id']]
        self.destroyed_ships[self.current_round].append(ship)
        ship['ship'].update_scorecard(self.current_round,st.losses,1)

    def report_summary(self):
        report = ''

        for current_round in range(0, self.final_round + 1):
            report += self.report_round(current_round) + '\n'

        report += '\n'
        report += self.generate_fleet_summaries() + '\n'

        return report

    def report_verbose(self):
        report = ''
        for current_round in self.events:
            if not len(self.events[current_round]): break

            report += '\n=====Round ' + str(current_round + 1) + '=====\n'
            for event in self.events[current_round]:
                report += event.show() + '\n'
            report += '\n'

        report += self.generate_fleet_summaries()

        return report

    def report_round(self, current_round):
        report = '\n=====Round ' + str(current_round + 1) + '=====\n'
        for side in self.sides:
            for fleet in self.sides[side]:
                report += 'Fleet: ' + fleet.fleet_name + '\n'
                report += fleet.generate_combat_scoreboard(current_round)
                report += '\n\n'

        # Report on destroyed ships
        report += '\n' + 'Ships Destroyed: ' + '\n'

        destroyed_ships = self.destroyed_ships[current_round]
        losses_counter = collections.Counter(
            [ship['ship'].fleet.fleet_name + ' ' + ship['ship'].class_name for ship in destroyed_ships])
        if len(losses_counter) > 0:
            losses = []
            for lost_ship in losses_counter:
                losses.append(lost_ship + ' x' + str(losses_counter[lost_ship]))
            losses.sort()
            report += '\n'.join(losses)
        else:
            report += 'None' + '\n'

        return report

    def generate_fleet_summaries(self):
        report = ''

        for side in self.sides:
            for fleet in self.sides[side]:
                report += 'Battle Results: ' + fleet.fleet_name + ' - Side ' + fleet.side + '\n'
                report += fleet.generate_fleet_summary()
                report += '\n'
            report += '\n'

        return report


if __name__ == '__main__':
    random.seed(5555)

    fleet1_filename = 'unifiedfleet.txt'
    fleet2_filename = 'gorn.txt'

    battle = Battle()
    battle.load_fleet(side=side_a, fleet_filename=fleet1_filename)
    battle.load_fleet(side=side_b, fleet_filename=fleet2_filename)

    battle.initialise_battle()
    battle.simulate_battle()

    f = open(os.path.join(OUTPUT_DIR,'test_battle.txt'), 'w')
    f.write(battle.report_summary())
    f.close()

    f = open(os.path.join(OUTPUT_DIR,'test_battle_verbose.txt'), 'w')
    f.write(battle.report_verbose())
    f.close()

    for side in battle.sides.values():
        for participating_fleet in side:
            f = open(os.path.join(OUTPUT_DIR,participating_fleet.fleet_name + ' - Post-Battle.txt'),'w')
            f.write(participating_fleet.generate_fleet_oob())
            f.close()

