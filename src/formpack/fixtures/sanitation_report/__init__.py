# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Sanitation report',
    u'versions': [
        load_fixture_json('sanitation_report/v1'),
    ],
}
