# coding: utf-8
'''
hxl_grouped_repeatable

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Household survey with HXL and repeatable groups',
    'id_string': 'hxl_grouped_repeatable',
    'versions': [
        load_fixture_json('hxl_grouped_repeatable/v1'),
    ],
}
