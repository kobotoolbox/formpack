# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
field_position_with_multiple_versions:

 * v1: `Fullname` and `Age` in repeating group
 * v2: Add `City` after repeating group
 * v3: Replace `Fullname` with `Firstname`, `Lastname`, and `Gender`

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Field Position with Multiple Versions',
    u'id_string': 'field_position_with_multiple_versions',
    u'versions': [
        load_fixture_json('field_position_with_multiple_versions/v1'),
        load_fixture_json('field_position_with_multiple_versions/v2'),
        load_fixture_json('field_position_with_multiple_versions/v3'),
    ],
}
