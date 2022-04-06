# coding: utf-8
from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Sanitation report',
    'versions': [
        load_fixture_json('sanitation_report/v1'),
    ],
}
