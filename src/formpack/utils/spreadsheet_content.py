import re
from copy import deepcopy
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


def flatten_to_spreadsheet_content(expanded_content):
    content = deepcopy(expanded_content)
    translations = content.pop('translations')
    translated_cols = content.pop('translated')
    if 'settings' in content and isinstance(content['settings'], (dict, OrderedDict)):
        content['settings'] = [content['settings']]
    sheet_names = _order_sheet_names(content.keys())

    def _row_to_ordered_dict(sheet_name, row):
        cols = row.keys()
        _ordered_cols = _order_cols(cols, sheet_name)
        _flatten_translated_fields(row, translations, translated_cols,
                                   col_order=_ordered_cols)
        newcols = row.keys()
        if not set(newcols).issubset(_ordered_cols):
            raise Exception('not all columns are included in ordered list')
        return OrderedDict([
                (key, row.get(key, None)) for key in _ordered_cols
            ])

    return OrderedDict([
        (sheet_name, [
            _row_to_ordered_dict(sheet_name, row) for row in content[sheet_name]
          ]) for sheet_name in sheet_names
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
