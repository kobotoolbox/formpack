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

from .utils import parse_xml_to_xmljson, normalize_data_type
from .utils.flatten_content import flatten_content
from .utils.future import OrderedDict
from .utils.xform_tools import formversion_pyxform

from a1d05eba1.utils.kfrozendict import kfrozendict
from a1d05eba1.utils.kfrozendict import freeze as kfrozendict_freeze

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


def iter_rows(row, parent=''):
    # yields: (rowdata, parentname)
    if isinstance(row, (list, tuple)):
        for subrow in row:
            for pps in iter_rows(subrow, parent):
                yield pps
    else:
        subrows = []
        if 'rows' in row:
            (row, subrows) = row.popout('rows')
        yield (row, parent)
        if len(subrows) > 0:
            for pps in iter_rows(subrows, row['name']):
                yield pps

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


class FormVersion(object):
    def __init__(self, form_pack, schema, content):
        # everything pulled from "schema" in these lines:
        id_string = schema.get('id_string')
        title = schema.get('title', form_pack.title)
        _id = schema.get('version')
        version_id_key = schema.get('version_id_key',
                                    form_pack.default_version_id_key)

        content = kfrozendict_freeze(content)
        self.title = title
        self.form_pack = form_pack
        self.content = content
        self.full_txs = content.get('translations')
        settings = content.get('settings')

        # slug of title
        self.root_node_name = self._get_root_node_name()

        # form version id, unique to this version of the form
        self.id = _id
        self.version_id_key = version_id_key

        # form string id, unique to this form, shared accross versions
        self.id_string = id_string
        if self.id_string:
            settings = settings.copy(identifier=self.id_string)
        elif self.form_pack.id_string:
            settings = settings.copy(identifier=self.form_pack.id_string)

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

        flat_choice_lists = []
        for (list_name, choices) in content['choices'].items():
            for choice in choices:
                flat_choice_lists.append(
                    {**choice.unfreeze(), 'list_name': list_name}
                )

        choice_lists = form_choice_list_from_json_definition(flat_choice_lists,
                                                             self.full_txs,
                                                             self.translations)
        survey_rows = (self._load_metas(settings['metas']) +
                       content['survey'],
                       )

        fields_by_name = {}
        self.sections = sections = OrderedDict()
        _title = form_pack.title
        sections[_title] = root_section = FormRootSection(name=_title)

        for (row, parent_name) in iter_rows(survey_rows, root_section.name):
            name = row['name']
            _type = row['type']
            parent_section = fields_by_name.get(parent_name, root_section)
            if _type in ['group', 'repeat']:
                extracted_labels = extract_label_ordered_dict(row,
                                                              self.full_txs)
                opts = {'name': row['name'],
                        'labels': extracted_labels}
                if _type == 'repeat':
                    obj = FormRepeatSection(**opts)
                    sections[obj.name]= obj
                else:
                    obj = FormGroup(**opts)
            else:
                if 'label' in row:
                    labels = LabelStruct(row['label'], self.full_txs)
                else:
                    labels = NoLabelStruct(row, self.full_txs)
                obj = form_field_from_json_definition(row,
                                                      labels,
                                                      choice_lists)
            obj.set_parent(parent_section)
            fields_by_name[name] = obj


    def _load_metas(self, frozen_metas):
        metas = frozen_metas.unfreeze()
        meta_rows = []
        def _load_meta(key, val):
            _row = {}
            if val is True:
                _row.update({
                    'name': key,
                    'type': key,
                    '$anchor': '$' + key,
                })
            elif isinstance(val, dict):
                _row.update(val)
            if 'name' not in _row:
                _row['name'] = metakey
            if 'type' not in _row:
                _row['type'] = metakey
            meta_rows.append(_row)
        for metakey in ['start']:
            if metakey in metas:
                metaval = metas.pop(metakey)
                _load_meta(metakey, metaval)
        for (metakey, metaval) in metas.items():
            _load_meta(metakey, metaval)
        return kfrozendict_freeze(meta_rows)

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
