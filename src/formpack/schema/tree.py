# coding: utf-8


class Iterfielded:
    def iterfields(self,
                   include_groups=False,
                   include_group_ends=None,
                   traverse_repeats=True,
                   ):
        for kid in self._children:
            _is_group = isinstance(kid, FormTreeGroupSection)
            _is_repeat = _is_group and kid.type == "repeat"
            if (_is_group and include_groups) or not _is_group:
                yield kid
            _traverse_this = False if (_is_repeat and not traverse_repeats) else _is_group
            if _traverse_this:
                for subkid in kid.iterfields(
                       include_groups=include_groups,
                       include_group_ends=include_group_ends,
                       ):
                    yield subkid
                if include_group_ends:
                    yield FormTreeGroupEnd(kid)


class FormTreeRoot(object, Iterfielded):
    def __init__(self, version):
        self._version = version
        self._children = []
        self._group_stack = []

    def __repr__(self):
        return '* FormTreeRoot'

    @property
    def _current(self):
        if len(self._group_stack) > 0:
            return self._group_stack[-1]
        else:
            return self

    def push_group(self, grp, repeat=False):
        item = FormTreeRepeat(grp) if repeat else FormTreeGroup(grp)
        item._next_ancestor = self._current
        self._current._children.append(item)
        self._group_stack.append(item)

    def pop_group(self, repeat=False):
        ppd = self._group_stack.pop()
        assert ppd.type == 'repeat' if repeat else 'group'

    def push_field(self, field):
        self._current.append_kid(field)

    def append_kid(self, kid):
        self._children.append(kid)
        kid._next_ancestor = self


class FormTreeGroupSection(object, Iterfielded):

    def __init__(self, origin):
        self._children = []
        self._origin = origin
        origin._intree = self
        self.name = origin.name
        self.path = origin.path
        self._full_path = origin._full_path
        self.src = origin.src

    def append_kid(self, kid):
        self._children.append(kid)
        kid._next_ancestor = self

    def __repr__(self):
        return ':'.join([self.__class__.__name__,
                         repr(self._origin)])

    @property
    def type(self):
        return self.TYPE

    @property
    def ancestors(self):
        ptr = self
        arr = [self]
        while hasattr(ptr, '_next_ancestor'):
            arr.append(ptr._next_ancestor)
            ptr = ptr._next_ancestor
        return arr


class FormTreeGroup(FormTreeGroupSection):
    TYPE = 'group'


class FormTreeRepeat(FormTreeGroupSection):
    TYPE = 'repeat'


class FormTreeGroupEnd(object):
    def __init__(self, related_group):
        self.related_group = related_group
        self.name = None
        self.path = None
        self.src = {}

    @property
    def type(self):
        return 'end_{}'.format(self.related_group.type)

    @property
    def ancestors(self):
        return self.related_group.ancestors
