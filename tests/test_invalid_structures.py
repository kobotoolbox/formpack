# coding: utf-8
from copy import copy

import pytest
import unittest

from formpack import FormPack

SINGLE_NOTE_SURVEY = {
    'content': {
        'survey': [
            {
                'type': 'note',
                'label': 'Note',
                'name': 'note',
            }
        ]
    }
}


class TestInvalidCases(unittest.TestCase):
    def test_single_version_doesnt_require_version(self):
        FormPack(
            id_string='idstring',
            versions=[
                copy(SINGLE_NOTE_SURVEY),
            ],
        )

    def test_conflicting_version_ids(self):
        with pytest.raises(ValueError):
            FormPack(
                id_string='idstring',
                versions=[
                    copy(SINGLE_NOTE_SURVEY),
                    copy(SINGLE_NOTE_SURVEY),
                ],
            )

    def test_formpack_cannot_have_name(self):
        with pytest.raises(TypeError):
            vdata = copy(SINGLE_NOTE_SURVEY)
            FormPack(
                id_string='idstring',
                name='somename',
                versions=[
                    vdata,
                ],
            )

    def test_formpack_version_cannot_have_name(self):
        with pytest.raises(ValueError):
            vdata = copy(SINGLE_NOTE_SURVEY)
            vdata['name'] = 'somename'
            FormPack(
                id_string='idstring',
                versions=[
                    vdata,
                ],
            )

    # TODO: remove this test of fix it
    # @raises(PyXFormError)
    # def test_xform(self):
    #     fp = FormPack(title='test_fixture_title',
    #                   root_node_name='daata',
    #                   versions=[
    #                       SINGLE_NOTE_SURVEY,
    #                   ])
    #     fp.versions[0].to_xml()
