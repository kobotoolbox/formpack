# coding: utf-8

from ..load_fixture_json import load_fixture_json

'''
media_types

'''

DATA = {
    'title': 'Media of your favourite Roman emperors',
    'id_string': 'media_types',
    'versions': [
        load_fixture_json('media_types/v1'),
    ],
}
