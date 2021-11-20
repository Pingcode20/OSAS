from battle import Battle, side_a, side_b
from definitions.paths import OUTPUT_DIR
import random
import os

if __name__ == '__main__':
    random.seed(5555)

    fleet1_filename = 'fleet_bully.txt'
    fleet2_filename = 'fleet_passive_defender.txt'

    battle = Battle()
    battle.load_fleet(side=side_a, fleet_filename=fleet1_filename)
    battle.load_fleet(side=side_b, fleet_filename=fleet2_filename)

    battle.initialise_battle()
    battle.simulate_battle()

    f = open(os.path.join(OUTPUT_DIR,'bully_battle.txt'), 'w')
    f.write(battle.report_summary())
    f.close()

    f = open(os.path.join(OUTPUT_DIR,'bully_battle_verbose.txt'), 'w')
    f.write(battle.report_verbose())
    f.close()

    for side in battle.sides.values():
        for participating_fleet in side:
            f = open(os.path.join(OUTPUT_DIR,participating_fleet.fleet_name + ' - Post-Battle.txt'),'w')
            f.write(participating_fleet.generate_fleet_oob())
            f.close()