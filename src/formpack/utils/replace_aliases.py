# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from collections import defaultdict
from copy import deepcopy
import json

from pyxform import aliases as pyxform_aliases
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT

from .future import iteritems, OrderedDict
from .string import str_types

# This file is a mishmash of things which culminate in the
# "replace_aliases" method which iterates through a survey and
# replaces xlsform aliases with a standardized set of colunns,
# question types, and values.


TF_COLUMNS = [
    'required',
]


def aliases_to_ordered_dict(_d):
    """
    unpacks a dict-with-lists to an ordered dict with keys sorted by length
    """
    arr = []
    for original, aliases in _d.items():
        arr.append((original, original))
        if isinstance(aliases, bool):
            aliases = [original]
        elif isinstance(aliases, str_types):
            aliases = [aliases]
        for alias in aliases:
            arr.append((alias, original,))
    return OrderedDict(sorted(arr, key=lambda _kv: 0-len(_kv[0])))


types = aliases_to_ordered_dict({
    'begin_group': [
        'begin group',
        'begin  group',
    ],
    'end_group': [
        'end group',
        'end  group'
    ],
    'begin_repeat': [
        'begin lgroup',
        'begin repeat',
        'begin looped group',
    ],
    'end_repeat': [
        'end lgroup',
        'end repeat',
        'end looped group',
    ],
    'text': ['string'],
    'acknowledge': ['trigger'],
    'image': ['photo'],
    'datetime': ['dateTime'],
    'deviceid': ['imei'],
    'geopoint': ['gps'],
})

selects = aliases_to_ordered_dict({
    'select_multiple': [
        'select all that apply',
        'select multiple',
        'select many',
        'select_many',
        'select all that apply from',
        'add select multiple prompt using',
    ],
    'select_one_external': [
        'select one external',
    ],
    'select_one': [
        'select one',
        'select one from',
        'add select one prompt using',
        'select1',
    ],
})
# Python3: Cast to a list because it's merged into other dicts
# (i.e `SELECT_SCHEMA` in validators.py)
SELECT_TYPES = list(selects.keys())

META_TYPES = [
    'start',
    'today',
    'end',
    'deviceid',
    'phone_number',
    'simserial',
    # meta values
    'username',
    # reconsider:
    'phonenumber',
    'imei',
    'subscriberid',
]

LABEL_OPTIONAL_TYPES = [
    'calculate',
    'begin_group',
    'begin_repeat',
] + META_TYPES

GEO_TYPES = [
    'gps',
    'geopoint',
    'geoshape',
    'geotrace',
]

MAIN_TYPES = [
    # basic entry
    'text',
    'integer',
    'decimal',
    'email',
    'barcode',
    # collect media
    'video',
    'image',
    'audio',
    # enter time values
    'date',
    'datetime',
    'time',

    # prompt to collect geo data
    'location',

    # no response
    'acknowledge',
    'note',
] + GEO_TYPES
formpack_preferred_types = set(MAIN_TYPES + LABEL_OPTIONAL_TYPES + SELECT_TYPES)

_pyxform_type_aliases = defaultdict(list)
_formpack_type_reprs = {}

for _type, val in QUESTION_TYPE_DICT.items():
    _xform_repr = json.dumps(val, sort_keys=True)
    if _type in formpack_preferred_types:
        _formpack_type_reprs[_type] = _xform_repr
    else:
        _pyxform_type_aliases[_xform_repr].append(_type)

formpack_type_aliases = aliases_to_ordered_dict(dict([
        (_type, _pyxform_type_aliases[_repr])
        for _type, _repr in _formpack_type_reprs.items()
    ]))


KNOWN_TYPES = set(list(QUESTION_TYPE_DICT.keys())
                  + list(selects.values())
                  + list(types.values()))


def _unpack_headers(p_aliases, fp_preferred):
    _aliases = p_aliases.copy().items()
    combined = dict([
        (key, val if (val not in fp_preferred) else fp_preferred[val])
        for key, val in _aliases
    ] + list(fp_preferred.items()))
    # ensure that id_string points to id_string (for example)
    combined.update(dict([
        (val, val) for val in combined.values()
    ]))
    return combined


formpack_preferred_settings_headers = {
    'title': 'form_title',
    'form_id': 'id_string',
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


def dealias_type(type_str, strict=False, allowed_types=None):
    if allowed_types is None:
        allowed_types = {}

    if type_str in types.keys():
        return types[type_str]
    if type_str in allowed_types.keys():
        return allowed_types[type_str]
    if type_str in KNOWN_TYPES:
        return type_str
    for key in SELECT_TYPES:
        if type_str.startswith(key):
            return type_str.replace(key, selects[key])
    if strict:
        raise ValueError('unknown type {}'.format([type_str]))


def replace_aliases(content, in_place=False, allowed_types=None):
    if in_place:
        replace_aliases_in_place(content, allowed_types=allowed_types)
        return None
    else:
        _content = deepcopy(content)
        replace_aliases_in_place(_content, allowed_types=allowed_types)
        return _content


def replace_aliases_in_place(content, allowed_types=None):
    if allowed_types is not None:
        allowed_types = aliases_to_ordered_dict(allowed_types)

    for row in content.get('survey', []):
        if row.get('type'):
            row['type'] = dealias_type(row.get('type'), strict=True, allowed_types=allowed_types)

        for col in TF_COLUMNS:
            if col in row:
                if row[col] in pyxform_aliases.yes_no:
                    row[col] = pyxform_aliases.yes_no[row[col]]

        for key, val in iteritems(survey_header_columns):
            if key in row and key != val:
                row[val] = row[key]
                del row[key]

    for row in content.get('choices', []):
        if 'list name' in row:
            row['list_name'] = row.pop('list name')
        if 'name' in row and 'value' in row and row['name'] != row['value']:
            raise ValueError('Conflicting name and value in row: {}'.format(repr(row)))
        if 'value' in row:
            row['name'] = row.pop('value')

    # replace settings
    settings = content.get('settings', {})
    if isinstance(settings, list):
        raise ValueError('Cannot run replace_aliases() on content which has not'
                         ' first been parsed through "expand_content".')

    if settings:
        content['settings'] = dict([
            (settings_header_columns.get(key, key), val)
            for key, val in settings.items()
        ])
