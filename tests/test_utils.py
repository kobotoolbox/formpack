# coding: utf-8

from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import unittest
from collections import OrderedDict
from formpack.utils.xls_to_ss_structure import _parsed_sheet
from formpack.utils.flatten_content import flatten_content
from formpack.utils.json_hash import json_hash


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


class TestNestedStructureToFlattenedStructure(unittest.TestCase):
    def _wrap_field(self, field_name, value):
        return {'survey': [
            {'type': 'text', 'name': 'x'},
            {'type': 'text', 'name': 'y', field_name: value},
        ]}

    def _wrap_type(self, type_val):
        return {'survey': [{
            'type': type_val,
            'name': 'q_yn',
            'label': 'Yes or No',
        }], 'choices': [
            {'list_name': 'yn', 'name': 'y', 'label': 'Yes'},
            {'list_name': 'yn', 'name': 'n', 'label': 'No'},
        ]}

    def test_flatten_empty_relevant(self):
        a1 = flatten_content(self._wrap_field('relevant', []))
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[1]['relevant'], '')

    def test_flatten_relevant(self):
        a1 = flatten_content(self._wrap_field('relevant', [{'$lookup': 'x'}]))
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[1]['relevant'], '${x}')

    def test_flatten_constraints(self):
        a1 = flatten_content(self._wrap_field('constraint', ['.', '>', {'$lookup': 'x'}]))
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[1]['constraint'], '. > ${x}')

    def test_flatten_select_one_type(self):
        a1 = flatten_content(self._wrap_type({'select_one': 'yn'}))
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[0]['type'], 'select_one yn')

    def test_flatten_select_multiple_type(self):
        a1 = flatten_content(self._wrap_type({'select_multiple': 'yn'}))
        ss_struct = a1['survey']
        self.assertEqual(ss_struct[0]['type'], 'select_multiple yn')


def test_json_hash():
    # consistent output
    assert json_hash({'a': 'z', 'b': 'y', 'c': 'x'}) == 'f6117d60'

    # second parameter is size of string
    val = json_hash(['abc'], 35)
    assert len(val) == 35

    # even OrderedDicts have the keys reordered
    assert json_hash(OrderedDict([
            ('c', 'x'),
            ('b', 'y'),
            ('a', 'z'),
        ])) == json_hash(OrderedDict([
            ('a', 'z'),
            ('b', 'y'),
            ('c', 'x'),
        ]))

    # identical objects match (==)
    assert json_hash({'d': 1, 'e': 2, 'f': 3}) == json_hash({'d': 1,
                                                             'e': 2,
                                                             'f': 3})
    # types don't match (1 != '1')
    assert json_hash({'d': 1, 'e': 2, 'f': 3}) != json_hash({'d': '1',
                                                             'e': '2',
                                                             'f': '3'})
