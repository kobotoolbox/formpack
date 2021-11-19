# coding: utf-8
'''
analysis_form_repeat_groups
'''

from ..load_fixture_json import load_fixture_json, load_analysis_form_json

DATA = {
    'title': 'Clerk Interaction Repeat Groups',
    'id_string': 'cerk_interaction_repeat_groups',
    'versions': [
        load_fixture_json('analysis_form_repeat_groups/v1'),
    ],
    'analysis_form': load_analysis_form_json('analysis_form_repeat_groups')
}
