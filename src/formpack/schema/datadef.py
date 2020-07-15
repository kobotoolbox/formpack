# coding: utf-8
from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

from copy import deepcopy

from ..constants import UNSPECIFIED_TRANSLATION, UNTRANSLATED
from ..utils import str_types
from ..utils.future import OrderedDict


class FormDataDef(object):
    """ Any object composing a form. It's only used with a subclass. """

    def __init__(self, name, labels=None, has_stats=False, *args, **kwargs):
        self.name = name
        self.labels = labels or {}
        self._parent = None
        self.value_names = self.get_value_names()
        self.has_stats = has_stats

    def __repr__(self):
        return "<%s name='%s'>" % (self.__class__.__name__, self.name)

    def get_value_names(self):
        return [self.name]

    @property
    def path(self):
        return '/'.join(item.name for item in self.hierarchy[1:])

    @property
    def hierarchy(self):
        if not hasattr(self, '__hierarchy'):
            pp = self
            self.__hierarchy = hh = [pp]
            while pp._parent is not None:
                pp = pp._parent
                hh.insert(0, pp)
        return self.__hierarchy

    @property
    def root_section(self):
        return self.hierarchy[0]

    @property
    def parent_section(self):
        if not hasattr(self, '__parent_section'):
            last_section = None
            for _par in self.hierarchy:
                if _par is self:
                    return last_section
                if hasattr(_par, 'fields'):
                    last_section = _par
            self.__parent_section = last_section
        return self.__parent_section

    @property
    def section(self):
        return self.parent_section

    def _add_to_parent_section_fields(self):
        _parent_section = self.parent_section
        if self.name in _parent_section.fields:
            if _parent_section.fields[self.name] is not self:
                raise ValueError('duplicate name?')
        else:
            _parent_section.fields[self.name] = self

    def set_parent(self, parent):
        # since this is called immediately after items are instanitated
        # we can probably move this into the __init__ method
        if self._parent is None:
            self._parent = parent
        if not issubclass(self.__class__, (FormGroup, FormSection)):
            self._add_to_parent_section_fields()
        elif issubclass(self.__class__, FormSection):
            _parent_section = self.parent_section
            if self in _parent_section.children:
                raise ValueError('duplicate?')
            _parent_section.children.append(self)
        return self


class FormGroup(FormDataDef):  # useful to get __repr__
    pass


class FormSection(FormDataDef):
    """ The tabular representation of a repeatable group of fields """

    def __init__(self, name="submissions", labels=None, fields=None,
                 parent=None, children=(),
                 *args, **kwargs):

        if labels is None:
            labels = {UNTRANSLATED: 'submissions'}

        super(FormSection, self).__init__(name, labels, *args, **kwargs)
        self.fields = fields or OrderedDict()
        self.parent = parent
        self.children = list(children)


    def get_label(self, lang=UNSPECIFIED_TRANSLATION):
        return [self.labels.get(lang) or self.name]

    def __repr__(self):
        parent_name = getattr(self.parent_section, 'name', '')
        return "<FormSection name='%s' parent='%s'>" % (self.name, parent_name)

class FormRootSection(FormSection):
    pass

class FormRepeatSection(FormSection):
    pass


class FormChoice(FormDataDef):
    def __init__(self, name, *args, **kwargs):
        super(FormChoice, self).__init__(name, *args, **kwargs)
        self.name = name
        self.options = OrderedDict()

def form_choice_list_from_json_definition(definition,
                                          translation_list,
                                          translation_names):
    all_choices = {}
    for choice_definition in definition:
        choice_value = choice_definition['value']
        choice_key = choice_definition['list_name']

        if choice_key not in all_choices:
            all_choices[choice_key] = FormChoice(choice_key)
        choices = all_choices[choice_key]

        option = choices.options[choice_value] = {}

        if 'label' in choice_definition:
            _label = choice_definition['label']
        else:
            _label = choice_definition.get('image')

        if _label is None:
            _label = {}

        _anchors = [tx['$anchor'] for tx in translation_list]
        _labels = [_label.get(tx_anchor, '') for tx_anchor in _anchors]

        option['labels'] = OrderedDict(zip(translation_names, _labels))
        option['name'] = choice_value
    return all_choices
