from pathlib import Path
from classes.ship import Ship, Fleet

fleet_filename = 'unifiedfleet.txt'

if __name__ == '__main__':
    fleet = Fleet(fleet_filename=fleet_filename)

    print(fleet.generate_fleet_oob())
