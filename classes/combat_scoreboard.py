import collections
from si_prefix import si_format

quantity = 'surviving'
losses = 'losses'
shots = 'shots'
hits = 'hits'
misses = 'misses'
damage = 'dmg inflicted'
attack = 'off. score'
defence = 'def. score'
hull_loss = 'dmg taken'
saturation = 'sat dmg taken'


class Scoreboard(collections.OrderedDict):

    def __init__(self, ship, initial_input: dict = {}):
        default_dict = {
            quantity: 0,
            losses: 0,
            hits: 0,
            misses: 0,
            damage: 0,
            hull_loss: 0,
            saturation: 0,
            attack: 0,
            defence: 0,
        }

        super(Scoreboard, self).__init__(default_dict)
        self.update(initial_input)
        self.ship = ship

    def rating(self):
        return self[attack] + self[defence]

    # Show basic stats. Ship, quantity, lost, rating
    def show_basic(self):
        strings = list()

        strings.append(quantity + ': ' + str(quantity))
        strings.append(losses + ': ' + str(losses))
        strings.append('Rating' + ': ' + self.rating())

        return ', '.join(strings)

    # Shots fired, Misses, etc. Category
    def show_details(self):
        pass

    # Detailed logs
    def show_log(self):
        pass

    # Show single line view
    def show_line(self):
        strings = []
        for k in self:
            if self[k] > 999:
                strings.append(k.title() + ': ' + si_format(self[k], precision=2))
            else:
                strings.append(k.title() + ': ' + str(self[k]))
        return ', '.join(strings)


def format_number(num):
    if num > 999:
        return si_format(num, precision=2)
    else:
        return str(num)
