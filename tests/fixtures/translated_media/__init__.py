# coding: utf-8
'''
translated_media
'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Your favourite Roman emperors',
    'id_string': 'translated_media',
    'versions': [
        load_fixture_json('translated_media/v1'),
    ],
}
