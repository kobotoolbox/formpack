# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict


class FormInfo(object):
    """ Any object composing a form. It's only used with a subclass. """

    def __init__(self, name, labels=None):
        self.name = name
        self.labels = labels or {}
        self.value_names = self.get_value_names()

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
        labels = OrderedDict({'_default': definition['name']})
        if "label" in definition:
            labels['_default'] = definition['label']

        for key, val in definition.items():
            if key.startswith('label::'):
                _, lang = key.split('::')
                labels[lang] = val
        return labels


class FormField(FormInfo):
    """ A form field definition knowing how to find and format data """

    def __init__(self, name, labels, data_type, hierarchy=(None,),
                 section=None, can_format=True):

        self.data_type = data_type
        self.section = section
        self.can_format = can_format
        self.hierarchy = list(hierarchy) + [self]

        super(FormField, self).__init__(name, labels)

        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    def get_labels(self, lang="_default", group_sep="/",
                   hierarchy_in_labels=False, multiple_select="both"):
        """ Return a list of labels for this field.

            Most fields have only one label, so the list contains only one item,
            but some fields can multiple values, and one label for each
            value.
        """
        args = lang, group_sep, hierarchy_in_labels, multiple_select
        return [self._get_label(*args)]

    # TODO: remove multiple_select ?
    def _get_label(self, lang="_default", group_sep='/',
                   hierarchy_in_labels=False, multiple_select="both",
                   _hierarchy_end=None):
        """Return the label for this field

        Args:
            lang (str, optional): Lang to translte the label to if possible.
            group_sep (str, optional): Group to seperate 2 levels of hierarchy
            hierarchy_in_labels (bool, optional):
                Label is the full hierarchy of the field
            multiple_select (str, optional):
                For multiple select, choose the type of display.
            _hierarchy_end (USub, optional):
                By pass to allow the reuse of this method while excluding self
                from the hierarchy.

        Returns:
            str: The label as "label", "Label" or "Parent / Parent / Label"
                 with "/" being the group separator.
        """

        if hierarchy_in_labels:
            path = []
            for level in self.hierarchy[1:_hierarchy_end]:
                path.append(level.labels.get(lang) or level.name)
            return group_sep.join(path)

        return self.labels.get(lang) or self.name

    def __repr__(self):
        args = (self.__class__.__name__, self.name, self.data_type)
        return "<%s name='%s' type='%s'>" % args

    @classmethod
    def from_json_definition(cls, definition, group=None,
                             section=None, field_choices={}):
        """Return an instance of a Field class matching this JSON field def

        Depending of the data datype extracted from the field definition,
        this method will return an instance of a different class.

        Args:
            definition (dict): Description
            group (FormGroup, optional): The group this field is into
            section (FormSection, optional): The section this field is into
            field_choices (dict, optional):
                A mapping of all the FormChoice instances available for
                this form.

        Returns:
            Union[FormChoiceField, FormChoiceField,
                  FormChoiceFieldWithMultipleSelect, FormField]:
                  The FormField instance matching this definiton.
        """
        name = definition['name']
        labels = cls._extract_json_labels(definition)
        data_type = definition['type']
        choices = None

        # Get the data type. If it has a foreign key, instanciate a subclass
        # dedicated to handle choices and pass it the choices matching this fk
        if " " in data_type:
            data_type, choice_id = data_type.split(' ')[:2]  # ignore optional or_other
            choices = field_choices[choice_id]

        data_type_classes = {
            "select_one": FormChoiceField,
            "select_multiple": FormChoiceFieldWithMultipleSelect,
            "geopoint": FormGPSField,
        }

        try:
            args = (name, labels, data_type, group, section, choices)
            return data_type_classes[data_type](*args)
        except KeyError:
            return cls(name, labels, data_type, group, section)

    def format(self, val, translation='_default', context=None):
        return {self.name: val}


class CopyField(FormField):
    """ Just copy the data over. No translation. No manipulation """
    def __init__(self, name, hierarchy=(None,), section=None):
        super(CopyField, self).__init__(name, labels=None,
                                        data_type=name,
                                        hierarchy=(None,),
                                        section=section,
                                        can_format=True)

    def get_labels(self, *args, **kwargs):
        """ Labels are the just the value name. Groups are ignored """
        return [self.name]


class FormGPSField(FormField):

    def __init__(self, name, labels, data_type, path=None,
                 section=None, choice=None):
        super(FormGPSField, self).__init__(name, labels, data_type,
                                           path, section)

    def get_labels(self, lang="_default", group_sep='/',
                   hierarchy_in_labels=False, multiple_select="both"):
        """Return a list of labels for this field.

        Most fields have only one label, so the list contains only one item,
        but some fields can multiple values, and one label for each
        value.

        """
        label = self._get_label(lang, group_sep, hierarchy_in_labels)
        labels = [self._get_label(lang, group_sep, hierarchy_in_labels)]

        components = {'suffix': label}
        pattern = '_{suffix}_{data_type}'

        prefix = self._get_label(lang, group_sep, hierarchy_in_labels,
                                 _hierarchy_end=-1)

        if hierarchy_in_labels and prefix:
            components['group_sep'] = group_sep
            components['prefix'] = prefix
            pattern = '{prefix}{group_sep}' + pattern

        for data_type in ('latitude', 'longitude', 'altitude', 'precision'):
            label = pattern.format(data_type=data_type, **components)
            labels.append(label)

        return labels

    def get_value_names(self, multiple_select="both"):
        """ Return the list of field identifiers used by this field"""
        names = []
        names.append(self.name)

        for data_type in ('latitude', 'longitude', 'altitude', 'precision'):
            names.append('_%s_%s' % (self.name, data_type))

        return names

    def format(self, val, translation='_default', group_sep='/',
              hierarchy_in_labels=False, multiple_select="both"):
        """Same than other format(), but dealing with 2 to 4 values

        The GPS value can contain 2, 3 or 4 numerical separated by a
        spaces: latitude, longitude altitude (optional) precision (optional)

        If a value is not present, we set it to an empty string since
        the column will be in the final export anyway.


        Args:
          val (str): The value from the submission.
          translation (str, optional): Not used. Part of the parent API.
          group_sep (str, optional): Not used. Part of the parent API.
          hierarchy_in_labels (bool, optional): Not used. Part of the parent API.
          multiple_select (str, optional): Not used. Part of the parent API.

        Returns:
          dict: The 4 values as {'_name_': raw initial value,
                                 '_name_latitude': latitude,
                                 etc.}

        """

        values = [val, "", "", "", ""]
        for i, value in enumerate(val.split(), 1):
            values[i] = value

        return dict(zip(self.value_names, values))


class FormChoiceField(FormField):
    """  Same as FormField, but link the data to a FormChoice """

    def __init__(self, name, labels, data_type, path=None,
                 section=None, choice=None):
        self.choice = choice or {}
        super(FormChoiceField, self).__init__(name, labels, data_type,
                                              path, section)

    def format(self, val, translation='_default', multiple_select="both"):
        if translation:
            try:
                val = self.choice.options[val]['labels'][translation]
            except KeyError:
                pass
        return {self.name: val}


class FormChoiceFieldWithMultipleSelect(FormChoiceField):
    """  Same as FormChoiceField, but you can select several answer """

    def _get_option_label(self, lang="_default", group_sep='/',
                          hierarchy_in_labels=False, option=None):
        """ Return the label for this field and this option in particular """

        label = self._get_label(lang, group_sep, hierarchy_in_labels)
        option_label = option['labels'].get(lang, option['name'])
        group_sep = group_sep or "/"
        return label + group_sep + option_label

    def get_labels(self, lang="_default", group_sep='/',
                   hierarchy_in_labels=False, multiple_select="both"):
        """ Return a list of labels for this field.

            Most fields have only one label, so the list contains only one item,
            but some fields can multiple values, and one label for each
            value.
        """
        labels = []
        if multiple_select in ("both", "summary"):
            labels.append(self._get_label(lang, group_sep, hierarchy_in_labels))

        if multiple_select in ("both", "details"):
            for option in self.choice.options.values():
                args = (lang, group_sep, hierarchy_in_labels, option)
                labels.append(self._get_option_label(*args))

        return labels

    def get_value_names(self, multiple_select="both"):
        """ Return the list of field identifiers used by this field"""
        names = []
        if multiple_select in ("both", "summary"):
            names.append(self.name)

        if multiple_select in ("both", "details"):
            for option_name in self.choice.options.keys():
                names.append(self.name + '/' + option_name)
        return names

    def __repr__(self):
        data = (self.name, self.data_type)
        return "<FormChoiceField name='%s' type='%s'>" % data

    # maybe try to cache those
    def format(self, val, translation='_default',
               group_sep="/", hierarchy_in_labels=False,
               multiple_select="both"):
        """ Same than other format(), with an option for multiple_select layout

                multiple_select:
                "both": add the summary column and a colum for each value
                "summary": only the summary column
                "details": only the details column
        """
        cells = dict.fromkeys(self.value_names, "0")
        if multiple_select in ("both", "summary"):
            res = []
            for v in val.split():
                try:
                    res.append(self.choice.options[v]['labels'][translation])
                except:
                    res.append(v)
            cells[self.name] = " ".join(res)

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
        super(FormChoice, self).__init__(name)
        self.name = name
        self.options = {}

    @classmethod
    def from_json_definition(cls, definition):
        raise NotImplemented('Use all_from_json_definition() or __init__()')

    @classmethod
    def all_from_json_definition(cls, definition):

        all_choices = {}
        for choice_definition in definition:
            # raise an exception if the incorrect alias is used
            if 'list name' in choice_definition:
                raise ValueError('use list_name instead of "list name"')

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
