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


formpack_preferred_type_aliases = {
    'select one': 'select_one',
    'select all that apply': 'select_multiple',
    'select one external': 'select_one_external',
    'begin group': 'begin_group',
    'end group': 'end_group',
    'begin repeat': 'begin_repeat',
    'end repeat': 'end_repeat',
}
pyxform_select = deepcopy(pyxform_aliases.select)
pyxform_select.update(formpack_preferred_type_aliases)
pyxform_select.update({
    'select multiple': 'select_multiple',
    'select many': 'select_multiple',
    'select_many': 'select_multiple',
})

_KNOWN_TYPES = QUESTION_TYPE_DICT.keys() + pyxform_select.values()

select_aliases = OrderedDict()
# sort select_aliases in order of string length
for key in sorted(pyxform_select.keys(), key=lambda k: -1*len(k)):
    val = pyxform_select[key]
    if key in formpack_preferred_type_aliases.values():
        select_aliases[key] = key
        continue
    if val in formpack_preferred_type_aliases:
        val = formpack_preferred_type_aliases[val]
    select_aliases[key] = val


def _unpack_headers(p_aliases, fp_preferred):
    _aliases = p_aliases.copy().items()
    return dict([
        (key, val if (val not in fp_preferred) else fp_preferred[val])
        for (key, val) in _aliases
    ] + [
        (key, val) for (key, val) in fp_preferred.items()
    ])

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
    if type_str in _KNOWN_TYPES:
        return type_str
    for key in select_aliases.keys():
        if type_str.startswith(key):
            return type_str.replace(key, select_aliases[key])
    if strict:
        raise ValueError('unknown type {}'.format([type_str]))


def replace_aliases(content):
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
