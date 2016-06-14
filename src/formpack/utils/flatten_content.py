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
    if 'survey' in survey_content:
        for row in survey_content['survey']:
            _flatten_survey_row(row)
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


def _flatten_survey_row(row):
    for key in ['relevant', 'constraint']:
        if key in row and isinstance(row[key], (list, tuple)):
            row[key] = array_to_xpath(row[key])
    if 'type' in row and isinstance(row['type'], dict):
        row['type'] = _stringify_type(row['type'])
