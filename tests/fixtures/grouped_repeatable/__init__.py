# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

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
