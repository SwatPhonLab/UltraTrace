import utils

from uuid import uuid4

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iadd__(self, other):
        if isinstance(other, Point):
            self.x += other.x
            self.y += other.y
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            self.x += other[0]
            self.y += other[1]
        else:
            raise TypeError(f'cannot add Point and {type(other)}')

    def __imul__(self, factor):
        if isinstance(factor, (int, float)):
            self.x *= factor
            self.y *= factor
        else:
            raise TypeError(f'cannot multiply Point and {type(other)}')

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        elif isinstance(other, (tuple, list)) and len(other) == 2:
            return Point(self.x + other[0], self.y + other[1])
        else:
            raise TypeError(f'cannot add Point and {type(other)}')

    def __mul__(self, factor):
        if isinstance(factor, (int, float)):
            return Point(self.x * factor, self.y * factor)
        else:
            raise TypeError(f'cannot multiply Point and {type(other)}')

class XHairsList:
    def __init__(self, trace):
        self.trace = trace
        self.xhairs = []

    def __len__(self):
        return len(self.xhairs)

    def __iter__(self):
        for xhair in self.xhairs:
            if not xhair.is_removed:
                yield xhair

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.xhairs[index]
        elif isinstance(index, str):
            # FIXME: this is inefficient :/
            for xhair in self:
                if xhair.id == index:
                    return xhair
            raise KeyError(f'cannot find xhair with index "{index}"')
        else:
            raise TypeError(f'cannot index xhairs with type "{type(index)}"')

    def __contains__(self, xhair):
        try:
            self.xhairs[xhair] # no-op
            return True
        except KeyError:
            return False

    def add(self, xhair):
        if isinstance(xhair, XHair):
            if xhair in self:
                self.xhair.is_removed = False
            else:
                # FIXME configure MAX_NUM_XHAIRS
                self.xhairs.append(xhair)
        else:
            raise TypeError(f'cannot add xhair of type "{type(xhair)}"')

    def remove(self, xhair):
        self.xhair.is_removed = True

    def __repr__(self):
        return f'[{",".join(map(repr, self))}]'

    def __str__(self):
        return f'[{",".join(map(str, self))}]'

    def prune(self):
        # run this before saving, ideally
        self.xhairs = [ xh for xh in self ] # __iter__ skips if is_removed

class XHair:
    def __init__(self, x, y):
        self.id = uuid4()
        self.coords = Point(x, y)
        self.is_removed = False

    def __iadd__(self, dx, dy):
        self.coords += (dx, dy)

    def __imul__(self, factor):
        self.coords *= factor

    def __add__(self, dx, dy):
        return self.coords + (dx, dy)

    def __mul__(self, factor):
        return self.coords * factor

    def __repr__(self):
        return f'XHair<{self.id}>(self.coords.x,self.coords.y)'

    def __str__(self):
        return f'XHair(self.coords.x,self.coords.y)'
