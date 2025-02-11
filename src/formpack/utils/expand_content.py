# coding: utf-8

# This module might be more appropriately named "standardize_content"
# and pass content through to formpack.utils.replace_aliases during
# the standardization step: expand_content_in_place(...)
import re
from collections import OrderedDict
from copy import deepcopy
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from .array_to_xpath import EXPANDABLE_FIELD_TYPES
from .iterator import get_first_occurrence
from .replace_aliases import META_TYPES, selects
from ..constants import (
    MEDIA_COLUMN_NAMES,
    OR_OTHER_COLUMN,
    TAG_COLUMNS_AND_SEPARATORS,
    UNTRANSLATED,
)

REMOVE_EMPTY_STRINGS = True
# this will be used to check which version of formpack was used to compile the
# asset content
SCHEMA_VERSION = '1'


def _expand_translatable_content(
    content: Dict[str, List[Any]],
    row: Dict[str, Union[str, List[Any]]],
    col_shortname: str,
    special_column_details: Dict[str, Optional[str]],
) -> None:
    _scd = special_column_details
    if 'translation' in _scd:
        translations = content['translations']
        cur_translation = _scd['translation']
        cur_translation_index = translations.index(cur_translation)
        _expandable_col = _scd['column']
        if _expandable_col not in row:
            row[_expandable_col] = [None] * len(translations)
        elif not isinstance(row[_expandable_col], list):
            _oldval = row[_expandable_col]
            _nti = translations.index(UNTRANSLATED)
            row[_expandable_col] = [None] * len(translations)
            row[_expandable_col][_nti] = _oldval
        if col_shortname != _expandable_col:
            row[_expandable_col][cur_translation_index] = row[col_shortname]
            breakpoint()
            del row[col_shortname]


def _expand_tags(
    row: Dict[str, Union[str, List[Any]]],
    tag_cols_and_seps: Optional[Dict[str, str]] = None,
) -> Dict[str, Union[str, List[Any]]]:
    if tag_cols_and_seps is None:
        tag_cols_and_seps = {}
    tags = []
    main_tags = row.pop('tags', None)
    if main_tags:
        if isinstance(main_tags, str):
            tags = tags + main_tags.split()
        elif isinstance(main_tags, list):
            # carry over any tags listed here
            tags = main_tags

    for tag_col in tag_cols_and_seps.keys():
        tags_str = row.pop(tag_col, None)
        if tags_str and isinstance(tags_str, str):
            for tag in re.findall(r'([\#\+][a-zA-Z][a-zA-Z0-9_]*)', tags_str):
                tags.append(f'hxl:{tag}')
    if tags:
        row['tags'] = tags
    return row


def _get_translations_from_special_cols(
    special_cols: OrderedDict,
    translations: List[str],
) -> Tuple[List[str], Set[str]]:
    translated_cols = []
    for colname, parsedvals in iter(special_cols.items()):
        if 'translation' in parsedvals:
            translated_cols.append(parsedvals['column'])
            if parsedvals['translation'] not in translations:
                translations.append(parsedvals['translation'])
    return translations, set(translated_cols)


def clean_column_name(column_name: str, already_seen: dict[str, str]) -> str:
    """

    Preserves ":" vs "::" and any spaces around the colons
    """
    RE_MEDIA_COLUMN_NAMES = '|'.join(MEDIA_COLUMN_NAMES)
    if column_name in already_seen:
        return already_seen[column_name]

    # "LaBeL" -> "label", "HiNT" -> "hint"
    if column_name.lower() in ['label', 'hint']:
        cleaned = column_name.lower()
        already_seen[column_name] = cleaned
        return cleaned

    # "Bind:Some:Thing" -> "bind:Some:Thing", "BodY:" -> "body:"
    match = re.match(r'^(bind|body):.*', column_name, flags=re.IGNORECASE)
    if match:
        lower_cased = match.groups()[0].lower()
        cleaned = re.sub(r'^(bind|body)', lower_cased, column_name, flags=re.IGNORECASE)
        already_seen[column_name] = cleaned
        return cleaned

    # "Media:Audio::ES" -> "media:audio::ES", "ViDeO : ES" -> "video : ES"
    match = re.match(
        rf'^(media\s*::?\s*)?({RE_MEDIA_COLUMN_NAMES})\s*::?\s*([^:]+)$',
        column_name,
        flags=re.IGNORECASE
    )
    if match:
        matched = match.groups()
        lower_media_prefix = matched[0].lower() if matched[0] else ''
        lower_media_type = matched[1].lower()
        cleaned = re.sub(rf'^(media\s*::?\s*)?({RE_MEDIA_COLUMN_NAMES})(\s*::?\s*)([^:]+)$',
                          rf'{lower_media_prefix}{lower_media_type}\3\4',
                          column_name, flags=re.IGNORECASE)
        already_seen[column_name] = cleaned
        return cleaned

    # "Media: AuDiO" -> "media: audio", "VIDEO" -> "video"
    match = re.match(
        rf'^(media\s*::?\s*)?({RE_MEDIA_COLUMN_NAMES})$', column_name, flags=re.IGNORECASE
    )
    if match:
        matched = match.groups()
        lower_media_prefix = matched[0].lower() if matched[0] else ''
        lower_media_type = matched[1].lower()
        cleaned = re.sub(rf'^(media\s*::?\s*)?({RE_MEDIA_COLUMN_NAMES})$',
                          rf'{lower_media_prefix}{lower_media_type}',
                          column_name, flags=re.IGNORECASE)
        already_seen[column_name] = cleaned

    match = re.match(r'^([^:]+)(\s*::?\s*)([^:]+)$', column_name)
    if match:
        # example: label::x, constraint_message::x, hint::x
        matched = match.groups()
        lower_column_shortname = matched[0].lower()
        cleaned = re.sub(r'^([^:]+)(\s*::?\s*)([^:]+)$', rf'{lower_column_shortname}\2\3', column_name,
                          flags=re.IGNORECASE)
        already_seen[column_name] = cleaned
        return cleaned
    cleaned = column_name.lower()
    already_seen[column_name] = cleaned
    return cleaned


def preprocess_columns(content: Dict[str, List[Any]]) -> None:
    seen = {}
    for sheet, rows in content.items():
        for row in rows:
            for column_name, value in row.copy().items():
                cleaned_name = clean_column_name(column_name, seen)
                del row[column_name]
                row[cleaned_name] = value

def expand_content_in_place(content: Dict[str, List[Any]]) -> None:
    preprocess_columns(content)

    specials, translations, transl_cols = _get_special_survey_cols(content)

    if len(translations) > 0:
        content['translations'] = translations
        content['translated'] = transl_cols

    survey_content = content.get('survey', [])
    _metas = []

    for row in survey_content:
        if 'name' in row and row['name'] is None:
            del row['name']
        if 'type' in row:
            _type = row['type']
            if _type in META_TYPES:
                _metas.append(row)
            if isinstance(_type, str):
                row.update(_expand_type_to_dict(row['type']))
            elif isinstance(_type, dict):
                # legacy {'select_one': 'xyz'} format might
                # still be on kobo-prod
                _type_str = _expand_type_to_dict(
                    get_first_occurrence(_type.keys())
                )['type']
                _list_name = get_first_occurrence(_type.values())
                row.update(
                    {
                        'type': _type_str,
                        'select_from_list_name': _list_name,
                    }
                )

        _expand_tags(row, tag_cols_and_seps=TAG_COLUMNS_AND_SEPARATORS)

        for key in EXPANDABLE_FIELD_TYPES:
            if key in row and isinstance(row[key], str):
                row[key] = _expand_xpath_to_list(row[key])
        for key, vals in iter(specials.items()):
            if key in row:
                _expand_translatable_content(content, row, key, vals)

        if REMOVE_EMPTY_STRINGS:
            row_copy = dict(row)
            for key, val in row_copy.items():
                if val == '':
                    del row[key]

    # for now, prepend meta questions to the beginning of the survey
    # eventually, we may want to create a new "sheet" with these fields
    for row in _metas[::-1]:
        survey_content.remove(row)
        survey_content.insert(0, row)

    for row in content.get('choices', []):
        for key, vals in iter(specials.items()):
            if key in row:
                _expand_translatable_content(content, row, key, vals)

    if 'settings' in content and isinstance(content['settings'], list):
        if len(content['settings']) > 0:
            content['settings'] = content['settings'][0]
        else:
            content['settings'] = {}
    content['schema'] = SCHEMA_VERSION


def expand_content(
    content: Dict[str, List[Any]],
    in_place: bool = False,
) -> Optional[Dict[str, List[Any]]]:
    if in_place:
        expand_content_in_place(content)
        return None
    else:
        content_copy = deepcopy(content)
        expand_content_in_place(content_copy)
        return content_copy


def _get_known_translated_cols(translated_cols: List[str]) -> List[str]:
    """
    This is necessary to handle a legacy issue where media attributes such as
    `image`, `audio` and `video` were transformed to `media::x`, but their
    value in the `translated` list was still `x` therefore not being recognized
    as a "known translated" column. This resulted in a mismatch in labels and
    translations and broke the exports and autoreport.
    """
    if not translated_cols:
        return []

    _translated_cols = []
    for col in translated_cols:
        if col in MEDIA_COLUMN_NAMES:
            col = f'media::{col}'
        _translated_cols.append(col)

    return _translated_cols


def _get_special_survey_cols(
    content: Dict[str, List[Any]],
) -> Tuple[OrderedDict, List[str], List[str]]:
    """
    This will extract information about columns in an xlsform with ':'s

    and give the "expand_content" information for parsing these columns.
    Examples--
        'media::image',
        'media::image::English',
        'label::Français',
        'hint::English',
    For more examples, see tests.
    """
    RE_MEDIA_COLUMN_NAMES = '|'.join(MEDIA_COLUMN_NAMES)

    uniq_cols = OrderedDict()
    special = OrderedDict()

    known_translated_cols = _get_known_translated_cols(
        content.get('translated')
    )

    def _pluck_uniq_cols(sheet_name: str) -> None:
        for row in content.get(sheet_name, []):
            # we don't want to expand columns which are already known
            # to be parsed and translated in a previous iteration
            _cols = [r for r in row.keys() if r not in known_translated_cols]

            uniq_cols.update(OrderedDict.fromkeys(_cols))

    def _mark_special(**kwargs: str) -> None:
        column_name = kwargs.pop('column_name')
        special[column_name] = kwargs

    _pluck_uniq_cols('survey')
    _pluck_uniq_cols('choices')

    for column_name in uniq_cols.keys():
        if column_name in ['label', 'hint']:
            _mark_special(
                column_name=column_name,
                column=column_name,
                translation=UNTRANSLATED,
            )
        if ':' not in column_name and column_name not in MEDIA_COLUMN_NAMES:
            continue
        if column_name.startswith('bind:'):
            continue
        if column_name.startswith('body:'):
            continue
        mtch = re.match(
            rf'^(media\s*::?\s*)?({RE_MEDIA_COLUMN_NAMES})\s*::?\s*([^:]+)$',
            column_name,
        )
        if mtch:
            matched = mtch.groups()
            media_type = matched[1]
            translation = matched[2]
            _mark_special(
                column_name=column_name,
                column='media::{}'.format(media_type),
                coltype='media',
                media=media_type,
                translation=translation,
            )
            continue
        mtch = re.match(
            rf'^(media\s*::?\s*)?({RE_MEDIA_COLUMN_NAMES})$', column_name
        )
        if mtch:
            matched = mtch.groups()
            media_type = matched[1]
            _mark_special(
                column_name=column_name,
                column='media::{}'.format(media_type),
                coltype='media',
                media=media_type,
                translation=UNTRANSLATED,
            )
            continue
        mtch = re.match(r'^([^:]+)\s*::?\s*([^:]+)$', column_name)
        if mtch:
            # example: label::x, constraint_message::x, hint::x
            matched = mtch.groups()
            column_shortname = matched[0]
            _mark_special(
                column_name=column_name,
                column=column_shortname,
                translation=matched[1],
            )

            # also add the empty column if it exists
            if column_shortname in uniq_cols:
                _mark_special(
                    column_name=column_shortname,
                    column=column_shortname,
                    translation=UNTRANSLATED,
                )
            continue
    translations, translated_cols = _get_translations_from_special_cols(
        special,
        content.get('translations', []),
    )
    translated_cols.update(known_translated_cols)
    return special, translations, sorted(translated_cols)


def _expand_type_to_dict(type_str: str) -> Dict[str, Union[str, bool]]:
    SELECT_PATTERN = r'^({select_type})\s+(\S+)$'
    out = {}
    match = re.search(r'\s+(or.other)$', type_str)
    if match:
        type_str = type_str.replace(match.groups()[0], '').strip()
        out[OR_OTHER_COLUMN] = True
    match = re.search('select_(one|multiple)(_or_other)', type_str)
    if match:
        type_str = type_str.replace('_or_other', '')
        out[OR_OTHER_COLUMN] = True
    if type_str in ['select_one', 'select_multiple']:
        out['type'] = type_str
        return out
    for select_type in selects.keys():
        match = re.match(
            SELECT_PATTERN.format(select_type=select_type), type_str
        )
        if match:
            (type_, list_name) = match.groups()
            matched_type = selects[select_type]
            out['type'] = matched_type
            ref_field_name = 'select_from_list_name'
            if 'from_file' in matched_type:
                ref_field_name = 'file'
            out[ref_field_name] = list_name
            return out
    # if it does not expand, we return the original string
    return {'type': type_str}


def _expand_xpath_to_list(xpath_string: str) -> str:
    # a placeholder for a future expansion
    return xpath_string
