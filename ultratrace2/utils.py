import sys

class __AbstractList: pass

class TypedList(__AbstractList):
    _ItemType = type(None)
    def __init__(self, *items):
        self.items = []
        for item in items:
            if type(item) == self._ItemType:
                self.add(item)
            elif type(item) == tuple:
                self.add(self._ItemType(*item))
            else:
                self.add(self._ItemType(item))
    def _enforce_type(self, item):
        if type(item) != self._ItemType:
            raise TypeError(f'cannot add <{type(item).__name__}> to List<{self._ItemType.__name__}>')
    def __eq__(self, other):
        if type(super(type(self))) != type(super(type(other))):
            return False
        if self._ItemType != other._ItemType:
            return False
        for my_item, other_item in zip(self, other):
            if my_item != other_item:
                return False
        return True
    def __len__(self):
        return len(self.items)
    def __iter__(self):
        for item in self.items:
            yield item
    def add(self, item):
        self._enforce_type(item)
        self.items.append(item)
    def remove(self, item):
        self._enforce_type(item)
        self.items.remove(item)
    def __contains__(self, item):
        self._enforce_type(item)
        for my_item in self:
            if my_item == item:
                return True
        return False
    def __getitem__(self, index):
        if isinstance(index, int):
            return self.items[index]
        else:
            raise TypeError(f'cannot index with type {type(index)}')
    def __repr__(self):
        return f'[{",".join(map(repr,self))}]'
    def __str__(self):
        return f'[{",".join(map(str,self))}]'
    @classmethod
    def of(cls, ItemType):
        if type(ItemType) != type:
            raise ValueError(f'expected a <type>, got <{ItemType}>')
        class Container(cls):
            _ItemType = ItemType
        return Container

class TypedHashList(TypedList):
    def __init__(self, *items):
        super().__init__(*items)
        self.table = {}
    def add(self, item):
        if item in self:
            raise ValueError('cannot have multiple copies of the same {type(item)}')
        self.items.append(item)
        self.table[hash(item)] = item
    def remove(self, item):
        super().remove(item)
        del self.table[hash(item)]
    def __contains__(self, item):
        self._enforce_type(item)
        return hash(item) in self.table
    def __getitem__(self, index):
        try:
            return self.table[index]
        except KeyError:
            pass
        return super().__getitem__(index)

def log(level, *msgs):
    print(level + ': ', ' '.join(map(str, msgs)), file=sys.stderr)

def severe(*msgs):
    log('SEVERE', *msgs)

def error(*msgs):
    log('ERROR', *msgs)

def warn(*msgs):
    log('WARN', *msgs)

def info(*msgs):
    log('INFO', *msgs)

def debug(*msgs):
    log('DEBUG', *msgs)

NotReached = False

if __name__ == '__main__':

    class IntList(TypedList):
        _ItemType = int

    il = IntList()

    il.add(2)
    il.add(3)
    il.add(4)

    assert 2 in il
    assert 3 in il
    assert 4 in il

    assert len(il) == 3

    for i, item in enumerate(il):
        assert (i+2) == item

    assert il[0] == 2
    assert il[1] == 3
    assert il[2] == 4

    assert repr(il) == '[2,3,4]'
    assert str(il) == '[2,3,4]'

    il.add(5)

    assert len(il) == 4
    assert 5 in il
    assert il[3] == 5

    il.remove(5)

    assert len(il) == 3
    assert 5 not in il

    try:
        il[3]
        assert NotReached
    except IndexError:
        pass

    try:
        il.add(1.0)
        assert NotReached
    except TypeError:
        pass

    try:
        il.remove(2.0)
        assert NotReached
    except TypeError:
        pass

    try:
        3.0 in il
        assert NotReached
    except TypeError:
        pass

    assert il == IntList(2,3,4)
    assert il == TypedList.of(int)(2,3,4)

    FloatList = TypedList.of(float)

    assert FloatList(1.0, 2.0, 3.0) == FloatList(1.0, 2.0, 3.0)

    class IntWrapper:
        def __init__(self, i):
            self.i = i
        def __eq__(self, other):
            return self.i == other.i

    IntWrapperList = TypedList.of(IntWrapper)

    assert IntWrapperList(IntWrapper(6), IntWrapper(9)) == IntWrapperList(IntWrapper(6), IntWrapper(9))
    assert IntWrapperList(IntWrapper(6), IntWrapper(9)) == IntWrapperList(6, 9)

    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def __eq__(self, other):
            if type(other) != Point:
                return False
            return self.x == other.x and self.y == other.y
        def __hash__(self):
            return hash((self.x, self.y))

    PointList = TypedList.of(Point)

    assert PointList(Point(1,2), Point(3,4)) == PointList(Point(1,2), Point(3,4))
    assert PointList(Point(1,2), Point(3,4)) == PointList((1,2),(3,4))

    PointHash = TypedHashList.of(Point)

    ph = PointHash()

    assert len(ph) == 0
    assert Point(0,0) not in ph

    ph.add(Point(0,0))

    assert Point(0,0) in ph
    assert Point(0,1) not in ph

    ph.add(Point(0,1))
    ph.add(Point(0,2))

    assert Point(0,1) in ph
    assert Point(0,2) in ph

    for i, pt in enumerate(ph):
        assert Point(0, i) == pt

    ph.remove(Point(0,1))

    assert Point(0,1) not in ph

    assert ph[0] == Point(0,0)
    assert ph[1] == Point(0,2)

    try:
        ph[2]
        assert NotReached
    except IndexError:
        pass
