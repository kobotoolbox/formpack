# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from ..models.formpack.pack import FormPack
from ..fixtures import build_fixture

restaurant_profile = build_fixture('restaurant_profile')


class TestSurveyParsers(unittest.TestCase):
    def test_fixture_has_translations(self):
        '''
        restauraunt_profile@v2 has two translations
        '''

        title, schemas, submissions = restaurant_profile
        fp = FormPack(schemas, title)
        self.assertEqual(len(fp[1].translations), 2)
