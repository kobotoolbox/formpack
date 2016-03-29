# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict


class FormInfo(object):
    """ Any object composing a form. It's only used with a subclass. """

    def __init__(self, name, labels):
        self.name = name
        self.value_names = [self.name]
        self.labels = labels

    def __repr__(self):
        return "<%s name='%s'>" % (self.__class__.__name__, self.name)

    @classmethod
    def from_json_definition(cls, definition):
        labels = cls._extract_json_labels(definition)
        return cls(definition['name'], labels)

    @classmethod
    def _extract_json_labels(cls, definition):
        """ Extract translation labels from the JSON data definition """
        labels = OrderedDict({'_default': definition['name']})
        if "label" in definition:
            labels['_default'] = definition['label']
        else:
            for key, val in definition.items():
                if key.startswith('label::'):
                    _, lang = key.split('::')
                    labels[lang] = val
        return labels


class FormField(FormInfo):
    """ A form field definition knowing how to find and format data """

    def __init__(self, name, labels, data_type, hierarchy=(None,),
                 section=None, can_format=True):
        super(FormField, self).__init__(name, labels)
        self.data_type = data_type
        self.section = section
        self.can_format = can_format
        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    def get_labels(self, lang="_default", group_sep=None, multiple_select="both"):
        """ Return a list of labels for this field.

            Most fields have only one label, so the list contains only one item,
            but some fields can multiple values, and one label for each
            value.
        """
        if group_sep:
            path = []
            for level in self.hierarchy[1:]:
                path.append(level.labels.get(lang) or level.name)
            return [group_sep.join(path)]
        return [self.labels.get(lang) or self.name]

    def get_names(self, multiple_select="both"):
        return [self.name]

    def __repr__(self):
        args = (self.__class__.__name__, self.name, self.data_type)
        return "<%s name='%s' type='%s'>" % args

    @classmethod
    def from_json_definition(cls, definition, group=None,
                             section=None, field_choices={}):

        name = definition['name']
        labels = cls._extract_json_labels(definition)
        data_type = definition['type']

        # Get the data type. If it has a foreign key, instanciate a subclass
        # dedicated to handle choices and pass it the choices matching this fk
        if " " in data_type:
            data_type, choice_id = data_type.split(' ')
            choices = field_choices[choice_id]

            if data_type == "select_one":
                return FormChoiceField(name, labels, data_type,
                                       group, section, choices)

            if data_type == "select_many":
                args = (name, labels, data_type, group, section, choices)
                return FormChoiceFieldWithMultipleSelect(*args)

        return cls(name, labels, data_type, group, section)

    def format(self, val, translation='_default'):
        return {self.name: val}


class FormChoiceField(FormField):
    """  Same as FormField, but link the data to a FormChoice """

    def __init__(self, name, labels, data_type, path=None,
                 section=None, choice=None):
        super(FormChoiceField, self).__init__(name, labels, data_type,
                                              path, section)
        self.choice = choice or {}

    def format(self, val, translation='_default', multiple_select="both"):
        if translation:
            try:
                val = self.choice.options[val]['labels'][translation]
            except KeyError:
                pass
        return {self.name: val}


class FormChoiceFieldWithMultipleSelect(FormChoiceField):
    """  Same as FormChoiceField, but you can select several answer """

    def __init__(self, name, labels, data_type, path=None,
                 section=None, choice=None):
        super(FormChoiceField, self).__init__(name, labels, data_type,
                                              path, section)
        self.choice = choice or {}
        self.value_names = self.get_value_names()

    def _get_label(self, lang="_default", group_sep=None):
        """ Return the label for this field, with no options """
        if group_sep:
            path = []
            for level in self.hierarchy[1:]:
                path.append(level.labels.get(lang) or level.name)
            return group_sep.join(path)

        return self.labels.get(lang) or self.name

    def _get_option_label(self, lang="_default", group_sep=None, option=None):
        """ Return the label for this field and this option in particular """

        label = self._get_label(lang, group_sep)
        option_label = option['labels'].get(lang, option['name'])
        group_sep = group_sep or "/"
        return label + group_sep + option_label

    def get_labels(self, lang="_default", group_sep=None, multiple_select="both"):
        """ Return a list of labels for this field.

            Most fields have only one label, so the list contains only one item,
            but some fields can multiple values, and one label for each
            value.
        """
        labels = []
        if multiple_select in ("both", "summary"):
            labels.append(self._get_label(lang, group_sep))

        if multiple_select in ("both", "details"):
            for option in self.choice.options.values():
                labels.append(self._get_option_label(lang, group_sep, option))

        return labels

    def get_value_names(self, multiple_select="both"):
        names = []
        if multiple_select in ("both", "summary"):
            names.append(self.name)

        if multiple_select in ("both", "details"):
            for option_name in self.choice.options.keys():
                names.append(self.name + "/" + option_name)
        return names

    def __repr__(self):
        data = (self.name, self.data_type)
        return "<FormChoiceField name='%s' type='%s'>" % data

    def format(self, val, translation='_default', multiple_select="both"):

        cells = dict.fromkeys(self.value_names, "0")
        if multiple_select in ("both", "summary"):
            cells[self.name] = val

        if multiple_select in ("both", "details"):
            for choice in val.split():
                cells[self.name + "/" + choice] = "1"
        return cells


class FormGroup(FormInfo):  # useful to get __repr__
    pass


class FormSection(FormInfo):
    """ The tabular representation of a repeatable group of fields """

    def __init__(self, name="submissions", labels=None, fields=None,
                 parent=None, children=(), hierarchy=(None,)):

        if labels is None:
            labels = {'_default': 'submissions'}

        super(FormSection, self).__init__(name, labels)
        self.fields = fields or OrderedDict()
        self.parent = parent
        self.children = list(children)

        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    @classmethod
    def from_json_definition(cls, definition, hierarchy=(None,), parent=None):
        labels = cls._extract_json_labels(definition)
        return cls(definition['name'], labels, hierarchy=hierarchy,
                   parent=parent)

    def get_label(self, lang="_default"):
        return [self.labels.get(lang) or self.name]

    def __repr__(self):
        parent_name = getattr(self.parent, 'name', None)
        return "<FormSection name='%s' parent='%s'>" % (self.name, parent_name)


class FormChoice(FormInfo):

    def __init__(self, name):
        self.name = name
        self.options = {}

    @classmethod
    def from_json_definition(cls, definition):
        raise NotImplemented('Use all_from_json_definition() or __init__()')

    @classmethod
    def all_from_json_definition(cls, definition):

        all_choices = {}
        for choice_definition in definition:
            choice_name = choice_definition['list_name']
            try:
                choices = all_choices[choice_name]
            except KeyError:
                choices = all_choices[choice_name] = cls(choice_name)

            option = choices.options[choice_definition['name']] = {}
            option['labels'] = cls._extract_json_labels(choice_definition)
            option['name'] = choice_definition['name']

        return all_choices

    @property
    def translations(self):
        for option in self.options.values():
            for translation in option['labels'].keys():
                yield translation
