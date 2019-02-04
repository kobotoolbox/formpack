# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Favorite coffee',
    u'id_string': 'favorite_coffee',
    u'versions': [
        load_fixture_json('favorite_coffee/v1'),
        load_fixture_json('favorite_coffee/v2')
    ]
}
