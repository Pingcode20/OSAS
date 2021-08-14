from pathlib import Path
from classes.ship import Ship, Fleet

fleet1_filename = 'extended_hullcount_test.txt'
fleet2_filename = 'opik.txt'

if __name__ == '__main__':
    fleet_a = Fleet(fleet_filename=fleet1_filename)
    fleet_b = Fleet(fleet_filename=fleet2_filename)


    print(fleet_a.generate_fleet_oob())
    # print('\n')
    # print(fleet_b.generate_fleet_summary())
