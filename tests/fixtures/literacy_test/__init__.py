# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
literacy_test

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Literacy test',
    u'id_string': 'literacy_test',
    u'versions': [
        load_fixture_json('literacy_test/v1'),
    ],
}
