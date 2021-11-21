import battle
import definitions.battle_properties
from definitions.paths import OUTPUT_DIR
import random
import os

if __name__ == '__main__':
    random.seed(5555)

    battle_name = 'bully_battle'
    fleet1_filename = 'fleet_bully.txt'
    fleet2_filename = 'fleet_mixed_defender.txt'

    battle_instance = battle.Battle()
    battle_instance.load_fleet(side=definitions.battle_properties.side_a, fleet_filename=fleet1_filename)
    battle_instance.load_fleet(side=definitions.battle_properties.side_b, fleet_filename=fleet2_filename)

    battle_instance.initialise_battle()
    battle_instance.simulate_battle()

    f = open(os.path.join(OUTPUT_DIR, battle_name + '.txt'), 'w')
    f.write(battle_instance.report_summary())
    f.close()

    f = open(os.path.join(OUTPUT_DIR, battle_name + '_verbose.txt'), 'w')
    f.write(battle_instance.report_verbose())
    f.close()

    for side in battle_instance.sides.values():
        for participating_fleet in side:
            f = open(
                os.path.join(OUTPUT_DIR, battle_name + ' - ' + participating_fleet.fleet_name + ' - Post-Battle.txt'),
                'w')
            f.write(participating_fleet.generate_fleet_oob())
            f.close()
