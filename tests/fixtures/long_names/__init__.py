# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
long_names

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'long survey name: the quick, brown fox jumps over the lazy dog',
    u'id_string': 'long_survey_name__the_quick__brown_fox_jumps_over_the_lazy_dog',
    u'versions': [
        load_fixture_json('long_names/v1'),
    ],
}
