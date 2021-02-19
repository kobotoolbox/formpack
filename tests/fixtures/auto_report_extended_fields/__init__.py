# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Auto report with extended fields',
    'id_string': 'auto_report_extended_fields',
    'versions': [
        load_fixture_json('auto_report_extended_fields/v1')
    ],
}
