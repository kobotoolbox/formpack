# coding: utf-8
from __future__ import (unicode_literals, print_function, absolute_import,
                        division)
from .constants import UNTRANSLATED
from .errors import SchemaError
from .errors import TranslationError
from .schema import (
                     FormField,
                     FormGroup,
                     FormRootSection,
                     FormRepeatSection,
                     FormChoice,
                    )
from .schema.fields import form_field_from_json_definition
from .schema.datadef import form_choice_list_from_json_definition

from .submission import FormSubmission
from .utils import parse_xml_to_xmljson, normalize_data_type
from .utils.flatten_content import flatten_content
from .utils.future import OrderedDict
from .utils.xform_tools import formversion_pyxform
from .validators import validate_content

from copy import deepcopy

class LabelStruct:
    def __init__(self, label, txs):
        self._label = label
        _labels = []
        self._txs = txs
        self._txnames = [tx['name'] for tx in txs]
        for tx in txs:
            _labels.append(self._label.get(tx['$anchor']))
        self._labels = _labels

    def get(self, key, _default):
        if key is None:
            key = ''
        if key is False:
            return _default
        else:
            _i = self._txnames.index(key)
            return self._labels[_i]


class NoLabelStruct:
    def __init__(self, *_args):
        self._args = _args
        self._labels = []

    def get(self, key, _default):
        return _default

class FormVersion(object):
    def __init__(self, form_pack, schema, content):
        if 'name' in schema:
            raise ValueError('FormVersion should not have a name parameter. '
                             'consider using "title" or "id_string"')

        self.schema = schema
        self.title = schema.get('title', form_pack.title)
        self.form_pack = form_pack
        self.content = content
        self.full_txs = content.get('translations')
        settings = content.get('settings')

        # slug of title
        self.root_node_name = self._get_root_node_name()

        # form version id, unique to this version of the form
        self.id = schema.get('version')
        self.version_id_key = schema.get('version_id_key',
                                         form_pack.default_version_id_key)

        # form string id, unique to this form, shared accross versions
        self.id_string = schema.get('id_string')
        if self.id_string:
            settings['identifier'] = self.id_string
        elif self.form_pack.id_string:
            settings['identifier'] = self.form_pack.id_string

        # TODO: set the title of the last version as the name of the first
        # section ?
        # Human readable title for this version

        # List of available language for translation. One translation does
        # not mean all labels are translated, but at least one.
        # One special translation not listed here is "_default", which
        # use either the only label available, or the field name.
        # This will be converted down the line to a list. We use an OrderedDict
        # to maintain order and remove duplicates, but will need indexing later

        # Sections separates fields from various level of nesting in case
        # we have repeat group. If you don't have repeat group, you have
        # only one section, if you have repeat groups, you will have one
        # section per repeat group. Sections eventually become sheets in
        # xls export.

        # translation_names
        get_name = lambda tt: tt['name'] if tt['name'] != '' else None
        self.translations = [get_name(t) for t in self.full_txs]

        survey = content['survey']
        fields_by_name = {}
        def _iter_rows(row):
            if isinstance(row, (list, tuple)):
                for subrow in row:
                    for isubrow in _iter_rows(subrow):
                        yield isubrow
            else:
                subrows = row.get('rows', [])
                yield row
                if len(subrows) > 0:
                    for isubrow in _iter_rows(subrows):
                        yield isubrow

        metas = settings.get('metas', {}).copy()
        meta_rows = []
        for metakey in ['start', 'end']:
            if metakey in metas:
                val = metas.pop(metakey)
                _metarow = {}
                if isinstance(val, dict):
                    _metarow = val
                else:
                    if val is True:
                        _metarow['name'] = metakey
                        _metarow['type'] = metakey
                        _metarow['$anchor'] = '${}'.format(metakey)
                if 'name' not in _metarow:
                    _metarow['name'] = metakey
                if 'type' not in _metarow:
                    _metarow['type'] = metakey
                meta_rows.append(_metarow)

        for row in _iter_rows(meta_rows):
            fields_by_name[row['name']] = row

        for row in _iter_rows(survey):
            fields_by_name[row['name']] = row

        choices_copy = deepcopy(content['choices'])
        flat_choice_lists = []
        for (list_name, choices) in choices_copy.items():
            for choice in choices:
                flat_choice_lists.append(
                    {**choice, 'list_name': list_name}
                )

        choice_lists = form_choice_list_from_json_definition(flat_choice_lists,
                                                             self.full_txs,
                                                             self.translations)

        # Extract fields data
        root_section_ = FormRootSection(name=form_pack.title)

        self.sections = OrderedDict()
        self.sections[form_pack.title] = root_section_

        def extract_label_ordered_dict(_row, _txs):
            _rowlabels = _row.get('label', {})
            labels = OrderedDict()
            for tx in _txs:
                anchor = tx['$anchor']
                name = tx['name']
                labels[name] = _rowlabels.get(anchor)
                if name == '':
                    labels[None] = _rowlabels.get(anchor)
            return labels

        def _parse_row(row, parent_group):
            name = row['name']
            if 'label' in row:
                row['labels'] = LabelStruct(row['label'], self.full_txs)
            else:
                row['labels'] = NoLabelStruct(row, self.full_txs)

            obj = form_field_from_json_definition(row, choice_lists)
            obj.set_parent(parent_group)

        def _parse_group(_group, parent):
            extracted_labels = extract_label_ordered_dict(_group,
                                                          self.full_txs)
            group = FormGroup(name=_group['name'],
                              labels=extracted_labels,
                              )
            group.set_parent(parent)
            for row in _group['rows']:
                _parse_row_or_group(row, group)

        def _parse_repeat(_repeat, parent):
            _name = _repeat['name']
            params = {
                'name': _repeat['name'],
                'labels': extract_label_ordered_dict(_repeat, self.full_txs)
            }
            repeat = FormRepeatSection(**params)
            self.sections[_name] = repeat
            repeat.set_parent(parent)
            for row in _repeat['rows']:
                _parse_row_or_group(row, repeat)

        def _parse_row_or_group(row_or_group, parent_group):
            if 'rows' in row_or_group and row_or_group['type'] == 'repeat':
                _parse_repeat(row_or_group, parent_group)
            elif 'rows' in row_or_group:
                _parse_group(row_or_group, parent_group)
            else:
                _parse_row(row_or_group, parent_group)

        for rows in [meta_rows,
                     content['survey']]:
            for row in rows:
                _parse_row_or_group(row, root_section_)

    # FIXME: Find a safe way to use this. Wrapping with try/except isn't enough
    # to fix https://github.com/kobotoolbox/formpack/issues/150
    #
    # def __repr__(self):
    #    return '<FormVersion %s>' % self._stats()

    def to_dict(self, **opts):
        # return self.content
        return flatten_content(self.schema['content'], **opts)

    def lookup(self, prop, default=None):
        result = getattr(self, prop, None)
        if result is None:
            result = self.form_pack.lookup(prop, default=default)
        return result

    def _get_root_node_name(self):
        return self.lookup('root_node_name', default='data')

    def _get_title(self):
        """
        if formversion has no name, uses form's name
        """
        if self.title is None:
            return self.form_pack.title
        return self.title

    def to_xml(self, warnings=None):
        # todo: collect warnings from pyxform compilation when a list is passed
        survey = formversion_pyxform(
            self.to_dict(remove_sheets=['translations', 'translated'],
                         )
                                     )
        title = self._get_title()

        if title is None:
            raise ValueError('cannot create xml on a survey with no title.')

        survey.update({
            'name': self.lookup('root_node_name', 'data'),
            'id_string': self.lookup('id_string'),
            'title': self.lookup('title'),
            'version': self.lookup('id'),
        })

        return survey._to_pretty_xml() #.encode('utf-8')
