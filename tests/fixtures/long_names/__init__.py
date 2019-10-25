# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
long_names

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'long survey name: the quick, brown fox jumps over the lazy dog',
    'id_string': 'long_survey_name__the_quick__brown_fox_jumps_over_the_lazy_dog',
    'versions': [
        load_fixture_json('long_names/v1'),
    ],
}
