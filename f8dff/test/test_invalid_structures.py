import unittest
from f8dff.models.formpack.pack import FormPack
from copy import copy
from nose.tools import raises

SINGLE_NOTE_SURVEY = {'content': {
        'survey': [
            {'type': 'note', 'label': 'Note', 'name': 'note'}
        ]
    }}


class TestInvalidCases(unittest.TestCase):
    def test_single_version_form(self):
        fp = FormPack(**{
                u'content': {}
            })
        self.assertEqual(len(fp.versions), 0)

    def test_single_version_doesnt_require_version(self):
        FormPack(id_string="idstring", versions=[
                copy(SINGLE_NOTE_SURVEY),
            ])

    @raises(ValueError)
    def test_conflicting_version_ids(self):
        FormPack(id_string="idstring", versions=[
                copy(SINGLE_NOTE_SURVEY),
                copy(SINGLE_NOTE_SURVEY),
            ])
