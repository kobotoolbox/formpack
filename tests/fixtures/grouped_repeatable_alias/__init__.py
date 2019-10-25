# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)



from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Grouped Repeatable Alias',
    'id_string': 'grouped_repeatable',
    'versions': [
        load_fixture_json('grouped_repeatable_alias/v1'),
    ],
}
