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


class FormDataDef(object):
    """ Any object composing a form. It's only used with a subclass. """

    def __init__(self, name, labels=None, has_stats=False, *args, **kwargs):
        self.name = name
        self.labels = labels or {}
        self.value_names = self.get_value_names()
        self.has_stats = has_stats

    def __repr__(self):
        return "<%s name='%s'>" % (self.__class__.__name__, self.name)

    def get_value_names(self):
        return [self.name]

    @classmethod
    def from_json_definition(cls, definition):
        labels = cls._extract_json_labels(definition)
        return cls(definition['name'], labels)

    @classmethod
    def _extract_json_labels(cls, definition):
        """ Extract translation labels from the JSON data definition """
        labels = OrderedDict()
        if "label" in definition:
            labels['_default'] = definition['label']

        for key, val in definition.items():
            if key.startswith('label:'):
                # sometime the label can be separated with 2 ::
                _, lang = re.split(r'::?', key, maxsplit=1, flags=re.U)
                labels[lang] = val
        return labels


class FormGroup(FormDataDef):  # useful to get __repr__
    pass


class FormSection(FormDataDef):
    """ The tabular representation of a repeatable group of fields """

    def __init__(self, name="submissions", labels=None, fields=None,
                 parent=None, children=(), hierarchy=(None,),
                 *args, **kwargs):

        if labels is None:
            labels = {'_default': 'submissions'}

        super(FormSection, self).__init__(name, labels, *args, **kwargs)
        self.fields = fields or OrderedDict()
        self.parent = parent
        self.children = list(children)

        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    @classmethod
    def from_json_definition(cls, definition, hierarchy=(None,), parent=None):
        labels = cls._extract_json_labels(definition)
        return cls(definition['name'], labels, hierarchy=hierarchy, parent=parent)

    def get_label(self, lang="_default"):
        return [self.labels.get(lang) or self.name]

    def __repr__(self):
        parent_name = getattr(self.parent, 'name', None)
        return "<FormSection name='%s' parent='%s'>" % (self.name, parent_name)


class FormChoice(FormDataDef):

    def __init__(self, name, *args, **kwargs):
        super(FormChoice, self).__init__(name, *args, **kwargs)
        self.name = name
        self.options = {}

    @classmethod
    def from_json_definition(cls, definition):
        raise NotImplemented('Use all_from_json_definition() or __init__()')

    @classmethod
    def all_from_json_definition(cls, definition):

        all_choices = {}
        for choice_definition in definition:

            # get the name, from one of the possible keys
            for alias in ('list_name', 'list name', 'List_name'):
                choice_key = choice_definition.get(alias)
                if choice_key:
                    break
            else: # handle no list_name given
                continue

            choice_name = choice_definition.get('name')
            if not choice_name:
                continue

            try:
                choices = all_choices[choice_key]
            except KeyError:
                choices = all_choices[choice_key] = cls(choice_key)

            option = choices.options[choice_name] = {}
            option['labels'] = cls._extract_json_labels(choice_definition)
            option['name'] = choice_name

        return all_choices

    @property
    def translations(self):
        for option in self.options.values():
            for translation in option['labels'].keys():
                yield translation
