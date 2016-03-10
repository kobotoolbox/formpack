# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
import json

from f8dff.models.formpack.pack import FormPack
from f8dff.fixtures import build_fixture


customer_satisfaction = build_fixture('customer_satisfaction')
restaurant_profile = build_fixture('restaurant_profile')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

    def test_generator_export(self):
        options = {}
        values_in_lists = FormPack(**customer_satisfaction)._export_to_lists(options)
        print(json.dumps(values_in_lists, indent=4))

    def test_generator_export_language_headers(self):
        '''
        formpack.versions[x].languages is not yet defined
        '''
        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp.versions), 2)
        self.assertEqual(len(fp.versions[1].languages), 2)

        # by default, exports use the question 'name' attribute

        # QUESTION FOR ALEX
        # Are we sure it works like that ? What about the lone "Label" field ?
        headers = fp._export_to_lists({})[0][1][0]
        self.assertEquals(headers, ['restaurant_name', 'location'])

        # the first language in the list is the language that appears first
        # in the column list. in this case, 'label::english'
        languages = fp.versions[1].languages
        headers = fp._export_to_lists({
            'header_language': languages[0],
        })[0][1][0]
        self.assertEquals(headers, ['Restaurant name', 'Location'])

        headers = FormPack(**restaurant_profile)._export_to_lists({
            'header_language': languages[1],
            })[0][1][0]
        self.assertEquals(headers, ['nom du restaurant', 'Location'])
