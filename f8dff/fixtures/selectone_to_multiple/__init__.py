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
    u'title': 'Select One to Multiple',
    u'id_string': 'selectone_to_multiple',
    u'versions': [
        load_fixture_json('selectone_to_multiple/v1_normal'),
        load_fixture_json('selectone_to_multiple/v2_selectone'),
        load_fixture_json('selectone_to_multiple/v3_selectmultiple'),
    ],
    u'submissions': load_fixture_json('selectone_to_multiple/submissions'
                                      ).get('submissions')
}
