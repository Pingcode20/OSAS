import collections
import random
from classes.fleet import Fleet
from classes.ship_manager import ShipManager
from classes.ship_instance import ShipInstance
import classes.battle_event as battle_event
import classes.combat_scoreboard as st
import definitions.battle_properties as bp
import definitions.configs as conf
import functions.target as targeting
from util import weighted_shuffle
import definitions.ship_properties as sp


class Battle:
    sm: ShipManager

    sides: dict
    fleets: list = []

    destroyed_ships: dict
    events: dict

    current_round: int
    final_round: int

    def __init__(self):
        self.sides = {
            bp.side_a: [],
            bp.side_b: []
        }

        self.fleets = []
        self.sm = ShipManager()

        self.destroyed_ships = {rnd: [] for rnd in range(0, len(bp.ranges))}
        self.events = {rnd: [] for rnd in range(0, len(bp.ranges))}

        self.current_round = 0
        self.final_round = 0

    # Only supports Side A and Side B for now
    def load_fleet(self, side, fleet_filename):
        fleet = Fleet(side=side, fleet_filename=fleet_filename)
        self.sides[side].append(fleet)
        self.fleets.append(fleet)
        self.sm.add_fleet(fleet)

    def initialise_battle(self):
        pass

    def attack(self, attacker: ShipInstance, defender: ShipInstance):
        current_round = self.current_round
        current_range = bp.ranges[current_round]

        # Get attack value
        defender_type = defender.get_hull_type()
        attack_value = attacker.get_attack_for_hull_type(defender_type, current_range)

        if attack_value == 0:
            return  # 0 attack means 0 impact

        # Get defence value
        defence_value = defender.get_stat(sp.stat_defence)

        # Roll 1d20+attack vs defence+10
        roll = random.randint(1, 20)
        pr_hit = min((attack_value - defence_value + 10) / 20, 1)
        result = roll + attack_value - defence_value - 10
        if result >= 16:
            damage = 2 + attacker.get_stat(sp.stat_devastate)
        elif result >= 6:
            damage = 2
        elif result >= 1:
            damage = 1
        else:
            damage = 0

        if damage:
            attacker.get_ship().update_scorecard(current_round, st.hits, 1)
            attacker.get_ship().update_scorecard(current_round, st.damage, damage)
            attacker.get_ship().add_target(target=defender, damage=damage, pr_hit=pr_hit)
        else:
            attacker.get_ship().update_scorecard(current_round, st.misses, 1)
            defender.get_ship().update_scorecard(current_round, st.defence, attack_value ** 2)

        # Inflict damage
        attacker.get_ship().update_scorecard(current_round, st.attack, damage * defence_value ** 2)
        defender.damage(damage)
        defender.get_ship().update_scorecard(current_round, st.hull_loss, damage)
        self.add_combat_event(
            battle_event.AttackEvent(attacker.get_name(), defender.get_name(), attack_value, defence_value, damage,
                                     roll))

        # Calculate saturation
        defender_sat_remaining = defender.saturate(attacker.get_stat(sp.stat_overload))
        if defender_sat_remaining < 0:
            self.add_combat_event(battle_event.SaturationEvent(defender.get_name()))
            defender.damage(1)
            defender.reset_saturation()  # Reset saturation after hit
            defender.get_ship().update_scorecard(current_round, st.saturation, 1)

        if defender.get_hull() <= 0:
            self.sm.destroy(defender)
            self.add_combat_event(battle_event.DestroyedEvent(defender.get_name()))
            self.destroyed_ships[self.current_round].append(defender)
            defender.get_ship().update_scorecard(self.current_round, st.losses, 1)

    def simulate_battle(self):
        for current_round in range(0, len(bp.ranges)):
            self.current_round = current_round

            all_ships = self.sm.get_all_ships()
            initiative_list: list[ShipInstance] = weighted_shuffle(all_ships,
                                                                   [instance.get_initiative() for instance in
                                                                    all_ships],
                                                                   reverse=True)

            for active_ship in initiative_list:
                if active_ship.is_dead(): continue  # Dead ships don't act

                # Primary attack
                # Check tactics
                if random.random() < conf.ai_tactic_chance:
                    defender = targeting.find_target_bully(self.sm, active_ship)
                else:
                    defender = targeting.find_target_priority_list(self.sm, active_ship)

                if defender:  # If a target was found
                    self.attack(attacker=active_ship, defender=defender)

                # AEGIS attacks
                for a in range(0, active_ship.get_stat(sp.stat_aegis)):
                    defender = targeting.find_target_hull_type(self.sm, active_ship, sp.size_drone)
                    if defender:
                        self.attack(attacker=active_ship, defender=defender)

            # Post-exchange
            for side in self.sides:
                for fleet in self.sides[side]:
                    for ship_id in fleet.ships:
                        ship = fleet.ships[ship_id]
                        ship.update_scorecard(current_round, st.quantity, ship.quantity())

            # Test if anyone has won
            survivor_counts = self.sm.get_survivor_counts()
            if len(survivor_counts) == 1:
                winning_side = list(survivor_counts.keys())[0]
                self.add_combat_event(
                    battle_event.BattleEndEvent([fleet.fleet_name for fleet in self.sides[winning_side]]))
                self.final_round = current_round
                return

            # Reset Saturation
            for ship in all_ships:
                ship.reset_saturation()

        # Default to no winners
        self.add_combat_event(battle_event.BattleEndEvent([]))
        self.final_round = current_round

    def add_combat_event(self, event):
        self.events[self.current_round].append(event)

    def destroy_ship(self, ship, index=None):
        side = ship.get_ship().get_side()
        hull_type = ship.get_ship().hull_type
        ship_list = self.ships_by_side[side][hull_type]
        index = index or ship_list.index(ship)

        self.add_combat_event(battle_event.DestroyedEvent(ship.get_name()))
        del ship_list[index]
        del self.target_weight_by_side[side][hull_type][index]
        del self.all_ships[ship.get_id()]
        self.destroyed_ships[self.current_round].append(ship)
        ship.get_ship().update_scorecard(self.current_round, st.losses, 1)

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
            [ship.get_ship().fleet.fleet_name + ' ' + ship.get_ship().class_name for ship in destroyed_ships])
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
