# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

# This file is a mishmash of things which culminate in the
# "replace_aliases" method which iterates through a survey and
# replaces xlsform aliases with a standardized set of colunns,
# question types, and values.

from copy import deepcopy

from .aliases import (
        LABEL_OPTIONAL_TYPES,
        KNOWN_TYPES,
        TYPES,
        TF_COLUMNS,
        SURVEY_RENAMES,
        SETTINGS_RENAMES,
        SELECTS,
        pyxform_aliases,
        aliases_to_ordered_dict,
    )


def dealias_type(type_str, strict=False, allowed_types=None):
    if allowed_types is None:
        allowed_types = {}

    if type_str in TYPES.keys():
        return TYPES[type_str]
    if type_str in allowed_types.keys():
        return allowed_types[type_str]
    if type_str in KNOWN_TYPES:
        return type_str
    for key in SELECTS.keys():
        if type_str.startswith(key):
            return type_str.replace(key, SELECTS[key])
    if strict:
        raise ValueError('unknown type {}'.format([type_str]))

def _survey_row_replace_type(row, allowed_types):
    if row.get('type'):
        row['type'] = dealias_type(row.get('type'),
                                   strict=True,
                                   allowed_types=allowed_types)


def get_survey_columns_to_rename(content__survey, columns):
    # without changing content, return a dict with columns in the survey
    # sheet that need to be renamed
    renames = {}
    for (key, val) in SURVEY_RENAMES.iteritems():
        if key == val:
            continue

        for col in columns:
            if col.startswith(key):
                renames[col] = col.replace(key, val)
    return renames


# lightweight utility methods that modify contents in-place using only
# the given parameters
#
def _all_keys(arr):
    all_keys = set()
    for row in arr:
        all_keys.update(row.keys())
    return all_keys


def _survey_row_parse_bool_values(row, tf_columns, yn_aliases):
    for col in tf_columns:
        if col in row:
            if row[col] in yn_aliases:
                row[col] = yn_aliases[row[col]]


def _survey_row_replace_columns(row, renames):
    for (col, replacewith) in renames.items():
        if col in row:
            row[replacewith] = row.pop(col)


def _replace_settings(content, renames):
    for key in content['settings'].keys():
        if key in renames and renames[key] != key:
            _new_key = renames[key]
            content['settings'][_new_key] = content['settings'].pop(key)


# the important functions in this file:
# replace_aliases, replace_aliases_in_place
#
def replace_aliases_in_place(content, allowed_types=None):
    '''
    fixes alias issues in a number of places:
    * survey sheet:
        - question types (e.g. change "select1" to "select_one")
        - replace boolean aliases in "required" fields, when appropriate
        - column headers (e.g. change "caption" to "label")

    * choices column headers
        - "list name" to "list_name"

    * settings
        - misc aliases
    '''
    if allowed_types is not None:
        allowed_types = aliases_to_ordered_dict(allowed_types)

    surv_content = content.get('survey', [])
    columns = _all_keys(surv_content)
    renames = get_survey_columns_to_rename(surv_content, columns)

    for row in surv_content:
        _survey_row_replace_type(row, allowed_types)
        _survey_row_replace_columns(row, renames)
        _survey_row_parse_bool_values(row, TF_COLUMNS, pyxform_aliases.yes_no)

    choices_renames = {
        'list name': 'list_name',
        'value': 'name',
    }
    for row in content.get('choices', []):
        _survey_row_replace_columns(row, choices_renames)

    # replace settings
    if 'settings' in content and isinstance(content['settings'], dict):
        _replace_settings(content, SETTINGS_RENAMES)


def replace_aliases(content, in_place=False, allowed_types=None):
    if in_place:
        replace_aliases_in_place(content, allowed_types=allowed_types)
        return None
    else:
        _content = deepcopy(content)
        replace_aliases_in_place(_content, allowed_types=allowed_types)
        return _content
