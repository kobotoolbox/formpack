# coding: utf-8
"""
all geo types:

 * v1: includes a `geopoint`, `geotrace`, and `geoshape`, as well as a `text`
 * v2: moves the `geopoint`, `geotrace`, and `geoshape` into a group and adds a
       new `geopoint` outside the group
"""

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'I have points, traces, and shapes!',
    'id_string': 'all_geo_types',
    'versions': [
        load_fixture_json('all_geo_types/v1'),
        load_fixture_json('all_geo_types/v2'),
    ],
}
