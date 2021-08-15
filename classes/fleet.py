import os
from classes.ship import Ship, hull_types
from definitions import OOB_DIR

class Fleet:
    fleet_name = ''
    side = ''

    ships = {}

    fleet_filename = ''

    def __init__(self, side:str, fleet_filename: str = None):
        if fleet_filename:
            self.load_fleet_file(fleet_filename)

        self.side = side

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

        ships = {}
        for statblock in oob[1:]:
            ship = Ship(fleet=self).parse_statblock(statblock)
            ships[ship.ship_id] = ship

        self.ships = ships

    def generate_combat_list(self):
        combat_list = {hull_type: [] for hull_type in hull_types}
        for ship_id in self.ships:
            ship = self.ships[ship_id]
            combat_list[ship.hull_type] += [instance for instance in ship.instances if instance['current_hull'] > 0]
        return combat_list

    def generate_fleet_oob(self):
        return self.fleet_name + '\n\n' + '\n\n'.join([self.ships[ship].generate_statblock() for ship in self.ships])

    def generate_fleet_summary(self):
        return self.fleet_name + '\n\n' + '\n'.join([self.ships[ship].generate_summary() for ship in self.ships])

if __name__ == '__main__':
    fleet = Fleet(fleet_filename='extended_hullcount_test.txt', side='Side A')
    print(fleet.generate_fleet_summary())
    print(fleet.generate_fleet_oob())