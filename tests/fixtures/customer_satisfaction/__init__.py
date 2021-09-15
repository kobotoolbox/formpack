# coding: utf-8

'''
customer_satisfaction survey

* has select_one (described in the choices sheet)

'''
from ..load_fixture_json import load_fixture_json

DATA = {
    'title': 'Customer Satisfaction',
    'id_string': 'customer_satisfaction',
    'versions': [
        load_fixture_json('customer_satisfaction/v1'),
    ],
}
