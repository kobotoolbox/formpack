# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
restaurant_profile:

 * v1 is single language
 * v2 is in 2 languages

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Restaurant profile',
    u'id_string': 'restaurant_profile',
    u'versions': [
        load_fixture_json('restaurant_profile/v1'),
        load_fixture_json('restaurant_profile/v2'),
        load_fixture_json('restaurant_profile/v3'),
        load_fixture_json('restaurant_profile/v4')
    ],
}
