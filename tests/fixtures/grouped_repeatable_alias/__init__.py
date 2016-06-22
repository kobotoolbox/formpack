# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)



from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Grouped Repeatable Alias',
    u'id_string': 'grouped_repeatable',
    u'versions': [
        load_fixture_json('grouped_repeatable_alias/v1'),
    ],
}
