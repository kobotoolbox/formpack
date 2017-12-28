# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
grouped_translated

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Animal identification survey with translations and groups',
    u'id_string': 'grouped_translated',
    u'versions': [
        load_fixture_json('grouped_translated/v1'),
    ],
}
