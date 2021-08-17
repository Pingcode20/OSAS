class BattleEvent:
    ship_name = ''
    def __init__(self, ship_name:str):
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
        if self.attack_value < self.defence_value + 10:
            return f'%s attacks %s but is ineffective' % (self.attacker, self.defender)
        elif self.damage == 0:
            return f'%s attacks %s but misses' % (self.attacker, self.defender)
        else:
            return f'%s attacks %s for %d damage' % (self.attacker, self.defender, self.damage)


class SaturationEvent(BattleEvent):
    def show(self):
        return f'%s''s defences were saturated and it took 1 damage' % self.ship_name


class DestroyedEvent(BattleEvent):
    def show(self):
        return f'%s was destroyed!' % self.ship_name
