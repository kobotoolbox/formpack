# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
grouped_repeatable

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Household survey with repeatable groups',
    u'id_string': 'grouped_repeatable',
    u'versions': [
        load_fixture_json('grouped_repeatable/v1'),
    ],
}
