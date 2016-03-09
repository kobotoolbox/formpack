# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest

from f8dff.models.formpack.pack import FormPack
from f8dff.fixtures import build_fixture

import json

customer_satisfaction = build_fixture('customer_satisfaction')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

    def test_generator_export(self):
        options = {}
        values_in_lists = FormPack(**customer_satisfaction)._export_to_lists(options)
        print(json.dumps(values_in_lists, indent=4))

