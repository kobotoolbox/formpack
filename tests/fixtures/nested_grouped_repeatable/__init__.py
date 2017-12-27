# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
nested_grouped_repeatable

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Bird nest survey with nested repeatable groups',
    u'id_string': 'nested_grouped_repeatable',
    u'versions': [
        load_fixture_json('nested_grouped_repeatable/v1'),
    ],
}
