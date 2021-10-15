# coding: utf-8
'''
grouped_repeatable

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Household survey with repeatable groups',
    'id_string': 'grouped_repeatable',
    'versions': [
        load_fixture_json('grouped_repeatable/v1'),
    ],
}
