import collections
import classes.combat_scoreboard as st
import re
import uuid

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
    instances = []

    def __init__(self, fleet=None):
        self.stats = collections.OrderedDict({
            'attack': {default_attack_type: [0, 0, 0, 0]},
            'defense': 0,
            'saturation': 0,
            'speed': 0,
            'jump': 0,
            'hull': 1,
            'slots': '',
            'aegis': 0,
            'targeting order': []
        })
        self.class_id = uuid.uuid4()
        self.fleet = fleet
        self.combat_scorecard = {}

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
            attack_match = re.match(r'attack(\s\[(\w+)])?', key)  # Match for both 'Attack' and 'Attack (ship) etc.'

            if key == 'quantity':
                quantity = int(re.match(r'(\d+)', val).group())
            elif attack_match:
                attack_type = attack_match.groups()[1] or default_attack_type
                attack_values = list(map(str.strip, val.split('/')))
                self.stats['attack'][attack_type] = [int(x) for x in attack_values]
            elif key == 'slots':
                self.parse_special_modules(val)
                self.stats[key] = val
            elif key == 'targeting order':
                # Clean up targeting order to remove formatting issues
                target_values = val.split(',')
                self.stats['targeting order'] = [target.strip().rstrip('s').title() for target in target_values]
            elif key == 'current hull':
                hulls = list(map(str.strip, val.split(',')))
                for hull_record in hulls:
                    count, hull = re.match(r'(\d+)x\s*(\d+)', hull_record).groups()
                    current_hulls.extend([int(hull)] * int(count))
            elif val.isnumeric():
                self.stats[key] = int(val)
            else:
                self.stats[key] = val

        if len(self.stats['targeting order']) == 0:
            self.stats['targeting order'] = targeting_orders[self.hull_subtype]

        self.prepare_derived_stats()
        self.initialise_instances(current_hulls=current_hulls, quantity=quantity)

        return self

    # Parse modules for any special effects like AEGIS
    def parse_special_modules(self, modules: str):
        # AEGIS
        match_aegis = re.match(r'.*AEGIS x(\d+).*', modules, re.IGNORECASE)
        if match_aegis:
            self.stats['aegis'] = self.stats['aegis'] or int(match_aegis.groups()[0])

        # Cruiser Targeting
        if re.match(r'.*cruiser targeting.*', modules, re.IGNORECASE):
            self.stats['targeting order'] = self.stats['targeting order'] or targeting_orders['Cruiser Targeting']

    # Prepare derived stats
    def prepare_derived_stats(self):
        # Rough power estimate based on starship attack + defence
        scaled_general_attack = [x ** 2 for x in self.stats['attack'][default_attack_type]]
        scaled_defence = self.stats['defense'] ** 2
        combat_value = (sum(scaled_general_attack) + scaled_general_attack[0] + scaled_defence * 9) ** 0.5
        self.combat_value = round(combat_value)

        self.initiative = self.stats['speed'] or 1
        self.target_weight = self.stats['speed'] or 1

    def initialise_instances(self, current_hulls, quantity):
        # Fill in extra hulls at full strength if quantity is higher than specified
        if len(current_hulls) < quantity:
            current_hulls.extend(
                [self.stats['hull']] * (quantity - len(current_hulls)))

        # Generate instances
        instances = []
        ship_id = 1
        for current_hull in current_hulls:
            instance = {
                'current_hull': current_hull,
                'saturation': self.stats['saturation'],
                'name': self.fleet.fleet_name + ' ' + self.short_name + ' #' + str(ship_id),
                'ship': self,
                'ship_id': uuid.uuid4()
            }
            instances.append(instance)
            ship_id += 1
        self.instances = instances

    def update_scorecard(self, current_round, field, points):
        if current_round not in self.combat_scorecard: self.combat_scorecard[current_round] = st.Scoreboard()

        self.combat_scorecard[current_round][field] = self.combat_scorecard[current_round].get(field, 0) + points

    def display_scorecard(self, current_round):
        if current_round not in self.combat_scorecard: return ''
        scorecard = self.combat_scorecard[current_round]
        return self.class_name + ': ' + scorecard.show()

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
            elif stat == 'targeting order':
                stat_string = ", ".join(map(str, stats[stat]))
            else:
                stat_string = str(stats[stat]).strip()

            stat_strings.append(stat.title() + ': ' + stat_string)

        hull_counter = collections.Counter([instance['current_hull'] for instance in self.instances])
        hull_string = ', '.join([str(hull_counter[hull]) + 'x ' + str(hull) for hull in hull_counter])
        stat_strings.append('Current Hull: ' + hull_string)

        return f"%s [%s]\n" % (self.class_name, self.hull_full_type) + f"Quantity: %d\n" % (len(self.instances)) + \
               '\n'.join(stat_strings)

    def generate_summary(self):
        quantity = len([inst for inst in self.instances if inst['current_hull'] > 0])
        hull_counter = collections.Counter(
            [instance['current_hull'] for instance in self.instances if instance['current_hull'] > 0])
        hull_string = ', '.join([str(hull_counter[hull]) + 'x ' + str(hull) for hull in hull_counter]) or 'None Left'

        return self.class_name + ' [' + self.hull_full_type + '] x' + str(quantity) + ' - ' + str(
            self.combat_value * quantity) + ' power rating (' + str(
            self.combat_value) + ' ea.)' + ' - Hull: ' + hull_string

    def get_quantity(self):
        return len([inst for inst in self.instances if inst['current_hull'] > 0])
