# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

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
