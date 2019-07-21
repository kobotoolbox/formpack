# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
all geo types:

includes a `geopoint`, `geotrace`, and `geoshape`, outside and inside of a
group. includes a second version where additional geo- questions are added.

 * v1: S
 * v2:  T
 * v3:   U
 * v4:    F
 * v5:     F

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'I have points, traces, and shapes!',
    'id_string': 'all_geo_types',
    'versions': [
        load_fixture_json('all_geo_types/v1'),
        load_fixture_json('all_geo_types/v2'),
    ],
}
