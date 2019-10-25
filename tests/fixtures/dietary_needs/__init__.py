# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
dietary_needs:

 * has a select_multiple (described in a different syntax)

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Dietary needs',
    'id_string': 'dietary_needs',
    'versions': [
        load_fixture_json('dietary_needs/v1'),
    ],
}
