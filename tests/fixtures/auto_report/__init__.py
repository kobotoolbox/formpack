# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)


from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Auto report',
    u'id_string': 'auto_report',
    u'versions': [
        load_fixture_json('auto_report/v1'),
    ],
}
