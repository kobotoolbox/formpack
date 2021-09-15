# -*- coding: utf-8 -*-
from collections import Counter, OrderedDict
from collections.abc import Callable

from .string import orderable_with_none


class OrderedCounter(Counter, OrderedDict):
    """
    Counter that keeps insertion order compatible with Python 2.7+

    Useless for Python3.6+ because Counter keeps insertion order.

    Source: https://stackoverflow.com/a/23747652
    """

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

    def __reduce__(self):
        return self.__class__, (OrderedDict(self),)

    def most_common(self, n=None, ordered=False):
        """
        If `ordered` is `True`, it sorts (ascendant) elements with equal counts,
        not ordered arbitrarily like `Counter` does.

        TODO: Not used with ordered=True so far. Discuss with other members of
        team if it's needed, otherwise delete it.

        Args:
            n (int): Optional
            ordered (bool): Optional

        Returns:
            list: list of tuples (items, count)
        """
        if ordered is False:
            return super().most_common(n)

        # We can use `lambda x: (-x[1], x[0])` to sort by:
        # - second element (descendant order)
        # - first element (ascendant order)
        # because elements of `Counter` are tuples (<item>, <count)
        most_common_ = sorted(iter(self.items()),
                              key=lambda x: (-x[1], orderable_with_none(x[0])))
        if n is None:
            return most_common_

        return most_common_[:n]


class OrderedDefaultdict(OrderedDict):
    """
    defaultdict that keeps insertion order compatible with Python 2.7+

    Source: https://stackoverflow.com/a/4127426

    """

    def __init__(self, default_factory=None, *args, **kwargs):
        if not (default_factory is None
                or isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable or None')
        super().__init__(*args, **kwargs)
        self.default_factory = default_factory  # called by __missing__()

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key, )
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else tuple()
        return self.__class__, args, None, None, iter(self.items())

    def __repr__(self):  # optional
        return '%s(%r, %r)' % (self.__class__.__name__, self.default_factory,
                               list(iter(self.items())))
