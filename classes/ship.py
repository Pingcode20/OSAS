import collections
import os
from pathlib import Path
import re
import numpy
import itertools
from definitions import OOB_DIR

targeting_orders = {
    'Drone': ['Drone', 'Destroyer', 'Cruiser', 'Capital'],
    'Destroyer': ['Drone', 'Destroyer', 'Cruiser', 'Capital'],
    'Cruiser': ['Destroyer', 'Cruiser', 'Drone', 'Capital'],
    'Capital': ['Capital', 'Cruiser', 'Destroyer', 'Drone'],
    'Bomber': ['Destroyer', 'Cruiser', 'Capital', 'Drone'],
    'Cruiser Targeting': ['Cruiser', 'Capital', 'Destroyer', 'Drone'],
}

default_attack_type = 'starship'


class Ship:
    class_name = ''
    hull_type = ''
    hull_subtype = ''
    hull_full_type = ''

    # Meta-stats
    combat_value = 0

    def __init__(self):
        self.stats = collections.OrderedDict({
            'quantity': 1,
            'attack': {default_attack_type: [0, 0, 0, 0]},
            'defense': 0,
            'saturation': 0,
            'speed': 0,
            'jump': 0,
            'hull': 1,
            'slots': '',
            'current hull': [],
            'aegis': 0,
            'targeting order': []
        })

    def parse_statblock(self, statblock: str):
        stats = statblock.split('\n')

        # First line defines the ship class and hull type
        match = re.match(r'(.*)\[(\w+)-?(\w+)?]', stats[0]).groups()
        self.class_name = match[0].strip()
        self.hull_type = match[1]
        self.hull_subtype = match[2] or match[1]

        if self.hull_type == self.hull_subtype:
            self.hull_full_type = self.hull_type
        else:
            self.hull_full_type = self.hull_type + '-' + self.hull_subtype

        for stat in stats[1:]:
            k, val = list(map(str.strip, stat.split(':', maxsplit=1)))

            key = k.lower()
            attack_match = re.match(r'attack(\s\[(\w+)])?', key)  # Match for both 'Attack' and 'Attack (ship) etc.'

            if key == 'quantity':
                self.stats[key] = int(re.match(r'(\d+)', val).group())
            elif attack_match:
                attack_type = attack_match.groups()[1] or default_attack_type
                attack_values = list(map(str.strip, val.split('/')))
                self.stats['attack'][attack_type] = [int(x) for x in attack_values]
            elif key == 'slots':
                self.parse_special_modules(val)
                self.stats[key] = val
            elif key == 'targeting order':
                self.stats['targeting order'] = list(map(str.strip, val.split(',')))
            elif key == 'current hull':
                hulls = list(map(str.strip, val.split(',')))
                current_hulls = []
                for hull_record in hulls:
                    count, hull = re.match(r'(\d+)x\s*(\d+)', hull_record).groups()
                    current_hulls.extend([int(hull)] * int(count))
                self.stats['current hull'] = current_hulls
            elif val.isnumeric():
                self.stats[key] = int(val)
            else:
                self.stats[key] = val

            if len(self.stats['targeting order']) == 0:
                self.stats['targeting order'] = targeting_orders[self.hull_subtype]

        # Fill in extra hulls at full strength if quantity is higher than specified
        if len(self.stats['current hull']) < self.stats['quantity']:
            self.stats['current hull'].extend(
                [self.stats['hull']] * (self.stats['quantity'] - len(self.stats['current hull'])))

        self.prepare_derived_stats()

    # Parse modules for any special effects like AEGIS
    def parse_special_modules(self, modules: str):
        # AEGIS
        match_aegis = re.match(r'.*AEGIS x(\d+).*', modules, re.IGNORECASE)
        if match_aegis:
            self.stats['aegis'] = self.stats['aegis'] or match_aegis.groups()[0]

        # Cruiser Targeting
        if re.match(r'.*cruiser targeting.*', modules, re.IGNORECASE):
            self.stats['targeting order'] = self.stats['targeting order'] or targeting_orders['Cruiser Targeting']

    # Prepare derived stats
    def prepare_derived_stats(self):
        # Update quantity to agree with current hull
        self.stats['quantity'] = len(self.stats['current hull'])

        # Rough power estimate based on starship attack + defence
        scaled_general_attack = [x ** 2 for x in self.stats['attack'][default_attack_type]]
        scaled_defence = self.stats['defense'] ** 2
        combat_value = (sum(scaled_general_attack) + scaled_general_attack[0] + scaled_defence * 9) ** 0.5
        self.combat_value = round(combat_value)

    def generate_statblock(self):
        stats = self.stats

        stat_strings = []
        for stat in stats:
            if stat == 'attack':
                attack_types = self.stats[stat]
                if len(attack_types) == 1:
                    stat_string = "/".join(map(str, stats[stat][default_attack_type]))
                    stat_strings.append('Attack: ' + stat_string)
                else:
                    for attack_type in self.stats[stat]:
                        stat_string = "/".join(map(str, stats[stat][attack_type]))
                        stat_strings.append('Attack [' + attack_type.capitalize() + ']: ' + stat_string)
                continue
            elif stat == 'current hull':
                hull_counter = collections.Counter(stats[stat])

                stat_string = ', '.join([str(hull_counter[hull]) + 'x ' + str(hull) for hull in hull_counter])
            elif stat == 'targeting order':
                stat_string = ", ".join(map(str, stats[stat]))
            else:
                stat_string = str(stats[stat]).strip()

            stat_strings.append(stat.title() + ': ' + stat_string)

        return f"%s [%s]\n" % (self.class_name, self.hull_full_type) + \
               '\n'.join(stat_strings)

    def generate_summary(self):
        return self.class_name + ' [' + self.hull_full_type + '] x' + str(self.stats['quantity']) + \
               ' - ' + str(self.combat_value * self.stats['quantity']) + \
               ' power rating (' + str(self.combat_value) + ' ea.)'


class Fleet:
    fleet_name = ''
    ships = []
    ship_instances = []

    fleet_filename = ''

    def __init__(self, fleet_filename: str = None):
        if fleet_filename:
            self.load_fleet_file(fleet_filename)

    def load_fleet_file(self, fleet_filename):
        self.fleet_filename = fleet_filename

        # Open OOB
        filename = os.path.join(OOB_DIR, fleet_filename)
        f = open(filename, 'r')
        oob_raw = f.read()
        f.close()

        # Split OOB into individual sections
        oob = list(map(str.strip, filter(None, oob_raw.split("\n\n"))))
        self.fleet_name = oob[0]  # First line should always be the fleet name

        ships = []
        for statblock in oob[1:]:
            ship = Ship()
            ship.parse_statblock(statblock)
            ships.append(ship)

        self.ships = ships

    def generate_fleet_oob(self):
        return self.fleet_name + '\n\n' + '\n\n'.join([ship.generate_statblock() for ship in self.ships])

    def generate_fleet_summary(self):
        return self.fleet_name + '\n\n' + '\n'.join([ship.generate_summary() for ship in self.ships])
