'''
customer_satisfaction survey

* has select_one (described in the choices sheet)

'''
from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': 'Customer Satisfaction',
    u'id_string': 'customer_satisfaction',
    u'versions': [
        load_fixture_json('customer_satisfaction/v1'),
    ],
}
