from classes.ship import Ship

result_miss = 0
result_hit = 1
result_penetrate = 2
result_critical = 3


class BasicDefence:
    ship: Ship = None

    def __init__(self, ship: Ship):
        self.ship = ship

    def __call__(self, attack_roll: int):
        defence = self.ship.stats['defence']
        result = attack_roll - 10 - defence

        if result > 20:
            return result_critical
        elif result > 5:
            return result_penetrate
        elif result > 0:
            return result_hit
        else:
            return result_miss

