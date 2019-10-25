# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
nested_grouped_repeatable

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Bird nest survey with nested repeatable groups',
    'id_string': 'nested_grouped_repeatable',
    'versions': [
        load_fixture_json('nested_grouped_repeatable/v1'),
    ],
}
