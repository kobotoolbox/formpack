# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from array_to_xpath import array_to_xpath
from copy import deepcopy


def flatten_content_inplace(survey_content):
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
                if len(translations) > 0:
                    _flatten_translated_fields(row, translations)
    _iter_through_sheet('survey')
    _iter_through_sheet('choices')
    return None


def flatten_content_copy(survey_content):
    survey_content_copy = deepcopy(survey_content)
    flatten_content_inplace(survey_content_copy)
    return survey_content_copy


def flatten_content(survey_content):
    flatten_content_inplace(survey_content)
    return survey_content


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
    for key in row.keys():
        val = row[key]
        if isinstance(val, list):
            items = val
            del row[key]
            for i in xrange(0, len(translations)):
                _t = translations[i]
                value = items[i]
                tkey = key if _t is None else '{}::{}'.format(key, _t)
                row[tkey] = value


def _flatten_survey_row(row):
    for key in ['relevant', 'constraint', 'calculation', 'repeat_count']:
        if key in row and isinstance(row[key], (list, tuple)):
            row[key] = array_to_xpath(row[key])
    if 'type' in row and isinstance(row['type'], dict):
        row['type'] = _stringify_type__depr(row['type'])
