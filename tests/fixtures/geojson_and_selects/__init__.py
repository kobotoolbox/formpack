# coding: utf-8

"""
geojson_and_selects
"""

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Geo and selects',
    'id_string': 'geojson_and_selects',
    'versions': [
        load_fixture_json('geojson_and_selects/v1'),
    ],
}
