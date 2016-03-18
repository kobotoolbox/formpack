# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

from collections import OrderedDict

from .utils import formversion_pyxform

from ...models.formpack.submission import FormSubmission
from ...models.formpack.utils import parse_xml_to_xmljson

# TODO: move submission, pack.py and version.py into a forms module with
#       __init__ their content


class FormVersion:
    def __init__(self, version_data, parent):

        # QUESTION FOR ALEX: why this check ?
        if 'name' in version_data:
            raise ValueError('FormVersion should not have a name parameter. '
                             'consider using "title" or "id_string"')
        # TODO: # rename _v to something meaningful
        self._v = version_data
        # QUESTION FOR ALEX: what is parent ?
        self._parent = parent
        self._root_node_name = version_data.get('root_node_name')
        self.version_title = version_data.get('title')
        self.submissions = []
        self.id_string = version_data.get('id_string')
        self.version_id = version_data.get('version')

        # List of available language for translation. One translation does
        # not mean all labels are translated, but at least one.
        # One special translation not listed here is "_default", which
        # use either the only label available, or the field name.
        # This will be converted down the line to a list. We use an OrderedDict
        # to maintain order and remove duplicates, but will need indexing later
        self.translations = OrderedDict()

        # Sections separates fields from various level of nesting in case
        # we have repeat group. If you don't have repeat group, you have
        # only one section, if you have repeat groups, you will have one
        # section per repeat group. Sections eventually become sheets in
        # xls export.
        self.sections = OrderedDict()

        content = self._v.get('content', {})

        # TODO: put those parts in a separate method and unit test it
        survey = content.get('survey', [])

        # Analyze the survey schema and extract the informations we need
        # to build the export: the sections, the choices, the fields
        # and translations for each of them.

        # Extract choices data.
        # Choices are the list of values you can choose from to answer a
        # specific question. They can have translatable labels.
        choices_definition = content.get('choices', ())
        field_choices = FormChoice.all_from_json_definition(choices_definition)
        for choice in field_choices.values():
            self.translations.update(OrderedDict.fromkeys(choice.translations))

        # Extract fields data
        group = None
        section = FormSection()
        self.sections["submissions"] = section

        # Those will keep track of were we are while traversing the
        # schema.
        # Hierarchy contains all the levels, mixing groups and sections,
        # including the first and last ones while stacks are just an history of
        # previous levels, and for either groups or sections.
        hierarchy = [section]
        group_stack = []
        section_stack = []

        for data_definition in survey:

            if data_definition['type'] == 'begin group':
                group_stack.append(group)
                group = FormGroup.from_json_definition(data_definition)
                # We go down in one level on nesting, so save the parent group.
                # Parent maybe None, in that case we are at the top level.
                hierarchy.append(group)

                # Get the labels and associated translations for this group
                self.translations.update(OrderedDict.fromkeys(group.labels))
                continue

            if data_definition['type'] == 'end group':
                # We go up in one level of nesting, so we set the current group
                # to be what used to be the parent group. We also remote one
                # level in the hierarchy.
                hierarchy.pop()
                group = group_stack.pop()
                continue

            if data_definition['type'] == 'begin repeat':
                # We go down in one level on nesting, so save the parent section.
                # Parent maybe None, in that case we are at the top level.
                parent_section = section

                section = FormSection.from_json_definition(data_definition,
                                                           hierarchy,
                                                           parent=parent_section)
                self.sections[section.name] = section
                hierarchy.append(section)
                section_stack.append(parent_section)
                parent_section.children.append(section)

                translations = OrderedDict.fromkeys(section.labels)
                self.translations.update(translations)
                continue

            if data_definition['type'] == 'end repeat':
                # We go up in one level of nesting, so we set the current section
                # to be what used to be the parent section
                hierarchy.pop()
                section = section_stack.pop()
                continue

            # Get the the data name and type
            if 'name' in data_definition:
                field = FormField.from_json_definition(data_definition,
                                                       hierarchy, section,
                                                       field_choices)
                section.fields[field.name] = field

                self.translations.update(OrderedDict.fromkeys(field.labels))

        # Convert it back to a list to get numerical indexing
        self.translations.pop('_default')
        self.translations = list(self.translations)

        # Set meta fields (such as indexes)
        for section_name, section in self.sections.items():

            # Add meta fields
            if section.children:
                section.fields['_index'] = FormField('_index', {}, 'meta',
                                                     can_format=False)

            if section.parent:
                field = FormField('_parent_table_name', {},
                                  'meta', can_format=False)
                section.fields['_parent_table_name'] = field

                section.fields['_parent_index'] = FormField('_parent_index',
                                                            {}, 'meta',
                                                            can_format=False)

        for submission in version_data.get('submissions', []):
            self.load_submission(submission)

    def __repr__(self):
        return '<FormVersion %s>' % self._stats()

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self._get_id_string()
        _stats['version'] = '' if not self.version_id else self.version_id
        _stats['row_count'] = len(self._v.get('content', {}).get('survey', []))
        _stats['submission_count'] = len(self.submissions)
        # returns stats in the format [ key="value" ]
        return '\n\t'.join(map(lambda key: '%s="%s"' % (key, str(_stats[key])),
                               _stats.keys()))

    def to_dict(self):
        _ss = []
        for _s in self.submissions:
            _ss.append(_s.to_dict())
        out = {}
        out.update(self._v)
        out[u'submissions'] = _ss
        return out

    def load_submission(self, v):
        self.submissions.append(FormSubmission(v, self))

    def _load_submission_xml(self, xml):
        _xmljson = parse_xml_to_xmljson(xml)
        _rootatts = _xmljson.get('attributes', {})
        _id_string = _rootatts.get('id_string')
        _version_id = _rootatts.get('version')
        if _id_string != self._get_id_string():
            raise ValueError('submission id_string does not match: %s != %s' %
                             (self._get_id_string(), _id_string))
        if _version_id != self.version_id:
            raise ValueError('mismatching version id %s != %s' %
                             (self.version_id, _version_id))
        self.submissions.append(FormSubmission.from_xml(_xmljson, self))

    def submissions_count(self):
        return len(self.submissions)

    def lookup(self, prop, default=None):
        result = getattr(self, prop, None)
        if result is None:
            result = self._parent.lookup(prop, default=default)
        return result

    def _get_root_node_name(self):
        return self.lookup('root_node_name', default='data')

    def _get_id_string(self):
        return self.lookup('id_string')

    def _get_title(self):
        '''
        if formversion has no name, uses form's name
        '''
        if self.version_title is None:
            return self._parent.title
        return self.version_title

    def submit(self, *args, **kwargs):
        self.load_submission(kwargs)

    def get_labels(self, lang="_default", group_sep=None):
        """ Returns a mapping of labels for {section: [field, field]...}

            Sections and fields labels can be set to use their slug name,
            their lone label, or one of the translated labels.

            If a field is part of a group and a group separator is passed,
            the group label is retrieved, possibly translated, and
            prepended to the field label itself.
        """

        all_labels = OrderedDict()
        for section_name, section in self.sections.items():

            section_label = section.labels.get(lang) or section_name
            section_labels = all_labels[section_label] = []

            for field_name, field in section.fields.items():
                    section_labels.append(field.get_label(lang, group_sep))

        return all_labels

    def to_xml(self):
        survey = formversion_pyxform(self._v)

        title = self._get_title()

        if title is None:
            raise ValueError('cannot create xml on a survey ' 'with no title.')
        survey.update({
            'name': self.lookup('root_node_name', 'data'),
            'id_string': self.lookup('id_string'),
            'title': title,
            'version': self.version_id,
        })
        return survey.to_xml().encode('utf-8')


class FormInfo(object):

    def __init__(self, name, labels):
        self.name = name
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

    def __init__(self, name, labels, data_type, hierarchy=(None,),
                 section=None, can_format=True):
        super(FormField, self).__init__(name, labels)
        self.data_type = data_type
        self.section = section
        self.can_format = can_format
        self.hierarchy = list(hierarchy) + [self]
        # do not include the root section in the path
        self.path = '/'.join(info.name for info in self.hierarchy[1:])

    def get_label(self, lang="_default", group_sep=None):
        if group_sep:
            path = []
            for level in self.hierarchy[1:]:
                path.append(level.labels.get(lang) or level.name)
            return group_sep.join(path)
        return self.labels.get(lang) or self.name

    def __repr__(self):
        return "<FormField name='%s' type='%s'>" % (self.name, self.data_type)

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

            return FormChoiceField(name, labels, data_type,
                                   group, section, choices)

        return cls(name, labels, data_type, group, section)

    def format(self, val, translation='_default'):
        return val


class FormChoiceField(FormField):

    def __init__(self, name, labels, data_type, path=None,
                 section=None, choice=None):
        super(FormChoiceField, self).__init__(name, labels, data_type,
                                              path, section)
        self.choice = choice or {}

    def __repr__(self):
        data = (self.name, self.data_type)
        return "<FormChoiceField name='%s' type='%s'>" % data

    def format(self, val, translation='_default'):
        if translation:
            # TODO: we may want to @memoize this method
            try:
                return self.choice.options[val]['labels'][translation]
            except KeyError:
                return val
        return val


class FormGroup(FormInfo):  # useful to get __repr__
    pass


class FormSection(FormInfo):

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

        return all_choices

    @property
    def translations(self):
        for option in self.options.values():
            for translation in option['labels'].keys():
                yield translation
