# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
restaurant_photo:

 * v1 has photo attachments
'''

from ..load_fixture_json import load_fixture_json

photos = load_fixture_json('restaurant_photo/images')
v1 = load_fixture_json('restaurant_photo/v1')
v1['submissions'] = [{'photo': pdata} for pdata in photos]

DATA = {
    'title': 'Restaurant profile',
    'versions': [
        v1
    ],
}
