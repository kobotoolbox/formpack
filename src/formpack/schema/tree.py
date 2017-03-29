# coding: utf-8

class FormTreeRoot(object):
    def __init__(self, version):
        self._version = version
        self._children = []
        self._group_stack = []

    def __repr__(self):
        return '* FormTreeRoot'

    def iterfields(self,
                   include_sections=False,
                   include_groups=False,
                   include_group_ends=None,
                   ):
        for kid in self._children:
            _is_group = isinstance(kid, FormTreeGroupSection)
            if _is_group and include_groups:
                yield kid
            elif not _is_group:
                yield kid
            if _is_group:
                for subkid in kid._children:
                    yield subkid
                if include_group_ends:
                    yield FormTreeGroupEnd(kid)

    @property
    def _current(self):
        if len(self._group_stack) > 0:
            return self._group_stack[-1]
        else:
            return self

    def push_group(self, grp, repeat=False):
        item = FormTreeRepeat(grp) if repeat else FormTreeGroup(grp)
        item._next_ancestor = self._current
        self._group_stack.append(item)
        self._children.append(item)

    def pop_group(self):
        self._group_stack.pop()

    def push_field(self, field):
        self._current.append_kid(field)

    def append_kid(self, kid):
        self._children.append(kid)
        kid._next_ancestor = self


class FormTreeGroupSection(object):
    def __init__(self, origin):
        self._children = []
        self._origin = origin
        self.name = origin.name
        self.path = origin.path
        self.src = origin.src

    def append_kid(self, kid):
        self._children.append(kid)
        kid._next_ancestor = self

    def __repr__(self):
        return '*{ {} }'.format(repr(self._origin))

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
        return '{}_end'.format(self.related_group.type)

    @property
    def ancestors(self):
        return self.related_group.ancestors
