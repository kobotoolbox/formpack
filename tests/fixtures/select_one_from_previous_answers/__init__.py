# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
select_one_from_previous_answers

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Household survey with select_one from previous answers',
    'id_string': 'select_one_from_previous_answers',
    'versions': [
        load_fixture_json('select_one_from_previous_answers/v1'),
    ],
}
