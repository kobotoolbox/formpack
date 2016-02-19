'''
dietary_needs:

 * has a select_multiple (described in a different syntax)

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'Dietary needs',
    u'versions': [
        load_fixture_json('dietary_needs/v1'),
    ],
}
