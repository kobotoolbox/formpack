import re
from copy import deepcopy, copy
from collections import OrderedDict

from .flatten_content import _flatten_translated_fields, _flatten_survey_row

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


def flatten_to_spreadsheet_content(expanded_content,
                                   prioritized_columns=None,
                                   deprioritized_columns=None,
                                   remove_columns=None,
                                   remove_sheets=None,
                                   ):
    if prioritized_columns is None:
        prioritized_columns = []
    if deprioritized_columns is None:
        deprioritized_columns = []
    if remove_columns is None:
        remove_columns = []
    if remove_sheets is None:
        remove_sheets = []

    content = deepcopy(expanded_content)
    translations = content.pop('translations')
    translated_cols = content.pop('translated')
    if 'settings' in content and isinstance(content['settings'], dict):
        content['settings'] = [content['settings']]
    sheet_names = _order_sheet_names(filter(lambda x: x not in remove_sheets,
                                            content.keys()))

    def _row_to_ordered_dict(row, cols):
        _flatten_translated_fields(row, translations, translated_cols,
                                   col_order=cols)
        newcols = row.keys()

        for pa in prioritized_columns[::-1]:
            if pa in cols:
                cols.remove(pa)
                cols.insert(0, pa)
        for pz in deprioritized_columns:
            if pz in cols:
                cols.remove(pz)
                cols.append(pz)

        if not set(newcols).issubset(cols):
            raise Exception('not all columns are included in ordered list')
        for xcol in remove_columns:
            if xcol in cols:
                cols.remove(xcol)
        _flatten_survey_row(row)
        return OrderedDict([
                (key, row.get(key, None)) for key in cols
            ])

    def _sheet_to_ordered_dicts(sheet_name):
        rows = content[sheet_name]
        all_cols = OrderedDict()
        if not isinstance(rows, list):
            return None
        for row in rows:
            all_cols.update(OrderedDict.fromkeys(row.keys()))
        _all_cols = _order_cols(all_cols.keys(), sheet_name)
        return [
            _row_to_ordered_dict(row, copy(_all_cols)) for row in rows
        ]
    return OrderedDict([
            (sheet_name, _sheet_to_ordered_dicts(sheet_name)) for sheet_name in sheet_names
        ])


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
