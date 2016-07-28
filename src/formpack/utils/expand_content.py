# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from collections import OrderedDict
import re

from .array_to_xpath import EXPANDABLE_FIELD_TYPES


def _convert_special_label_col(content, row, col_shortname, vals):
    if 'translation' in vals:
        translations = content['translations']
        cur_translation = vals['translation']
        cur_translation_index = translations.index(cur_translation)
        _expandable_col = vals['column']
        if _expandable_col not in row:
            row[_expandable_col] = [None] * len(translations)
        elif not isinstance(row[_expandable_col], list):
            _oldval = row[_expandable_col]
            _nti = translations.index(None)
            row[_expandable_col] = [None] * len(translations)
            row[_expandable_col][_nti] = _oldval
        if col_shortname != _expandable_col:
            row[_expandable_col][cur_translation_index] = row[col_shortname]
            del row[col_shortname]


def _get_translations_from_special_cols(special_cols, translations):
    for (colname, parsedvals) in special_cols.iteritems():
        if 'translation' in parsedvals:
            if parsedvals['translation'] not in translations:
                translations.append(parsedvals['translation'])
    return translations


def expand_content(content):
    (specials, translations) = _get_special_survey_cols(content)

    if len(translations) > 0:
        content['translations'] = translations

    for row in content.get('survey', []):
        if 'type' in row:
            _type = row['type']
            if isinstance(_type, basestring):
                row.update(_expand_type_to_dict(row['type']))
            elif isinstance(_type, dict):
                row.update({u'type': _type.keys()[0],
                            u'select_from': _type.values()[0]})
        for key in EXPANDABLE_FIELD_TYPES:
            if key in row and isinstance(row[key], basestring):
                row[key] = _expand_xpath_to_list(row[key])
        for (key, vals) in specials.iteritems():
            if key in row:
                _convert_special_label_col(content, row, key, vals)
    for row in content.get('choices', []):
        for (key, vals) in specials.iteritems():
            if key in row:
                _convert_special_label_col(content, row, key, vals)


def _get_special_survey_cols(content):
    '''This will extract information about columns in an xlsform with ':'s
    and give the "expand_content" information for parsing these columns.
    Examples--
        'media::image',
        'media::image::English',
        'label::Français',
        'hint::English',
    For more examples, see tests.
    '''
    uniq_cols = OrderedDict()
    special = OrderedDict()

    def _pluck_uniq_cols(sheet_name):
        for row in content.get(sheet_name, []):
            _row = dict(filter(lambda (k, v): not isinstance(v, list),
                        row.items()))
            uniq_cols.update(OrderedDict.fromkeys(row.keys()))
    _pluck_uniq_cols('survey')
    _pluck_uniq_cols('choices')

    for column_name in uniq_cols.keys():
        if ':' not in column_name:
            continue
        if column_name.startswith('bind:'):
            continue
        if column_name.startswith('body:'):
            continue
        mtch = re.match('^media\s*::?\s*([^:]+)\s*::?\s*([^:]+)$', column_name)
        if mtch:
            matched = mtch.groups()
            media_type = matched[0]
            special[column_name] = {
                'coltype': 'media',
                'column': 'media::{}'.format(media_type),
                'media': media_type,
                'translation': matched[1],
            }
            continue
        mtch = re.match('^media\s*::?\s*([^:]+)$', column_name)
        if mtch:
            media_type = mtch.groups()[0]
            special[column_name] = {
                'coltype': 'media',
                'column': 'media::{}'.format(media_type),
                'media': media_type,
            }
            continue
        mtch = re.match('^([^:]+)\s*::?\s*([^:]+)$', column_name)
        if mtch:
            # example: label::x, constraint_message::x, hint::x
            matched = mtch.groups()
            column_shortname = matched[0]
            special[column_name] = {
                'column': column_shortname,
                'translation': matched[1],
            }
            # also add the empty column if it exists
            if column_shortname in uniq_cols:
                special[column_shortname] = {
                    'column': column_shortname,
                    'translation': None,
                }
            continue
    translations = _get_translations_from_special_cols(special,
                        content.get('translations', []))
    return (special, translations)


def _expand_type_to_dict(type_str):
    for _re in [
                '^(select_one) (\w+)$',
                '^(select_multiple) (\w+)$',
               ]:
        match = re.match(_re, type_str)
        if match:
            (type_, list_name) = match.groups()
            return {u'type': type_,
                    u'select_from': list_name}

    _or_other = re.match('^select_one (\w+) or_other$', type_str)
    if _or_other:
        list_name = _or_other.groups()[0]
        return {u'type': 'select_one_or_other',
                u'select_from': list_name}

    # if it does not expand, we return the original string
    return {u'type': type_str}


def _expand_xpath_to_list(xpath_string):
    # a placeholder for a future expansion
    return xpath_string
