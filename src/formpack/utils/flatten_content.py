# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from copy import deepcopy
from array_to_xpath import array_to_xpath, EXPANDABLE_FIELD_TYPES
from ..constants import UNTRANSLATED


def flatten_content_in_place(survey_content):
    '''
    if asset.content contains nested objects, then
    this is where we "flatten" them so that they
    will pass through to pyxform and to XLS exports
    '''
    translations = survey_content.get('translations', [])

    def _iter_through_sheet(sheet_name):
        if sheet_name in survey_content:
            for row in survey_content[sheet_name]:
                _flatten_survey_row(row)
                _flatten_translated_fields(row, translations)
    _iter_through_sheet('survey')
    _iter_through_sheet('choices')

    if isinstance(survey_content.get('settings'), dict):
        survey_content['settings'] = [survey_content['settings']]

    # do not list translations when only default exists
    if len(translations) == 1 and translations[0] == UNTRANSLATED:
        del survey_content['translations']
    return None


def flatten_content(survey_content, in_place=False):
    if in_place:
        flatten_content_in_place(survey_content)
        return None
    else:
        survey_content_copy = deepcopy(survey_content)
        flatten_content_in_place(survey_content_copy)
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


def _flatten_translated_fields(row, translations):
    # a workaround to get the desired values
    if len(translations) == 0:
        translations = [UNTRANSLATED]
    for key in row.keys():
        val = row[key]
        if isinstance(val, list):
            items = val
            del row[key]
            for i in xrange(0, len(translations)):
                _t = translations[i]
                value = items[i]
                if value is None:
                    continue
                if _t is UNTRANSLATED:
                    row[key] = value
                else:
                    row['{}::{}'.format(key, _t)] = value


def _flatten_survey_row(row):
    for key in EXPANDABLE_FIELD_TYPES:
        if key in row and isinstance(row[key], (list, tuple)):
            row[key] = array_to_xpath(row[key])
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
            else:
                row['type'] = '{} {}'.format(_type, _list_name)
