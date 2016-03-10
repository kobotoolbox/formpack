# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from f8dff.models.formpack.pack import FormPack
from f8dff.fixtures import build_fixture


customer_satisfaction = build_fixture('customer_satisfaction')
restaurant_profile = build_fixture('restaurant_profile')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

    def test_generator_export(self):
        values_exported = FormPack(**customer_satisfaction
                                   )._export_to_lists()
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
        self.assertEqual(len(fp[1].translations), 2)

        # by default, exports use the question 'name' attribute
        headers = fp._export_to_lists(version=1)[0][1][0]
        self.assertEquals(headers, ['restaurant_name', 'location'])

        # the first translation in the list is the translation that
        # appears first in the column list. in this case, 'label::english'
        translations = fp[1].translations
        self.assertEqual(len(translations), 2)

        headers = fp._export_to_lists(header_lang=translations[0],
                                      version=1)[0][1][0]
        self.assertEquals(headers, ['restaurant name', 'location'])

        formpack = FormPack(**restaurant_profile)
        headers = formpack._export_to_lists(header_lang=translations[1],
                                            version=1)
        self.assertEquals(headers[0][1][0], ['nom du restaurant', 'location'])
