# coding: utf-8

from ..load_fixture_json import load_fixture_json


def _wc(id_string, version_id, surv):
    return {
        'id_string': id_string,
        'version': version_id,
        'content': {
            'survey': surv
        }
    }

DATA = {
    'title': 'Favorite color',
    'versions': [
        _wc('favcolor', 'favcolor_v1', [
            {'type': 'text', 'name': 'what_is_your_name_',
             'label': 'What is your name?', 'required': 'true()'},
            {'type': 'text', 'name': 'what_is_your_favorite_color_',
             'label': 'What is your favorite color?', 'required': 'true()'},
        ]),
        _wc('favcolor', 'favcolor_v2', [
            {'type': 'text', 'name': 'what_is_your_firstname',
             'label': 'What is your first name?', 'required': 'true()'},
            {'type': 'text', 'name': 'what_is_your_surname',
             'label': 'What is your last name?', 'required': 'true()'},
            {'type': 'text', 'name': 'what_is_your_favorite_color_',
             'label': 'What is your favorite color?', 'required': 'true()'},
        ]),
    ],
    'submissions_xml': load_fixture_json('favcolor/xml_instances'),
}
