# coding: utf-8
'''
field_position_with_multiple_versions:

 * v1: `Fullname` and `Age` in repeating group
 * v2: Add `City` after repeating group
 * v3: Replace `Fullname` with `Firstname`, `Lastname`, and `Gender`

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Field Position with Multiple Versions',
    'id_string': 'field_position_with_multiple_versions',
    'versions': [
        load_fixture_json('field_position_with_multiple_versions/v1'),
        load_fixture_json('field_position_with_multiple_versions/v2'),
        load_fixture_json('field_position_with_multiple_versions/v3'),
    ],
}
