# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from copy import deepcopy
from collections import defaultdict, OrderedDict
from array_to_xpath import array_to_xpath
from ..constants import (UNTRANSLATED, OR_OTHER_COLUMN,
                         TAG_COLUMNS_AND_SEPARATORS)


def flatten_content_in_place(survey_content,
                             remove_columns=None,
                             remove_sheets=None,
                             ):
    '''
    if asset.content contains nested objects, then
    this is where we "flatten" them so that they
    will pass through to pyxform and to XLS exports
    '''
    if isinstance(remove_columns, list):
        raise Exception('bad')
    if remove_columns is None:
        remove_columns = {}
    if remove_sheets is None:
        remove_sheets = []
    remove_sheets = set(remove_sheets + ['translated', 'translations', 'schema'])
    popped_sheets = {}
    for sheet_name in remove_sheets:
        popped_sheets[sheet_name] = survey_content.pop(sheet_name, [])

    def _iter_through_sheet(sheet_name):
        _removed = remove_columns.get(sheet_name, [])
        if sheet_name in survey_content:
            for row in survey_content[sheet_name]:
                _flatten_translated_fields(row,
                                           popped_sheets.get('translations'),
                                           popped_sheets.get('translated'),
                                           )
                _flatten_survey_row(row)
                for key in _removed:
                    row.pop(key, None)
    _iter_through_sheet('survey')
    _iter_through_sheet('choices')

    if isinstance(survey_content.get('settings'), dict):
        survey_content['settings'] = [survey_content['settings']]

    return None


def flatten_content(survey_content, in_place=False, **opts):
    if in_place:
        flatten_content_in_place(survey_content, **opts)
        return None
    else:
        survey_content_copy = deepcopy(survey_content)
        flatten_content_in_place(survey_content_copy, **opts)
        return survey_content_copy


def _stringify_type__depr(json_qtype):
    '''
    NOTE: This particular representation of select_* types is being
          deprecated. [Oct 2016]

    {'select_one': 'xyz'} -> 'select_one xyz'
    {'select_multiple': 'xyz'} -> 'select_mutliple xyz'
    '''
    _type_keys = ['select_one', 'select_multiple']
    if len(json_qtype.keys()) != 1:
        raise ValueError('Type object must have exactly one key: %s' %
                         ', '.join(_type_keys))
    for try_key in _type_keys:
        if try_key in json_qtype:
            return '{} {}'.format(try_key, json_qtype[try_key])
    if 'select_one_or_other' in json_qtype:
        return 'select_one %s or_other' % json_qtype['select_one_or_other']


def flatten_tag_list(tag_list, tag_cols_and_seps=None):
    '''
    takes a list of tags and reassigns them to the tag column in which they
    appear on import of xls
    '''
    return _flatten_tags({'tags': tag_list}, tag_cols_and_seps)


def _flatten_tags(row, tag_cols_and_seps=None):
    '''
    takes a "tags" column with an array of tags and
    reassigns them to the tag column in which they appear
    on import of xls
    '''
    if tag_cols_and_seps is None:
        tag_cols_and_seps = {}

    for col in ['tags'] + tag_cols_and_seps.keys():
        if col in row and isinstance(row[col], basestring):
            return

    tag_list = row.pop('tags', [])
    tag_res = OrderedDict()
    for tag_col in tag_cols_and_seps.keys():
        tag_res[tag_col] = r'^%s:(\S+)$' % tag_col

    additionals = defaultdict(list)

    for tag in tag_list:
        matched = False
        for (col, re_str) in tag_res.items():
            mtch = re.match(re_str, tag)
            if mtch:
                additionals[col].append(mtch.groups()[0])
                matched = True
        if not matched:
            additionals['tags'].append(tag)

    for (col, items) in additionals.items():
        separator = tag_cols_and_seps.get(col, ' ')
        row[col] = separator.join(items)

    return row


def translated_col_list(columns, translations, translated):
    if (len(translations) == 0 and len(translated) != 0) or (
            len(translations) != 0 and len(translated) == 0):
        raise ValueError('cannot have translations with no translated')

    def _for_each_t(col):
        return lambda arr, _tr: arr + [
            col if (_tr is None) else "{}::{}".format(col, _tr)
        ]

    def _expand_translateds(arr, col):
        if col in translated:
            arr += reduce(_for_each_t(col), translations, [])
        else:
            arr.append(col)
        return arr
    return reduce(_expand_translateds, columns, [])


def _flatten_translated_fields(row, translations, translated_cols,
                               col_order=False,
                               strip_null_vals_from_named_translations=True,
                               ):
    if len(translations) == 0:
        translations = [UNTRANSLATED]

    _placed_cols = set()

    def _place_col_in_order(col, base_col=None):
        if col_order is False:
            return
        if col in col_order:
            if col not in _placed_cols:
                _placed_cols.update([col])
            return
        else:
            if base_col in col_order:
                _i = col_order.index(base_col)
                col_order.insert(_i, col)
                _placed_cols.update([col])
            else:
                col_order.append(col)
                _placed_cols.update([col])

    o_row = deepcopy(row)
    for key in (k for k in translated_cols if k in row):
        items = row[key]
        if not isinstance(items, list):
            raise ValueError('"{}" column is not translated'.format(
                    key,
                ), o_row)
        if len(items) != len(translations):
            raise ValueError('Incorrect translation count: "{}"'.format(
                    key,
                ), o_row)
        del row[key]
        for i in xrange(0, len(translations)):
            _t = translations[i]
            try:
                value = items[i]
            except IndexError:
                raise ValueError(
                    'Column "{}" does not have enough translations'.format(key)
                    )
            if _t is UNTRANSLATED:
                row[key] = value
                _place_col_in_order(key)
            else:
                _built_colname = '{}::{}'.format(key, _t)
                if (value is None) and strip_null_vals_from_named_translations:
                    value = ''
                row[_built_colname] = value
                _place_col_in_order(_built_colname, key)
    _placed_cols.update(row.keys())
    if col_order:
        for col in (c for c in col_order if c not in _placed_cols):
            col_order.remove(col)


def _flatten_survey_row(row):
    for key in row:
        if isinstance(row[key], (list, tuple)):
            row[key] = array_to_xpath(row[key])
    if 'tags' in row:
        _flatten_tags(row, tag_cols_and_seps=TAG_COLUMNS_AND_SEPARATORS)
    if 'type' in row:
        _type = row['type']
        if isinstance(row.get('required'), bool):
            row['required'] = 'true' if row['required'] else 'false'
        if isinstance(_type, dict):
            row['type'] = _stringify_type__depr(_type)
        elif 'select_from_list_name' in row:
            _list_name = row.pop('select_from_list_name')
            if row['type'] == 'select_one_or_other':
                row['type'] = 'select_one {} or_other'.format(_list_name)
            elif row['type'] == 'select_multiple_or_other':
                row['type'] = 'select_multiple {} or_other'.format(_list_name)
            elif row.get(OR_OTHER_COLUMN):
                row['type'] = '{} {} or_other'.format(_type, _list_name)
            else:
                row['type'] = '{} {}'.format(_type, _list_name)

    # TODO: remove this once https://github.com/XLSForm/pyxform/issues/236 is
    # fixed?
    try:
        _order = row['order']
    except KeyError:
        pass
    else:
        if not isinstance(_order, basestring):
            row['order'] = '{}'.format(_order)
