# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

'''
long_unicode_labels

*** WARNING ***
Pay attention to the line delimiters (\r\n) and Unicode BOM in the `sps` files.
Some editors may mangle these without warning, and this will cause tests to
fail!

'''

from ..load_fixture_json import load_fixture_json

DATA = {
    u'title': u'long unicode labels to test SPSS export',
    u'id_string': 'long_labels',
    u'versions': [
        load_fixture_json('long_unicode_labels/v1'),
    ],
}
