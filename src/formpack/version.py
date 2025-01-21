# coding: utf-8
from collections import OrderedDict, defaultdict
from typing import (
    Dict,
    List,
    Union,
)

from pyxform import aliases as pyxform_aliases

from .constants import UNTRANSLATED
from .errors import SchemaError
from .errors import TranslationError
from .schema import FormField, FormGroup, FormSection, FormChoice
from .submission import FormSubmission
from .utils import parse_xml_to_xmljson, normalize_data_type
from .utils.xlsform_parameters import parameters_string_to_dict, parameters_dict_to_string

from .utils.flatten_content import flatten_content
from .utils.xform_tools import formversion_pyxform
from .validators import validate_content


YES_NO = pyxform_aliases.yes_no


class LabelStruct:
    """
    LabelStruct stores labels + translations assigned to `field.labels`
    """

    def __init__(self, labels=[], translations=[]):
        if len(labels) != len(translations):
            errmsg = (
                'Mismatched labels and translations: [{}] [{}] '
                '{}!={}'.format(
                    ', '.join(labels),
                    ', '.join(map(str, translations)),
                    len(labels),
                    len(translations),
                )
            )
            raise TranslationError(errmsg)
        self._labels = labels
        self._translations = translations
        self._vals = dict(zip(translations, labels))

    def get(self, key, default=None):
        return self._vals.get(key, default)


class BaseForm:
    @staticmethod
    def _get_field_labels(
        field: FormField,
        translations: List[str],
    ) -> LabelStruct:
        if 'label' in field:
            if not isinstance(field['label'], list):
                field['label'] = [field['label']]
            return LabelStruct(labels=field['label'], translations=translations)
        return LabelStruct()

    @staticmethod
    def _get_fields_by_name(
        survey: Dict[str, Union[str, List]]
    ) -> Dict[str, Dict[str, Union[str, List]]]:
        return {row['name']: row for row in survey if 'name' in row}

    @staticmethod
    def _get_translations(content: Dict[str, List]) -> List[str]:
        return [
            t if t is not None else UNTRANSLATED
            for t in content.get('translations', [None])
        ]


class AnalysisForm(BaseForm):
    def __init__(
        self,
        formpack: 'FormPack',
        schema: Dict[str, Union[str, List]],
    ) -> None:

        self.schema = schema
        self.formpack = formpack

        survey = self.schema.get('additional_fields', [])
        fields_by_name = self._get_fields_by_name(survey)
        section = FormSection(name=formpack.title)

        self.translations = self._get_translations(schema)

        for data_def in survey:
            field = FormField.from_json_definition(
                definition=data_def,
                section=section,
                translations=self.translations,
            )

            # qualitative analysis labels and choices are fundamentally
            # different from XLSForm, but this is kind of a hack. when (if)
            # qualitative analysis gets full support for translated labels,
            # this will have to change
            try:
                # should become a dictionary (like choice labels) with language
                # codes as keys and labels as values once translations are
                # supported
                field.labels = [data_def['label']]
            except KeyError:
                field.labels = []
            field.choices = data_def.get('choices', [])

            section.fields[field.name] = field

        self.fields = list(section.fields.values())
        self.fields_by_source = self._get_fields_by_source()

    def __repr__(self) -> str:
        return f"<AnalysisForm parent='{self.formpack.title}'>"

    def _get_fields_by_source(self) -> Dict[str, List[FormField]]:
        fields_by_source = defaultdict(list)
        for field in self.fields:
            fields_by_source[field.source].append(field)
        return fields_by_source

    def _map_sections_to_analysis_fields(
        self, survey_field: FormField
    ) -> List[FormField]:
        _fields = []
        for analysis_field in self.fields_by_source[survey_field.qpath]:
            analysis_field.section = survey_field.section
            analysis_field.source_field = survey_field
            _fields.append(analysis_field)
        return _fields

    def insert_analysis_fields(
        self, fields: List[FormField]
    ) -> List[FormField]:
        _fields = []
        for field in fields:
            _fields.append(field)
            if field.qpath in self.fields_by_source:
                _fields += self._map_sections_to_analysis_fields(field)
        return _fields


class FormVersion(BaseForm):
    @classmethod
    def verify_schema_structure(cls, struct):
        if 'content' not in struct:
            raise SchemaError('version content must have "content"')
        if 'survey' not in struct['content']:
            raise SchemaError('version content must have "survey"')
        validate_content(struct['content'])

    # QUESTION FOR ALEX: get rid off _root_node_name ? What is it for ?
    def __init__(self, form_pack, schema):

        # QUESTION FOR ALEX: why this check ?
        if 'name' in schema:
            raise ValueError(
                'FormVersion should not have a name parameter. '
                'consider using "title" or "id_string"'
            )
        self.schema = schema
        self.form_pack = form_pack

        # slug of title
        self.root_node_name = self._get_root_node_name()

        # form version id, unique to this version of the form
        self.id = schema.get('version')
        self.version_id_key = schema.get(
            'version_id_key', form_pack.default_version_id_key
        )

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

        content = self.schema['content']

        self.translations = self._get_translations(content)

        # TODO: put those parts in a separate method and unit test it
        survey = content.get('survey', [])

        survey = self._append_pseudo_questions(survey)

        fields_by_name = self._get_fields_by_name(survey)

        # Analyze the survey schema and extract the informations we need
        # to build the export: the sections, the choices, the fields
        # and translations for each of them.

        # Extract choices data.
        # Choices are the list of values you can choose from to answer a
        # specific question. They can have translatable labels.
        choices_definition = content.get('choices', ())
        field_choices = FormChoice.all_from_json_definition(
            choices_definition, self.translations
        )

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
            if 'disabled' in data_definition:
                if YES_NO.get(str(data_definition['disabled']), False):
                    continue

            data_type = data_definition.get('type')
            if not data_type:  # handle broken data type definition
                continue

            data_type = normalize_data_type(data_type)
            name = data_definition.get('name')

            # parse closing groups and repeat
            if data_type is None:
                continue

            if data_type == 'end_group':
                # We go up in one level of nesting, so we set the current group
                # to be what used to be the parent group. We also remote one
                # level in the hierarchy.
                hierarchy.pop()
                group = group_stack.pop()
                continue

            if data_type == 'end_repeat':
                # We go up in one level of nesting, so we set the current section
                # to be what used to be the parent section
                hierarchy.pop()
                section = section_stack.pop()
                continue

            # parse defintinitions of stuff having a name such as fields
            # or opening groups and repeats
            if name is None:
                continue

            if data_type == 'begin_group':
                group_stack.append(group)
                group = FormGroup.from_json_definition(
                    data_definition,
                    translations=self.translations,
                )
                # We go down in one level on nesting, so save the parent group.
                # Parent maybe None, in that case we are at the top level.
                hierarchy.append(group)
                continue

            if data_type == 'begin_repeat':
                # We go down in one level on nesting, so save the parent section.
                # Parent maybe None, in that case we are at the top level.
                parent_section = section

                section = FormSection.from_json_definition(
                    data_definition,
                    hierarchy,
                    parent=parent_section,
                    translations=self.translations,
                )
                self.sections[section.name] = section
                hierarchy.append(section)
                section_stack.append(parent_section)
                parent_section.children.append(section)
                continue

            # If we are here, it's a regular field
            # Get the the data name and type
            field = FormField.from_json_definition(
                data_definition,
                hierarchy,
                section,
                field_choices,
                translations=self.translations,
            )
            section.fields[field.name] = field

            _f = fields_by_name[field.name]
            field.labels = self._get_field_labels(_f, self.translations)
            assert 'labels' not in _f

    # FIXME: Find a safe way to use this. Wrapping with try/except isn't enough
    # to fix https://github.com/kobotoolbox/formpack/issues/150
    #
    # def __repr__(self):
    #    return '<FormVersion %s>' % self._stats()

    def _append_pseudo_questions(self, survey):
        _survey = []
        for item in survey:
            _survey.append(item)
            if item.get('_or_other', False):
                _survey.append(
                    {
                        'type': 'text',
                        'name': f'{item["name"]}_other',
                        'label': [None] * len(self.translations),
                    }
                )
        return _survey

    def _stats(self):
        _stats = OrderedDict()
        _stats['id_string'] = self._get_id_string()
        _stats['version'] = self.id
        _stats['row_count'] = len(
            self.schema.get('content', {}).get('survey', [])
        )
        # returns stats in the format [ key="value" ]
        return '\n\t'.join(
            ['%s="%s"' % (key, str(_stats[key])) for key in _stats.keys()]
        )

    def to_dict(self, **opts):
        content = flatten_content(self.schema['content'], **opts)
        im_max_pixs = self.form_pack.default_image_max_pixels
        if im_max_pixs is not None:
            for row in content.get('survey'):
                if row.get('type') == 'image':
                    rparams = parameters_string_to_dict(row.get('parameters', ''))
                    if rparams.get('max-pixels') == '-1':
                        del rparams['max-pixels']
                    elif 'max-pixels' not in rparams:
                        rparams['max-pixels'] = str(im_max_pixs)
                    row['parameters'] = parameters_dict_to_string(rparams)
        return content

    # TODO: find where to move that
    def _load_submission_xml(self, xml):
        raise NotImplementedError(
            "This doesn't work now that submissions "
            "are out of the class. Port it to Export."
        )
        _xmljson = parse_xml_to_xmljson(xml)
        _rootatts = _xmljson.get('attributes', {})
        _id_string = _rootatts.get('id_string')
        _version_id = _rootatts.get('version')
        if _id_string != self._get_id_string():
            raise ValueError(
                'submission id_string does not match: %s != %s'
                % (self._get_id_string(), _id_string)
            )
        if _version_id != self.form_pack.id_string:
            raise ValueError(
                'mismatching version id %s != %s'
                % (self.form_pack.id_string, _version_id)
            )
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
        """
        If formversion has no name, uses form's name
        """
        if self.title is None:
            return self.form_pack.title
        return self.title

    def get_labels(self, lang=UNTRANSLATED, group_sep=None):
        """
        Returns a mapping of labels for {section: [field_label, ...]...}

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

    def to_xml(self, warnings=None):
        # todo: collect warnings from pyxform compilation when a list is passed
        survey = formversion_pyxform(
            self.to_dict(
                remove_sheets=['translations', 'translated'],
            )
        )
        title = self._get_title()

        if title is None:
            raise ValueError('cannot create xml on a survey with no title.')

        # pyxform 3.0.0 has removed the ability to call `survey.update()`
        # https://github.com/XLSForm/pyxform/commit/6918b400d3cf6c9151db2104137afe2c52dd68e4
        for k, v in {
            'name': self.lookup('root_node_name', 'data'),
            'id_string': self.lookup('id_string'),
            'title': self.lookup('title'),
            'version': self.lookup('id'),
        }.items():
            survey[k] = v

        return survey._to_pretty_xml()  # .encode('utf-8')
