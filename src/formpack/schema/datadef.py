# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

import re

try:
    xrange = xrange
except NameError:  # python 3
    xrange = range

try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from ..constants import UNTRANSLATED
from ..translated_item import TranslatedItem


class FormDataDef(object):
    """ Any object composing a form. It's only used with a subclass. """

    def __init__(self, name, labels=None,
                 has_stats=False, src=None,
                 *args, **kwargs):
        self.name = name
        # assert labels is None or isinstance(labels, TranslatedItem)
        self.labels = labels or TranslatedItem()
        self.value_names = self.get_value_names()
        self.has_stats = has_stats
        self.src = src or {}

    def __repr__(self):
        return "{} <{}>".format(self.__class__.__name__, self.name)

    def get_value_names(self):
        return [self.name]

    @property
    def ancestors(self):
        # assert that return value == self._hierarchy
        if self._parent is None:
            return [self]
        return self._parent.ancestors + [self]

    @property
    def is_root(self):
        return False


class FormGroup(FormDataDef):  # useful to get __repr__
    def set_parent(self, item):
        # a workaround to ensure parent can be set consistently
        self._group_parent = item

    @property
    def _parent(self):
        return self._group_parent

    @property
    def type(self):
        return 'group'


class FormSection(FormDataDef):
    """ The tabular representation of a repeatable group of fields """

    def __init__(self, name="submissions", labels=None, fields=None,
                 parent=None, children=(), hierarchy=(None,),
                 *args, **kwargs):

        if labels is None:
            labels = TranslatedItem()

        self._parent = parent
        super(FormSection, self).__init__(name, labels, *args, **kwargs)
        self.fields = fields or OrderedDict()
        self.children = list(children)

        self._hierarchy = list(hierarchy) + [self]

        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    @property
    def type(self):
        return 'repeat'

    @property
    def parent_section(self):
        try:
            return next(anc for anc in self.ancestors[:-1][::-1]
                        if isinstance(anc, FormSection))
        except StopIteration:
            return None

    @property
    def hierarchy(self):
        _ancestors = self.ancestors
        if len(_ancestors) == 1:
            return [None] + _ancestors
        return self._hierarchy

    @property
    def rows(self, include_groups=False):
        for (name, field) in self.fields.items():
            if include_groups and hasattr(self, 'begin_rows'):
                for row in self.begin_rows:
                    yield row.src

            yield field.src

            if include_groups and hasattr(self, 'end_rows'):
                for row in self.end_rows:
                    yield row.src

    def get_label(self, lang=UNTRANSLATED):
        return [self.labels.get(lang) or self.name]


class FormRoot(FormSection):
    @property
    def is_root(self):
        return True

    @property
    def type(self):
        return 'root'


class FormChoice(FormDataDef):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.options = kwargs.pop('options', OrderedDict())
        super(FormChoice, self).__init__(name, *args, **kwargs)

    @property
    def translations(self):
        for option in self.options.values():
            for translation in option['labels'].keys():
                yield translation
