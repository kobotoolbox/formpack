# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from formpack.utils.xls_to_ss_structure import _parsed_sheet


class TestXlsToSpreadsheetStructure(unittest.TestCase):
    def _to_dicts(self, list_of_ordered_dicts):
        # convert OrderedDicts to dicts
        return [dict(d) for d in list_of_ordered_dicts]

    def test_internal_method_parsed_sheet_normal(self):
        '''
        in xls_to_ss_structure, the internal method
        _parsed_sheet(...) accepts a list of lists and
        returns a list of dicts
        '''
        sheet_dicts = _parsed_sheet([['h1', 'h2'],
                                     ['r1v1', 'r1v2'],
                                     ['r2v1', 'r2v2']])
        sheet_dicts = self._to_dicts(sheet_dicts)

        self.assertEqual(sheet_dicts, [
                {'h1': 'r1v1', 'h2': 'r1v2'},
                {'h1': 'r2v1', 'h2': 'r2v2'},
            ])

    def test_internal_method_parsed_sheet_normal(self):
        '''
        edge cases:
         * sheet has only column headers (no values)
         * sheet has no rows
        should return an empty list
        '''
        sheet_dicts = self._to_dicts(_parsed_sheet([['h1', 'h2']]))
        self.assertEqual(sheet_dicts, [])

        sheet_dicts = self._to_dicts(_parsed_sheet([]))
        self.assertEqual(sheet_dicts, [])
