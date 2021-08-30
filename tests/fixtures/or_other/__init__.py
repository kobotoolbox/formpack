# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
or_other
'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Your favourite Roman emperors or other',
    'id_string': 'or_other',
    'versions': [
        load_fixture_json('or_other/v1'),
    ],
}
