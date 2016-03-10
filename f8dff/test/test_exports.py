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
        forms = FormPack(**customer_satisfaction)
        values_exported = forms._export_to_lists()
        expected = [["submissions", [
                        ["restaurant_name", "customer_enjoyment"],
                        [
                            ["Felipes", "yes"],
                            ["Dunkin Donuts", "no"],
                            ["McDonalds", "no"]]]
                     ]]

        self.assertEqual(expected, values_exported)

    def test_generator_export_translation_headers(self):
        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp.versions), 3)
        self.assertEqual(len(fp[1].translations), 2)

        # by default, exports use the question 'name' attribute
        headers = fp._export_to_lists(version=0)[0][1][0]
        self.assertEquals(headers, ['restaurant_name', 'location'])

        # the first translation in the list is the translation that
        # appears first in the column list. in this case, 'label::english'
        translations = fp[1].translations
        headers = fp._export_to_lists(header_lang=translations[0],
                                      version=1)[0][1][0]
        self.assertEquals(headers, ['restaurant name', 'location'])

        headers = fp._export_to_lists(header_lang=translations[1],
                                      version=1)[0][1][0]
        # TODO: location is "lieu" in french, or just "adresse"
        self.assertEquals(headers, ['nom du restaurant', 'location'])

        # "default" use the "Label" field
        # TODO: make a separate test to test to test __getitem__
        formpack = FormPack(**restaurant_profile)
        headers = formpack._export_to_lists(header_lang="default",
                                            version='rpv1')
        self.assertEquals(headers[0][1][0], ['restaurant name', 'location'])

    def test_export_with_choice_lists(self):
        fp = FormPack(**restaurant_profile)
        self.assertEqual(len(fp[1].translations), 2)

        # by default, exports use the question 'name' attribute
        _as_lists = fp._export_to_lists(version='rpV3')[0][1]
        (headers, submissions) = _as_lists
        self.assertEquals(headers, ['restaurant_name', 'location', 'eatery_type'])
        self.assertEquals(submissions, [['Taco Truck', '13.42 -25.43', 'takeaway'],
                                        ['Harvest', '12.43 -24.53', 'sit_down']])
