# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from array_to_xpath import array_to_xpath

TYPE_KEYS = ['select_one', 'select_multiple']


def flatten_content(survey_content):
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
    return survey_content


def _stringify_type(json_qtype):
    '''
    {'select_one': 'xyz'} -> 'select_one xyz'
    {'select_multiple': 'xyz'} -> 'select_mutliple xyz'
    '''
    if len(json_qtype.keys()) != 1:
        raise ValueError('Type object must have exactly one key: %s' %
                         ', '.join(TYPE_KEYS))
    for try_key in TYPE_KEYS:
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
    for key in ['relevant', 'constraint']:
        if key in row and isinstance(row[key], (list, tuple)):
            row[key] = array_to_xpath(row[key])
    if 'type' in row and isinstance(row['type'], dict):
        row['type'] = _stringify_type(row['type'])
