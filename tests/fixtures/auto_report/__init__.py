# coding: utf-8

from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Auto report',
    'id_string': 'auto_report',
    'versions': [
        load_fixture_json('auto_report/v1'),
    ],
}
