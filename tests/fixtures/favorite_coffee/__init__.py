# coding: utf-8

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Favorite coffee',
    'id_string': 'favorite_coffee',
    'versions': [
        load_fixture_json('favorite_coffee/v1'),
        load_fixture_json('favorite_coffee/v2')
    ]
}
