import collections
import classes.combat_scoreboard as st
import re
import uuid
from classes.ship_instance import ShipInstance

import definitions.configs
import definitions.ship_properties as sp

targeting_orders = {
    'Drone': ['Drone', 'Destroyer', 'Cruiser', 'Capital'],
    'Destroyer': ['Drone', 'Destroyer', 'Cruiser', 'Capital'],
    'Cruiser': ['Destroyer', 'Cruiser', 'Drone', 'Capital'],
    'Capital': ['Capital', 'Cruiser', 'Destroyer', 'Drone'],
    'Bomber': ['Destroyer', 'Cruiser', 'Capital', 'Drone'],
    'Cruiser Targeting': ['Cruiser', 'Capital', 'Destroyer', 'Drone'],
}

hull_types = ['Drone', 'Destroyer', 'Cruiser', 'Capital']

default_attack_type = 'starship'


class Ship:
    # Ship name
    short_name = ''
    role = ''
    class_name = ''
    hull_type = ''
    hull_subtype = ''
    hull_full_type = ''
    fleet = None

    # Meta-stats
    class_id = ''
    combat_value = 0
    combat_scorecard = None

    # Combat stats
    initiative = 0
    target_weight = 0

    # instances
    instances: list
    tactics_targets: dict  # Previous targets

    def __init__(self, fleet=None):
        self.stats = collections.OrderedDict({
            sp.stat_attack: {sp.attack_type_any: [0, 0, 0, 0]},
            sp.stat_defence: 0,
            sp.stat_saturation: 0,
            sp.stat_speed: 0,
            sp.stat_jump: 0,
            sp.stat_hull: 1,
            sp.stat_slots: '',
            sp.stat_aegis: 0,
            sp.stat_targeting: [],
            sp.stat_tactics: definitions.configs.ai_default,
            sp.stat_overload: 1,
            sp.stat_devastate: 1,
        })
        self.class_id = uuid.uuid4()
        self.fleet = fleet
        self.combat_scorecard = {}
        self.tactics_targets = {}

    def get_side(self):
        return self.fleet.side

    def get_stat(self, stat_name: str):
        if stat_name in self.stats:
            return self.stats[stat_name]
        else:
            return 0

    def parse_statblock(self, statblock: str):
        stats = statblock.split('\n')

        # First line defines the ship class and hull type
        match = re.match(r'(.*)\[(\w+)-?(\w+)?]', stats[0]).groups()
        self.class_name = match[0].strip()
        self.hull_type = match[1]
        self.hull_subtype = match[2] or match[1]

        # Split the name if possible
        name_match = re.match(r'(.*?)-?class\s*(.*)', self.class_name, re.IGNORECASE)
        if name_match:
            self.short_name = name_match.groups()[0].strip()
            self.role = (name_match.groups()[1] or self.short_name).strip()
        else:
            self.short_name = self.class_name
            self.role = self.class_name

        if self.hull_type == self.hull_subtype:
            self.hull_full_type = self.hull_type
        else:
            self.hull_full_type = self.hull_type + '-' + self.hull_subtype

        quantity = 1  # Default to 1 ship if otherwise unspecified
        current_hulls = []
        for stat in stats[1:]:
            k, val = list(map(str.strip, stat.split(':', maxsplit=1)))

            key = k.lower()
            attack_match = re.match(rf'{sp.stat_attack}(\s\[(\w+)])?', key,
                                    re.IGNORECASE)  # Match for both sp.stat_attack and 'Attack (ship) etc.'

            if key == sp.stat_quantity:
                quantity = int(re.match(r'(\d+)', val).group())
            elif attack_match:
                attack_type = attack_match.groups()[1] or default_attack_type
                attack_values = list(map(str.strip, val.split('/')))
                self.stats[sp.stat_attack][attack_type] = [int(x) for x in attack_values]
            elif key == sp.stat_slots:
                self.parse_special_modules(val)
                self.stats[key] = val
            elif key == sp.stat_targeting:
                # Clean up targeting order to remove formatting issues
                target_values = val.split(',')
                self.stats[sp.stat_targeting] = [target.strip().rstrip('s').title() for target in target_values]
            elif key == sp.stat_current_hull:
                hulls = list(map(str.strip, val.split(',')))
                for hull_record in hulls:
                    count, hull = re.match(r'(\d+)x\s*(\d+)', hull_record).groups()
                    current_hulls.extend([int(hull)] * int(count))
            elif val.isnumeric():
                self.stats[key] = int(val)
            else:
                self.stats[key] = val

        if len(self.stats[sp.stat_targeting]) == 0:
            self.stats[sp.stat_targeting] = sp.targeting_orders[self.hull_subtype]

        self.prepare_derived_stats()
        self.initialise_instances(current_hulls=current_hulls, quantity=quantity)

        return self

    # Parse modules for any special effects like AEGIS
    def parse_special_modules(self, modules: str):
        # AEGIS
        match_aegis = re.match(r'.*AEGIS\s?x(\d+).*', modules, re.IGNORECASE)
        if match_aegis:
            self.stats[sp.stat_aegis] = self.stats[sp.stat_aegis] or int(match_aegis.groups()[0])

        # Cruiser Targeting
        if re.match(r'.*cruiser targeting.*', modules, re.IGNORECASE):
            self.stats[sp.stat_targeting] = self.stats[sp.stat_targeting] or sp.targeting_orders[
                sp.subtype_anti_cruiser]

    # Prepare derived stats
    def prepare_derived_stats(self):
        # Rough power estimate based on starship attack + defence
        scaled_general_attack = [x ** 2 for x in self.stats[sp.stat_attack][default_attack_type]]
        scaled_defence = self.stats[sp.stat_defence] ** 2
        combat_value = (sum(scaled_general_attack) + scaled_general_attack[0] + scaled_defence * 9) ** 0.5
        self.combat_value = round(combat_value)

        self.initiative = self.stats[sp.stat_speed] or 1
        self.target_weight = self.stats[sp.stat_speed] or 1

    def initialise_instances(self, current_hulls, quantity):
        # Fill in extra hulls at full strength if quantity is higher than specified
        if len(current_hulls) < quantity:
            current_hulls.extend(
                [self.stats[sp.stat_hull]] * (quantity - len(current_hulls)))

        # Generate instances
        instances = []
        ship_id = 1
        for current_hull in current_hulls:
            ship_name = self.fleet.fleet_name + ' ' + self.short_name + ' #' + str(ship_id)
            instance = ShipInstance(ship=self, name=ship_name, current_hull=current_hull)
            instances.append(instance)
            ship_id += 1
        self.instances = instances

    def update_scorecard(self, current_round, field, points):
        if current_round not in self.combat_scorecard: self.combat_scorecard[current_round] = st.Scoreboard(ship=self)

        self.combat_scorecard[current_round][field] = self.combat_scorecard[current_round].get(field, 0) + points

    def display_scorecard(self, current_round):
        if current_round not in self.combat_scorecard: return ''
        scorecard = self.combat_scorecard[current_round]
        return self.class_name + ': ' + scorecard.show_line()

    def generate_statblock(self):
        stats = self.stats

        stat_strings = []
        for stat in stats:
            if stat == sp.stat_attack:
                attack_types = self.stats[stat]
                if len(attack_types) == 1:
                    stat_string = "/".join(map(str, stats[stat][default_attack_type]))
                    stat_strings.append(sp.stat_attack.capitalize() + ': ' + stat_string)
                else:
                    for attack_type in self.stats[stat]:
                        stat_string = "/".join(map(str, stats[stat][attack_type]))
                        stat_strings.append(sp.stat_attack.capitalize() + ' [' + attack_type.capitalize() + ']: '
                                            + stat_string)
                continue
            elif stat == sp.stat_targeting:
                stat_string = ", ".join(map(str, stats[stat]))
            else:
                stat_string = str(stats[stat]).strip()

            stat_strings.append(stat.title() + ': ' + stat_string)

        hull_counter = collections.Counter([instance.get_hull() for instance in self.instances])
        hull_string = ', '.join([str(hull_counter[hull]) + 'x ' + str(hull) for hull in hull_counter if hull > 0])
        stat_strings.append(sp.stat_current_hull.title() + ': ' + hull_string)

        return f"%s [%s]\n" % (self.class_name, self.hull_full_type) \
               + f"%s: %d\n" % (sp.stat_quantity.capitalize(), self.quantity()) \
               + '\n'.join(stat_strings)

    def generate_summary(self):
        quantity = len([instance for instance in self.instances if instance.get_hull() > 0])
        hull_counter = collections.Counter(
            [instance.get_hull() for instance in self.instances if instance.get_hull() > 0])
        hull_string = ', '.join([str(hull_counter[hull]) + 'x ' + str(hull) for hull in hull_counter]) or 'None Left'

        return self.class_name + ' [' + self.hull_full_type + '] x' + str(quantity) + ' - ' + str(
            self.combat_value * quantity) + ' power rating (' + str(
            self.combat_value) + ' ea.)' + ' - ' + sp.stat_hull.capitalize() + ': ' + hull_string

    def quantity(self):
        return len([inst for inst in self.instances if inst.get_hull() > 0])

    def add_target(self, target: ShipInstance, damage: int, pr_hit: float):
        if target not in self.tactics_targets:
            self.tactics_targets[target] = 0

        self.tactics_targets[target] += damage * pr_hit

    def get_targets(self):
        # Clean any stale targets
        for target in list(self.tactics_targets.keys()):
            if target.is_dead():
                del self.tactics_targets[target]

        return self.tactics_targets
