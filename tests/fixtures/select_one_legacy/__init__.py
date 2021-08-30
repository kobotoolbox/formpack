# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
select_one_legacy

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Your favourite Roman emperors',
    'id_string': 'select_one_legacy',
    'versions': [
        load_fixture_json('select_one_legacy/v1'),
    ],
}
