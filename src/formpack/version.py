# coding: utf-8

from __future__ import (unicode_literals, print_function, absolute_import,
                        division)


try:
    from cyordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

from .utils import formversion_pyxform

from .submission import FormSubmission
from .utils import parse_xml_to_xmljson, normalize_data_type
from .schema import (FormField, FormGroup, FormSection, FormChoice)


class FormVersion(object):

    # QUESTION FOR ALEX: get rid off _root_node_name ? What is it for ?
    def __init__(self, form_pack, schema):

        # QUESTION FOR ALEX: why this check ?
        if 'name' in schema:
            raise ValueError('FormVersion should not have a name parameter. '
                             'consider using "title" or "id_string"')
        self.schema = schema
        self.form_pack = form_pack

        # slug of title
        self._root_node_name = form_pack.title

        # form version id, unique to this version of the form
        self.id = schema.get('version')

        # form string id, unique to this form, shared accross versions
        self.id_string = schema.get('id_string')

        # TODO: set the title of the last version as the name of the first
        # section ?
        # Human readable title for this version
        self.title = schema.get('title', form_pack.title)

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

        content = self.schema.get('content', {})

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
        section = FormSection(name=form_pack.title)
        self.sections[form_pack.title] = section

        # Those will keep track of were we are while traversing the
        # schema.
        # Hierarchy contains all the levels, mixing groups and sections,
        # including the first and last ones while stacks are just an history of
        # previous levels, and for either groups or sections.
        hierarchy = [section]
        group_stack = []
        section_stack = []

        for data_definition in survey:

            data_type = data_definition.get('type')
            if not data_type: # handle broken data type definition
                continue

            data_type = normalize_data_type(data_type)
            name = data_definition.get('name')

            # parse closing groups and repeat
            if data_type is None:
                continue

            if data_type.startswith('end_group'):
                # We go up in one level of nesting, so we set the current group
                # to be what used to be the parent group. We also remote one
                # level in the hierarchy.
                hierarchy.pop()
                group = group_stack.pop()
                continue

            if data_type.startswith('end_repeat'):
                # We go up in one level of nesting, so we set the current section
                # to be what used to be the parent section
                hierarchy.pop()
                section = section_stack.pop()
                continue

            # parse defintinitions of stuff having a name such as fields
            # or opening groups and repeats
            if name is None:
                continue

            if data_type.startswith('begin_group'):
                group_stack.append(group)
                group = FormGroup.from_json_definition(data_definition)
                # We go down in one level on nesting, so save the parent group.
                # Parent maybe None, in that case we are at the top level.
                hierarchy.append(group)

                # Get the labels and associated translations for this group
                self.translations.update(OrderedDict.fromkeys(group.labels))
                continue

            if data_type.startswith('begin_repeat'):
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

            # If we are here, it's a regular field
            # Get the the data name and type
            field = FormField.from_json_definition(data_definition,
                                                   hierarchy, section,
                                                   field_choices)
            section.fields[field.name] = field

            self.translations.update(OrderedDict.fromkeys(field.labels))

        # Convert it back to a list to get numerical indexing
        self.translations = list(self.translations)

    def __repr__(self):
        return '<FormVersion %s>' % self._stats()

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self._get_id_string()
        _stats['version'] = self.form_pack.id_string or ''
        _stats['row_count'] = len(self.schema.get('content', {}).get('survey', []))
        # returns stats in the format [ key="value" ]
        return '\n\t'.join(map(lambda key: '%s="%s"' % (key, str(_stats[key])),
                               _stats.keys()))

    def to_dict(self):
        return self.schema

    # TODO: find where to move that
    def _load_submission_xml(self, xml):
        raise NotImplementedError("This doesn't work now that submissions "
                                  "are out of the class. Port it to Export.")
        _xmljson = parse_xml_to_xmljson(xml)
        _rootatts = _xmljson.get('attributes', {})
        _id_string = _rootatts.get('id_string')
        _version_id = _rootatts.get('version')
        if _id_string != self._get_id_string():
            raise ValueError('submission id_string does not match: %s != %s' %
                             (self._get_id_string(), _id_string))
        if _version_id != self.form_pack.id_string:
            raise ValueError('mismatching version id %s != %s' %
                             (self.form_pack.id_string, _version_id))
        self.submissions.append(FormSubmission.from_xml(_xmljson, self))

    def lookup(self, prop, default=None):
        result = getattr(self, prop, None)
        if result is None:
            result = self.form_pack.lookup(prop, default=default)
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
            return self.form_pack.title
        return self.version_title

    def get_labels(self, lang="_default", group_sep=None):
        """ Returns a mapping of labels for {section: [field_label, ...]...}

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
                    section_labels.extend(field.get_labels(lang, group_sep))

        return all_labels

    def to_xml(self):
        survey = formversion_pyxform(self.schema)

        title = self._get_title()

        if title is None:
            raise ValueError('cannot create xml on a survey ' 'with no title.')
        survey.update({
            'name': self.lookup('root_node_name', 'data'),
            'id_string': self.lookup('id_string'),
            'title': title,
            'version': self.form_pack.id_string,
        })
        return survey.to_xml().encode('utf-8')
