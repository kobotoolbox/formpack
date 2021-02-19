# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Sanitation report external',
    'versions': [
        load_fixture_json('sanitation_report_external/v1'),
    ],
}
