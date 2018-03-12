# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
site_inspection:

 * v1: "yes" and "no" named as labeled
 * v2: "yes" and "no" named 1 and 0
 * v3: remove duplicate "was_there_damage_to_the_site_dupe"
 * v4: rename group "group_proprietary_tool" to "group_network_quality"
 * v5: add group "group_perimeter" and move "is_plant_life_encroaching" into it

Inspired by support request #2808

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Site inspection',
    u'id_string': 'site_inspection',
    u'versions': [
        load_fixture_json('site_inspection/v1'),
        load_fixture_json('site_inspection/v2'),
        load_fixture_json('site_inspection/v3'),
        load_fixture_json('site_inspection/v4'),
        load_fixture_json('site_inspection/v5')
    ],
}


DATA_WITH_COPY_FIELDS = {
    u'title': 'Site inspection',
    u'id_string': 'site_inspection',
    u'versions': [
        load_fixture_json('site_inspection/v1'),
        load_fixture_json('site_inspection/v2'),
        load_fixture_json('site_inspection/v3'),
        load_fixture_json('site_inspection/v4'),
        load_fixture_json('site_inspection/v5'),
        load_fixture_json('site_inspection/v6'),
    ],
}
