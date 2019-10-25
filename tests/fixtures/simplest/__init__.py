# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
simplest:

* has bare minimum attributes to generate a usable xform project
'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'The simplest possible survey',
    'id_string': 'simplest',
    'versions': [
        load_fixture_json('simplest/v1'),
    ],
}
