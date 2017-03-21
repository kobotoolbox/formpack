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
        self.src = src

    def __repr__(self):
        return "{} <{}>".format(self.__class__.__name__, self.name)

    def get_value_names(self):
        return [self.name]


class FormGroup(FormDataDef):  # useful to get __repr__
    pass


class FormSection(FormDataDef):
    """ The tabular representation of a repeatable group of fields """

    def __init__(self, name="submissions", labels=None, fields=None,
                 parent=None, children=(), hierarchy=(None,),
                 *args, **kwargs):

        if labels is None:
            labels = TranslatedItem()

        self.parent = parent
        super(FormSection, self).__init__(name, labels, *args, **kwargs)
        self.fields = fields or OrderedDict()
        self.children = list(children)

        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

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

    def __repr__(self):
        parent_name = getattr(self.parent, 'name', None)
        return "<FormSection name='%s' parent='%s'>" % (self.name, parent_name)


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
