# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


'''
customer_satisfaction survey

* has select_one (described in the choices sheet)

'''
from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Unknown Columns',
    u'id_string': 'unknown_columns',
    u'versions': [
        load_fixture_json('unknown_columns/v1'),
    ],
}
