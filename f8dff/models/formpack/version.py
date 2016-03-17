# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)

from collections import OrderedDict, defaultdict

from .utils import formversion_pyxform

from ...models.formpack.submission import FormSubmission
from ...models.formpack.utils import parse_xml_to_xmljson

# TODO: move submission, pack.py and version.py into a forms module with
#       __init__ their content
# TODO: put formatters in their own module


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
        field_choices = defaultdict(OrderedDict)
        for choice_definition in content.get('choices', ()):
            choices = field_choices[choice_definition['list_name']]
            name = choice_definition['name']
            choice = choices[name] = {}

            # Get the labels and associated translations for this data
            choice['labels'] = self._extract_labels(choice_definition)
            self.translations.update(OrderedDict.fromkeys(choice['labels']))

        # Extract fields data
        group = None
        previous_groups = []

        fields = OrderedDict()
        section = {
            'parent': None,
            'children': [],
            "fields": fields,
            'name': 'submissions',
            'labels': {'_default': 'submissions'}
        }
        self.sections["submissions"] = section
        previous_sections = []

        for data_definition in survey:

            if data_definition['type'] == 'begin group':
                name = data_definition['name']
                # We go down in one level on nesting, so save the parent group.
                # Parent maybe None, in that case we are at the top level.
                previous_groups.append(group)
                group = {'name': name}

                # Get the labels and associated translations for this group
                group['labels'] = self._extract_labels(data_definition)
                self.translations.update(OrderedDict.fromkeys(group['labels']))
                continue

            if data_definition['type'] == 'end group':
                # We go up in one level of nesting, so we set the current group
                # to be what used to be the parent group
                group = previous_groups.pop()
                continue

            if data_definition['type'] == 'begin repeat':
                # We go down in one level on nesting, so save the parent section.
                # Parent maybe None, in that case we are at the top level.
                parent_section = section
                fields = OrderedDict()
                section = {
                    "parent": parent_section,
                    "children": [],
                    "fields": fields,
                    "name": name
                }

                self.sections[name] = section
                previous_sections.append(parent_section)
                parent_section['children'].append(section)

                section['labels'] = self._extract_labels(data_definition)
                translations = OrderedDict.fromkeys(section['labels'])
                self.translations.update(translations)
                continue

            if data_definition['type'] == 'end repeat':
                # We go up in one level of nesting, so we set the current section
                # to be what used to be the parent section
                section = previous_sections.pop()
                fields = section['fields']
                continue

            # QUESTION FOR ALEX: is there a case where 'name' is not in there ?
            # if yes, what do we do with it ?
            # Get the the data name and type
            if 'name' in data_definition:
                name = data_definition['name']
                field = fields[name] = {'choices': None}
                field['group'] = group
                field['section'] = section

                # Get the data type. If it has a foreign key, map the
                # label translations
                field_type = data_definition['type']
                if " " in field_type:
                    field_type, choice_id = field_type.split(' ')
                    field['choices'] = field_choices[choice_id]
                field['type'] = field_type

                # Get the labels and associated translations for this choice
                field['labels'] = self._extract_labels(data_definition)
                self.translations.update(OrderedDict.fromkeys(field['labels']))

        # Convert it back to a list to get numerical indexing
        self.translations.pop('_default')
        self.translations = list(self.translations)

        self.formatters = OrderedDict()

        # Set formatters and meta fields (such as indexes)
        for section_name, section in self.sections.items():

            # Add formatters for each field
            formatters = self.formatters.setdefault(section_name, OrderedDict())
            fields = section['fields']
            for field_name, field in fields.items():
                formatters[field_name] = Formatter(
                    name, field['type'], field.get('choices'), field['group'])

            # Add meta fields
            if section['children']:
                fields['_index'] = {'name': '_index'}

            if section['parent']:
                fields['_parent_table_name'] = {'name': '_parent_table_name'}
                fields['_parent_index'] = {'name': '_parent_index'}

        for submission in version_data.get('submissions', []):
            self.load_submission(submission)

    def _extract_labels(self, data_definition):
        """ Extract translation labels from the JSON data definition """
        labels = OrderedDict({'_default': data_definition['name']})
        if "label" in data_definition:
            labels['_default'] = data_definition['label']
        else:
            for key, val in data_definition.items():
                if key.startswith('label::'):
                    _, lang = key.split('::')
                    labels[lang] = val
        return labels

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

            section_label = section['labels'].get(lang) or section_name
            section_labels = all_labels[section_label] = []

            for field_name, field in section['fields'].items():

                    field_label = field['labels'].get(lang) or field_name
                    group = field.get('group')
                    if group_sep and group:
                        group = group['labels'].get(lang) or group['name']
                        section_labels.append(group + group_sep + field_label)
                    else:
                        section_labels.append(field_label)

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


class Formatter:
    def __init__(self, name, data_type, choices=None, group=None):
        self.data_type = data_type
        self.name = name
        self.choices = choices
        self.group = group

    def format(self, val, translation='_default'):
        if self.choices and translation:
            # TODO: we may want to @memoize this method
            try:
                return self.choices[val]['labels'][translation]
            except KeyError:
                return val
        return val

    def __repr__(self):
        return "<Formatter type='%s' name='%s'>" % (self.data_type, self.name)
