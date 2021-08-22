import collections
from si_prefix import si_format

quantity = 'surviving'
shots = 'shots'
hits = 'hits'
misses = 'misses'
damage = 'dmg inflicted'
attack = 'off. score'
defence = 'def. score'
hull_loss = 'dmg taken'
saturation = 'sat dmg taken'


class Scoreboard(collections.OrderedDict):

    def __init__(self, input: dict = {}):
        default_dict = {
            quantity: 0,
            hits: 0,
            misses: 0,
            damage: 0,
            hull_loss: 0,
            saturation: 0,
            attack: 0,
            defence: 0,
        }

        super(Scoreboard, self).__init__(default_dict)
        self.update(input)

    def show(self):
        strings = []
        for k in self:
            if self[k] > 999:
                strings.append(k.title() + ': ' + si_format(self[k], precision=2))
            else:
                strings.append(k.title() + ': ' + str(self[k]))
        return ', '.join(strings)
