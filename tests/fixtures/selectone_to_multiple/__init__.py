'''
selectone_to_multiple has

* text question
    turns to
* select_one
    turns to
* select_multiple
'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Select One to Multiple',
    'id_string': 'selectone_to_multiple',
    'versions': [
        load_fixture_json('selectone_to_multiple/v1_normal'),
        load_fixture_json('selectone_to_multiple/v2_selectone'),
        load_fixture_json('selectone_to_multiple/v3_selectmultiple'),
    ],
    'submissions': load_fixture_json('selectone_to_multiple/submissions'
                                      ).get('submissions')
}
