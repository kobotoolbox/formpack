'''
dietary_needs:

 * has a select_multiple (described in a different syntax)

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Household survey with repeatable groups',
    u'id_string': 'grouped_repeatable',
    u'versions': [
        load_fixture_json('grouped_repeatable/v1'),
    ],
}
