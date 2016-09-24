# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

# This file is a mishmash of things which culminate in the
# "replace_aliases" method which iterates through a survey and
# replaces xlsform aliases with a standardized set of colunns,
# question types, and values.

import json
from copy import deepcopy
from collections import OrderedDict

from pyxform import aliases as pyxform_aliases
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT


TF_COLUMNS = [
    'required',
]


def aliases_to_ordered_dict(_d):
    '''
    unpacks a dict-with-lists to an ordered dict with keys sorted by length
    '''
    arr = []
    for (original, aliases) in _d.items():
        arr.append((original, original))
        for alias in aliases:
            arr.append((alias, original,))
    return OrderedDict(sorted(arr, key=lambda _kv: 0-len(_kv[0])))

types = aliases_to_ordered_dict({
    u'begin_group': [
        u'begin group',
        u'begin  group',
    ],
    u'end_group': [
        u'end group',
        u'end  group'
    ],
    u'begin_repeat': [
        u'begin lgroup',
        u'begin repeat',
        u'begin looped group',
    ],
    u'end_repeat': [
        u'end lgroup',
        u'end repeat',
        u'end looped group',
    ],
})

selects = aliases_to_ordered_dict({
    u'select_multiple': [
        u'select all that apply',
        u'select multiple',
        u'select many',
        u'select_many',
        u'select all that apply from',
        u'add select multiple prompt using',
    ],
    u'select_one_external': [
        u'select one external',
    ],
    u'select_one': [
        u'select one',
        u'select one from',
        u'add select one prompt using',
        u'select1',
    ],
})

KNOWN_TYPES = set(QUESTION_TYPE_DICT.keys() + selects.values() + types.values())


def _unpack_headers(p_aliases, fp_preferred):
    _aliases = p_aliases.copy().items()
    combined = dict([
        (key, val if (val not in fp_preferred) else fp_preferred[val])
        for (key, val) in _aliases
    ] + fp_preferred.items())
    # ensure that id_string points to id_string (for example)
    combined.update(dict([
        (val, val) for val in combined.values()
    ]))
    return combined

formpack_preferred_settings_headers = {
    'title': 'form_title',
}
settings_header_columns = _unpack_headers(pyxform_aliases.settings_header,
                                          formpack_preferred_settings_headers)

# this opts out of columns with '::' (except media columns)
formpack_preferred_survey_headers = {
    'bind::calculate': 'calculation',
    'bind::required': 'required',
    'bind::jr:requiredMsg': 'required_message',
    'bind::relevant': 'relevant',
    'bind::jr:constraintMsg': 'constraint_message',
    'bind::constraint': 'constraint',
    'bind::readonly': 'read_only',
    'control::jr:count': 'repeat_count',
    'control::appearance': 'appearance',
    'control::rows': 'rows',
    'control::autoplay': 'autoplay',
    'bind::jr:noAppErrorString': 'no_app_error_string',
}
survey_header_columns = _unpack_headers(pyxform_aliases.survey_header,
                                        formpack_preferred_survey_headers)


def dealias_type(type_str, strict=False):
    if type_str in KNOWN_TYPES:
        return type_str
    if type_str in types.keys():
        return types[type_str]
    for key in selects.keys():
        if type_str.startswith(key):
            return type_str.replace(key, selects[key])
    if strict:
        raise ValueError('unknown type {}'.format([type_str]))


def replace_aliases(content, in_place=False):
    if in_place:
        replace_aliases_in_place(content)
        return None
    else:
        _content = deepcopy(content)
        replace_aliases_in_place(_content)
        return _content


def replace_aliases_in_place(content):
    for row in content.get('survey', []):
        if row.get('type'):
            row['type'] = dealias_type(row.get('type'), strict=True)

        for col in TF_COLUMNS:
            if col in row:
                if row[col] in pyxform_aliases.yes_no:
                    row[col] = pyxform_aliases.yes_no[row[col]]

        for (key, val) in survey_header_columns.iteritems():
            if key in row and key != val:
                row[val] = row[key]
                del row[key]

    # replace settings
    settings = content.get('settings', {})
    if isinstance(settings, list) and len(settings) > 0:
        settings = settings[0]

    if settings:
        content['settings'] = dict([
            (settings_header_columns[key], val)
            for (key, val) in settings.items() if key in settings_header_columns
        ])
