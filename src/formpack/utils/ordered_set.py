import collections


class OrderedSet(collections.MutableSet):
    def __init__(self, iterable=None):
        self.set = set()
        self.list = []
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.list)

    def __contains__(self, key):
        return key in self.set

    def add(self, key):
        if key not in self.set:
            self.set.add(key)
            self.list.append(key)

    def update(self, keys):
        map(self.add, keys)

    def discard(self, key):
        if key in self.set:
            self.set.discard(key)
            self.list.remove(key)

    def __iter__(self):
        curr = 0
        while curr < len(self.list):
            yield self.list[curr]
            curr += 1

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)
