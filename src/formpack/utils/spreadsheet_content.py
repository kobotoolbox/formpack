import re
from copy import deepcopy, copy
from collections import OrderedDict, defaultdict

from ..constants import TAG_COLUMNS_AND_SEPARATORS
from .flatten_content import (_flatten_translated_fields, _flatten_survey_row,
                              _flatten_tags,
                              translated_col_list)

# xlsform specific ordering preferences

SHEET_ORDER = ['survey', 'choices', 'settings']

ORDERS_BY_SHEET = {
    'survey': [
        '^type$',
        '^name$',
        '^label',
        '^hint',
    ],
    'choices': [
        '^list_name$',
        '^name$',
        '^label',
    ],
    'settings': [
        '^id_string$',
        '^form_title$',
    ]
}


def flatten_to_spreadsheet_content(content,
                                   in_place=False,
                                   prioritized_columns=None,
                                   deprioritized_columns=None,
                                   remove_columns=None,
                                   remove_sheets=None,
                                   ):
    if prioritized_columns is None:
        prioritized_columns = {}
    if deprioritized_columns is None:
        deprioritized_columns = {}
    if remove_columns is None:
        remove_columns = {}
    if remove_sheets is None:
        remove_sheets = []
    if not in_place:
        content = deepcopy(content)

    translations = content.pop('translations', [])
    translated_cols = content.pop('translated', [])
    if 'settings' in content and isinstance(content['settings'], dict):
        content['settings'] = [content['settings']]
    sheet_names = _order_sheet_names(filter(lambda x: x not in remove_sheets,
                                            content.keys()))
    def _row_to_ordered_dict(row, dest):
        _flatten_translated_fields(row, translations, translated_cols,
                                   col_order=dest.keys(),
                                   )
        _flatten_survey_row(row)
        for key in dest.keys():
            dest[key] = row.get(key, None)
        return dest

    def _sheet_to_ordered_dicts(sheet_name, rows):
        all_cols = OrderedDict()
        if not isinstance(rows, list):
            return None
        for row in rows:
            all_cols.update(OrderedDict.fromkeys(row.keys()))
        _all_cols = _order_cols(all_cols.keys(), sheet_name)

        removed = remove_columns.get(sheet_name, [])
        firsts = prioritized_columns.get(sheet_name, [])
        firsts = list(filter(lambda x: x in _all_cols, firsts))
        lasts = deprioritized_columns.get(sheet_name, [])
        lasts = list(filter(lambda x: x in _all_cols, lasts))
        _not_mids = firsts + lasts + removed
        mids = list(filter(lambda x: x not in _not_mids, _all_cols))

        ordered_cols = translated_col_list((firsts + mids + lasts), translations, translated_cols)
        return [
            _row_to_ordered_dict(row, OrderedDict.fromkeys(ordered_cols)) for row in rows
        ]
    if in_place:
        _od = content
        for sheet in remove_sheets:
            _od.pop(sheet)
    else:
        _od = OrderedDict()
    all_sheets = content.keys()
    for sheet_name in sheet_names:
        rows = content.pop(sheet_name)
        for row in rows:
            if 'tags' in row:
                _flatten_tags(
                    row, tag_cols_and_seps=TAG_COLUMNS_AND_SEPARATORS)
        if sheet_name in all_sheets:
            all_sheets.remove(sheet_name)
        _od[sheet_name] = _sheet_to_ordered_dicts(sheet_name, rows)
    if not in_place:
        return _od


def _order_sheet_names(sheet_names):
    _ordered = []
    for sht in SHEET_ORDER:
        if sht in sheet_names:
            _ordered.append(sht)
            sheet_names.remove(sht)
    return _ordered + sheet_names


def _order_cols(cols, sheet_name=False):
    _ordered = []
    orders = ORDERS_BY_SHEET.get(sheet_name, ORDERS_BY_SHEET['survey'])
    for _cre in orders:
        _ms = []
        for _c in cols:
            if re.search(_cre, _c):
                _ms.append(_c)
                cols.remove(_c)
        _ordered += _ms
    return _ordered + cols
