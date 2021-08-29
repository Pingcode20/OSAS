class BattleEvent:
    ship_name = ''

    def __init__(self, ship_name: str):
        self.ship_name = ship_name

    def show(self):
        pass


class AttackEvent(BattleEvent):
    attacker = ''
    defender = ''

    attack_value = 0
    defence_value = 0

    damage = 0
    roll = 0

    def __init__(self, attacker, defender, attack_value, defence_value, damage, roll):
        self.attacker = attacker
        self.defender = defender
        self.attack_value = attack_value
        self.defence_value = defence_value
        self.damage = damage
        self.roll = roll

    def show(self):
        if self.attack_value < self.defence_value - 10:
            return f'%s attacks %s but is ineffective (1d20+%d vs %d)' % (self.attacker, self.defender, self.attack_value, self.defence_value+10)
        elif self.damage == 0:
            return f'%s attacks %s but misses (%d+%d vs %d)' % (self.attacker, self.defender, self.roll, self.attack_value, self.defence_value+10)
        else:
            return f'%s attacks %s for %d damage (%d+%d vs %d)' % (self.attacker, self.defender, self.damage, self.roll, self.attack_value, self.defence_value+10)


class SaturationEvent(BattleEvent):
    def show(self):
        return f'%s\'s defences were saturated and it took 1 damage' % self.ship_name


class DestroyedEvent(BattleEvent):
    def show(self):
        return f'%s was destroyed!' % self.ship_name


class RoundStartEvent(BattleEvent):
    current_round = 0

    def __init__(self, current_round):
        self.current_round = current_round

    def show(self):
        return f'\n====== Round %d ======\n' % self.current_round


class BattleEndEvent(BattleEvent):
    winning_fleets = []

    def __init__(self, winning_fleets: list):
        self.winning_fleets = winning_fleets

    def show(self):
        return f'Battle Ended! Victorious Fleets: %s' % ', '.join(self.winning_fleets)
