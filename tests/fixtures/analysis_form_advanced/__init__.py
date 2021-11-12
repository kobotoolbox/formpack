# coding: utf-8
'''
analysis_form_advanced
'''

from ..load_fixture_json import load_fixture_json, load_analysis_form_json

DATA = {
    'title': 'Advanced Clerk Interaction',
    'id_string': 'cerk_interaction_advanced',
    'versions': [
        load_fixture_json('analysis_form_advanced/v1'),
    ],
    'analysis_form': load_analysis_form_json('analysis_form_advanced')
}
