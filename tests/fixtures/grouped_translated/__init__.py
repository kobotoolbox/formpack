# coding: utf-8
'''
grouped_translated

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Animal identification survey with translations and groups',
    'id_string': 'grouped_translated',
    'versions': [
        load_fixture_json('grouped_translated/v1'),
    ],
}
