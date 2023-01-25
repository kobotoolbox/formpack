# coding: utf-8
'''
analysis_form
'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Simple Clerk Interaction',
    'id_string': 'cerk_interaction',
    'versions': [
        load_fixture_json('analysis_form/v1'),
        load_fixture_json('analysis_form/v2'),
    ],
}
