# coding: utf-8
'''
simple_grouped_repeatable
'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Simple grouped repeatable',
    'id_string': 'simple_grouped_repeatable',
    'versions': [
        load_fixture_json('simple_grouped_repeatable/v1'),
        load_fixture_json('simple_grouped_repeatable/v2'),
    ],
}
