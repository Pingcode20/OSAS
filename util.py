import numpy, random


def rect2pol(x: float, y: float):
    r = numpy.sqrt(numpy.power(x, 2) + numpy.power(y, 2))
    theta = numpy.arctan2(y, x)

    return r, theta


def pol2rect(r: float, theta: float):
    x = r * numpy.cos(theta)
    y = r * numpy.sin(theta)

    return x, y


# Calculate polar vector between two cartesian points
def rect_vector(a, b):
    return rect2pol(b[0] - a[0], b[1] - a[1])


# Weighted Random Shuffle
# http://utopia.duth.gr/~pefraimi/research/data/2007EncOfAlg.pdf
def weighted_shuffle(items, weights):
    order = sorted(range(len(items)), key=lambda i: random.random() ** (1.0 / weights[i]))
    return [items[i] for i in order]


if __name__ == '__main__':
    print('util test')

    print(rect_vector([2, 2], [-1, -1]))
