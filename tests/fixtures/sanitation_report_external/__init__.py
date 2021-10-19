# coding: utf-8
from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Sanitation report external',
    'versions': [
        load_fixture_json('sanitation_report_external/v1'),
    ],
}
