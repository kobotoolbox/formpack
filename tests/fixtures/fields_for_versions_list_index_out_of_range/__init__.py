# coding: utf-8
'''
fields_for_versions_list_index_out_of_range:

 * v1: Three text fields: `first_but_not_one`, `one`, `third`
 * v2: Remove `first_but_not_one` and `third

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Fields for versions list index out of range',
    'id_string': 'fields_for_versions_list_index_out_of_range',
    'versions': [
        load_fixture_json('fields_for_versions_list_index_out_of_range/v1'),
        load_fixture_json('fields_for_versions_list_index_out_of_range/v2'),
    ],
}
