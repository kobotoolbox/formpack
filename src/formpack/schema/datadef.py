# coding: utf-8
from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

from ..constants import UNSPECIFIED_TRANSLATION, UNTRANSLATED
from ..utils import str_types
from ..utils.future import OrderedDict


class FormDataDef(object):
    """ Any object composing a form. It's only used with a subclass. """

    def __init__(self, name, labels=None, has_stats=False, *args, **kwargs):
        self.name = name
        self.labels = labels or {}
        self.has_stats = has_stats

    def __repr__(self):
        return "<%s name='%s'>" % (self.__class__.__name__, self.name)

    def get_value_names(self):
        return [self.name]

    @classmethod
    def from_json_definition(cls, definition, translations=None):
        labels = cls._extract_json_labels(definition, translations)
        return cls(definition['name'], labels)

    @classmethod
    def _extract_json_labels(cls, definition, translations):
        """ Extract translation labels from the JSON data definition """
        label = definition.get('label')
        if label:
            labels = OrderedDict(zip(translations, label))
        else:
            labels = {}
        return labels


class FormGroup(FormDataDef):  # useful to get __repr__
    pass


class FormSection(FormDataDef):
    """ The tabular representation of a repeatable group of fields """

    def __init__(self, name="submissions", labels=None, fields=None,
                 parent=None, children=(), hierarchy=(None,),
                 *args, **kwargs):

        if labels is None:
            labels = {UNTRANSLATED: 'submissions'}

        super(FormSection, self).__init__(name, labels, *args, **kwargs)
        self.fields = fields or OrderedDict()
        self.parent = parent
        self.children = list(children)

        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    @classmethod
    def from_json_definition(cls, definition, hierarchy=(None,), parent=None,
                             translations=None):
        labels = cls._extract_json_labels(definition, translations)
        return cls(definition['name'], labels, hierarchy=hierarchy, parent=parent)

    def get_label(self, lang=UNSPECIFIED_TRANSLATION):
        return [self.labels.get(lang) or self.name]

    def __repr__(self):
        parent_name = getattr(self.parent, 'name', None)
        return "<FormSection name='%s' parent='%s'>" % (self.name, parent_name)


class FormChoice(FormDataDef):
    def __init__(self, name, *args, **kwargs):
        super(FormChoice, self).__init__(name, *args, **kwargs)
        self.name = name
        self.options = OrderedDict()

    @classmethod
    def all_from_json_definition(cls, definition, translation_list):
        all_choices = {}
        for choice_definition in definition:
            choice_name = choice_definition.get('name')
            choice_key = choice_definition.get('list_name')
            if not choice_name or not choice_key:
                continue

            if choice_key not in all_choices:
                all_choices[choice_key] = FormChoice(choice_key)
            choices = all_choices[choice_key]

            option = choices.options[choice_name] = {}

            # apparently choices dont need a label if they have an image
            if 'label' in choice_definition:
                _label = choice_definition['label']
            else:
                _label = choice_definition.get('image')
            if isinstance(_label, str_types):
                _label = [_label]
            elif _label is None:
                _label = []
            option['labels'] = OrderedDict(zip(translation_list, _label))
            option['name'] = choice_name
        return all_choices

    @property
    def translations(self):
        for option in self.options.values():
            for translation in option['labels'].keys():
                yield translation
