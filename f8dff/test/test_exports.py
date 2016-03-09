import unittest

from f8dff.models.formpack.pack import FormPack
from f8dff.fixtures import build_fixture

import json

sanitation_report = build_fixture('sanitation_report')


class TestFormPackExport(unittest.TestCase):
    maxDiff = None

    def test_generator_export(self):
        options = {}
        values_in_lists = FormPack(**sanitation_report)._export_to_lists(options)
        print json.dumps(values_in_lists, indent=4)
