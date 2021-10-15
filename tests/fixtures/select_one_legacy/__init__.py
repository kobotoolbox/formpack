# coding: utf-8
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
