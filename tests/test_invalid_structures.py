# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from copy import copy

from nose.tools import raises

from formpack import FormPack

SINGLE_NOTE_SURVEY = {
    'schema': '2',
    'survey': [
        {'type': 'note',
         'label': {'tx0': 'Note'},
         '$anchor': 'note',
         'name': 'note'},
    ],
    'settings': {
        'identifier': 'idstring',
        'title': 'Single Note Survey'
    },
    'translations': [{'$anchor': 'tx0', 'name': ''}]
}


class TestInvalidCases(unittest.TestCase):

    def test_single_version_doesnt_require_version(self):
        FormPack(versions=[
                copy(SINGLE_NOTE_SURVEY),
            ])

    @raises(ValueError)
    def test_conflicting_version_ids(self):
        FormPack(versions=[
                copy(SINGLE_NOTE_SURVEY),
                copy(SINGLE_NOTE_SURVEY),
            ])
